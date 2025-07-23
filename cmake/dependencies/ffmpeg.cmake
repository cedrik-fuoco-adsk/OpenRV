#
# Copyright (C) 2025  Autodesk, Inc. All Rights Reserved.
#
# SPDX-License-Identifier: Apache-2.0
#

SET(_target
    "RV_DEPS_FFMPEG"
)

# Versions management
IF(RV_FFMPEG_7)
  SET(_version
      7.1
  )
ELSEIF(RV_FFMPEG_6)
  SET(_version
      6.1.1
  )
ELSE()
  # This shouldn't happen, but it could if there are changes the acceptable versions of FFmpeg in ffmpeg.cmake and this section is not updated accordingly.
  MESSAGE(FATAL_ERROR "The requested version of FFmpeg is not supported.")
ENDIF()

SET(_find_target
    ffmpeg
)

FIND_PACKAGE(${_find_target} ${_version} CONFIG REQUIRED)

# Prints the variables.
CONAN_PRINT_TARGET_VARIABLES("${_find_target}")

# Library naming conventions
IF(RV_FFMPEG_7)
  IF(RV_TARGET_DARWIN)
    SET(_ffmpeg_avutil_lib_name
        ${CMAKE_SHARED_LIBRARY_PREFIX}avutil.59${CMAKE_SHARED_LIBRARY_SUFFIX}
    )
    SET(_ffmpeg_swresample_lib_name
        ${CMAKE_SHARED_LIBRARY_PREFIX}swresample.5${CMAKE_SHARED_LIBRARY_SUFFIX}
    )
    SET(_ffmpeg_swscale_lib_name
        ${CMAKE_SHARED_LIBRARY_PREFIX}swscale.8${CMAKE_SHARED_LIBRARY_SUFFIX}
    )
    SET(_ffmpeg_avcodec_lib_name
        ${CMAKE_SHARED_LIBRARY_PREFIX}avcodec.61${CMAKE_SHARED_LIBRARY_SUFFIX}
    )
    SET(_ffmpeg_avformat_lib_name
        ${CMAKE_SHARED_LIBRARY_PREFIX}avformat.61${CMAKE_SHARED_LIBRARY_SUFFIX}
    )
  ELSEIF(RV_TARGET_LINUX)
    SET(_ffmpeg_avutil_lib_name
        ${CMAKE_SHARED_LIBRARY_PREFIX}avutil${CMAKE_SHARED_LIBRARY_SUFFIX}.59
    )
    SET(_ffmpeg_swresample_lib_name
        ${CMAKE_SHARED_LIBRARY_PREFIX}swresample${CMAKE_SHARED_LIBRARY_SUFFIX}.5
    )
    SET(_ffmpeg_swscale_lib_name
        ${CMAKE_SHARED_LIBRARY_PREFIX}swscale${CMAKE_SHARED_LIBRARY_SUFFIX}.8
    )
    SET(_ffmpeg_avcodec_lib_name
        ${CMAKE_SHARED_LIBRARY_PREFIX}avcodec${CMAKE_SHARED_LIBRARY_SUFFIX}.61
    )
    SET(_ffmpeg_avformat_lib_name
        ${CMAKE_SHARED_LIBRARY_PREFIX}avformat${CMAKE_SHARED_LIBRARY_SUFFIX}.61
    )
  ELSEIF(RV_TARGET_WINDOWS)
    SET(_ffmpeg_avutil_lib_name
        ${CMAKE_SHARED_LIBRARY_PREFIX}avutil-59${CMAKE_SHARED_LIBRARY_SUFFIX}
    )
    SET(_ffmpeg_swresample_lib_name
        ${CMAKE_SHARED_LIBRARY_PREFIX}swresample-5${CMAKE_SHARED_LIBRARY_SUFFIX}
    )
    SET(_ffmpeg_swscale_lib_name
        ${CMAKE_SHARED_LIBRARY_PREFIX}swscale-8${CMAKE_SHARED_LIBRARY_SUFFIX}
    )
    SET(_ffmpeg_avcodec_lib_name
        ${CMAKE_SHARED_LIBRARY_PREFIX}avcodec-61${CMAKE_SHARED_LIBRARY_SUFFIX}
    )
    SET(_ffmpeg_avformat_lib_name
        ${CMAKE_SHARED_LIBRARY_PREFIX}avformat-61${CMAKE_SHARED_LIBRARY_SUFFIX}
    )
  ENDIF()
