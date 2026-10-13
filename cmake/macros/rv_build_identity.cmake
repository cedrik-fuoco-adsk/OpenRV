#
# Copyright (C) 2026  Autodesk, Inc. All Rights Reserved.
#
# SPDX-License-Identifier: Apache-2.0
#

#
# rv_build_identity.cmake
#
# Computes the build identity: a single authoritative description of the platform this build targets. It exists so that the CMake dependency resolution path and
# the Conan profile derive their values from one computation instead of each normalizing on its own -- a Conan profile that says compiler.version=11 while the
# host compiler is 13 is drift that should be reported, not discovered later as a link error.
#
# The normalization rules live in src/build/build_identity.py, which both this module and the Conan generate step invoke. Keeping the rules in one place is the
# point: two independent normalizations would reintroduce exactly the drift this is meant to remove.
#
# This module is read-only. It records and reports; it reroutes nothing.
#
# Note on FUNCTION versus MACRO: everything that can return early is a FUNCTION. A RETURN() inside a MACRO returns from the caller's file, which would silently
# abandon the rest of CMakeLists.txt; a RETURN() inside a FUNCTION returns only from the function.
#
# Requirements it satisfies, from specs/build-identity: - Identity is computed once per configuration - Identity content - Build configuration is part of
# identity - Python identity is ABI-granular - Identity is reported to the user - Identity computation does not change build behaviour - Identity computation
# requires no external tool
#

SET(RV_BUILD_IDENTITY_SCRIPT
    "${PROJECT_SOURCE_DIR}/src/build/build_identity.py"
    CACHE INTERNAL "Path to the shared build identity computation"
)

# Output fields, in report order. Kept in sync with OUTPUT_FIELDS in build_identity.py.
#
# `crt` is Windows only, and is absent from the identity elsewhere rather than set to a placeholder: there is no correct value to invent on a platform without
# that axis, and an invented one would read as a fact.
SET(RV_BUILD_IDENTITY_FIELDS
    "vfx_platform;target_os;target_arch;compiler_id;compiler_version;stdlib;crt;cxx_standard;build_config;python_abi;qt_version"
    CACHE INTERNAL "Fields carried by the build identity"
)

#
# The Python 3 interpreter used by the identity computation, the artifact probe and the manifest assembler.
#
# Deliberately discovered with find_program under a project-specific name rather than find_package(Python3). FindPython writes Python3_* cache variables into
# the top-level build tree, and this project has been bitten by exactly that: OIIO forces -DPython3_ROOT_DIR because "OIIO 3.x still calls find_package(Python3)
# ... to prevent finding the system Python (e.g. 3.14 from GitHub runner toolcache)", and OCIO mirrors the Python3_ variables for the same reason. Computing an
# identity must not change which Python anything else finds, so it does not go near FindPython.
#
# A Python 3 interpreter is already a prerequisite of this build (requirements.txt, rvsetup, and every src/build script). It is not an inspection tool: no
# readelf, otool or dumpbin is needed to compute an identity.
#
SET(RV_BUILD_PYTHON
    ""
    CACHE STRING "Python 3 interpreter used for the build identity, artifact probing and the build manifest (default: the first python3 on PATH)"
)

#
# A candidate is accepted only if it runs as Python 3. On Windows, PATH often contains App Execution Aliases (WindowsApps/python3.exe and python.exe) that are
# stubs which open the Store rather than running Python, and find_program cannot tell the difference. Accepting one would leave every later script invocation
# failing in a way that looks unrelated.
#
FUNCTION(RV_BUILD_PYTHON_RUNS _rbpr_candidate _rbpr_out)
  EXECUTE_PROCESS(
    COMMAND "${_rbpr_candidate}" -c "import sys; sys.exit(0 if sys.version_info[0] == 3 else 1)"
    RESULT_VARIABLE _rbpr_result
    OUTPUT_QUIET ERROR_QUIET
  )
  IF(_rbpr_result EQUAL 0)
    SET(${_rbpr_out}
        TRUE
        PARENT_SCOPE
    )
  ELSE()
    SET(${_rbpr_out}
        FALSE
        PARENT_SCOPE
    )
  ENDIF()
ENDFUNCTION()

