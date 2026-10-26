#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# *****************************************************************************
# Copyright 2026 Autodesk, Inc. All rights reserved.
#
# SPDX-License-Identifier: Apache-2.0
#
# *****************************************************************************

"""Self-verifying tests for build_identity.py.

Run directly:

    python3 src/build/test_build_identity.py

Exits non-zero if any check fails. Follows the same standalone-script
convention as the other tests in this directory, so it can be invoked from
CMake or CI without a test framework.
"""

import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "build_identity.py")

FAILURES = []


def check(description: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"  ok   {description}")
    else:
        print(f"  FAIL {description}{(': ' + detail) if detail else ''}")
        FAILURES.append(description)


def write_inputs(directory: str, name: str, **overrides) -> str:
    fields = {
        "vfx_platform": "cy2025",
        "target_os": "Linux",
        "target_arch": "AMD64",
        "compiler_id": "GNU",
        "compiler_version": "11.2.1",
        "stdlib": "libstdc++",
        "cxx_standard": "gnu++17",
        "build_config": "release",
        "python_version": "3.11.9",
        "qt_version": "6.5.3",
    }
    fields.update(overrides)
    path = os.path.join(directory, name)
    with open(path, "w", encoding="utf-8") as handle:
        for key, value in fields.items():
            handle.write(f"{key}={value}\n")
    return path


def run(*args):
    return subprocess.run([sys.executable, SCRIPT, *args], capture_output=True, text=True)


def emit(directory: str, name: str, **overrides) -> dict:
    inputs = write_inputs(directory, name + ".inputs", **overrides)
    out = os.path.join(directory, name + ".json")
    result = run("emit", "--inputs", inputs, "--out", out)
    if result.returncode != 0:
        return {"__error__": result.stderr, "__code__": result.returncode}
    with open(out, "r", encoding="utf-8") as handle:
        return json.load(handle)


def test_normalization(directory: str) -> None:
    print("normalization")
    document = emit(directory, "base")
    expected = {
        "vfx_platform": "CY2025",
        "target_os": "linux",
        "target_arch": "x86_64",
        "compiler_id": "gcc",
        "compiler_version": "11.2.1",
        "stdlib": "libstdc++11",
        "cxx_standard": "17",
        "build_config": "Release",
        "python_abi": "3.11",
        "qt_version": "6.5.3",
        "fields_version": 2,
    }
    for field, value in expected.items():
        check(f"{field} normalized to {value!r}", document.get(field) == value, f"got {document.get(field)!r}")

    # The C runtime is a Windows-only axis, so it is absent here rather than set to a placeholder: a value would be read as a fact about the build.
    check("no C runtime is recorded on a non-Windows target", "crt" not in document, str(document.get("crt")))

    check(
        "identity carries a sha256 hash", str(document.get("hash", "")).startswith("sha256:"), str(document.get("hash"))
    )

    macos = emit(directory, "macos", target_os="Macos", compiler_id="AppleClang", stdlib="libc++", target_arch="arm64")
    check("macOS normalizes", macos.get("target_os") == "macos", str(macos.get("target_os")))
    check(
        "AppleClang normalizes to apple-clang", macos.get("compiler_id") == "apple-clang", str(macos.get("compiler_id"))
    )
    check("arm64 is preserved", macos.get("target_arch") == "arm64", str(macos.get("target_arch")))

    windows = emit(directory, "windows", target_os="Windows", compiler_id="MSVC", stdlib="msvc", target_arch="AMD64")
    check("Windows normalizes", windows.get("target_os") == "windows", str(windows.get("target_os")))
    check("MSVC normalizes to msvc", windows.get("compiler_id") == "msvc", str(windows.get("compiler_id")))


def test_python_series_granularity(directory: str) -> None:
    print("python identity is ABI-series granular")
    a = emit(directory, "py1", python_version="3.11.9")
    b = emit(directory, "py2", python_version="3.11.14")
    check("3.11.9 and 3.11.14 share a python_abi", a.get("python_abi") == b.get("python_abi") == "3.11")
    check("3.11.9 and 3.11.14 produce an equal identity", a == b, "identities differ across a patch release")

    c = emit(directory, "py3", python_version="3.12.0")
    check("a series change produces a different identity", c.get("hash") != a.get("hash"))
    check("a series change is visible in python_abi", c.get("python_abi") == "3.12")