ELSEIF(RV_FFMPEG_6)
  IF(RV_TARGET_DARWIN)
    SET(_ffmpeg_avutil_lib_name
        ${CMAKE_SHARED_LIBRARY_PREFIX}avutil.58${CMAKE_SHARED_LIBRARY_SUFFIX}
    )
    SET(_ffmpeg_swresample_lib_name
        ${CMAKE_SHARED_LIBRARY_PREFIX}swresample.4${CMAKE_SHARED_LIBRARY_SUFFIX}
    )
    SET(_ffmpeg_swscale_lib_name
        ${CMAKE_SHARED_LIBRARY_PREFIX}swscale.7${CMAKE_SHARED_LIBRARY_SUFFIX}
    )
    SET(_ffmpeg_avcodec_lib_name
        ${CMAKE_SHARED_LIBRARY_PREFIX}avcodec.60${CMAKE_SHARED_LIBRARY_SUFFIX}
    )
    SET(_ffmpeg_avformat_lib_name
        ${CMAKE_SHARED_LIBRARY_PREFIX}avformat.60${CMAKE_SHARED_LIBRARY_SUFFIX}
    )
  ELSEIF(RV_TARGET_LINUX)
    SET(_ffmpeg_avutil_lib_name
        ${CMAKE_SHARED_LIBRARY_PREFIX}avutil${CMAKE_SHARED_LIBRARY_SUFFIX}.58
    )
    SET(_ffmpeg_swresample_lib_name
        ${CMAKE_SHARED_LIBRARY_PREFIX}swresample${CMAKE_SHARED_LIBRARY_SUFFIX}.4
    )
    SET(_ffmpeg_swscale_lib_name
        ${CMAKE_SHARED_LIBRARY_PREFIX}swscale${CMAKE_SHARED_LIBRARY_SUFFIX}.7
    )
    SET(_ffmpeg_avcodec_lib_name
        ${CMAKE_SHARED_LIBRARY_PREFIX}avcodec${CMAKE_SHARED_LIBRARY_SUFFIX}.60
    )
    SET(_ffmpeg_avformat_lib_name
        ${CMAKE_SHARED_LIBRARY_PREFIX}avformat${CMAKE_SHARED_LIBRARY_SUFFIX}.60
    )
  ELSEIF(RV_TARGET_WINDOWS)
    SET(_ffmpeg_avutil_lib_name
        ${CMAKE_SHARED_LIBRARY_PREFIX}avutil-58${CMAKE_SHARED_LIBRARY_SUFFIX}
    )
    SET(_ffmpeg_swresample_lib_name
        ${CMAKE_SHARED_LIBRARY_PREFIX}swresample-4${CMAKE_SHARED_LIBRARY_SUFFIX}
    )
    SET(_ffmpeg_swscale_lib_name
        ${CMAKE_SHARED_LIBRARY_PREFIX}swscale-7${CMAKE_SHARED_LIBRARY_SUFFIX}
    )
    SET(_ffmpeg_avcodec_lib_name
        ${CMAKE_SHARED_LIBRARY_PREFIX}avcodec-60${CMAKE_SHARED_LIBRARY_SUFFIX}
    )
    SET(_ffmpeg_avformat_lib_name
        ${CMAKE_SHARED_LIBRARY_PREFIX}avformat-60${CMAKE_SHARED_LIBRARY_SUFFIX}
    )
  ENDIF()
ELSE()
  # This shouldn't happen. But it could if there are changes the acceptable versions of FFmpeg in ffmpeg.cmake and this section is not updated accordingly.
  MESSAGE(FATAL_ERROR "The requested version of FFmpeg is not supported.")
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

CONAN_SETUP_STAGING(${_target} ${_find_target})

# custom command to copy the library to the staging area

SET(${_target}-stage-flag
    ${RV_STAGE_LIB_DIR}/${_target}-stage-flag
)

ADD_CUSTOM_TARGET(
  clean-${_target}
  COMMENT "Cleaning '${_target}' ..."
  COMMAND ${CMAKE_COMMAND} -E remove_directory ${_base_dir}
  COMMAND ${CMAKE_COMMAND} -E remove_directory ${RV_DEPS_BASE_DIR}/cmake/dependencies/${_target}-prefix
)

IF(RV_TARGET_WINDOWS)
  ADD_CUSTOM_COMMAND(
    TARGET ${_target}
    POST_BUILD
    COMMENT "Installing ${_target}'s libs and bin into ${RV_STAGE_LIB_DIR} and ${RV_STAGE_BIN_DIR}"
    # Note: The FFmpeg build stores both the import lib and the dll in the install bin directory
    COMMAND ${CMAKE_COMMAND} -E copy_directory ${_install_dir}/bin ${RV_STAGE_LIB_DIR}
    COMMAND ${CMAKE_COMMAND} -E copy_directory ${_install_dir}/bin ${RV_STAGE_BIN_DIR}
    COMMAND cmake -E touch ${${_target}-stage-flag}
    BYPRODUCTS ${${_target}-stage-flag}
  )
ELSE()
  ADD_CUSTOM_COMMAND(
    TARGET ${_target}
    POST_BUILD
    COMMENT "Installing ${_target}'s libs into ${RV_STAGE_LIB_DIR}"
    COMMAND ${CMAKE_COMMAND} -E copy_directory ${_lib_dir} ${RV_STAGE_LIB_DIR}
    COMMAND cmake -E touch ${${_target}-stage-flag}
    BYPRODUCTS ${${_target}-stage-flag}
  )
ENDIF()

ADD_CUSTOM_TARGET(
  ${_target}-stage-target ALL
  DEPENDS ${${_target}-stage-flag}
)

ADD_DEPENDENCIES(dependencies ${_target}-stage-target)

STRING(TOUPPER ${_find_target} _find_target_uppercase)
SET(RV_DEPS_${_find_target_uppercase}_VERSION
    ${${_find_target}_VERSION}
    CACHE INTERNAL "" FORCE
)
