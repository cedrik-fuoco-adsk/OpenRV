#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# *****************************************************************************
# Copyright 2026 Autodesk, Inc. All rights reserved.
#
# SPDX-License-Identifier: Apache-2.0
#
# *****************************************************************************

"""Check that staged and installed output is independent of the store and of the build directory.

    python3 src/build/check_packaging.py scan <tree> --forbid <directory> [--forbid <directory> ...]
    python3 src/build/check_packaging.py fingerprint <tree> --out <file.json>
    python3 src/build/check_packaging.py compare <left.json> <right.json>
    python3 src/build/check_packaging.py run <prefix> [--hide <directory> ...]

scan
    Fails if any file under the tree names one of the forbidden directories -- the store, the build
    directory -- in any spelling, as text or as a UTF-16 string. A staged or installed tree that does
    is not what was packaged: it still reaches back to where it was built.

fingerprint, compare
    Records what decides whether a staged tree works once moved: every file's relative path, and for
    each binary the names it is known by and the names and search paths it loads its dependencies
    with -- install name, rpaths and load commands on macOS, SONAME, RUNPATH and NEEDED on Linux, the
    imported DLLs on Windows. Two trees with equal fingerprints were normalized the same way, which is
    how a build that took a dependency from the store is shown to stage like one that built it in
    place. Absolute paths are recorded relative to the tree when they point into it, so the two trees
    need not be at the same location.

run
    Runs rv, rvio and rvls with -version from an install prefix, with the loader's search variables
    cleared and every --hide directory renamed aside for the duration, so that a library found only
    through the build directory or the store fails to load instead of passing. -version returns before
    any window is created, so no display is needed, while the loader still resolves every library each
    program links.

Each command exits 0 on success and 1, naming every problem, on failure.
"""

import argparse
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from check_relocation import find_references, spellings  # noqa: E402
from probe_artifact import detect_format, read_pe_imports  # noqa: E402

PROGRAMS = ("rv", "rvio", "rvls")

# The loader's search variables, which would otherwise let a library be found somewhere the package does not carry it.
LOADER_VARIABLES = ("LD_LIBRARY_PATH", "DYLD_LIBRARY_PATH", "DYLD_FALLBACK_LIBRARY_PATH", "DYLD_FRAMEWORK_PATH")


def all_spellings(directory: str) -> set:
    found = set()
    for variant in spellings(os.path.abspath(directory)):
        found.add(variant)
        forward = variant.replace("\\", "/")
        # The msys2 spelling of a Windows path, /D/a/..., which commands run through an msys2 shell are given.
        if re.match(r"^[A-Za-z]:/", forward):
            found.update({f"/{forward[0].lower()}{forward[2:]}", f"/{forward[0].upper()}{forward[2:]}"})
    return found


def reference_kind(path: str, needles) -> str:
    """Whether a file names a location in how it finds libraries, which changes what it loads, or only in some string."""
    reader = FACTS.get(detect_format(path))
    if reader is None:
        return "file content"
    facts = reader(path)
    loads = [value for values in facts.values() if isinstance(values, list) for value in values]
    if any(needle in value for value in loads for needle in needles):
        return "library search path"
    return "embedded string"


def cmd_scan(args) -> int:
    needles = set()
    for directory in args.forbid:
        needles |= all_spellings(directory)
    offenders = find_references(args.tree, sorted(needles, key=len, reverse=True))
    if offenders:
        print(f"{len(offenders)} file(s) under {args.tree} name a forbidden location:")
        for path, lines in sorted(offenders.items()):
            print(f"  - {path} [{reference_kind(os.path.join(args.tree, path), needles)}]: {lines[0][:160]}")
        return 1
    print(f"nothing under {args.tree} names {', '.join(args.forbid)}")
    return 0


def run_tool(command):
    try:
        return subprocess.run(command, capture_output=True, text=True, errors="replace", timeout=120).stdout
    except (OSError, subprocess.TimeoutExpired):
        return None


def macho_facts(path: str) -> dict:
    output = run_tool(["otool", "-l", path])
    if output is None:
        return {"unreadable": "otool"}
    facts = {"id": [], "rpath": [], "load": []}
    command = None
    for line in output.splitlines():
        line = line.strip()
        if line.startswith("cmd "):
            command = line.split()[1]
        elif line.startswith(("name ", "path ")):
            value = line.split(None, 1)[1].rsplit(" (offset", 1)[0]
            key = {"LC_ID_DYLIB": "id", "LC_RPATH": "rpath"}.get(
                command, "load" if command and "LOAD" in command else None
            )
            if key:
                facts[key].append(value)
    return facts


def elf_facts(path: str) -> dict:
    output = run_tool(["readelf", "-d", "-W", path])
    if output is None:
        return {"unreadable": "readelf"}
    facts = {"soname": [], "runpath": [], "needed": []}
    for line in output.splitlines():
        match = re.search(r"\((SONAME|RUNPATH|RPATH|NEEDED)\).*\[(.*)\]", line)
        if match:
            kind = {"RPATH": "runpath", "RUNPATH": "runpath"}.get(match.group(1), match.group(1).lower())
            facts[kind].append(match.group(2))
    return facts


def pe_facts(path: str) -> dict:
    imports = read_pe_imports(path)
    return {"unreadable": "PE headers"} if imports is None else {"imports": sorted(imports)}


