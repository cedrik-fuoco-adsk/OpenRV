# *****************************************************************************
# Copyright 2026 Autodesk, Inc. All rights reserved.
#
# SPDX-License-Identifier: Apache-2.0
#
# *****************************************************************************

#
# Verifies how RV_BUILD_IDENTITY_CRT resolves CMAKE_MSVC_RUNTIME_LIBRARY into the `<kind>:<runtime type>` the identity records.
#
# This is CMake-side string logic, so the Python checks cannot reach it, and the value it produces decides whether two builds are allowed to share artifacts.
# Run it with:
#
# cmake -P cmake/macros/test_rv_build_identity_crt.cmake
#
# MSVC is forced on rather than detected, because the resolution depends only on the variable and the build type. The Windows-only branch is therefore checked
# on every platform, which is the point: an untested branch here is a wrong runtime silently recorded as a fact.
#

SET(MSVC
    TRUE
)
# Set to a running interpreter so that including the macro file does not go looking for one.
SET(RV_BUILD_PYTHON
    "${CMAKE_COMMAND}"
)

INCLUDE("${CMAKE_CURRENT_LIST_DIR}/rv_build_identity.cmake")

SET(_rt_failures
    0
)

# EXPECT_CRT(<CMAKE_MSVC_RUNTIME_LIBRARY> <CMAKE_BUILD_TYPE> <expected>)
MACRO(EXPECT_CRT _rt_library _rt_config _rt_expected)
  SET(CMAKE_MSVC_RUNTIME_LIBRARY
      "${_rt_library}"
  )
  SET(CMAKE_BUILD_TYPE
      "${_rt_config}"
  )
  RV_BUILD_IDENTITY_CRT(_rt_actual)
  # Both sides are dereferenced and quoted: a macro's parameters are string replacements, so a bare `_rt_expected` in an if() is the literal text "_rt_expected"
  # and every comparison would be false.
  IF("${_rt_actual}" STREQUAL "${_rt_expected}")
    MESSAGE(STATUS "  ok: '${_rt_library}' with ${_rt_config} -> '${_rt_actual}'")
  ELSE()
    MESSAGE(STATUS "  FAILED: '${_rt_library}' with ${_rt_config} -> '${_rt_actual}', expected '${_rt_expected}'")
    MATH(EXPR _rt_failures "${_rt_failures} + 1")
  ENDIF()
ENDMACRO()

MESSAGE(STATUS "RV_BUILD_IDENTITY_CRT")

# The default is CMake's own default for the property, a generator expression: MultiThreaded$<$<CONFIG:Debug>:Debug>DLL. It has to be resolved for this
# configuration because the identity is computed before generation.
EXPECT_CRT("" "Release" "dynamic:Release")
EXPECT_CRT("" "Debug" "dynamic:Debug")
EXPECT_CRT("" "RelWithDebInfo" "dynamic:Release")

# An explicit selection, in each of CMake's four values.
EXPECT_CRT("MultiThreadedDLL" "Release" "dynamic:Release")
EXPECT_CRT("MultiThreadedDebugDLL" "Debug" "dynamic:Debug")
EXPECT_CRT("MultiThreaded" "Release" "static:Release")
EXPECT_CRT("MultiThreadedDebug" "Debug" "static:Debug")

# An explicit selection containing the generator expression rather than the resolved name.
EXPECT_CRT("\$<\$<CONFIG:Debug>:Debug>DLL" "Release" "dynamic:Release")
EXPECT_CRT("\$<\$<CONFIG:Debug>:Debug>DLL" "Debug" "dynamic:Debug")

# The static runtime in a Release build, and the dynamic runtime in a Debug build. These are the cases the field exists for: the configuration name alone would
# record them as sharing an identity with the default of the same configuration.
EXPECT_CRT("MultiThreaded" "Release" "static:Release")
EXPECT_CRT("MultiThreadedDebugDLL" "Debug" "dynamic:Debug")

# A configuration whose runtime does not follow the configuration name is recorded as what it links, not as the name. If a Release build is told to use the
# debug runtime, that difference must appear in the identity rather than be flattened by it.
EXPECT_CRT("MultiThreadedDebug" "Release" "static:Debug")

# An expression this does not understand is recorded verbatim instead of being resolved wrongly, so the identity differs from a resolved one rather than
# silently matching it. The warning printed here is the expected outcome.
MESSAGE(STATUS "  the next warning is expected: an unresolvable expression")
EXPECT_CRT("\$<IF:\$<CONFIG:Debug>,MultiThreadedDebugDLL,MultiThreadedDLL>" "Release" "\$<IF:\$<CONFIG:Debug>,MultiThreadedDebugDLL,MultiThreadedDLL>")

# Not Windows: no field at all, whatever the variable says, because there is no correct value to invent on a platform without this axis.
SET(MSVC
    FALSE
)
EXPECT_CRT("MultiThreadedDebugDLL" "Debug" "")

MESSAGE(STATUS "")
IF(_rt_failures GREATER 0)
  MESSAGE(FATAL_ERROR "RV_BUILD_IDENTITY_CRT: ${_rt_failures} check(s) failed")
ENDIF()
MESSAGE(STATUS "all C runtime resolution checks passed")
