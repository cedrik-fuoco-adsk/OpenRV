#
# Copyright (C) 2026  Autodesk, Inc. All Rights Reserved.
#
# SPDX-License-Identifier: Apache-2.0
#

#
# rv_build_manifest.cmake
#
# Writes the build manifest: one file that answers "what is this build made of?" from the identity, the resolved Conan package set, and the facts probed from
# the prebuilt artifacts consumed.
#
# Assembly is delegated to src/build/build_manifest.py because a write failure must be a warning rather than a fatal error, which CMake's file(WRITE) cannot
# express, and because JSON escaping is trivial there and error-prone here.
#
# Note on FUNCTION versus MACRO: RV_WRITE_BUILD_MANIFEST is a FUNCTION because it returns early. A RETURN() inside a MACRO returns from the caller's file, which
# would silently abandon the rest of CMakeLists.txt.
#
# Requirements it satisfies, from specs/build-manifest: - A manifest is written for every configured build - Manifest content - Manifest reference format
# (content-derived) - Manifest writing does not fail a build - Manifest is deterministic for the same inputs - Manifest does not embed credentials
#

SET(RV_BUILD_MANIFEST_SCRIPT
    "${PROJECT_SOURCE_DIR}/src/build/build_manifest.py"
    CACHE INTERNAL "Path to the build manifest assembler"
)

SET(RV_BUILD_MANIFEST_FILE
    "${CMAKE_BINARY_DIR}/build-manifest.json"
    CACHE INTERNAL "Build manifest"
)

#
# RV_WRITE_BUILD_MANIFEST()
#
# Write the manifest. A default build warns and continues if it cannot be written; a configuration that requires an identity (the store) fails instead.
#
FUNCTION(RV_WRITE_BUILD_MANIFEST)
  IF(NOT RV_BUILD_MANIFEST)
    RETURN()
  ENDIF()

  IF(NOT RV_BUILD_PYTHON)
    MESSAGE(WARNING "Build manifest: no Python 3 interpreter found, so no manifest was written.")
    RETURN()
  ENDIF()

  IF(NOT EXISTS "${RV_BUILD_MANIFEST_SCRIPT}")
    MESSAGE(WARNING "Build manifest: ${RV_BUILD_MANIFEST_SCRIPT} not found, so no manifest was written.")
    RETURN()
  ENDIF()

  # Artifacts are probed first: the manifest records their facts.
  RV_RUN_ARTIFACT_PROBES(_rvbm_probes)

  SET(_rvbm_args
      --identity "${RV_BUILD_IDENTITY_FILE}" --out "${RV_BUILD_MANIFEST_FILE}"
  )
  IF(_rvbm_probes)
    LIST(APPEND _rvbm_args --probes "${_rvbm_probes}")
  ENDIF()
  IF(RV_CONAN_IDENTITY_FILE)
    LIST(APPEND _rvbm_args --conan-identity "${RV_CONAN_IDENTITY_FILE}")
  ENDIF()
  IF(RV_CONAN_PACKAGES_FILE)
    LIST(APPEND _rvbm_args --conan-packages "${RV_CONAN_PACKAGES_FILE}")
  ENDIF()

  # The store cannot proceed without a manifest, because the store is keyed by the identity the manifest records.
  IF(RV_DEPS_STORE)
    LIST(APPEND _rvbm_args --require-identity)
  ENDIF()

  EXECUTE_PROCESS(
    COMMAND "${RV_BUILD_PYTHON}" "${RV_BUILD_MANIFEST_SCRIPT}" ${_rvbm_args}
    RESULT_VARIABLE _rvbm_result
    OUTPUT_VARIABLE _rvbm_stdout
    ERROR_VARIABLE _rvbm_stderr
  )

  IF(_rvbm_result EQUAL 0)
    IF(EXISTS "${RV_BUILD_MANIFEST_FILE}")
      MESSAGE(STATUS "Build manifest: ${RV_BUILD_MANIFEST_FILE}")
    ENDIF()
  ELSEIF(_rvbm_result EQUAL 3)
    MESSAGE(FATAL_ERROR "Build manifest: ${_rvbm_stderr}")
  ELSE()
    # A manifest that cannot be written must not fail a build.
    MESSAGE(WARNING "Build manifest: could not be written (exit ${_rvbm_result}). ${_rvbm_stderr}")
  ENDIF()
ENDFUNCTION()