#
# Find the first interpreter on PATH that runs, trying python3 then python in each directory before moving to the next. A python.org install on Windows provides
# python.exe but no python3.exe, so a search that tries python3 across the whole PATH first finds the WindowsApps stub and never reaches the real python.exe.
#
FUNCTION(RV_BUILD_PYTHON_SEARCH_PATH _rbpsp_out)
  SET(${_rbpsp_out}
      ""
      PARENT_SCOPE
  )
  IF(WIN32)
    SET(_rbpsp_names
        python3.exe python.exe
    )
  ELSE()
    SET(_rbpsp_names
        python3 python
    )
  ENDIF()
  FILE(TO_CMAKE_PATH "$ENV{PATH}" _rbpsp_directories)
  FOREACH(
    _rbpsp_directory
    ${_rbpsp_directories}
  )
    FOREACH(
      _rbpsp_name
      ${_rbpsp_names}
    )
      SET(_rbpsp_candidate
          "${_rbpsp_directory}/${_rbpsp_name}"
      )
      IF(EXISTS "${_rbpsp_candidate}"
         AND NOT IS_DIRECTORY "${_rbpsp_candidate}"
      )
        RV_BUILD_PYTHON_RUNS("${_rbpsp_candidate}" _rbpsp_runs)
        IF(_rbpsp_runs)
          SET(${_rbpsp_out}
              "${_rbpsp_candidate}"
              PARENT_SCOPE
          )
          RETURN()
        ENDIF()
      ENDIF()
    ENDFOREACH()
  ENDFOREACH()
ENDFUNCTION()

IF(RV_BUILD_PYTHON)
  # An interpreter given explicitly is validated but never replaced: the caller asked for that one.
  RV_BUILD_PYTHON_RUNS("${RV_BUILD_PYTHON}" _rvbp_runs)
  IF(NOT _rvbp_runs)
    MESSAGE(
      WARNING
        "Build identity: '${RV_BUILD_PYTHON}' does not run as a Python 3 interpreter, so it will not be used. Set -DRV_BUILD_PYTHON=<path> to provide one."
    )
    SET(RV_BUILD_PYTHON
        ""
        CACHE STRING "Python 3 interpreter used for the build identity, artifact probing and the build manifest (default: the first python3 on PATH)" FORCE
    )
  ENDIF()
ELSE()
  FIND_PROGRAM(
    RV_BUILD_PYTHON_DISCOVERED
    NAMES python3 python NAMES_PER_DIR
  )
  SET(_rvbp_found
      ""
  )
  IF(RV_BUILD_PYTHON_DISCOVERED)
    RV_BUILD_PYTHON_RUNS("${RV_BUILD_PYTHON_DISCOVERED}" _rvbp_runs)
    IF(_rvbp_runs)
      SET(_rvbp_found
          "${RV_BUILD_PYTHON_DISCOVERED}"
      )
    ENDIF()
  ENDIF()
  IF(NOT _rvbp_found)
    # The first match does not run -- typically a WindowsApps stub ahead of the real interpreter on PATH -- so keep looking rather than giving up on the first.
    RV_BUILD_PYTHON_SEARCH_PATH(_rvbp_found)
  ENDIF()
  IF(_rvbp_found)
    SET(RV_BUILD_PYTHON
        "${_rvbp_found}"
        CACHE STRING "Python 3 interpreter used for the build identity, artifact probing and the build manifest (default: the first python3 on PATH)" FORCE
    )
  ELSEIF(RV_BUILD_PYTHON_DISCOVERED)
    MESSAGE(
      WARNING
        "Build identity: '${RV_BUILD_PYTHON_DISCOVERED}' does not run as a Python 3 interpreter and no other on PATH does, so none will be used. Set -DRV_BUILD_PYTHON=<path> to provide one."
    )
  ENDIF()
ENDIF()

#
# Default the Conan document paths to where Conan's generate step writes them.
#
# The Conan toolchain passes these as cache variables, but only for the generators where CMakeToolchain writes cache variables into conan_toolchain.cmake. With
# a multi-config generator such as Visual Studio they are written to CMakePresets.json instead, which a configure driven by -DCMAKE_TOOLCHAIN_FILE never reads
# -- so on Windows the paths would silently never arrive and the Conan section of the manifest would be empty with no indication why.
#
# Conan writes the documents into the CMake binary directory on every generator, so that is the default here, and a cache variable remains an override for any
# layout that differs.
#
IF(NOT RV_CONAN_IDENTITY_FILE
   AND EXISTS "${CMAKE_BINARY_DIR}/conan-identity.json"
)
  SET(RV_CONAN_IDENTITY_FILE
      "${CMAKE_BINARY_DIR}/conan-identity.json"
      CACHE STRING "Conan profile identity document, as written by the Conan generate step"
  )
