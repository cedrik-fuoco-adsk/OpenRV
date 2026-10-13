# *****************************************************************************
# Copyright 2026 Autodesk, Inc. All rights reserved.
#
# SPDX-License-Identifier: Apache-2.0
#
# *****************************************************************************

#
# The identity-addressed dependency store.
#
# A store entry is the *installed* tree of one dependency, for one platform, built from one recipe:
#
# <store>/<platform>/<dependency>/<recipe>/install/...
#
# <platform> is a short digest of the build identity together with the platform facts the identity does not yet carry -- the macOS architectures and deployment
# target, and the Linux C library -- so an entry is never served to a build targeting something else. <recipe> is a short digest of what the dependency is built
# from: its version, its download hash, its dependency files and the patches they apply. A version bump or a patch change therefore addresses a new entry rather
# than finding the old one, so a hit can only occur for the same content.
#
# Only installed trees are placed there. Source, build and stamp trees stay in the build directory, because they embed absolute paths and are not portable -- a
# store on a shared path would hand one machine another machine's build state, which is worse than rebuilding. See D4.
#
# Eligibility is per dependency (D5): naming a dependency in RV_DEPS_STORE_ELIGIBLE is the statement that its installed tree has passed its relocation check, so
# the store never holds a dependency that cannot be moved. A dependency forced to build from source is never stored.
#
# Everything here is inert while RV_DEPS_STORE is unset, which is the default: no store directory is created, no store is consulted, and no cache entry is added
# beyond the options themselves.
#

# Bumped whenever the layout of an entry or what the publish step writes into it changes, so that entries written by an older layout are not consumed.
SET(RV_DEPS_STORE_FORMAT
    "1"
)

SET(RV_DEPS_INSTALL_SCRIPT
    "${PROJECT_SOURCE_DIR}/cmake/macros/rv_store_install.cmake"
)

#
# The dependencies whose relocation check has passed, and which RV_DEPS_STORE_ELIGIBLE's "default" stands for. Each name here was installed, relocated, linked
# against and run from a different path before being added, and is then verified by a first build populating the store and a second build directory reusing it
# -- see docs/build_system/dependency_store.md. RV_DEPS_ZLIB passed the gate on 2026-10-12, and the gate is re-run against the zlib the store actually publishes
# by src/build/test_deps_store_roundtrip.py.
#
# Kept here rather than as the cache default, so that adding or removing a name reaches trees that were configured before the change.
#
SET(RV_DEPS_STORE_ELIGIBLE_DEFAULT
    "RV_DEPS_ZLIB"
)

#
# RV_DEPS_FORGET_CACHED_PATHS(<prefix> [KEEP <prefix>])
#
# Remove every cache entry whose value names a path under <prefix>, except those under the KEEP prefix.
#
# A find module caches what it found (ZLIB_INCLUDE_DIR, ZLIB_LIBRARY_RELEASE, ...) and a dependency file caches its own paths (RV_DEPS_ZLIB_INCLUDE_DIR), and
# neither looks again while the cached value is set. Once the store location an entry came from is no longer the one in use -- the store was turned off, moved,
# or the dependency's recipe changed -- those values name a tree this configuration must not use. Matching on the value rather than on a list of names reaches
# every such entry without having to know which find module wrote it.
#
FUNCTION(RV_DEPS_FORGET_CACHED_PATHS _rvdfcp_prefix)
  CMAKE_PARSE_ARGUMENTS(_RVDFCP "" "KEEP" "" ${ARGN})
  IF(NOT _rvdfcp_prefix)
    RETURN()
  ENDIF()
  GET_CMAKE_PROPERTY(_rvdfcp_names CACHE_VARIABLES)
  FOREACH(
    _rvdfcp_name
    ${_rvdfcp_names}
  )
    # The store's own bookkeeping names the previous location on purpose, and is maintained by RV_RESOLVE_DEPS_STORE.
    IF(_rvdfcp_name MATCHES "^RV_DEPS_STORE")
      CONTINUE()
    ENDIF()
    GET_PROPERTY(
      _rvdfcp_value
      CACHE ${_rvdfcp_name}
      PROPERTY VALUE
    )
    STRING(FIND "${_rvdfcp_value}" "${_rvdfcp_prefix}/" _rvdfcp_at)
    IF(_rvdfcp_at EQUAL -1)
      CONTINUE()
    ENDIF()
    IF(_RVDFCP_KEEP)
      STRING(FIND "${_rvdfcp_value}" "${_RVDFCP_KEEP}/" _rvdfcp_keep_at)
      IF(NOT _rvdfcp_keep_at EQUAL -1)
        CONTINUE()
      ENDIF()
    ENDIF()
    MESSAGE(STATUS "Dependency store: forgetting ${_rvdfcp_name}, which names '${_rvdfcp_prefix}'")
    UNSET(${_rvdfcp_name} CACHE)
  ENDFOREACH()
