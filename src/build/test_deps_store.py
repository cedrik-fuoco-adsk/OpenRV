#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# *****************************************************************************
# Copyright 2026 Autodesk, Inc. All rights reserved.
#
# SPDX-License-Identifier: Apache-2.0
#
# *****************************************************************************

"""Self-verifying tests for the identity-addressed dependency store.

Run directly:

    python3 src/build/test_deps_store.py

Exits non-zero if any check fails.

Most of what the store does cannot be checked without building dependencies, but its addressing and
its reuse can: which directory an eligible dependency's installed tree goes to, whether that follows
the identity, whether a dependency that has been published is found instead of built, and whether
opting out returns the tree to the build directory. Those are the parts where a mistake is silently
expensive -- a tree that keeps using a store after it was removed, a store entry that a later
configure consumes while it is half-written, or two identities sharing a slot -- so they are checked
here on every platform.

The harness includes the real options, identity, store and find macros in the order the real
configure uses them. Reconfiguring matters as much as configuring: the install root is derived, so
the only way to show that opting out works is to configure twice and look at the second configure.
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))

FAILURES = []

HARNESS = """\
cmake_minimum_required(VERSION 3.27)
project(deps_store_harness LANGUAGES CXX)

set(RV_SRC "{repo}")
list(APPEND CMAKE_MODULE_PATH "${{RV_SRC}}/cmake/defaults" "${{RV_SRC}}/cmake/macros")
set(PROJECT_SOURCE_DIR "${{RV_SRC}}")
# Defaulted rather than set: on a single-configuration generator CMake creates this cache entry as
# empty before this runs, so a non-FORCE set does nothing and the identity has no build configuration.
# Guarded rather than forced so a caller can still ask for another configuration, which the identity
# slot checks rely on.
if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE "Release" CACHE STRING "harness build type" FORCE)
endif()

if(WIN32)
  set(RV_TARGET_WINDOWS ON)
elseif(APPLE)
  set(RV_TARGET_DARWIN ON)
else()
  set(RV_TARGET_LINUX ON)
endif()

set(RV_VFX_PLATFORM "CY2025")
include(rv_options)

# What the real configure takes from cmake/defaults/CY2025.cmake.
set(HARNESS_QT_VERSION "6.5.3" CACHE STRING "")
set(RV_DEPS_PYTHON_VERSION "3.11.9")
set(RV_DEPS_QT_VERSION "${{HARNESS_QT_VERSION}}")

set(RV_BUILD_IDENTITY ON CACHE BOOL "")
set(RV_BUILD_MANIFEST OFF)
include(rv_build_identity)
RV_COMPUTE_BUILD_IDENTITY()

include(rv_deps_store)
RV_RESOLVE_DEPS_STORE()

# Two dependencies: one eligible, one not, so the tests can show the difference.
RV_DEPS_INSTALL_PATHS(RV_DEPS_ZLIB _zlib_install _zlib_staging)
RV_DEPS_INSTALL_PATHS(RV_DEPS_OIIO _oiio_install _oiio_staging)
message(STATUS "HARNESS hash=${{RV_BUILD_IDENTITY_HASH}}")
message(STATUS "HARNESS base=${{RV_DEPS_BASE_DIR}}")
message(STATUS "HARNESS install_root=${{RV_DEPS_INSTALL_ROOT}}")
message(STATUS "HARNESS entry=${{RV_DEPS_STORE_IDENTITY_DIR}}")
message(STATUS "HARNESS eligible_install=${{_zlib_install}}")
message(STATUS "HARNESS eligible_staging=${{_zlib_staging}}")
message(STATUS "HARNESS ineligible_install=${{_oiio_install}}")

# Consumption: with an entry in the store, the dependency is found rather than built.
if(HARNESS_FIND)
  set(RV_DEPS_VERSION_MATCH "MINIMUM")
  # The find macro delegates its wiring to macros defined beside the dependency variables, so the
  # harness includes that file too rather than only the finder.
  include(rv_create_std_deps_vars)
  include(rv_find_dependency)
  RV_FIND_DEPENDENCY(TARGET RV_DEPS_ZLIB PACKAGE Zlib VERSION 1.3.1)
  message(STATUS "HARNESS found=${{RV_DEPS_ZLIB_FOUND}}")
