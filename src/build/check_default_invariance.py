#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# *****************************************************************************
# Copyright 2026 Autodesk, Inc. All rights reserved.
#
# SPDX-License-Identifier: Apache-2.0
#
# *****************************************************************************

"""Check that a default configure generates the same build as a baseline.

    python3 src/build/check_default_invariance.py <baseline build dir> <candidate build dir>

Both trees are configured from different checkouts with the same options and the same generator,
Ninja or Visual Studio. The build identity, manifest and store add configure-time reporting and cache options, and
must change nothing that is built, where any dependency is placed, or what is staged and installed.
That is checked on what CMake generated rather than on a finished build, because the generated build
decides all of it:

- build.ninja and CMakeFiles/rules.ninja, or every .vcxproj and .sln: every dependency's
  ExternalProject steps and commands, including its install directory, and every staging and
  packaging rule.
- ExternalProject's generated step scripts (``*-prefix/tmp`` and the stamp directories).
- Every cmake_install.cmake: the install layout.
- CMakeCache.txt: an entry may exist only in the candidate if it is one of the variables this change
  adds, and no entry present in both may differ.

cmake/install/CMakeLists.txt forwards every non-empty RV_* variable into the install script with SET(),
so the variables this change adds appear there too. No install script reads them, and those forwarded
SET() lines are the one difference allowed in a cmake_install.cmake.

The source and build directories are replaced by placeholders before comparing, as are the values
that differ between any two checkouts: the git hash compiled into the application, what git reports
about the checkout (RV_GIT_*, including a branch that is HEAD in a detached worktree), and the names CMake
derives from absolute paths (Ninja depfiles, Visual Studio project GUIDs and rule directories). What re-runs CMake when one
of its input files changes is ignored -- the RERUN_CMAKE statement of build.ninja, ZERO_CHECK and each
project's CMakeLists.txt custom build -- because it names the macro files this change adds and is not
part of what is built.

Exits 0 when the two are equivalent and 1, listing every difference, when they are not.
"""

import argparse
import difflib
import os
import re
import sys

# Variables this change adds. Each is an option or bookkeeping value for the identity, the manifest, the
# probe or the store; none decides what a default build builds.
OWN_VARIABLE = (
    r"(?:RV_BUILD_IDENTITY\w*|RV_BUILD_MANIFEST\w*|RV_BUILD_PYTHON\w*|RV_DEPS_PROBE_\w+|RV_PROBE_\w+"
    r"|RV_DEPS_STORE\w*|RV_DEPS_INSTALL_SCRIPT|RV_CONAN_\w+_FILE|RV_DEPS_QT_FOUND_VERSION)"
)
OWN_CACHE_ENTRY = re.compile(rf"^{OWN_VARIABLE}$")
# What git says about the checkout -- its commit and its branch, which is HEAD in a detached worktree -- differs between any two
# checkouts and is recorded, not built from.
GIT_DESCRIPTION = r"RV_GIT_\w+"
FORWARDED = 'if\\(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT\\)\\n  SET\\({} [^\\n]*\\)\\nendif\\(\\)\\n\\n'
FORWARDED_OWN_VARIABLE = re.compile(FORWARDED.format(OWN_VARIABLE))
FORWARDED_GIT_DESCRIPTION = re.compile(FORWARDED.format(GIT_DESCRIPTION))

# Cache entries that differ between any two configures, or any two commits, and say nothing about the build.
VOLATILE_CACHE_ENTRIES = re.compile(
    rf"^(CMAKE_CACHEFILE_DIR|CMAKE_HOME_DIRECTORY|\w+_BINARY_DIR|\w+_SOURCE_DIR|{GIT_DESCRIPTION})$"
)
VOLATILE_VALUES = [
    (re.compile(r"CMakeFiles([/\\])d\1[0-9a-f]{64}\.d"), r"CMakeFiles\1d\1<DEPFILE>.d"),
    (re.compile(r"CMakeFiles([/\\])[0-9a-f]{32}\1"), r"CMakeFiles\1<HASH>\1"),
    (re.compile(r"\{[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}\}"), "{<GUID>}"),
]
REGENERATION_CUSTOM_BUILD = re.compile(r'<CustomBuild Include="[^"]*CMakeLists\.txt">.*?</CustomBuild>', re.S)