def test_build_configuration_distinguishes_identity(directory: str) -> None:
    print("Release and Debug identities are distinct")
    release = emit(directory, "rel", build_config="release")
    debug = emit(directory, "dbg", build_config="Debug")
    check("build_config is recorded", release.get("build_config") == "Release" and debug.get("build_config") == "Debug")
    check("Release and Debug hashes differ", release.get("hash") != debug.get("hash"))
    check(
        "only build_config differs",
        {k: v for k, v in release.items() if k != "hash" and k != "build_config"}
        == {k: v for k, v in debug.items() if k != "hash" and k != "build_config"},
    )


def test_c_runtime(directory: str) -> None:
    print("C runtime")
    cases = [
        ("dynamic:Debug", "dynamic-debug"),
        ("dynamic:Release", "dynamic"),
        ("static:Debug", "static-debug"),
        ("static:Release", "static"),
        ("dynamic-debug", "dynamic-debug"),
        ("MultiThreadedDebugDLL", "MultiThreadedDebugDLL"),
    ]
    for raw, expected in cases:
        document = emit(directory, "crt-" + raw.replace(":", "-"), target_os="Windows", crt=raw)
        check(
            f"crt={raw!r} normalizes to {expected!r}", document.get("crt") == expected, f"got {document.get('crt')!r}"
        )

    # The case the field exists for: same configuration, same compiler, different runtime. Before the
    # field existed these two produced the same identity, so one could be handed the other's
    # artifacts, which on MSVC is a link error at best and two heaps holding the same pointer at
    # worst.
    dynamic = emit(
        directory,
        "crt-dyn",
        target_os="Windows",
        compiler_id="msvc",
        stdlib="msvc",
        build_config="Release",
        crt="dynamic:Release",
    )
    static = emit(
        directory,
        "crt-stat",
        target_os="Windows",
        compiler_id="msvc",
        stdlib="msvc",
        build_config="Release",
        crt="static:Release",
    )
    check("the dynamic runtime is recorded", dynamic.get("crt") == "dynamic")
    check("the static runtime is recorded", static.get("crt") == "static")
    check("the two produce different identities", dynamic.get("hash") != static.get("hash"))

    # The debug runtime is distinguished from the release one within each kind, independently of the
    # configuration name that usually implies it.
    debug_runtime = emit(
        directory,
        "crt-dbg",
        target_os="Windows",
        compiler_id="msvc",
        stdlib="msvc",
        build_config="Release",
        crt="dynamic:Debug",
    )
    check("the debug runtime is recorded", debug_runtime.get("crt") == "dynamic-debug")
    check(
        "a Release build linking the debug runtime differs from one linking the release runtime",
        debug_runtime.get("hash") != dynamic.get("hash"),
    )


def test_determinism(directory: str) -> None:
    print("determinism")
    first = emit(directory, "det1")
    second = emit(directory, "det2")
    check("equal inputs produce an equal hash", first.get("hash") == second.get("hash"))

    with open(os.path.join(directory, "det1.json"), "rb") as handle:
        body1 = handle.read()
    with open(os.path.join(directory, "det2.json"), "rb") as handle:
        body2 = handle.read()
    check("the emitted document is byte-identical for equal inputs", body1 == body2)


