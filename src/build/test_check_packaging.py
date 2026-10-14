#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# *****************************************************************************
# Copyright 2026 Autodesk, Inc. All rights reserved.
#
# SPDX-License-Identifier: Apache-2.0
#
# *****************************************************************************

"""Self-verifying tests for check_packaging.py.

Run directly:

    python3 src/build/test_check_packaging.py

The packaging check runs on full builds in CI, where a check that cannot fail would pass silently.
These tests build a real installed package -- a shared library and three programs named rv, rvio and
rvls that link it and answer -version -- two ways:

  relocatable   the programs find the library relative to themselves, as a staged RV does
  build-bound   the programs find the library only through an absolute path into the build
                directory, the shape of a package that still reaches back to where it was built

and require the checks to tell them apart: scan finds a reference to the build directory, run fails
once the build directory is hidden, and the fingerprints differ. Building requires a working C++
toolchain; without one the suite says so rather than passing quietly, and fails in CI.

Exits non-zero if any check fails.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "check_packaging.py")

FAILURES = []

PROJECT = """\
cmake_minimum_required(VERSION 3.27)
project(Packaged LANGUAGES CXX)
set(CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS ON)
add_library(packaged SHARED packaged.cpp)
foreach(program rv rvio rvls)
  add_executable(${{program}} main.cpp)
  target_link_libraries(${{program}} PRIVATE packaged)
  set_target_properties(${{program}} PROPERTIES INSTALL_RPATH "{rpath}" BUILD_WITH_INSTALL_RPATH OFF)
endforeach()
if(APPLE)
  set_target_properties(packaged PROPERTIES INSTALL_NAME_DIR "@rpath")
