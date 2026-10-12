#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# *****************************************************************************
# Copyright 2026 Autodesk, Inc. All rights reserved.
#
# SPDX-License-Identifier: Apache-2.0
#
# *****************************************************************************

"""Self-verifying tests for build_manifest.py.

Run directly:

    python3 src/build/test_build_manifest.py

Exits non-zero if any check fails.
"""

import json
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "build_manifest.py")
IDENTITY_SCRIPT = os.path.join(HERE, "build_identity.py")

FAILURES = []

CREDENTIAL_RE = re.compile(r"(password|token|secret|authorization|api[-_]?key|credential)", re.IGNORECASE)


def check(description: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"  ok   {description}")
    else:
        print(f"  FAIL {description}{(': ' + detail) if detail else ''}")
        FAILURES.append(description)


def run(*args):
    return subprocess.run([sys.executable, SCRIPT, *args], capture_output=True, text=True)


def write_json(path: str, document) -> str:
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(document, handle, indent=2, sort_keys=True)
    return path


def make_identity(directory: str) -> str:
    inputs = os.path.join(directory, "identity.inputs")
    with open(inputs, "w", encoding="utf-8") as handle:
        handle.write(
            "vfx_platform=cy2025\ntarget_os=Linux\ntarget_arch=x86_64\ncompiler_id=GNU\n"
            "compiler_version=11.2.1\nstdlib=libstdc++11\ncxx_standard=17\nbuild_config=release\n"
            "python_version=3.11.9\nqt_version=6.5.3\n"
        )
    out = os.path.join(directory, "build-identity.json")
    subprocess.run(
        [sys.executable, IDENTITY_SCRIPT, "emit", "--inputs", inputs, "--out", out], check=True, capture_output=True
    )
    return out


def test_identity_only(directory: str) -> None:
    print("manifest with only an identity")
    identity = make_identity(directory)
    out = os.path.join(directory, "manifest.json")
    result = run("--identity", identity, "--out", out)
    check("the build continues", result.returncode == 0, f"exit {result.returncode}")
    check("the manifest exists", os.path.isfile(out))

    document = json.load(open(out, encoding="utf-8"))
    check("the manifest carries a schema version", document.get("fields_version") == 1)
    check(
        "the manifest embeds the full identity",
        document.get("identity", {}).get("compiler_id") == "gcc",
        str(document.get("identity")),
    )
    check(
        "absent sections are recorded rather than silently dropped",
        {entry["section"] for entry in document.get("omitted", [])} == {"probes", "conan_identity", "conan_packages"},
        str(document.get("omitted")),
    )


def test_full_manifest(directory: str) -> None:
    print("manifest with identity, artifacts and Conan packages")
    identity = make_identity(directory)
    probes = write_json(
        os.path.join(directory, "artifact-probes.json"),
        {
            "fields_version": 1,
            "probes": [{"role": "derived", "content_reference": "sha256:deadbeef", "path": "/x/libQt6Core.so.6.5.3"}],
        },
    )
    conan_identity = write_json(
        os.path.join(directory, "conan-identity.json"), {"compiler_id": "gcc", "compiler_version": "11"}
    )
    conan_packages = write_json(
        os.path.join(directory, "conan-packages.json"),
        {"packages": [{"name": "openexr", "version": "3.3.6", "package_id": "abc123"}]},
    )

    out = os.path.join(directory, "manifest_full.json")
    result = run(
        "--identity",
        identity,
        "--probes",
        probes,
        "--conan-identity",
        conan_identity,
        "--conan-packages",
        conan_packages,
        "--out",
        out,
    )
    check("the build continues", result.returncode == 0, f"exit {result.returncode}")

    document = json.load(open(out, encoding="utf-8"))
    check("the identity section is present", "identity" in document)
    check("the artifact section is present", "artifacts" in document)
    check("the Conan section is present", "conan" in document)
    check("the Conan package set is present", "packages" in document.get("conan", {}))
    check("the Conan identity is present", "identity" in document.get("conan", {}))
    check(
        "the artifact carries a content-derived reference",
        document["artifacts"]["probes"][0]["content_reference"].startswith("sha256:"),
        str(document["artifacts"]["probes"][0]),
    )
    check("nothing was omitted", "omitted" not in document, str(document.get("omitted")))


