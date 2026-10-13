# *****************************************************************************
# Copyright 2026 Autodesk, Inc. All rights reserved.
#
# SPDX-License-Identifier: Apache-2.0
#
# *****************************************************************************

#
# The identity-addressed dependency store.
#
# A store entry is the *installed* tree of one dependency for one identity:
#
# <store>/<identity>/<dependency>/install/...
#
# Only installed trees are placed there. Source, build and stamp trees stay in the build directory, because they embed absolute paths and are not portable -- a
# store on a shared path would hand one machine another machine's build state, which is worse than rebuilding. See D4.
#
# Eligibility is per dependency (D5): naming a dependency in RV_DEPS_STORE_ELIGIBLE is the statement that its installed tree has passed its relocation check, so
# the store never holds a dependency that cannot be moved.
#
# Everything here is inert while RV_DEPS_STORE is unset, which is the default.
#
SET(RV_DEPS_INSTALL_SCRIPT
    "${PROJECT_SOURCE_DIR}/cmake/macros/rv_store_install.cmake"
    CACHE INTERNAL "Path to the staged install and publish step"
)

SET(RV_DEPS_PUBLISH_SCRIPT
    "${PROJECT_SOURCE_DIR}/cmake/macros/rv_store_publish.cmake"
    CACHE INTERNAL "Path to the store publish step"
)

#
# RV_RESOLVE_DEPS_STORE()
#
# Resolve where installed dependency trees go. Sets:
#
# RV_DEPS_INSTALL_ROOT        the root installed trees are placed under RV_DEPS_STORE_IDENTITY_DIR  the store entry for this identity, empty when no store is
# used
#
FUNCTION(RV_RESOLVE_DEPS_STORE)
  SET(RV_DEPS_STORE_IDENTITY_DIR
      ""
      CACHE INTERNAL "The store entry for this build identity, empty when no store is used" FORCE
  )

  IF(NOT RV_DEPS_STORE)
    # No store: installed trees stay beside the source and build trees, exactly as before.
    SET(RV_DEPS_INSTALL_ROOT
        "${RV_DEPS_BASE_DIR}"
        CACHE STRING "Root that installed dependency trees are placed under" FORCE
    )
    RETURN()
  ENDIF()

  IF(NOT RV_BUILD_IDENTITY_AVAILABLE)
    MESSAGE(
      FATAL_ERROR
        "RV_DEPS_STORE is set, but no build identity was computed, and a store entry is addressed by identity. Set -DRV_BUILD_IDENTITY=ON, provide an interpreter with -DRV_BUILD_PYTHON=<path> if none was found, or unset RV_DEPS_STORE."
    )
  ENDIF()

  # The hash carries its algorithm prefix, which cannot appear in a path on Windows.
  STRING(REPLACE "sha256:" "" _rvds_identity "${RV_BUILD_IDENTITY_HASH}")
  SET(_rvds_entry
      "${RV_DEPS_STORE}/${_rvds_identity}"
  )

  SET(RV_DEPS_STORE_IDENTITY_DIR
      "${_rvds_entry}"
      CACHE INTERNAL "The store entry for this build identity, empty when no store is used" FORCE
  )
  SET(RV_DEPS_INSTALL_ROOT
      "${_rvds_entry}"
      CACHE STRING "Root that installed dependency trees are placed under" FORCE
  )

  IF(NOT EXISTS "${RV_DEPS_STORE}")
    FILE(MAKE_DIRECTORY "${RV_DEPS_STORE}")
  ENDIF()

  MESSAGE(STATUS "Dependency store: ${RV_DEPS_STORE}")
  MESSAGE(STATUS "    identity:     ${RV_BUILD_IDENTITY_HASH}")
  IF(RV_DEPS_STORE_ELIGIBLE)
    MESSAGE(STATUS "    eligible:     ${RV_DEPS_STORE_ELIGIBLE}")
  ELSE()
    # Worth saying plainly: a store with nothing eligible in it places nothing, and the build is unchanged. Otherwise this looks like it did something.
    MESSAGE(STATUS "    eligible:     none, so no dependency is placed in the store")
  ENDIF()
