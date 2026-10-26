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

Most of what the store does cannot be checked without building dependencies, but its addressing,
its reuse, its publishing and its opt-out can: which directory an eligible dependency's installed
tree goes to, whether that follows the identity and the dependency's recipe, whether a published
dependency is found instead of built, whether two installs racing for one entry leave it whole, and
whether opting out leaves nothing that still points at the store. Those are the parts where a
mistake is silently expensive, so they are checked here on every platform.

The harness includes the real options, identity, store and find macros in the order the real
configure uses them. Reconfiguring matters as much as configuring: the opt-out only shows on a
second configure of the same tree, so several checks configure twice and look at the second.
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
set(RV_DEPS_ZLIB_VERSION "1.3.1" CACHE STRING "")
set(RV_DEPS_ZLIB_DOWNLOAD_HASH "127b8a71a3fb8b4a3bfa1d5a4d3c8f6e" CACHE STRING "")

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
message(STATUS "HARNESS root=${{RV_DEPS_STORE_ROOT}}")
message(STATUS "HARNESS entry=${{RV_DEPS_STORE_IDENTITY_DIR}}")
message(STATUS "HARNESS eligible_install=${{_zlib_install}}")
message(STATUS "HARNESS eligible_staging=${{_zlib_staging}}")
message(STATUS "HARNESS ineligible_install=${{_oiio_install}}")

include(rv_create_std_deps_vars)

# What zlib.cmake does with its include directory: a non-FORCE cache entry naming the installed tree.
if(HARNESS_CACHE_INCLUDE)
  set(RV_DEPS_ZLIB_INCLUDE_DIR "${{_zlib_install}}/include" CACHE STRING "")
  message(STATUS "HARNESS cached_include=${{RV_DEPS_ZLIB_INCLUDE_DIR}}")
endif()

# A dependency configured before zlib, as openssl and Python are in the real configure.
if(HARNESS_STD)
  RV_CREATE_STANDARD_DEPS_VARIABLES("RV_DEPS_EARLY" "1.0" "" "")
  message(STATUS "HARNESS std_early_options=${{_configure_options}}")
endif()

# Consumption: with an entry in the store, the dependency is found rather than built.
if(HARNESS_FIND)
  set(RV_DEPS_VERSION_MATCH "MINIMUM")
  include(rv_find_dependency)
  RV_FIND_DEPENDENCY(TARGET RV_DEPS_ZLIB PACKAGE Zlib VERSION 1.3.1)
  message(STATUS "HARNESS found=${{RV_DEPS_ZLIB_FOUND}}")
endif()

# The standard dependency variables, as a dependency file creates them: the install command, and
# the configure options every dependency sub-build gets.
if(HARNESS_STD)
  RV_CREATE_STANDARD_DEPS_VARIABLES("RV_DEPS_ZLIB" "${{RV_DEPS_ZLIB_VERSION}}" "" "")
  message(STATUS "HARNESS std_install=${{_install_dir}}")
  message(STATUS "HARNESS std_install_command=${{_cmake_install_command}}")
  RV_CREATE_STANDARD_DEPS_VARIABLES("RV_DEPS_PNG" "1.6.0" "" "")
  message(STATUS "HARNESS std_png_options=${{_configure_options}}")
endif()

# A dependency that forces its own build from source, as tiff.cmake and raw.cmake do: the flag is set in the dependency file
# itself, before the standard variables decide where it installs.
if(HARNESS_SELF_FORCED)
  set(RV_DEPS_SELFFORCED_FORCE_BUILD ON CACHE BOOL "")
  RV_CREATE_STANDARD_DEPS_VARIABLES("RV_DEPS_SELFFORCED" "1.0" "" "")
  message(STATUS "HARNESS self_forced_install=${{_install_dir}}")
endif()
"""

VALUE_RE = {
    name: re.compile(rf"^--\s+HARNESS {name}=(.*)$", re.MULTILINE)
    for name in (
        "hash",
        "base",
        "root",
        "entry",
        "eligible_install",
        "eligible_staging",
        "ineligible_install",
        "cached_include",
        "found",
        "std_install",
        "std_install_command",
        "std_png_options",
        "std_early_options",
        "self_forced_install",
    )
}

ELIGIBLE = "-DRV_DEPS_STORE_ELIGIBLE=RV_DEPS_ZLIB"


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

    On Windows a temporary directory can arrive in 8.3 form (``RUNNER~1``) while CMake resolves it to
    the long name, and on macOS /var is a link to /private/var. Both are the same directory, so
    comparing the strings as given compares spelling rather than location.
    """
    return os.path.normcase(os.path.realpath(text.strip()))


def inside(path: str, root: str) -> bool:
    path, root = normalized_path(path), normalized_path(root)
    return path == root or path.startswith(root + os.sep)


