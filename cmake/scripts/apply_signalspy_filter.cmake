#
# Copyright (C) 2024  Autodesk, Inc. All Rights Reserved.
#
# SPDX-License-Identifier: Apache-2.0
#

#
# CMake script-mode file for applying sed-style literal string substitutions.
# Used to patch Qt moc-generated SignalSpy files without requiring bash or sed.
#
# Usage:
#   cmake -DINPUT_FILE=<path> -DOUTPUT_FILE=<path> -DSED_FILE=<path> -P apply_signalspy_filter.cmake
#
# The sed file must contain only s/PATTERN/REPLACEMENT/ style lines with literal strings
# (no regex). Uses STRING(REPLACE) for exact matching.
#

IF(NOT INPUT_FILE)
  MESSAGE(FATAL_ERROR "INPUT_FILE not specified")
ENDIF()
IF(NOT OUTPUT_FILE)
  MESSAGE(FATAL_ERROR "OUTPUT_FILE not specified")
ENDIF()
IF(NOT SED_FILE)
  MESSAGE(FATAL_ERROR "SED_FILE not specified")
ENDIF()

FILE(READ "${INPUT_FILE}" _content)
FILE(READ "${SED_FILE}" _sed_content)

# Parse each line of the sed file
STRING(REPLACE "\n" ";" _sed_lines "${_sed_content}")
FOREACH(_line IN LISTS _sed_lines)
  STRING(STRIP "${_line}" _line)
  IF("${_line}" STREQUAL "" OR "${_line}" MATCHES "^#")
    CONTINUE()
  ENDIF()
  # Parse s/PATTERN/REPLACEMENT/ — detect delimiter (char after 's')
  STRING(SUBSTRING "${_line}" 0 1 _prefix)
  IF(NOT "${_prefix}" STREQUAL "s")
    CONTINUE()
  ENDIF()
  STRING(SUBSTRING "${_line}" 1 1 _delim)
  STRING(SUBSTRING "${_line}" 2 -1 _rest)
  # Find delimiter separating pattern from replacement
  STRING(FIND "${_rest}" "${_delim}" _split_pos)
  IF(_split_pos EQUAL -1)
    CONTINUE()
  ENDIF()
  STRING(SUBSTRING "${_rest}" 0 ${_split_pos} _pattern)
  MATH(EXPR _repl_start "${_split_pos} + 1")
  STRING(SUBSTRING "${_rest}" ${_repl_start} -1 _repl_rest)
  # Find trailing delimiter
  STRING(FIND "${_repl_rest}" "${_delim}" _end_pos)
  IF(_end_pos GREATER -1)
    STRING(SUBSTRING "${_repl_rest}" 0 ${_end_pos} _replacement)
  ELSE()
    SET(_replacement "${_repl_rest}")
  ENDIF()
  STRING(REPLACE "${_pattern}" "${_replacement}" _content "${_content}")
ENDFOREACH()

FILE(WRITE "${OUTPUT_FILE}" "${_content}")
