#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# *****************************************************************************
# Copyright 2026 Autodesk, Inc. All rights reserved.
#
# SPDX-License-Identifier: Apache-2.0
#
# *****************************************************************************

"""Compare the files Conan generates between a baseline tree and the current tree.

Task 2.3 of the build-identity change is that the Conan path still generates the same files as
it did before the identity work, with the additions being a known, named set. Building the same
tree twice and diffing the output is the only way to actually show that, so this exists to make
the comparison precise rather than a wall of diff output that someone has to eyeball.

Three kinds of difference are reported, and each is either on an allow-list or a violation:

  added      present in the current tree only
  removed    present in the baseline tree only
  changed    present in both, different content -- and for a file allowed to change, every
             differing LINE must match one of the allowed patterns

A fourth classification is reported and does *not* fail: `reordered`, for a file carrying the
same lines in a different order. Conan's CMakeDeps writes some dependency configuration files
with two blocks of independently-assigned variables whose relative order varies between installs
of one tree, so a reordering is non-determinism in the generator rather than a difference a change
made. It is named in the summary so it is visible, and any line that is added, removed or altered
makes the sorted lines differ and is still a violation.

Both trees embed their own absolute paths in the generated files, so text is normalized before
comparison: each tree root is replaced with a placeholder, which is what makes a meaningful
comparison possible at all.
"""

from __future__ import annotations

import argparse
import difflib
import json
import os
import re
import sys


def read_file(path: str):
    """Return ``(is_text, content)``; binary files are compared as bytes."""
    try:
        with open(path, "rb") as handle:
            data = handle.read()
    except OSError as error:
        return False, f"<unreadable: {error}>".encode()
    try:
        return True, data.decode("utf-8")
    except UnicodeDecodeError:
        return False, data


def _canonical_json(text: str, ignore_keys) -> str:
    """Re-serialize JSON canonically, dropping named keys wherever they appear.

    Comparing JSON as text is the wrong tool twice over: adding a key also changes the preceding
    line's comma, so a line-level allowance can never permit a legitimate addition, and any
    formatting difference would look like a content difference. Parsing and re-serializing makes
    the comparison semantic, and dropping the named keys expresses "these may differ" precisely.
    """
    try:
        document = json.loads(text)
    except json.JSONDecodeError:
        return text

    def strip(node):
        if isinstance(node, dict):
            return {key: strip(value) for key, value in node.items() if key not in ignore_keys}
        if isinstance(node, list):
            return [strip(item) for item in node]
        return node

    return json.dumps(strip(document), indent=2, sort_keys=True)


def collect(root: str, normalizations, json_ignore_keys=(), regex_normalizations=()) -> dict:
    """Map relative path -> (is_text, normalized content) for every file under ``root``.

    ``normalizations`` are literal ``(from, to)`` pairs, used for the tree's own path.
    ``regex_normalizations`` are ``(pattern, replacement)`` pairs and exist for Conan's cache: a
    package is rebuilt with a new folder hash whenever the build flags force it, which rewrites
    every generated file that mentions that package while saying nothing about what was generated.
    Left unnormalized, that churn makes a file's contents unexamined rather than equal.

    JSON files are canonicalized, and ``json_ignore_keys`` are dropped from them, so a file whose
    only difference is those keys compares equal.
    """
    ignore = set(json_ignore_keys)
    files = {}
    for dirpath, _dirnames, filenames in os.walk(root):
        for name in filenames:
            full = os.path.join(dirpath, name)
            relative = os.path.relpath(full, root).replace(os.sep, "/")
            is_text, content = read_file(full)
            if is_text:
                for source, replacement in normalizations:
                    if source:
                        content = content.replace(source, replacement)
                        content = content.replace(source.replace("\\", "/"), replacement)
                for pattern, replacement in regex_normalizations:
                    content = pattern.sub(replacement, content)
                content = content.replace("\r\n", "\n")
                if relative.endswith(".json"):
                    content = _canonical_json(content, ignore)
            files[relative] = (is_text, content)
    return files


def _matches(patterns, value: str) -> bool:
    return any(re.fullmatch(pattern, value) for pattern in patterns)


def _reordered(before: str, after: str) -> bool:
    """True when the two texts carry the same lines in a different order.

    Conan's CMakeDeps writes some dependency configuration files with two blocks of
    independently-assigned variables -- WebPConfig.cmake carries both `WebP_*` and `WEBP_*` --
    and their relative order varies between installs of the *same* tree. It is
    non-determinism in the generator, not a difference a change made, and it turns up between
    two installs of an unmodified tree as readily as between two trees: the determinism
    control caught it in one run and missed it in another, where it surfaced as a failure.

    A permutation adds, removes and alters nothing, so it is named in the summary and does not
    fail. Any line added, removed or changed makes the sorted lines differ, and is still a
    difference.
    """
    if not isinstance(before, str) or not isinstance(after, str):
        return False
    return sorted(before.splitlines()) == sorted(after.splitlines())


