#
# Copyright (C) 2022  Autodesk, Inc. All Rights Reserved.
#
# SPDX-License-Identifier: Apache-2.0
#

#
# Debugging options
OPTION(RV_VERBOSE_INVOCATION "Show the compiler/link command invocation." OFF)
OPTION(RV_SHOW_ALL_VARIABLES "Displays all build variables." ON)

#
# General build options
#
# RV_DEPS_BASE_DIR stays local to the build directory: it holds dependency source, build and stamp trees, which embed absolute paths and must not be shared.
# Only *installed* dependency trees are placed in the store, by RV_DEPS_INSTALL_ROOT in cmake/macros/rv_deps_store.cmake.
SET(RV_DEPS_BASE_DIR
    "${CMAKE_BINARY_DIR}"
    CACHE STRING "RV's 3rd party cache location."
)
SET(RV_DEPS_DOWNLOAD_DIR
    "${RV_DEPS_BASE_DIR}/RV_DEPS_DOWNLOAD"
    CACHE STRING "RV's 3rd party download cache location."
)

IF(NOT EXISTS (${RV_DEPS_BASE_DIR}))
  FILE(MAKE_DIRECTORY ${RV_DEPS_BASE_DIR})
ENDIF()

IF(NOT EXISTS (${RV_DEPS_DOWNLOAD_DIR}))
  FILE(MAKE_DIRECTORY ${RV_DEPS_DOWNLOAD_DIR})
ENDIF()

#
# VFX Platform option
#
# That option is to control the versions of the external dependencies that OpenRV downloads and install based on the VFX platform.
#
# e.g. For CY2023, OCIO 2.2.x should be supported. For CY2024, OCIO 2.3.x should be supported.
#
# Supported VFX platform.
SET(RV_VFX_SUPPORTED_OPTIONS
    CY2023 CY2024 CY2025 CY2026
)
# Default option
SET(_RV_VFX_PLATFORM
    "CY2025"
)

IF(DEFINED RV_VFX_PLATFORM)
  # Match lowercase and uppercase.
  STRING(TOUPPER "${RV_VFX_PLATFORM}" _RV_VFX_PLATFORM)
  IF(NOT "${_RV_VFX_PLATFORM}" IN_LIST RV_VFX_SUPPORTED_OPTIONS)
    MESSAGE(FATAL_ERROR "RV_VFX_PLATFORM=${RV_VFX_PLATFORM} is unsupported. Supported values are: ${RV_VFX_SUPPORTED_OPTIONS}")
  ENDIF()
ENDIF()

# Overwrite the cache variable with the normalized (upper)case.
SET(RV_VFX_PLATFORM
    "${_RV_VFX_PLATFORM}"
    CACHE STRING "Set the VFX platform for installaing external dependencies" FORCE
)

SET_PROPERTY(
  CACHE RV_VFX_PLATFORM
  PROPERTY STRINGS ${_RV_VFX_PLATFORM}
)

#
# C/C++ standard options
#
# The C++ standard follows the VFX Reference Platform: CY2026 and later require C++20, earlier years stay on C++17. It is derived from RV_VFX_PLATFORM rather
# than set by the user, so that the standard RV is built with always matches the one its dependencies are built with.
#
IF(RV_VFX_PLATFORM STRGREATER_EQUAL "CY2026")
  SET(_RV_CPP_STANDARD
      "20"
  )
ELSE()
  SET(_RV_CPP_STANDARD
      "17"
  )
ENDIF()

# Re-derived on every configure (FORCE), like RV_VFX_PLATFORM above. Without it an existing build tree reconfigured to a newer VFX platform would keep the
# standard cached by its first configure and silently build CY2026 with C++17.
SET(RV_CPP_STANDARD
    "${_RV_CPP_STANDARD}"
    CACHE STRING "RV's general C++ coding standard" FORCE
)
SET_PROPERTY(
  CACHE RV_CPP_STANDARD
  PROPERTY STRINGS ${_RV_CPP_STANDARD}
)

# The C standard stays at C17 on every VFX platform. It is deliberately not tied to RV_CPP_STANDARD: there is no C20, and CMake silently ignores an invalid
# C_STANDARD value (emitting no -std flag at all, which would un-pin the C standard). C17 is the newest C standard with universal MSVC/GCC/Clang support, and
# the VFX Reference Platform pins only the C++ standard.
SET(RV_C_STANDARD
    "17"
    CACHE STRING "RV's general C coding standard"
)
SET_PROPERTY(
  CACHE RV_C_STANDARD
  PROPERTY STRINGS 99 11 17
)

#
# FFmpeg option
#
# This option is to control the version of FFmpeg that OpenRV downloads and installs.
#
# There will be one version used by default per major release. Any other version will require RV_FFMPEG env var to be set with the desired major version.
#