ENDFUNCTION()

#
# RV_RESOLVE_DEPS_STORE()
#
# Resolve whether a store is used and which platform slot of it this configuration addresses. Sets, as ordinary variables visible to the dependency files:
#
# RV_DEPS_STORE_ROOT          the store location, absolute and in CMake's path form; empty when no store is used RV_DEPS_STORE_IDENTITY_DIR  the platform slot
# for this configuration; empty when no store is used
#
# The previously resolved slot is remembered, only once a store has been used, so that the next configure can tell the slot changed and forget the cached paths
# that still name it. That is what makes turning the store off -- or moving it -- a complete opt-out rather than one that only applies to trees that never saw a
# store.
#
MACRO(RV_RESOLVE_DEPS_STORE)
  SET(RV_DEPS_STORE_ROOT
      ""
  )
  SET(RV_DEPS_STORE_IDENTITY_DIR
      ""
  )
  # Left by an earlier version of this file, which cached these. A cached value would otherwise be read wherever the ordinary variable is not in scope.
  UNSET(RV_DEPS_STORE_IDENTITY_DIR CACHE)
  UNSET(RV_DEPS_INSTALL_ROOT CACHE)

  IF(RV_DEPS_STORE)
    _RV_DEPS_STORE_RESOLVE_SLOT()
  ENDIF()

  IF(DEFINED CACHE{RV_DEPS_STORE_LAST_SLOT}
     AND NOT "$CACHE{RV_DEPS_STORE_LAST_SLOT}" STREQUAL "${RV_DEPS_STORE_IDENTITY_DIR}"
  )
    MESSAGE(STATUS "Dependency store: the store slot changed from '$CACHE{RV_DEPS_STORE_LAST_SLOT}' to '${RV_DEPS_STORE_IDENTITY_DIR}'")
    RV_DEPS_FORGET_CACHED_PATHS("$CACHE{RV_DEPS_STORE_LAST_SLOT}")
  ENDIF()

  IF(RV_DEPS_STORE_IDENTITY_DIR)
    SET(RV_DEPS_STORE_LAST_SLOT
        "${RV_DEPS_STORE_IDENTITY_DIR}"
        CACHE INTERNAL "The store slot the previous configure used"
    )
  ELSE()
    UNSET(RV_DEPS_STORE_LAST_SLOT CACHE)
  ENDIF()
ENDMACRO()

