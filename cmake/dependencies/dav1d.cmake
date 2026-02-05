#
# Copyright (C) 2022  Autodesk, Inc. All Rights Reserved.
#
# SPDX-License-Identifier: Apache-2.0
#

SET(_target
    "RV_DEPS_DAV1D"
)

IF(RV_USE_PACKAGE_MANAGER)
  #
  # ====== PACKAGE MANAGER MODE (Conan via find_package) ======
  #
  MESSAGE(STATUS "Finding ${_target} from Conan via find_package()")

  SET(_find_target
      dav1d
  )

  # Use version from CYCOMMON.cmake
  FIND_PACKAGE(${_find_target} ${RV_DEPS_DAV1D_VERSION} CONFIG REQUIRED)

  # Make dav1d targets GLOBAL
  RV_MAKE_TARGETS_GLOBAL(dav1d::dav1d)

  # Print package info for debugging
  RV_PRINT_PACKAGE_INFO("${_find_target}")

  LIST(APPEND RV_DEPS_LIST dav1d::dav1d)

  # Library naming conventions
  SET(_david_lib_name
      ${CMAKE_STATIC_LIBRARY_PREFIX}dav1d${CMAKE_STATIC_LIBRARY_SUFFIX}
  )

  # Set up staging directories from Conan package location
  RV_SETUP_PACKAGE_STAGING(${_target} ${_find_target})

  # Copy libraries to staging area
  IF(RV_TARGET_WINDOWS)
    ADD_CUSTOM_COMMAND(
      COMMENT "Installing ${_target}'s libs and bin into ${RV_STAGE_LIB_DIR} and ${RV_STAGE_BIN_DIR}"
      OUTPUT ${RV_STAGE_LIB_DIR}/${_david_lib_name}
      COMMAND ${CMAKE_COMMAND} -E copy_directory ${_lib_dir} ${RV_STAGE_LIB_DIR}
      COMMAND ${CMAKE_COMMAND} -E copy_directory ${_bin_dir} ${RV_STAGE_BIN_DIR}
      DEPENDS ${_target}
    )
    ADD_CUSTOM_TARGET(
      ${_target}-stage-target ALL
      DEPENDS ${RV_STAGE_LIB_DIR}/${_david_lib_name}
    )
  ELSE()
    ADD_CUSTOM_COMMAND(
      COMMENT "Installing ${_target}'s libs into ${RV_STAGE_LIB_DIR}"
      OUTPUT ${RV_STAGE_LIB_DIR}/${_david_lib_name}
      COMMAND ${CMAKE_COMMAND} -E copy_directory ${_lib_dir} ${RV_STAGE_LIB_DIR}
      DEPENDS ${_target}
    )
    ADD_CUSTOM_TARGET(
      ${_target}-stage-target ALL
      DEPENDS ${RV_STAGE_LIB_DIR}/${_david_lib_name}
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

  # Include the original dav1d build logic
  INCLUDE(dav1d3)

ENDIF()