# Supported FFmpeg versions.
SET(RV_FFMPEG_SUPPORTED_OPTIONS
    6 7 8
)
# Default option
SET(_RV_FFMPEG
    "8"
)

IF(DEFINED RV_FFMPEG)
  SET(_RV_FFMPEG
      ${RV_FFMPEG}
  )
  IF(NOT "${_RV_FFMPEG}" IN_LIST RV_FFMPEG_SUPPORTED_OPTIONS)
    MESSAGE(FATAL_ERROR "RV_FFMPEG=${RV_FFMPEG} is unsupported. Supported values are: ${RV_FFMPEG_SUPPORTED_OPTIONS}")
  ENDIF()
ENDIF()

# Overwrite the cache variable
SET(RV_FFMPEG
    "${_RV_FFMPEG}"
    CACHE STRING "Set FFmpeg version for installing external depdendency" FORCE
)
SET_PROPERTY(
  CACHE RV_FFMPEG
  PROPERTY STRINGS ${_RV_FFMPEG}
)

#
# Dependency resolution option
#
# When ON, try find_package() for each dependency before building from source. When OFF (default), always build dependencies from source (current behavior).
#
# Per-dependency override: set RV_DEPS_<NAME>_FORCE_BUILD=ON to force building a specific dependency from source even when RV_DEPS_PREFER_INSTALLED=ON.
#
OPTION(RV_DEPS_PREFER_INSTALLED "Try find_package() for dependencies before building from source" OFF)

#
# Version matching mode for dependency resolution.
#
# Controls how RV_FIND_DEPENDENCY matches versions when RV_DEPS_PREFER_INSTALLED=ON. EXACT requires the exact version specified in CY*.cmake (default,
# recommended). MINIMUM accepts the specified version or newer (standard find_package behavior).
#
# Per-dependency override: set RV_DEPS_<NAME>_VERSION_MATCH=EXACT or MINIMUM to override the global setting for a specific dependency.
#
SET(RV_DEPS_VERSION_MATCH
    "EXACT"
    CACHE STRING "Version matching mode for find_package: EXACT or MINIMUM"
)
SET_PROPERTY(
  CACHE RV_DEPS_VERSION_MATCH
  PROPERTY STRINGS EXACT MINIMUM
)

#
# Build identity, manifest and artifact probing
#
# The build identity is a single authoritative description of the platform this build targets -- VFX platform, target OS and architecture, toolchain, build
# configuration, Python ABI series and Qt version -- computed once so that the CMake dependency path and the Conan profile cannot drift apart. It is reported at
# configure time and recorded in the build manifest.
#
# Everything in this group is read-only: it records and reports what the build already is and reroutes nothing. Turning RV_BUILD_IDENTITY off restores the
# previous configure output exactly.
#
OPTION(RV_BUILD_IDENTITY "Compute and report the build identity" ON)
OPTION(RV_BUILD_MANIFEST "Write a build manifest recording what this build is made of" ON)
OPTION(RV_DEPS_PROBE_ARTIFACTS "Probe prebuilt artifacts and record their facts in the build manifest" ON)

#
# Strict artifact probing: fail naming the missing inspection tool instead of recording the fact as unknown. The store path requires strict probing because a
# store entry that cannot be verified must not be used. A default build leaves this OFF so that a machine without readelf/otool/dumpbin still builds.
#
OPTION(RV_DEPS_PROBE_STRICT "Fail artifact probing when an inspection tool is missing" OFF)

#
# Identity-addressed dependency store (phase 1).
#
# When set, the *installed* trees of the dependencies named in RV_DEPS_STORE_ELIGIBLE are placed in this store, keyed by the build identity, instead of inside
# the build directory. Source, build and stamp trees stay local, because they embed absolute paths and are not portable -- see D4. When unset, the default,
# nothing is placed in a store and the layout is exactly as before.
#
# Eligibility is per dependency and starts empty: a dependency is named here only once its relocation check has passed, so the store never holds a dependency
# whose installed tree cannot be moved. See D5.
#
# The store is never required: building everything from source remains a supported mode on every platform.
#
SET(RV_DEPS_STORE
    ""
    CACHE STRING "Identity-addressed store for installed dependency trees (phase 1; unset preserves the in-build-directory layout)"
)
# Dependencies whose installed trees have been through the relocation gate. Each name here was installed, relocated, linked against and run from a different
# path before being added, and then verified by a first build populating the store and a second build directory reusing it -- see
# docs/build_system/dependency_store.md. RV_DEPS_ZLIB passed the gate on 2026-10-12: status relocatable, with its shared library loaded from the relocated tree
# and no reference to the path it was installed at.
SET(RV_DEPS_STORE_ELIGIBLE
    "RV_DEPS_ZLIB"
    CACHE STRING "Semicolon-separated dependency targets whose installed trees may be placed in the store; each must have passed its relocation check"
)
