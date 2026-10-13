# *****************************************************************************
# Copyright 2026 Autodesk, Inc. All rights reserved.
#
# SPDX-License-Identifier: Apache-2.0
#
# *****************************************************************************

#
# Publish a staged dependency install into the store. Run as a CMake script:
#
# cmake -DRV_PUBLISH_STAGING=<staged install> -DRV_PUBLISH_FINAL=<store entry install> -P rv_store_publish.cmake
#
# The install is assembled in the staging directory and moved into place here, because a store entry has to appear complete or not at all. Installing directly
# into the store entry would leave a partial tree that the next configure -- in any build directory, on any machine sharing the store -- would find and use as a
# finished dependency, which is a failure that looks like a broken build of whatever consumed it.
#
# The move is a rename, which is atomic within one filesystem; the staging directory is inside the store entry for exactly that reason, so a store on another
# filesystem from the build still works.
#
# Two configurations can finish the same dependency at the same time (task 5.5), so a final directory that already exists is success rather than an error:
# whoever got there first published the same thing, for the same identity, from the same source. The rename is attempted rather than only checked for, and
# checked again after it fails, because the check on its own is a race.
#

IF(NOT RV_PUBLISH_FINAL)
  MESSAGE(FATAL_ERROR "rv_store_publish: RV_PUBLISH_FINAL is required")
ENDIF()

# Staging leaves the directory skeletons it created behind, because the rename moves the tree out of them. Only empty directories are removed, so a concurrent
# build staging its own tree is untouched.
FUNCTION(RV_PUBLISH_TIDY_EMPTY _rvpte_path _rvpte_root)
  SET(_rvpte_current
      "${_rvpte_path}"
  )
  WHILE(
    _rvpte_current
    AND IS_DIRECTORY "${_rvpte_current}"
    AND NOT "${_rvpte_current}" STREQUAL "${_rvpte_root}"
  )
    FILE(GLOB _rvpte_entries "${_rvpte_current}/*")
    IF(_rvpte_entries)
      RETURN()
    ENDIF()
    FILE(REMOVE_RECURSE "${_rvpte_current}")
    GET_FILENAME_COMPONENT(_rvpte_current "${_rvpte_current}" DIRECTORY)
  ENDWHILE()
ENDFUNCTION()

FUNCTION(RV_PUBLISH_TIDY_TREE _rvptt_root)
  IF(NOT _rvptt_root
     OR NOT EXISTS "${_rvptt_root}"
  )
    RETURN()
  ENDIF()
  FILE(
    GLOB_RECURSE _rvptt_entries
    LIST_DIRECTORIES TRUE
    "${_rvptt_root}/*"
  )
  LIST(SORT _rvptt_entries)
  LIST(REVERSE _rvptt_entries)
  FOREACH(
    _rvptt_entry
    ${_rvptt_entries}
  )
    RV_PUBLISH_TIDY_EMPTY("${_rvptt_entry}" "${_rvptt_root}")
  ENDFOREACH()
  FILE(GLOB _rvptt_remaining "${_rvptt_root}/*")
  IF(NOT _rvptt_remaining)
    FILE(REMOVE_RECURSE "${_rvptt_root}")
  ENDIF()
ENDFUNCTION()

# Before: anything an earlier run left behind. After: this run's own skeletons, once the tree has been moved out of them.
RV_PUBLISH_TIDY_TREE("${RV_PUBLISH_ROOT}")

# The staged tree is found by searching the staging root for the install suffix, rather than by recomputing its path. CMake derives the DESTDIR path itself --
# it folds a drive letter into it, and the obvious spellings of that do not match what it produces -- so a path computed elsewhere is a guess, and a wrong guess
# here publishes nothing while looking like it worked.
IF(RV_PUBLISH_ROOT
   AND RV_PUBLISH_SUFFIX
)
  # Every directory under the root is considered and matched on its tail, rather than globbing a pattern with a wildcard in the middle: DESTDIR prepends the
  # whole install path, so the staged tree sits many levels down and a single-level pattern silently matches nothing.
  FILE(
    GLOB_RECURSE _rvp_directories
    LIST_DIRECTORIES TRUE
    "${RV_PUBLISH_ROOT}/*"
  )
  FOREACH(
    _rvp_directory
    ${_rvp_directories}
  )
    IF(_rvp_directory MATCHES "/${RV_PUBLISH_SUFFIX}$")
      SET(RV_PUBLISH_STAGING
          "${_rvp_directory}"
      )
    ENDIF()
  ENDFOREACH()
