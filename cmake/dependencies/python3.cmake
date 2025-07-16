#
# Copyright (C) 2022 Autodesk, Inc. All Rights Reserved.
#
# SPDX-License-Identifier: Apache-2.0
#

# Define the target names for Python and PySide dependencies
SET(_python3_target "RV_DEPS_PYTHON3")
SET(_opentimelineio_target "RV_DEPS_OPENTIMELINEIO")
RV_VFX_SET_VARIABLE(_pyside_target CY2023 "RV_DEPS_PYSIDE2" CY2024 "RV_DEPS_PYSIDE6")

# Define Python version components based on VFX platform
SET(PYTHON_VERSION_MAJOR 3)
RV_VFX_SET_VARIABLE(PYTHON_VERSION_MINOR CY2023 "10" CY2024 "11")
RV_VFX_SET_VARIABLE(PYTHON_VERSION_PATCH CY2023 "13" CY2024 "9")

# Construct the full Python version string
SET(_python3_version "${PYTHON_VERSION_MAJOR}.${PYTHON_VERSION_MINOR}.${PYTHON_VERSION_PATCH}")

# Set Python version variables for external use
SET(RV_DEPS_PYTHON_VERSION_MAJOR ${PYTHON_VERSION_MAJOR})
SET(RV_DEPS_PYTHON_VERSION_SHORT "${PYTHON_VERSION_MAJOR}.${PYTHON_VERSION_MINOR}")

# Define OpenTimelineIO and PySide versions (these are external dependencies)
SET(_opentimelineio_version "0.16.0")
RV_VFX_SET_VARIABLE(_pyside_version CY2023 "5.15.10" CY2024 "6.5.3")

# Define installation directories for Python
SET(_install_dir "${RV_DEPS_BASE_DIR}/${_python3_target}/install")
SET(_source_dir "${RV_DEPS_BASE_DIR}/${_python3_target}/src")
SET(_build_dir "${RV_DEPS_BASE_DIR}/${_python3_target}/build")

# Declare FetchContent for OpenTimelineIO (Windows only) and PySide
IF(RV_TARGET_WINDOWS)
  FETCHCONTENT_DECLARE(
    ${_opentimelineio_target}
    GIT_REPOSITORY "${_opentimelineio_download_url}"
    GIT_TAG "${_opentimelineio_git_tag}"
    SOURCE_SUBDIR "src" # Avoids the top level CMakeLists.txt
  )
  FETCHCONTENT_MAKEAVAILABLE(${_opentimelineio_target})
ENDIF()

FETCHCONTENT_DECLARE(
  ${_pyside_target}
  URL "${_pyside_archive_url}"
  URL_HASH MD5=${_pyside_download_hash}
  SOURCE_SUBDIR "sources" # Avoids the top level CMakeLists.txt
)
FETCHCONTENT_MAKEAVAILABLE(${_pyside_target})

# Define Python-build-standalone specific variables
SET(_python_build_standalone_base_url "https://github.com/indygreg/python-build-standalone/releases/download")
SET(_python_build_standalone_build_date "20240415") # Example build date, update as needed

# Determine the correct python-build-standalone archive based on OS and architecture
IF(RV_TARGET_DARWIN)
  IF(RV_TARGET_APPLE_ARM64)
    SET(_python_build_standalone_arch "aarch64-apple-darwin")
  ELSE()
    SET(_python_build_standalone_arch "x86_64-apple-darwin")
  ENDIF()
  SET(_python_build_standalone_archive_type "tar.gz")
  SET(_python_build_standalone_file_suffix "-install_only.tar.gz")
  SET(_python_build_standalone_lib_prefix "") # No prefix for libpython on macOS
ELSEIF(RV_TARGET_LINUX)
  SET(_python_build_standalone_arch "x86_64-unknown-linux-gnu")
  SET(_python_build_standalone_archive_type "tar.gz")
  SET(_python_build_standalone_file_suffix "-install_only.tar.gz")
  SET(_python_build_standalone_lib_prefix "lib") # e.g., libpython3.10.so
