#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# *****************************************************************************
# Copyright 2026 Autodesk, Inc. All rights reserved.
#
# SPDX-License-Identifier: Apache-2.0
#
# *****************************************************************************

"""Self-verifying tests for check_relocation.py.

Run directly:

    python3 src/build/test_check_relocation.py

Exits non-zero if any check fails.

A relocation check that cannot fail is worth nothing, so these tests build a real installed
dependency four ways:

  relocatable     an ordinary CMake install, whose export files use relative paths
  absolute        a config that hardcodes the install directory it was built at, which is the
                  shape a hand-written or badly generated package config takes
  referenced      a config that works from the new location but still names the old one, so the
                  build and the run both succeed and only a reference search can tell
  data            a library that links and loads from anywhere but reads a data file from the
                  location it was installed at -- the case a check that only links and runs would
                  pass on any machine that still has the original

All but the first must fail, each for the right reason: they are what the check is for. Building
requires a working C++ toolchain; without one the suite reports that it could not run rather than
passing quietly, and fails in CI, where a missing toolchain is a broken runner.
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "check_relocation.py")

FAILURES = []

PACKAGE = """\
cmake_minimum_required(VERSION 3.27)
project(Tiny LANGUAGES CXX VERSION 1.0.0)

# Without this a Windows DLL exports nothing, produces no import library, and cannot be linked --
# the fixture would then fail for a reason that has nothing to do with relocation.
set(CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS ON)
add_library(tiny SHARED tiny.cpp)
# Declared public, as a real dependency does: without it the export carries no include directory and
# a consumer cannot include the header even though the tree is relocatable.
target_include_directories(tiny PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}>
  $<INSTALL_INTERFACE:include>)
install(TARGETS tiny EXPORT TinyTargets
        RUNTIME DESTINATION bin
        LIBRARY DESTINATION lib
        ARCHIVE DESTINATION lib)
install(FILES tiny.h DESTINATION include)
install(EXPORT TinyTargets NAMESPACE Tiny:: FILE TinyTargets.cmake DESTINATION lib/cmake/Tiny)

include(CMakePackageConfigHelpers)
write_basic_package_version_file(
  "${CMAKE_CURRENT_BINARY_DIR}/TinyConfigVersion.cmake"
  VERSION 1.0.0
  COMPATIBILITY SameMajorVersion)
install(FILES "${CMAKE_CURRENT_BINARY_DIR}/TinyConfigVersion.cmake" DESTINATION lib/cmake/Tiny)
install(FILES TinyConfig.cmake DESTINATION lib/cmake/Tiny)
"""

CONFIG = """\
include("${CMAKE_CURRENT_LIST_DIR}/TinyTargets.cmake")
set(Tiny_VERSION "1.0.0")
"""

SOURCE = """\
extern "C" int tiny_value() { return 42; }
"""

HEADER = """\
#pragma once
extern "C" int tiny_value();
"""


def check(description: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"  ok   {description}")
    else:
        print(f"  FAIL {description}{(': ' + detail) if detail else ''}")
        FAILURES.append(description)


def build_package(work: str, mutation=None, package=PACKAGE, source_code=SOURCE, extra=()) -> str:
    """Build and install the fixture, optionally rewriting its package config or its sources."""
    source = os.path.join(work, "package-src")
    build = os.path.join(work, "package-build")
    install = os.path.join(work, "install")
    os.makedirs(source, exist_ok=True)

    for name, body in (
        ("CMakeLists.txt", package),
        ("tiny.cpp", source_code),
        ("tiny.h", HEADER),
        ("TinyConfig.cmake", CONFIG),
        *extra,
    ):
        with open(os.path.join(source, name), "w", encoding="utf-8") as handle:
            handle.write(body)

    if mutation is not None:
        with open(os.path.join(source, "TinyConfig.cmake"), "w", encoding="utf-8") as handle:
            handle.write(mutation(install))

    for command in (
        # The build type is set explicitly, as a build would: on a single-configuration generator an
        # unset one produces an export with no per-configuration location, and a consumer configured
        # for Release then finds nothing to link.
        ["cmake", "-S", source, "-B", build, "-DCMAKE_BUILD_TYPE=Release", f"-DCMAKE_INSTALL_PREFIX={install}"],
        ["cmake", "--build", build, "--config", "Release"],
        ["cmake", "--install", build, "--config", "Release"],
    ):
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"could not build the fixture: {command}\n{result.stdout}\n{result.stderr}")
    return install


def absolute_config(install: str) -> str:
    """A config that remembers where it was installed, as a generated one might."""
    # Forward slashes, as CMake writes paths: a Windows path written literally is a CMake escape
    # error, and the fixture would then fail for that rather than for the reference it holds.
    forward = install.replace("\\", "/")
    return (
        'include("${CMAKE_CURRENT_LIST_DIR}/TinyTargets.cmake")\n'
        f'set_property(TARGET Tiny::tiny PROPERTY INTERFACE_INCLUDE_DIRECTORIES "{forward}/include")\n'
        f'set(Tiny_VERSION "1.0.0")\n'
    )


# A library that reads its value from a data file at the location it was installed at, compiled in as
# an absolute path -- the shape of a dependency that finds its own resources by install prefix.
DATA_PACKAGE = (
    PACKAGE
    + """
