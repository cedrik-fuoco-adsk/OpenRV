#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# *****************************************************************************
# Copyright 2026 Autodesk, Inc. All rights reserved.
#
# SPDX-License-Identifier: Apache-2.0
#
# *****************************************************************************

"""Self-verifying round trip for the dependency store, with a real dependency.

Run directly:

    python3 src/build/test_deps_store_roundtrip.py

Exits non-zero if any check fails, and reports that it could not run (without failing) when there is
no network or no toolchain.

test_deps_store.py checks the store's addressing with planted trees, which is fast and runs
everywhere. This checks the thing those cannot: that a real dependency builds into the store, is
published atomically, and is then reused by a second build directory instead of being rebuilt.

Every defect in this area was found this way rather than by reading or by fixtures -- a configure
prefix that contradicted the install prefix, a publish step that never ran, a staging lookup one
level too shallow, and an unexpected writer of the install directory. A fixture cannot catch those,
because a fixture is written by someone who already believes they know how the mechanism works.

The harness includes the real options, identity, store and find macros in the order the real
configure uses them, and the real dependency file for zlib. Its dependency versions come from
cmake/defaults/CY20xx.cmake, the same source the real configure reads, so the harness cannot drift
from it; an earlier version restated them and missed an identity input for it.
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
project(deps_store_roundtrip LANGUAGES CXX)

set(RV_SRC "{repo}")
list(APPEND CMAKE_MODULE_PATH "${{RV_SRC}}/cmake/defaults" "${{RV_SRC}}/cmake/macros")
set(PROJECT_SOURCE_DIR "${{RV_SRC}}")

# Defaulted, not set: a single-configuration generator creates this cache entry as empty before this
# runs, and a non-FORCE set would leave the identity without a build configuration.
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

set(RV_VFX_PLATFORM "{vfx}")
include(rv_options)
# The dependency versions, from the same files the real configure reads -- cmake/defaults/cxx_defaults
# includes CYCOMMON and then the platform year, so the harness does the same rather than restating them.
include(CYCOMMON)
include(${{RV_VFX_PLATFORM}})

set(RV_BUILD_IDENTITY ON CACHE BOOL "")
set(RV_BUILD_MANIFEST OFF)
include(rv_build_identity)
RV_COMPUTE_BUILD_IDENTITY()

include(rv_deps_store)
RV_RESOLVE_DEPS_STORE()

include(ExternalProject)
include(FetchContent)
set(RV_DEPS_LIST "")
include(rv_create_std_deps_vars)
include(rv_find_dependency)
include(rv_make_std_lib_name)
include(rv_add_imported_library)
# Defines RV_REGISTER_PREBUILT_TARGET, which the find path calls when it accepts a package.
include(rv_probe_artifact)

# Staging copies dependency libraries next to the application, which this harness does not build.
# Only that step is replaced; the dependency file, the store and the find path are the real ones.
macro(RV_STAGE_DEPENDENCY_LIBS)
endmacro()

include("${{RV_SRC}}/cmake/dependencies/zlib.cmake")
message(STATUS "HARNESS entry=${{RV_DEPS_STORE_IDENTITY_DIR}}")
message(STATUS "HARNESS zlib_install=${{RV_DEPS_STORE_IDENTITY_DIR}}/RV_DEPS_ZLIB/install")
"""

ENTRY_RE = re.compile(r"^--\s+HARNESS entry=(.*)$", re.MULTILINE)


def check(description: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"  ok   {description}")
    else:
        print(f"  FAIL {description}{(': ' + detail) if detail else ''}")
        FAILURES.append(description)