FUNCTION(_RV_DEPS_STORE_RESOLVE_SLOT)
  IF(NOT RV_BUILD_IDENTITY_AVAILABLE)
    MESSAGE(
      FATAL_ERROR
        "RV_DEPS_STORE is set, but no build identity was computed, and a store entry is addressed by identity. Set -DRV_BUILD_IDENTITY=ON, provide an interpreter with -DRV_BUILD_PYTHON=<path> if none was found, or unset RV_DEPS_STORE."
    )
  ENDIF()

  # A store given as C:\rv-store, or as ~/.cache/rv-deps -- which no shell expands inside a -D argument -- is normalized here once, so every path derived from
  # it is in CMake's form. A backslash path breaks wherever it is interpolated into a string that is parsed again, and a relative one would mean something
  # different in every build directory; it is taken relative to the build directory, and reported.
  SET(_rvds_root
      "${RV_DEPS_STORE}"
  )
  IF(_rvds_root MATCHES "^~[/\\\\]?")
    IF(DEFINED ENV{HOME})
      SET(_rvds_home
          "$ENV{HOME}"
      )
    ELSE()
      SET(_rvds_home
          "$ENV{USERPROFILE}"
      )
    ENDIF()
    STRING(
      REGEX
      REPLACE "^~" "${_rvds_home}" _rvds_root "${_rvds_root}"
    )
  ENDIF()
  FILE(TO_CMAKE_PATH "${_rvds_root}" _rvds_root)
  GET_FILENAME_COMPONENT(_rvds_root "${_rvds_root}" ABSOLUTE BASE_DIR "${CMAKE_BINARY_DIR}")

  # The platform facts the identity does not carry yet, but which decide whether two installed trees are interchangeable: a universal or cross-architecture
  # macOS build, the oldest macOS a binary may run on, and the C library a Linux binary was linked against -- Rocky 9 artifacts do not run on Rocky 8.
  SET(_rvds_platform
      "identity=${RV_BUILD_IDENTITY_HASH}"
  )
  IF(APPLE)
    STRING(APPEND _rvds_platform "|osx_architectures=${CMAKE_OSX_ARCHITECTURES}|osx_deployment_target=${CMAKE_OSX_DEPLOYMENT_TARGET}")
  ELSEIF(UNIX)
    EXECUTE_PROCESS(
      COMMAND getconf GNU_LIBC_VERSION
      OUTPUT_VARIABLE _rvds_libc
      OUTPUT_STRIP_TRAILING_WHITESPACE ERROR_QUIET
    )
    IF(NOT _rvds_libc)
      SET(_rvds_libc
          "unknown"
      )
    ENDIF()
    STRING(APPEND _rvds_platform "|libc=${_rvds_libc}")
  ENDIF()
  STRING(APPEND _rvds_platform "|format=${RV_DEPS_STORE_FORMAT}")

  # Short digests keep entry paths well inside Windows' MAX_PATH, which staging doubles; 64 bits is ample to keep platforms apart in one store.
  STRING(SHA256 _rvds_digest "${_rvds_platform}")
  STRING(SUBSTRING "${_rvds_digest}" 0 16 _rvds_digest)

  SET(RV_DEPS_STORE_ROOT
      "${_rvds_root}"
      PARENT_SCOPE
  )
  SET(RV_DEPS_STORE_IDENTITY_DIR
      "${_rvds_root}/${_rvds_digest}"
      PARENT_SCOPE
  )

  IF(NOT EXISTS "${_rvds_root}")
    FILE(MAKE_DIRECTORY "${_rvds_root}")
  ENDIF()

  RV_DEPS_STORE_ELIGIBLE_LIST(_rvds_eligible)
  MESSAGE(STATUS "Dependency store: ${_rvds_root}")
  MESSAGE(STATUS "    identity:     ${RV_BUILD_IDENTITY_HASH}")
  MESSAGE(STATUS "    platform:     ${_rvds_platform}")
  MESSAGE(STATUS "    slot:         ${_rvds_root}/${_rvds_digest}")
  IF(_rvds_eligible)
    MESSAGE(STATUS "    eligible:     ${_rvds_eligible}")
  ELSE()
    # Worth saying plainly: a store with nothing eligible in it places nothing, and the build is unchanged. Otherwise this looks like it did something.
    MESSAGE(STATUS "    eligible:     none, so no dependency is placed in the store")
  ENDIF()
ENDFUNCTION()