target_compile_definitions(tiny PRIVATE "TINY_DATA=\\"${CMAKE_INSTALL_PREFIX}/share/tiny/value.txt\\"")
install(FILES value.txt DESTINATION share/tiny)
"""
)

DATA_SOURCE = """\
#include <cstdio>
extern "C" int tiny_value() {
    std::FILE* file = std::fopen(TINY_DATA, "r");
    if (!file) return -1;
    int value = 0;
    if (std::fscanf(file, "%d", &value) != 1) value = -2;
    std::fclose(file);
    return value;
}
"""


def referenced_config(install: str) -> str:
    """A config that works from anywhere but still names where it came from.

    Only a *recorded* path, not one used to find anything: pointing an imported target at the old
    directory makes the configure fail outright, which is the absolute fixture above. What is left is
    the shape that passes a build-and-run check and still breaks on a machine that lacks the
    original: a package config that remembers the prefix it was built at.
    """
    forward = install.replace("\\", "/")
    return (
        'include("${CMAKE_CURRENT_LIST_DIR}/TinyTargets.cmake")\n'
        f'set(Tiny_ORIGINAL_INSTALL "{forward}" CACHE INTERNAL "where this package was built")\n'
        'set(Tiny_VERSION "1.0.0")\n'
    )


def relocate(work: str, install: str):
    result = subprocess.run(
        [
            sys.executable,
            SCRIPT,
            "--install",
            install,
            "--package",
            "Tiny",
            "--target",
            "Tiny::tiny",
            "--include",
            "tiny.h",
            "--exercise",
            'if (tiny_value() != 42) { std::printf("unexpected value\\n"); return 1; }',
            "--work",
            os.path.join(work, "relocation"),
            "--json",
            os.path.join(work, "report.json"),
        ],
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout + result.stderr


def read_json(path: str) -> dict:
    import json

    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def test_a_relocatable_package_passes(work: str) -> None:
    print("an ordinarily installed package is relocatable")
    install = build_package(os.path.join(work, "relocatable"))
    code, output = relocate(os.path.join(work, "relocatable"), install)
    check("the check passes", code == 0, output[-1200:])
    check("the tree was put back", os.path.isdir(install) and not os.path.isdir(install + ".relocating"))
    report = read_json(os.path.join(work, "relocatable", "report.json"))
    check("the result says relocatable", report.get("status") == "relocatable", str(report.get("status")))
    check("the check ran the consumer", "run" in report.get("steps", {}), str(report.get("steps", {}).keys()))
    check(
        "the relocated copy was not the original path",
        install not in report.get("steps", {}).get("relocated", ""),
        str(report.get("steps", {}).get("relocated")),
    )


def test_a_package_that_remembers_where_it_was_built_fails(work: str) -> None:
    print("a package that hardcodes its install directory is not relocatable")
    install = build_package(os.path.join(work, "absolute"), absolute_config)
    code, output = relocate(os.path.join(work, "absolute"), install)
    check("the check fails", code == 1, f"exit {code}: {output[-800:]}")
    report = read_json(os.path.join(work, "absolute", "report.json"))
    check("the result says it is not relocatable", report.get("status") == "failed", str(report.get("status")))
    # Found in the relocated tree itself, before anything is built; were it missed there, the consumer's
    # configure would fail on the include directory that no longer exists.
    check(
        "the failure is attributed to a stage",
        report.get("stage") in ("tree-reference", "configure", "build"),
        str(report.get("stage")),
    )
    check(
        "the reference is reported with the file that holds it",
        any("TinyConfig.cmake" in path for path in (report.get("references") or {})),
        str(report.get("references")),
    )
    check("the tree was put back anyway", os.path.isdir(install) and not os.path.isdir(install + ".relocating"))


def test_a_package_that_merely_names_the_old_path_fails(work: str) -> None:
    print("a package that still names the old location is not relocatable")
    install = build_package(os.path.join(work, "referenced"), referenced_config)
    code, output = relocate(os.path.join(work, "referenced"), install)
    check("the check fails", code == 1, f"exit {code}: {output[-800:]}")
    report = read_json(os.path.join(work, "referenced", "report.json"))
    check("the result says it is not relocatable", report.get("status") == "failed", str(report.get("status")))
    # Nothing fails to build or run here -- the package works from its new location -- so this is the
    # case a check that only built and ran the consumer would accept.
    check(
        "the failure is a reference to the old location",
        report.get("stage") in ("tree-reference", "reference"),
        str(report.get("stage")),
    )
    check(
        "the reference is reported with the file that holds it",
        bool(report.get("references")),
        str(report.get("references")),
    )


def test_a_package_that_reads_from_the_old_location_fails(work: str) -> None:
    print("a package that links and loads but reads a data file from the old location is not relocatable")
    install = build_package(
        os.path.join(work, "data"),
        package=DATA_PACKAGE,
        source_code=DATA_SOURCE,
        extra=(("value.txt", "42\n"),),
    )
    code, output = relocate(os.path.join(work, "data"), install)
    check("the check fails", code == 1, f"exit {code}: {output[-800:]}")
    report = read_json(os.path.join(work, "data", "report.json"))
    check("the result says it is not relocatable", report.get("status") == "failed", str(report.get("status")))
    # The library names the data file's absolute location, which the tree search finds; were it missed,
    # the run fails, because the original location is moved aside while the consumer runs.
    check(
        "the failure is the library's reference, or the run that depends on it",
        report.get("stage") in ("tree-reference", "run"),
        str(report.get("stage")),
    )
    if report.get("stage") == "tree-reference":
        check(
            "the library is named as holding the reference",
            any(path.endswith(("libtiny.so", "libtiny.dylib", "tiny.dll")) for path in report.get("references", {})),
            str(report.get("references")),
        )
    check("the tree was put back", os.path.isdir(install) and not os.path.isdir(install + ".relocating"))


def test_a_missing_tree_is_an_error_not_a_pass(work: str) -> None:
    print("a tree that is not there is an error, not a silent pass")
    code, output = relocate(os.path.join(work, "missing"), os.path.join(work, "missing-install"))
    check("the check reports it could not run", code == 2, f"exit {code}: {output[-600:]}")
    check("the reason names the missing tree", "no installed tree" in output, output[-600:])


def main() -> int:
    # In CI a missing tool or toolchain is a broken runner, and a skip there would read as a pass.
    unavailable = 1 if os.environ.get("CI") else 0
    for tool in ("cmake",):
        if shutil.which(tool) is None:
            print(f"{tool} is not on PATH, so the relocation check cannot be tested")
            return unavailable

    print(f"relocation check ({HERE})")
    with tempfile.TemporaryDirectory() as work:
        try:
            build_package(os.path.join(work, "toolchain-probe"))
        except RuntimeError as error:
            print("no working C++ toolchain, so the relocation check cannot be tested")
            print(re.sub(r"\s+", " ", str(error))[:400])
            return unavailable

        test_a_relocatable_package_passes(work)
        test_a_package_that_remembers_where_it_was_built_fails(work)
        test_a_package_that_merely_names_the_old_path_fails(work)
        test_a_package_that_reads_from_the_old_location_fails(work)
        test_a_missing_tree_is_an_error_not_a_pass(work)

    print()
    if FAILURES:
        print(f"{len(FAILURES)} check(s) failed:")
        for failure in FAILURES:
            print(f"  - {failure}")
        return 1
    print("all relocation check checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
