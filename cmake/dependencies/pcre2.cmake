#
# Copyright (C) 2025  Autodesk, Inc. All Rights Reserved.
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

SET(_find_target
    pcre2
)

MESSAGE(STATUS "Finding ${_find_target}")
FIND_PACKAGE(${_find_target} CONFIG REQUIRED)

MESSAGE(STATUS "Found ${_find_target}")
# Prints the variables.
CONAN_PRINT_TARGET_VARIABLES("${_find_target}")
# Create wrapper interface targets since we can't modify imported Conan targets
ADD_LIBRARY(RV_PCRE2_8BIT INTERFACE)
ADD_LIBRARY(RV_PCRE2_POSIX INTERFACE)

# Link to the Conan targets and add the required compile definitions
TARGET_LINK_LIBRARIES(
  RV_PCRE2_8BIT
  INTERFACE PCRE2::8BIT
)
TARGET_COMPILE_DEFINITIONS(
  RV_PCRE2_8BIT
  INTERFACE PCRE2_CODE_UNIT_WIDTH=8
)

TARGET_LINK_LIBRARIES(
  RV_PCRE2_POSIX
  INTERFACE PCRE2::POSIX
)
TARGET_COMPILE_DEFINITIONS(
  RV_PCRE2_POSIX
  INTERFACE PCRE2_CODE_UNIT_WIDTH=8
)

MESSAGE(STATUS "Appending wrapper targets to RV_DEPS_LIST")
LIST(APPEND RV_DEPS_LIST RV_PCRE2_8BIT RV_PCRE2_POSIX)

# Library naming conventions for Windows (Conan/MSVC naming)
SET(_pcre2_libname
    pcre2-8${CMAKE_SHARED_LIBRARY_SUFFIX}
)
SET(_pcre2_libname_posix
    pcre2-posix${CMAKE_SHARED_LIBRARY_SUFFIX}
)

SET(_pcre2_implibname
    pcre2-8${CMAKE_IMPORT_LIBRARY_SUFFIX}
)
SET(_pcre2_implibname_posix
    pcre2-posix${CMAKE_IMPORT_LIBRARY_SUFFIX}
)

# Get include directory from target since pcre2_INCLUDE_DIRS may not be set by Conan config
IF(NOT ${_find_target}_INCLUDE_DIRS)
  GET_TARGET_PROPERTY(_pcre2_include_dir PCRE2::8BIT INTERFACE_INCLUDE_DIRECTORIES)
  SET(${_find_target}_INCLUDE_DIRS
      ${_pcre2_include_dir}
  )
  MESSAGE(STATUS "Got PCRE2 include dir from target: ${_pcre2_include_dir}")
ENDIF()

MESSAGE(STATUS "Setting up staging")
CONAN_SETUP_STAGING(${_target} ${_find_target})
MESSAGE(STATUS "Staging done")

# Set the output files for dependency tracking
SET(_pcre2_stage_output
    ${RV_STAGE_BIN_DIR}/${_pcre2_libname} ${RV_STAGE_BIN_DIR}/${_pcre2_libname_posix}
)

# Custom command to copy the library to the staging area - use OUTPUT for proper dependency tracking
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

STRING(TOUPPER ${_find_target} _find_target_uppercase)
SET(RV_DEPS_${_find_target_uppercase}_VERSION
    ${${_find_target}_VERSION}
    CACHE INTERNAL "" FORCE
)