ELSEIF(RV_TARGET_WINDOWS)
  SET(_python_build_standalone_arch "x86_64-pc-windows-msvc-shared")
  SET(_python_build_standalone_archive_type "zip")
  SET(_python_build_standalone_file_suffix "-install_only.zip")
  SET(_python_build_standalone_lib_prefix "") # e.g., python310.dll
ENDIF()

SET(_python3_download_url
  "${_python_build_standalone_base_url}/${_python_build_standalone_build_date}/cpython-${_python3_version}+${_python_build_standalone_build_date}-${_python_build_standalone_arch}${_python_build_standalone_file_suffix}"
)

# NOTE: Replace these with actual MD5 hashes for the chosen python-build-standalone archives!
IF(RV_VFX_PLATFORM STREQUAL CY2023)
  IF(RV_TARGET_DARWIN)
    IF(RV_TARGET_APPLE_ARM64)
      SET(_python3_download_hash "78b1c16a9fd032997ba92a60f46a64f795cd18ff335659dfdf6096df277b24d5")
    ELSE()
      SET(_python3_download_hash "78b1c16a9fd032997ba92a60f46a64f795cd18ff335659dfdf6096df277b24d5")
    ENDIF()
  ELSEIF(RV_TARGET_LINUX)
    SET(_python3_download_hash "78b1c16a9fd032997ba92a60f46a64f795cd18ff335659dfdf6096df277b24d5")
  ELSEIF(RV_TARGET_WINDOWS)
    SET(_python3_download_hash "78b1c16a9fd032997ba92a60f46a64f795cd18ff335659dfdf6096df277b24d5")
  ENDIF()
ELSEIF(RV_VFX_PLATFORM STREQUAL CY2024)
  IF(RV_TARGET_DARWIN)
    IF(RV_TARGET_APPLE_ARM64)
      SET(_python3_download_hash "78b1c16a9fd032997ba92a60f46a64f795cd18ff335659dfdf6096df277b24d5")
    ELSE()
      SET(_python3_download_hash "78b1c16a9fd032997ba92a60f46a64f795cd18ff335659dfdf6096df277b24d5")
    ENDIF()
  ELSEIF(RV_TARGET_LINUX)
    SET(_python3_download_hash "78b1c16a9fd032997ba92a60f46a64f795cd18ff335659dfdf6096df277b24d5")
  ELSEIF(RV_TARGET_WINDOWS)
    SET(_python3_download_hash "78b1c16a9fd032997ba92a60f46a64f795cd18ff335659dfdf6096df277b24d5")
  ENDIF()
ENDIF()

# Define the Python interpreter script (make_python.py)
SET(_python3_make_command_script "${PROJECT_SOURCE_DIR}/src/build/make_python.py")
SET(_python3_make_command "${PYTHON_EXECUTABLE}" "${_python3_make_command_script}") # Use system Python to run it

# Arguments for make_python.py (only for PySide and requirements now)
LIST(APPEND _python3_make_command "--variant")
LIST(APPEND _python3_make_command ${CMAKE_BUILD_TYPE})
LIST(APPEND _python3_make_command "--output-dir")
LIST(APPEND _python3_make_command ${_install_dir})
LIST(APPEND _python3_make_command "--temp-dir")
LIST(APPEND _python3_make_command ${_build_dir})
LIST(APPEND _python3_make_command "--vfx_platform")
RV_VFX_SET_VARIABLE(_vfx_platform_ CY2023 "2023" CY2024 "2024")
LIST(APPEND _python3_make_command ${_vfx_platform_})
IF(RV_TARGET_WINDOWS)
  LIST(APPEND _python3_make_command "--opentimelineio-source-dir")
  LIST(APPEND _python3_make_command ${rv_deps_opentimelineio_SOURCE_DIR})
  LIST(APPEND _python3_make_command "--python-version")
  LIST(APPEND _python3_make_command "${PYTHON_VERSION_MAJOR}${PYTHON_VERSION_MINOR}")
ENDIF()

