#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# *****************************************************************************
# Copyright 2026 Autodesk, Inc. All rights reserved.
#
# SPDX-License-Identifier: Apache-2.0
#
# *****************************************************************************

"""Canonicalize, hash and compare OpenRV build identities.

This script is the single source of truth for what a build identity is. Both
consumers invoke it so that they derive the identity from the same computation
instead of each normalizing on their own:

  * the CMake configure path, from ``cmake/macros/rv_build_identity.cmake``
  * the Conan generate path, from ``openrvcore-conanfile.py``

Deriving the identity twice, independently, is the drift this exists to
prevent: a Conan profile that says ``compiler.version=11`` while the host
compiler is 13 must be detectable, not discovered later as a link error.

Subcommands
-----------

``emit``
    Read a raw ``key=value`` input file and write canonical identity JSON.

``compare``
    Compare two canonical identity documents field by field and report which
    fields disagree. Used to check a Conan profile against the identity the
    CMake path computed.

Only the Python standard library is used, so this runs anywhere the build
already runs Python: it is not an inspection tool and never needs readelf,
otool or dumpbin.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys

# Bump when normalization rules change, so that artifacts keyed by an older
# rule set can never be confused with ones keyed by a newer one.
#
# 2: added `crt`, the C runtime library on Windows. A Release build against the
#    static runtime and one against the dynamic runtime used to produce the same
#    identity, because a build configuration name does not determine which
#    runtime is linked.
FIELDS_VERSION = 2

# Fields every identity must carry. `python_abi` is derived from the raw
# `python_version` input; the rest are normalized one-to-one.
REQUIRED_RAW_FIELDS = (
    "vfx_platform",
    "target_os",
    "target_arch",
    "compiler_id",
    "compiler_version",
    "stdlib",
    "cxx_standard",
    "build_config",
    "python_version",
)

# Fields derived from a raw input rather than carried through unchanged.
DERIVED_FIELDS = ("python_abi",)

# Output fields, in the order they are documented. JSON is emitted with sorted
# keys for byte-stability; this order is only used for reporting.
OUTPUT_FIELDS = (
    "compiler_id",
    "compiler_version",
    "build_config",
    "crt",
    "cxx_standard",
    "python_abi",
    "qt_version",
    "stdlib",
    "target_arch",
    "target_os",
    "vfx_platform",
)

# Fields both the CMake path and the Conan path can know, and therefore the
# only fields a mismatch report can be made about. Qt and Python versions are
# VFX/CMake concerns that a Conan profile does not express.
COMPARABLE_FIELDS = (
    "target_os",
    "target_arch",
    "compiler_id",
    "compiler_version",
    "stdlib",
    "crt",
    "cxx_standard",
    "build_config",
)

SUPPORTED_OSES = ("linux", "macos", "windows")

_OS_ALIASES = {
    "linux": "linux",
    "macos": "macos",
    "macosx": "macos",
    "darwin": "macos",
    "osx": "macos",
    "windows": "windows",
    "win32": "windows",
    "win": "windows",
}

_ARCH_ALIASES = {
    "x86_64": "x86_64",
    "amd64": "x86_64",
    "x64": "x86_64",
    "arm64": "arm64",
    "aarch64": "arm64",
    "armv8": "arm64",
    "armv8.5": "arm64",
}

_COMPILER_ALIASES = {
    "gnu": "gcc",
    "gcc": "gcc",
    "clang": "clang",
    "llvm": "clang",
    "appleclang": "apple-clang",
    "apple-clang": "apple-clang",
    "apple_clang": "apple-clang",
    "msvc": "msvc",
}

_STDLIB_ALIASES = {
    "libstdc++": "libstdc++11",
    "libstdc++11": "libstdc++11",
    "gnu": "libstdc++11",
    "libc++": "libc++",
    "libcxx": "libc++",
    "msvc": "msvc",
    "msvcrt": "msvc",
    "vcruntime": "msvc",
}

_BUILD_CONFIG_ALIASES = {
    "release": "Release",
    "relwithdebinfo": "Release",
    "minsizerel": "Release",
    "debug": "Debug",
}

# The C runtime library, as the two questions that actually change the ABI:
# dynamic or static, and debug or release. The build configuration name answers
# only the second of those, which is why this is recorded separately.
_CANONICAL_CRT = ("dynamic", "static", "dynamic-debug", "static-debug")

_RUNTIME_KINDS = {
    "dynamic": "dynamic",
    "static": "static",
}

_RUNTIME_TYPES = {
    "debug": True,
    "release": False,
}

_SEPARATOR_RE = re.compile(r"[\s=:\t]+")
_VERSION_LEADING_INT_RE = re.compile(r"(\d+)")
_MAJOR_RE = re.compile(r"^\s*(\d+)")


def _log(message: str) -> None:
    print(f"[build_identity] {message}", file=sys.stderr, flush=True)


def _first_int(value: str, what: str) -> str:
    """Return the leading integer of ``value`` (``gnu++17`` -> ``17``)."""
    match = _VERSION_LEADING_INT_RE.search(value)
    if not match:
        raise ValueError(f"could not read a numeric {what} from {value!r}")
    return match.group(1)


def normalize_vfx_platform(raw: str) -> str:
    value = raw.strip().upper()
    if not re.fullmatch(r"CY\d{4}", value):
        raise ValueError(f"unrecognized VFX platform {raw!r}, expected a CY<year> identifier")
    return value


def normalize_os(raw: str) -> str:
    value = raw.strip().lower()
    if value not in _OS_ALIASES:
        raise ValueError(f"unsupported target OS {raw!r}; supported platforms are {', '.join(SUPPORTED_OSES)}")
    return _OS_ALIASES[value]


def normalize_arch(raw: str) -> str:
    value = raw.strip().lower()
    if value in _ARCH_ALIASES:
        return _ARCH_ALIASES[value]
    # Unknown architectures are carried through lowercased rather than
    # rejected: they still form a distinct, stable identity.
    _log(f"unrecognized architecture {raw!r}, carrying it through unchanged")
    return value


def normalize_compiler(raw: str) -> str:
    value = raw.strip().lower()
    if value in _COMPILER_ALIASES:
        return _COMPILER_ALIASES[value]
    _log(f"unrecognized compiler identifier {raw!r}, carrying it through unchanged")
    return value


def normalize_stdlib(raw: str) -> str:
    value = raw.strip().lower()
    if value in _STDLIB_ALIASES:
        return _STDLIB_ALIASES[value]
    _log(f"unrecognized standard library {raw!r}, carrying it through unchanged")
    return value


def normalize_build_config(raw: str) -> str:
    value = raw.strip()
    if value.lower() in _BUILD_CONFIG_ALIASES:
        return _BUILD_CONFIG_ALIASES[value.lower()]
    _log(f"unrecognized build configuration {raw!r}, carrying it through unchanged")
    return value


def normalize_crt(raw: str) -> str:
    """Normalize the C runtime library into ``<kind>[-debug]``.

    Only Windows has this as a separate ABI axis; elsewhere the field is absent,
    because the standard library is already carried by ``stdlib`` and a placeholder
    value would be read as a fact rather than as "not applicable".

    Accepts ``<kind>:<runtime type>`` -- the shape the CMake path resolves
    ``CMAKE_MSVC_RUNTIME_LIBRARY`` into, and the shape a Conan profile's
    ``compiler.runtime`` and ``compiler.runtime_type`` join to -- as well as an
    already canonical value.
    """
    value = raw.strip().lower()
    if value in _CANONICAL_CRT:
        return value
    kind, separator, runtime_type = value.partition(":")
    if separator and kind.strip() in _RUNTIME_KINDS and runtime_type.strip() in _RUNTIME_TYPES:
        resolved = _RUNTIME_KINDS[kind.strip()]
        return f"{resolved}-debug" if _RUNTIME_TYPES[runtime_type.strip()] else resolved
    _log(f"unrecognized C runtime {raw!r}, carrying it through unchanged")
    return raw.strip()


def normalize_python_abi(raw: str) -> str:
    """Reduce an exact Python version to its ABI series.

    The CPython C application binary interface is stable within a series, so
    the series is the identity fact that matters: 3.11.9 and 3.11.14 must
    produce the same identity.
    """
    value = raw.strip()
    match = re.match(r"^\s*(\d+)\.(\d+)", value)
    if not match:
        raise ValueError(f"could not read a Python major.minor series from {raw!r}")
    return f"{match.group(1)}.{match.group(2)}"


def normalize_version(raw: str) -> str:
    value = raw.strip()
    return value if value else "unknown"


# Per-field normalization used in partial mode, where every field is optional.
_PARTIAL_NORMALIZERS = {
    "vfx_platform": normalize_vfx_platform,
    "target_os": normalize_os,
    "target_arch": normalize_arch,
    "compiler_id": normalize_compiler,
    "compiler_version": normalize_version,
    "stdlib": normalize_stdlib,
    "crt": normalize_crt,
    "cxx_standard": lambda value: _first_int(value, "C++ standard"),
    "build_config": normalize_build_config,
    "python_version": normalize_python_abi,
    "qt_version": normalize_version,
}


def normalize_raw_fields(raw: dict, partial: bool = False) -> dict:
    """Normalize a raw key/value mapping into canonical identity fields.

    In ``partial`` mode a consumer that genuinely cannot know a field -- a Conan
    profile says nothing about the Python ABI series or the Qt version -- omits
    it instead of guessing, and the document is marked partial so a reader can
    tell the difference between "not known here" and "not applicable".
    """
    normalized = {}

    if partial:
        for key, value in raw.items():
            if value.strip() == "":
                continue
            normalizer = _PARTIAL_NORMALIZERS.get(key)
            if normalizer is not None:
                normalized[key] = normalizer(value)
            elif key in REQUIRED_RAW_FIELDS or key == "qt_version":
                _log(f"unknown identity input {key!r} carried through unchanged")
                normalized[key] = value.strip()
        normalized["partial"] = "true"
        return normalized

    for key in REQUIRED_RAW_FIELDS:
        if key not in raw or raw[key].strip() == "":
            raise ValueError(f"required identity input {key!r} is missing or empty")

    normalized["vfx_platform"] = normalize_vfx_platform(raw["vfx_platform"])
    normalized["target_os"] = normalize_os(raw["target_os"])
    normalized["target_arch"] = normalize_arch(raw["target_arch"])
    normalized["compiler_id"] = normalize_compiler(raw["compiler_id"])
    normalized["compiler_version"] = normalize_version(raw["compiler_version"])
    normalized["stdlib"] = normalize_stdlib(raw["stdlib"])
    normalized["cxx_standard"] = _first_int(raw["cxx_standard"], "C++ standard")
    normalized["build_config"] = normalize_build_config(raw["build_config"])
    normalized["python_abi"] = normalize_python_abi(raw["python_version"])
    normalized["qt_version"] = normalize_version(raw.get("qt_version", ""))

    # Windows only, and absent rather than defaulted elsewhere: there is no correct
    # value to invent on a platform that does not have this axis.
    if raw.get("crt", "").strip():
        normalized["crt"] = normalize_crt(raw["crt"])

    known = set(REQUIRED_RAW_FIELDS) | {"qt_version", "crt"}
    for key, value in raw.items():
        if key not in known:
            _log(f"unknown identity input {key!r} carried through unchanged")
            normalized[key] = value.strip()

    return normalized


def canonical_body(fields: dict) -> str:
    """Serialize fields into the exact byte sequence the hash is taken over."""
    payload = {key: str(value) for key, value in fields.items()}
    payload["fields_version"] = str(FIELDS_VERSION)
    lines = [f"{key}={payload[key]}" for key in sorted(payload)]
    return "\n".join(lines) + "\n"


def compute_hash(fields: dict) -> str:
    digest = hashlib.sha256(canonical_body(fields).encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def build_identity_document(fields: dict) -> dict:
    document = {key: str(value) for key, value in fields.items()}
    document["fields_version"] = FIELDS_VERSION
    document["hash"] = compute_hash(fields)
    return document


def read_inputs(path: str) -> dict:
    """Read a raw ``key=value`` file. Blank lines and ``#`` comments are ignored."""
    raw = {}
    with open(path, "r", encoding="utf-8") as handle:
        for lineno, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if "=" not in stripped:
                raise ValueError(f"{path}:{lineno}: expected key=value, got {stripped!r}")
            key, value = stripped.split("=", 1)
            key = key.strip().lower()
            if not key:
                raise ValueError(f"{path}:{lineno}: empty key")
            raw[key] = value.strip()
    return raw


