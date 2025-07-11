#
# Copyright (C) 2025  Autodesk, Inc. All Rights Reserved.
#
# SPDX-License-Identifier: Apache-2.0
#

SET(_target
    "RV_DEPS_IMATH"
)

SET(_find_target
    Imath
)

FIND_PACKAGE(${_find_target} 3.1.6 CONFIG REQUIRED)

# Prints the variables.
CONAN_PRINT_TARGET_VARIABLES("${_find_target}")

LIST(APPEND RV_DEPS_LIST Imath::Imath)

IF(RV_TARGET_DARWIN)
  SET(_libname
      ${CMAKE_SHARED_LIBRARY_PREFIX}Imath-3_1${RV_DEBUG_POSTFIX}.29.5.0${CMAKE_SHARED_LIBRARY_SUFFIX}
  )
ELSEIF(RV_TARGET_LINUX)
  SET(_libname
      ${CMAKE_SHARED_LIBRARY_PREFIX}Imath-3_1${RV_DEBUG_POSTFIX}${CMAKE_SHARED_LIBRARY_SUFFIX}.29.5.0
  )
ELSEIF(RV_TARGET_WINDOWS)
  SET(_libname
      ${CMAKE_SHARED_LIBRARY_PREFIX}Imath-3_1${RV_DEBUG_POSTFIX}${CMAKE_SHARED_LIBRARY_SUFFIX}
  )
ENDIF()

IF(RV_TARGET_WINDOWS)
  SET(_implibpath
      ${_lib_dir}/${CMAKE_IMPORT_LIBRARY_PREFIX}Imath-3_1${RV_DEBUG_POSTFIX}${CMAKE_IMPORT_LIBRARY_SUFFIX}
  )
ENDIF()

CONAN_SETUP_STAGING(${_target} ${_find_target})

IF(RV_TARGET_WINDOWS)
  ADD_CUSTOM_COMMAND(
    TARGET ${_target}
    POST_BUILD
    COMMENT "Installing ${_target}'s libs and bin into ${RV_STAGE_LIB_DIR} and ${RV_STAGE_BIN_DIR}"
    COMMAND ${CMAKE_COMMAND} -E copy_directory ${_lib_dir} ${RV_STAGE_LIB_DIR}
    COMMAND ${CMAKE_COMMAND} -E copy_directory ${_bin_dir} ${RV_STAGE_BIN_DIR}
  )
  ADD_CUSTOM_TARGET(
    ${_target}-stage-target ALL
    DEPENDS ${RV_STAGE_BIN_DIR}/${_libname}
  )
ELSE()
  ADD_CUSTOM_COMMAND(
    COMMENT "Installing ${_target}'s libs into ${RV_STAGE_LIB_DIR}"
    OUTPUT ${RV_STAGE_LIB_DIR}/${_libname}
    COMMAND ${CMAKE_COMMAND} -E copy_directory ${_lib_dir} ${RV_STAGE_LIB_DIR}
    DEPENDS ${_target}
  )
  ADD_CUSTOM_TARGET(
    ${_target}-stage-target ALL
    DEPENDS ${RV_STAGE_LIB_DIR}/${_libname}
  )
ENDIF()

ADD_DEPENDENCIES(dependencies ${_target}-stage-target)

STRING(TOUPPER ${_find_target} _find_target_uppercase)
SET(RV_DEPS_${_find_target_uppercase}_VERSION
    ${${_find_target}_VERSION}
    CACHE INTERNAL "" FORCE
)