ENDIF()
IF(NOT RV_CONAN_PACKAGES_FILE
   AND EXISTS "${CMAKE_BINARY_DIR}/conan-packages.json"
)
  SET(RV_CONAN_PACKAGES_FILE
      "${CMAKE_BINARY_DIR}/conan-packages.json"
      CACHE STRING "Conan resolved package set, as written by the Conan generate step"
  )
ENDIF()

#
# Map the CMake target detection onto the identity's target OS.
#
MACRO(RV_BUILD_IDENTITY_TARGET_OS _rbbi_out)
  IF(RV_TARGET_DARWIN)
    SET(${_rbbi_out}
        "macos"
    )
  ELSEIF(RV_TARGET_LINUX)
    SET(${_rbbi_out}
        "linux"
    )
  ELSEIF(RV_TARGET_WINDOWS)
    SET(${_rbbi_out}
        "windows"
    )
  ELSE()
    SET(${_rbbi_out}
        ""
    )
  ENDIF()
ENDMACRO()

#
# Map the compiler and target onto the standard library the build links against. RV sets no -stdlib override for Clang on Linux or Windows, so the platform
# default applies.
#
MACRO(RV_BUILD_IDENTITY_STDLIB _rbbi_out)
  IF(MSVC)
    SET(${_rbbi_out}
        "msvc"
    )
  ELSEIF(CMAKE_CXX_COMPILER_ID MATCHES "AppleClang")
    SET(${_rbbi_out}
        "libc++"
    )
  ELSE()
    # GNU, and Clang on Linux, both default to libstdc++.
    SET(${_rbbi_out}
        "libstdc++11"
    )
  ENDIF()
ENDMACRO()

#
# Resolve the C runtime library the build links against, as <kind>:<runtime type>.
#
# Windows only. On Linux and macOS the C runtime is not a separate ABI axis, so nothing is emitted and the field stays absent.
#
# The identity records the resolved runtime rather than the build configuration name, because the configuration name does not determine the runtime.
# CMAKE_MSVC_RUNTIME_LIBRARY selects /MD or /MT independently of the configuration, so without this a Release build against the static runtime would produce the
# same identity as one against the dynamic runtime and could be served the other's artifacts. Mixing the two is a link error at best and memory allocated in one
# heap and freed in another at worst, which is the failure this whole field exists to make impossible.
#
# Must remain a MACRO: it returns through the caller's argument, so a FUNCTION would set the variable in the wrong scope.
#
MACRO(RV_BUILD_IDENTITY_CRT _rbbi_out)
  SET(${_rbbi_out}
      ""
  )

  IF(MSVC)
    # The variable initializes the MSVC_RUNTIME_LIBRARY target property, and its own default is a generator expression. The identity is computed at configure
    # time, before generation, so the expression is resolved here for this configuration. CMake 3.27 is required by this project, so CMP0091 is NEW and the
    # variable is authoritative: no /MD or /MDd appears in the per-configuration flags.
    IF(CMAKE_MSVC_RUNTIME_LIBRARY)
      SET(_rbbi_crt_value
          "${CMAKE_MSVC_RUNTIME_LIBRARY}"
      )
    ELSE()
      SET(_rbbi_crt_value
          "MultiThreaded$<$<CONFIG:Debug>:Debug>DLL"
      )
    ENDIF()

    IF(CMAKE_BUILD_TYPE MATCHES "^[Dd]ebug$")
      STRING(REPLACE "$<$<CONFIG:Debug>:Debug>" "Debug" _rbbi_crt_value "${_rbbi_crt_value}")
    ELSE()
      STRING(REPLACE "$<$<CONFIG:Debug>:Debug>" "" _rbbi_crt_value "${_rbbi_crt_value}")
    ENDIF()

    IF(_rbbi_crt_value MATCHES "\\$<")
      # An expression this does not understand. Record what the build was told rather than resolving it wrongly: an unrecognized value is carried through
      # unchanged by the normalizer, so the identity still differs from a resolved one instead of silently matching it.
      MESSAGE(
        WARNING
          "Build identity: the C runtime library '${_rbbi_crt_value}' contains a generator expression that cannot be resolved at configure time, so it is recorded verbatim. This identity will not match a resolved one."
      )
      SET(${_rbbi_out}
          "${_rbbi_crt_value}"
      )
    ELSE()
      IF(_rbbi_crt_value MATCHES "Debug")
        SET(_rbbi_crt_type
            "Debug"
        )
      ELSE()
        SET(_rbbi_crt_type
            "Release"
        )
      ENDIF()
      IF(_rbbi_crt_value MATCHES "DLL$")
        SET(_rbbi_crt_kind
            "dynamic"
        )
      ELSE()
        SET(_rbbi_crt_kind
            "static"
        )
      ENDIF()
      SET(${_rbbi_out}
          "${_rbbi_crt_kind}:${_rbbi_crt_type}"
      )
    ENDIF()
  ENDIF()
