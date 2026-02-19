#
# Copyright (C) 2022  Autodesk, Inc. All Rights Reserved.
#
# SPDX-License-Identifier: Apache-2.0
#

# IMPORTANT: CMake minimum version need to be increased everytime Boost version is increased. e.g. CMake 3.27 is needed for Boost 1.82 to be found by
# FindBoost.cmake.
#
# Starting from CMake 3.30, FindBoost.cmake has been removed in favor of BoostConfig.cmake (Boost 1.70+). This behavior is covered by CMake policy CMP0167.

SET(_target
    "RV_DEPS_BOOST"
)

IF(RV_USE_PACKAGE_MANAGER)
  #
  # ====== PACKAGE MANAGER MODE (Conan via find_package) ======
  #
  MESSAGE(STATUS "Finding ${_target} from Conan via find_package()")

  SET(_find_target
      Boost
  )

  # Library components (define before find_package to make targets GLOBAL)
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

  # Use version from CYCOMMON.cmake
  FIND_PACKAGE(${_find_target} ${RV_DEPS_BOOST_VERSION} CONFIG REQUIRED)

  # Make Boost targets GLOBAL so they can be used in subdirectories
  SET(_boost_targets
      ""
  )
  FOREACH(
    _boost_component
    ${_boost_libs}
  )
    LIST(APPEND _boost_targets Boost::${_boost_component})
  ENDFOREACH()
  LIST(APPEND _boost_targets Boost::headers)
  RV_MAKE_TARGETS_GLOBAL(${_boost_targets})

  # Print package info for debugging
  RV_PRINT_PACKAGE_INFO("${_find_target}")

  # Note: Boost has a custom lib naming scheme on windows However, Conan builds Boost with simple names (boost_filesystem.dll, not
  # boost_filesystem-vc143-mt-x64-1_82.dll)
  IF(RV_TARGET_WINDOWS)
    SET(BOOST_SHARED_LIBRARY_PREFIX
        ""
    )
    # Conan uses simple naming without version suffix
    SET(BOOST_SHARED_LIBRARY_SUFFIX
        ${CMAKE_SHARED_LIBRARY_SUFFIX}
    )
    SET(BOOST_IMPORT_LIBRARY_PREFIX
        ""
    )
    SET(BOOST_IMPORT_LIBRARY_SUFFIX
        ${CMAKE_IMPORT_LIBRARY_SUFFIX}
    )
  ELSE()
    SET(BOOST_SHARED_LIBRARY_PREFIX
        ${CMAKE_SHARED_LIBRARY_PREFIX}
    )
    SET(BOOST_SHARED_LIBRARY_SUFFIX
        ${CMAKE_SHARED_LIBRARY_SUFFIX}
    )
  ENDIF()

  # Set up staging directories from Conan package location
  RV_SETUP_PACKAGE_STAGING(${_target} ${_find_target})

  # Build staging output list
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
    IF(RV_TARGET_WINDOWS)
      # On Windows, DLLs go to bin directory
      LIST(APPEND _boost_stage_output ${RV_STAGE_BIN_DIR}/${_boost_${_boost_lib}_lib_name})
    ELSE()
      LIST(APPEND _boost_stage_output ${RV_STAGE_LIB_DIR}/${_boost_${_boost_lib}_lib_name})
    ENDIF()
  ENDFOREACH()

  # Copy libraries to staging area
  IF(RV_TARGET_WINDOWS)
    ADD_CUSTOM_COMMAND(
      COMMENT "Installing ${_target}'s libs and bin into ${RV_STAGE_LIB_DIR} and ${RV_STAGE_BIN_DIR}"
      OUTPUT ${_boost_stage_output}
      COMMAND ${CMAKE_COMMAND} -E copy_directory ${_lib_dir} ${RV_STAGE_LIB_DIR}
      COMMAND ${CMAKE_COMMAND} -E copy_directory ${_bin_dir} ${RV_STAGE_BIN_DIR}
      DEPENDS ${_target}
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

  # Include the original boost build logic
  INCLUDE(${CMAKE_CURRENT_LIST_DIR}/build/boost.cmake)

ENDIF()