CACHE_LINE = re.compile(r"^([^#/][^:=]*):([A-Z]+)=(.*)$")


def read_text(path: str) -> str:
    with open(path, encoding="utf-8", errors="replace") as handle:
        return handle.read()


def spellings(directory: str):
    """Every spelling of a directory a generated file may use, longest first so none is half-replaced."""
    candidates = set()
    for value in (directory, os.path.realpath(directory)):
        value = os.path.abspath(value)
        candidates.add(value)
        candidates.add(value.replace("\\", "/"))
        if os.name == "nt":
            candidates.add(value.lower())
            candidates.add(value.replace("\\", "/").lower())
        # The msys2 spelling, /D/a/..., which commands run through an msys2 shell are given.
        forward = value.replace("\\", "/")
        if re.match(r"^[A-Za-z]:/", forward):
            for drive in (forward[0].upper(), forward[0].lower()):
                candidates.add(f"/{drive}{forward[2:]}")
    return sorted(candidates, key=len, reverse=True)


def cache_value(build: str, key: str) -> str:
    match = re.search(rf"^{key}:[A-Z]+=(.*)$", read_text(os.path.join(build, "CMakeCache.txt")), re.M)
    return match.group(1) if match else ""


def source_of(build: str) -> str:
    source = cache_value(build, "CMAKE_HOME_DIRECTORY")
    if not source:
        raise SystemExit(f"{build}: no CMAKE_HOME_DIRECTORY in CMakeCache.txt; is this a configured build directory?")
    return source


def normalizer(build: str, other: str):
    # Both trees' directories are replaced in both trees' files: an input both use, such as a Qt installed inside one
    # checkout, is then the same placeholder in each rather than a placeholder in one and a path in the other.
    replacements = []
    for tree in (build, other):
        replacements += [(s, "<BUILD>") for s in spellings(tree)] + [
            (s, "<SOURCE>") for s in spellings(source_of(tree))
        ]
    # The commit each tree was configured from is compiled into the application and recorded for the install.
    commit = cache_value(build, "RV_GIT_COMMIT_SHORT_HASH")
    if commit:
        replacements.append((commit, "<COMMIT>"))
    # The build directory is usually inside the source directory, so it is replaced first.
    replacements.sort(key=lambda pair: len(pair[0]), reverse=True)

    def normalize(text: str) -> str:
        for old, new in replacements:
            text = text.replace(old, new)
        for pattern, new in VOLATILE_VALUES:
            text = pattern.sub(new, text)
        return text

    return normalize


def ninja_statements(text: str):
    """Ninja statements with their $-newline continuations joined."""
    return re.sub(r"\$\n\s*", " ", text).split("\n")


def without_regeneration(text: str) -> str:
    kept = []
    for statement in ninja_statements(text):
        if "RERUN_CMAKE" in statement:
            continue
        # The phony statement listing the CMake inputs, so a deleted input does not break the build.
        if statement.startswith("build ") and statement.rstrip().endswith(": phony") and "<SOURCE>/cmake/" in statement:
            continue
        kept.append(statement)
    return "\n".join(kept)


