# *****************************************************************************
# Copyright 2026 Autodesk, Inc. All rights reserved.
#
# SPDX-License-Identifier: Apache-2.0
#
# *****************************************************************************

#
# Install a stored dependency into a private staging tree and publish it. Run as a CMake script:
#
# cmake -DRV_INSTALL_BUILD=<build dir> -DRV_INSTALL_PREFIX=<entry install dir> -DRV_INSTALL_CONFIG=<config> -DRV_INSTALL_STORE=<store root> \
# -DRV_INSTALL_TAG=<build tag> [-DRV_INSTALL_FIXUP=<script>] -P rv_store_install.cmake
#
# Both halves are one command on purpose. They were previously two commands in an ExternalProject INSTALL_COMMAND, separated by `COMMAND` after a `cmake -E env
# DESTDIR=...` prefix -- and `-E env` does not treat `COMMAND` as a separator, so the publish half silently never ran while the install half succeeded.
#
# The install is staged with DESTDIR rather than with a staging install prefix, so the prefix stays where the tree will actually live and anything the
# dependency bakes into its installed files names the real place.
#
# Every install stages into a directory of its own, <store>/.staging/<tag>-<random>, held under a lock for as long as this script runs. Two build directories
# installing the same dependency at once therefore never write into the same tree, and a staging directory left by an install that was killed -- whose lock the
# operating system has released -- is recognized and removed by the next install, while one that is still being written is left alone.
#

FOREACH(
  _rvsi_required
  RV_INSTALL_BUILD RV_INSTALL_PREFIX RV_INSTALL_CONFIG RV_INSTALL_STORE RV_INSTALL_TAG
)
  IF(NOT ${_rvsi_required})
    MESSAGE(FATAL_ERROR "rv_store_install: ${_rvsi_required} is required")
  ENDIF()
ENDFOREACH()

SET(_rvsi_staging_parent
    "${RV_INSTALL_STORE}/.staging"
)
FILE(MAKE_DIRECTORY "${_rvsi_staging_parent}")

# Staging directories whose lock can be taken belong to no running install, so they are leftovers of an interrupted one.
FILE(GLOB _rvsi_locks "${_rvsi_staging_parent}/*.lock")
FOREACH(
  _rvsi_lock
  ${_rvsi_locks}
)
  FILE(
    LOCK "${_rvsi_lock}"
    GUARD PROCESS
    TIMEOUT 0
    RESULT_VARIABLE _rvsi_lock_result
  )
  IF(_rvsi_lock_result EQUAL 0)
    STRING(
      REGEX
      REPLACE "\\.lock$" "" _rvsi_leftover "${_rvsi_lock}"
    )
    FILE(REMOVE_RECURSE "${_rvsi_leftover}")
    FILE(LOCK "${_rvsi_lock}" RELEASE)
    # Best effort: on Windows another install may have the file open to try the same thing, and the lock file costs nothing to leave.
    EXECUTE_PROCESS(
      COMMAND ${CMAKE_COMMAND} -E rm -f "${_rvsi_lock}"
      RESULT_VARIABLE _rvsi_ignored
      OUTPUT_QUIET ERROR_QUIET
    )
  ENDIF()
ENDFOREACH()

STRING(
  RANDOM
  LENGTH 8
  ALPHABET "0123456789abcdef" _rvsi_random
)
SET(_rvsi_name
    "${RV_INSTALL_TAG}-${_rvsi_random}"
)
SET(_rvsi_root
    "${_rvsi_staging_parent}/${_rvsi_name}"
)
FILE(
  LOCK "${_rvsi_root}.lock"
  GUARD PROCESS
  TIMEOUT 0
  RESULT_VARIABLE _rvsi_lock_result
)
IF(NOT _rvsi_lock_result EQUAL 0
   OR EXISTS "${_rvsi_root}"
)
  MESSAGE(FATAL_ERROR "rv_store_install: could not claim the staging directory '${_rvsi_root}' (${_rvsi_lock_result})")
ENDIF()
FILE(MAKE_DIRECTORY "${_rvsi_root}")

# DESTDIR is set for the install subprocess only, and prepends the staging root to whatever the install writes, leaving the configured prefix intact inside the
# staged tree.
SET(ENV{DESTDIR}
    "${_rvsi_root}"
)
EXECUTE_PROCESS(
  COMMAND ${CMAKE_COMMAND} --install "${RV_INSTALL_BUILD}" --prefix "${RV_INSTALL_PREFIX}" --config "${RV_INSTALL_CONFIG}"
  RESULT_VARIABLE _rvsi_result
)
UNSET(ENV{DESTDIR})
IF(_rvsi_result)
  FILE(REMOVE_RECURSE "${_rvsi_root}")
  MESSAGE(FATAL_ERROR "rv_store_install: the install failed (exit ${_rvsi_result}), so nothing was published")
ENDIF()