def flattened(text: str) -> str:
    """Collapse whitespace, because CMake wraps MESSAGE text at the terminal width."""
    return re.sub(r"\s+", " ", text)


def configure(source: str, build: str, *definitions, env=None):
    result = subprocess.run(["cmake", "-S", source, "-B", build, *definitions], capture_output=True, text=True, env=env)
    return result.returncode, result.stdout + result.stderr


def cache_text(build: str) -> str:
    with open(os.path.join(build, "CMakeCache.txt"), encoding="utf-8", errors="replace") as handle:
        return handle.read()


def cache_mentions(build: str, path: str) -> list:
    """Cache lines whose value names a path under ``path``, in either spelling."""
    spellings = {path.replace("\\", "/"), os.path.realpath(path).replace("\\", "/")}
    return [
        line
        for line in cache_text(build).splitlines()
        if not line.startswith(("#", "//")) and any(spelling in line for spelling in spellings)
    ]


def package_config(install: str) -> str:
    """A minimal installed package, as a dependency build would publish it into the store."""
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
    # The publish marker, which is what distinguishes a published entry from a directory that merely
    # exists: RV's configure creates the install directory for every dependency, so existence alone
    # is not evidence that a dependency was ever installed there.
    with open(os.path.join(os.path.dirname(install), ".published"), "w", encoding="utf-8") as handle:
        handle.write("")
    return install


def test_default_configure_is_unchanged(directory: str, source: str) -> None:
    print("without a store, installed trees stay in the build directory and no store is consulted")
    build = os.path.join(directory, "default")
    code, output = configure(source, build, "-DHARNESS_FIND=ON", "-DHARNESS_STD=ON")
    check("the configure succeeds", code == 0, output[-800:])
    check(
        "an eligible dependency still installs locally when there is no store",
        normalized_path(value("eligible_install", output))
        == normalized_path(os.path.join(build, "RV_DEPS_ZLIB", "install")),
        f"got {value('eligible_install', output)!r}",
    )
    check("no store entry is used", value("entry", output) == "", value("entry", output))
    check("no staging is used", value("eligible_staging", output) == "", value("eligible_staging", output))
    check(
        "the install command is the plain one",
        "rv_store_install" not in value("std_install_command", output)
        and "--install" in value("std_install_command", output),
        value("std_install_command", output),
    )
    check(
        "sub-builds get no store arguments",
        "-U" not in value("std_png_options", output),
        value("std_png_options", output),
    )
    # Not consulted means not mentioned: nothing is reported about a store, nothing is found in one,
    # and none of the store's bookkeeping is written into the cache.
    check("nothing is reported about a store", "Dependency store" not in output, output[-600:])
    check("the dependency is not found anywhere", value("found", output) == "FALSE", value("found", output))
    cache = cache_text(build)
    check(
        "the store adds no cache entry beyond its options",
        not re.search(r"^RV_DEPS_(STORE_(LAST_SLOT|PACKAGES|IDENTITY_DIR)|INSTALL_ROOT)\b", cache, re.MULTILINE),
        "\n".join(line for line in cache.splitlines() if line.startswith("RV_DEPS_STORE")),
    )
    created = [
        os.path.join(root, name)
        for root, directories, files in os.walk(build)
        for name in directories + files
        if name in (".staging", ".published") or name.endswith(".lock")
    ]
    check("no store directory or marker is created", not created, str(created))


def test_an_explicit_base_directory_is_honoured(directory: str, source: str) -> None:
    print("an explicitly set dependency directory is still where local trees go")
    build = os.path.join(directory, "explicit-base")
    base = os.path.join(directory, "explicit-base-deps")
    code, output = configure(source, build, f"-DRV_DEPS_BASE_DIR={base}")
    check("the configure succeeds", code == 0, output[-800:])
    check(
        "without a store, the eligible dependency installs under it",
        inside(value("eligible_install", output), base),
        value("eligible_install", output),
    )
    store = os.path.join(directory, "explicit-base-store")
    code, output = configure(source, build, f"-DRV_DEPS_BASE_DIR={base}", f"-DRV_DEPS_STORE={store}", ELIGIBLE)
    check(
        "with a store, the ineligible dependency still installs under it",
        inside(value("ineligible_install", output), base),
    )
    check("and the eligible one installs in the store", inside(value("eligible_install", output), store))