ENDMACRO()

#
# RV_IDENTITY_GET(<field> <out_var>)
#
# Read one field back from the computed identity document. Values are read back from the canonical document rather than recomputed here, so the normalization
# rules have exactly one implementation.
#
# The document is read from disk rather than held in a cache variable, because a CMake cache variable cannot contain a newline and a JSON document does:
# assigning one to a cache variable silently truncates it at the first line.
#
# Must remain a MACRO: it sets a variable in the caller's scope.
#
MACRO(RV_IDENTITY_GET _rvig_field _rvig_out)
  SET(${_rvig_out}
      ""
  )
  IF(RV_BUILD_IDENTITY_AVAILABLE
     AND EXISTS "${RV_BUILD_IDENTITY_FILE}"
  )
    FILE(READ "${RV_BUILD_IDENTITY_FILE}" _rvig_document)
    STRING(
      JSON
      _rvig_value
      ERROR_VARIABLE
      _rvig_error
      GET
      "${_rvig_document}"
      "${_rvig_field}"
    )
    IF(NOT _rvig_error)
      SET(${_rvig_out}
          "${_rvig_value}"
      )
    ENDIF()
  ENDIF()
ENDMACRO()

#
# RV_BUILD_IDENTITY_COMPARE_WITH_CONAN()
#
# Report every field where the Conan profile disagrees with the computed identity. A Conan profile expresses only the compiler major, so versions are compared
# at major granularity: reporting drift that does not exist would make the report useless.
#
FUNCTION(RV_BUILD_IDENTITY_COMPARE_WITH_CONAN)
  IF(NOT RV_CONAN_IDENTITY_FILE
     OR NOT EXISTS "${RV_CONAN_IDENTITY_FILE}"
  )
    RETURN()
  ENDIF()

  EXECUTE_PROCESS(
    COMMAND "${RV_BUILD_PYTHON}" "${RV_BUILD_IDENTITY_SCRIPT}" compare --left "${RV_BUILD_IDENTITY_FILE}" --right "${RV_CONAN_IDENTITY_FILE}" --left-name
            "computed" --right-name "conan-profile"
    RESULT_VARIABLE _rbbi_compare_result
    OUTPUT_VARIABLE _rbbi_compare_stdout
    ERROR_VARIABLE _rbbi_compare_stderr
  )

  IF(_rbbi_compare_result EQUAL 0)
    MESSAGE(STATUS "Build identity: the Conan profile agrees with the computed identity")
  ELSEIF(_rbbi_compare_result EQUAL 2)
    # Reported, not enforced: making this a gate is a later phase.
    MESSAGE(WARNING "Build identity: the Conan profile disagrees with the computed identity (reported, not enforced):\n${_rbbi_compare_stdout}")
  ELSE()
    MESSAGE(WARNING "Build identity: could not compare the identity against the Conan profile (exit ${_rbbi_compare_result}). ${_rbbi_compare_stderr}")
  ENDIF()
ENDFUNCTION()

