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
  MESSAGE(DEBUG "  _target       ='${_target}'")
  MESSAGE(DEBUG "  _version      ='${_version}'")
  MESSAGE(DEBUG "  _base_dir     ='${_base_dir}'")
  MESSAGE(DEBUG "  _build_dir    ='${_build_dir}'")
  MESSAGE(DEBUG "  _source_dir   ='${_source_dir}'")
  MESSAGE(DEBUG "  _install_dir  ='${_install_dir}'")
  MESSAGE(DEBUG "  _include_dir  ='${_include_dir}'")
  MESSAGE(DEBUG "  _bin_dir      ='${_bin_dir}'")
  MESSAGE(DEBUG "  _lib_dir      ='${_lib_dir}'")
  MESSAGE(DEBUG "  _make_command      ='${_make_command}'")
  MESSAGE(DEBUG "  _configure_command ='${_configure_command}'")
  MESSAGE(DEBUG "  ${_target}_VERSION='${${_target}_VERSION}'")
  MESSAGE(DEBUG "  ${_target}_ROOT_DIR='${${_target}_ROOT_DIR}'")
ENDMACRO()

# Get all propreties that cmake supports
IF(NOT CMAKE_PROPERTY_LIST)
  EXECUTE_PROCESS(
    COMMAND cmake --help-property-list
    OUTPUT_VARIABLE CMAKE_PROPERTY_LIST
  )

  # Convert command output into a CMake list
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

MACRO(CONAN_PRINT_TARGET_VARIABLES target)
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

  STRING(REPLACE ";" " " openssl_COMPONENT_NAMES_SPLIT "${${_target_lowercase}_COMPONENT_NAMES}")
  MESSAGE(STATUS "    ${target} component names: ${openssl_COMPONENT_NAMES_SPLIT}")
  MESSAGE(STATUS "    ${target} components: ${${_target_lowercase}_COMPONENT_NAMES_SPLIT}")

  # Print the target properties
  FOREACH(
    component
    ${${_target_lowercase}_COMPONENT_NAMES}
  )
    PRINT_TARGET_PROPERTIES(${component})
  ENDFOREACH()
ENDMACRO()

MACRO(CONAN_SETUP_STAGING RV_DEPS_TARGET FIND_TARGET)
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
      MESSAGE("Found root directory for ${FIND_TARGET}: ${_install_dir}")
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
ENDMACRO()

MACRO(CONAN_SETUP_WINDOWS_IMPLIB implibname)
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
