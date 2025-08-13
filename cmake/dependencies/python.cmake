#
# Copyright (C) 2022  Autodesk, Inc. All Rights Reserved.
#
# SPDX-License-Identifier: Apache-2.0
#

SET(_python3_target
    "RV_DEPS_PYTHON3"
)

SET(_opentimelineio_target
    "RV_DEPS_OPENTIMELINEIO"
)

RV_VFX_SET_VARIABLE(_pyside_target CY2023 "RV_DEPS_PYSIDE2" CY2024 "RV_DEPS_PYSIDE6")

SET(PYTHON_VERSION_MAJOR
    3
)

RV_VFX_SET_VARIABLE(PYTHON_VERSION_MINOR CY2023 "10" CY2024 "11")

RV_VFX_SET_VARIABLE(PYTHON_VERSION_PATCH CY2023 "13" CY2024 "9")

SET(_python3_version
    "${PYTHON_VERSION_MAJOR}.${PYTHON_VERSION_MINOR}.${PYTHON_VERSION_PATCH}"
)

SET(RV_DEPS_PYTHON_VERSION_MAJOR
    ${PYTHON_VERSION_MAJOR}
)
SET(RV_DEPS_PYTHON_VERSION_SHORT
    "${PYTHON_VERSION_MAJOR}.${PYTHON_VERSION_MINOR}"
)

SET(_opentimelineio_version
    "0.16.0"
)

RV_VFX_SET_VARIABLE(_pyside_version CY2023 "5.15.10" CY2024 "6.5.3")

SET(_opentimelineio_download_url
    "https://github.com/AcademySoftwareFoundation/OpenTimelineIO"
)
SET(_opentimelineio_git_tag
    "v${_opentimelineio_version}"
)

RV_VFX_SET_VARIABLE(
  _pyside_archive_url
  CY2023
  "https://mirrors.ocf.berkeley.edu/qt/official_releases/QtForPython/pyside2/PySide2-${_pyside_version}-src/pyside-setup-opensource-src-${_pyside_version}.zip"
  CY2024
  "https://mirrors.ocf.berkeley.edu/qt/official_releases/QtForPython/pyside6/PySide6-${_pyside_version}-src/pyside-setup-everywhere-src-${_pyside_version}.zip"
)

RV_VFX_SET_VARIABLE(_pyside_download_hash CY2023 "87841aaced763b6b52e9b549e31a493f" CY2024 "515d3249c6e743219ff0d7dd25b8c8d8")

# Find Python using find_package instead of building from source
SET(Python_FIND_STRATEGY VERSION)
SET(Python_FIND_UNVERSIONED_NAMES FIRST)

# Look for the specific version we need
find_package(Python ${RV_DEPS_PYTHON_VERSION_SHORT} EXACT REQUIRED 
    COMPONENTS Interpreter Development.Module Development.Embed
)

# Verify we found the right version
if(NOT Python_VERSION VERSION_EQUAL "${_python3_version}")
    message(WARNING "Found Python ${Python_VERSION}, but expected ${_python3_version}")
endif()

CONAN_PRINT_TARGET_VARIABLES("Python")

# Set up variables for compatibility with the rest of the build system
SET(_python3_executable ${Python_EXECUTABLE})
SET(_include_dir ${Python_INCLUDE_DIRS})
SET(_python3_lib ${Python_LIBRARIES})

# Set up install directory for staging
SET(_install_dir
    ${RV_DEPS_BASE_DIR}/${_python3_target}/install
)
SET(_build_dir
    ${RV_DEPS_BASE_DIR}/${_python3_target}/build
)

# Windows-specific library naming
IF(RV_TARGET_WINDOWS)
  IF(CMAKE_BUILD_TYPE MATCHES "^Debug$")
    SET(PYTHON3_EXTRA_WIN_LIBRARY_SUFFIX_IF_DEBUG "_d")
  ELSE()
    SET(PYTHON3_EXTRA_WIN_LIBRARY_SUFFIX_IF_DEBUG "")
  ENDIF()
  
  SET(_python_name
      python${PYTHON_VERSION_MAJOR}${PYTHON_VERSION_MINOR}${PYTHON3_EXTRA_WIN_LIBRARY_SUFFIX_IF_DEBUG}
  )
  SET(_python3_lib_name
      ${_python_name}${CMAKE_SHARED_LIBRARY_SUFFIX}
  )
  
  # For staging purposes, we'll copy the found Python installation
  SET(_bin_dir ${_install_dir}/bin)
  SET(_lib_dir ${_install_dir}/libs)
