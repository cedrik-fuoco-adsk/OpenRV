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
# The install is assembled in a staging directory and moved into place here, because a store entry has to appear complete or not at all. Installing directly
# into the store entry would leave a partial tree that the next configure -- in any build directory, on any machine sharing the store -- would find and use as a
# finished dependency, which is a failure that looks like a broken build of whatever consumed it.
#
# The move is a rename, which is atomic within one filesystem; staging directories are inside the store for exactly that reason, so a store on another
# filesystem from the build still works.
#
# Publishing is serialized per entry with a lock beside it, so two builds finishing the same dependency at once cannot interleave: under the lock, an entry that
# carries its marker is published and is never touched again -- the staged copy is discarded, because the entry's recipe digest says it is the same dependency
# -- and an entry without one is replaced. The marker is written last, so until the tree is complete in place nothing consumes it.
#

FOREACH(
  _rvp_required
  RV_PUBLISH_STAGING RV_PUBLISH_FINAL
)
  IF(NOT ${_rvp_required})
    MESSAGE(FATAL_ERROR "rv_store_publish: ${_rvp_required} is required")
  ENDIF()
ENDFOREACH()

GET_FILENAME_COMPONENT(_rvp_entry "${RV_PUBLISH_FINAL}" DIRECTORY)
GET_FILENAME_COMPONENT(_rvp_entry_parent "${_rvp_entry}" DIRECTORY)
SET(_rvp_marker
    "${_rvp_entry}/.published"
)
FILE(MAKE_DIRECTORY "${_rvp_entry_parent}")

# Outside the entry, so that replacing the entry never removes the file being locked. Long enough for a slow shared filesystem, short enough that a hung
# publisher is reported rather than waited on forever.
FILE(
  LOCK "${_rvp_entry}.lock"
  GUARD PROCESS
  TIMEOUT 1800
  RESULT_VARIABLE _rvp_lock_result
)
IF(NOT _rvp_lock_result EQUAL 0)
  MESSAGE(FATAL_ERROR "rv_store_publish: could not lock '${_rvp_entry}.lock': ${_rvp_lock_result}")
ENDIF()

IF(EXISTS "${_rvp_marker}")
  # Published already, by an earlier build or by one that finished first. The entry is never replaced once published: other builds may be reading it.
  IF(EXISTS "${RV_PUBLISH_STAGING}")
    FILE(REMOVE_RECURSE "${RV_PUBLISH_STAGING}")
    MESSAGE(STATUS "Dependency store: '${RV_PUBLISH_FINAL}' is already published, staged copy discarded")
  ELSE()
    MESSAGE(STATUS "Dependency store: '${RV_PUBLISH_FINAL}' is already published")
  ENDIF()
  FILE(LOCK "${_rvp_entry}.lock" RELEASE)
  RETURN()
ENDIF()

IF(NOT IS_DIRECTORY "${RV_PUBLISH_STAGING}")
  # Nothing staged and nothing published: the install produced nothing. Reporting success here would leave the build pointing at an entry that does not exist.
  FILE(LOCK "${_rvp_entry}.lock" RELEASE)
  MESSAGE(FATAL_ERROR "rv_store_publish: nothing was staged at '${RV_PUBLISH_STAGING}' and '${RV_PUBLISH_FINAL}' is not published")
ENDIF()

# Not published, so whatever is at the destination is not a dependency: RV's configure creates every dependency's install directory, with an include
# subdirectory, so that imported targets name a directory that exists, and an interrupted publish can leave a tree without its marker. It is replaced. A
# configure in another build directory can create that skeleton again between the removal and the rename, which makes the rename fail, so the pair is retried.
SET(_rvp_result
    1
)
FOREACH(
  _rvp_attempt
  RANGE 1 5
)
  IF(EXISTS "${RV_PUBLISH_FINAL}")
    FILE(REMOVE_RECURSE "${RV_PUBLISH_FINAL}")
  ENDIF()
  FILE(MAKE_DIRECTORY "${_rvp_entry}")
  EXECUTE_PROCESS(
    COMMAND ${CMAKE_COMMAND} -E rename "${RV_PUBLISH_STAGING}" "${RV_PUBLISH_FINAL}"
    RESULT_VARIABLE _rvp_result
    OUTPUT_QUIET ERROR_QUIET
  )
  IF(_rvp_result EQUAL 0)
    BREAK()
  ENDIF()
  EXECUTE_PROCESS(COMMAND ${CMAKE_COMMAND} -E sleep 1)
ENDFOREACH()

IF(NOT _rvp_result EQUAL 0)
  FILE(LOCK "${_rvp_entry}.lock" RELEASE)
  MESSAGE(FATAL_ERROR "rv_store_publish: could not move '${RV_PUBLISH_STAGING}' to '${RV_PUBLISH_FINAL}' (exit ${_rvp_result})")
ENDIF()

FILE(
  WRITE "${_rvp_marker}"
  ""
)
FILE(LOCK "${_rvp_entry}.lock" RELEASE)
MESSAGE(STATUS "Dependency store: published '${RV_PUBLISH_FINAL}'")
