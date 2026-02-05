#
# Copyright (C) 2023  Autodesk, Inc. All Rights Reserved.
#
# SPDX-License-Identifier: Apache-2.0
#

#
# Create the standard variables common to most RV_DEPS_xyz modules
MACRO(RV_CREATE_STANDARD_DEPS_VARIABLES target_name version make_command configure_command)

  SET(_target
      ${target_name}
  )
  SET(_base_dir
      ${RV_DEPS_BASE_DIR}/${target_name}
  )
  SET(_install_dir
      ${_base_dir}/install
  )
  # Create commonly used definition when cross-building dependencies RV_DEPS_<target-name>_ROOT_DIR variable
  SET(${target_name}_ROOT_DIR
      ${_install_dir}
  )
  SET(_include_dir
      ${_install_dir}/include
  )
  SET(_bin_dir
      ${_install_dir}/bin
  )
  SET(_build_dir
      ${_base_dir}/build
  )
  SET(_source_dir
      ${_base_dir}/src
  )
  IF(RHEL_VERBOSE)
    SET(_lib_dir
        ${_install_dir}/lib64
    )
  ELSE()
    SET(_lib_dir
        ${_install_dir}/lib
    )
  ENDIF()

  #
  # Create locally used _version and globally used RV_DEPS_XYZ_VERSION variables.
  #
  SET(_version
      ${version}
  )

  # Attempt to match Major.Minor.Patch CMAKE_MATCH_1 will be Major, CMAKE_MATCH_2 Minor, etc.
  STRING(REGEX MATCH "^([0-9]+)\\.?([0-9]*)\\.?([0-9]*)" _dummy "${_version}")
  # If the group was found, use it; otherwise default to 0
  IF(CMAKE_MATCH_1)
    SET(_version_major
        ${CMAKE_MATCH_1}
    )
  ELSE()
    SET(_version_major
        0
    )
  ENDIF()

  IF(CMAKE_MATCH_2)
    SET(_version_minor
        ${CMAKE_MATCH_2}
    )
  ELSE()
    SET(_version_minor
        0
    )
  ENDIF()

  IF(CMAKE_MATCH_3)
    SET(_version_patch
        ${CMAKE_MATCH_3}
    )
  ELSE()
    SET(_version_patch
        0
    )
  ENDIF()
  SET(${target_name}_VERSION
      ${_version}
      CACHE INTERNAL "" FORCE
  )

  #
  # Create locally used make command
  #
  SET(_make_command
      ${make_command}
  )

  SET(_cmake_build_command
      ${CMAKE_COMMAND} --build ${_build_dir} --config ${CMAKE_BUILD_TYPE} -j${_cpu_count}
  )

  IF(RV_TARGET_WINDOWS)
    # MSYS2/CMake defaults to Ninja
    SET(_make_command
        ninja
    )
  ENDIF()

  #
  # Create locally used configure command
  #
  SET(_configure_command
      ${configure_command}
  )

  #
  # Also reset a number of secondary list variables
  #
  SET(_byproducts
      ""
  )
  SET(_configure_options
      ""
  )
  LIST(APPEND _configure_options "-DCMAKE_INSTALL_PREFIX=${_install_dir}")
  LIST(APPEND _configure_options "-DCMAKE_OSX_ARCHITECTURES=${CMAKE_OSX_ARCHITECTURES}")
  LIST(APPEND _configure_options "-DCMAKE_BUILD_TYPE=${CMAKE_BUILD_TYPE}")
  LIST(APPEND _configure_options "-S ${_source_dir}")
  LIST(APPEND _configure_options "-B ${_build_dir}")

  SET(_cmake_install_command
      ${CMAKE_COMMAND} --install ${_build_dir} --prefix ${_install_dir} --config ${CMAKE_BUILD_TYPE}
  )

  #
  # Finally add a clean-<target-name> target
  #
  ADD_CUSTOM_TARGET(
    clean-${target_name}
    COMMENT "Cleaning '${target_name}' ..."
    COMMAND ${CMAKE_COMMAND} -E remove_directory ${_base_dir}
    COMMAND ${CMAKE_COMMAND} -E remove_directory ${RV_DEPS_BASE_DIR}/cmake/dependencies/${_target}-prefix
  )
ENDMACRO()

