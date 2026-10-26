#
# Copyright (C) 2026  Autodesk, Inc. All Rights Reserved.
#
# SPDX-License-Identifier: Apache-2.0
#

#
# rv_probe_artifact.cmake
#
# Registers the prebuilt artifacts a configuration consumes, and runs the probe over them.
#
# Probing is off by default (RV_DEPS_PROBE_ARTIFACTS), because inspecting binaries on every configure is a slowdown no default build should pay. A configuration
# with a store probes regardless, because a store entry must be verified before it is used.
#
# Only prebuilt artifacts are registered. A dependency built from source is described by its build recipe and probing it would slow every configure for no
# benefit; the artifacts worth recording are the ones the build did not produce, because those are the ones whose ABI the build is trusting.
#
# The probe runs once per configuration over every registered artifact, and its results are cached by artifact content, so the cost of inspecting an artifact is
# paid once per distinct artifact rather than once per configure.
#
# Note on FUNCTION versus MACRO: everything that can return early is a FUNCTION. A RETURN() inside a MACRO returns from the caller's file, which would silently
# abandon the rest of the file that called it.
#
# Requirements it satisfies, from specs/dependency-abi-probe: - Facts are read from the artifact - Input and derived artifacts are probed separately - Probe
# results are cached by artifact content - Probing does not modify the artifact - Probing is not required for a default build
#

SET(RV_PROBE_ARTIFACT_SCRIPT
    "${PROJECT_SOURCE_DIR}/src/build/probe_artifact.py"
    CACHE INTERNAL "Path to the artifact probe"
)

SET(RV_PROBE_CACHE_DIR
    "${CMAKE_BINARY_DIR}/rv-probe-cache"
    CACHE INTERNAL "Cache of probe results, keyed by artifact content"
)

# Properties start unset. DEFINE_PROPERTY is used only to document them: an empty INITIALIZE value is rejected, and an unset global property reads as empty.
DEFINE_PROPERTY(
  GLOBAL
  PROPERTY RV_PREBUILT_ARTIFACTS
  BRIEF_DOCS "Registered prebuilt artifacts, as role|path|metadata_root"
)
DEFINE_PROPERTY(
  GLOBAL
  PROPERTY RV_PREBUILT_ARTIFACT_PATHS
  BRIEF_DOCS "Registered prebuilt artifact paths, for deduplication"
)

#
# RV_DEPS_PROBE_IS_ENABLED(<out_var>)
#
# Must remain a MACRO: it sets a variable in the caller's scope.
#
MACRO(RV_DEPS_PROBE_IS_ENABLED _rdpie_out)
  IF(RV_DEPS_PROBE_ARTIFACTS
     OR RV_DEPS_STORE
  )
    SET(${_rdpie_out}
        TRUE
    )
  ELSE()
    SET(${_rdpie_out}
        FALSE
    )
  ENDIF()
ENDMACRO()

#
# RV_REGISTER_PREBUILT_ARTIFACT(<role> <path> [METADATA_ROOT <dir>])
#
# Record one prebuilt artifact for probing. <role> is "input" for an artifact the build ingested, or "derived" for one the build produced by adapting an input;
# keeping them separate is what lets an adaptation that changes a fact be seen. METADATA_ROOT applies to this artifact alone.
#
FUNCTION(RV_REGISTER_PREBUILT_ARTIFACT _rrpa_role _rrpa_path)
  CMAKE_PARSE_ARGUMENTS(_RRPA "" "" "METADATA_ROOT" ${ARGN})

  RV_DEPS_PROBE_IS_ENABLED(_rrpa_enabled)
  IF(NOT _rrpa_enabled)
    RETURN()
  ENDIF()

  IF(NOT _rrpa_path
     OR NOT EXISTS "${_rrpa_path}"
  )
    RETURN()
  ENDIF()

  GET_PROPERTY(
    _rrpa_paths GLOBAL
    PROPERTY RV_PREBUILT_ARTIFACT_PATHS
  )
  IF("${_rrpa_path}" IN_LIST _rrpa_paths)
    RETURN()
  ENDIF()
  SET_PROPERTY(
    GLOBAL APPEND
    PROPERTY RV_PREBUILT_ARTIFACT_PATHS "${_rrpa_path}"
  )

  # "|" separates the fields because it cannot appear in a Windows path.
  SET_PROPERTY(
    GLOBAL APPEND
    PROPERTY RV_PREBUILT_ARTIFACTS "${_rrpa_role}|${_rrpa_path}|${_RRPA_METADATA_ROOT}"
  )
ENDFUNCTION()