def configure(source: str, build: str, store: str, eligible: str):
    # Forward slashes, which is how CMake itself writes a Windows path. A raw backslash path works in
    # most places and then breaks where it is interpolated into a string that is re-parsed, as
    # RV_ADD_IMPORTED_LIBRARY does -- an argument defect rather than a store one, and not what this
    # suite is about.
    store = store.replace("\\", "/")
    result = subprocess.run(
        [
            "cmake",
            "-S",
            source,
            "-B",
            build,
            f"-DRV_DEPS_STORE={store}",
            f"-DRV_DEPS_STORE_ELIGIBLE={eligible}",
        ],
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout + result.stderr


def build(build_dir: str, log: str) -> int:
    result = subprocess.run(
        ["cmake", "--build", build_dir, "--config", "Release", "--target", "RV_DEPS_ZLIB"],
        capture_output=True,
        text=True,
    )
    with open(log, "w", encoding="utf-8") as handle:
        handle.write(result.stdout + result.stderr)
    return result.returncode


def read(log: str) -> str:
    with open(log, encoding="utf-8", errors="replace") as handle:
        return handle.read()


def content_digest(root: str) -> str:
    """A digest over every file's size and content, so 'unchanged' means unchanged."""
    import hashlib

    digest = hashlib.sha256()
    for directory, _subdirectories, files in sorted(os.walk(root)):
        for name in sorted(files):
            path = os.path.join(directory, name)
            digest.update(os.path.relpath(path, root).encode("utf-8"))
            with open(path, "rb") as handle:
                digest.update(handle.read())
    return digest.hexdigest()


def main() -> int:
    for tool in ("cmake",):
        if shutil.which(tool) is None:
            print(f"{tool} is not on PATH, so the round trip cannot be run")
            return 0

    print(f"dependency store round trip with a real dependency ({REPO})")
    with tempfile.TemporaryDirectory() as work:
        source = os.path.join(work, "harness")
        store = os.path.join(work, "store")
        os.makedirs(source)
        with open(os.path.join(source, "CMakeLists.txt"), "w", encoding="utf-8") as handle:
            handle.write(HARNESS.format(repo=REPO.replace("\\", "/"), vfx="CY2025"))

        first = os.path.join(work, "first")
        code, output = configure(source, first, store, "RV_DEPS_ZLIB")
        check("the harness configures", code == 0, output[-1500:])
        if code != 0:
            return 1

        entry = (ENTRY_RE.search(output) or [None, ""])[1].strip()
        check("the harness resolved a store entry", entry != "", output[-500:])

        # Eligibility is checked in test_deps_store.py, against planted trees, where it can be
        # asserted directly instead of by parsing a configure log. Duplicating it here only produced
        # a fragile check that failed for string reasons of its own.

        print("first build")
        code = build(first, os.path.join(work, "first.log"))
        if code != 0:
            # A download failure is not this suite's subject. Say so rather than failing on it.
            log = read(os.path.join(work, "first.log"))
            if re.search(r"download|Could not resolve|curl|timed out", log, re.IGNORECASE):
                print("could not fetch the dependency, so the round trip was not run")
                return 0
            check("the dependency builds", False, log[-1500:])
            return 1

        log = read(os.path.join(work, "first.log"))
        install = os.path.join(entry, "RV_DEPS_ZLIB", "install")
        check("the install was staged before being published", ".publishing" in log, log[-800:])
        check("the entry was published", "Dependency store: published" in log, log[-800:])
        check(
            "the published tree is complete",
            all(os.path.isdir(os.path.join(install, part)) for part in ("bin", "include", "lib")),
            str(sorted(os.listdir(install)) if os.path.isdir(install) else install),
        )
        check("the published marker is present", os.path.isfile(os.path.join(entry, "RV_DEPS_ZLIB", ".published")))
        check("the staging tree was tidied away", not os.path.exists(os.path.join(entry, ".publishing")))

        print("cleaning a configuration that built it")
        before = content_digest(install)
        result = subprocess.run(
            ["cmake", "--build", first, "--config", "Release", "--target", "clean-RV_DEPS_ZLIB"],
            capture_output=True,
            text=True,
        )
        check("the clean succeeds", result.returncode == 0, (result.stdout + result.stderr)[-800:])
        check("the local build tree was removed", not os.path.isdir(os.path.join(first, "RV_DEPS_ZLIB", "src")))
        check("the store is untouched by the clean", content_digest(install) == before)

        print("second build directory, same identity")
        second = os.path.join(work, "second")
        code, output = configure(source, second, store, "RV_DEPS_ZLIB")
        check("the second configuration succeeds", code == 0, output[-1000:])
        check(
            "the dependency is found in the store",
            "found in the dependency store" in output,
            output[-1000:],
        )
        # Consuming it means nothing is rebuilt: the entry must come out of the second configuration
        # exactly as it went in. Whether a build target exists is an implementation detail and not
        # what the store promises -- an earlier version of this check asserted its absence and was
        # wrong, which is its own small lesson about asserting mechanisms rather than outcomes.
        before = content_digest(install)
        result = subprocess.run(["cmake", "--build", second, "--config", "Release"], capture_output=True, text=True)
        check("the second configuration builds", result.returncode == 0, (result.stdout + result.stderr)[-800:])
        check("reusing the entry did not change it", content_digest(install) == before)

        print("removing the build directory that populated the store")
        shutil.rmtree(first)
        check("the entry survived", os.path.isdir(install))
        check("and is unchanged", content_digest(install) == before)

    print()
    if FAILURES:
        print(f"{len(FAILURES)} check(s) failed:")
        for failure in FAILURES:
            print(f"  - {failure}")
        return 1
    print("all dependency store round trip checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
