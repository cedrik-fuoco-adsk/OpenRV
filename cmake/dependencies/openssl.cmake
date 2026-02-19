#
# Copyright (C) 2022  Autodesk, Inc. All Rights Reserved.
#
# SPDX-License-Identifier: Apache-2.0
#

SET(_target
    "RV_DEPS_OPENSSL"
)

IF(RV_USE_PACKAGE_MANAGER)
  #
  # ====== PACKAGE MANAGER MODE (Conan via find_package) ======
  #
  MESSAGE(STATUS "Finding ${_target} from Conan via find_package()")

  SET(_find_target
      OpenSSL
  )

  # Use version from CYCOMMON.cmake
  FIND_PACKAGE(${_find_target} ${RV_DEPS_OPENSSL_VERSION} CONFIG REQUIRED)

  # Make OpenSSL targets GLOBAL
  RV_MAKE_TARGETS_GLOBAL(OpenSSL::SSL OpenSSL::Crypto)

  # Print package info for debugging
  RV_PRINT_PACKAGE_INFO("${_find_target}")

  LIST(APPEND RV_DEPS_LIST OpenSSL::SSL)
  LIST(APPEND RV_DEPS_LIST OpenSSL::Crypto)

  # Library naming conventions (use CYCOMMON variables)
  SET(_dot_version
      ${RV_DEPS_OPENSSL_VERSION_DOT}
  )
  SET(_underscore_version
      ${RV_DEPS_OPENSSL_VERSION_UNDERSCORE}
  )

  IF(RV_TARGET_LINUX)
    SET(_crypto_lib_name
        ${CMAKE_SHARED_LIBRARY_PREFIX}crypto${CMAKE_SHARED_LIBRARY_SUFFIX}${_dot_version}
    )
    SET(_ssl_lib_name
        ${CMAKE_SHARED_LIBRARY_PREFIX}ssl${CMAKE_SHARED_LIBRARY_SUFFIX}${_dot_version}
    )
  ELSEIF(RV_TARGET_WINDOWS)
    # OpenSSL 3.x naming: libcrypto-3-x64.dll and libssl-3-x64.dll
    SET(_crypto_lib_name
        libcrypto-${_underscore_version}-x64${CMAKE_SHARED_LIBRARY_SUFFIX}
    )
    SET(_ssl_lib_name
        libssl-${_underscore_version}-x64${CMAKE_SHARED_LIBRARY_SUFFIX}
    )
  ELSE()
    SET(_crypto_lib_name
        ${CMAKE_SHARED_LIBRARY_PREFIX}crypto${_dot_version}${CMAKE_SHARED_LIBRARY_SUFFIX}
    )
    SET(_ssl_lib_name
        ${CMAKE_SHARED_LIBRARY_PREFIX}ssl${_dot_version}${CMAKE_SHARED_LIBRARY_SUFFIX}
    )
  ENDIF()

  # OpenSSL staging directory (Linux uses separate OpenSSL dir)
  IF(RV_TARGET_LINUX)
    SET(_openssl_stage_lib_dir
        ${RV_STAGE_LIB_DIR}/OpenSSL
    )
  ELSE()
    SET(_openssl_stage_lib_dir
        ${RV_STAGE_LIB_DIR}
    )
  ENDIF()

  # Set up staging directories from Conan package location
  RV_SETUP_PACKAGE_STAGING(${_target} ${_find_target})

  # Export OpenSSL install directory for other cmake files (e.g., python.cmake needs this for cryptography/Rust openssl-sys)
  SET(RV_DEPS_OPENSSL_INSTALL_DIR
      ${_install_dir}
      CACHE INTERNAL "OpenSSL installation directory from Conan" FORCE
  )

  # Copy libraries to staging area
  IF(RV_TARGET_WINDOWS)
    ADD_CUSTOM_COMMAND(
      COMMENT "Installing ${_target}'s libs and bin into ${_openssl_stage_lib_dir} and ${RV_STAGE_BIN_DIR}"
      OUTPUT ${RV_STAGE_BIN_DIR}/${_crypto_lib_name} ${RV_STAGE_BIN_DIR}/${_ssl_lib_name}
      COMMAND ${CMAKE_COMMAND} -E copy_directory ${_lib_dir} ${_openssl_stage_lib_dir}
      COMMAND ${CMAKE_COMMAND} -E copy_directory ${_lib_dir} ${RV_STAGE_LIB_DIR}
      COMMAND ${CMAKE_COMMAND} -E copy_directory ${_bin_dir} ${RV_STAGE_BIN_DIR}
      DEPENDS OpenSSL::SSL OpenSSL::Crypto
    )
    ADD_CUSTOM_TARGET(
      ${_target}-stage-target ALL
      DEPENDS ${RV_STAGE_BIN_DIR}/${_crypto_lib_name} ${RV_STAGE_BIN_DIR}/${_ssl_lib_name}
    )
  ELSE()
    ADD_CUSTOM_COMMAND(
      COMMENT "Installing ${_target}'s libs into ${_openssl_stage_lib_dir}"
      OUTPUT ${_openssl_stage_lib_dir}/${_crypto_lib_name} ${_openssl_stage_lib_dir}/${_ssl_lib_name}
      COMMAND ${CMAKE_COMMAND} -E copy_directory ${_lib_dir} ${_openssl_stage_lib_dir}
      COMMAND ${CMAKE_COMMAND} -E copy_directory ${_lib_dir} ${RV_STAGE_LIB_DIR}
      DEPENDS OpenSSL::SSL OpenSSL::Crypto
    )
    ADD_CUSTOM_TARGET(
      ${_target}-stage-target ALL
      DEPENDS ${_openssl_stage_lib_dir}/${_crypto_lib_name} ${_openssl_stage_lib_dir}/${_ssl_lib_name}
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

  # Include the original openssl build logic
  INCLUDE(${CMAKE_CURRENT_LIST_DIR}/build/openssl.cmake)

ENDIF()