ELSE()
  SET(_python_name
      python${PYTHON_VERSION_MAJOR}.${PYTHON_VERSION_MINOR}
  )
  SET(_python3_lib_name
      ${CMAKE_SHARED_LIBRARY_PREFIX}${_python_name}${CMAKE_SHARED_LIBRARY_SUFFIX}
  )
  
  SET(_lib_dir ${_install_dir}/lib)
ENDIF()

# OpenTimelineIO setup (Windows only)
IF(RV_TARGET_WINDOWS)
  FETCHCONTENT_DECLARE(
    ${_opentimelineio_target}
    GIT_REPOSITORY ${_opentimelineio_download_url}
    GIT_TAG ${_opentimelineio_git_tag}
    SOURCE_SUBDIR "src" # Avoids the top level CMakeLists.txt
  )

  FETCHCONTENT_MAKEAVAILABLE(${_opentimelineio_target})
ENDIF()

# PySide setup
FETCHCONTENT_DECLARE(
  ${_pyside_target}
  URL ${_pyside_archive_url}
  URL_HASH MD5=${_pyside_download_hash}
  SOURCE_SUBDIR "sources" # Avoids the top level CMakeLists.txt
)

FETCHCONTENT_MAKEAVAILABLE(${_pyside_target})

# Requirements installation
SET(_requirements_file
    "${PROJECT_SOURCE_DIR}/src/build/requirements.txt"
)
SET(_requirements_install_command
    "${_python3_executable}" -m pip install --upgrade -r "${_requirements_file}"
)

# Create a custom target for Python requirements installation
SET(${_python3_target}-requirements-flag
    ${_install_dir}/${_python3_target}-requirements-flag
)

ADD_CUSTOM_COMMAND(
  COMMENT "Installing requirements from ${_requirements_file}"
  OUTPUT ${${_python3_target}-requirements-flag}
  COMMAND ${CMAKE_COMMAND} -E make_directory ${_install_dir}
  COMMAND ${_requirements_install_command}
  COMMAND ${CMAKE_COMMAND} -E touch ${${_python3_target}-requirements-flag}
  DEPENDS ${_requirements_file}
)

ADD_CUSTOM_TARGET(
  ${_python3_target}-requirements
  DEPENDS ${${_python3_target}-requirements-flag}
)

# ##############################################################################################################################################################
# This is temporary until the patch gets into the official PyOpenGL repo.      #
# ##############################################################################################################################################################
# Only for Apple Intel. Windows and Linux uses the requirements.txt file to install PyOpenGL-accelerate.
IF(APPLE AND RV_TARGET_APPLE_X86_64)
  MESSAGE(STATUS "Patching PyOpenGL and building PyOpenGL from source")
  SET(_patch_pyopengl_command
      patch -p1 < ${CMAKE_CURRENT_SOURCE_DIR}/patch/pyopengl-accelerate.patch
  )

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
    DEPENDS ${_python3_target}-requirements
    BUILD_IN_SOURCE TRUE
    USES_TERMINAL_BUILD TRUE
  )

  # Ensure pyopengl_accelerate is built as part of the dependencies target
  ADD_DEPENDENCIES(dependencies pyopengl_accelerate)
ENDIF()
# ##############################################################################################################################################################