MACRO(RV_SHOW_STANDARD_DEPS_VARIABLES)
  MESSAGE(DEBUG "RV_CREATE_STANDARD_DEPS_VARIABLES:")
  MESSAGE(DEBUG "  _target        ='${_target}'")
  MESSAGE(DEBUG "  _version       ='${_version}'")
  MESSAGE(DEBUG "  _version_major ='${_version_major}'")
  MESSAGE(DEBUG "  _version_minor ='${_version_minor}'")
  MESSAGE(DEBUG "  _version_patch ='${_version_patch}'")
  MESSAGE(DEBUG "  _base_dir      ='${_base_dir}'")
  MESSAGE(DEBUG "  _build_dir     ='${_build_dir}'")
  MESSAGE(DEBUG "  _source_dir    ='${_source_dir}'")
  MESSAGE(DEBUG "  _install_dir   ='${_install_dir}'")
  MESSAGE(DEBUG "  _include_dir   ='${_include_dir}'")
  MESSAGE(DEBUG "  _bin_dir       ='${_bin_dir}'")
  MESSAGE(DEBUG "  _lib_dir       ='${_lib_dir}'")
  MESSAGE(DEBUG "  _make_command      ='${_make_command}'")
  MESSAGE(DEBUG "  _configure_command ='${_configure_command}'")
  MESSAGE(DEBUG "  ${_target}_VERSION='${${_target}_VERSION}'")
  MESSAGE(DEBUG "  ${_target}_ROOT_DIR='${${_target}_ROOT_DIR}'")
ENDMACRO()

#
# ============================================================================
# Package Manager Helper Macros (for use with RV_USE_PACKAGE_MANAGER=ON)
# ============================================================================
#

# Get all properties that cmake supports (for debugging)
IF(NOT CMAKE_PROPERTY_LIST)
  EXECUTE_PROCESS(
    COMMAND cmake --help-property-list
    OUTPUT_VARIABLE CMAKE_PROPERTY_LIST
  )
  STRING(
    REGEX
    REPLACE ";" "\\\\;" CMAKE_PROPERTY_LIST "${CMAKE_PROPERTY_LIST}"
  )
  STRING(
    REGEX
    REPLACE "\n" ";" CMAKE_PROPERTY_LIST "${CMAKE_PROPERTY_LIST}"
  )
  LIST(REMOVE_DUPLICATES CMAKE_PROPERTY_LIST)
ENDIF()

FUNCTION(print_properties)
  MESSAGE(STATUS "CMAKE_PROPERTY_LIST = ${CMAKE_PROPERTY_LIST}")
ENDFUNCTION()

FUNCTION(print_target_properties target)
  IF(NOT TARGET ${target})
    MESSAGE(STATUS "There is no target named '${target}'")
    RETURN()
  ENDIF()

  FOREACH(
    property
    ${CMAKE_PROPERTY_LIST}
  )
    STRING(REPLACE "<CONFIG>" "${CMAKE_BUILD_TYPE}" property ${property})

    # Fix https://stackoverflow.com/questions/32197663/how-can-i-remove-the-the-location-property-may-not-be-read-from-target-error-i
    IF(property STREQUAL "LOCATION"
       OR property MATCHES "^LOCATION_"
       OR property MATCHES "_LOCATION$"
    )
      CONTINUE()
    ENDIF()

    GET_PROPERTY(
      was_set
      TARGET ${target}
      PROPERTY ${property}
      SET
    )
    IF(was_set)
      GET_TARGET_PROPERTY(value ${target} ${property})
      MESSAGE(STATUS "        ${target} ${property} = ${value}")
    ENDIF()
  ENDFOREACH()
ENDFUNCTION()

#
# RV_PRINT_PACKAGE_INFO - Print diagnostic info about a found package
#
# Usage: RV_PRINT_PACKAGE_INFO("PackageName")
#
MACRO(RV_PRINT_PACKAGE_INFO target)
  MESSAGE(STATUS "${target} info:")
  MESSAGE(STATUS "    ${target} version:      ${${target}_VERSION_STRING}")
  MESSAGE(STATUS "    ${target} include_dirs: ${${target}_INCLUDE_DIRS}")
  # Loop through the libraries and print each file name
  FOREACH(
    lib
    ${${target}_INCLUDE_DIRS}
  )
    FILE(GLOB_RECURSE lib_files "${lib}/../lib*")
    SET(library_names
        ""
    )
    FOREACH(
      file
      ${lib_files}
    )
      GET_FILENAME_COMPONENT(file_name ${file} NAME)
      LIST(APPEND library_names ${file_name})
    ENDFOREACH()
    STRING(JOIN " " library_names_joined ${library_names})
    MESSAGE(STATUS "    ${target} libraries: ${library_names_joined}")
  ENDFOREACH()

  STRING(TOLOWER ${target} _target_lowercase)

  STRING(REPLACE ";" " " _component_names_split "${${_target_lowercase}_COMPONENT_NAMES}")
  MESSAGE(STATUS "    ${target} component names: ${_component_names_split}")

  # Print the target properties
  FOREACH(
    component
    ${${_target_lowercase}_COMPONENT_NAMES}
  )
    PRINT_TARGET_PROPERTIES(${component})
  ENDFOREACH()
