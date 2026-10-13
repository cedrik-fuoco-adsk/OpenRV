#
# Copyright (C) 2026  Autodesk, Inc. All Rights Reserved.
#
# SPDX-License-Identifier: Apache-2.0
#

#
# RV_FIND_DEPENDENCY
#
# Try to find a pre-built package, set ${TARGET}_FOUND
#
# Checks RV_DEPS_PREFER_INSTALLED and per-dep RV_DEPS_<NAME>_FORCE_BUILD. Tries find_package(CONFIG) first, then falls back to pkg-config if PKG_CONFIG_NAME is
# set. If found: sets up directory vars, adds to RV_DEPS_LIST. If not found or finding disabled: sets ${TARGET}_FOUND=FALSE (caller handles fallback).
#
# Imported targets from find_package(CONFIG) are automatically GLOBAL via CMAKE_FIND_PACKAGE_TARGETS_GLOBAL (set in cmake/dependencies/CMakeLists.txt).
# INTERFACE_LIBRARY targets (e.g. from Conan CMakeDeps) are automatically resolved to their underlying real targets via RV_EXTRACT_LINK_TARGETS before appending
# to RV_DEPS_LIST. For pkg-config, the caller is responsible for creating proper imported targets (with LOCATION) after this macro returns.
#
# Must be a MACRO because RV_SET_FOUND_PACKAGE_DIRS / RV_SET_FOUND_PKGCONFIG_DIRS set _lib_dir, _bin_dir, _include_dir in the caller's scope via text
# substitution.
#
# cmake-format: off
# Usage:
#   RV_FIND_DEPENDENCY(
#     TARGET <rv-deps-target>        # REQUIRED: e.g., RV_DEPS_IMATH
#     PACKAGE <find-package-name>    # REQUIRED: e.g., Imath
#     [VERSION <version>]            # Optional version (EXACT or MINIMUM per RV_DEPS_VERSION_MATCH)
#     [PKG_CONFIG_NAME <name>]       # Optional pkg-config module name for fallback
#     [ALLOW_MODULE]                 # Also try find_package(MODULE) for packages with built-in Find modules
#     [COMPONENTS <c1>...]           # Optional find_package COMPONENTS (e.g., Boost components)
#     [DEPS_LIST_TARGETS <t1>...]    # Targets to append to RV_DEPS_LIST
#   )
# cmake-format: on
MACRO(RV_FIND_DEPENDENCY)
  CMAKE_PARSE_ARGUMENTS(_RFD "ALLOW_MODULE" "TARGET;PACKAGE;VERSION;PKG_CONFIG_NAME" "DEPS_LIST_TARGETS;COMPONENTS" ${ARGN})

  SET(${_RFD_TARGET}_FOUND
      FALSE
  )
  SET(_RFD_FOUND_VIA
      ""
  )

  # A dependency this identity has already built and published is consumed from the store instead of built again. That is what the store is for: another build
  # directory, or another machine with the same identity, finds the installed tree.
  #
  # This is checked independently of RV_DEPS_PREFER_INSTALLED, because a store entry is this project's own artifact for this identity rather than a system
  # package that happens to be present. A dependency forced to build from source is not eligible, so it is never taken from the store.
  #
  # The entry is consumed by the ordinary find_package below, pointed at the entry through <Package>_ROOT -- which is searched before CMAKE_PREFIX_PATH and the
  # system -- rather than by pre-seeding ExternalProject state, so the dependency's own files are what describe it. What was found is then checked to be inside
  # the entry before the build is told it came from the store.
  SET(_rfd_store_entry
      ""
  )
  RV_DEPS_IS_STORE_ELIGIBLE(${_RFD_TARGET} _rfd_store_eligible)

  # Sub-builds configured after this point forget what they cached for this package whenever they are reconfigured, in any tree where it has ever been stored;
  # see RV_CREATE_STANDARD_DEPS_VARIABLES. Recorded here, where the package is processed, rather than up front, so that a dependency configured before it --
  # which cannot be consuming it -- never gets the argument, and so never has its configure command change between configures.
  IF(_rfd_store_eligible
     AND NOT "${_RFD_PACKAGE}" IN_LIST RV_DEPS_STORE_PACKAGES
  )
    SET(RV_DEPS_STORE_PACKAGES
        ${RV_DEPS_STORE_PACKAGES} ${_RFD_PACKAGE}
        CACHE INTERNAL "Packages that have been served from or published into a dependency store in this tree"
    )
  ENDIF()
  IF("${_RFD_PACKAGE}" IN_LIST RV_DEPS_STORE_PACKAGES)
    SET_PROPERTY(
      GLOBAL APPEND
      PROPERTY RV_DEPS_STORE_FORGET_IN_SUBBUILDS ${_RFD_PACKAGE}
    )
  ENDIF()

  IF(_rfd_store_eligible)
    RV_DEPS_INSTALL_PATHS(${_RFD_TARGET} _rfd_store_install _rfd_store_staging)
    GET_FILENAME_COMPONENT(_rfd_store_recipe_dir "${_rfd_store_install}" DIRECTORY)
    GET_FILENAME_COMPONENT(_rfd_store_target_dir "${_rfd_store_recipe_dir}" DIRECTORY)

    # Cached paths into another recipe of this dependency -- the entry before a version bump or a patch change -- name a tree this configuration must not use.
    RV_DEPS_FORGET_CACHED_PATHS("${_rfd_store_target_dir}" KEEP "${_rfd_store_recipe_dir}")

    # Only a published entry counts, so a directory left by a configure, or by an interrupted install, is not consumed as if it were a finished dependency.
    RV_DEPS_PUBLISH_COMPLETE(${_RFD_TARGET} _rfd_store_complete)
    IF(_rfd_store_complete)
      SET(_rfd_store_entry
          "${_rfd_store_install}"
      )
      # A find module keeps what it found in the cache and does not search again, so what an earlier configure found elsewhere -- the system's copy, or this
      # dependency built in the build directory -- would win over the entry. Forgotten here, and searched for again with the entry first.
      GET_CMAKE_PROPERTY(_rfd_store_cache CACHE_VARIABLES)
      STRING(TOUPPER "${_RFD_PACKAGE}" _rfd_store_upper)
      FOREACH(
        _rfd_store_name
        ${_rfd_store_cache}
      )
        IF(_rfd_store_name MATCHES "^(${_RFD_PACKAGE}|${_rfd_store_upper})_(DIR|INCLUDE_DIR|INCLUDE_DIRS|LIBRARY|LIBRARY_RELEASE|LIBRARY_DEBUG|LIBRARIES)$"
           OR _rfd_store_name STREQUAL "__pkg_config_checked_${_RFD_TARGET}_PC"
        )
          UNSET(${_rfd_store_name} CACHE)
        ENDIF()
      ENDFOREACH()
      SET(_rfd_store_saved_root_defined
          FALSE
      )
      IF(DEFINED ${_RFD_PACKAGE}_ROOT)
        SET(_rfd_store_saved_root_defined
            TRUE
        )
        SET(_rfd_store_saved_root
            "${${_RFD_PACKAGE}_ROOT}"
        )
      ENDIF()
      SET(${_RFD_PACKAGE}_ROOT
          "${_rfd_store_install}"
      )
    ENDIF()
  ENDIF()

  IF((RV_DEPS_PREFER_INSTALLED
      OR _rfd_store_entry)
     AND NOT ${_RFD_TARGET}_FORCE_BUILD
  )

    # Determine version match mode: per-dep override > global default
    IF(DEFINED ${_RFD_TARGET}_VERSION_MATCH)
      SET(_rfd_match_mode
          "${${_RFD_TARGET}_VERSION_MATCH}"
      )
    ELSE()
      SET(_rfd_match_mode
          "${RV_DEPS_VERSION_MATCH}"
      )
    ENDIF()

    # Build optional COMPONENTS argument list
    SET(_rfd_components_args
        ""
    )
    IF(_RFD_COMPONENTS)
      SET(_rfd_components_args
          COMPONENTS ${_RFD_COMPONENTS}
      )
    ENDIF()

    # Strategy 1: CMake CONFIG mode
    IF(_RFD_VERSION)
      IF(_rfd_match_mode STREQUAL "EXACT")
        FIND_PACKAGE(${_RFD_PACKAGE} ${_RFD_VERSION} EXACT CONFIG ${_rfd_components_args})
      ELSE()
        FIND_PACKAGE(${_RFD_PACKAGE} ${_RFD_VERSION} CONFIG ${_rfd_components_args})
      ENDIF()
    ELSE()
      FIND_PACKAGE(${_RFD_PACKAGE} CONFIG ${_rfd_components_args})
    ENDIF()

    IF(${_RFD_PACKAGE}_FOUND)
      SET(_RFD_FOUND_VIA
          "config"
      )
    ENDIF()

    # Strategy 1.5: CMake MODULE mode (built-in Find modules) Some packages (e.g., zlib) don't ship CMake config files but have built-in Find modules
    # (FindZLIB.cmake) that create proper imported targets.  Opt-in via ALLOW_MODULE to avoid unexpected matches.
    IF(NOT ${_RFD_PACKAGE}_FOUND
       AND _RFD_ALLOW_MODULE
    )
      IF(_RFD_VERSION)
        IF(_rfd_match_mode STREQUAL "EXACT")
          FIND_PACKAGE(${_RFD_PACKAGE} ${_RFD_VERSION} EXACT MODULE ${_rfd_components_args})
        ELSE()
          FIND_PACKAGE(${_RFD_PACKAGE} ${_RFD_VERSION} MODULE ${_rfd_components_args})
        ENDIF()
      ELSE()
        FIND_PACKAGE(${_RFD_PACKAGE} MODULE ${_rfd_components_args})
      ENDIF()

      IF(${_RFD_PACKAGE}_FOUND)
        SET(_RFD_FOUND_VIA
            "module"
        )
      ENDIF()
    ENDIF()

    # Strategy 2: pkg-config fallback
    IF(NOT ${_RFD_PACKAGE}_FOUND
       AND _RFD_PKG_CONFIG_NAME
    )
      FIND_PACKAGE(PkgConfig QUIET)
      IF(PKG_CONFIG_FOUND)
        # pkg_check_modules only searches PKG_CONFIG_PATH by default. Temporarily enable CMAKE_PREFIX_PATH integration so that
        # -DCMAKE_PREFIX_PATH=/opt/homebrew/opt/zlib also exposes <prefix>/lib/pkgconfig/*.pc to pkg-config.  Restored afterwards to avoid side-effects on
        # unrelated pkg_check_modules calls.
        SET(_rfd_saved_pc_prefix_path
            "${PKG_CONFIG_USE_CMAKE_PREFIX_PATH}"
        )
        SET(PKG_CONFIG_USE_CMAKE_PREFIX_PATH
            ON
        )

        IF(_RFD_VERSION)
          IF(_rfd_match_mode STREQUAL "EXACT")
            PKG_CHECK_MODULES(${_RFD_TARGET}_PC QUIET IMPORTED_TARGET "${_RFD_PKG_CONFIG_NAME}=${_RFD_VERSION}")
          ELSE()
            PKG_CHECK_MODULES(${_RFD_TARGET}_PC QUIET IMPORTED_TARGET "${_RFD_PKG_CONFIG_NAME}>=${_RFD_VERSION}")
          ENDIF()
        ELSE()
          PKG_CHECK_MODULES(${_RFD_TARGET}_PC QUIET IMPORTED_TARGET ${_RFD_PKG_CONFIG_NAME})
        ENDIF()

        SET(PKG_CONFIG_USE_CMAKE_PREFIX_PATH
            "${_rfd_saved_pc_prefix_path}"
        )

        IF(${_RFD_TARGET}_PC_FOUND)
          SET(${_RFD_PACKAGE}_FOUND
              TRUE
          )
          SET(${_RFD_PACKAGE}_VERSION
              "${${_RFD_TARGET}_PC_VERSION}"
          )
          SET(_RFD_FOUND_VIA
              "pkgconfig"
          )
        ENDIF()
      ENDIF()
    ENDIF()

    # Common handling for found packages
    IF(${_RFD_PACKAGE}_FOUND)
      SET(${_RFD_TARGET}_FOUND
          TRUE
      )

      IF(_RFD_FOUND_VIA STREQUAL "config")
        MESSAGE(STATUS "Found ${_RFD_PACKAGE} ${${_RFD_PACKAGE}_VERSION} via CMake config. Using installed package.")
        # Build a resolved target list for root validation; apply the same namespaced fallback so that Conan targets (e.g. openjph::openjph for upstream
        # openjph) can be used for IMPORTED_LOCATION resolution.
        SET(_rfd_resolved_targets)
        FOREACH(
          _rfd_t
          ${_RFD_DEPS_LIST_TARGETS}
        )
          IF(TARGET ${_rfd_t})
            LIST(APPEND _rfd_resolved_targets ${_rfd_t})
          ELSEIF(TARGET ${_RFD_PACKAGE}::${_rfd_t})
            LIST(APPEND _rfd_resolved_targets ${_RFD_PACKAGE}::${_rfd_t})
          ENDIF()
        ENDFOREACH()
        RV_SET_FOUND_PACKAGE_DIRS(${_RFD_TARGET} ${_RFD_PACKAGE} DEPS_LIST_TARGETS ${_rfd_resolved_targets})

        # Package config files may suffer the same symlink resolution bug as our walk-up logic (CMake normalizes "../" before resolving symlinks). If the
        # resolved and unresolved include dirs differ, fix ALL imported targets from this package (not just DEPS_LIST_TARGETS). Config files often create
        # auxiliary interface targets (e.g. Imath::ImathConfig, OpenEXR::OpenEXRConfig) that carry include dirs and are linked transitively by the library
        # targets.
        IF(NOT "${_sfpd_unresolved_include_dir}" STREQUAL "${_include_dir}")
          # Record the contaminating prefix so ExternalProject sub-builds can exclude it via CMAKE_IGNORE_PREFIX_PATH. This is how we propagate the symlink fix
          # to sub-builds that run their own CMake and would otherwise rediscover packages at the unresolved (shared) prefix.
          LIST(APPEND RV_DEPS_IGNORE_PREFIXES "${_sfpd_unresolved_root}")
          LIST(REMOVE_DUPLICATES RV_DEPS_IGNORE_PREFIXES)
          SET(RV_DEPS_IGNORE_PREFIXES
              "${RV_DEPS_IGNORE_PREFIXES}"
              CACHE INTERNAL "Contaminating prefixes detected during symlink resolution (for ExternalProject sub-builds)" FORCE
          )
          MESSAGE(STATUS "  Added ${_sfpd_unresolved_root} to RV_DEPS_IGNORE_PREFIXES (symlink resolved to ${_install_dir})")

          GET_PROPERTY(
            _rfd_all_imported_targets
            DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}"
            PROPERTY IMPORTED_TARGETS
          )
          IF(NOT _rfd_all_imported_targets)
            MESSAGE(WARNING "RV_FIND_DEPENDENCY: IMPORTED_TARGETS is empty for ${_RFD_PACKAGE}: symlink include fixup skipped")
          ENDIF()
          FOREACH(
            _rfd_dep
            ${_rfd_all_imported_targets}
          )
            IF("${_rfd_dep}" MATCHES "^${_RFD_PACKAGE}::")
              GET_TARGET_PROPERTY(_rfd_inc_dirs ${_rfd_dep} INTERFACE_INCLUDE_DIRECTORIES)
              IF(_rfd_inc_dirs)
                STRING(REPLACE "${_sfpd_unresolved_include_dir}" "${_include_dir}" _rfd_fixed_inc_dirs "${_rfd_inc_dirs}")
                IF(NOT "${_rfd_fixed_inc_dirs}" STREQUAL "${_rfd_inc_dirs}")
                  SET_TARGET_PROPERTIES(
                    ${_rfd_dep}
                    PROPERTIES INTERFACE_INCLUDE_DIRECTORIES "${_rfd_fixed_inc_dirs}"
                  )
                  MESSAGE(STATUS "  Fixed ${_rfd_dep} include: ${_rfd_inc_dirs} -> ${_rfd_fixed_inc_dirs}")
                ENDIF()
              ENDIF()
            ENDIF()
          ENDFOREACH()
        ENDIF()
      ELSEIF(_RFD_FOUND_VIA STREQUAL "module")
        MESSAGE(STATUS "Found ${_RFD_PACKAGE} ${${_RFD_PACKAGE}_VERSION} via CMake Find module. Using installed package.")
        RV_SET_FOUND_MODULE_DIRS(${_RFD_TARGET} ${_RFD_PACKAGE} "${_RFD_DEPS_LIST_TARGETS}")
      ELSEIF(_RFD_FOUND_VIA STREQUAL "pkgconfig")
        MESSAGE(STATUS "Found ${_RFD_PACKAGE} ${${_RFD_PACKAGE}_VERSION} via pkg-config. Using installed package.")
        RV_SET_FOUND_PKGCONFIG_DIRS(${_RFD_TARGET} ${_RFD_TARGET}_PC)
      ENDIF()

      FOREACH(
        _rfd_dep
        ${_RFD_DEPS_LIST_TARGETS}
      )
        # Resolve the target to append to RV_DEPS_LIST. rv_stage.cmake's RPATH fixup loop expects all entries to have IMPORTED_LOCATION.
        SET(_rfd_actual_dep
            ${_rfd_dep}
        )

        # If the upstream target name doesn't exist, try the namespaced variant. Conan CMakeDeps creates <Package>::<target> instead of the upstream
        # non-namespaced name (e.g. openjph::openjph instead of openjph).
        IF(NOT TARGET ${_rfd_dep})
          SET(_rfd_namespaced
              "${_RFD_PACKAGE}::${_rfd_dep}"
          )
          IF(TARGET ${_rfd_namespaced})
            SET(_rfd_actual_dep
                ${_rfd_namespaced}
            )
          ELSE()
            MESSAGE(WARNING "RV_FIND_DEPENDENCY: target ${_rfd_dep} (and ${_rfd_namespaced}) not found, skipping RV_DEPS_LIST append")
            CONTINUE()
          ENDIF()
        ENDIF()

        # Resolve INTERFACE_LIBRARY targets (e.g. Conan CMakeDeps wrappers) to their underlying real target. Conan CMakeDeps may create nested INTERFACE chains
        # (e.g. libraw::libraw → libraw::libraw_ → CONAN_LIB::...), so traverse up to 3 levels with a visited set to prevent infinite loops.
        IF(TARGET ${_rfd_actual_dep})
          GET_TARGET_PROPERTY(_rfd_dep_type ${_rfd_actual_dep} TYPE)
          IF(_rfd_dep_type STREQUAL "INTERFACE_LIBRARY")
            SET(_rfd_found_real
                FALSE
            )
            SET(_rfd_iface_queue
                ${_rfd_actual_dep}
            )
            SET(_rfd_iface_visited
                ""
            )
            SET(_rfd_iface_depth
                0
            )
            WHILE(
              _rfd_iface_queue
              AND NOT _rfd_found_real
              AND _rfd_iface_depth LESS 3
            )
              SET(_rfd_iface_next_queue
                  ""
              )
              FOREACH(
                _rfd_iface_tgt
                ${_rfd_iface_queue}
              )
                IF(_rfd_found_real)
                  BREAK()
                ENDIF()
                IF("${_rfd_iface_tgt}" IN_LIST _rfd_iface_visited)
                  CONTINUE()
                ENDIF()
                LIST(APPEND _rfd_iface_visited "${_rfd_iface_tgt}")
                GET_TARGET_PROPERTY(_rfd_iface_libs ${_rfd_iface_tgt} INTERFACE_LINK_LIBRARIES)
                IF(NOT _rfd_iface_libs)
                  CONTINUE()
                ENDIF()
                RV_EXTRACT_LINK_TARGETS("${_rfd_iface_libs}" _rfd_resolved_deps)
                FOREACH(
                  _rfd_resolved_dep
                  ${_rfd_resolved_deps}
                )
                  GET_TARGET_PROPERTY(_rfd_resolved_type ${_rfd_resolved_dep} TYPE)
                  IF(NOT _rfd_resolved_type STREQUAL "INTERFACE_LIBRARY")
                    SET(_rfd_actual_dep
                        ${_rfd_resolved_dep}
                    )
                    SET(_rfd_found_real
                        TRUE
                    )
                    BREAK()
                  ELSE()
                    LIST(APPEND _rfd_iface_next_queue ${_rfd_resolved_dep})
                  ENDIF()
                ENDFOREACH()
              ENDFOREACH()
              SET(_rfd_iface_queue
                  ${_rfd_iface_next_queue}
              )
              MATH(EXPR _rfd_iface_depth "${_rfd_iface_depth} + 1")
            ENDWHILE()
            IF(NOT _rfd_found_real)
              MESSAGE(WARNING "RV_FIND_DEPENDENCY: ${_rfd_dep} is INTERFACE but no underlying library target found, skipping RV_DEPS_LIST append")
              CONTINUE()
            ENDIF()
          ENDIF()
        ENDIF()
        LIST(APPEND RV_DEPS_LIST ${_rfd_actual_dep})
        RV_RESOLVE_DARWIN_INSTALL_NAME(${_rfd_actual_dep})

        # This dependency was satisfied from an installed package, so it is a prebuilt artifact whose ABI the build is trusting. Register it for probing and for
        # the manifest. Dependencies built from source are deliberately not registered: they are described by their build recipe, and probing them would slow
        # every configure for no benefit.
        IF(RV_DEPS_PROBE_ARTIFACTS)
          RV_REGISTER_PREBUILT_TARGET(${_rfd_actual_dep})
        ENDIF()
      ENDFOREACH()

      STRING(TOUPPER ${_RFD_PACKAGE} _RFD_PKG_UPPER)
      SET(RV_DEPS_${_RFD_PKG_UPPER}_VERSION
          ${${_RFD_PACKAGE}_VERSION}
          CACHE INTERNAL "" FORCE
      )

      RV_PRINT_PACKAGE_INFO(${_RFD_PACKAGE})
    ELSE()
      MESSAGE(STATUS "${_RFD_PACKAGE} ${_RFD_VERSION} not found. It will be built from source")
    ENDIF()
  ENDIF()

  IF(_rfd_store_entry)
    # <Package>_ROOT pointed at the entry for this search only; whatever the caller had is put back.
    IF(_rfd_store_saved_root_defined)
      SET(${_RFD_PACKAGE}_ROOT
          "${_rfd_store_saved_root}"
      )
    ELSE()
      UNSET(${_RFD_PACKAGE}_ROOT)
    ENDIF()

    # Reported as coming from the store only when it did. The search can still settle elsewhere -- a find module that prefers a cached or system location -- and
    # a report that says "store" while the build links something else is worse than none.
    IF(${_RFD_TARGET}_FOUND)
      # Compared after resolving symbolic links: the found-package helpers resolve them, and a store under a linked directory (/tmp on macOS) would otherwise
      # never match.
      GET_FILENAME_COMPONENT(_rfd_store_found_real "${_install_dir}" REALPATH)
      GET_FILENAME_COMPONENT(_rfd_store_entry_real "${_rfd_store_entry}" REALPATH)
      STRING(FIND "${_rfd_store_found_real}/" "${_rfd_store_entry_real}/" _rfd_store_inside)
      IF(_rfd_store_inside EQUAL 0)
        MESSAGE(STATUS "${_RFD_TARGET}: found in the dependency store (${_rfd_store_entry})")
      ELSE()
        MESSAGE(WARNING "${_RFD_TARGET}: a published store entry exists at '${_rfd_store_entry}', but ${_RFD_PACKAGE} was found at '${_install_dir}' instead")
      ENDIF()
    ENDIF()
  ENDIF()
ENDMACRO()