#
# RV_DEPS_STORE_ELIGIBLE_LIST(<out_var>)
#
# RV_DEPS_STORE_ELIGIBLE with "default" replaced by the built-in list, so a user can extend the list without restating it ("default;RV_DEPS_IMATH") or replace
# it entirely. An empty value means nothing is eligible.
#
FUNCTION(RV_DEPS_STORE_ELIGIBLE_LIST _rvdsel_out)
  SET(_rvdsel_list
      ""
  )
  FOREACH(
    _rvdsel_name
    ${RV_DEPS_STORE_ELIGIBLE}
  )
    IF(_rvdsel_name STREQUAL "default")
      LIST(APPEND _rvdsel_list ${RV_DEPS_STORE_ELIGIBLE_DEFAULT})
    ELSE()
      LIST(APPEND _rvdsel_list ${_rvdsel_name})
    ENDIF()
  ENDFOREACH()
  LIST(REMOVE_DUPLICATES _rvdsel_list)
  SET(${_rvdsel_out}
      "${_rvdsel_list}"
      PARENT_SCOPE
  )
ENDFUNCTION()

#
# RV_DEPS_IS_STORE_ELIGIBLE(<target> <out_var>)
#
# Whether this dependency's installed tree may be placed in the store. A dependency forced to build from source is not: forcing a build is how a user gets away
# from a store entry, so a forced build must neither be served from the store nor publish into it.
#
FUNCTION(RV_DEPS_IS_STORE_ELIGIBLE _rvdse_target _rvdse_out)
  SET(${_rvdse_out}
      FALSE
      PARENT_SCOPE
  )
  IF(NOT RV_DEPS_STORE_IDENTITY_DIR
     OR ${_rvdse_target}_FORCE_BUILD
  )
    RETURN()
  ENDIF()
  RV_DEPS_STORE_ELIGIBLE_LIST(_rvdse_eligible)
  IF(_rvdse_target IN_LIST _rvdse_eligible)
    SET(${_rvdse_out}
        TRUE
        PARENT_SCOPE
    )
  ENDIF()
ENDFUNCTION()

#
# RV_DEPS_STORE_RECIPE(<target> <version> <out_var>)
#
# A short digest of what a dependency is built from, which names its entry within the platform slot. Computed from the dependency file that is being processed
# -- this is called from RV_CREATE_STANDARD_DEPS_VARIABLES, a macro, so CMAKE_CURRENT_LIST_FILE is the dependency's own file -- its build/ counterpart, every
# patch either of them names, the version, the download hash, and the library directory layout.
#
FUNCTION(RV_DEPS_STORE_RECIPE _rvdsr_target _rvdsr_version _rvdsr_out)
  SET(_rvdsr_text
      "format=${RV_DEPS_STORE_FORMAT}|target=${_rvdsr_target}|version=${_rvdsr_version}|download=${${_rvdsr_target}_DOWNLOAD_HASH}|rhel_lib64=${RHEL_VERBOSE}"
  )
  GET_FILENAME_COMPONENT(_rvdsr_name "${CMAKE_CURRENT_LIST_FILE}" NAME)
  SET(_rvdsr_files
      "${CMAKE_CURRENT_LIST_FILE}"
  )
  IF(EXISTS "${CMAKE_CURRENT_LIST_DIR}/build/${_rvdsr_name}")
    LIST(APPEND _rvdsr_files "${CMAKE_CURRENT_LIST_DIR}/build/${_rvdsr_name}")
  ENDIF()
  SET(_rvdsr_patches
      ""
  )
  FOREACH(
    _rvdsr_file
    ${_rvdsr_files}
  )
    FILE(SHA256 "${_rvdsr_file}" _rvdsr_file_digest)
    GET_FILENAME_COMPONENT(_rvdsr_file_name "${_rvdsr_file}" NAME)
    STRING(APPEND _rvdsr_text "|${_rvdsr_file_name}=${_rvdsr_file_digest}")
    FILE(READ "${_rvdsr_file}" _rvdsr_body)
    STRING(REGEX MATCHALL "patch/[A-Za-z0-9_.+-]+" _rvdsr_named "${_rvdsr_body}")
    LIST(APPEND _rvdsr_patches ${_rvdsr_named})
  ENDFOREACH()
  LIST(REMOVE_DUPLICATES _rvdsr_patches)
  LIST(SORT _rvdsr_patches)
  FOREACH(
    _rvdsr_patch
    ${_rvdsr_patches}
  )
    IF(EXISTS "${CMAKE_CURRENT_LIST_DIR}/${_rvdsr_patch}")
      FILE(SHA256 "${CMAKE_CURRENT_LIST_DIR}/${_rvdsr_patch}" _rvdsr_patch_digest)
      STRING(APPEND _rvdsr_text "|${_rvdsr_patch}=${_rvdsr_patch_digest}")
    ENDIF()
  ENDFOREACH()
  STRING(SHA256 _rvdsr_digest "${_rvdsr_text}")
  STRING(SUBSTRING "${_rvdsr_digest}" 0 12 _rvdsr_digest)
  SET(${_rvdsr_out}
      "${_rvdsr_digest}"
      PARENT_SCOPE
  )
