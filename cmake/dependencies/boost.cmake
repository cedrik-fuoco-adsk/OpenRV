#
# Copyright (C) 2025  Autodesk, Inc. All Rights Reserved.
#
# SPDX-License-Identifier: Apache-2.0
#

SET(_target
    "RV_DEPS_BOOST"
)

SET(_find_target
    Boost
)

FIND_PACKAGE(${_find_target} 1.82 CONFIG REQUIRED)

# Prints the variables.
CONAN_PRINT_TARGET_VARIABLES("${_find_target}")

# Library naming conventions

SET(_boost_libs
    atomic
    chrono
    date_time
    filesystem
    graph
    iostreams
    locale
    program_options
    random
    regex
    serialization
    system
    thread
    timer
)

# Note: Boost has a custom lib naming scheme on windows
IF(RV_TARGET_WINDOWS)
  SET(BOOST_SHARED_LIBRARY_PREFIX
      ""
  )
  IF(CMAKE_BUILD_TYPE MATCHES "^Debug$")
    SET(BOOST_LIBRARY_SUFFIX
        "-vc143-mt-gd-x64-${_major_minor_version}"
    )
  ELSE()
    SET(BOOST_LIBRARY_SUFFIX
        "-vc143-mt-x64-${_major_minor_version}"
    )
  ENDIF()
  SET(BOOST_SHARED_LIBRARY_SUFFIX
      ${BOOST_LIBRARY_SUFFIX}${CMAKE_SHARED_LIBRARY_SUFFIX}
  )
  SET(BOOST_IMPORT_LIBRARY_PREFIX
      ""
  )
  SET(BOOST_IMPORT_LIBRARY_SUFFIX
      ${BOOST_LIBRARY_SUFFIX}${CMAKE_IMPORT_LIBRARY_SUFFIX}
  )
ELSE()
  SET(BOOST_SHARED_LIBRARY_PREFIX
      ${CMAKE_SHARED_LIBRARY_PREFIX}
  )
  SET(BOOST_SHARED_LIBRARY_SUFFIX
      ${CMAKE_SHARED_LIBRARY_SUFFIX}
  )
ENDIF()

CONAN_SETUP_STAGING(${_target} ${_find_target})

# custom command to copy the library to the staging area

FOREACH(
  _boost_lib
  ${_boost_libs}
)
  SET(_boost_${_boost_lib}_lib_name
      ${BOOST_SHARED_LIBRARY_PREFIX}boost_${_boost_lib}${BOOST_SHARED_LIBRARY_SUFFIX}
  )
  SET(_boost_${_boost_lib}_lib
      ${_lib_dir}/${_boost_${_boost_lib}_lib_name}
  )

  IF(RV_TARGET_WINDOWS)
    SET(_boost_${_boost_lib}_implib
        ${_lib_dir}/${BOOST_IMPORT_LIBRARY_PREFIX}boost_${_boost_lib}${BOOST_IMPORT_LIBRARY_SUFFIX}
    )
  ENDIF()

  LIST(APPEND RV_DEPS_LIST Boost::${_boost_lib})
  LIST(APPEND _boost_stage_output ${RV_STAGE_LIB_DIR}/${_boost_${_boost_lib}_lib_name})
ENDFOREACH()

IF(RV_TARGET_WINDOWS)
  ADD_CUSTOM_COMMAND(
    TARGET ${_target}
    POST_BUILD
    COMMENT "Installing ${_target}'s libs and bin into ${RV_STAGE_LIB_DIR} and ${RV_STAGE_BIN_DIR}"
    COMMAND ${CMAKE_COMMAND} -E copy_directory ${_lib_dir} ${RV_STAGE_LIB_DIR}
    COMMAND ${CMAKE_COMMAND} -E copy_directory ${_lib_dir} ${RV_STAGE_BIN_DIR}
  )
ELSE()
  ADD_CUSTOM_COMMAND(
    COMMENT "Installing ${_target}'s libs into ${RV_STAGE_LIB_DIR}"
    OUTPUT ${_boost_stage_output}
    COMMAND ${CMAKE_COMMAND} -E copy_directory ${_lib_dir} ${RV_STAGE_LIB_DIR}
    DEPENDS ${_target}
  )
ENDIF()

ADD_CUSTOM_TARGET(
  ${_target}-stage-target ALL
  DEPENDS ${_boost_stage_output}
)

ADD_DEPENDENCIES(dependencies ${_target}-stage-target)

STRING(TOUPPER ${_find_target} _find_target_uppercase)
SET(RV_DEPS_${_find_target_uppercase}_VERSION
    ${${_find_target}_VERSION}
    CACHE INTERNAL "" FORCE
)
