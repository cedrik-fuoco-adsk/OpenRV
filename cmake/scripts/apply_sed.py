#!/usr/bin/env python3
#
# Copyright (C) 2024  Autodesk, Inc. All Rights Reserved.
#
# SPDX-License-Identifier: Apache-2.0
#

"""
Applies sed-style substitution scripts to input files.
Supports Python regex syntax including lookbehinds (?<!...).

Replacement for the 'sed' Unix utility in the OpenRV build system,
allowing Windows builds without MSYS2.

Usage:
    python3 apply_sed.py --sed-file SCRIPT --input INPUT --output OUTPUT
"""

import argparse
import re
import sys


def parse_sed_file(sed_path):
    """Parse a sed script file, returning list of (pattern, replacement) tuples.

    Supports:
        s/PATTERN/REPLACEMENT/
        s,PATTERN,REPLACEMENT,
        (any single character as delimiter after 's')
    """
    substitutions = []
    with open(sed_path, "r") as f:
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
            else:
                # No trailing delimiter — take the rest as replacement
                replacement = after_pattern

            substitutions.append((pattern, replacement))
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
    """Apply all substitutions to text using Python regex."""
    for pattern, replacement in substitutions:
        text = re.sub(pattern, replacement, text)
    return text


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
    with open(args.input, "r") as f:
        content = f.read()
    result = apply_substitutions(content, substitutions)
    with open(args.output, "w") as f:
        f.write(result)


if __name__ == "__main__":
    main()