def test_unsupported_platform(directory: str) -> None:
    print("unsupported platform")
    inputs = write_inputs(directory, "plan9.inputs", target_os="Plan9")
    result = run("emit", "--inputs", inputs, "--out", os.path.join(directory, "plan9.json"))
    check("configuration fails", result.returncode == 3, f"exit {result.returncode}")
    check("the message names the unsupported platform", "Plan9" in result.stderr, result.stderr.strip())

    missing = write_inputs(directory, "missing.inputs")
    with open(missing, "a", encoding="utf-8") as handle:
        pass
    with open(missing, "r", encoding="utf-8") as handle:
        lines = [line for line in handle if not line.startswith("qt_version") and not line.startswith("compiler_id")]
    with open(missing, "w", encoding="utf-8") as handle:
        handle.writelines(lines)
    result = run("emit", "--inputs", missing, "--out", os.path.join(directory, "missing.json"))
    check("a missing required input fails", result.returncode != 0)
    # Exit 3 is the one CMake turns into a fatal error. A missing or malformed input means the identity
    # cannot be computed, not that the platform cannot be built, so it must never be reported as 3.
    check("a missing required input is not an unsupported target", result.returncode == 6, f"exit {result.returncode}")
    check("the message names the missing field", "compiler_id" in result.stderr, result.stderr.strip())

    malformed = write_inputs(directory, "malformed.inputs", python_version="unknown", cxx_standard="latest")
    result = run("emit", "--inputs", malformed, "--out", os.path.join(directory, "malformed.json"))
    check("a malformed input is not an unsupported target", result.returncode == 6, f"exit {result.returncode}")


def test_compare(directory: str) -> None:
    print("compare")
    computed = os.path.join(directory, "base.json")
    # A Conan profile expresses only the compiler major.
    conan_match = os.path.join(directory, "conan_match.json")
    inputs = write_inputs(directory, "cm.inputs", compiler_version="11")
    run("emit", "--inputs", inputs, "--out", conan_match)
    result = run("compare", "--left", computed, "--right", conan_match)
    check(
        "a coarse profile matching the compiler major is accepted",
        result.returncode == 0,
        result.stdout.strip() + result.stderr.strip(),
    )

    conan_drift = os.path.join(directory, "conan_drift.json")
    inputs = write_inputs(directory, "cd.inputs", compiler_version="13", cxx_standard="gnu++20")
    run("emit", "--inputs", inputs, "--out", conan_drift)
    result = run("compare", "--left", computed, "--right", conan_drift)
    check("drift is reported", result.returncode == 2, f"exit {result.returncode}")
    check("the report names compiler_version", "compiler_version" in result.stdout, result.stdout.strip())
    check("the report names cxx_standard", "cxx_standard" in result.stdout, result.stdout.strip())
    check("the report shows both sides", "11.2.1" in result.stdout and "13" in result.stdout, result.stdout.strip())

    result = run("compare", "--left", computed, "--right", conan_match, "--version-granularity", "exact")
    check("exact granularity surfaces the coarse profile", result.returncode == 2, f"exit {result.returncode}")

    # MSVC: CMake reports 19.44.35229.0, a Conan profile states the toolset series 194.
    msvc = dict(target_os="Windows", compiler_id="MSVC", stdlib="msvc", crt="dynamic:release")
    msvc_computed = os.path.join(directory, "msvc_computed.json")
    run(
        "emit",
        "--inputs",
        write_inputs(directory, "mc.inputs", compiler_version="19.44.35229.0", **msvc),
        "--out",
        msvc_computed,
    )
    msvc_profile = os.path.join(directory, "msvc_profile.json")
    run("emit", "--inputs", write_inputs(directory, "mp.inputs", compiler_version="194", **msvc), "--out", msvc_profile)
    result = run("compare", "--left", msvc_computed, "--right", msvc_profile)
    check("an MSVC 19.44 compiler matches a 194 profile", result.returncode == 0, result.stdout.strip())
    msvc_older = os.path.join(directory, "msvc_older.json")
    run("emit", "--inputs", write_inputs(directory, "mo.inputs", compiler_version="193", **msvc), "--out", msvc_older)
    result = run("compare", "--left", msvc_computed, "--right", msvc_older)
    check("an MSVC 19.44 compiler does not match a 193 profile", result.returncode == 2, result.stdout.strip())