def test_store_places_only_eligible_dependencies(directory: str, source: str) -> None:
    print("with a store, only the eligible dependency's installed tree moves")
    build = os.path.join(directory, "store-build")
    store = os.path.join(directory, "store")
    code, output = configure(source, build, f"-DRV_DEPS_STORE={store}", ELIGIBLE, "-DHARNESS_STD=ON")
    check("the configure succeeds", code == 0, output[-800:])

    entry = value("entry", output)
    check(
        "the slot is inside the store", inside(entry, store) and normalized_path(entry) != normalized_path(store), entry
    )
    check(
        "the slot is a short digest, to keep paths inside MAX_PATH",
        re.fullmatch(r"[0-9a-f]{16}", os.path.basename(entry)) is not None,
        entry,
    )
    install = value("eligible_install", output)
    check(
        "the eligible dependency installs into a recipe entry under the slot",
        re.fullmatch(
            re.escape(normalized_path(os.path.join(entry, "RV_DEPS_ZLIB"))) + r"[\\/][0-9a-f]{12}[\\/]install",
            normalized_path(install),
        )
        is not None,
        install,
    )
    check(
        "the ineligible dependency installs in the build directory",
        normalized_path(value("ineligible_install", output))
        == normalized_path(os.path.join(build, "RV_DEPS_OIIO", "install")),
        value("ineligible_install", output),
    )
    check(
        "the install is staged and published rather than written in place",
        "rv_store_install" in value("std_install_command", output),
        value("std_install_command", output),
    )
    check(
        "the standard variables agree with the store paths",
        normalized_path(value("std_install", output)) == normalized_path(install),
        f"{value('std_install', output)!r} != {install!r}",
    )
    check("the store directory was created", os.path.isdir(store), store)
    check("the eligible dependency is named in the report", "RV_DEPS_ZLIB" in output, output[-600:])


def test_an_empty_eligibility_list_places_nothing(directory: str, source: str) -> None:
    print("a store with nothing eligible changes nothing about where dependencies go")
    build = os.path.join(directory, "empty-eligibility")
    store = os.path.join(directory, "empty-store")
    code, output = configure(source, build, f"-DRV_DEPS_STORE={store}", "-DRV_DEPS_STORE_ELIGIBLE=")
    check("the configure succeeds", code == 0, output[-800:])
    check(
        "the eligible dependency is placed in the build directory anyway",
        inside(value("eligible_install", output), build),
        value("eligible_install", output),
    )
    check("the report says nothing is eligible", "none, so no dependency is placed" in flattened(output), output[-600:])


def test_the_default_list_is_not_frozen(directory: str, source: str) -> None:
    print("'default' follows the built-in list, and can be extended")
    store = os.path.join(directory, "default-list-store")
    _, output = configure(source, os.path.join(directory, "default-list"), f"-DRV_DEPS_STORE={store}")
    check(
        "the cached value is 'default'",
        "RV_DEPS_STORE_ELIGIBLE:STRING=default" in cache_text(os.path.join(directory, "default-list")),
    )
    check(
        "the built-in list is applied",
        inside(value("eligible_install", output), store),
        value("eligible_install", output),
    )
    _, output = configure(
        source,
        os.path.join(directory, "extended-list"),
        f"-DRV_DEPS_STORE={store}",
        "-DRV_DEPS_STORE_ELIGIBLE=default;RV_DEPS_OIIO",
    )
    check("an extension keeps the built-in list", inside(value("eligible_install", output), store))
    check("and adds the named dependency", inside(value("ineligible_install", output), store))


def test_a_forced_build_never_uses_the_store(directory: str, source: str) -> None:
    print("a dependency forced to build from source neither installs into nor is taken from the store")
    store = os.path.join(directory, "forced-store")
    arguments = (f"-DRV_DEPS_STORE={store}", ELIGIBLE, "-DHARNESS_FIND=ON", "-DHARNESS_STD=ON")
    _, first = configure(source, os.path.join(directory, "forced-first"), *arguments)
    package_config(value("eligible_install", first))

    build = os.path.join(directory, "forced")
    _, output = configure(source, build, *arguments, "-DRV_DEPS_ZLIB_FORCE_BUILD=ON")
    check(
        "it installs in the build directory",
        normalized_path(value("std_install", output))
        == normalized_path(os.path.join(build, "RV_DEPS_ZLIB", "install")),
        value("std_install", output),
    )
    check(
        "its install is not staged into the store",
        "rv_store_install" not in value("std_install_command", output),
        value("std_install_command", output),
    )
    check("the published entry is not used", value("found", output) == "FALSE", value("found", output))


def test_a_dependency_forcing_itself_is_never_stored(directory: str, source: str) -> None:
    print("a dependency that forces its own build from source stays out of the store from the first configure")
    build = os.path.join(directory, "self-forced")
    _, output = configure(
        source,
        build,
        f"-DRV_DEPS_STORE={os.path.join(directory, 'self-forced-store')}",
        "-DRV_DEPS_STORE_ELIGIBLE=RV_DEPS_ZLIB;RV_DEPS_SELFFORCED",
        "-DHARNESS_SELF_FORCED=ON",
    )
    check(
        "it installs in the build directory even though it is named as eligible",
        normalized_path(value("self_forced_install", output))
        == normalized_path(os.path.join(build, "RV_DEPS_SELFFORCED", "install")),
        value("self_forced_install", output),
    )


