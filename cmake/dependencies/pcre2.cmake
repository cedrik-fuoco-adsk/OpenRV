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
MESSAGE(STATUS "Appending to RV_DEPS_LIST")
LIST(APPEND RV_DEPS_LIST PCRE2::8BIT PCRE2::POSIX)

# Library naming conventions for Windows
SET(_pcre2_libname
    libpcre2-8-0${CMAKE_SHARED_LIBRARY_SUFFIX}
)
SET(_pcre2_libname_posix
    libpcre2-posix-3${CMAKE_SHARED_LIBRARY_SUFFIX}
)

SET(_pcre2_implibname
    libpcre2-8.dll.a
)
SET(_pcre2_implibname_posix
    libpcre2-posix.dll.a
)
MESSAGE(STATUS "Setting up staging")
CONAN_SETUP_STAGING(${_target} ${_find_target})
MESSAGE(STATUS "Staging done")
# Custom command to copy the library to the staging area
ADD_CUSTOM_COMMAND(
  TARGET ${_target}
  POST_BUILD
  COMMENT "Installing ${_target}'s libs and bin into ${RV_STAGE_LIB_DIR} and ${RV_STAGE_BIN_DIR}"
  COMMAND ${CMAKE_COMMAND} -E copy_directory ${_lib_dir} ${RV_STAGE_LIB_DIR}
  COMMAND ${CMAKE_COMMAND} -E copy_directory ${_bin_dir} ${RV_STAGE_BIN_DIR}
)

ADD_CUSTOM_TARGET(
  ${_target}-stage-target ALL
  DEPENDS ${RV_STAGE_BIN_DIR}/${_pcre2_libname} ${RV_STAGE_BIN_DIR}/${_pcre2_libname_posix}
)

ADD_DEPENDENCIES(dependencies ${_target}-stage-target)

STRING(TOUPPER ${_find_target} _find_target_uppercase)
SET(RV_DEPS_${_find_target_uppercase}_VERSION
    ${${_find_target}_VERSION}
    CACHE INTERNAL "" FORCE
)