# PySide build commands (unchanged from original logic)
IF(RV_VFX_PLATFORM STREQUAL CY2023)
  SET(_pyside_make_command_script "${PROJECT_SOURCE_DIR}/src/build/make_pyside.py")
  SET(_pyside_make_command "${PYTHON_EXECUTABLE}" "${_pyside_make_command_script}")
  LIST(APPEND _pyside_make_command "--variant")
  LIST(APPEND _pyside_make_command ${CMAKE_BUILD_TYPE})
  LIST(APPEND _pyside_make_command "--source-dir")
  LIST(APPEND _pyside_make_command ${rv_deps_pyside2_SOURCE_DIR})
  LIST(APPEND _pyside_make_command "--output-dir")
  LIST(APPEND _pyside_make_command ${_install_dir})
  LIST(APPEND _pyside_make_command "--temp-dir")
  LIST(APPEND _pyside_make_command ${_build_dir})
  LIST(APPEND _pyside_make_command "--python-dir")
  LIST(APPEND _pyside_make_command ${_install_dir})
  LIST(APPEND _pyside_make_command "--qt-dir")
  LIST(APPEND _pyside_make_command ${RV_DEPS_QT5_LOCATION})
  LIST(APPEND _pyside_make_command "--python-version")
  LIST(APPEND _pyside_make_command "${RV_DEPS_PYTHON_VERSION_SHORT}")
ELSEIF(RV_VFX_PLATFORM STREQUAL CY2024)
  SET(_pyside_make_command_script "${PROJECT_SOURCE_DIR}/src/build/make_pyside6.py")
  SET(_pyside_make_command "${PYTHON_EXECUTABLE}" "${_pyside_make_command_script}")
  LIST(APPEND _pyside_make_command "--variant")
  LIST(APPEND _pyside_make_command ${CMAKE_BUILD_TYPE})
  LIST(APPEND _pyside_make_command "--source-dir")
  LIST(APPEND _pyside_make_command ${rv_deps_pyside6_SOURCE_DIR})
  LIST(APPEND _pyside_make_command "--output-dir")
  LIST(APPEND _pyside_make_command ${_install_dir})
  LIST(APPEND _pyside_make_command "--temp-dir")
  LIST(APPEND _pyside_make_command ${_build_dir})
  LIST(APPEND _pyside_make_command "--python-dir")
  LIST(APPEND _pyside_make_command ${_install_dir})
  LIST(APPEND _pyside_make_command "--qt-dir")
  LIST(APPEND _pyside_make_command ${RV_DEPS_QT6_LOCATION})
  LIST(APPEND _pyside_make_command "--python-version")
  LIST(APPEND _pyside_make_command "${RV_DEPS_PYTHON_VERSION_SHORT}")
ENDIF()

# Define Python paths based on python-build-standalone structure
IF(RV_TARGET_WINDOWS)
  IF(CMAKE_BUILD_TYPE MATCHES "^Debug$")
    SET(PYTHON3_EXTRA_WIN_LIBRARY_SUFFIX_IF_DEBUG "_d")
  ELSE()
    SET(PYTHON3_EXTRA_WIN_LIBRARY_SUFFIX_IF_DEBUG "")
  ENDIF()
  SET(_python_base_name "python") # The executable is usually just "python.exe"
  SET(_include_dir "${_install_dir}/include")
  SET(_bin_dir "${_install_dir}/bin")
  SET(_lib_dir "${_install_dir}/libs") # For .lib files
  SET(_python3_lib_name "${_python_base_name}${PYTHON_VERSION_MAJOR}${PYTHON_VERSION_MINOR}${PYTHON3_EXTRA_WIN_LIBRARY_SUFFIX_IF_DEBUG}${CMAKE_SHARED_LIBRARY_SUFFIX}")
  SET(_python3_lib "${_bin_dir}/${_python3_lib_name}") # The DLL is in bin
  SET(_python3_implib "${_lib_dir}/${_python_base_name}${PYTHON_VERSION_MAJOR}${PYTHON_VERSION_MINOR}${PYTHON3_EXTRA_WIN_LIBRARY_SUFFIX_IF_DEBUG}${CMAKE_IMPORT_LIBRARY_SUFFIX}")
  SET(_python3_executable "${_bin_dir}/${_python_base_name}${PYTHON3_EXTRA_WIN_LIBRARY_SUFFIX_IF_DEBUG}.exe")

  # When building in Debug, we need the Release name also: see below for add_custom_command.
  # This might not be needed with python-build-standalone, but keeping it for compatibility.
  SET(_python_release_libname "python${PYTHON_VERSION_MAJOR}${PYTHON_VERSION_MINOR}${CMAKE_STATIC_LIBRARY_SUFFIX}")
  SET(_python_release_libpath "${_lib_dir}/${_python_release_libname}")
  SET(_python_release_in_bin_libpath "${_bin_dir}/${_python_release_libname}")
