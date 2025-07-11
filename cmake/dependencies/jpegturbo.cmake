#
# Copyright (C) 2025  Autodesk, Inc. All Rights Reserved.
#
# SPDX-License-Identifier: Apache-2.0
#

SET(_target
    "RV_DEPS_JPEGTURBO"
)

SET(_find_target
    libjpeg-turbo
)

FIND_PACKAGE(${_find_target} 2.1.4 CONFIG REQUIRED)

# Prints the variables.
CONAN_PRINT_TARGET_VARIABLES("${_find_target}")

LIST(APPEND RV_DEPS_LIST libjpeg-turbo::jpeg)
LIST(APPEND RV_DEPS_LIST libjpeg-turbo::turbojpeg)

CONAN_SETUP_STAGING(${_target} ${_find_target})

# CMake is not generating debug postfix for JpegTurbo
RV_MAKE_STANDARD_LIB_NAME("jpeg" "62.3.0" "SHARED" "")
SET(_winlibjpegname
    jpeg62.dll
)
SET(_libjpegname
    ${_libname}
)
SET(_libjpegpath
    ${_libpath}
)
IF(RV_TARGET_WINDOWS)
  SET(_libjpegimplibpath
      ${_implibpath}
  )
ENDIF()
SET(_winlibjpegpath
    ${_bin_dir}/${_winlibjpegname}
)

# CMake is not generating debug postfix for JpegTurbo Note: This library is added by one of our DEP (TIFF or a JPEG DEP) and thus we're copying it. Ideally, we
# should use the above and remove this one.
RV_MAKE_STANDARD_LIB_NAME("jpeg" "8.2.2" "SHARED" "")
SET(_libjpeg62name
    ${_libname}
)
SET(_libjpeg62path
    ${_libpath}
)

# CMake is not generating debug postfix for JpegTurbo
RV_MAKE_STANDARD_LIB_NAME("turbojpeg" "0.2.0" "SHARED" "")
SET(_winlibturbojpegname
    turbojpeg.dll
)
SET(_libturbojpegname
    ${_libname}
)

# The macro is using existing _target, _libname, _lib_dir and _bin_dir variabless
IF(NOT RV_TARGET_WINDOWS)
  RV_COPY_LIB_BIN_FOLDERS()
ELSE()
  # Don't use RV_COPY_LIB_BIN_FOLDERS() because RV don't need the whole bin directory. Copying the two DLLs from jpegturbo.
  ADD_CUSTOM_COMMAND(
    TARGET ${_target}
    POST_BUILD
    COMMENT "Installing ${_target}'s libs and bin into ${RV_STAGE_LIB_DIR} and ${RV_STAGE_BIN_DIR}"
    COMMAND ${CMAKE_COMMAND} -E copy_directory ${_lib_dir} ${RV_STAGE_LIB_DIR}
    COMMAND ${CMAKE_COMMAND} -E copy ${_bin_dir}/${_winlibjpegname} ${RV_STAGE_BIN_DIR}
    COMMAND ${CMAKE_COMMAND} -E copy ${_bin_dir}/${_libturbojpegname} ${RV_STAGE_BIN_DIR}
  )

  ADD_CUSTOM_TARGET(
    ${_target}-stage-target ALL
    DEPENDS ${RV_STAGE_BIN_DIR}/${_libname}
  )
ENDIF()

IF(NOT RV_TARGET_WINDOWS)
  # RV_COPY_LIB_BIN_FOLDERS doesn't copy symlinks so this command is used for _libjpeg62path
  ADD_CUSTOM_COMMAND(
    TARGET ${_target}
    POST_BUILD
    COMMENT "Copying jpegturbo's libjpeg ('${_libjpeg62path}') to '${RV_STAGE_LIB_DIR}'."
    COMMAND ${CMAKE_COMMAND} -E copy ${_libjpeg62path} ${RV_STAGE_LIB_DIR}
  )
ENDIF()

ADD_DEPENDENCIES(dependencies ${_target}-stage-target)

STRING(TOUPPER ${_find_target} _find_target_uppercase)
SET(RV_DEPS_${_find_target_uppercase}_VERSION
    ${${_find_target}_VERSION}
    CACHE INTERNAL "" FORCE
)
