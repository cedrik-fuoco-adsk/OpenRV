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

SET(RV_CPP_STANDARD
    "17"
    CACHE STRING "RV's general C++ coding standard"
)
SET_PROPERTY(
  CACHE RV_CPP_STANDARD
  PROPERTY STRINGS 14 17
)

SET(RV_C_STANDARD
    "17"
    CACHE STRING "RV's general C coding standard"
)
SET_PROPERTY(
  CACHE RV_C_STANDARD
  PROPERTY STRINGS C99 11 17
)

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
    "CY2023"
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
    "6"
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
# Package Manager option
#
# This option controls whether OpenRV uses pre-built packages from a package manager (Conan) or builds dependencies from source using ExternalProject_Add.
#
# When OFF (default): Dependencies are built from source (traditional mode) When ON: Dependencies are found via find_package() from Conan-provided packages
#
# Usage with Conan: 1. conan install conanfile.py --build=missing -of=build/Release 2. cmake -B build -S . -DRV_USE_PACKAGE_MANAGER=ON \
# -DCMAKE_TOOLCHAIN_FILE=build/Release/generators/conan_toolchain.cmake
#
OPTION(RV_USE_PACKAGE_MANAGER "Use pre-built packages from package manager (Conan) instead of building from source" OFF)

IF(RV_USE_PACKAGE_MANAGER)
  MESSAGE(STATUS "RV_USE_PACKAGE_MANAGER=ON: Using Conan packages via find_package()")
  # Verify that CMAKE_TOOLCHAIN_FILE is set (required for Conan integration)
  IF(NOT DEFINED CMAKE_TOOLCHAIN_FILE)
    MESSAGE(WARNING "RV_USE_PACKAGE_MANAGER=ON but CMAKE_TOOLCHAIN_FILE not set. "
                    "You may need to run: conan install conanfile.py --build=missing -of=<build_dir> "
                    "and pass -DCMAKE_TOOLCHAIN_FILE=<build_dir>/generators/conan_toolchain.cmake"
    )
  ENDIF()
ELSE()
  MESSAGE(STATUS "RV_USE_PACKAGE_MANAGER=OFF: Building dependencies from source (traditional mode)")
ENDIF()
