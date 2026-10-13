#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# *****************************************************************************
# Copyright 2026 Autodesk, Inc. All rights reserved.
#
# SPDX-License-Identifier: Apache-2.0
#
# *****************************************************************************

"""Check whether a dependency's installed tree still works from a different path.

    python3 src/build/check_relocation.py --install <tree> --package <Name> --target <Target>

Exits 0 when the tree is relocatable, 1 when it is not, 2 when the check could not be run.

This is the gate for the dependency store. A store entry is found by path, so an installed tree that
remembers where it was installed -- a config file with an absolute include directory, a library with
an absolute runtime search path -- works perfectly until it is used from anywhere else, and then
fails somewhere unrelated. A dependency is only named store-eligible after this passes.

The check is deliberately destructive in one narrow way, because a check that leaves the original in
place cannot detect a reference to it: an absolute reference would resolve to the original and the
check would pass while proving nothing. So the installed tree is moved aside for the duration --
renamed, not deleted, so a failure to restore is visible and recoverable -- and the consumer is built
against a copy at a different path. Any reference to the original path then has nothing to resolve
to, which is what makes the check mean something.

Nothing about this runs during a normal configure or build. It is run when a dependency is being
considered for the store, and its result is recorded.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile

# Extensions of things that are loaded at run time rather than linked, which is where an embedded
# absolute path shows up only when the library is actually resolved.
SHARED_LIBRARY_SUFFIXES = (".so", ".dylib", ".dll")

CONSUMER_SOURCE = """\
// Written by src/build/check_relocation.py. Links the dependency's imported target, calls into it
// if the caller said how, and loads every shared library in the tree at run time -- linking alone
// would not prove the libraries resolve, because a library nothing references need not be loaded.
#include <cstdio>
{includes}

{load_includes}