#
# RV_REGISTER_PREBUILT_TARGET(<target>)
#
# Register a found dependency target. Its imported location is resolved now, because a target with no location is not an artifact and there is nothing to probe.
#
FUNCTION(RV_REGISTER_PREBUILT_TARGET _rrpt_target)
  RV_DEPS_PROBE_IS_ENABLED(_rrpt_enabled)
  IF(NOT _rrpt_enabled)
    RETURN()
  ENDIF()
  IF(NOT TARGET ${_rrpt_target})
    RETURN()
  ENDIF()

  RV_RESOLVE_IMPORTED_LOCATION(${_rrpt_target} _rrpt_location)
  IF(_rrpt_location
     AND EXISTS "${_rrpt_location}"
  )
    # RV_RESOLVE_IMPORTED_LOCATION is a MACRO, so it wrote _rrpt_location into this function's scope.
    RV_REGISTER_PREBUILT_ARTIFACT(input "${_rrpt_location}")
  ENDIF()
ENDFUNCTION()

#
# RV_DEPS_PROBE_IS_STRICT(<out_var>)
#
# Strict probing fails naming the missing inspection tool instead of recording the fact as unknown. The store requires it, because a store entry whose facts
# cannot be verified must not be used. A default build does not, so that a machine without readelf/otool/dumpbin still builds.
#
# Must remain a MACRO: it sets a variable in the caller's scope.
#
MACRO(RV_DEPS_PROBE_IS_STRICT _rrpis_out)
  IF(RV_DEPS_PROBE_STRICT
     OR RV_DEPS_STORE
  )
    SET(${_rrpis_out}
        TRUE
    )
  ELSE()
    SET(${_rrpis_out}
        FALSE
    )
  ENDIF()
ENDMACRO()

#
# RV_RUN_ARTIFACT_PROBES(<out_var>)
#
# Probe every registered artifact. Sets <out_var> to the provision document, or to "" when there was nothing to probe or probing could not run.
#
FUNCTION(RV_RUN_ARTIFACT_PROBES _rrap_out)
  SET(${_rrap_out}
      ""
      PARENT_SCOPE
  )

  RV_DEPS_PROBE_IS_ENABLED(_rrap_enabled)
  IF(NOT _rrap_enabled)
    RETURN()
  ENDIF()

  GET_PROPERTY(
    _rrap_entries GLOBAL
    PROPERTY RV_PREBUILT_ARTIFACTS
  )
  IF(NOT _rrap_entries)
    MESSAGE(STATUS "Artifact probing: no prebuilt artifacts were consumed by this configuration")
    RETURN()
  ENDIF()

  IF(NOT RV_BUILD_PYTHON)
    MESSAGE(WARNING "Artifact probing: no Python 3 interpreter found, so prebuilt artifacts were not probed.")
    RETURN()
  ENDIF()

  RV_DEPS_PROBE_IS_STRICT(_rrap_strict)

  SET(_rrap_document
      "${CMAKE_BINARY_DIR}/artifact-probes.json"
  )
  SET(_rrap_args
      probe
  )
  FOREACH(
    _rrap_entry
    ${_rrap_entries}
  )
    STRING(REPLACE "|" ";" _rrap_parts "${_rrap_entry}")
    LIST(GET _rrap_parts 0 _rrap_role)
    LIST(GET _rrap_parts 1 _rrap_path)
    LIST(GET _rrap_parts 2 _rrap_root)
    LIST(APPEND _rrap_args "--artifact" "${_rrap_role}=${_rrap_path}")
    # Keyed by the artifact, not the role: Qt's root carries Qt's version and features, and every other input artifact would otherwise be recorded with them.
    IF(_rrap_root)
      LIST(APPEND _rrap_args "--artifact-metadata-root" "${_rrap_path}" "${_rrap_root}")
    ENDIF()
  ENDFOREACH()
  LIST(APPEND _rrap_args "--cache-dir" "${RV_PROBE_CACHE_DIR}" "--out" "${_rrap_document}")
  IF(_rrap_strict)
    LIST(APPEND _rrap_args "--strict")
  ENDIF()

  EXECUTE_PROCESS(
    COMMAND "${RV_BUILD_PYTHON}" "${RV_PROBE_ARTIFACT_SCRIPT}" ${_rrap_args}
    RESULT_VARIABLE _rrap_result
    OUTPUT_VARIABLE _rrap_stdout
    ERROR_VARIABLE _rrap_stderr
  )

  IF(_rrap_result EQUAL 0)
    MESSAGE(STATUS "Artifact probing: recorded facts for the prebuilt artifacts this configuration consumed")
    SET(${_rrap_out}
        "${_rrap_document}"
        PARENT_SCOPE
    )
  ELSEIF(_rrap_strict)
    # The store path cannot tolerate an unverified artifact, so this is fatal here. The message carries the missing tool's name.
    MESSAGE(FATAL_ERROR "Artifact probing failed, and this configuration requires verified artifacts: ${_rrap_stderr}")
  ELSE()
    # A default build must not fail because an inspection tool is missing.
    MESSAGE(WARNING "Artifact probing: could not probe prebuilt artifacts (exit ${_rrap_result}). ${_rrap_stderr}")
  ENDIF()
ENDFUNCTION()