ENDFUNCTION()

#
# RV_DEPS_INSTALL_PATHS(<target> <install_dir_out> <staging_out>)
#
# Where a dependency's installed tree goes, and whether it is staged and published there.
#
# An eligible dependency is installed into a private staging tree with DESTDIR and renamed into place once the install has finished, so that an interrupted
# build leaves nothing a later configure would consume as a dependency. <staging_out> is then the store root, which is where rv_store_install.cmake makes each
# install's private staging directory; it is empty for everything else.
#
# DESTDIR rather than a staging install *prefix*, and the distinction matters. The configure prefix stays the location the tree will occupy once published, so
# anything a dependency bakes into its installed files names the real place. With a staging prefix instead, every baked-in path names a directory that does not
# exist afterwards -- a broken tree that a relocation check on the published path cannot even see, because it looks for the path it moved the tree from.
#
# The recipe digest is taken from ${target}_STORE_RECIPE, which RV_CREATE_STANDARD_DEPS_VARIABLES sets, and computed here otherwise.
#
# An ineligible dependency, or one built with no store configured, gets the ordinary directory and no staging, and is installed in place as it always was.
#
FUNCTION(RV_DEPS_INSTALL_PATHS _rvdip_target _rvdip_install_out _rvdip_staging_out)
  RV_DEPS_IS_STORE_ELIGIBLE(${_rvdip_target} _rvdip_eligible)

  IF(_rvdip_eligible)
    IF(DEFINED ${_rvdip_target}_STORE_RECIPE)
      SET(_rvdip_recipe
          "${${_rvdip_target}_STORE_RECIPE}"
      )
    ELSE()
      RV_DEPS_STORE_RECIPE(${_rvdip_target} "${${_rvdip_target}_VERSION}" _rvdip_recipe)
    ENDIF()
    SET(${_rvdip_install_out}
        "${RV_DEPS_STORE_IDENTITY_DIR}/${_rvdip_target}/${_rvdip_recipe}/install"
        PARENT_SCOPE
    )
    SET(${_rvdip_staging_out}
        "${RV_DEPS_STORE_ROOT}"
        PARENT_SCOPE
    )
  ELSE()
    SET(${_rvdip_install_out}
        "${RV_DEPS_BASE_DIR}/${_rvdip_target}/install"
        PARENT_SCOPE
    )
    SET(${_rvdip_staging_out}
        ""
        PARENT_SCOPE
    )
  ENDIF()
ENDFUNCTION()