ELSE() # Not WINDOWS
  SET(_python_name "python${PYTHON_VERSION_MAJOR}.${PYTHON_VERSION_MINOR}")
  SET(_include_dir "${_install_dir}/include/${_python_name}")
  SET(_lib_dir "${_install_dir}/lib")
  SET(_python3_lib_name "${CMAKE_SHARED_LIBRARY_PREFIX}${_python_name}${CMAKE_SHARED_LIBRARY_SUFFIX}")
  SET(_python3_lib "${_lib_dir}/${_python3_lib_name}")
  SET(_python3_executable "${_install_dir}/bin/python3")
ENDIF()

SET(_requirements_file "${PROJECT_SOURCE_DIR}/src/build/requirements.txt")
SET(_requirements_install_command "${_python3_executable}" -m pip install --upgrade -r "${_requirements_file}")

# EXTERNALPROJECT_ADD for python-build-standalone
EXTERNALPROJECT_ADD(
  ${_python3_target}
  URL ${_python3_download_url}
  URL_MD5 ${_python3_download_hash}
  DOWNLOAD_NAME ${_python3_target}_${_python3_version}.${_python_build_standalone_archive_type}
  DOWNLOAD_DIR ${RV_DEPS_DOWNLOAD_DIR}
  DOWNLOAD_EXTRACT_TIMESTAMP TRUE
  SOURCE_DIR ${_source_dir} # This will be the extracted root of the archive
  INSTALL_DIR ${_install_dir} # This will be the target install directory
  # No configure, build, or patch commands needed as it's pre-built
  CONFIGURE_COMMAND ""
  BUILD_COMMAND ""
  PATCH_COMMAND ""
  INSTALL_COMMAND
    # Copy the extracted contents to the final install directory
    ${CMAKE_COMMAND} -E copy_directory "${_source_dir}/python" "${_install_dir}"
  BUILD_BYPRODUCTS
    ${_python3_executable}
    ${_python3_lib}
    ${_python3_implib} # Only for Windows
  BUILD_IN_SOURCE TRUE # This means the extracted archive is treated as the source
  BUILD_ALWAYS FALSE
  USES_TERMINAL_BUILD TRUE
)

# ##############################################################################################################################################################
# This is temporary until the patch gets into the official PyOpenGL repo.
# ##############################################################################################################################################################
# Only for Apple Intel. Windows and Linux uses the requirements.txt file to install PyOpenGL-accelerate.
IF(APPLE AND RV_TARGET_APPLE_X86_64)
  MESSAGE(STATUS "Patching PyOpenGL and building PyOpenGL from source")
  SET(_patch_pyopengl_command patch -p1 < ${CMAKE_CURRENT_SOURCE_DIR}/patch/pyopengl-accelerate.patch)
  EXTERNALPROJECT_ADD(
    pyopengl_accelerate
    URL "https://github.com/mcfletch/pyopengl/archive/refs/tags/release-3.1.8.tar.gz"
    URL_MD5 "d7a9e2f8c2d981b58776ded865b3e22a"
    DOWNLOAD_NAME release-3.1.8.tar.gz
    DOWNLOAD_DIR ${RV_DEPS_DOWNLOAD_DIR}
    DOWNLOAD_EXTRACT_TIMESTAMP TRUE
    SOURCE_DIR ${CMAKE_BINARY_DIR}/pyopengl_accelerate
    PATCH_COMMAND ${_patch_pyopengl_command}
    CONFIGURE_COMMAND ""
    BUILD_COMMAND "${_python3_executable}" -m pip install ./accelerate
    INSTALL_COMMAND ${CMAKE_COMMAND} -E touch ${CMAKE_BINARY_DIR}/pyopengl_accelerate/.pip_installed
    BUILD_BYPRODUCTS ${CMAKE_BINARY_DIR}/pyopengl_accelerate/setup.py
    DEPENDS ${${_python3_target}-requirements-flag}
    BUILD_IN_SOURCE TRUE
    USES_TERMINAL_BUILD TRUE
  )
  # Ensure pyopengl_accelerate is built as part of the dependencies target
  ADD_DEPENDENCIES(dependencies pyopengl_accelerate)
