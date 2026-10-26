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
no network or no toolchain -- except in CI, where either is a broken runner and fails.

test_deps_store.py checks the store's addressing with planted trees, which is fast and runs
everywhere. This checks the thing those cannot: that a real dependency builds into the store, is
published atomically, and is then reused by a second build directory instead of being rebuilt.

Every defect in this area was found this way rather than by reading or by fixtures -- a configure
prefix that contradicted the install prefix, a publish step that never ran, a staging lookup one
level too shallow, and an unexpected writer of the install directory. A fixture cannot catch those,
because a fixture is written by someone who already believes they know how the mechanism works.

The harness includes the real options, identity, store, find and staging macros in the order the
real configure uses them, and the real dependency file for zlib, so what consumers do to a stored
dependency -- staging its library, fixing its install name -- is exercised against the store too.
The published entry is then put through the relocation gate, so the evidence for zlib's eligibility
is re-established on every run rather than recorded once. Its dependency versions come from
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

# The real staging, into a stage directory in the build tree, so whatever it does to the dependency's
# files is done here as it would be in a real build.
set(RV_STAGE_ROOT_DIR "${{CMAKE_BINARY_DIR}}/stage")
set(RV_STAGE_LIB_DIR "${{RV_STAGE_ROOT_DIR}}/lib")
set(RV_STAGE_BIN_DIR "${{RV_STAGE_ROOT_DIR}}/bin")
set(RV_STAGE_INCLUDE_DIR "${{RV_STAGE_ROOT_DIR}}/include")
add_custom_target(dependencies ALL)
include(rv_stage_dependency_libs)

