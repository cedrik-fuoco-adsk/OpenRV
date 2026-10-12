#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# *****************************************************************************
# Copyright 2026 Autodesk, Inc. All rights reserved.
#
# SPDX-License-Identifier: Apache-2.0
#
# *****************************************************************************

"""Assemble the build manifest: a single answer to "what is this build made of?".

The manifest ties together the things that together define a build, so that
support, release validation and licence review do not have to reconstruct it
from a build log:

  * the computed build identity
  * the resolved Conan package set, with the identity it was resolved under
  * each prebuilt or derived artifact, with the facts probed from it

Assembly happens here rather than in CMake for two reasons: JSON escaping is
trivial in Python and error-prone in CMake, and a write failure must be a
warning rather than a fatal error, which CMake's ``file(WRITE)`` cannot express.

The output is deliberately deterministic -- sorted keys and no timestamp -- so
that two configurations with unchanged inputs produce byte-identical manifests
and a diff between them is meaningful.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

FIELDS_VERSION = 1


def _log(message: str) -> None:
    print(f"[build_manifest] {message}", file=sys.stderr, flush=True)


def read_json(path, section):
    """Read an optional JSON input. Returns ``(value, omission_or_None)``."""
    if not path:
        return None, {"section": section, "reason": "not produced by this configuration"}
    if not os.path.isfile(path):
        return None, {"section": section, "reason": f"{path} does not exist"}
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle), None
    except (OSError, json.JSONDecodeError) as error:
        return None, {"section": section, "reason": f"{path} could not be read: {error}"}


def build_document(identity, probes, conan):
    """Assemble the manifest body. Sections are included only when they exist."""
    document = {"fields_version": FIELDS_VERSION, "identity": identity}
    if probes is not None:
        document["artifacts"] = probes
    if conan:
        document["conan"] = conan
    return document


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--identity", required=True, help="canonical identity document written by build_identity.py")
    parser.add_argument("--probes", help="provision document written by probe_artifact.py")
    parser.add_argument("--conan-identity", help="identity document written by the Conan generate step")
    parser.add_argument("--conan-packages", help="resolved Conan package set written by the Conan generate step")
    parser.add_argument("--out", required=True, help="path of the manifest to write")
    parser.add_argument("--print", action="store_true", help="also write the manifest to stdout")
    parser.add_argument(
        "--require-identity",
        action="store_true",
        help="fail when no identity is available; the store path uses this, a default build does not",
    )
    args = parser.parse_args(argv)

    omitted = []

    identity, omission = read_json(args.identity, "identity")
    if omission:
        omitted.append(omission)

    if identity is None and args.require_identity:
        print(
            f"no build identity is available ({omission['reason']}), and this configuration requires one",
            file=sys.stderr,
        )
        return 3

    probes, omission = read_json(args.probes, "probes")
    if omission:
        omitted.append(omission)

    conan = {}
    conan_identity, omission = read_json(args.conan_identity, "conan_identity")
    if omission:
        omitted.append(omission)
    else:
        conan["identity"] = conan_identity

    conan_packages, omission = read_json(args.conan_packages, "conan_packages")
    if omission:
        omitted.append(omission)
    else:
        conan["packages"] = conan_packages

    document = build_document(identity, probes, conan)
    if omitted:
        document["omitted"] = sorted(omitted, key=lambda entry: (entry["section"], entry["reason"]))

    body = json.dumps(document, indent=2, sort_keys=True) + "\n"
    try:
        directory = os.path.dirname(os.path.abspath(args.out))
        if directory:
            os.makedirs(directory, exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as handle:
            handle.write(body)
    except OSError as error:
        # A manifest that cannot be written must not fail a build.
        print(f"could not write the build manifest to {args.out}: {error}", file=sys.stderr)
        return 5

    for entry in omitted:
        _log(f"warning: manifest section '{entry['section']}' omitted: {entry['reason']}")

    if args.print:
        sys.stdout.write(body)
    return 0


if __name__ == "__main__":
    sys.exit(main())