# PySide build commands
# TODO_QT: Maybe we could use something like NOT CY2023 since after 2023, it is Qt6 TODO_QT: Below code could be simplified, but for now it is faster to test.
IF(RV_VFX_PLATFORM STREQUAL CY2023)
  SET(_pyside_make_command_script
      "${PROJECT_SOURCE_DIR}/src/build/make_pyside.py"
  )
  SET(_pyside_make_command
      python3 "${_pyside_make_command_script}"
  )

  LIST(APPEND _pyside_make_command "--variant")
  LIST(APPEND _pyside_make_command ${CMAKE_BUILD_TYPE})
  LIST(APPEND _pyside_make_command "--source-dir")
  LIST(APPEND _pyside_make_command ${rv_deps_pyside2_SOURCE_DIR})
  LIST(APPEND _pyside_make_command "--output-dir")
  LIST(APPEND _pyside_make_command ${_install_dir})
  LIST(APPEND _pyside_make_command "--temp-dir")
  LIST(APPEND _pyside_make_command ${_build_dir})

  IF(DEFINED RV_DEPS_OPENSSL_INSTALL_DIR)
    LIST(APPEND _pyside_make_command "--openssl-dir")
    LIST(APPEND _pyside_make_command ${RV_DEPS_OPENSSL_INSTALL_DIR})
  ENDIF()

  LIST(APPEND _pyside_make_command "--python-dir")
  LIST(APPEND _pyside_make_command ${Python_STDLIB})  # Use found Python stdlib
  LIST(APPEND _pyside_make_command "--qt-dir")
  LIST(APPEND _pyside_make_command ${RV_DEPS_QT5_LOCATION})
  LIST(APPEND _pyside_make_command "--python-version")
  LIST(APPEND _pyside_make_command "${RV_DEPS_PYTHON_VERSION_SHORT}")
ELSEIF(RV_VFX_PLATFORM STREQUAL CY2024)
  SET(_pyside_make_command_script
      "${PROJECT_SOURCE_DIR}/src/build/make_pyside6.py"
  )
  SET(_pyside_make_command
      python3 "${_pyside_make_command_script}"
  )

  LIST(APPEND _pyside_make_command "--variant")
  LIST(APPEND _pyside_make_command ${CMAKE_BUILD_TYPE})
  LIST(APPEND _pyside_make_command "--source-dir")
  LIST(APPEND _pyside_make_command ${rv_deps_pyside6_SOURCE_DIR})
  LIST(APPEND _pyside_make_command "--output-dir")
  LIST(APPEND _pyside_make_command ${_install_dir})
  LIST(APPEND _pyside_make_command "--temp-dir")
  LIST(APPEND _pyside_make_command ${_build_dir})

  IF(DEFINED RV_DEPS_OPENSSL_INSTALL_DIR)
    LIST(APPEND _pyside_make_command "--openssl-dir")
    LIST(APPEND _pyside_make_command ${RV_DEPS_OPENSSL_INSTALL_DIR})
  ENDIF()

  LIST(APPEND _pyside_make_command "--python-dir")
  LIST(APPEND _pyside_make_command ${Python_STDLIB})  # Use found Python stdlib
  LIST(APPEND _pyside_make_command "--qt-dir")
  LIST(APPEND _pyside_make_command ${RV_DEPS_QT6_LOCATION})
  LIST(APPEND _pyside_make_command "--python-version")
  LIST(APPEND _pyside_make_command "${RV_DEPS_PYTHON_VERSION_SHORT}")
ENDIF()

SET(${_pyside_target}-build-flag
    ${_install_dir}/${_pyside_target}-build-flag
)

# TODO_QT: Maybe we could use something like NOT CY2023 since after 2023, it is Qt6 TODO_QT: Below code could be simplified, but for now it is faster to test.
IF(RV_VFX_PLATFORM STREQUAL CY2023)
  ADD_CUSTOM_COMMAND(
    COMMENT "Building PySide2 using ${_pyside_make_command_script}"
    OUTPUT ${${_pyside_target}-build-flag}
    # First PySide build script on Windows which doesn't respect '--debug' option
    COMMAND ${CMAKE_COMMAND} -E copy ${PROJECT_SOURCE_DIR}/src/build/patch_PySide2/windows_desktop.py
            ${rv_deps_pyside2_SOURCE_DIR}/build_scripts/platforms/windows_desktop.py
    COMMAND ${_pyside_make_command} --prepare --build
    COMMAND ${CMAKE_COMMAND} -E touch ${${_pyside_target}-build-flag}
    DEPENDS ${_pyside_make_command_script} ${${_python3_target}-requirements-flag}
    USES_TERMINAL
  )

  SET(_build_flag_depends
      ${${_pyside_target}-build-flag}
  )