# Where DESTDIR put the tree. CMake's install script drops a Windows drive letter and its colon before prepending DESTDIR -- C:/store/... is staged at
# <DESTDIR>/store/... -- and leaves any other absolute path as it is. The staging directory is private to this install, so if that rule ever differs the tree is
# looked for under it, where nothing but this install can be.
FILE(TO_CMAKE_PATH "${RV_INSTALL_PREFIX}" _rvsi_prefix)
STRING(
  REGEX
  REPLACE "^[A-Za-z]:" "" _rvsi_relative "${_rvsi_prefix}"
)
SET(_rvsi_staged
    "${_rvsi_root}${_rvsi_relative}"
)
IF(NOT IS_DIRECTORY "${_rvsi_staged}")
  GET_FILENAME_COMPONENT(_rvsi_recipe_dir "${_rvsi_prefix}" DIRECTORY)
  GET_FILENAME_COMPONENT(_rvsi_recipe "${_rvsi_recipe_dir}" NAME)
  FILE(
    GLOB_RECURSE _rvsi_candidates
    LIST_DIRECTORIES TRUE
    "${_rvsi_root}/*"
  )
  SET(_rvsi_staged
      ""
  )
  FOREACH(
    _rvsi_candidate
    ${_rvsi_candidates}
  )
    IF(IS_DIRECTORY "${_rvsi_candidate}"
       AND _rvsi_candidate MATCHES "/${_rvsi_recipe}/install$"
    )
      SET(_rvsi_staged
          "${_rvsi_candidate}"
      )
    ENDIF()
  ENDFOREACH()
  IF(NOT _rvsi_staged)
    FILE(REMOVE_RECURSE "${_rvsi_root}")
    MESSAGE(FATAL_ERROR "rv_store_install: the install wrote nothing under '${_rvsi_root}' for '${RV_INSTALL_PREFIX}'")
  ENDIF()
ENDIF()

# pkg-config files name the absolute install prefix, which is the store entry. Rewritten relative to the file itself, which pkg-config and pkgconf both support,
# so the entry still describes itself correctly if the store is moved and the relocation check finds no reference to where it was installed.
#
# The dependency may have written the prefix in another spelling than the one it was given: on Windows a store under %TEMP% is often an 8.3 short path
# (C:/Users/RUNNER~1/...) that CMake expands to the long one when it records CMAKE_INSTALL_PREFIX. Both spellings are rewritten, the long one derived from the
# store root, which exists, because the entry itself does not yet.
SET(_rvsi_prefix_spellings
    "${_rvsi_prefix}"
)
FILE(TO_CMAKE_PATH "${RV_INSTALL_STORE}" _rvsi_store)
FILE(REAL_PATH "${_rvsi_store}" _rvsi_store_real)
STRING(FIND "${_rvsi_prefix}" "${_rvsi_store}" _rvsi_store_at)
IF(_rvsi_store_at EQUAL 0
   AND NOT _rvsi_store_real STREQUAL _rvsi_store
)
  STRING(LENGTH "${_rvsi_store}" _rvsi_store_length)
  STRING(SUBSTRING "${_rvsi_prefix}" ${_rvsi_store_length} -1 _rvsi_prefix_tail)
  LIST(APPEND _rvsi_prefix_spellings "${_rvsi_store_real}${_rvsi_prefix_tail}")
ENDIF()
FILE(GLOB _rvsi_pc_files "${_rvsi_staged}/lib/pkgconfig/*.pc" "${_rvsi_staged}/lib64/pkgconfig/*.pc" "${_rvsi_staged}/share/pkgconfig/*.pc")
FOREACH(
  _rvsi_pc
  ${_rvsi_pc_files}
)
  FILE(READ "${_rvsi_pc}" _rvsi_pc_body)
  GET_FILENAME_COMPONENT(_rvsi_pc_dir "${_rvsi_pc}" DIRECTORY)
  FILE(RELATIVE_PATH _rvsi_pc_up "${_rvsi_pc_dir}" "${_rvsi_staged}")
  FOREACH(
    _rvsi_spelling
    ${_rvsi_prefix_spellings}
  )
    STRING(REPLACE "${_rvsi_spelling}" "\${pcfiledir}/${_rvsi_pc_up}" _rvsi_pc_body "${_rvsi_pc_body}")
  ENDFOREACH()
  FILE(
    WRITE "${_rvsi_pc}"
    "${_rvsi_pc_body}"
  )
ENDFOREACH()

# What the dependency adjusts after installing, applied to the staged tree because a published entry is shared and never modified in place.
IF(RV_INSTALL_FIXUP
   AND EXISTS "${RV_INSTALL_FIXUP}"
)
  SET(RV_STAGED_INSTALL
      "${_rvsi_staged}"
  )
  INCLUDE("${RV_INSTALL_FIXUP}")
ENDIF()

EXECUTE_PROCESS(
  COMMAND ${CMAKE_COMMAND} -DRV_PUBLISH_STAGING=${_rvsi_staged} -DRV_PUBLISH_FINAL=${_rvsi_prefix} -P "${CMAKE_CURRENT_LIST_DIR}/rv_store_publish.cmake"
  RESULT_VARIABLE _rvsi_publish
)
FILE(REMOVE_RECURSE "${_rvsi_root}")
FILE(LOCK "${_rvsi_root}.lock" RELEASE)
EXECUTE_PROCESS(
  COMMAND ${CMAKE_COMMAND} -E rm -f "${_rvsi_root}.lock"
  RESULT_VARIABLE _rvsi_ignored
  OUTPUT_QUIET ERROR_QUIET
)
IF(_rvsi_publish)
  MESSAGE(FATAL_ERROR "rv_store_install: publishing failed (exit ${_rvsi_publish})")
ENDIF()
