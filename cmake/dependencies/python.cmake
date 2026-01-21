#
# Copyright (C) 2022  Autodesk, Inc. All Rights Reserved.
#
# SPDX-License-Identifier: Apache-2.0
#

SET(_target
    "RV_DEPS_PYTHON3"
)

SET(_find_target
    Python
)

SET(_opentimelineio_target
    "RV_DEPS_OPENTIMELINEIO"
)

# PySide target variables removed - now handled by Conan

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

# PySide version variables removed - now handled by Conan

SET(_opentimelineio_download_url
    "https://github.com/AcademySoftwareFoundation/OpenTimelineIO"
)
SET(_opentimelineio_git_tag
    "v${_opentimelineio_version}"
)

# PySide archive URL variables removed - now handled by Conan

# PySide download hash variables removed - now handled by Conan

# Find Python using find_package instead of building from source
SET(Python_FIND_STRATEGY
    VERSION
)
SET(Python_FIND_UNVERSIONED_NAMES
    FIRST
)

# Look for the specific version we need
FIND_PACKAGE(
  ${_find_target} ${RV_DEPS_PYTHON_VERSION_SHORT} EXACT REQUIRED
  COMPONENTS Interpreter Development.Module Development.Embed
)

FIND_PACKAGE(pyside6 CONFIG REQUIRED)

# Verify we found the right version
IF(NOT Python_VERSION VERSION_EQUAL "${_python3_version}")
  MESSAGE(WARNING "Found Python ${Python_VERSION}, but expected ${_python3_version}")
ENDIF()

CONAN_PRINT_TARGET_VARIABLES("Python")
CONAN_PRINT_TARGET_VARIABLES("pyside6")

# Set up install directory for staging
SET(_install_dir
    ${RV_DEPS_BASE_DIR}/${_target}/install
)
SET(_build_dir
    ${RV_DEPS_BASE_DIR}/${_target}/build
)

# Windows-specific library naming
IF(RV_TARGET_WINDOWS)
  IF(CMAKE_BUILD_TYPE MATCHES "^Debug$")
    SET(PYTHON3_EXTRA_WIN_LIBRARY_SUFFIX_IF_DEBUG
        "_d"
    )
  ELSE()
    SET(PYTHON3_EXTRA_WIN_LIBRARY_SUFFIX_IF_DEBUG
        ""
    )
  ENDIF()

  SET(_python_name
      python${PYTHON_VERSION_MAJOR}${PYTHON_VERSION_MINOR}${PYTHON3_EXTRA_WIN_LIBRARY_SUFFIX_IF_DEBUG}
  )
  SET(_python3_lib_name
      ${_python_name}${CMAKE_SHARED_LIBRARY_SUFFIX}
  )

  # For staging purposes, we'll copy the found Python installation
  SET(_bin_dir
      ${_install_dir}/bin
  )
  SET(_lib_dir
      ${_install_dir}/libs
  )
ELSE()
  SET(_python_name
      python${PYTHON_VERSION_MAJOR}.${PYTHON_VERSION_MINOR}
  )
  SET(_python3_lib_name
      ${CMAKE_SHARED_LIBRARY_PREFIX}${_python_name}${CMAKE_SHARED_LIBRARY_SUFFIX}
  )

  SET(_lib_dir
      ${_install_dir}/lib
  )
ENDIF()

# TODO: This should be done by Python recipe in Conan, but it isn't yet. Set up variables for compatibility with the rest of the build system Make
# Python_INCLUDE_DIRS available in other CMake files.
# ------------------------------------------------------------------------------------------------
SET(Python_INCLUDE_DIRS
    "${Python_INCLUDE_DIRS}"
    CACHE INTERNAL "Python include directories" FORCE
)
SET(_include_dir
    ${Python_INCLUDE_DIRS}
)

IF(RV_TARGET_WINDOWS)
  CMAKE_PATH(SET _Python_ROOT_ NORMALIZE ${Python_INCLUDE_DIRS}/..)
ELSE()
  CMAKE_PATH(SET _Python_ROOT_ NORMALIZE ${Python_INCLUDE_DIRS}/../..)
ENDIF()

CMAKE_PATH(SET Python_LIB_DIR NORMALIZE ${_Python_ROOT_}/lib)
CMAKE_PATH(SET Python_BIN_DIR NORMALIZE ${_Python_ROOT_}/bin)

MESSAGE(STATUS "Cedrik debug: ${Python_LIB_DIR}")
MESSAGE(STATUS "Cedrik debug: ${Python_BIN_DIR}")
MESSAGE(STATUS "Cedrik debug: ${_Python_ROOT_}")
# Legacy variable for compatibility
IF(RV_TARGET_WINDOWS)
  SET(_python3_executable
      "${Python_BIN_DIR}/python${PYTHON3_EXTRA_WIN_LIBRARY_SUFFIX_IF_DEBUG}.exe"
  )
