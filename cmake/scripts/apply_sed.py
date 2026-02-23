#!/usr/bin/env python3
#
# Copyright (C) 2026  Autodesk, Inc. All Rights Reserved.
#
# SPDX-License-Identifier: Apache-2.0
#

"""
Applies sed-style substitution scripts to input files.
Emulates GNU sed BRE (Basic Regular Expression) behavior.

Replacement for the 'sed' Unix utility in the OpenRV build system,
allowing Windows builds without MSYS2.

Usage:
    python3 apply_sed.py --sed-file SCRIPT --input INPUT --output OUTPUT
"""

import argparse
import re
import sys


def _bre_to_python_regex(bre_pattern):
    """Convert a sed BRE (Basic Regular Expression) pattern to Python regex.

    In BRE:
        ( ) ? + { } | are literal characters
        \\( \\) are group delimiters
        \\? \\+ are quantifiers (GNU extension)
        \\{ \\} are interval brackets
        \\| is alternation (GNU extension)
        . * ^ $ [ ] \\ are special as in Python regex
    """
    result = []
    i = 0
    while i < len(bre_pattern):
        if bre_pattern[i] == "\\" and i + 1 < len(bre_pattern):
            next_char = bre_pattern[i + 1]
            if next_char == "(":
                result.append("(")
            elif next_char == ")":
                result.append(")")
            elif next_char == "{":
                result.append("{")
            elif next_char == "}":
                result.append("}")
            elif next_char == "?":
                result.append("?")
            elif next_char == "+":
                result.append("+")
            elif next_char == "|":
                result.append("|")
            elif next_char == "1":
                result.append("\\1")
            elif next_char == "2":
                result.append("\\2")
            elif next_char == "3":
                result.append("\\3")
            elif next_char == "4":
                result.append("\\4")
            elif next_char == "5":
                result.append("\\5")
            elif next_char == "6":
                result.append("\\6")
            elif next_char == "7":
                result.append("\\7")
            elif next_char == "8":
                result.append("\\8")
            elif next_char == "9":
                result.append("\\9")
            else:
                # Other backslash sequences pass through (e.g. \n, \t, \., \\)
                result.append("\\")
                result.append(next_char)
            i += 2
            continue
        elif bre_pattern[i] == "(":

            result.append("\\(")
        elif bre_pattern[i] == ")":
            result.append("\\)")
        elif bre_pattern[i] == "?":
            result.append("\\?")
        elif bre_pattern[i] == "+":
            result.append("\\+")
        elif bre_pattern[i] == "{":
            result.append("\\{")
        elif bre_pattern[i] == "}":
            result.append("\\}")
        elif bre_pattern[i] == "|":
            result.append("\\|")
        else:
            result.append(bre_pattern[i])
            i += 1
            continue
        i += 1
    return "".join(result)


def _bre_to_python_replacement(bre_replacement):
    """Convert a sed BRE replacement string to Python regex replacement.

    In sed replacements:
        & refers to the entire match
        \\1-\\9 are backreferences (same as Python)
        \\n is a newline
    """
    result = []
    i = 0
    while i < len(bre_replacement):
        if bre_replacement[i] == "\\" and i + 1 < len(bre_replacement):
            next_char = bre_replacement[i + 1]
            if next_char == "&":
                # Escaped ampersand — literal &
                result.append("&")
            elif next_char == "\\":
                result.append("\\\\")
            elif next_char == "n":
                result.append("\n")
            else:
                result.append("\\")
                result.append(next_char)
            i += 2
        elif bre_replacement[i] == "&":
            result.append("\\g<0>")
            i += 1
        else:
            result.append(bre_replacement[i])
            i += 1
    return "".join(result)


def parse_sed_file(sed_path):
    """Parse a sed script file, returning list of (pattern, replacement, flags) tuples.

    Supports:
        s/PATTERN/REPLACEMENT/[flags]
        s,PATTERN,REPLACEMENT,[flags]
        (any single character as delimiter after 's')
    """
    substitutions = []
    with open(sed_path, "r", newline="") as f:
        for line_num, line in enumerate(f, 1):
            line = line.rstrip("\n\r")
            if not line or line.startswith("#"):
                continue
            if not line.startswith("s"):
                print(
                    f"Warning: skipping unrecognized line {line_num}: {line}",
                    file=sys.stderr,
                )
                continue

            delim = line[1]
            # Split the rest by the delimiter to get pattern and replacement.
            # We need to handle the case where the delimiter appears in the
            # pattern/replacement (escaped with backslash).
            rest = line[2:]

            # Find the unescaped delimiter separating pattern from replacement
            pattern_end = _find_unescaped(rest, delim, 0)
            if pattern_end is None:
                print(
                    f"Warning: malformed sed command at line {line_num}: {line}",
                    file=sys.stderr,
                )
                continue

            pattern = rest[:pattern_end]
            after_pattern = rest[pattern_end + 1 :]

            # Find the unescaped delimiter ending the replacement
            repl_end = _find_unescaped(after_pattern, delim, 0)
            if repl_end is not None:
                replacement = after_pattern[:repl_end]
                flags = after_pattern[repl_end + 1 :]
            else:
                # No trailing delimiter — take the rest as replacement
                replacement = after_pattern
                flags = ""

            py_pattern = _bre_to_python_regex(pattern)
            py_replacement = _bre_to_python_replacement(replacement)
            substitutions.append((py_pattern, py_replacement, flags))
    return substitutions


def _find_unescaped(s, char, start):
    """Find the first unescaped occurrence of char in s starting at start."""
    i = start
    while i < len(s):
        if s[i] == "\\" and i + 1 < len(s):
            i += 2  # skip escaped character
            continue
        if s[i] == char:
            return i
        i += 1
    return None


def apply_substitutions(text, substitutions):
    """Apply all substitutions to text, emulating sed line-by-line behavior.

    Without 'g' flag: replaces only the first match per line.
    With 'g' flag: replaces all matches per line.
    """
    lines = text.split("\n")
    for i, line in enumerate(lines):
        for pattern, replacement, flags in substitutions:
            global_replace = "g" in flags
            if global_replace:
                line = re.sub(pattern, replacement, line)
            else:
                line = re.sub(pattern, replacement, line, count=1)
        lines[i] = line
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Apply sed-style substitutions to a file"
    )
    parser.add_argument(
        "--sed-file", required=True, help="Path to the sed script file"
    )
    parser.add_argument("--input", required=True, help="Path to the input file")
    parser.add_argument("--output", required=True, help="Path to the output file")
    args = parser.parse_args()

    substitutions = parse_sed_file(args.sed_file)
    with open(args.input, "r", newline="") as f:
        content = f.read()
    result = apply_substitutions(content, substitutions)
    with open(args.output, "w", newline="") as f:
        f.write(result)


if __name__ == "__main__":
    main()