#
# RV_COMPUTE_BUILD_IDENTITY()
#
# Gather the raw facts, delegate normalization and hashing to build_identity.py, and record the result. Sets:
#
# RV_BUILD_IDENTITY_AVAILABLE   TRUE when an identity was computed RV_BUILD_IDENTITY_FILE        canonical identity document RV_BUILD_IDENTITY_HASH sha256 of
# the canonical form
#
# All outputs are cache variables, so a FUNCTION is safe here and keeps the early returns from escaping into CMakeLists.txt. The document itself is not cached:
# see RV_IDENTITY_GET.
#
FUNCTION(RV_COMPUTE_BUILD_IDENTITY)
  SET(RV_BUILD_IDENTITY_AVAILABLE
      FALSE
      CACHE INTERNAL "Whether a build identity was computed" FORCE
  )
  SET(RV_BUILD_IDENTITY_FILE
      "${CMAKE_BINARY_DIR}/build-identity.json"
      CACHE INTERNAL "Canonical build identity document" FORCE
  )
  SET(RV_BUILD_IDENTITY_HASH
      ""
      CACHE INTERNAL "Build identity hash" FORCE
  )
  # A document left by an earlier configure describes that configure. Removed before anything can return early, so that a configure which computes no identity
  # -- disabled, no interpreter, an emit failure -- leaves no file for the manifest, the store or a reader to mistake for its own.
  FILE(REMOVE "${RV_BUILD_IDENTITY_FILE}")

  IF(NOT RV_BUILD_IDENTITY)
    MESSAGE(STATUS "Build identity: disabled by RV_BUILD_IDENTITY=OFF")
    RETURN()
  ENDIF()

  SET(RV_BUILD_IDENTITY_SCRIPT
      "${PROJECT_SOURCE_DIR}/src/build/build_identity.py"
      CACHE INTERNAL "Path to the shared build identity computation"
  )

  # The target OS drives the unsupported-platform failure below, so it is resolved before any tool is looked for.
  RV_BUILD_IDENTITY_TARGET_OS(_rbbi_target_os)
  IF(_rbbi_target_os STREQUAL "")
    # The identity is asked for on a platform the build does not support. Fail with a message naming it rather than proceeding with an identity that says
    # nothing about the ABI.
    MESSAGE(
      FATAL_ERROR
        "Build identity: unsupported target platform '${CMAKE_SYSTEM_NAME}' (processor '${CMAKE_SYSTEM_PROCESSOR}'). Supported platforms are Linux, macOS and "
        "Windows. Set -DRV_BUILD_IDENTITY=OFF to configure without an identity."
    )
  ENDIF()

  RV_BUILD_IDENTITY_STDLIB(_rbbi_stdlib)
  RV_BUILD_IDENTITY_CRT(_rbbi_crt)

  IF(NOT RV_BUILD_PYTHON)
    # A default build must not break because the identity cannot be computed. Record the absence and continue; the store requires an identity and fails instead.
    MESSAGE(WARNING "Build identity: no Python 3 interpreter found, so no identity will be computed. Set -DRV_BUILD_PYTHON=<path> to provide one.")
    RETURN()
  ENDIF()

  IF(NOT EXISTS "${RV_BUILD_IDENTITY_SCRIPT}")
    MESSAGE(WARNING "Build identity: ${RV_BUILD_IDENTITY_SCRIPT} not found, so no identity will be computed.")
    RETURN()
  ENDIF()

  SET(_rbbi_inputs
      "${CMAKE_BINARY_DIR}/build-identity.inputs"
  )

  # build_config is CMAKE_BUILD_TYPE even with a multi-configuration generator (Visual Studio, Xcode). RV builds its dependencies with --config
  # ${CMAKE_BUILD_TYPE} and names their libraries from it, so it is the configuration the dependencies actually are; building another --config in the same tree
  # was already a mismatch before the identity existed, and the identity does not try to describe it.
  FILE(
    WRITE "${_rbbi_inputs}"
    "# Raw build identity inputs, gathered by cmake/macros/rv_build_identity.cmake.\n"
    "# Normalization and hashing happen in src/build/build_identity.py, which the Conan path also invokes.\n"
    "vfx_platform=${RV_VFX_PLATFORM}\n"
    "target_os=${_rbbi_target_os}\n"
    "target_arch=${CMAKE_SYSTEM_PROCESSOR}\n"
    "compiler_id=${CMAKE_CXX_COMPILER_ID}\n"
    "compiler_version=${CMAKE_CXX_COMPILER_VERSION}\n"
    "stdlib=${_rbbi_stdlib}\n"
    "crt=${_rbbi_crt}\n"
    "cxx_standard=${RV_CPP_STANDARD}\n"
    "build_config=${CMAKE_BUILD_TYPE}\n"
    "python_version=${RV_DEPS_PYTHON_VERSION}\n"
    "qt_version=${RV_DEPS_QT_VERSION}\n"
  )

  EXECUTE_PROCESS(
    COMMAND "${RV_BUILD_PYTHON}" "${RV_BUILD_IDENTITY_SCRIPT}" emit --inputs "${_rbbi_inputs}" --out "${RV_BUILD_IDENTITY_FILE}"
    RESULT_VARIABLE _rbbi_result
    OUTPUT_VARIABLE _rbbi_stdout
    ERROR_VARIABLE _rbbi_stderr
  )

  IF(NOT _rbbi_result EQUAL 0)
    IF(_rbbi_result EQUAL 3)
      # The script rejects the target rather than inventing an identity for it.
      MESSAGE(FATAL_ERROR "Build identity: ${_rbbi_stderr}")
    ENDIF()
    MESSAGE(WARNING "Build identity: could not compute an identity (exit ${_rbbi_result}). ${_rbbi_stderr}")
    RETURN()
  ENDIF()

  FILE(READ "${RV_BUILD_IDENTITY_FILE}" _rbbi_document)
  STRING(
    JSON
    _rbbi_hash
    ERROR_VARIABLE
    _rbbi_hash_error
    GET
    "${_rbbi_document}"
    "hash"
  )
  IF(_rbbi_hash_error)
    MESSAGE(WARNING "Build identity: the identity document could not be parsed (${_rbbi_hash_error}).")
    RETURN()
  ENDIF()

  SET(RV_BUILD_IDENTITY_AVAILABLE
      TRUE
      CACHE INTERNAL "Whether a build identity was computed" FORCE
  )
  SET(RV_BUILD_IDENTITY_HASH
      "${_rbbi_hash}"
      CACHE INTERNAL "Build identity hash" FORCE
  )
