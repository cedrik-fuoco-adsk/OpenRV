#
# Copyright (C) 2022  Autodesk, Inc. All Rights Reserved.
#
# SPDX-License-Identifier: Apache-2.0
#

SET(_target
    "RV_DEPS_FFMPEG"
)

IF(RV_USE_PACKAGE_MANAGER)
  #
  # ====== PACKAGE MANAGER MODE (Conan via find_package) ======
  #
  MESSAGE(STATUS "Finding ${_target} from Conan via find_package()")

  SET(_find_target
      ffmpeg
  )

  # Use version from CYCOMMON.cmake (RV_DEPS_FFMPEG_VERSION is set in CYCOMMON based on RV_FFMPEG option)
  SET(_version
      ${RV_DEPS_FFMPEG_VERSION}
  )

  # Strip leading 'n' if present (CYCOMMON uses "n6.1.2" format, Conan uses "6.1.2")
  STRING(
    REGEX
    REPLACE "^n" "" RV_DEPS_FFMPEG_VERSION "${_version}"
  )

  FIND_PACKAGE(${_find_target} ${RV_DEPS_FFMPEG_VERSION} CONFIG REQUIRED)

  # Make FFmpeg targets GLOBAL
  SET(_ffmpeg_targets
      ffmpeg::avutil ffmpeg::swresample ffmpeg::swscale ffmpeg::avcodec ffmpeg::avformat
  )
  RV_MAKE_TARGETS_GLOBAL(${_ffmpeg_targets})

  # Print package info for debugging
  RV_PRINT_PACKAGE_INFO("${_find_target}")

  # Library naming conventions - use CYCOMMON variables (RV_DEPS_FFMPEG_VERSION_LIB_*)
  IF(RV_TARGET_DARWIN)
    SET(_ffmpeg_avutil_lib_name
        ${CMAKE_SHARED_LIBRARY_PREFIX}avutil.${RV_DEPS_FFMPEG_VERSION_LIB_avutil}${CMAKE_SHARED_LIBRARY_SUFFIX}
    )
    SET(_ffmpeg_swresample_lib_name
        ${CMAKE_SHARED_LIBRARY_PREFIX}swresample.${RV_DEPS_FFMPEG_VERSION_LIB_swresample}${CMAKE_SHARED_LIBRARY_SUFFIX}
    )
    SET(_ffmpeg_swscale_lib_name
        ${CMAKE_SHARED_LIBRARY_PREFIX}swscale.${RV_DEPS_FFMPEG_VERSION_LIB_swscale}${CMAKE_SHARED_LIBRARY_SUFFIX}
    )
    SET(_ffmpeg_avcodec_lib_name
        ${CMAKE_SHARED_LIBRARY_PREFIX}avcodec.${RV_DEPS_FFMPEG_VERSION_LIB_avcodec}${CMAKE_SHARED_LIBRARY_SUFFIX}
    )
    SET(_ffmpeg_avformat_lib_name
        ${CMAKE_SHARED_LIBRARY_PREFIX}avformat.${RV_DEPS_FFMPEG_VERSION_LIB_avformat}${CMAKE_SHARED_LIBRARY_SUFFIX}
    )
  ELSEIF(RV_TARGET_LINUX)
    SET(_ffmpeg_avutil_lib_name
        ${CMAKE_SHARED_LIBRARY_PREFIX}avutil${CMAKE_SHARED_LIBRARY_SUFFIX}.${RV_DEPS_FFMPEG_VERSION_LIB_avutil}
    )
    SET(_ffmpeg_swresample_lib_name
        ${CMAKE_SHARED_LIBRARY_PREFIX}swresample${CMAKE_SHARED_LIBRARY_SUFFIX}.${RV_DEPS_FFMPEG_VERSION_LIB_swresample}
    )
    SET(_ffmpeg_swscale_lib_name
        ${CMAKE_SHARED_LIBRARY_PREFIX}swscale${CMAKE_SHARED_LIBRARY_SUFFIX}.${RV_DEPS_FFMPEG_VERSION_LIB_swscale}
    )
    SET(_ffmpeg_avcodec_lib_name
        ${CMAKE_SHARED_LIBRARY_PREFIX}avcodec${CMAKE_SHARED_LIBRARY_SUFFIX}.${RV_DEPS_FFMPEG_VERSION_LIB_avcodec}
    )
    SET(_ffmpeg_avformat_lib_name
        ${CMAKE_SHARED_LIBRARY_PREFIX}avformat${CMAKE_SHARED_LIBRARY_SUFFIX}.${RV_DEPS_FFMPEG_VERSION_LIB_avformat}
    )
  ELSEIF(RV_TARGET_WINDOWS)
    SET(_ffmpeg_avutil_lib_name
        ${CMAKE_SHARED_LIBRARY_PREFIX}avutil-${RV_DEPS_FFMPEG_VERSION_LIB_avutil}${CMAKE_SHARED_LIBRARY_SUFFIX}
    )
    SET(_ffmpeg_swresample_lib_name
        ${CMAKE_SHARED_LIBRARY_PREFIX}swresample-${RV_DEPS_FFMPEG_VERSION_LIB_swresample}${CMAKE_SHARED_LIBRARY_SUFFIX}
    )
    SET(_ffmpeg_swscale_lib_name
        ${CMAKE_SHARED_LIBRARY_PREFIX}swscale-${RV_DEPS_FFMPEG_VERSION_LIB_swscale}${CMAKE_SHARED_LIBRARY_SUFFIX}
    )
    SET(_ffmpeg_avcodec_lib_name
        ${CMAKE_SHARED_LIBRARY_PREFIX}avcodec-${RV_DEPS_FFMPEG_VERSION_LIB_avcodec}${CMAKE_SHARED_LIBRARY_SUFFIX}
    )
    SET(_ffmpeg_avformat_lib_name
        ${CMAKE_SHARED_LIBRARY_PREFIX}avformat-${RV_DEPS_FFMPEG_VERSION_LIB_avformat}${CMAKE_SHARED_LIBRARY_SUFFIX}
    )
  ENDIF()

  SET(_ffmpeg_libs
      avutil swresample swscale avcodec avformat
  )

  FOREACH(
    _ffmpeg_lib
    ${_ffmpeg_libs}
  )
    LIST(APPEND RV_DEPS_LIST ffmpeg::${_ffmpeg_lib})
  ENDFOREACH()

  # Set up staging directories from Conan package location
  RV_SETUP_PACKAGE_STAGING(${_target} ${_find_target})

  SET(_base_dir
      ${RV_DEPS_BASE_DIR}/${_target}
  )

  # Clean target
  ADD_CUSTOM_TARGET(
    clean-${_target}
    COMMENT "Cleaning '${_target}' ..."
    COMMAND ${CMAKE_COMMAND} -E remove_directory ${_base_dir}
    COMMAND ${CMAKE_COMMAND} -E remove_directory ${RV_DEPS_BASE_DIR}/cmake/dependencies/${_target}-prefix
  )

  SET(${_target}-stage-flag
      ${RV_STAGE_LIB_DIR}/${_target}-stage-flag
  )

  # Copy libraries to staging area
  IF(RV_TARGET_WINDOWS)
    ADD_CUSTOM_COMMAND(
      COMMENT "Installing ${_target}'s libs and bin into ${RV_STAGE_LIB_DIR} and ${RV_STAGE_BIN_DIR}"
      OUTPUT ${${_target}-stage-flag}
      COMMAND ${CMAKE_COMMAND} -E copy_directory ${_lib_dir} ${RV_STAGE_LIB_DIR}
      COMMAND ${CMAKE_COMMAND} -E copy_directory ${_bin_dir} ${RV_STAGE_BIN_DIR}
      COMMAND cmake -E touch ${${_target}-stage-flag}
      DEPENDS ${_target}
    )
  ELSE()
    ADD_CUSTOM_COMMAND(
      COMMENT "Installing ${_target}'s libs into ${RV_STAGE_LIB_DIR}"
      OUTPUT ${${_target}-stage-flag}
      COMMAND ${CMAKE_COMMAND} -E copy_directory ${_lib_dir} ${RV_STAGE_LIB_DIR}
      COMMAND cmake -E touch ${${_target}-stage-flag}
      DEPENDS ${_target}
    )
  ENDIF()

  ADD_CUSTOM_TARGET(
    ${_target}-stage-target ALL
    DEPENDS ${${_target}-stage-flag}
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

  # Include the original ffmpeg build logic
  INCLUDE(ffmpeg3)

ENDIF()
