#
# Copyright (C) 2022  Autodesk, Inc. All Rights Reserved.
#
# SPDX-License-Identifier: Apache-2.0
#

SET(_target
    "RV_DEPS_ZLIB"
)

IF(RV_USE_PACKAGE_MANAGER)
  #
  # ====== PACKAGE MANAGER MODE (Conan via find_package) ======
  #
  MESSAGE(STATUS "Finding ${_target} from Conan via find_package()")

  SET(_find_target
      ZLIB
  )

  # Use version from CYCOMMON.cmake
  FIND_PACKAGE(${_find_target} ${RV_DEPS_ZLIB_VERSION} CONFIG REQUIRED)

  # Make ZLIB targets GLOBAL
  RV_MAKE_TARGETS_GLOBAL(ZLIB::ZLIB)

  # Print package info for debugging
  RV_PRINT_PACKAGE_INFO("${_find_target}")

  LIST(APPEND RV_DEPS_LIST ZLIB::ZLIB)

  # Library naming conventions (Conan produces different names)
  IF(RV_TARGET_WINDOWS)
    # Conan produces zlib1.dll for release builds
    IF(CMAKE_BUILD_TYPE MATCHES "^Debug$")
      SET(_zlibname
          "zlibd1"
      )
    ELSE()
      SET(_zlibname
          "zlib1"
      )
    ENDIF()
  ELSE()
    SET(_zlibname
        "z"
    )
  ENDIF()

  SET(_libname
      ${CMAKE_SHARED_LIBRARY_PREFIX}${_zlibname}${CMAKE_SHARED_LIBRARY_SUFFIX}
  )

  IF(RV_TARGET_WINDOWS)
    SET(_implibname
        ${CMAKE_IMPORT_LIBRARY_PREFIX}${_zlibname}${CMAKE_IMPORT_LIBRARY_SUFFIX}
    )
    SET(_implibpath
        ${_lib_dir}/${_implibname}
    )
  ENDIF()

  # Set up staging directories from Conan package location
  RV_SETUP_PACKAGE_STAGING(${_target} ${_find_target})

  # Copy libraries to staging area
  IF(RV_TARGET_WINDOWS)
    # FFmpeg expect "zlib" in Release and Debug.
    IF(CMAKE_BUILD_TYPE MATCHES "^Debug$")
      ADD_CUSTOM_COMMAND(
        TARGET ${_target}
        POST_BUILD
        COMMENT "Renaming the ZLIB import debug lib to the name FFmpeg is expecting (release name)"
        COMMAND ${CMAKE_COMMAND} -E copy ${_implibpath} ${_lib_dir}/zlib.lib
      )
    ENDIF()

    # Use OUTPUT-based command for proper dependency tracking
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
  ELSEIF(RV_TARGET_DARWIN)
    ADD_CUSTOM_COMMAND(
      COMMENT "Installing ${_target}'s libs into ${RV_STAGE_LIB_DIR}"
      OUTPUT ${RV_STAGE_LIB_DIR}/${_libname}
      COMMAND ${CMAKE_INSTALL_NAME_TOOL} -id "@rpath/${_libname}" "${_lib_dir}/${_libname}"
      COMMAND ${CMAKE_COMMAND} -E copy_directory ${_lib_dir} ${RV_STAGE_LIB_DIR}
      DEPENDS ${_target}
    )
    ADD_CUSTOM_TARGET(
      ${_target}-stage-target ALL
      DEPENDS ${RV_STAGE_LIB_DIR}/${_libname}
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

  # Include the original zlib build logic
  INCLUDE(zlib3)

ENDIF()
