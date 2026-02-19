#
# Copyright (C) 2024  Autodesk, Inc. All Rights Reserved.
#
# SPDX-License-Identifier: Apache-2.0
#

# PCRE2 is only used on Windows (boost regex is used on other platforms)
IF(NOT RV_TARGET_WINDOWS)
  RETURN()
ENDIF()

SET(_target
    "RV_DEPS_PCRE2"
)

IF(RV_USE_PACKAGE_MANAGER)
  #
  # ====== PACKAGE MANAGER MODE (Conan via find_package) ======
  #
  MESSAGE(STATUS "Finding ${_target} from Conan via find_package()")

  SET(_find_target
      pcre2
  )

  FIND_PACKAGE(${_find_target} CONFIG REQUIRED)

  # Make PCRE2 targets GLOBAL
  RV_MAKE_TARGETS_GLOBAL(PCRE2::8BIT PCRE2::POSIX)

  # Print package info for debugging
  RV_PRINT_PACKAGE_INFO("${_find_target}")

  # Create wrapper interface targets with the names expected by source CMakeLists files The source code links to pcre2-8 and pcre2-posix, so we need to create
  # targets with those names
  ADD_LIBRARY(pcre2-8 INTERFACE)
  ADD_LIBRARY(pcre2-posix INTERFACE)

  # Link to the Conan targets and add the required compile definitions PCRE2_CODE_UNIT_WIDTH=8 MUST be defined before including pcre2.h
  TARGET_LINK_LIBRARIES(
    pcre2-8
    INTERFACE PCRE2::8BIT
  )
  TARGET_COMPILE_DEFINITIONS(
    pcre2-8
    INTERFACE PCRE2_CODE_UNIT_WIDTH=8
  )

  TARGET_LINK_LIBRARIES(
    pcre2-posix
    INTERFACE PCRE2::POSIX
  )
  TARGET_COMPILE_DEFINITIONS(
    pcre2-posix
    INTERFACE PCRE2_CODE_UNIT_WIDTH=8
  )

  LIST(APPEND RV_DEPS_LIST pcre2-8 pcre2-posix)

  # Library naming conventions for Windows (Conan/MSVC naming)
  SET(_pcre2_libname
      pcre2-8${CMAKE_SHARED_LIBRARY_SUFFIX}
  )
  SET(_pcre2_libname_posix
      pcre2-posix${CMAKE_SHARED_LIBRARY_SUFFIX}
  )

  # Get include directory from target since pcre2_INCLUDE_DIRS may not be set by Conan config
  IF(NOT ${_find_target}_INCLUDE_DIRS)
    GET_TARGET_PROPERTY(_pcre2_include_dir PCRE2::8BIT INTERFACE_INCLUDE_DIRECTORIES)
    SET(${_find_target}_INCLUDE_DIRS
        ${_pcre2_include_dir}
    )
  ENDIF()

  # Set up staging directories from Conan package location
  RV_SETUP_PACKAGE_STAGING(${_target} ${_find_target})

  # Set the output files for dependency tracking
  SET(_pcre2_stage_output
      ${RV_STAGE_BIN_DIR}/${_pcre2_libname} ${RV_STAGE_BIN_DIR}/${_pcre2_libname_posix}
  )

  # Copy libraries to staging area
  ADD_CUSTOM_COMMAND(
    COMMENT "Installing ${_target}'s libs and bin into ${RV_STAGE_LIB_DIR} and ${RV_STAGE_BIN_DIR}"
    OUTPUT ${_pcre2_stage_output}
    COMMAND ${CMAKE_COMMAND} -E copy_directory ${_lib_dir} ${RV_STAGE_LIB_DIR}
    COMMAND ${CMAKE_COMMAND} -E copy_directory ${_bin_dir} ${RV_STAGE_BIN_DIR}
    DEPENDS ${_target}
  )

  ADD_CUSTOM_TARGET(
    ${_target}-stage-target ALL
    DEPENDS ${_pcre2_stage_output}
  )

  ADD_DEPENDENCIES(dependencies ${_target}-stage-target)

  # Set version from found package
  STRING(TOUPPER ${_find_target} _find_target_uppercase)
  SET(RV_DEPS_${_find_target_uppercase}_VERSION
      ${${_find_target}_VERSION}
      CACHE INTERNAL "" FORCE
  )

ELSE()
  #
  # ====== TRADITIONAL MODE (Build from source) ======
  #
  MESSAGE(STATUS "Building ${_target} from source using ExternalProject_Add")

  # Include the original pcre2 build logic
  INCLUDE(${CMAKE_CURRENT_LIST_DIR}/build/pcre2.cmake)

ENDIF()