ENDIF()
IF(NOT RV_PUBLISH_STAGING)
  SET(RV_PUBLISH_STAGING
      "${RV_PUBLISH_ROOT}/${RV_PUBLISH_SUFFIX}"
  )
ENDIF()

IF(NOT EXISTS "${RV_PUBLISH_STAGING}")
  IF(EXISTS "${RV_PUBLISH_FINAL}")
    # Nothing staged, and something is already at the destination. Saying so matters: this is reached when the staged tree could not be found, and returning
    # quietly here is how a half-written entry survived a build that reported success.
    MESSAGE(STATUS "Dependency store: nothing staged under '${RV_PUBLISH_ROOT}', leaving the existing '${RV_PUBLISH_FINAL}'")
    RETURN()
  ENDIF()
  MESSAGE(FATAL_ERROR "rv_store_publish: nothing was staged at '${RV_PUBLISH_STAGING}' and no store entry exists at '${RV_PUBLISH_FINAL}'")
ENDIF()

# A published entry is one that carries the marker, not merely one whose directory exists: RV's own configure creates the install directory for every dependency
# so that imported targets name a directory that exists, so a bare directory here may be an empty leftover rather than a dependency. With a staged tree in hand,
# a destination that was never published is discarded and replaced.
GET_FILENAME_COMPONENT(_rvp_final_parent "${RV_PUBLISH_FINAL}" DIRECTORY)
SET(_rvp_marker
    "${_rvp_final_parent}/.published"
)

IF(EXISTS "${RV_PUBLISH_FINAL}")
  IF(EXISTS "${_rvp_marker}")
    # Genuinely published, by an earlier build or by a concurrent one: the first publisher wins, and their tree is the same dependency for the same identity.
    FILE(REMOVE_RECURSE "${RV_PUBLISH_STAGING}")
    MESSAGE(STATUS "Dependency store: '${RV_PUBLISH_FINAL}' is already published, staged copy discarded")
    RETURN()
  ENDIF()
  MESSAGE(STATUS "Dependency store: '${RV_PUBLISH_FINAL}' exists but was never published; replacing it")
  FILE(REMOVE_RECURSE "${RV_PUBLISH_FINAL}")
ENDIF()

IF(NOT EXISTS "${_rvp_final_parent}")
  FILE(MAKE_DIRECTORY "${_rvp_final_parent}")
ENDIF()

EXECUTE_PROCESS(
  COMMAND ${CMAKE_COMMAND} -E rename "${RV_PUBLISH_STAGING}" "${RV_PUBLISH_FINAL}"
  RESULT_VARIABLE _rvp_result
)

IF(_rvp_result)
  IF(EXISTS "${RV_PUBLISH_FINAL}")
    # Lost the race by milliseconds: the winner published the same thing.
    FILE(REMOVE_RECURSE "${RV_PUBLISH_STAGING}")
    MESSAGE(STATUS "Dependency store: '${RV_PUBLISH_FINAL}' was published by a concurrent build, staged copy discarded")
  ELSE()
    MESSAGE(FATAL_ERROR "rv_store_publish: could not move '${RV_PUBLISH_STAGING}' to '${RV_PUBLISH_FINAL}' (exit ${_rvp_result})")
  ENDIF()
ELSE()
  # The marker is written last, and only after the tree is in place: until it exists the entry is not consumable, which is what makes an interrupted publish
  # leave nothing usable behind.
  FILE(
    WRITE "${_rvp_marker}"
    ""
  )
  RV_PUBLISH_TIDY_TREE("${RV_PUBLISH_ROOT}")
  MESSAGE(STATUS "Dependency store: published '${RV_PUBLISH_FINAL}'")
ENDIF()