ELSE()
  SET(_python3_executable
      "${Python_BIN_DIR}/python"
  )
ENDIF()

SET(_python3_lib
    "${Python_LIB_DIR}/${_python3_lib_name}"
)
# Standard variables
SET(Python_EXECUTABLE
    ${_python3_executable}
)
SET(Python_LIBRARY
    ${_python3_lib}
)

STRING(REPLACE "." "" PYTHON_VERSION_SHORT_NO_DOT ${RV_DEPS_PYTHON_VERSION_SHORT})
IF(RV_TARGET_WINDOWS)
  SET(Python_LIBRARY
      "${Python_BIN_DIR}/python${PYTHON_VERSION_SHORT_NO_DOT}.lib"
  )
ENDIF()

SET(Python_ROOT
    "${_Python_ROOT_}"
)
# ------------------------------------------------------------------------------------------------

CONAN_SETUP_STAGING(${_target} ${_find_target})

# Add dependencies to the main target so it actually does something when built
ADD_DEPENDENCIES(${_target} ${_target}-stage-target)

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

# PySide6 is now handled by Conan - see openrvcore-conanfile.py

# Requirements installation
SET(_requirements_file
    "${PROJECT_SOURCE_DIR}/src/build/requirements.txt"
)

# On Windows, we need to set up the Visual Studio environment before running pip install because some packages (like OpenTimelineIO) need to compile C/C++
# extensions. Conan's VCVars generator creates conanvcvars.bat which sets up the VS environment. We also set CMAKE_ARGS to pass the generator to CMake inside
# pip's isolated build. Create a wrapper batch script to properly set environment and run pip.
IF(RV_TARGET_WINDOWS)
  SET(_conanvcvars_bat
      "${CMAKE_BINARY_DIR}/generators/conanvcvars.bat"
  )

  # Create a wrapper batch file that sets up the environment correctly We write to CMAKE_BINARY_DIR to ensure the directory exists at configure time.
  SET(_pip_wrapper_bat
      "${CMAKE_BINARY_DIR}/pip_install_wrapper.bat"
  )

  # Use CMAKE_ARGS to specify the generator using single quotes for the name. This quoting style ("-G 'Generator Name'") is often required for Python build
  # tools (like scikit-build) to correctly parse arguments with spaces.
  FILE(
    WRITE ${_pip_wrapper_bat}
    "@echo off
call \"${_conanvcvars_bat}\"
set CMAKE_ARGS=\"-G 'Visual Studio 17 2022'\"
\"${_python3_executable}\" -m pip install --upgrade -r \"${_requirements_file}\"
"
  )

  SET(_requirements_install_command
      ${_pip_wrapper_bat}
  )
ELSE()
  SET(_requirements_install_command
      "${_python3_executable}" -m pip install --upgrade -r "${_requirements_file}"
  )
ENDIF()

# Create a custom target for Python requirements installation
SET(${_target}-requirements-flag
    ${_install_dir}/${_target}-requirements-flag
)

ADD_CUSTOM_COMMAND(
  COMMENT "Installing requirements from ${_requirements_file}: ${_requirements_install_command}"
  OUTPUT ${${_target}-requirements-flag}
  COMMAND ${CMAKE_COMMAND} -E make_directory ${_install_dir}
  COMMAND ${_requirements_install_command}
  COMMAND ${CMAKE_COMMAND} -E touch ${${_target}-requirements-flag}
  DEPENDS ${_requirements_file}
)

ADD_CUSTOM_TARGET(
  ${_target}-requirements
  DEPENDS ${${_target}-requirements-flag}
)

# ##############################################################################################################################################################
# This is temporary until the patch gets into the official PyOpenGL repo.      #
# ##############################################################################################################################################################
# Only for Apple Intel. Windows and Linux uses the requirements.txt file to install PyOpenGL-accelerate.
IF(APPLE
   AND RV_TARGET_APPLE_X86_64
)
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
    DEPENDS ${_target}-requirements
    BUILD_IN_SOURCE TRUE
    USES_TERMINAL_BUILD TRUE
  )

  # Ensure pyopengl_accelerate is built as part of the dependencies target
  ADD_DEPENDENCIES(dependencies pyopengl_accelerate)
ENDIF()
# ##############################################################################################################################################################

# PySide build commands removed - now handled by Conan pyside6/6.5.3@openrv package

# Set empty build flag dependencies since PySide6 is handled by Conan
SET(_build_flag_depends
    ""
)