#
# RV_DEPS_PUBLISH_MARKER(<entry install dir> <out_var>)
#
# The file whose presence means a store entry was published rather than merely present.
#
# Something has to distinguish those two, because RV's own configure creates the install directory (and its include subdirectory) for every dependency, so that
# imported targets name a directory that exists. A published entry is therefore one that carries this marker, which only the publish step writes, and which is
# only written after the tree has been moved into place.
#
FUNCTION(RV_DEPS_PUBLISH_MARKER _rvdpm_install _rvdpm_out)
  GET_FILENAME_COMPONENT(_rvdpm_parent "${_rvdpm_install}" DIRECTORY)
  SET(${_rvdpm_out}
      "${_rvdpm_parent}/.published"
      PARENT_SCOPE
  )
ENDFUNCTION()

#
# RV_DEPS_PUBLISH_COMPLETE(<target> <out_var>)
#
# Whether a dependency's store entry exists and is finished. A staged tree that was never renamed into place is invisible to this, which is the point: an
# interrupted build leaves nothing that a later configure would consume.
#
FUNCTION(RV_DEPS_PUBLISH_COMPLETE _rvdpc_target _rvdpc_out)
  RV_DEPS_INSTALL_PATHS(${_rvdpc_target} _rvdpc_install _rvdpc_staging)
  RV_DEPS_PUBLISH_MARKER("${_rvdpc_install}" _rvdpc_marker)
  IF(_rvdpc_staging
     AND EXISTS "${_rvdpc_install}"
     AND EXISTS "${_rvdpc_marker}"
  )
    SET(${_rvdpc_out}
        TRUE
        PARENT_SCOPE
    )
  ELSE()
    SET(${_rvdpc_out}
        FALSE
        PARENT_SCOPE
    )
  ENDIF()
ENDFUNCTION()

#
# RV_DEPS_STORE_FIXUP(<target> <cmake code>)
#
# Code the install step runs against the staged tree, as RV_STAGED_INSTALL, before it is published. A dependency that adjusts its installed files after
# installing -- an install name, a renamed import library -- does it here when it is stored, because a published entry is shared and is never modified in place.
#
FUNCTION(RV_DEPS_STORE_FIXUP _rvdsf_target _rvdsf_code)
  FILE(
    WRITE "${RV_DEPS_BASE_DIR}/${_rvdsf_target}/store_fixup.cmake"
    "${_rvdsf_code}\n"
  )
ENDFUNCTION()

#
# RV_DEPS_STORE_RESET_STALE_INSTALL(<target> <install dir>)
#
# A store is a cache, and an entry can be deleted from it. The build directory that produced the entry still has ExternalProject stamps saying the install step
# ran, and would not run it again, leaving the build to link against a tree that is gone. When an entry is not published, its install and done stamps are
# removed so the install runs, and publishes, again.
#
FUNCTION(RV_DEPS_STORE_RESET_STALE_INSTALL _rvdsrsi_target _rvdsrsi_install)
  RV_DEPS_PUBLISH_MARKER("${_rvdsrsi_install}" _rvdsrsi_marker)
  IF(EXISTS "${_rvdsrsi_marker}")
    RETURN()
  ENDIF()
  SET(_rvdsrsi_stamps
      "${CMAKE_CURRENT_BINARY_DIR}/${_rvdsrsi_target}-prefix/src/${_rvdsrsi_target}-stamp"
  )
  # A multi-configuration generator keeps the stamps in a per-configuration subdirectory.
  FILE(GLOB _rvdsrsi_found "${_rvdsrsi_stamps}/${_rvdsrsi_target}-install" "${_rvdsrsi_stamps}/*/${_rvdsrsi_target}-install")
  IF(_rvdsrsi_found)
    FILE(GLOB _rvdsrsi_done "${_rvdsrsi_stamps}/${_rvdsrsi_target}-done" "${_rvdsrsi_stamps}/*/${_rvdsrsi_target}-done")
    FILE(REMOVE ${_rvdsrsi_found} ${_rvdsrsi_done})
    MESSAGE(STATUS "${_rvdsrsi_target}: its store entry is not published, so its install will run again")
  ENDIF()
ENDFUNCTION()