ELSEIF(RV_VFX_PLATFORM STREQUAL CY2024)
  ADD_CUSTOM_COMMAND(
    COMMENT "Building PySide6 using ${_pyside_make_command_script}"
    OUTPUT ${${_pyside_target}-build-flag}
    COMMAND ${_pyside_make_command} --prepare --build
    COMMAND ${CMAKE_COMMAND} -E touch ${${_pyside_target}-build-flag}
    DEPENDS ${_pyside_make_command_script} ${${_python3_target}-requirements-flag}
    USES_TERMINAL
  )

  SET(_build_flag_depends
      ${${_pyside_target}-build-flag}
  )
ENDIF()

# Staging targets - copy Python installation to staging area
IF(RV_TARGET_WINDOWS)
  SET(_copy_commands
      COMMAND ${CMAKE_COMMAND} -E copy_directory ${Python_STDLIB} ${RV_STAGE_LIB_DIR}
      COMMAND ${CMAKE_COMMAND} -E copy_directory ${_include_dir} ${RV_STAGE_INCLUDE_DIR}
      COMMAND ${CMAKE_COMMAND} -E copy ${_python3_executable} ${RV_STAGE_BIN_DIR}/
      COMMAND ${CMAKE_COMMAND} -E copy ${_python3_lib} ${RV_STAGE_BIN_DIR}/${_python3_lib_name}
  )

  IF(RV_VFX_CY2024)
    # Copy DLLs directory if it exists in the Python installation
    GET_FILENAME_COMPONENT(_python_root ${_python3_executable} DIRECTORY)
    GET_FILENAME_COMPONENT(_python_root ${_python_root} DIRECTORY)
    SET(_python_dlls_dir ${_python_root}/DLLs)
    
    IF(EXISTS ${_python_dlls_dir})
      LIST(
        APPEND
        _copy_commands
        COMMAND
        ${CMAKE_COMMAND}
        -E
        copy_directory
        ${_python_dlls_dir}
        ${RV_STAGE_ROOT_DIR}/DLLs
      )
    ENDIF()
  ENDIF()

  ADD_CUSTOM_COMMAND(
    COMMENT "Installing ${_python3_target}'s include and libs into staging area"
    OUTPUT ${RV_STAGE_BIN_DIR}/${_python3_lib_name}
    ${_copy_commands}
    DEPENDS ${${_python3_target}-requirements-flag} ${_build_flag_depends}
  )

  ADD_CUSTOM_TARGET(
    ${_python3_target}-stage-target ALL
    DEPENDS ${RV_STAGE_BIN_DIR}/${_python3_lib_name}
  )
ELSE()
  ADD_CUSTOM_COMMAND(
    COMMENT "Installing ${_python3_target}'s include and libs into staging area"
    OUTPUT ${RV_STAGE_LIB_DIR}/${_python3_lib_name}
    COMMAND ${CMAKE_COMMAND} -E copy_directory ${Python_STDLIB} ${RV_STAGE_LIB_DIR}
    COMMAND ${CMAKE_COMMAND} -E copy_directory ${_include_dir} ${RV_STAGE_INCLUDE_DIR}
    COMMAND ${CMAKE_COMMAND} -E copy ${_python3_executable} ${RV_STAGE_BIN_DIR}/
    COMMAND ${CMAKE_COMMAND} -E copy ${_python3_lib} ${RV_STAGE_LIB_DIR}/${_python3_lib_name}
    DEPENDS ${${_python3_target}-requirements-flag} ${_build_flag_depends}
  )
  ADD_CUSTOM_TARGET(
    ${_python3_target}-stage-target ALL
    DEPENDS ${RV_STAGE_LIB_DIR}/${_python3_lib_name}
  )
ENDIF()

# Python::Python target is already created by Conan, so we just add it to the deps list
LIST(APPEND RV_DEPS_LIST Python::Python)

ADD_DEPENDENCIES(dependencies ${_python3_target}-stage-target)

# Set cache variables for compatibility
SET(RV_DEPS_PYTHON3_VERSION
    ${Python_VERSION}
    CACHE INTERNAL "" FORCE
)
SET(RV_DEPS_PYSIDE_VERSION
    ${_pyside_version}
    CACHE INTERNAL "" FORCE
)

SET(RV_DEPS_PYTHON3_EXECUTABLE
    ${_python3_executable}
    CACHE INTERNAL "" FORCE
)