def test_partial_emission(directory: str) -> None:
    print("partial emission (a Conan profile knows only part of the identity)")
    inputs = os.path.join(directory, "profile.inputs")
    with open(inputs, "w", encoding="utf-8") as handle:
        handle.write(
            "vfx_platform=CY2025\ntarget_os=Linux\ntarget_arch=x86_64\ncompiler_id=gcc\n"
            "compiler_version=11\nstdlib=libstdc++11\ncxx_standard=17\nbuild_config=Release\n"
        )
    out = os.path.join(directory, "partial.json")
    result = run("emit", "--inputs", inputs, "--partial", "--out", out)
    check("a profile missing Python and Qt still emits", result.returncode == 0, result.stderr.strip())

    document = json.load(open(out, encoding="utf-8"))
    check("the document is marked partial", document.get("partial") == "true", str(document.get("partial")))
    check("the Python ABI series is not guessed", "python_abi" not in document, str(document))
    check("the Qt version is not guessed", "qt_version" not in document, str(document))
    check(
        "the fields a profile does know are normalized",
        document.get("target_os") == "linux",
        str(document.get("target_os")),
    )

    full = os.path.join(directory, "base.json")
    result = run("compare", "--left", full, "--right", out)
    check("a matching profile compares equal", result.returncode == 0, result.stdout.strip())

    drifted = os.path.join(directory, "partial_drift.json")
    with open(inputs, "w", encoding="utf-8") as handle:
        handle.write(
            "compiler_id=gcc\ncompiler_version=13\ncxx_standard=17\nbuild_config=Release\ntarget_os=Linux\ntarget_arch=x86_64\n"
        )
    run("emit", "--inputs", inputs, "--partial", "--out", drifted)
    result = run("compare", "--left", full, "--right", drifted)
    check("drift is still detected through a partial document", result.returncode == 2, f"exit {result.returncode}")
    check("the drift report names compiler_version", "compiler_version" in result.stdout, result.stdout.strip())

    # A profile that does not state a setting is saying "use the default", not "I disagree".
    # Reporting that as drift would make the report noisy and therefore ignored.
    silent = os.path.join(directory, "partial_silent.json")
    with open(inputs, "w", encoding="utf-8") as handle:
        handle.write(
            "compiler_id=gcc\ncompiler_version=11\nbuild_config=Release\ntarget_os=Linux\ntarget_arch=x86_64\n"
        )
    run("emit", "--inputs", inputs, "--partial", "--out", silent)
    result = run("compare", "--left", full, "--right", silent)
    check(
        "an unstated field is not reported as drift",
        result.returncode == 0,
        f"exit {result.returncode}: {result.stdout.strip()}",
    )
    check(
        "the unstated field is named as not compared",
        "cxx_standard" in result.stdout and "not stated" in result.stdout,
        result.stdout.strip(),
    )

    # Skipping unstated fields must not soften a field that IS stated and differs.
    stated_drift = os.path.join(directory, "partial_stated_drift.json")
    with open(inputs, "w", encoding="utf-8") as handle:
        handle.write(
            "compiler_id=gcc\ncompiler_version=13\nbuild_config=Release\ntarget_os=Linux\ntarget_arch=x86_64\n"
        )
    run("emit", "--inputs", inputs, "--partial", "--out", stated_drift)
    result = run("compare", "--left", full, "--right", stated_drift)
    check("a stated field that differs is still reported", result.returncode == 2, f"exit {result.returncode}")
    check("the stated drift is named", "compiler_version" in result.stdout, result.stdout.strip())


def main() -> int:
    if not os.path.isfile(SCRIPT):
        print(f"build_identity.py not found at {SCRIPT}", file=sys.stderr)
        return 1

    with tempfile.TemporaryDirectory() as directory:
        test_normalization(directory)
        test_python_series_granularity(directory)
        test_build_configuration_distinguishes_identity(directory)
        test_c_runtime(directory)
        test_determinism(directory)
        test_unsupported_platform(directory)
        test_compare(directory)
        test_partial_emission(directory)

    print()
    if FAILURES:
        print(f"{len(FAILURES)} check(s) failed:")
        for failure in FAILURES:
            print(f"  - {failure}")
        return 1
    print("all build identity checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
