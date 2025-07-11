#
# Copyright (C) 2025  Autodesk, Inc. All Rights Reserved.
#
# SPDX-License-Identifier: Apache-2.0
#

SET(_target
    "RV_DEPS_IMATH"
)

SET(_find_target
    Imath
)

FIND_PACKAGE(${_find_target} 3.1.6 CONFIG REQUIRED)

# Prints the variables.
CONAN_PRINT_TARGET_VARIABLES("${_find_target}")

# LIST(APPEND RV_DEPS_LIST OpenSSL::SSL)

# Library naming conventions

CONAN_SETUP_STAGING(${_target} ${_find_target})

# custom command to copy the library to the staging area

ADD_DEPENDENCIES(dependencies ${_target}-stage-target)

STRING(TOUPPER ${_find_target} _find_target_uppercase)
SET(RV_DEPS_${_find_target_uppercase}_VERSION
    ${${_find_target}_VERSION}
    CACHE INTERNAL "" FORCE
)