include("${{RV_SRC}}/cmake/dependencies/zlib.cmake")
message(STATUS "HARNESS entry=${{RV_DEPS_STORE_IDENTITY_DIR}}")
message(STATUS "HARNESS zlib_install=${{_install_dir}}")
"""

ENTRY_RE = re.compile(r"^--\s+HARNESS entry=(.*)$", re.MULTILINE)
INSTALL_RE = re.compile(r"^--\s+HARNESS zlib_install=(.*)$", re.MULTILINE)

sys.path.insert(0, HERE)
from check_relocation import find_references, spellings  # noqa: E402


def check(description: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"  ok   {description}")
    else:
        print(f"  FAIL {description}{(': ' + detail) if detail else ''}")
        FAILURES.append(description)


def configure(source: str, build: str, store: str, eligible: str):
    # Passed as the platform writes it, backslashes and all on Windows: the store normalizes its location,
    # and a test that cleaned it up first would hide a defect there.
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


def build(build_dir: str, log: str, target: str = "RV_DEPS_ZLIB") -> int:
    result = subprocess.run(
        ["cmake", "--build", build_dir, "--config", "Release", "--target", target],
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
            # In CI a missing tool is a broken runner, and a skip there would read as a pass.
            return 1 if os.environ.get("CI") else 0

    print(f"dependency store round trip with a real dependency ({REPO})")
    with tempfile.TemporaryDirectory() as work:
        source = os.path.join(work, "harness")
        store = os.path.join(work, "store")
        os.makedirs(source)
        with open(os.path.join(source, "CMakeLists.txt"), "w", encoding="utf-8") as handle:
            handle.write(HARNESS.format(repo=REPO.replace("\\", "/"), vfx="CY2025"))
        # The dependency files find their patches relative to CMAKE_CURRENT_SOURCE_DIR, which is the
        # harness here rather than cmake/dependencies, so the patches go where they will be looked for.
        shutil.copytree(os.path.join(REPO, "cmake", "dependencies", "patch"), os.path.join(source, "patch"))

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
            # A download failure is not this suite's subject. Say so rather than failing on it -- but
            # only for a failed download, never for a step that merely follows one, and never in CI,
            # where a skip would read as a pass.
            log = read(os.path.join(work, "first.log"))
            download_failed = re.search(
                r"error: downloading|Could not resolve host|status_code: [1-9]|timed out", log, re.IGNORECASE
            )
            if download_failed and not os.environ.get("CI"):
                print("could not fetch the dependency, so the round trip was not run")
                return 0
            check("the dependency builds", False, log[-1500:])
            return 1

        log = read(os.path.join(work, "first.log"))
        install = (INSTALL_RE.search(output) or [None, ""])[1].strip()
        check(
            "the entry is addressed by recipe under the slot",
            re.search(r"/RV_DEPS_ZLIB/[0-9a-f]{12}/install$", install) is not None,
            install,
        )
        check("the install was staged before being published", "/.staging/" in log.replace("\\", "/"), log[-800:])
        check("the entry was published", "Dependency store: published" in log, log[-800:])
        check(
            "the published tree is complete",
            # zlib installs bin/ only on Windows, where it holds the DLL.
            all(
                os.path.isdir(os.path.join(install, part))
                for part in (("bin",) if os.name == "nt" else ()) + ("include", "lib")
            ),
            str(sorted(os.listdir(install)) if os.path.isdir(install) else install),
        )
        check("the published marker is present", os.path.isfile(os.path.join(os.path.dirname(install), ".published")))
        staging = os.path.join(store, ".staging")
        leftovers = (
            [name for name in os.listdir(staging) if not name.endswith(".lock")] if os.path.isdir(staging) else []
        )
        check("the staging tree was tidied away", not leftovers, str(leftovers))
        if sys.platform == "darwin":
            result = subprocess.run(
                ["otool", "-D", os.path.join(install, "lib", "libz.dylib")], capture_output=True, text=True
            )
            check(
                "the install name was fixed before publishing",
                result.stdout.strip().endswith("@rpath/libz.dylib"),
                result.stdout,
            )

        # A consumer stages the library next to the application, and on macOS sets its install name.
        # That is done to the published entry's copy, never to the entry: other build directories may
        # be reading it.
        published = content_digest(install)
        code = build(first, os.path.join(work, "first-stage.log"), "RV_DEPS_ZLIB-stage-target")
        check(
            "the first configuration stages the library", code == 0, read(os.path.join(work, "first-stage.log"))[-800:]
        )
        check("staging did not modify the published entry", content_digest(install) == published)
        stage = os.path.join(first, "stage")
        references = find_references(stage, spellings(store))
        check("nothing staged names the store", not references, str(references))

        # The relocation gate, against the tree the store actually published: this is the evidence that
        # zlib may be stored, re-established on every run.
        print("relocation gate on the published entry")
        result = subprocess.run(
            [
                sys.executable,
                os.path.join(HERE, "check_relocation.py"),
                "--install",
                install,
                "--package",
                "ZLIB",
                "--target",
                "ZLIB::ZLIB",
                "--module",
                "--include",
                "zlib.h",
                "--exercise",
                "if (!zlibVersion()) { return 1; }",
                "--work",
                os.path.join(work, "gate"),
            ],
            capture_output=True,
            text=True,
        )
        check("the published zlib is relocatable", result.returncode == 0, (result.stdout + result.stderr)[-1500:])
        check("the gate put the entry back unchanged", content_digest(install) == published)

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
        # exactly as it went in, staging included. Whether a build target exists is an implementation
        # detail and not what the store promises -- an earlier version of this check asserted its
        # absence and was wrong, which is its own small lesson about asserting mechanisms rather than
        # outcomes.
        result = subprocess.run(["cmake", "--build", second, "--config", "Release"], capture_output=True, text=True)
        check(
            "the second configuration builds and stages", result.returncode == 0, (result.stdout + result.stderr)[-800:]
        )
        check("reusing the entry did not change it", content_digest(install) == before)
        check(
            "the second configuration did not build zlib",
            not os.path.isdir(os.path.join(second, "RV_DEPS_ZLIB", "src")),
        )
        references = find_references(os.path.join(second, "stage"), spellings(store))
        check("nothing the second configuration staged names the store", not references, str(references))

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