ENDIF()
# ##############################################################################################################################################################

SET(${_python3_target}-requirements-flag "${_install_dir}/${_python3_target}-requirements-flag")
ADD_CUSTOM_COMMAND(
  COMMENT "Installing requirements from ${_requirements_file}"
  OUTPUT ${${_python3_target}-requirements-flag}
  COMMAND ${_requirements_install_command}
  COMMAND cmake -E touch ${${_python3_target}-requirements-flag}
  DEPENDS ${_python3_target} ${_requirements_file}
)

IF(RV_TARGET_WINDOWS AND CMAKE_BUILD_TYPE MATCHES "^Debug$")
  # OCIO v2.2's pybind11 doesn't find python<ver>.lib in Debug since the name is python<ver>_d.lib.
  # This might not be needed with python-build-standalone, but keeping it for compatibility.
  ADD_CUSTOM_COMMAND(
    TARGET ${_python3_target}
    POST_BUILD
    COMMENT "Copying Debug Python lib as a unversionned file for Debug"
    COMMAND cmake -E copy_if_different ${_python3_implib} ${_python_release_libpath}
    COMMAND cmake -E copy_if_different ${_python3_implib} ${_python_release_in_bin_libpath}
    DEPENDS ${_python3_target} ${_requirements_file}
  )
ENDIF()

SET(${_pyside_target}-build-flag "${_install_dir}/${_pyside_target}-build-flag")
# TODO_QT: Maybe we could use something like NOT CY2023 since after 2023, it is Qt6
# TODO_QT: Below code could be simplified, but for now it is faster to test.
IF(RV_VFX_PLATFORM STREQUAL CY2023)
  ADD_CUSTOM_COMMAND(
    COMMENT "Building PySide2 using ${_pyside_make_command_script}"
    OUTPUT ${${_pyside_target}-build-flag}
    # First PySide build script on Windows which doesn't respect '--debug' option
    COMMAND ${CMAKE_COMMAND} -E copy ${PROJECT_SOURCE_DIR}/src/build/patch_PySide2/windows_desktop.py ${rv_deps_pyside2_SOURCE_DIR}/build_scripts/platforms/windows_desktop.py
    COMMAND ${_pyside_make_command} --prepare --build
    COMMAND cmake -E touch ${${_pyside_target}-build-flag}
    DEPENDS ${_python3_target} ${_pyside_make_command_script} ${${_python3_target}-requirements-flag}
    USES_TERMINAL
  )
  SET(_build_flag_depends ${${_pyside_target}-build-flag})
ELSEIF(RV_VFX_PLATFORM STREQUAL CY204)
  ADD_CUSTOM_COMMAND(
    COMMENT "Building PySide6 using ${_pyside_make_command_script}"
    OUTPUT ${${_pyside_target}-build-flag}
    COMMAND ${_pyside_make_command} --prepare --build
    COMMAND cmake -E touch ${${_pyside_target}-build-flag}
    DEPENDS ${_python3_target} ${_pyside_make_command_script} ${${_python3_target}-requirements-flag}
    USES_TERMINAL
  )
  SET(_build_flag_depends ${${_pyside_target}-build-flag})
ENDIF()