endif()
"""

VALUE_RE = {
    name: re.compile(rf"^--\s+HARNESS {name}=(.*)$", re.MULTILINE)
    for name in (
        "hash",
        "base",
        "install_root",
        "entry",
        "eligible_install",
        "eligible_staging",
        "ineligible_install",
        "found",
    )
}


def check(description: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"  ok   {description}")
    else:
        print(f"  FAIL {description}{(': ' + detail) if detail else ''}")
        FAILURES.append(description)


def value(name: str, output: str) -> str:
    match = VALUE_RE[name].search(output)
    return match.group(1).strip() if match else ""


def normalized_path(text: str) -> str:
    """Compare paths without caring how they were written.

    CMake joins a value given on the command line with its own separator, so a store passed as
    ``C:\\tmp\\store`` comes back as ``C:\\tmp\\store/90ee...``; and on Windows a temporary directory
    can arrive in 8.3 form (``RUNNER~1``) while CMake resolves it to the long name. Both are the same
    directory, so comparing the strings as given compares spelling rather than location.
    """
    return os.path.normcase(os.path.realpath(text.strip()))


def flattened(text: str) -> str:
    """Collapse whitespace, because CMake wraps MESSAGE text at the terminal width."""
    return re.sub(r"\s+", " ", text)


def configure(source: str, build: str, *definitions):
    result = subprocess.run(["cmake", "-S", source, "-B", build, *definitions], capture_output=True, text=True)
    return result.returncode, result.stdout + result.stderr


def package_config(store_entry: str) -> str:
    """A minimal installed package, as a dependency build would leave in the store."""
    install = os.path.join(store_entry, "RV_DEPS_ZLIB", "install")
    # Written into a CMake file, where a backslash is an escape character, so the paths are
    # normalized to forward slashes: a Windows path written literally corrupts the config file.
    cmake_install = install.replace("\\", "/")
    os.makedirs(os.path.join(install, "include"), exist_ok=True)
    os.makedirs(os.path.join(install, "lib", "cmake", "Zlib"), exist_ok=True)
    with open(os.path.join(install, "include", "zlib.h"), "w", encoding="utf-8") as handle:
        handle.write("/* stored zlib */\n")
    with open(os.path.join(install, "lib", "libz.so"), "w", encoding="utf-8") as handle:
        handle.write("# stored zlib library\n")
    with open(os.path.join(install, "lib", "cmake", "Zlib", "ZlibConfig.cmake"), "w", encoding="utf-8") as handle:
        handle.write(
            'set(Zlib_VERSION "1.3.1")\n'
            "if(NOT TARGET ZLIB::ZLIB)\n"
            "  add_library(ZLIB::ZLIB SHARED IMPORTED)\n"
            f'  set_target_properties(ZLIB::ZLIB PROPERTIES IMPORTED_LOCATION "{cmake_install}/lib/libz.so")\n'
            f'  set_target_properties(ZLIB::ZLIB PROPERTIES INTERFACE_INCLUDE_DIRECTORIES "{cmake_install}/include")\n'
            "endif()\n"
        )
    # The publish marker, which is what distinguishes a published entry from a directory that merely
    # exists: RV's configure creates the install directory for every dependency, so existence alone
    # is not evidence that a dependency was ever installed there.
    with open(os.path.join(store_entry, "RV_DEPS_ZLIB", ".published"), "w", encoding="utf-8") as handle:
        handle.write("")

    # A version file, which every real dependency install has. Without it a find_package asking for
    # a version does not find the package at all, so the fixture would test the absence of this file
    # rather than the store.
    with open(
        os.path.join(install, "lib", "cmake", "Zlib", "ZlibConfigVersion.cmake"), "w", encoding="utf-8"
    ) as handle:
        handle.write(
            'set(PACKAGE_VERSION "1.3.1")\n'
            "if(PACKAGE_VERSION VERSION_LESS PACKAGE_FIND_VERSION)\n"
            "  set(PACKAGE_VERSION_COMPATIBLE FALSE)\n"
            "else()\n"
            "  set(PACKAGE_VERSION_COMPATIBLE TRUE)\n"
            "  if(PACKAGE_FIND_VERSION STREQUAL PACKAGE_VERSION)\n"
            "    set(PACKAGE_VERSION_EXACT TRUE)\n"
            "  endif()\n"
            "endif()\n"
        )
    return install


def test_default_configure_is_unchanged(directory: str, source: str) -> None:
    print("without a store, installed trees stay in the build directory")
    build = os.path.join(directory, "default")
    code, output = configure(source, build)
    check("the configure succeeds", code == 0, output[-800:])
    check(
        "the install root is the build directory",
        normalized_path(value("install_root", output)) == normalized_path(build),
        f"got {value('install_root', output)!r}",
    )
    check(
        "an eligible dependency still installs locally when there is no store",
        normalized_path(value("eligible_install", output))
        == normalized_path(os.path.join(build, "RV_DEPS_ZLIB", "install")),
        f"got {value('eligible_install', output)!r}",
    )
    check("no store entry is used", value("entry", output) == "", value("entry", output))


def test_store_places_only_eligible_dependencies(directory: str, source: str) -> None:
    print("with a store, only the eligible dependency's installed tree moves")
    build = os.path.join(directory, "store-build")
    store = os.path.join(directory, "store")
    code, output = configure(source, build, f"-DRV_DEPS_STORE={store}", "-DRV_DEPS_STORE_ELIGIBLE=RV_DEPS_ZLIB")
    check("the configure succeeds", code == 0, output[-800:])

    entry = value("entry", output)
    digest = value("hash", output).replace("sha256:", "")
    check(
        "the store entry is the identity", normalized_path(entry) == normalized_path(os.path.join(store, digest)), entry
    )
    check(
        "the eligible dependency installs into the store",
        normalized_path(value("eligible_install", output))
        == normalized_path(os.path.join(entry, "RV_DEPS_ZLIB", "install")),
        value("eligible_install", output),
    )
    check(
        "the ineligible dependency installs in the build directory",
        normalized_path(value("ineligible_install", output))
        == normalized_path(os.path.join(build, "RV_DEPS_OIIO", "install")),
        value("ineligible_install", output),
    )
    check(
        "the staged path is not the published path",
        normalized_path(value("eligible_staging", output)) != normalized_path(value("eligible_install", output)),
        "a stored dependency would be published in place, so a half-written tree would be consumable",
    )
    check("the store directory was created", os.path.isdir(store), store)
    check("the eligible dependency is named in the report", "RV_DEPS_ZLIB" in output, output[-600:])


def test_an_empty_eligibility_list_places_nothing(directory: str, source: str) -> None:
    print("a store with nothing eligible changes nothing about where dependencies go")
    build = os.path.join(directory, "empty-eligibility")
    store = os.path.join(directory, "empty-store")
    # The list is emptied explicitly: the default names the dependencies that have passed the
    # relocation gate, so "nothing eligible" is a premise of this check rather than the default.
    code, output = configure(source, build, f"-DRV_DEPS_STORE={store}", "-DRV_DEPS_STORE_ELIGIBLE=")
    check("the configure succeeds", code == 0, output[-800:])
    check(
        "the eligible dependency is placed in the build directory anyway",
        normalized_path(value("eligible_install", output)).startswith(normalized_path(build)),
        value("eligible_install", output),
    )
    check("the report says nothing is eligible", "none, so no dependency is placed" in flattened(output), output[-600:])


def test_one_store_holds_one_slot_per_identity(directory: str, source: str) -> None:
    print("one store holds one slot per identity")
    store = os.path.join(directory, "shared")
    arguments = (f"-DRV_DEPS_STORE={store}", "-DRV_DEPS_STORE_ELIGIBLE=RV_DEPS_ZLIB")

    _, release = configure(source, os.path.join(directory, "shared-release"), "-DCMAKE_BUILD_TYPE=Release", *arguments)
    _, debug = configure(source, os.path.join(directory, "shared-debug"), "-DCMAKE_BUILD_TYPE=Debug", *arguments)
    check("a Release and a Debug configuration get different entries", value("entry", release) != value("entry", debug))

    # The same identity in another build directory must resolve to the same entry: that is what makes
    # the artifacts reusable rather than merely moved.
    _, second = configure(
        source, os.path.join(directory, "shared-release-second"), "-DCMAKE_BUILD_TYPE=Release", *arguments
    )
    check(
        "a second build directory with the same identity shares the entry",
        normalized_path(value("entry", second)) == normalized_path(value("entry", release)),
        f"{value('entry', second)!r} != {value('entry', release)!r}",
    )


def test_a_published_dependency_is_found_not_built(directory: str, source: str) -> None:
    print("a dependency published for this identity is found in the store")
    store = os.path.join(directory, "consume-store")
    arguments = (f"-DRV_DEPS_STORE={store}", "-DRV_DEPS_STORE_ELIGIBLE=RV_DEPS_ZLIB", "-DHARNESS_FIND=ON")

    # Nothing published yet: the store must not be what makes this succeed.
    _, empty = configure(source, os.path.join(directory, "consume-empty"), *arguments)
    check("the configure succeeds", "HARNESS found=" in empty, empty[-600:])
    check("an unpublished dependency is not found", value("found", empty) == "FALSE", value("found", empty))

    # Publish an entry by hand, as a dependency build would leave it, and find it.
    entry = None
    _, first = configure(source, os.path.join(directory, "consume-first"), *arguments)
    entry = value("entry", first)
    check("the entry was resolved", entry != "", first[-600:])
    package_config(entry)

    _, published = configure(source, os.path.join(directory, "consume-published"), *arguments)
    check("the published dependency is found", value("found", published) == "TRUE", value("found", published))
    check(
        "the report says it came from the store",
        "found in the dependency store" in flattened(published),
        published[-600:],
    )

    # An entry that is staged but not yet published must not be consumable: this is what an
    # interrupted install leaves behind, and finding it would mean using a half-written dependency.
    staged_only = os.path.join(directory, "consume-staged-only")
    staged_store = os.path.join(directory, "consume-staged-store")
    staged_args = (f"-DRV_DEPS_STORE={staged_store}", "-DRV_DEPS_STORE_ELIGIBLE=RV_DEPS_ZLIB", "-DHARNESS_FIND=ON")
    _, staged_first = configure(source, staged_only, *staged_args)
    staged_entry = value("entry", staged_first)
    staging = os.path.join(staged_entry, ".publishing", "RV_DEPS_ZLIB", "install")
    os.makedirs(os.path.join(staging, "lib", "cmake", "Zlib"), exist_ok=True)
    with open(os.path.join(staging, "lib", "cmake", "Zlib", "ZlibConfig.cmake"), "w", encoding="utf-8") as handle:
        handle.write('set(Zlib_VERSION "1.3.1")\n')
    _, staged_again = configure(source, os.path.join(directory, "consume-staged-again"), *staged_args)
    check(
        "a staged but unpublished entry is not consumed",
        value("found", staged_again) == "FALSE",
        value("found", staged_again),
    )

    # An ineligible dependency must not be taken from the store even if something is there.
    _, ineligible = configure(
        source,
        os.path.join(directory, "consume-ineligible"),
        f"-DRV_DEPS_STORE={store}",
        "-DRV_DEPS_STORE_ELIGIBLE=RV_DEPS_OIIO",
        "-DHARNESS_FIND=ON",
    )
    check(
        "an ineligible dependency is not taken from the store",
        value("found", ineligible) == "FALSE",
        value("found", ineligible),
    )


def test_opting_out_returns_to_the_build_directory(directory: str, source: str) -> None:
    print("removing the store returns a configured tree to the build directory")
    build = os.path.join(directory, "optout")
    store = os.path.join(directory, "optout-store")

    _, with_store = configure(source, build, f"-DRV_DEPS_STORE={store}", "-DRV_DEPS_STORE_ELIGIBLE=RV_DEPS_ZLIB")
    check(
        "the first configure uses the store",
        normalized_path(value("entry", with_store)).startswith(normalized_path(store)),
    )

    # The cache still holds the store settings. Re-deriving is what makes this a real opt-out rather
    # than a switch that only applies to trees that never saw a store.
    _, without_store = configure(source, build, "-DRV_DEPS_STORE=", "-DRV_DEPS_STORE_ELIGIBLE=")
    check("the entry is gone", value("entry", without_store) == "", value("entry", without_store))
    check(
        "the eligible dependency installs in the build directory again",
        normalized_path(value("eligible_install", without_store))
        == normalized_path(os.path.join(build, "RV_DEPS_ZLIB", "install")),
        value("eligible_install", without_store),
    )


def test_the_store_requires_an_identity(directory: str, source: str) -> None:
    print("a store without an identity fails, naming the reason")
    build = os.path.join(directory, "no-identity")
    store = os.path.join(directory, "no-identity-store")
    code, output = configure(source, build, f"-DRV_DEPS_STORE={store}", "-DRV_BUILD_IDENTITY=OFF")
    check("the configure fails", code != 0, "a store was configured without an identity")
    check("the failure names the store", "RV_DEPS_STORE" in flattened(output), output[-800:])
    check("the failure names the identity requirement", "identity" in flattened(output), output[-800:])


def test_publishing_is_atomic_and_survives_a_race(directory: str) -> None:
    print("publishing appears complete or not at all")
    script = os.path.join(REPO, "cmake", "macros", "rv_store_publish.cmake")
    root = os.path.join(directory, "publish")

    def publish(staging: str, final: str):
        result = subprocess.run(
            ["cmake", f"-DRV_PUBLISH_STAGING={staging}", f"-DRV_PUBLISH_FINAL={final}", "-P", script],
            capture_output=True,
            text=True,
        )
        return result.returncode, result.stdout + result.stderr

    # A staged tree is moved into place.
    staging = os.path.join(root, "staging", "install")
    final = os.path.join(root, "entry", "RV_DEPS_ZLIB", "install")
    os.makedirs(staging)
    with open(os.path.join(staging, "marker"), "w", encoding="utf-8") as handle:
        handle.write("installed\n")
    code, output = publish(staging, final)
    check("a staged tree is published", code == 0, output[-600:])
    check("the published tree is in place", os.path.isfile(os.path.join(final, "marker")), final)
    check("the staging directory is gone", not os.path.exists(staging), staging)

    # Publishing again with nothing staged is success, which is what makes a repeated install safe.
    code, output = publish(staging, final)
    check("publishing with nothing staged and the entry present succeeds", code == 0, output[-600:])

    # An entry that is already published wins, and the staged copy is discarded rather than applied.
    second_staging = os.path.join(root, "staging2", "install")
    os.makedirs(second_staging)
    with open(os.path.join(second_staging, "marker"), "w", encoding="utf-8") as handle:
        handle.write("different\n")
    code, output = publish(second_staging, final)
    check("an already published entry is not replaced", code == 0, output[-600:])
    with open(os.path.join(final, "marker"), encoding="utf-8") as handle:
        check("the published content is unchanged", handle.read().strip() == "installed")

    # Nothing staged and nothing published is a failure, not a silent success: it means the install
    # produced nothing, and reporting success would publish an entry that does not exist.
    code, output = publish(os.path.join(root, "missing"), os.path.join(root, "missing-final"))
    check("nothing staged and nothing published fails", code != 0, f"exit {code}")
    check("the failure says nothing was staged", "nothing was staged" in flattened(output), output[-600:])


def main() -> int:
    if shutil.which("cmake") is None:
        print("cmake is not on PATH, so the dependency store cannot be checked")
        return 0

    print(f"dependency store ({REPO})")
    with tempfile.TemporaryDirectory() as directory:
        source = os.path.join(directory, "harness")
        os.makedirs(source)
        with open(os.path.join(source, "CMakeLists.txt"), "w", encoding="utf-8") as handle:
            handle.write(HARNESS.format(repo=REPO.replace("\\", "/")))

        test_default_configure_is_unchanged(directory, source)
        test_store_places_only_eligible_dependencies(directory, source)
        test_an_empty_eligibility_list_places_nothing(directory, source)
        test_one_store_holds_one_slot_per_identity(directory, source)
        test_a_published_dependency_is_found_not_built(directory, source)
        test_opting_out_returns_to_the_build_directory(directory, source)
        test_the_store_requires_an_identity(directory, source)
        test_publishing_is_atomic_and_survives_a_race(directory)

    print()
    if FAILURES:
        print(f"{len(FAILURES)} check(s) failed:")
        for failure in FAILURES:
            print(f"  - {failure}")
        return 1
    print("all dependency store checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