def compare(baseline: dict, current: dict, allow_added, allow_removed, allow_changed, allow_changed_lines):
    """Return ``(summary, violations)``."""
    baseline_names = set(baseline)
    current_names = set(current)

    added = sorted(current_names - baseline_names)
    removed = sorted(baseline_names - current_names)
    changed = []
    reordered = []
    for name in sorted(baseline_names & current_names):
        before = baseline[name][1]
        after = current[name][1]
        if before == after:
            continue
        if _reordered(before, after):
            reordered.append(name)
        else:
            changed.append(name)

    violations = []

    for name in added:
        if not _matches(allow_added, name):
            violations.append({"kind": "added", "path": name, "detail": "file was added and is not on the allow-list"})

    for name in removed:
        if not _matches(allow_removed, name):
            violations.append(
                {"kind": "removed", "path": name, "detail": "file disappeared and is not on the allow-list"}
            )

    allowed_line = re.compile("|".join(allow_changed_lines)) if allow_changed_lines else None

    for name in changed:
        if not _matches(allow_changed, name):
            violations.append(
                {
                    "kind": "changed",
                    "path": name,
                    "detail": "file content changed and the file is not allowed to change",
                }
            )
            continue
        if allowed_line is None:
            continue
        _is_text, before = baseline[name]
        _is_text, after = current[name]
        if not isinstance(before, str) or not isinstance(after, str):
            continue
        for line in difflib.unified_diff(before.splitlines(), after.splitlines(), lineterm="", n=0):
            if line.startswith(("---", "+++", "@@")):
                continue
            if not line.startswith(("+", "-")):
                continue
            if allowed_line is not None and allowed_line.search(line[1:].strip()):
                continue
            violations.append({"kind": "changed-line", "path": name, "detail": line.strip()})

    summary = {
        "added": added,
        "removed": removed,
        "changed": changed,
        "reordered": reordered,
        "violations": violations,
    }
    return summary, violations


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--baseline", required=True, help="generated-files directory from the baseline tree")
    parser.add_argument("--current", required=True, help="generated-files directory from the current tree")
    parser.add_argument(
        "--normalize",
        action="append",
        default=[],
        metavar="PATH=PLACEHOLDER",
        help="replace an absolute path with a placeholder before comparing; repeatable. Both trees embed their own paths.",
    )
    parser.add_argument("--allow-added", action="append", default=[], metavar="REGEX")
    parser.add_argument("--allow-removed", action="append", default=[], metavar="REGEX")
    parser.add_argument("--allow-changed", action="append", default=[], metavar="REGEX")
    parser.add_argument(
        "--allow-changed-line",
        action="append",
        default=[],
        metavar="REGEX",
        help="for a file allowed to change, the only differing lines permitted; repeatable",
    )
    parser.add_argument(
        "--json-ignore-key",
        action="append",
        default=[],
        metavar="KEY",
        help="ignore this JSON key wherever it appears, so files differing only by it compare equal; repeatable",
    )
    parser.add_argument(
        "--normalize-regex",
        action="append",
        default=[],
        metavar="PATTERN=REPLACEMENT",
        help="regular expression to normalize before comparing, e.g. Conan cache package folders; "
        "the pattern must not itself contain '='; repeatable",
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    if not os.path.isdir(args.baseline):
        print(f"the baseline directory does not exist: {args.baseline}", file=sys.stderr)
        return 4
    if not os.path.isdir(args.current):
        print(f"the current directory does not exist: {args.current}", file=sys.stderr)
        return 4

    normalizations = []
    for item in args.normalize:
        if "=" not in item:
            print(f"--normalize expects PATH=PLACEHOLDER, got {item!r}", file=sys.stderr)
            return 4
        source, replacement = item.split("=", 1)
        normalizations.append((source, replacement))

    regex_normalizations = []
    for item in args.normalize_regex:
        if "=" not in item:
            print(f"--normalize-regex expects PATTERN=REPLACEMENT, got {item!r}", file=sys.stderr)
            return 4
        pattern, replacement = item.split("=", 1)
        try:
            regex_normalizations.append((re.compile(pattern), replacement))
        except re.error as error:
            print(f"--normalize-regex pattern {pattern!r} is not valid: {error}", file=sys.stderr)
            return 4

    baseline = collect(args.baseline, normalizations, args.json_ignore_key, regex_normalizations)
    current = collect(args.current, normalizations, args.json_ignore_key, regex_normalizations)
    summary, violations = compare(
        baseline, current, args.allow_added, args.allow_removed, args.allow_changed, args.allow_changed_line
    )

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 0 if not violations else 2

    print(f"compared {len(baseline)} baseline file(s) against {len(current)} current file(s)")
    for label in ("added", "removed", "changed", "reordered"):
        names = summary[label]
        print(f"  {label:8} {len(names)}" + (f": {', '.join(names)}" if names else ""))
    if summary["reordered"]:
        print("  (reordered files carry the same lines in a different order, which installs of one tree do too)")

    if not violations:
        print("OK: every difference is one of the expected, named ones")
        return 0

    print()
    print(f"{len(violations)} unexpected difference(s):")
    for violation in violations:
        print(f"  {violation['kind']}: {violation['path']}: {violation['detail']}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
