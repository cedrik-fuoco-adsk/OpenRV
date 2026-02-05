#
# Copyright (C) 2022  Autodesk, Inc. All Rights Reserved.
#
# SPDX-License-Identifier: Apache-2.0
#

SET(_target
    "RV_DEPS_IMATH"
)

IF(RV_USE_PACKAGE_MANAGER)
  #
  # ====== PACKAGE MANAGER MODE (Conan via find_package) ======
  #
  MESSAGE(STATUS "Finding ${_target} from Conan via find_package()")

  SET(_find_target
      Imath
  )

  # Use version from CYCOMMON.cmake
  FIND_PACKAGE(${_find_target} ${RV_DEPS_IMATH_VERSION} CONFIG REQUIRED)

  # Make Imath targets GLOBAL
  RV_MAKE_TARGETS_GLOBAL(Imath::Imath)

  # Print package info for debugging
  RV_PRINT_PACKAGE_INFO("${_find_target}")

  LIST(APPEND RV_DEPS_LIST Imath::Imath)

  # Library naming conventions (use CYCOMMON variables)
  IF(RV_TARGET_DARWIN)
    SET(_libname
        ${CMAKE_SHARED_LIBRARY_PREFIX}Imath-${RV_DEPS_IMATH_LIB_MAJOR}${RV_DEBUG_POSTFIX}.${RV_DEPS_IMATH_LIB_VER}${CMAKE_SHARED_LIBRARY_SUFFIX}
    )
  ELSEIF(RV_TARGET_LINUX)
    SET(_libname
        ${CMAKE_SHARED_LIBRARY_PREFIX}Imath-${RV_DEPS_IMATH_LIB_MAJOR}${RV_DEBUG_POSTFIX}${CMAKE_SHARED_LIBRARY_SUFFIX}.${RV_DEPS_IMATH_LIB_VER}
    )
  ELSEIF(RV_TARGET_WINDOWS)
    SET(_libname
        ${CMAKE_SHARED_LIBRARY_PREFIX}Imath-${RV_DEPS_IMATH_LIB_MAJOR}${RV_DEBUG_POSTFIX}${CMAKE_SHARED_LIBRARY_SUFFIX}
    )
  ENDIF()

  IF(RV_TARGET_WINDOWS)
    SET(_implibpath
        ${_lib_dir}/${CMAKE_IMPORT_LIBRARY_PREFIX}Imath-${RV_DEPS_IMATH_LIB_MAJOR}${RV_DEBUG_POSTFIX}${CMAKE_IMPORT_LIBRARY_SUFFIX}
    )
  ENDIF()

  # Set up staging directories from Conan package location
  RV_SETUP_PACKAGE_STAGING(${_target} ${_find_target})

  # Copy libraries to staging area
  IF(RV_TARGET_WINDOWS)
    ADD_CUSTOM_COMMAND(
      COMMENT "Installing ${_target}'s libs and bin into ${RV_STAGE_LIB_DIR} and ${RV_STAGE_BIN_DIR}"
      OUTPUT ${RV_STAGE_BIN_DIR}/${_libname}
      COMMAND ${CMAKE_COMMAND} -E copy_directory ${_lib_dir} ${RV_STAGE_LIB_DIR}
      COMMAND ${CMAKE_COMMAND} -E copy_directory ${_bin_dir} ${RV_STAGE_BIN_DIR}
      DEPENDS ${_target}
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

  # Include the original imath build logic
  INCLUDE(imath3)

ENDIF()
