#
# Copyright (C) 2022  Autodesk, Inc. All Rights Reserved.
#
# SPDX-License-Identifier: Apache-2.0
#

SET(_target
    "RV_DEPS_JPEGTURBO"
)

IF(RV_USE_PACKAGE_MANAGER)
  #
  # ====== PACKAGE MANAGER MODE (Conan via find_package) ======
  #
  MESSAGE(STATUS "Finding ${_target} from Conan via find_package()")

  SET(_find_target
      libjpeg-turbo
  )

  # Use version from CYCOMMON.cmake
  FIND_PACKAGE(${_find_target} ${RV_DEPS_JPEGTURBO_VERSION} CONFIG REQUIRED)

  # Make libjpeg-turbo targets GLOBAL
  RV_MAKE_TARGETS_GLOBAL(libjpeg-turbo::jpeg libjpeg-turbo::turbojpeg)

  # Print package info for debugging
  RV_PRINT_PACKAGE_INFO("${_find_target}")

  LIST(APPEND RV_DEPS_LIST libjpeg-turbo::jpeg)
  LIST(APPEND RV_DEPS_LIST libjpeg-turbo::turbojpeg)

  # Set up staging directories from Conan package location
  RV_SETUP_PACKAGE_STAGING(${_target} ${_find_target})

  # Library naming conventions Conan libjpeg-turbo produces different naming than build-from-source
  IF(RV_TARGET_WINDOWS)
    SET(_winlibjpegname
        jpeg8.dll
    )
    SET(_winlibturbojpegname
        turbojpeg.dll
    )
  ENDIF()

  # CMake is not generating debug postfix for JpegTurbo
  RV_MAKE_STANDARD_LIB_NAME("jpeg" "8.2.2" "SHARED" "")
  SET(_libjpegname
      ${_libname}
  )
  SET(_libjpegpath
      ${_libpath}
  )

  RV_MAKE_STANDARD_LIB_NAME("turbojpeg" "0.2.0" "SHARED" "")
  SET(_libturbojpegname
      ${_libname}
  )

  # Copy libraries to staging area
  IF(NOT RV_TARGET_WINDOWS)
    RV_COPY_LIB_BIN_FOLDERS()
  ELSE()
    ADD_CUSTOM_COMMAND(
      COMMENT "Installing ${_target}'s libs and bin into ${RV_STAGE_LIB_DIR} and ${RV_STAGE_BIN_DIR}"
      OUTPUT ${RV_STAGE_BIN_DIR}/${_winlibjpegname} ${RV_STAGE_BIN_DIR}/${_libturbojpegname}
      COMMAND ${CMAKE_COMMAND} -E copy_directory ${_lib_dir} ${RV_STAGE_LIB_DIR}
      COMMAND ${CMAKE_COMMAND} -E copy ${_bin_dir}/${_winlibjpegname} ${RV_STAGE_BIN_DIR}
      COMMAND ${CMAKE_COMMAND} -E copy ${_bin_dir}/${_libturbojpegname} ${RV_STAGE_BIN_DIR}
      DEPENDS ${_target}
    )

    ADD_CUSTOM_TARGET(
      ${_target}-stage-target ALL
      DEPENDS ${RV_STAGE_BIN_DIR}/${_winlibjpegname} ${RV_STAGE_BIN_DIR}/${_winlibturbojpegname}
    )
  ENDIF()

  IF(NOT RV_TARGET_WINDOWS)
    ADD_CUSTOM_COMMAND(
      TARGET ${_target}
      POST_BUILD
      COMMENT "Copying jpegturbo's libjpeg ('${_libjpegpath}') to '${RV_STAGE_LIB_DIR}'."
      COMMAND ${CMAKE_COMMAND} -E copy ${_libjpegpath} ${RV_STAGE_LIB_DIR}
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

  # Include the original jpegturbo build logic
  INCLUDE(jpegturbo3)

ENDIF()
