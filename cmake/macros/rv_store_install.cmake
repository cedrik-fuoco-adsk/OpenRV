# *****************************************************************************
# Copyright 2026 Autodesk, Inc. All rights reserved.
#
# SPDX-License-Identifier: Apache-2.0
#
# *****************************************************************************

#
# Install a stored dependency into a staging tree and publish it. Run as a CMake script:
#
# cmake -DRV_INSTALL_BUILD=<build dir> -DRV_INSTALL_PREFIX=<entry install dir> \ -DRV_INSTALL_CONFIG=<config> -DRV_INSTALL_STAGING_ROOT=<entry .publishing> \
# -DRV_INSTALL_SUFFIX=<target>/install -P rv_store_install.cmake
#
# Both halves are one command on purpose. They were previously two commands in an ExternalProject INSTALL_COMMAND, separated by `COMMAND` after a `cmake -E env
# DESTDIR=...` prefix -- and `-E env` does not treat `COMMAND` as a separator, so the publish half silently never ran while the install half succeeded. The
# entry was then left half-written and `.publishing` left behind, and the step reported success.
#
# The install is staged with DESTDIR rather than with a staging install prefix, so the prefix stays where the tree will actually live and anything the
# dependency bakes into its installed files names the real place.
#

FOREACH(
  _rvsi_required
  RV_INSTALL_BUILD RV_INSTALL_PREFIX RV_INSTALL_STAGING_ROOT RV_INSTALL_SUFFIX
)
  IF(NOT ${_rvsi_required})
    MESSAGE(FATAL_ERROR "rv_store_install: ${_rvsi_required} is required")
  ENDIF()
ENDFOREACH()

FILE(MAKE_DIRECTORY "${RV_INSTALL_STAGING_ROOT}")

# DESTDIR is set for the install subprocess only, and prepends the staging root to whatever the install writes, leaving the configured prefix intact inside the
# staged tree.
SET(ENV{DESTDIR}
    "${RV_INSTALL_STAGING_ROOT}"
)
EXECUTE_PROCESS(
  COMMAND ${CMAKE_COMMAND} --install "${RV_INSTALL_BUILD}" --prefix "${RV_INSTALL_PREFIX}" --config "${RV_INSTALL_CONFIG}"
  RESULT_VARIABLE _rvsi_result
)
IF(_rvsi_result)
  MESSAGE(FATAL_ERROR "rv_store_install: the install failed (exit ${_rvsi_result}), so nothing was published")
ENDIF()

# Publishing is handed to its own script, which finds the staged tree rather than recomputing a path: CMake folds a drive letter into the DESTDIR path in a way
# that does not match the obvious spellings, and a wrong guess there publishes nothing while looking like it worked.
EXECUTE_PROCESS(
  COMMAND ${CMAKE_COMMAND} -DRV_PUBLISH_ROOT=${RV_INSTALL_STAGING_ROOT} -DRV_PUBLISH_SUFFIX=${RV_INSTALL_SUFFIX} -DRV_PUBLISH_FINAL=${RV_INSTALL_PREFIX} -P
          "${CMAKE_CURRENT_LIST_DIR}/rv_store_publish.cmake"
  RESULT_VARIABLE _rvsi_publish
)
IF(_rvsi_publish)
  MESSAGE(FATAL_ERROR "rv_store_install: publishing failed (exit ${_rvsi_publish})")
ENDIF()