def generated_files(build: str):
    """Relative paths of the generated files compared, excluding fetched sources and dependency builds."""
    found = {"build.ninja", os.path.join("CMakeFiles", "rules.ninja")}
    for directory, subdirectories, files in os.walk(build):
        relative = os.path.relpath(directory, build)
        # Sources fetched at configure, dependency sub-builds and CMake's own scratch space are not generated by
        # this project's configure, or are generated identically from it.
        in_dependency = os.path.basename(directory).startswith("RV_DEPS_")
        subdirectories[:] = [
            d
            for d in subdirectories
            if d not in ("CMakeFiles", "_deps", "RV_DEPS_DOWNLOAD")
            and not (in_dependency and d in ("src", "build", "install"))
        ]
        for name in files:
            path = os.path.normpath(os.path.join(relative, name))
            if name == "cmake_install.cmake" or name.endswith(".sln"):
                found.add(path)
            elif name.endswith(".vcxproj") and name != "ZERO_CHECK.vcxproj":
                found.add(path)
            elif re.search(r"-prefix[/\\](tmp|src[/\\][^/\\]+-stamp)([/\\]|$)", path) and not name.endswith(
                (".rule", "-done", "-download", "-update", "-patch", "-configure", "-build", "-install", "-mkdir")
            ):
                found.add(path)
    return {path for path in found if os.path.isfile(os.path.join(build, path))}


def read_cache(build: str, normalize):
    entries = {}
    for line in read_text(os.path.join(build, "CMakeCache.txt")).splitlines():
        match = CACHE_LINE.match(line)
        if match:
            key, kind, value = match.groups()
            entries[key] = (kind, normalize(value))
    return entries


def compare(baseline: str, candidate: str) -> list:
    problems = []
    normalize_baseline = normalizer(baseline, candidate)
    normalize_candidate = normalizer(candidate, baseline)

    baseline_files = generated_files(baseline)
    candidate_files = generated_files(candidate)
    for path in sorted(baseline_files - candidate_files):
        problems.append(f"generated only by the baseline: {path}")
    for path in sorted(candidate_files - baseline_files):
        problems.append(f"generated only by the candidate: {path}")

    for path in sorted(baseline_files & candidate_files):
        left = normalize_baseline(read_text(os.path.join(baseline, path)))
        right = normalize_candidate(read_text(os.path.join(candidate, path)))
        if path == "build.ninja":
            left, right = without_regeneration(left), without_regeneration(right)
        elif path.endswith(".vcxproj"):
            left, right = REGENERATION_CUSTOM_BUILD.sub("", left), REGENERATION_CUSTOM_BUILD.sub("", right)
        elif os.path.basename(path) == "cmake_install.cmake":
            left = FORWARDED_GIT_DESCRIPTION.sub("", left)
            right = FORWARDED_GIT_DESCRIPTION.sub("", FORWARDED_OWN_VARIABLE.sub("", right))
        if left != right:
            diff = difflib.unified_diff(
                left.splitlines(), right.splitlines(), f"baseline/{path}", f"candidate/{path}", n=0, lineterm=""
            )
            problems.append(f"{path} differs:\n" + "\n".join(list(diff)[:40]))

    baseline_cache = read_cache(baseline, normalize_baseline)
    candidate_cache = read_cache(candidate, normalize_candidate)
    for key in sorted(baseline_cache.keys() - candidate_cache.keys()):
        problems.append(f"cache entry removed: {key}")
    for key in sorted(candidate_cache.keys() - baseline_cache.keys()):
        if not OWN_CACHE_ENTRY.match(key):
            problems.append(
                f"cache entry added that is not one of this change's options: {key}={candidate_cache[key][1]}"
            )
    for key in sorted(baseline_cache.keys() & candidate_cache.keys()):
        if VOLATILE_CACHE_ENTRIES.match(key):
            continue
        if baseline_cache[key] != candidate_cache[key]:
            problems.append(f"cache entry differs: {key}: {baseline_cache[key][1]!r} != {candidate_cache[key][1]!r}")

    return problems, len(baseline_files & candidate_files)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("baseline", help="build directory configured from the baseline checkout")
    parser.add_argument("candidate", help="build directory configured from the candidate checkout")
    args = parser.parse_args()

    problems, compared = compare(args.baseline, args.candidate)
    if problems:
        print(f"the default configure differs from the baseline in {len(problems)} way(s):")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    print(
        f"the default configure generates the same build as the baseline ({compared} generated files and the cache compared)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