IF(RV_TARGET_WINDOWS)
  SET(_copy_commands
    COMMAND ${CMAKE_COMMAND} -E copy_directory ${_install_dir}/lib ${RV_STAGE_LIB_DIR}
    COMMAND ${CMAKE_COMMAND} -E copy_directory ${_install_dir}/include ${RV_STAGE_INCLUDE_DIR}
    COMMAND ${CMAKE_COMMAND} -E copy_directory ${_install_dir}/bin ${RV_STAGE_BIN_DIR}
  )
  IF(RV_VFX_CY2024)
    LIST(
      APPEND _copy_commands
      COMMAND ${CMAKE_COMMAND} -E copy_directory ${_install_dir}/DLLs ${RV_STAGE_ROOT_DIR}/DLLs
    )
  ENDIF()
  ADD_CUSTOM_COMMAND(
    COMMENT "Installing ${_python3_target}'s include and libs into ${RV_STAGE_LIB_DIR}"
    OUTPUT ${RV_STAGE_BIN_DIR}/${_python3_lib_name}
    ${_copy_commands}
    DEPENDS ${_python3_target} ${${_python3_target}-requirements-flag} ${_build_flag_depends}
  )
  ADD_CUSTOM_TARGET(
    ${_python3_target}-stage-target ALL
    DEPENDS ${RV_STAGE_BIN_DIR}/${_python3_lib_name}
  )
ELSE()
  ADD_CUSTOM_COMMAND(
    COMMENT "Installing ${_python3_target}'s include and libs into ${RV_STAGE_LIB_DIR}"
    OUTPUT ${RV_STAGE_LIB_DIR}/${_python3_lib_name}
    COMMAND ${CMAKE_COMMAND} -E copy_directory ${_install_dir}/lib ${RV_STAGE_LIB_DIR}
    COMMAND ${CMAKE_COMMAND} -E copy_directory ${_install_dir}/include ${RV_STAGE_INCLUDE_DIR}
    COMMAND ${CMAKE_COMMAND} -E copy_directory ${_install_dir}/bin ${RV_STAGE_BIN_DIR}
    DEPENDS ${_python3_target} ${${_python3_target}-requirements-flag} ${_build_flag_depends}
  )
  ADD_CUSTOM_TARGET(
    ${_python3_target}-stage-target ALL
    DEPENDS ${RV_STAGE_LIB_DIR}/${_python3_lib_name}
  )
ENDIF()

ADD_LIBRARY(Python::Python SHARED IMPORTED GLOBAL)
ADD_DEPENDENCIES(Python::Python ${_python3_target})
SET_PROPERTY(
  TARGET Python::Python
  PROPERTY IMPORTED_LOCATION ${_python3_lib}
)
SET_PROPERTY(
  TARGET Python::Python
  PROPERTY IMPORTED_SONAME ${_python3_lib_name}
)
IF(RV_TARGET_WINDOWS)
  SET_PROPERTY(
    TARGET Python::Python
    PROPERTY IMPORTED_IMPLIB ${_python3_implib}
  )
ENDIF()
SET_PROPERTY(
  TARGET Python::Python
  PROPERTY INTERFACE_INCLUDE_DIRECTORIES ${_include_dir}
)

LIST(APPEND RV_DEPS_LIST Python::Python)

SET(RV_DEPS_PYTHON3_VERSION
    ${_python3_version}
    CACHE INTERNAL "" FORCE
)

SET(RV_DEPS_PYSIDE_VERSION
    ${_pyside_version}
    CACHE INTERNAL "" FORCE
)

# FFmpeg customization to make it use this version of python
SET_PROPERTY(
  GLOBAL APPEND
  PROPERTY "RV_FFMPEG_DEPENDS" RV_DEPS_PYTHON3
)
SET_PROPERTY(
  GLOBAL APPEND
  PROPERTY "RV_FFMPEG_EXTRA_C_OPTIONS" "--extra-cflags=-I${_include_dir}"
)
IF(RV_TARGET_WINDOWS)
  SET_PROPERTY(
    GLOBAL APPEND
    PROPERTY "RV_FFMPEG_EXTRA_LIBPATH_OPTIONS" "--extra-ldflags=-LIBPATH:${_lib_dir}"
  )
ELSE()
  SET_PROPERTY(
    GLOBAL APPEND
    PROPERTY "RV_FFMPEG_EXTRA_LIBPATH_OPTIONS" "--extra-ldflags=-L${_lib_dir}"
  )
ENDIF()
SET_PROPERTY(
  GLOBAL APPEND
  PROPERTY "RV_FFMPEG_EXTERNAL_LIBS" "--enable-libpython"
)