ENDMACRO()

#
# RV_MAKE_TARGETS_GLOBAL - Make imported targets GLOBAL so they can be used in subdirectories
#
# This macro takes a list of target names and makes them GLOBAL if they exist. This is necessary for targets imported via find_package() from package managers
# like Conan.
#
# Usage: RV_MAKE_TARGETS_GLOBAL(Target1::lib Target2::component ...)
#
MACRO(RV_MAKE_TARGETS_GLOBAL)
  FOREACH(
    _target
    ${ARGN}
  )
    IF(TARGET ${_target})
      SET_TARGET_PROPERTIES(
        ${_target}
        PROPERTIES IMPORTED_GLOBAL TRUE
      )
    ENDIF()
  ENDFOREACH()
ENDMACRO()

#
# RV_SETUP_PACKAGE_STAGING - Set up staging variables for a package found via find_package()
#
# This macro creates the same variables that RV_CREATE_STANDARD_DEPS_VARIABLES creates, but derived from the package found via find_package() (e.g., from
# Conan).
#
# Usage: RV_SETUP_PACKAGE_STAGING(RV_DEPS_ZLIB ZLIB) Where RV_DEPS_ZLIB is the target name and ZLIB is the find_package target name
#
MACRO(RV_SETUP_PACKAGE_STAGING RV_DEPS_TARGET FIND_TARGET)
  ADD_CUSTOM_TARGET(
    ${RV_DEPS_TARGET}
    COMMENT "${FIND_TARGET} found via find_package"
  )

  # Get the include dir path
  SET(_include_path
      ${${FIND_TARGET}_INCLUDE_DIRS}
  )

  # Keep going up until we find a directory that has both lib and include as siblings
  SET(_current_path
      ${_include_path}
  )
  SET(_found_root
      FALSE
  )
  WHILE(NOT _found_root)
    GET_FILENAME_COMPONENT(_parent_dir "${_current_path}" DIRECTORY)
    IF(EXISTS "${_parent_dir}/lib"
       AND EXISTS "${_parent_dir}/include"
    )
      SET(_found_root
          TRUE
      )
      SET(_install_dir
          ${_parent_dir}
      )
      MESSAGE(STATUS "Found root directory for ${FIND_TARGET}: ${_install_dir}")
    ELSE()
      SET(_current_path
          ${_parent_dir}
      )
      # Safety check to avoid infinite loop - stop at root directory Check for both Unix (/) and Windows (C:\, D:\, etc.) root directories
      GET_FILENAME_COMPONENT(_current_path_name "${_current_path}" NAME)
      IF(_current_path STREQUAL "/"
         OR _current_path_name STREQUAL ""
         OR _current_path MATCHES "^[A-Za-z]:[\\\\/]?$"
      )
        MESSAGE(WARNING "Could not find root directory containing lib and include for ${FIND_TARGET}")
        # Fallback to original behavior
        SET(_install_dir
            ${${FIND_TARGET}_INCLUDE_DIRS}/..
        )
        BREAK()
      ENDIF()
    ENDIF()
  ENDWHILE()

  SET(${RV_DEPS_TARGET}_ROOT_DIR
      ${_install_dir}
  )

  SET(_lib_dir
      "${_install_dir}/lib"
  )
  SET(_bin_dir
      "${_install_dir}/bin"
  )
  SET(_include_dir
      "${_install_dir}/include"
  )
ENDMACRO()

#
# RV_SETUP_WINDOWS_IMPLIB - Set up Windows import library paths
#
# Usage: RV_SETUP_WINDOWS_IMPLIB(libname [libpath])
#
MACRO(RV_SETUP_WINDOWS_IMPLIB implibname)
  IF(RV_TARGET_WINDOWS)
    SET(_implibname
        ${implibname}
    )

    # Check if implibpath is provided.
    IF(ARG2)
      SET(_implibpath
          ${ARG2}
      )
    ELSE()
      SET(_implibpath
          ${_lib_dir}/${_implibname}
      )
    ENDIF()
  ENDIF()
ENDMACRO()