ENDFUNCTION()

#
# RV_DEPS_IS_STORE_ELIGIBLE(<target> <out_var>)
#
# Whether this dependency's installed tree may be placed in the store.
#
FUNCTION(RV_DEPS_IS_STORE_ELIGIBLE _rvdse_target _rvdse_out)
  SET(${_rvdse_out}
      FALSE
      PARENT_SCOPE
  )
  IF(NOT RV_DEPS_STORE)
    RETURN()
  ENDIF()
  IF(_rvdse_target IN_LIST RV_DEPS_STORE_ELIGIBLE)
    SET(${_rvdse_out}
        TRUE
        PARENT_SCOPE
    )
  ENDIF()
ENDFUNCTION()

#
# RV_DEPS_INSTALL_PATHS(<target> <install_dir_out> <staging_root_out>)
#
# Where a dependency's installed tree goes, and where it is assembled first.
#
# An eligible dependency is installed into a staging tree with DESTDIR and renamed into place once the install has finished, so that an interrupted build leaves
# nothing a later configure would consume as a dependency. The rename is the publish: it is atomic within one filesystem, and the staging tree is inside the
# same store entry for that reason.
#
# DESTDIR rather than a staging install *prefix*, and the distinction matters. The configure prefix stays the location the tree will occupy once published, so
# anything a dependency bakes into its installed files names the real place. With a staging prefix instead, every baked-in path names a directory that does not
# exist afterwards -- a broken tree that a relocation check on the published path cannot even see, because it looks for the path it moved the tree from.
#
# An ineligible dependency, or one built with no store configured, gets the ordinary directory and no staging root, and is installed in place as it always was.
#
FUNCTION(RV_DEPS_INSTALL_PATHS _rvdip_target _rvdip_install_out _rvdip_staging_out)
  RV_DEPS_IS_STORE_ELIGIBLE(${_rvdip_target} _rvdip_eligible)

  IF(_rvdip_eligible
     AND RV_DEPS_STORE_IDENTITY_DIR
  )
    SET(${_rvdip_install_out}
        "${RV_DEPS_STORE_IDENTITY_DIR}/${_rvdip_target}/install"
        PARENT_SCOPE
    )
    SET(${_rvdip_staging_out}
        "${RV_DEPS_STORE_IDENTITY_DIR}/.publishing"
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
# RV_DEPS_PUBLISH_COMPLETE(<target> <out_var>)
#
# Whether a dependency's installed tree exists and is finished.
#
# A staged tree that was never renamed into place is invisible to this, which is the point: an interrupted build leaves nothing that a later configure would
# consume.
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

FUNCTION(RV_DEPS_PUBLISH_COMPLETE _rvdpc_target _rvdpc_out)
  RV_DEPS_INSTALL_PATHS(${_rvdpc_target} _rvdpc_install _rvdpc_staging)
  RV_DEPS_PUBLISH_MARKER("${_rvdpc_install}" _rvdpc_marker)
  IF(EXISTS "${_rvdpc_install}"
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
# RV_DEPS_STAGED_INSTALL_DIR(<install_dir> <staging_root> <out_var>)
#
# Where an install lands when it is staged with DESTDIR.
#
# DESTDIR is prepended to the install prefix, so the staged tree sits under the staging root at the same path the install was configured with. The drive letter
# is folded into the path rather than left in the middle of it, which is what CMake's own install script does on Windows, so that the rename afterwards moves a
# directory and not something that only looks like one.
#
FUNCTION(RV_DEPS_STAGED_INSTALL_DIR _rvdsi_install _rvdsi_staging_root _rvdsi_out)
  IF(NOT _rvdsi_staging_root)
    SET(${_rvdsi_out}
        "${_rvdsi_install}"
        PARENT_SCOPE
    )
    RETURN()
  ENDIF()
  STRING(
    REGEX
    REPLACE "^([A-Za-z]):/" "/\\1/" _rvdsi_relative "${_rvdsi_install}"
  )
  SET(${_rvdsi_out}
      "${_rvdsi_staging_root}${_rvdsi_relative}"
      PARENT_SCOPE
  )
ENDFUNCTION()