def _major(value: str) -> str:
    match = _MAJOR_RE.match(str(value))
    return match.group(1) if match else str(value)


def compare_documents(left: dict, right: dict, fields, granularity: str):
    """Compare two identity documents over ``fields``.

    Returns ``(disagreements, unstated)``. A field that either side does not state at all is
    not a disagreement: a Conan profile that leaves ``compiler.cppstd`` unset is saying "use the
    compiler default", not "I disagree". Reporting that as drift would make the report noisy and
    therefore ignored, which is the opposite of its purpose.
    """
    disagreements = []
    unstated = []
    for field in fields:
        if field not in left or field not in right:
            unstated.append(field)
            continue
        left_value = str(left[field])
        right_value = str(right[field])
        if granularity == "major" and field in ("compiler_version",):
            if _major(left_value) == _major(right_value):
                continue
        if left_value != right_value:
            disagreements.append((field, left_value, right_value))
    return disagreements, unstated


def cmd_emit(args: argparse.Namespace) -> int:
    try:
        raw = read_inputs(args.inputs)
        fields = normalize_raw_fields(raw, partial=args.partial)
    except ValueError as error:
        print(f"build identity is not supported on this target: {error}", file=sys.stderr)
        return 3

    document = build_identity_document(fields)

    body = json.dumps(document, indent=2, sort_keys=True) + "\n"
    try:
        directory = os.path.dirname(os.path.abspath(args.out))
        if directory:
            os.makedirs(directory, exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as handle:
            handle.write(body)
    except OSError as error:
        print(f"could not write identity document to {args.out}: {error}", file=sys.stderr)
        return 4

    if args.print:
        sys.stdout.write(body)
    return 0


def cmd_compare(args: argparse.Namespace) -> int:
    fields = COMPARABLE_FIELDS
    if args.fields:
        fields = tuple(f.strip() for f in args.fields.split(",") if f.strip())

    try:
        with open(args.left, "r", encoding="utf-8") as handle:
            left = json.load(handle)
        with open(args.right, "r", encoding="utf-8") as handle:
            right = json.load(handle)
    except (OSError, json.JSONDecodeError) as error:
        print(f"could not read an identity document to compare: {error}", file=sys.stderr)
        return 4

    disagreements, unstated = compare_documents(left, right, fields, args.version_granularity)

    if args.json:
        print(
            json.dumps(
                {
                    "match": not disagreements,
                    "fields": list(fields),
                    "version_granularity": args.version_granularity,
                    "unstated": unstated,
                    "disagreements": [
                        {"field": field, "left": left_value, "right": right_value}
                        for field, left_value, right_value in disagreements
                    ],
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0 if not disagreements else 2

    if unstated:
        print(f"not stated by both sides, so not compared: {', '.join(unstated)}")

    if not disagreements:
        return 0

    print(f"build identity mismatch on {len(disagreements)} of {len(fields)} compared fields:")
    for field, left_value, right_value in disagreements:
        print(f"  {field}: {args.left_name}={left_value}  {args.right_name}={right_value}")
    return 2


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    subparsers = parser.add_subparsers(dest="command", required=True)

    emit = subparsers.add_parser("emit", help="normalize raw inputs into canonical identity JSON")
    emit.add_argument("--inputs", required=True, help="raw key=value input file")
    emit.add_argument("--out", required=True, help="path of the canonical identity JSON to write")
    emit.add_argument("--print", action="store_true", help="also write the document to stdout")
    emit.add_argument(
        "--partial",
        action="store_true",
        help="the caller knows only part of the identity: omit what was not supplied and mark the document partial, "
        "rather than requiring every field or guessing one",
    )
    emit.set_defaults(func=cmd_emit)

    compare = subparsers.add_parser("compare", help="compare two canonical identity documents")
    compare.add_argument("--left", required=True)
    compare.add_argument("--right", required=True)
    compare.add_argument("--left-name", default="computed")
    compare.add_argument("--right-name", default="conan")
    compare.add_argument(
        "--version-granularity",
        choices=("major", "exact"),
        default="major",
        help="compare compiler versions at major granularity (default) or exactly; "
        "a Conan profile expresses only the compiler major, so exact comparison "
        "would report drift that does not exist",
    )
    compare.add_argument("--fields", help="comma-separated field subset to compare")
    compare.add_argument("--json", action="store_true")
    compare.set_defaults(func=cmd_compare)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