ENDFUNCTION()

#
# RV_REPORT_BUILD_IDENTITY()
#
# Print the identity, and compare it against the Conan profile's view of the platform.
#
# Separate from the computation because the computation has to happen before the dependencies are configured -- when a store location is set, the dependency
# base directory is derived from the identity -- while the report belongs where the platform is settled and the Conan documents are on disk. Reporting reads the
# document the computation wrote rather than recomputing, so the two cannot disagree.
#
FUNCTION(RV_REPORT_BUILD_IDENTITY)
  IF(NOT RV_BUILD_IDENTITY_AVAILABLE)
    RETURN()
  ENDIF()

  # Report every field the identity carries, so what the build believes it is building against is visible without inspecting internal state. A field the
  # document does not carry is skipped rather than printed empty: the C runtime is absent off Windows, and `crt:` with nothing after it would read as a field
  # whose value is empty rather than as one that does not apply here.
  MESSAGE(STATUS "Build identity (${RV_BUILD_IDENTITY_HASH}):")
  FOREACH(
    _rbbi_field
    ${RV_BUILD_IDENTITY_FIELDS}
  )
    RV_IDENTITY_GET(${_rbbi_field} _rbbi_value)
    IF(NOT "${_rbbi_value}" STREQUAL "")
      MESSAGE(STATUS "    ${_rbbi_field}: ${_rbbi_value}")
    ENDIF()
  ENDFOREACH()

  # The identity is computed before the dependencies, so its Qt version is the one this build is configured for. The Qt actually found is only known now, and
  # can differ when QT_HOME points at another Qt; that is reported here, and the manifest records the found version alongside the identity.
  RV_IDENTITY_GET(qt_version _rbbi_identity_qt)
  IF(RV_DEPS_QT_FOUND_VERSION
     AND NOT "${RV_DEPS_QT_FOUND_VERSION}" STREQUAL "${_rbbi_identity_qt}"
  )
    MESSAGE(
      WARNING
        "Build identity: the identity records Qt ${_rbbi_identity_qt}, the version ${RV_VFX_PLATFORM} specifies, but the Qt found is ${RV_DEPS_QT_FOUND_VERSION}. The build uses the Qt found; the manifest records both."
    )
  ENDIF()

  # Compare against the Conan profile when the Conan path produced one. Phase 0 reports drift; it does not fail the build for it.
  RV_BUILD_IDENTITY_COMPARE_WITH_CONAN()
ENDFUNCTION()