FACTS = {"macho": macho_facts, "elf": elf_facts, "pe": pe_facts}


def fingerprint(tree: str) -> dict:
    tree = os.path.abspath(tree)
    roots = sorted(all_spellings(tree), key=len, reverse=True)

    def relative(value):
        for root in roots:
            value = value.replace(root, "<TREE>")
        return value

    files = {}
    for directory, _subdirectories, names in os.walk(tree):
        for name in names:
            path = os.path.join(directory, name)
            key = os.path.relpath(path, tree).replace("\\", "/")
            if os.path.islink(path):
                files[key] = {"link": relative(os.readlink(path))}
                continue
            reader = FACTS.get(detect_format(path))
            files[key] = (
                {
                    k: [relative(v) for v in values] if isinstance(values, list) else values
                    for k, values in reader(path).items()
                }
                if reader
                else {}
            )
    return files


def cmd_fingerprint(args) -> int:
    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(fingerprint(args.tree), handle, indent=1, sort_keys=True)
    print(f"fingerprint of {args.tree} written to {args.out}")
    return 0


def cmd_compare(args) -> int:
    with open(args.left, encoding="utf-8") as handle:
        left = json.load(handle)
    with open(args.right, encoding="utf-8") as handle:
        right = json.load(handle)
    problems = [f"only in {args.left}: {path}" for path in sorted(left.keys() - right.keys())]
    problems += [f"only in {args.right}: {path}" for path in sorted(right.keys() - left.keys())]
    problems += [
        f"{path} differs: {left[path]} != {right[path]}"
        for path in sorted(left.keys() & right.keys())
        if left[path] != right[path]
    ]
    if problems:
        print(f"the staged trees differ in {len(problems)} way(s):")
        for problem in problems[:200]:
            print(f"  - {problem}")
        return 1
    print(f"the staged trees are equivalent ({len(left)} files compared)")
    return 0


def find_programs(prefix: str) -> dict:
    """The programs a user runs, by name: on Linux these are launcher scripts beside the real binaries, and are what is run."""
    found = {}
    for directory, _subdirectories, names in os.walk(prefix):
        for name in names:
            stem = os.path.splitext(name)[0].lower() if name.lower().endswith(".exe") else name.lower()
            path = os.path.abspath(os.path.join(directory, name))
            if stem in PROGRAMS and stem not in found and (name.lower().endswith(".exe") or os.access(path, os.X_OK)):
                found[stem] = path
    return found


def run_program(path: str, environment: dict):
    """Exit code and output of <program> -version, or None and the reason it could not be started."""
    try:
        result = subprocess.run(
            [path, "-version"],
            capture_output=True,
            text=True,
            errors="replace",
            timeout=300,
            env=environment,
            cwd=os.path.dirname(path),
        )
        return result.returncode, (result.stdout + result.stderr).strip()
    except (OSError, subprocess.TimeoutExpired) as error:
        return None, str(error)


def cmd_run(args) -> int:
    programs = find_programs(args.prefix)
    problems = [f"no {name} executable under {args.prefix}" for name in PROGRAMS if name not in programs]

    environment = {key: value for key, value in os.environ.items() if key not in LOADER_VARIABLES}
    failed = {}
    hidden = []
    try:
        for directory in args.hide:
            if os.path.exists(directory):
                aside = directory.rstrip("/\\") + ".hidden-by-check-packaging"
                os.rename(directory, aside)
                hidden.append((aside, directory))
        for name, path in sorted(programs.items()):
            code, output = run_program(path, environment)
            if code == 0:
                print(f"  ok   {name} -version: {output.splitlines()[0] if output else '(no output)'}")
            else:
                failed[name] = (code, output)
    finally:
        for aside, directory in reversed(hidden):
            os.rename(aside, directory)

    # A program that fails with the build directory and the store hidden is run again with nothing hidden, so that one that
    # depends on them is told apart from one that fails wherever it is run.
    for name, (code, output) in sorted(failed.items()):
        retry, _ = run_program(programs[name], environment)
        cause = (
            "it also fails with nothing hidden"
            if retry != 0
            else "it runs with nothing hidden, so it depends on a hidden location"
        )
        status = f"exited {code}" if code is not None else "could not start"
        problems.append(f"{name} -version {status}; {cause}: {output[-600:]}")

    if problems:
        print(f"the installed programs did not all run from {args.prefix}:")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    print(f"rv, rvio and rvls run from {args.prefix} with {', '.join(args.hide) or 'nothing'} hidden")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)

    scan = commands.add_parser("scan", help="fail if a tree names a forbidden location")
    scan.add_argument("tree")
    scan.add_argument("--forbid", action="append", required=True)
    scan.set_defaults(func=cmd_scan)

    record = commands.add_parser("fingerprint", help="record what decides whether a staged tree relocates")
    record.add_argument("tree")
    record.add_argument("--out", required=True)
    record.set_defaults(func=cmd_fingerprint)

    compare = commands.add_parser("compare", help="compare two fingerprints")
    compare.add_argument("left")
    compare.add_argument("right")
    compare.set_defaults(func=cmd_compare)

    run = commands.add_parser("run", help="run the installed programs with the build and the store hidden")
    run.add_argument("prefix")
    run.add_argument("--hide", action="append", default=[])
    run.set_defaults(func=cmd_run)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