# Staging targets - copy Python installation to staging area
IF(RV_TARGET_WINDOWS)
  SET(_copy_commands
      COMMAND ${CMAKE_COMMAND} -E copy_directory ${_include_dir} ${RV_STAGE_INCLUDE_DIR} COMMAND ${CMAKE_COMMAND} -E copy_directory ${Python_BIN_DIR}
      ${RV_STAGE_BIN_DIR} COMMAND ${CMAKE_COMMAND} -E copy_directory ${Python_LIB_DIR} ${RV_STAGE_LIB_DIR}
  )

  IF(RV_VFX_CY2024)
    # Copy DLLs directory if it exists in the Python installation
    GET_FILENAME_COMPONENT(_python_root ${_python3_executable} DIRECTORY)
    GET_FILENAME_COMPONENT(_python_root ${_python_root} DIRECTORY)
    SET(_python_dlls_dir
        ${_python_root}/DLLs
    )

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
    COMMENT "Installing ${_target}'s include and libs into staging area"
    OUTPUT ${RV_STAGE_BIN_DIR}/${_python3_lib_name} ${_copy_commands}
    DEPENDS ${${_target}-requirements-flag} ${_build_flag_depends}
  )

  ADD_CUSTOM_TARGET(
    ${_target}-stage-target ALL
    DEPENDS ${RV_STAGE_BIN_DIR}/${_python3_lib_name}
  )
ELSE()
  ADD_CUSTOM_COMMAND(
    COMMENT "Installing ${_target}'s include and libs into staging area"
    OUTPUT ${RV_STAGE_LIB_DIR}/${_python3_lib_name}
    COMMAND ${CMAKE_COMMAND} -E copy_directory ${_include_dir} ${RV_STAGE_INCLUDE_DIR}
    COMMAND ${CMAKE_COMMAND} -E copy_directory ${Python_BIN_DIR} ${RV_STAGE_BIN_DIR}
    COMMAND ${CMAKE_COMMAND} -E copy_directory ${Python_LIB_DIR} ${RV_STAGE_LIB_DIR}
    DEPENDS ${${_target}-requirements-flag} ${_build_flag_depends}
  )
  ADD_CUSTOM_TARGET(
    ${_target}-stage-target ALL
    DEPENDS ${RV_STAGE_LIB_DIR}/${_python3_lib_name}
  )
ENDIF()

# Python::Python target is already created by Conan, so we just add it to the deps list
LIST(APPEND RV_DEPS_LIST Python::Python)

# PySide6 staging - copy PySide6 files into Python staging area This maintains the original architecture where PySide6 appears inside Python
IF(RV_VFX_PLATFORM STREQUAL CY2024)
  # Get PySide6 package location from CMake target (set by Conan)
  GET_TARGET_PROPERTY(_pyside6_root pyside6::pyside6 INTERFACE_INCLUDE_DIRECTORIES)
  IF(_pyside6_root)
    # PySide6 root should point to the site-packages directory containing PySide6
    LIST(GET _pyside6_root 0 _pyside6_package_root)

    # Determine destination site-packages in staging area
    IF(RV_TARGET_WINDOWS)
      SET(_staged_site_packages
          ${RV_STAGE_LIB_DIR}/Lib/site-packages
      )
    ELSE()
      SET(_staged_site_packages
          ${RV_STAGE_LIB_DIR}/python${RV_DEPS_PYTHON_VERSION_SHORT}/site-packages
      )
    ENDIF()

    # Create PySide6 staging flag
    SET(_pyside6_stage_flag
        ${_install_dir}/pyside6-stage-flag
    )

    ADD_CUSTOM_COMMAND(
      COMMENT "Copying PySide6 into Python staging area"
      OUTPUT ${_pyside6_stage_flag}
      COMMAND ${CMAKE_COMMAND} -E make_directory ${_staged_site_packages}
      COMMAND ${CMAKE_COMMAND} -E copy_directory ${_pyside6_package_root}/PySide6 ${_staged_site_packages}/PySide6
      COMMAND ${CMAKE_COMMAND} -E copy_directory ${_pyside6_package_root}/shiboken6 ${_staged_site_packages}/shiboken6
      COMMAND ${CMAKE_COMMAND} -E touch ${_pyside6_stage_flag}
      DEPENDS ${_target}-stage-target pyside6::pyside6
    )

    ADD_CUSTOM_TARGET(
      ${_target}-pyside6-stage ALL
      DEPENDS ${_pyside6_stage_flag}
    )

    ADD_DEPENDENCIES(dependencies ${_target}-pyside6-stage)
  ENDIF()
ENDIF()

ADD_DEPENDENCIES(dependencies ${_target}-stage-target)

# Set cache variables for compatibility
SET(RV_DEPS_PYTHON3_VERSION
    ${Python_VERSION}
    CACHE INTERNAL "" FORCE
)
SET(RV_DEPS_PYSIDE_VERSION
    "6.5.3"
    CACHE INTERNAL "" FORCE
)

SET(RV_DEPS_PYTHON3_EXECUTABLE
    ${_python3_executable}
    CACHE INTERNAL "" FORCE
)