int main() {{
{exercise}
    int failures = 0;
{loads}
    return failures == 0 ? 0 : 1;
}}
"""


def log(message: str) -> None:
    print(f"[check_relocation] {message}", file=sys.stderr, flush=True)


def run(command, cwd=None, env=None):
    result = subprocess.run(command, cwd=cwd, env=env, capture_output=True, text=True)
    return result.returncode, (result.stdout or "") + (result.stderr or "")


def shared_libraries(install_dir: str):
    """Every shared library in the tree, relative to its install directory."""
    found = []
    for root, _directories, files in os.walk(install_dir):
        for name in files:
            if name.lower().endswith(SHARED_LIBRARY_SUFFIXES):
                found.append(os.path.join(root, name))
    return sorted(found)


def write_consumer(
    work: str, install_dir: str, package: str, target: str, includes, exercise: str, libraries, module=False
):
    """Write a consumer project that uses the dependency from its new location."""
    consumer = os.path.join(work, "consumer")
    os.makedirs(consumer, exist_ok=True)

    if os.name == "nt":
        load_includes = "#include <windows.h>"
        loads = "\n".join(
            f'    if (!LoadLibraryW(L"{path.replace(os.sep, "/")}")) {{ std::printf("failed to load {os.path.basename(path)}\\n"); failures++; }}'
            for path in libraries
        )
    else:
        load_includes = "#include <dlfcn.h>"
        loads = "\n".join(
            f'    if (!dlopen("{path}", RTLD_NOW)) {{ std::printf("failed to load %s: %s\\n", "{path}", dlerror()); failures++; }}'
            for path in libraries
        )

    include_lines = "\n".join(
        f"#include <{name}>" if not name.startswith(("<", '"')) else f"#include {name}" for name in includes
    )

    with open(os.path.join(consumer, "main.cpp"), "w", encoding="utf-8") as handle:
        handle.write(
            CONSUMER_SOURCE.format(
                includes=include_lines,
                load_includes=load_includes,
                exercise=exercise,
                loads=loads,
            )
        )

    with open(os.path.join(consumer, "CMakeLists.txt"), "w", encoding="utf-8") as handle:
        # The only route to the dependency is the relocated prefix. Nothing points at the original
        # location, which no longer exists.
        handle.write(
            "cmake_minimum_required(VERSION 3.27)\n"
            "project(relocation_consumer LANGUAGES CXX)\n"
            f'list(PREPEND CMAKE_PREFIX_PATH "{install_dir.replace(os.sep, "/")}")\n'
            f"find_package({package} REQUIRED {'MODULE' if module else 'CONFIG'})\n"
            "add_executable(consumer main.cpp)\n"
            f"target_link_libraries(consumer PRIVATE {target})\n"
        )
    return consumer


def runtime_environment(install_dir: str):
    """The environment a consumer needs to load a dependency from a relocated tree.

    A linked executable is started by the loader, which finds shared libraries through the platform's
    search path -- not through the directory of the library it was linked against. For the check to
    be about relocation rather than about the loader, that search path is pointed at the relocated
    tree. It is never pointed anywhere near the original, which is part of what the check proves.
    """
    environment = dict(os.environ)
    directories = [
        path for name in ("bin", "lib", "lib64") for path in [os.path.join(install_dir, name)] if os.path.isdir(path)
    ]
    if not directories:
        return environment

    if os.name == "nt":
        variable = "PATH"
    elif sys.platform == "darwin":
        variable = "DYLD_LIBRARY_PATH"
    else:
        variable = "LD_LIBRARY_PATH"

    existing = environment.get(variable, "")
    environment[variable] = os.pathsep.join(directories + ([existing] if existing else []))
    return environment


def references(output: str, needle: str) -> list:
    """Lines that mention a path, for reporting where a reference was found."""
    return [line.strip()[:200] for line in output.splitlines() if needle in line]


def check(options) -> dict:
    install = os.path.abspath(options.install)
    if not os.path.isdir(install):
        return {"status": "error", "reason": f"no installed tree at {install}"}

    moved_aside = install + ".relocating"
    if os.path.exists(moved_aside):
        return {"status": "error", "reason": f"{moved_aside} already exists; a previous check did not finish"}

    # Discovered from the relocated copy, not from the original: naming the original path here would
    # make the consumer load from the location the check is trying to prove it does not need, and
    # would then be reported as a reference to it.
    libraries = []
    report = {
        "install": install,
        "package": options.package,
        "target": options.target,
        "shared_libraries": [],
        "steps": {},
    }

    work = options.work or tempfile.mkdtemp(prefix="rv-relocation-")
    os.makedirs(work, exist_ok=True)
    relocated = os.path.join(work, "relocated", "install")
    build = os.path.join(work, "build")

    try:
        # Move the tree aside first: the original path has to be empty for a reference to it to be
        # detectable, and renamed rather than deleted so it can always be put back.
        os.rename(install, moved_aside)
        os.makedirs(os.path.dirname(relocated), exist_ok=True)
        shutil.copytree(moved_aside, relocated, symlinks=True)
        report["steps"]["relocated"] = relocated
        libraries = shared_libraries(relocated)
        report["shared_libraries"] = [os.path.relpath(path, relocated) for path in libraries]

        consumer = write_consumer(
            work,
            relocated,
            options.package,
            options.target,
            options.include,
            options.exercise,
            libraries,
            options.module,
        )

        code, output = run(["cmake", "-S", consumer, "-B", build, "-DCMAKE_BUILD_TYPE=Release"])
        report["steps"]["configure"] = {"exit": code}
        if code != 0:
            report.update({"status": "failed", "stage": "configure", "output": output[-4000:]})
            return report

        code, output = run(["cmake", "--build", build, "--config", "Release"])
        report["steps"]["build"] = {"exit": code}
        if code != 0:
            report.update({"status": "failed", "stage": "build", "output": output[-4000:]})
            return report

        # A single-configuration generator writes the executable into the build directory; a
        # multi-configuration one (Visual Studio) writes it into a per-configuration subdirectory, so
        # search rather than assume.
        executables = []
        for root, _directories, files in os.walk(build):
            for name in files:
                if name in ("consumer", "consumer.exe"):
                    executables.append(os.path.join(root, name))
        executables.sort(key=lambda path: ("Release" not in path, path))
        if not executables:
            report.update({"status": "error", "reason": f"the consumer was not built under {build}"})
            return report
        executable = executables[0]

        code, output = run([executable], env=runtime_environment(relocated))
        report["steps"]["run"] = {"exit": code, "output": output[-2000:]}
        if code != 0:
            report.update({"status": "failed", "stage": "run", "output": output[-4000:]})
            return report

        # Nothing in what was built may point at the location the tree came from. The original path
        # does not exist while this runs, so a hit means the consumer or the dependency would look
        # there on a machine that has it, or fail where it does not.
        #
        # Both separator styles are searched for: CMake writes the path however the package config
        # wrote it, and a checker that only looked for the style it was given would miss a real
        # reference and report a dependency as relocatable when it is not.
        needles = {install, install.replace("\\", "/"), install.replace("/", "\\")}
        offenders = {}
        for root, _directories, files in os.walk(build):
            for name in files:
                path = os.path.join(root, name)
                try:
                    with open(path, "rb") as handle:
                        body = handle.read()
                except OSError:
                    continue
                for needle in needles:
                    if needle.encode("utf-8") in body:
                        offenders[os.path.relpath(path, build)] = references(
                            body.decode("utf-8", errors="replace"), needle
                        )[:3]
                        break
        if offenders:
            report.update({"status": "failed", "stage": "reference", "references": offenders})
            return report

        report["status"] = "relocatable"
        return report
    finally:
        if os.path.isdir(moved_aside) and not os.path.isdir(install):
            os.rename(moved_aside, install)
        elif os.path.isdir(moved_aside):
            # Both exist, which means the move back would lose something. Leave the copy in place and
            # say so loudly, rather than overwrite either.
            log(f"both {install} and {moved_aside} exist; left the original at {moved_aside}")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--install", required=True, help="the dependency's installed tree")
    parser.add_argument("--package", required=True, help="the CMake package name to find, e.g. Zlib")
    parser.add_argument("--target", required=True, help="the imported target to link, e.g. ZLIB::ZLIB")
    parser.add_argument(
        "--include",
        action="append",
        default=[],
        metavar="HEADER",
        help="a header to include in the consumer, so it can call into the dependency; repeatable",
    )
    parser.add_argument(
        "--exercise",
        default="",
        help="C++ statements that call into the dependency, so linking is not the only thing tested",
    )
    parser.add_argument(
        "--module",
        action="store_true",
        help="also search CMake's built-in Find modules, for a dependency that installs no CMake package config",
    )
    parser.add_argument("--work", default="", help="a directory to work in; a temporary one by default")
    parser.add_argument("--json", default="", help="write the result here as JSON")
    options = parser.parse_args(argv)

    if shutil.which("cmake") is None:
        log("cmake is not on PATH, so the relocation check cannot run")
        return 2

    report = check(options)
    report["dependency"] = os.path.basename(os.path.dirname(os.path.abspath(options.install)))

    if options.json:
        # The report is written even when the check could not run, so create its directory rather
        # than assuming the caller did.
        parent = os.path.dirname(os.path.abspath(options.json))
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(options.json, "w", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2, sort_keys=True)

    status = report["status"]
    if status == "relocatable":
        log(f"{report['dependency']}: relocatable")
        return 0
    if status == "error":
        log(f"{report['dependency']}: could not be checked: {report.get('reason')}")
        return 2

    log(f"{report['dependency']}: NOT relocatable (failed at {report.get('stage')})")
    for line in str(report.get("output", "")).splitlines()[-25:]:
        log(f"    {line}")
    for path, lines in (report.get("references") or {}).items():
        log(f"    {path} refers to the original location:")
        for line in lines:
            log(f"        {line}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
