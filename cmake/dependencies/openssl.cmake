#
# Copyright (C) 2025  Autodesk, Inc. All Rights Reserved.
#
# SPDX-License-Identifier: Apache-2.0
#

SET(_target
    "RV_DEPS_OPENSSL"
)

SET(_find_target
    OpenSSL
)

FIND_PACKAGE(${_find_target} 3.5.0 CONFIG REQUIRED)

# Prints the variables.
CONAN_PRINT_TARGET_VARIABLES("${_find_target}")

LIST(APPEND RV_DEPS_LIST OpenSSL::SSL)

IF(RV_TARGET_LINUX)
  SET(_crypto_lib_name
      ${CMAKE_SHARED_LIBRARY_PREFIX}crypto${CMAKE_SHARED_LIBRARY_SUFFIX}${_dot_version}
  )

  SET(_ssl_lib_name
      ${CMAKE_SHARED_LIBRARY_PREFIX}ssl${CMAKE_SHARED_LIBRARY_SUFFIX}${_dot_version}
  )
ELSEIF(RV_TARGET_WINDOWS)
  # As stated in the openssl documentation, the names are libcrypto-1_1-x64 and libssl-1_1-x64 when OpenSSL is build with MSVC.
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

IF(RV_TARGET_LINUX)
  SET(_openssl_stage_lib_dir
      ${RV_STAGE_LIB_DIR}/OpenSSL
  )
ELSE()
  SET(_openssl_stage_lib_dir
      ${RV_STAGE_LIB_DIR}
  )
ENDIF()

CONAN_SETUP_STAGING(${_target} ${_find_target})

ADD_CUSTOM_COMMAND(
  COMMENT "Installing ${_target}'s libs into ${_openssl_stage_lib_dir}"
  OUTPUT ${_openssl_stage_lib_dir}/${_crypto_lib_name} ${_openssl_stage_lib_dir}/${_ssl_lib_name}
  COMMAND ${CMAKE_COMMAND} -E copy_directory ${_lib_dir} ${_openssl_stage_lib_dir}
  DEPENDS OpenSSL::SSL OpenSSL::Crypto
)
ADD_CUSTOM_TARGET(
  ${_target}-stage-target ALL
  DEPENDS ${_openssl_stage_lib_dir}/${_crypto_lib_name} ${_openssl_stage_lib_dir}/${_ssl_lib_name}
)

ADD_DEPENDENCIES(dependencies ${_target}-stage-target)

STRING(TOUPPER ${_find_target} _find_target_uppercase)
SET(RV_DEPS_${_find_target_uppercase}_VERSION
    ${${_find_target}_VERSION}
    CACHE INTERNAL "" FORCE
)