endif()
# On Windows the library goes beside the programs, which is how a Windows package carries it.
install(TARGETS packaged rv rvio rvls RUNTIME DESTINATION bin LIBRARY DESTINATION lib ARCHIVE DESTINATION lib)
"""

LIBRARY = 'extern "C" int packaged_value() { return 42; }\n'

MAIN = """\
#include <cstdio>
#include <cstring>
extern "C" int packaged_value();
int main(int argc, char** argv)
{
    if (argc > 1 && std::strcmp(argv[1], "-version") == 0)
    {
        std::printf("1.0.%d\\n", packaged_value());
        return 0;
    }
    return 1;
}
"""


def check(description: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"  ok   {description}")
    else:
        print(f"  FAIL {description}{(': ' + detail) if detail else ''}")
        FAILURES.append(description)


def build(work: str, name: str, rpath: str) -> tuple:
    """Build and install the fixture under <work>/<name>; returns (build directory, install prefix)."""
    source = os.path.join(work, name, "src")
    build_dir = os.path.join(work, name, "build")
    prefix = os.path.join(work, name, "prefix")
    os.makedirs(source)
    for file, body in (("CMakeLists.txt", PROJECT.format(rpath=rpath)), ("packaged.cpp", LIBRARY), ("main.cpp", MAIN)):
        with open(os.path.join(source, file), "w", encoding="utf-8") as handle:
            handle.write(body)
    for command in (
        ["cmake", "-S", source, "-B", build_dir, "-DCMAKE_BUILD_TYPE=Release", f"-DCMAKE_INSTALL_PREFIX={prefix}"],
        ["cmake", "--build", build_dir, "--config", "Release"],
        ["cmake", "--install", build_dir, "--config", "Release"],
    ):
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"could not build the fixture: {command}\n{result.stdout}\n{result.stderr}")
    return build_dir, prefix


def run(*arguments):
    result = subprocess.run([sys.executable, SCRIPT, *arguments], capture_output=True, text=True)
    return result.returncode, result.stdout + result.stderr


def main() -> int:
    if shutil.which("cmake") is None:
        print("cmake is not on PATH, so the packaging check could not be exercised")
        return 1 if os.environ.get("CI") else 0

    relative = "$ORIGIN/../lib" if sys.platform.startswith("linux") else "@loader_path/../lib"
    with tempfile.TemporaryDirectory() as work:
        try:
            _, relocatable = build(work, "relocatable", relative)
            # Its search path is the build directory, where the library sits on a single-configuration generator.
            bound_build, bound = build(work, "bound", os.path.join(work, "bound", "build").replace("\\", "/"))
        except RuntimeError as error:
            print(f"the fixture could not be built, so the packaging check could not be exercised:\n{error}")
            return 1 if os.environ.get("CI") else 0

        # The build-bound package finds its library through the build directory, as a program left with its build
        # tree's search path does: on Linux and macOS its rpath names only the build directory. On Windows the loader
        # searches beside the program and PATH instead, so the library is removed from the prefix and reached only
        # through PATH pointing into the build directory.
        if os.name == "nt":
            for name in os.listdir(os.path.join(bound, "bin")):
                if name.lower().endswith(".dll"):
                    os.remove(os.path.join(bound, "bin", name))
            os.environ["PATH"] = os.path.join(bound_build, "Release") + os.pathsep + os.environ["PATH"]

        print("scan")
        code, output = run("scan", relocatable, "--forbid", os.path.join(work, "relocatable", "build"))
        check("a relocatable package names neither its build directory nor the store", code == 0, output[-600:])
        planted = os.path.join(relocatable, "share", "planted.txt")
        os.makedirs(os.path.dirname(planted))
        with open(planted, "w", encoding="utf-8") as handle:
            handle.write(f"cache={os.path.join(work, 'store')}/entry\n")
        code, output = run("scan", relocatable, "--forbid", os.path.join(work, "store"))
        check("a file naming the store is reported", code == 1 and "planted.txt" in output, output[-600:])
        os.remove(planted)
        os.rmdir(os.path.dirname(planted))
        if os.name != "nt":
            code, output = run("scan", bound, "--forbid", bound_build)
            check("a program whose search path names the build directory is reported", code == 1, output[-600:])
            check(
                "the reference is labelled as a library search path", "[library search path]" in output, output[-600:]
            )

        print("run")
        code, output = run("run", relocatable, "--hide", os.path.join(work, "relocatable", "build"))
        check("a relocatable package runs with its build directory hidden", code == 0, output[-600:])
        check("all three programs ran", output.count("  ok   ") == 3, output[-600:])
        code, output = run("run", bound, "--hide", bound_build)
        check("a package that loads from its build directory fails once it is hidden", code == 1, output[-600:])
        check("the failure is put down to the hidden location", "depends on a hidden location" in output, output[-600:])
        check("the build directory is put back afterwards", os.path.isdir(bound_build))
        if os.name != "nt":
            # Linux packages start rv through a launcher script beside the real binary; the launcher is what is run.
            launcher = os.path.join(relocatable, "bin", "rvls")
            os.rename(launcher, launcher + ".bin")
            with open(launcher, "w", encoding="utf-8") as handle:
                handle.write('#!/bin/sh\nexec "$(dirname "$0")/rvls.bin" "$@"\n')
            os.chmod(launcher, 0o755)
            code, output = run("run", relocatable)
            check("a launcher script is found and run", code == 0 and output.count("  ok   ") == 3, output[-600:])

        empty = os.path.join(work, "empty")
        os.makedirs(empty)
        code, output = run("run", empty)
        check("a prefix without the programs is reported", code == 1 and "no rv executable" in output, output[-600:])

        print("fingerprint")
        moved = os.path.join(work, "moved")
        shutil.copytree(relocatable, moved, symlinks=True)
        left, right, other = (os.path.join(work, f"{name}.json") for name in ("left", "right", "other"))
        run("fingerprint", relocatable, "--out", left)
        run("fingerprint", moved, "--out", right)
        code, output = run("compare", left, right)
        check("the same package at two locations fingerprints the same", code == 0, output[-600:])
        with open(left, encoding="utf-8") as handle:
            facts = json.load(handle)
        program = next(key for key in facts if os.path.basename(key).split(".")[0] == "rv")
        check("the program's link facts are recorded", any(facts[program].values()), str(facts[program]))
        run("fingerprint", bound, "--out", other)
        code, output = run("compare", left, other)
        check("a package normalized differently fingerprints differently", code == 1, output[-600:])

    if FAILURES:
        print(f"\n{len(FAILURES)} check(s) failed:")
        for failure in FAILURES:
            print(f"  - {failure}")
        return 1
    print("\nall packaging checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