def test_force_built_dependencies_stay_ineligible() -> None:
    print("the dependencies built from source on purpose are never stored")
    dependencies = os.path.join(REPO, "cmake", "dependencies")
    with open(os.path.join(REPO, "cmake", "macros", "rv_deps_store.cmake"), encoding="utf-8") as handle:
        default = re.search(r'SET\(RV_DEPS_STORE_ELIGIBLE_DEFAULT\s+"([^"]*)"', handle.read()).group(1).split(";")
    forced = []
    for name in sorted(os.listdir(dependencies)):
        if not name.endswith(".cmake"):
            continue
        with open(os.path.join(dependencies, name), encoding="utf-8") as handle:
            text = handle.read()
        for match in re.finditer(r"SET\((RV_DEPS_\w+)_FORCE_BUILD\s+ON\b", text):
            target = match.group(1)
            forced.append(target)
            standard = text.find(f'RV_CREATE_STANDARD_DEPS_VARIABLES("{target}"')
            check(
                f"{target} is forced before the standard variables decide where it installs ({name})",
                standard == -1 or match.start() < standard,
            )
            check(f"{target} is not in the built-in eligible list", target not in default, str(default))
    check(
        "libtiff and libraw are among the dependencies forced to build from source",
        {"RV_DEPS_TIFF", "RV_DEPS_RAW"} <= set(forced),
        str(forced),
    )


def test_the_entry_follows_the_recipe(directory: str, source: str) -> None:
    print("a dependency's entry changes with what it is built from")
    store = os.path.join(directory, "recipe-store")
    arguments = (f"-DRV_DEPS_STORE={store}", ELIGIBLE)

    def entry(name, *extra):
        _, output = configure(source, os.path.join(directory, name), *arguments, *extra)
        return value("eligible_install", output)

    base = entry("recipe-a")
    check("the same recipe in another build directory shares the entry", entry("recipe-b") == base)
    check("a version bump addresses a new entry", entry("recipe-version", "-DRV_DEPS_ZLIB_VERSION=1.3.2") != base)
    check(
        "a different download addresses a new entry",
        entry("recipe-hash", "-DRV_DEPS_ZLIB_DOWNLOAD_HASH=00000000000000000000000000000000") != base,
    )
    check(
        "the slot is unchanged by the recipe",
        os.path.dirname(os.path.dirname(os.path.dirname(entry("recipe-version2", "-DRV_DEPS_ZLIB_VERSION=1.3.2"))))
        == os.path.dirname(os.path.dirname(os.path.dirname(base))),
    )
    if sys.platform == "darwin":
        check(
            "a different macOS architecture addresses a different slot",
            os.path.dirname(
                os.path.dirname(os.path.dirname(entry("recipe-arch", "-DCMAKE_OSX_ARCHITECTURES=x86_64;arm64")))
            )
            != os.path.dirname(os.path.dirname(os.path.dirname(base))),
        )


def test_one_store_holds_one_slot_per_identity(directory: str, source: str) -> None:
    print("one store holds one slot per identity")
    store = os.path.join(directory, "shared")
    arguments = (f"-DRV_DEPS_STORE={store}", ELIGIBLE)

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


def test_the_store_location_is_normalized(directory: str, source: str) -> None:
    print("a store given relatively, with ~, or with backslashes is normalized")
    build = os.path.join(directory, "relative")
    _, output = configure(source, build, "-DRV_DEPS_STORE=relative-store", ELIGIBLE)
    check(
        "a relative store is taken relative to the build directory",
        normalized_path(value("root", output)) == normalized_path(os.path.join(build, "relative-store")),
        value("root", output),
    )

    home = os.path.join(directory, "home")
    os.makedirs(home)
    environment = dict(os.environ, HOME=home, USERPROFILE=home)
    _, output = configure(
        source, os.path.join(directory, "tilde"), "-DRV_DEPS_STORE=~/tilde-store", ELIGIBLE, env=environment
    )
    check(
        "a store starting with ~ is in the home directory",
        normalized_path(value("root", output)) == normalized_path(os.path.join(home, "tilde-store")),
        value("root", output),
    )

    backslashed = os.path.join(directory, "backslash-store").replace("/", "\\") if os.name == "nt" else None
    if backslashed:
        _, output = configure(source, os.path.join(directory, "backslash"), f"-DRV_DEPS_STORE={backslashed}", ELIGIBLE)
        check(
            "a backslash store comes back in CMake's form",
            "\\" not in value("eligible_install", output),
            value("eligible_install", output),
        )


