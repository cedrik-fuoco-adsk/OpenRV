#
# Copyright (C) 2022  Autodesk, Inc. All Rights Reserved.
#
# SPDX-License-Identifier: Apache-2.0
#

SET(_target
    "RV_DEPS_PYTHON3"
)

SET(_python3_target
    "RV_DEPS_PYTHON3"
)

IF(RV_USE_PACKAGE_MANAGER)
  #
  # ====== PACKAGE MANAGER MODE (Conan via find_package) ======
  #
  MESSAGE(STATUS "Finding Python from Conan via find_package()")

  SET(_find_target
      Python
  )

  # Parse version from CYCOMMON
  SET(_python3_version
      "${RV_DEPS_PYTHON_VERSION}"
  )
  STRING(REPLACE "." ";" _python_version_list "${_python3_version}")
  LIST(GET _python_version_list 0 PYTHON_VERSION_MAJOR)
  LIST(GET _python_version_list 1 PYTHON_VERSION_MINOR)
  LIST(GET _python_version_list 2 PYTHON_VERSION_PATCH)

  SET(RV_DEPS_PYTHON_VERSION_SHORT
      "${PYTHON_VERSION_MAJOR}.${PYTHON_VERSION_MINOR}"
  )

  # This version is used for generating src/build/requirements.txt from requirements.txt.in template
  SET(_opentimelineio_version
      "${RV_DEPS_OTIO_VERSION}"
  )

  SET(_pyside_version
      "${RV_DEPS_PYSIDE_VERSION}"
  )

  SET(_numpy_version
      "${RV_DEPS_NUMPY_VERSION}"
  )

  # Look for the specific version we need
  FIND_PACKAGE(
    ${_find_target} ${RV_DEPS_PYTHON_VERSION_SHORT} EXACT REQUIRED
    COMPONENTS Interpreter Development.Module Development.Embed
  )

  # Make Python targets GLOBAL
  RV_MAKE_TARGETS_GLOBAL(Python::Python)

  FIND_PACKAGE(pyside6 CONFIG REQUIRED)

  # Make PySide6 targets GLOBAL
  RV_MAKE_TARGETS_GLOBAL(pyside6::pyside6 pyside6::shiboken6)

  # Verify we found the right version
  IF(NOT Python_VERSION VERSION_EQUAL "${_python3_version}")
    MESSAGE(WARNING "Found Python ${Python_VERSION}, but expected ${_python3_version}")
  ENDIF()

  # Print package info for debugging
  RV_PRINT_PACKAGE_INFO("${_find_target}")
  RV_PRINT_PACKAGE_INFO("pyside6")

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

  # Set up staging target
  RV_SETUP_PACKAGE_STAGING(${_target} ${_find_target})

  # Generate requirements.txt from template
  SET(_requirements_input_file
      "${PROJECT_SOURCE_DIR}/src/build/requirements.txt.in"
  )
  SET(_requirements_output_file
      "${CMAKE_BINARY_DIR}/requirements.txt"
  )

  CONFIGURE_FILE(${_requirements_input_file} ${_requirements_output_file} @ONLY)

  # Set environment for pip install
  IF(CMAKE_BUILD_TYPE MATCHES "^Debug$")
    SET(_otio_debug_env
        "OTIO_CXX_DEBUG_BUILD=1"
    )
  ELSE()
    SET(_otio_debug_env
        ""
    )
  ENDIF()

  # Build dependencies that must be installed FIRST
  SET(RV_PYTHON_BUILD_DEPS
      "pip" "setuptools" "wheel" "Cython" "meson-python" "ninja"
      CACHE STRING "Build dependencies to install first (from wheels)"
  )

  # List of packages safe to install from pre-built wheels
  SET(RV_PYTHON_WHEEL_SAFE
      ${RV_PYTHON_BUILD_DEPS} "PyOpenGL" "certifi" "six" "packaging" "requests"
      CACHE STRING "Packages safe to install from wheels (pure Python or build tools)"
  )

  STRING(REPLACE ";" "," _wheel_safe_packages "${RV_PYTHON_WHEEL_SAFE}")

  # On Mac, ensure we build the python packages with the SDK
  IF(RV_TARGET_DARWIN
     AND CMAKE_OSX_SYSROOT
  )
    MESSAGE(STATUS "Using macOS SDK for Python packages: ${CMAKE_OSX_SYSROOT}")
    SET(_sdkroot_env
        "SDKROOT=${CMAKE_OSX_SYSROOT}"
    )
  ENDIF()

  # Phase 1: Install build dependencies
  SET(_build_deps_install_command
      ${CMAKE_COMMAND} -E env ${_sdkroot_env} "${_python3_executable}" -s -E -I -m pip install --upgrade --no-cache-dir ${RV_PYTHON_BUILD_DEPS}
  )

  # Phase 2: Install main requirements
  SET(_requirements_install_command
      ${CMAKE_COMMAND} -E env ${_otio_debug_env} ${_sdkroot_env}
  )

  # Set OpenSSL environment variables for pip install (needed for cryptography/Rust openssl-sys)
  IF(DEFINED RV_DEPS_OPENSSL_INSTALL_DIR)
    LIST(APPEND _requirements_install_command "OPENSSL_DIR=${RV_DEPS_OPENSSL_INSTALL_DIR}")
    # Windows needs additional variables for Rust's openssl-sys crate
    IF(RV_TARGET_WINDOWS)
      LIST(APPEND _requirements_install_command "OPENSSL_LIB_DIR=${RV_DEPS_OPENSSL_INSTALL_DIR}/lib")
      LIST(APPEND _requirements_install_command "OPENSSL_INCLUDE_DIR=${RV_DEPS_OPENSSL_INSTALL_DIR}/include")
      # Force dynamic linking with shared OpenSSL
      LIST(APPEND _requirements_install_command "OPENSSL_STATIC=0")
    ENDIF()
  ENDIF()

  # On Windows, pass compiler paths so MSVC is found in pip's isolated build environment. The MSVC environment from vcvarsall may not propagate through the
  # MSYS2 → CMake → pip → CMake chain. This mirrors the approach used in the PySide6 Conan recipe (conan/recipes/pyside6/all/conanfile.py).
  IF(RV_TARGET_WINDOWS)
    LIST(APPEND _requirements_install_command "CC=${CMAKE_C_COMPILER}")
    LIST(APPEND _requirements_install_command "CXX=${CMAKE_CXX_COMPILER}")

    # Override TMP/TEMP to a short path. MSYS2's temp dir is deeply nested inside Conan's cache (e.g. .conan2/p/b/msys2.../p/bin/msys64/tmp/) and pip builds
    # create further subdirectories, easily exceeding Windows' 260-char MAX_PATH and causing cl.exe to fail with "Cannot open compiler generated file".
    SET(_pip_tmp_dir
        "${CMAKE_BINARY_DIR}/pip_tmp"
    )
    FILE(MAKE_DIRECTORY "${_pip_tmp_dir}")
    LIST(APPEND _requirements_install_command "TMP=${_pip_tmp_dir}")
    LIST(APPEND _requirements_install_command "TEMP=${_pip_tmp_dir}")
  ENDIF()

  # Python_LIBRARY is already set above (lines ~153-162) with the actual file path. Conan creates Python::Python as an INTERFACE IMPORTED target, so
  # IMPORTED_IMPLIB and IMPORTED_LOCATION are not available via GET_TARGET_PROPERTY.
  SET(_python3_cmake_library
      "${Python_LIBRARY}"
  )

  SET(_cmake_args_value
      "-DPYTHON_LIBRARY=${_python3_cmake_library} -DPYTHON_INCLUDE_DIR=${_include_dir} -DPYTHON_EXECUTABLE=${_python3_executable}"
  )

  # On Windows, forward MSVC compiler paths to pip's isolated build environment. Without this, packages built from source via pip (e.g. OpenTimelineIO) cannot
  # find cl.exe because the vcvarsall environment doesn't propagate through the Conan -> CMake -> pip -> CMake chain.
  #
  # We use a CMake initial-cache script (-C <file>) instead of inline -DCMAKE_C_COMPILER=<path> because MSVC paths typically contain spaces (e.g. "C:/Program
  # Files/Microsoft Visual Studio/...") which break the space-delimited CMAKE_ARGS parsing.
  IF(RV_TARGET_WINDOWS)
    SET(_pip_compiler_cache
        "${CMAKE_BINARY_DIR}/_pip_compiler_init.cmake"
    )
    FILE(
      WRITE "${_pip_compiler_cache}"
      "set(CMAKE_C_COMPILER \"${CMAKE_C_COMPILER}\" CACHE FILEPATH \"\")\n" "set(CMAKE_CXX_COMPILER \"${CMAKE_CXX_COMPILER}\" CACHE FILEPATH \"\")\n"
    )
    STRING(APPEND _cmake_args_value " -C ${_pip_compiler_cache}")
  ENDIF()

  LIST(
    APPEND
    _requirements_install_command
    "CMAKE_ARGS=${_cmake_args_value}"
    "${_python3_executable}"
    -s
    -E
    -I
    -m
    pip
    install
    --upgrade
    --no-cache-dir
    --force-reinstall
    --no-binary
    :all:
    --only-binary
    ${_wheel_safe_packages}
    -r
    "${_requirements_output_file}"
  )

  # Phase 1 flag: Build dependencies
  SET(${_target}-build-deps-flag
      ${_install_dir}/${_target}-build-deps-flag
  )

  ADD_CUSTOM_COMMAND(
    COMMENT "Installing Python build dependencies (pip, setuptools, wheel, Cython, etc.)"
    OUTPUT ${${_target}-build-deps-flag}
    COMMAND ${_build_deps_install_command}
    COMMAND cmake -E touch ${${_target}-build-deps-flag}
    DEPENDS ${_target}
  )

  # Phase 2 flag: Main requirements
  SET(${_target}-requirements-flag
      ${_install_dir}/${_target}-requirements-flag
  )

  ADD_CUSTOM_COMMAND(
    COMMENT "Installing requirements from ${_requirements_output_file}"
    OUTPUT ${${_target}-requirements-flag}
    COMMAND ${_requirements_install_command}
    COMMAND cmake -E touch ${${_target}-requirements-flag}
    DEPENDS ${_target} ${${_target}-build-deps-flag} ${_requirements_output_file} ${_requirements_input_file}
  )

  # Test the Python distribution
  SET(${_target}-test-flag
      ${_install_dir}/${_target}-test-flag
  )

  SET(_test_python_script
      "${PROJECT_SOURCE_DIR}/src/build/test_python.py"
  )

  ADD_CUSTOM_COMMAND(
    COMMENT "Testing Python distribution"
    OUTPUT ${${_target}-test-flag}
    COMMAND python3 "${_test_python_script}" --python-home "${_Python_ROOT_}" --variant "${CMAKE_BUILD_TYPE}"
    COMMAND cmake -E touch ${${_target}-test-flag}
    DEPENDS ${${_target}-requirements-flag} ${_test_python_script}
  )

  # Staging - copy Python files to app bundle
  IF(RV_TARGET_WINDOWS)
    ADD_CUSTOM_COMMAND(
      COMMENT "Installing ${_target}'s include and libs into staging area"
      OUTPUT ${RV_STAGE_BIN_DIR}/${_python3_lib_name}
      COMMAND ${CMAKE_COMMAND} -E copy_directory ${_include_dir} ${RV_STAGE_INCLUDE_DIR}
      COMMAND ${CMAKE_COMMAND} -E copy_directory ${Python_BIN_DIR} ${RV_STAGE_BIN_DIR}
      COMMAND ${CMAKE_COMMAND} -E copy_directory ${Python_LIB_DIR} ${RV_STAGE_LIB_DIR}
      DEPENDS ${${_target}-test-flag}
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
      DEPENDS ${${_target}-test-flag}
    )
    ADD_CUSTOM_TARGET(
      ${_target}-stage-target ALL
      DEPENDS ${RV_STAGE_LIB_DIR}/${_python3_lib_name}
    )
  ENDIF()

  ADD_DEPENDENCIES(dependencies ${_target}-stage-target)

  # Set cache variables for compatibility
  SET(RV_DEPS_PYTHON3_VERSION
      ${_python3_version}
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

  LIST(APPEND RV_DEPS_LIST Python::Python)

ELSE()
  #
  # ====== TRADITIONAL MODE (Build from source) ======
  #
  MESSAGE(STATUS "Building Python from source (traditional mode)")

  INCLUDE(python3)

ENDIF()