def test_determinism(directory: str) -> None:
    print("manifest is deterministic")
    identity = make_identity(directory)
    first = os.path.join(directory, "det1.json")
    second = os.path.join(directory, "det2.json")
    run("--identity", identity, "--out", first)
    run("--identity", identity, "--out", second)
    with open(first, "rb") as handle:
        body1 = handle.read()
    with open(second, "rb") as handle:
        body2 = handle.read()
    check("two configurations produce byte-identical manifests", body1 == body2)
    check("no timestamp is embedded", b"timestamp" not in body1 and b"generated" not in body1)


def test_write_failure_is_a_warning(directory: str) -> None:
    print("write failure")
    identity = make_identity(directory)
    # A regular file used as a directory component: this fails identically on
    # every platform, unlike a null byte in argv or a Windows-only drive letter.
    blocker = os.path.join(directory, "not-a-directory")
    with open(blocker, "w", encoding="utf-8") as handle:
        handle.write("\n")
    result = run("--identity", identity, "--out", os.path.join(blocker, "manifest.json"))
    check("an unwritable location is reported", result.returncode != 0, f"exit {result.returncode}")
    check(
        "the failure names the manifest",
        "manifest" in (result.stderr + result.stdout).lower(),
        (result.stderr + result.stdout).strip(),
    )
    check("the failure is not a crash", result.returncode == 5, f"exit {result.returncode}")


def test_missing_identity(directory: str) -> None:
    print("missing identity")
    out = os.path.join(directory, "no_identity.json")
    result = run("--identity", os.path.join(directory, "absent.json"), "--out", out)
    check("a default build continues", result.returncode == 0, f"exit {result.returncode}")
    check("a manifest is still written", os.path.isfile(out))
    document = json.load(open(out, encoding="utf-8"))
    check("the absent identity is recorded", document.get("identity") is None)
    check("the reason is recorded", any(entry["section"] == "identity" for entry in document.get("omitted", [])))

    required = os.path.join(directory, "no_identity_required.json")
    result = run("--identity", os.path.join(directory, "absent.json"), "--require-identity", "--out", required)
    check("a configuration requiring an identity fails", result.returncode == 3, f"exit {result.returncode}")
    check("the failure explains why", "identity" in result.stderr, result.stderr.strip())


def test_malformed_input_is_omitted(directory: str) -> None:
    print("malformed input")
    identity = make_identity(directory)
    broken = os.path.join(directory, "broken-probes.json")
    with open(broken, "w", encoding="utf-8") as handle:
        handle.write("{ this is not json")
    out = os.path.join(directory, "manifest_broken.json")
    result = run("--identity", identity, "--probes", broken, "--out", out)
    check("a malformed section does not fail the build", result.returncode == 0, f"exit {result.returncode}")
    document = json.load(open(out, encoding="utf-8"))
    check("the malformed section is omitted", "artifacts" not in document)
    check(
        "the omission is recorded with a reason",
        any(entry["section"] == "probes" for entry in document.get("omitted", [])),
    )


def test_no_credentials(directory: str) -> None:
    print("no credential material")
    identity = make_identity(directory)
    conan_packages = write_json(
        os.path.join(directory, "conan-packages.json"),
        {"packages": [{"name": "openexr", "version": "3.3.6", "package_id": "abc123", "remote": "aswf-conan"}]},
    )
    out = os.path.join(directory, "manifest_creds.json")
    run("--identity", identity, "--conan-packages", conan_packages, "--out", out)
    body = open(out, encoding="utf-8").read()

    def walk(node, path=""):
        found = []
        if isinstance(node, dict):
            for key, value in node.items():
                if CREDENTIAL_RE.search(key):
                    found.append(f"{path}.{key}")
                found += walk(value, f"{path}.{key}")
        elif isinstance(node, list):
            for index, value in enumerate(node):
                found += walk(value, f"{path}[{index}]")
        return found

    leaked = walk(json.loads(body))
    check("no credential-named field appears", not leaked, str(leaked))
    check("the remote name is kept, not its credentials", "aswf-conan" in body)


def main() -> int:
    if not os.path.isfile(SCRIPT):
        print(f"build_manifest.py not found at {SCRIPT}", file=sys.stderr)
        return 1

    with tempfile.TemporaryDirectory() as directory:
        test_identity_only(directory)
        test_full_manifest(directory)
        test_determinism(directory)
        test_write_failure_is_a_warning(directory)
        test_missing_identity(directory)
        test_malformed_input_is_omitted(directory)
        test_no_credentials(directory)

    print()
    if FAILURES:
        print(f"{len(FAILURES)} check(s) failed:")
        for failure in FAILURES:
            print(f"  - {failure}")
        return 1
    print("all build manifest checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