def test_a_published_dependency_is_found_not_built(directory: str, source: str) -> None:
    print("a dependency published for this identity is found in the store")
    store = os.path.join(directory, "consume-store")
    arguments = (f"-DRV_DEPS_STORE={store}", ELIGIBLE, "-DHARNESS_FIND=ON")

    # Nothing published yet: the store must not be what makes this succeed.
    _, empty = configure(source, os.path.join(directory, "consume-empty"), *arguments)
    check("the configure succeeds", "HARNESS found=" in empty, empty[-600:])
    check("an unpublished dependency is not found", value("found", empty) == "FALSE", value("found", empty))

    # Publish an entry by hand, as a dependency build would leave it, and find it.
    package_config(value("eligible_install", empty))

    _, published = configure(source, os.path.join(directory, "consume-published"), *arguments)
    check("the published dependency is found", value("found", published) == "TRUE", value("found", published))
    check(
        "the report says it came from the store",
        "found in the dependency store" in flattened(published),
        published[-600:],
    )

    # A prefix that also provides the package does not win over the entry: the entry is searched first.
    decoy = os.path.join(directory, "decoy")
    shutil.copytree(os.path.dirname(value("eligible_install", empty)), os.path.join(decoy, "x"))
    _, decoyed = configure(
        source,
        os.path.join(directory, "consume-decoyed"),
        *arguments,
        f"-DCMAKE_PREFIX_PATH={os.path.join(decoy, 'x', 'install')}",
    )
    check("the entry wins over another prefix", "found in the dependency store" in flattened(decoyed), decoyed[-600:])

    # A staged tree that was never published must not be consumable: this is what an interrupted
    # install leaves behind, and finding it would mean using a half-written dependency.
    staged_store = os.path.join(directory, "consume-staged-store")
    staged_args = (f"-DRV_DEPS_STORE={staged_store}", ELIGIBLE, "-DHARNESS_FIND=ON")
    _, staged_first = configure(source, os.path.join(directory, "consume-staged-only"), *staged_args)
    staging = os.path.join(staged_store, ".staging", "00000000-00000000", "x", "install")
    os.makedirs(os.path.join(staging, "lib", "cmake", "Zlib"), exist_ok=True)
    with open(os.path.join(staging, "lib", "cmake", "Zlib", "ZlibConfig.cmake"), "w", encoding="utf-8") as handle:
        handle.write('set(Zlib_VERSION "1.3.1")\n')
    # And an entry directory with content but no marker, which is what an interrupted publish leaves.
    unmarked = value("eligible_install", staged_first)
    package_config(unmarked)
    os.remove(os.path.join(os.path.dirname(unmarked), ".published"))
    _, staged_again = configure(source, os.path.join(directory, "consume-staged-again"), *staged_args)
    check(
        "a staged or unmarked entry is not consumed",
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
    print("removing the store returns a configured tree to the build directory, and forgets it")
    build = os.path.join(directory, "optout")
    store = os.path.join(directory, "optout-store")
    arguments = ("-DHARNESS_FIND=ON", "-DHARNESS_CACHE_INCLUDE=ON", "-DHARNESS_STD=ON", "-DRV_DEPS_PREFER_INSTALLED=ON")

    # A first configure to learn the entry, publish it, and a second that consumes it, so the tree's
    # cache holds everything a real consumer would: the find result and the dependency's own paths.
    _, with_store = configure(source, build, f"-DRV_DEPS_STORE={store}", ELIGIBLE, *arguments)
    package_config(value("eligible_install", with_store))
    _, consumed = configure(source, build, f"-DRV_DEPS_STORE={store}", ELIGIBLE, *arguments)
    check("the tree consumes the store", value("found", consumed) == "TRUE", consumed[-600:])
    check("the cache names the store", bool(cache_mentions(build, store)), "nothing to forget, so this proves nothing")
    check(
        "sub-builds forget what they cached for a stored package when reconfigured",
        "-UZlib_*" in value("std_png_options", consumed),
        value("std_png_options", consumed),
    )

    # 6.1: the store location is removed and the tree reconfigured. The store directory is left on
    # disk, which is the harder case: a cached path into it would still resolve.
    _, without_store = configure(source, build, "-DRV_DEPS_STORE=", *arguments)
    check("the entry is gone", value("entry", without_store) == "", value("entry", without_store))
    check(
        "the eligible dependency installs in the build directory again",
        normalized_path(value("eligible_install", without_store))
        == normalized_path(os.path.join(build, "RV_DEPS_ZLIB", "install")),
        value("eligible_install", without_store),
    )
    check(
        "the dependency's cached include directory follows",
        inside(value("cached_include", without_store), build),
        value("cached_include", without_store),
    )
    # 6.2: nothing is resolved from the removed location, including through a cached find result,
    # even with installed packages preferred.
    check(
        "the dependency is not found in the removed store",
        value("found", without_store) == "FALSE",
        without_store[-600:],
    )
    check(
        "no cache entry names the removed store",
        not cache_mentions(build, store),
        "\n".join(cache_mentions(build, store)),
    )
    check(
        "sub-builds keep forgetting what they cached, so they re-resolve too",
        "-UZlib_*" in value("std_png_options", without_store),
        value("std_png_options", without_store),
    )
    check(
        "a dependency configured before the stored one never gets the argument, so its command never changes",
        "-U" not in value("std_early_options", consumed) and "-U" not in value("std_early_options", without_store),
        value("std_early_options", consumed),
    )

    # The same holds when the store moves rather than goes away.
    _, moved = configure(source, build, f"-DRV_DEPS_STORE={store}", ELIGIBLE, *arguments)
    other = os.path.join(directory, "moved-store")
    _, moved = configure(source, build, f"-DRV_DEPS_STORE={other}", ELIGIBLE, *arguments)
    check(
        "moving the store forgets the old location",
        not cache_mentions(build, store),
        "\n".join(cache_mentions(build, store)),
    )


def test_a_recipe_change_forgets_the_old_entry(directory: str, source: str) -> None:
    print("bumping a stored dependency forgets the entry it replaces")
    build = os.path.join(directory, "bump")
    store = os.path.join(directory, "bump-store")
    arguments = (f"-DRV_DEPS_STORE={store}", ELIGIBLE, "-DHARNESS_FIND=ON", "-DHARNESS_CACHE_INCLUDE=ON")
    _, first = configure(source, build, *arguments)
    old = value("eligible_install", first)
    package_config(old)
    _, consumed = configure(source, build, *arguments)
    check("the old entry is consumed", value("found", consumed) == "TRUE", consumed[-600:])

    _, bumped = configure(source, build, *arguments, "-DRV_DEPS_ZLIB_VERSION=1.3.2")
    check("the bumped dependency is not found in the old entry", value("found", bumped) == "FALSE", bumped[-600:])
    check(
        "no cache entry names the old entry",
        not cache_mentions(build, os.path.dirname(old)),
        "\n".join(cache_mentions(build, os.path.dirname(old))),
    )


def test_an_evicted_entry_reinstalls(directory: str, source: str) -> None:
    print("a build directory whose entry was removed from the store installs it again")
    build = os.path.join(directory, "evicted")
    store = os.path.join(directory, "evicted-store")
    arguments = (f"-DRV_DEPS_STORE={store}", ELIGIBLE, "-DHARNESS_STD=ON")
    _, first = configure(source, build, *arguments)
    stamps = os.path.join(build, "RV_DEPS_ZLIB-prefix", "src", "RV_DEPS_ZLIB-stamp")
    os.makedirs(stamps)
    for name in ("RV_DEPS_ZLIB-install", "RV_DEPS_ZLIB-done", "RV_DEPS_ZLIB-build"):
        open(os.path.join(stamps, name), "w").close()

    # Published: the stamps are right, and kept.
    package_config(value("std_install", first))
    configure(source, build, *arguments)
    check("the stamps of a published entry are kept", os.path.exists(os.path.join(stamps, "RV_DEPS_ZLIB-install")))

    # Evicted: the install stamp would stop the install from running again.
    shutil.rmtree(os.path.dirname(value("std_install", first)))
    _, output = configure(source, build, *arguments)
    check("the install stamp is removed", not os.path.exists(os.path.join(stamps, "RV_DEPS_ZLIB-install")))
    check("the done stamp is removed", not os.path.exists(os.path.join(stamps, "RV_DEPS_ZLIB-done")))
    check("the build stamp is kept", os.path.exists(os.path.join(stamps, "RV_DEPS_ZLIB-build")))
    check("the report says why", "will run again" in flattened(output), output[-600:])


def test_the_store_requires_an_identity(directory: str, source: str) -> None:
    print("a store without an identity fails, naming the reason")
    build = os.path.join(directory, "no-identity")
    store = os.path.join(directory, "no-identity-store")
    code, output = configure(source, build, f"-DRV_DEPS_STORE={store}", "-DRV_BUILD_IDENTITY=OFF")
    check("the configure fails", code != 0, "a store was configured without an identity")
    check("the failure names the store", "RV_DEPS_STORE" in flattened(output), output[-800:])
    check("the failure names the identity requirement", "identity" in flattened(output), output[-800:])


PUBLISH = os.path.join(REPO, "cmake", "macros", "rv_store_publish.cmake")
INSTALL = os.path.join(REPO, "cmake", "macros", "rv_store_install.cmake")


def publish_command(staging: str, final: str):
    return ["cmake", f"-DRV_PUBLISH_STAGING={staging}", f"-DRV_PUBLISH_FINAL={final}", "-P", PUBLISH]


def run(command):
    result = subprocess.run(command, capture_output=True, text=True)
    return result.returncode, result.stdout + result.stderr


def tree(path: str, content: str, count: int = 1) -> str:
    os.makedirs(path)
    for index in range(count):
        with open(os.path.join(path, f"file{index:04d}"), "w", encoding="utf-8") as handle:
            handle.write(content)
    return path


def contents(path: str) -> set:
    found = set()
    for root, _directories, files in os.walk(path):
        for name in files:
            with open(os.path.join(root, name), encoding="utf-8") as handle:
                found.add(handle.read())
    return found


def test_publishing_is_atomic(directory: str) -> None:
    print("publishing appears complete or not at all")
    root = os.path.join(directory, "publish")
    final = os.path.join(root, "slot", "RV_DEPS_ZLIB", "abc", "install")
    marker = os.path.join(os.path.dirname(final), ".published")

    staging = tree(os.path.join(root, "staging", "install"), "installed\n")
    code, output = run(publish_command(staging, final))
    check("a staged tree is published", code == 0, output[-600:])
    check("the published tree is in place", contents(final) == {"installed\n"}, final)
    check("the marker is written", os.path.isfile(marker))
    check("the staging directory is gone", not os.path.exists(staging), staging)

    code, output = run(publish_command(staging, final))
    check("publishing again with nothing staged succeeds", code == 0, output[-600:])

    second = tree(os.path.join(root, "staging2", "install"), "different\n")
    code, output = run(publish_command(second, final))
    check("an already published entry is not replaced", code == 0, output[-600:])
    check("the published content is unchanged", contents(final) == {"installed\n"})
    check("the staged copy is discarded", not os.path.exists(second))

    # An entry with content but no marker is what an interrupted publish leaves, or the skeleton a
    # configure creates. It is not a published dependency, so it is replaced rather than accepted.
    unmarked = os.path.join(root, "slot", "RV_DEPS_ZLIB", "def", "install")
    tree(unmarked, "partial\n")
    third = tree(os.path.join(root, "staging3", "install"), "complete\n")
    code, output = run(publish_command(third, unmarked))
    check("an unmarked entry is replaced", code == 0 and contents(unmarked) == {"complete\n"}, output[-600:])

    # Nothing staged and nothing published is a failure, not a silent success -- including when an
    # unmarked directory is in the way, which an earlier version reported as success.
    skeleton = os.path.join(root, "slot", "RV_DEPS_ZLIB", "ghi", "install")
    os.makedirs(os.path.join(skeleton, "include"))
    code, output = run(publish_command(os.path.join(root, "missing"), skeleton))
    check("nothing staged and an unmarked skeleton fails", code != 0, f"exit {code}")
    check("the failure says nothing was staged", "nothing was staged" in flattened(output), output[-600:])
    check(
        "the skeleton is not marked published",
        not os.path.exists(os.path.join(os.path.dirname(skeleton), ".published")),
    )


def test_racing_publishes_leave_one_whole_entry(directory: str) -> None:
    print("two publishes racing for one entry leave exactly one of them, whole")
    for attempt in range(3):
        root = os.path.join(directory, f"race{attempt}")
        final = os.path.join(root, "slot", "RV_DEPS_ZLIB", "abc", "install")
        first = tree(os.path.join(root, "a", "install"), "a\n", 300)
        second = tree(os.path.join(root, "b", "install"), "b\n", 300)
        processes = [
            subprocess.Popen(publish_command(path, final), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            for path in (first, second)
        ]
        outputs = [process.communicate()[0] for process in processes]
        codes = [process.returncode for process in processes]
        check(f"both publishes succeed ({attempt})", codes == [0, 0], "\n".join(output[-300:] for output in outputs))
        check(
            f"the entry is one of them, whole ({attempt})", contents(final) in ({"a\n"}, {"b\n"}), str(contents(final))
        )
        check(f"the entry has every file ({attempt})", len(os.listdir(final)) == 300, str(len(os.listdir(final))))
        check(f"the entry is marked ({attempt})", os.path.isfile(os.path.join(os.path.dirname(final), ".published")))
        check(f"neither staged copy is left ({attempt})", not os.path.exists(first) and not os.path.exists(second))


INSTALL_PROJECT = """\
cmake_minimum_required(VERSION 3.27)
project(store_install_fixture NONE)
file(GLOB _files "${CMAKE_CURRENT_SOURCE_DIR}/data/*")
install(FILES ${_files} DESTINATION share/data)
configure_file(fixture.pc.in fixture.pc @ONLY)
install(FILES "${CMAKE_CURRENT_BINARY_DIR}/fixture.pc" DESTINATION lib/pkgconfig)
"""


def test_racing_installs_stage_privately(directory: str) -> None:
    print("two installs of one dependency stage privately, and a leftover is cleaned up")
    root = os.path.join(directory, "install-race")
    source = os.path.join(root, "src")
    tree(os.path.join(source, "data"), "data\n", 300)
    with open(os.path.join(source, "CMakeLists.txt"), "w", encoding="utf-8") as handle:
        handle.write(INSTALL_PROJECT)
    with open(os.path.join(source, "fixture.pc.in"), "w", encoding="utf-8") as handle:
        handle.write("prefix=@CMAKE_INSTALL_PREFIX@\nlibdir=@CMAKE_INSTALL_PREFIX@/lib\nName: fixture\nVersion: 1\n")

    store = os.path.join(root, "store")
    final = os.path.join(store, "slot", "RV_DEPS_FIXTURE", "abc", "install").replace("\\", "/")
    builds = []
    for name in ("one", "two"):
        build = os.path.join(root, name)
        code, output = run(["cmake", "-S", source, "-B", build, f"-DCMAKE_INSTALL_PREFIX={final}"])
        check(f"the fixture configures ({name})", code == 0, output[-600:])
        builds.append(build)

    # A leftover of an install that was killed: its lock is free, so it is not anybody's.
    leftover = os.path.join(store, ".staging", "deadbeef-00000000")
    tree(leftover, "leftover\n")
    open(leftover + ".lock", "w").close()

    fixup = os.path.join(root, "fixup.cmake")
    with open(fixup, "w", encoding="utf-8") as handle:
        handle.write('file(WRITE "${RV_STAGED_INSTALL}/fixed-up" "yes\\n")\n')

    def install(build, tag):
        return subprocess.Popen(
            [
                "cmake",
                f"-DRV_INSTALL_BUILD={build}",
                f"-DRV_INSTALL_PREFIX={final}",
                "-DRV_INSTALL_CONFIG=Release",
                f"-DRV_INSTALL_STORE={store}",
                f"-DRV_INSTALL_TAG={tag}",
                f"-DRV_INSTALL_FIXUP={fixup}",
                "-P",
                INSTALL,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )

    processes = [install(builds[0], "aaaaaaaa"), install(builds[1], "bbbbbbbb")]
    outputs = [process.communicate()[0] for process in processes]
    check(
        "both installs succeed",
        [process.returncode for process in processes] == [0, 0],
        "\n".join(o[-600:] for o in outputs),
    )
    check("the entry is complete", len(os.listdir(os.path.join(final, "share", "data"))) == 300)
    check("the entry is marked", os.path.isfile(os.path.join(os.path.dirname(final), ".published")))
    check("the fixup ran on the staged tree", os.path.isfile(os.path.join(final, "fixed-up")))
    with open(os.path.join(final, "lib", "pkgconfig", "fixture.pc"), encoding="utf-8") as handle:
        pc = handle.read()
    # Both spellings: on Windows the temporary directory is often an 8.3 short path, and CMake records the long one.
    spellings = {final, os.path.realpath(final).replace("\\", "/")}
    check("the pkg-config file no longer names the install prefix", not any(s in pc for s in spellings), pc)
    check("it is relative to itself instead", "prefix=${pcfiledir}/../.." in pc, pc)
    remaining = os.listdir(os.path.join(store, ".staging")) if os.path.isdir(os.path.join(store, ".staging")) else []
    check(
        "no staging directory is left behind, including the leftover",
        not [n for n in remaining if not n.endswith(".lock")],
        str(remaining),
    )


def main() -> int:
    if shutil.which("cmake") is None:
        print("cmake is not on PATH, so the dependency store cannot be checked")
        # In CI a missing tool is a broken runner, not a pass.
        return 1 if os.environ.get("CI") else 0

    print(f"dependency store ({REPO})")
    with tempfile.TemporaryDirectory() as directory:
        source = os.path.join(directory, "harness")
        os.makedirs(source)
        with open(os.path.join(source, "CMakeLists.txt"), "w", encoding="utf-8") as handle:
            handle.write(HARNESS.format(repo=REPO.replace("\\", "/")))

        test_default_configure_is_unchanged(directory, source)
        test_an_explicit_base_directory_is_honoured(directory, source)
        test_store_places_only_eligible_dependencies(directory, source)
        test_an_empty_eligibility_list_places_nothing(directory, source)
        test_the_default_list_is_not_frozen(directory, source)
        test_a_forced_build_never_uses_the_store(directory, source)
        test_a_dependency_forcing_itself_is_never_stored(directory, source)
        test_force_built_dependencies_stay_ineligible()
        test_the_entry_follows_the_recipe(directory, source)
        test_one_store_holds_one_slot_per_identity(directory, source)
        test_the_store_location_is_normalized(directory, source)
        test_a_published_dependency_is_found_not_built(directory, source)
        test_opting_out_returns_to_the_build_directory(directory, source)
        test_a_recipe_change_forgets_the_old_entry(directory, source)
        test_an_evicted_entry_reinstalls(directory, source)
        test_the_store_requires_an_identity(directory, source)
        test_publishing_is_atomic(directory)
        test_racing_publishes_leave_one_whole_entry(directory)
        test_racing_installs_stage_privately(directory)

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
