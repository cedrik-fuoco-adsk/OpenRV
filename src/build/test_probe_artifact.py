#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# *****************************************************************************
# Copyright 2026 Autodesk, Inc. All rights reserved.
#
# SPDX-License-Identifier: Apache-2.0
#
# *****************************************************************************

"""Self-verifying tests for probe_artifact.py.

Run directly:

    python3 src/build/test_probe_artifact.py

Exits non-zero if any check fails. Container formats are covered with minimal
synthesized artifacts so the header parsing is tested on every platform; the
tool-backed ABI facts are covered with real artifacts cross-compiled by clang
and with a system binary, and skipped with a notice where those are unavailable.
"""

import importlib.util
import json
import os
import shutil
import struct
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "probe_artifact.py")

FAILURES = []
SKIPPED = []


def check(description: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"  ok   {description}")
    else:
        print(f"  FAIL {description}{(': ' + detail) if detail else ''}")
        FAILURES.append(description)


def skip(description: str, why: str) -> None:
    print(f"  skip {description} ({why})")
    SKIPPED.append(description)


def load_module():
    spec = importlib.util.spec_from_file_location("probe_artifact", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run(*args):
    return subprocess.run([sys.executable, SCRIPT, *args], capture_output=True, text=True)


# --- synthesized minimal containers -----------------------------------------


def synth_elf(path: str, e_type: int) -> str:
    header = b"\x7fELF" + bytes([2, 1, 1, 0]) + b"\x00" * 8
    with open(path, "wb") as handle:
        handle.write(header + struct.pack("<H", e_type) + b"\x00" * 64)
    return path


def synth_macho(path: str, filetype: int, big_endian: bool = False) -> str:
    magic = b"\xfe\xed\xfa\xcf" if big_endian else b"\xcf\xfa\xed\xfe"
    with open(path, "wb") as handle:
        handle.write(magic + b"\x00" * 8 + struct.pack(">I" if big_endian else "<I", filetype) + b"\x00" * 64)
    return path


def synth_pe(path: str, is_dll: bool) -> str:
    pe_offset = 0x80
    data = bytearray(b"MZ" + b"\x00" * (pe_offset - 2))
    data[0x3C:0x40] = struct.pack("<I", pe_offset)
    data += b"PE\x00\x00" + b"\x00" * 18 + struct.pack("<H", 0x2000 if is_dll else 0x0000)
    with open(path, "wb") as handle:
        handle.write(bytes(data))
    return path


def probe_document(directory: str, name: str, artifacts) -> dict:
    out = os.path.join(directory, f"{name}.json")
    args = ["probe"]
    for role, path in artifacts:
        args += ["--artifact", f"{role}={path}"]
    args += ["--out", out]
    result = run(*args)
    if result.returncode != 0:
        return {"__error__": result.stderr, "__code__": result.returncode}
    with open(out, "r", encoding="utf-8") as handle:
        return json.load(handle)


# --- tests ------------------------------------------------------------------


def test_container_headers(directory: str) -> None:
    print("container headers, linkage and endianness")
    artifacts = [
        ("shared-elf", synth_elf(os.path.join(directory, "libshared.so.3.2.1"), 3)),
        ("static-elf", synth_elf(os.path.join(directory, "libstatic.a"), 1)),
        ("dylib-macho", synth_macho(os.path.join(directory, "libthing.dylib"), 6)),
        ("object-macho", synth_macho(os.path.join(directory, "thing.o"), 1)),
        ("dylib-macho-be", synth_macho(os.path.join(directory, "libbe.dylib"), 6, big_endian=True)),
        ("dll-pe", synth_pe(os.path.join(directory, "thing.dll"), True)),
        ("exe-pe", synth_pe(os.path.join(directory, "thing.exe"), False)),
    ]
    document = probe_document(directory, "containers", artifacts)
    probes = {probe["role"]: probe for probe in document.get("probes", [])}

    expected = {
        "shared-elf": ("elf", "shared"),
        "static-elf": ("elf", "static"),
        "dylib-macho": ("macho", "shared"),
        "object-macho": ("macho", "static"),
        "dylib-macho-be": ("macho", "shared"),
        "dll-pe": ("pe", "shared"),
        "exe-pe": ("pe", "executable"),
    }
    for role, (fmt, linkage) in expected.items():
        probe = probes.get(role, {})
        check(f"{role} detected as {fmt}", probe.get("format") == fmt, str(probe.get("format")))
        check(
            f"{role} linkage is {linkage}",
            probe.get("linkage", {}).get("type") == linkage,
            str(probe.get("linkage", {}).get("type")),
        )

    check(
        "big-endian Mach-O reports the same linkage as little-endian",
        probes["dylib-macho-be"].get("linkage", {}).get("type") == probes["dylib-macho"].get("linkage", {}).get("type"),
        "endianness is being read the wrong way round",
    )
    check(
        "version is read from a shared library filename",
        probes["shared-elf"].get("version", {}).get("value") == "3.2.1",
        str(probes["shared-elf"].get("version")),
    )


def test_unknown_is_recorded_not_omitted(directory: str) -> None:
    print("undeterminable facts are recorded as unknown")
    garbage = os.path.join(directory, "garbage.bin")
    with open(garbage, "wb") as handle:
        handle.write(os.urandom(512))

    result = run("probe", "--artifact", f"derived={garbage}", "--out", os.path.join(directory, "junk.json"))
    check("an unreadable artifact is not an error", result.returncode == 0, f"exit {result.returncode}")

    document = probe_document(directory, "junk2", [("derived", garbage)])
    probe = document["probes"][0]
    for category in ("linkage", "version", "features", "abi_demands"):
        entry = probe.get(category, {})
        check(f"{category} is present and marked unknown", entry.get("known") is False, str(entry))
        check(f"{category} carries a reason", bool(entry.get("reason")), str(entry))


def test_input_and_derived_are_separate(directory: str) -> None:
    print("input and derived artifacts are probed and retained separately")
    # Deliberately different content: an ingested shared library and a derived
    # artifact that differs from it. Identical content is covered separately,
    # where sharing a reference is the correct behaviour.
    ingested = synth_elf(os.path.join(directory, "libinput.so.1.0.0"), 3)
    derived = synth_elf(os.path.join(directory, "libderived.so.1.0.0"), 1)
    document = probe_document(directory, "pair", [("input", ingested), ("derived", derived)])

    roles = sorted(probe["role"] for probe in document["probes"])
    check("both roles are retained", roles == ["derived", "input"], str(roles))
    paths = {probe["role"]: probe["path"] for probe in document["probes"]}
    check("the input path is recorded", paths.get("input", "").endswith("libinput.so.1.0.0"), str(paths))
    check("the derived path is recorded", paths.get("derived", "").endswith("libderived.so.1.0.0"), str(paths))
    check(
        "differing content yields differing references",
        len({probe["content_reference"] for probe in document["probes"]}) == 2,
    )
    by_role = {probe["role"]: probe for probe in document["probes"]}
    check(
        "the input and derived facts are recorded independently",
        by_role["input"]["linkage"]["type"] != by_role["derived"]["linkage"]["type"],
        f"{by_role['input']['linkage']['type']} vs {by_role['derived']['linkage']['type']}",
    )


def test_content_reference(directory: str) -> None:
    print("content-derived references")
    original = synth_elf(os.path.join(directory, "liborig.so.1.0.0"), 3)
    copy = os.path.join(directory, "elsewhere", "liborig.so.1.0.0")
    os.makedirs(os.path.dirname(copy), exist_ok=True)
    shutil.copyfile(original, copy)

    document = probe_document(directory, "same", [("input", original), ("derived", copy)])
    references = {probe["content_reference"] for probe in document["probes"]}
    paths = {probe["path"] for probe in document["probes"]}
    check(
        "identical content at different paths shares one reference",
        len(references) == 1 and len(paths) == 2,
        str(references),
    )
    check(
        "an input and a derived artifact with identical content share a reference",
        len(document["probes"]) == 2 and len(references) == 1,
        "content addressing must be independent of role",
    )

    changed = os.path.join(directory, "liborig.so.1.0.1")
    synth_elf(changed, 1)
    other = probe_document(directory, "different", [("derived", changed)])
    check("different content produces a different reference", other["probes"][0]["content_reference"] not in references)


def test_probe_cache(directory: str) -> None:
    print("probe results are cached by artifact content")
    # A file of no known container format: its facts are unknown for a reason that is about the file,
    # not about the host, so it is cached on every host. A synthetic ELF would not be -- on a host without
    # readelf, or where readelf rejects it, the result is retryable and deliberately not cached.
    artifact = os.path.join(directory, "libcached.so.2.0.0")
    with open(artifact, "wb") as handle:
        handle.write(b"not a container" * 8)
    cache = os.path.join(directory, "cache")

    first = probe_document_cached(directory, "cache1", artifact, cache)
    second = probe_document_cached(directory, "cache2", artifact, cache)
    check(
        "first probe inspects the artifact",
        first["probes"][0]["inspection"] == "performed",
        str(first["probes"][0]["inspection"]),
    )
    check(
        "second probe reuses the cached result",
        second["probes"][0]["inspection"] == "cached",
        str(second["probes"][0]["inspection"]),
    )

    with open(artifact, "ab") as handle:
        handle.write(b"changed")
    third = probe_document_cached(directory, "cache3", artifact, cache)
    check(
        "a changed artifact is inspected again",
        third["probes"][0]["inspection"] == "performed",
        str(third["probes"][0]["inspection"]),
    )


def test_retryable_results_are_not_cached(directory: str) -> None:
    print("an inspection that did not happen is not cached")
    module = load_module()
    artifact = synth_pe(os.path.join(directory, "retry.dll"), True)
    cache = os.path.join(directory, "retry-cache")

    original_which = module.shutil.which
    try:
        module.shutil.which = lambda name, *args, **kwargs: None
        out = os.path.join(directory, "retry1.json")
        code = module.main(["probe", "--artifact", f"derived={artifact}", "--cache-dir", cache, "--out", out])
        check("a probe without its tool still succeeds", code == 0, str(code))
        entries = os.listdir(cache) if os.path.isdir(cache) else []
        check("a result with a missing tool is not cached", entries == [], str(entries))

        # Plant what an earlier probe, or an earlier version of this one, might have left: a cached
        # result whose ABI demands are unknown because the tool was missing.
        with open(out, "r", encoding="utf-8") as handle:
            planted = json.load(handle)["probes"][0]
        observed = {key: planted[key] for key in ("format", "linkage", "version", "features", "abi_demands")}
        os.makedirs(cache, exist_ok=True)
        reference = module.content_reference(artifact)
        with open(module._cache_path(cache, reference, None), "w", encoding="utf-8") as handle:
            json.dump(observed, handle)

        strict_out = os.path.join(directory, "retry-strict.json")
        code = module.main(
            ["probe", "--artifact", f"derived={artifact}", "--cache-dir", cache, "--strict", "--out", strict_out]
        )
        check("a strict probe is not satisfied by a cached unknown", code == 5, str(code))
    finally:
        module.shutil.which = original_which


def test_metadata_root_is_per_artifact(directory: str) -> None:
    print("a metadata root belongs to one artifact")
    qt = os.path.join(directory, "qt")
    os.makedirs(os.path.join(qt, "mkspecs"))
    with open(os.path.join(qt, "mkspecs", "qconfig.pri"), "w", encoding="utf-8") as handle:
        handle.write("QT_VERSION = 6.5.3\nQT_CONFIG += opengl ssl\n")
    os.makedirs(os.path.join(qt, "lib"))
    qtcore = synth_elf(os.path.join(qt, "lib", "libQt6Core.so.6"), 3)
    zlib_dir = os.path.join(directory, "zlib", "lib")
    os.makedirs(zlib_dir)
    zlib = synth_elf(os.path.join(zlib_dir, "libz.so.1.3.1"), 3)
    cache = os.path.join(directory, "root-cache")

    def probes(name):
        out = os.path.join(directory, f"{name}.json")
        result = run(
            "probe",
            "--artifact",
            f"input={qtcore}",
            "--artifact-metadata-root",
            qtcore,
            qt,
            "--artifact",
            f"input={zlib}",
            "--cache-dir",
            cache,
            "--out",
            out,
        )
        if result.returncode != 0:
            return {}
        with open(out, "r", encoding="utf-8") as handle:
            return {os.path.basename(probe["path"]): probe for probe in json.load(handle)["probes"]}

    document = probes("roots")
    check(
        "Qt's version is read from Qt's root",
        document.get("libQt6Core.so.6", {}).get("version", {}).get("value") == "6.5.3",
        str(document.get("libQt6Core.so.6", {}).get("version")),
    )
    zlib_probe = document.get("libz.so.1.3.1", {})
    check(
        "another input artifact does not inherit Qt's version",
        zlib_probe.get("version", {}).get("value") == "1.3.1",
        str(zlib_probe.get("version")),
    )
    check(
        "another input artifact does not inherit Qt's features",
        not zlib_probe.get("features", {}).get("known"),
        str(zlib_probe.get("features")),
    )

    module = load_module()
    reference = module.content_reference(qtcore)
    check(
        "the metadata root is part of the cache key",
        module._cache_path(cache, reference, qt) != module._cache_path(cache, reference, None),
    )


def probe_document_cached(directory: str, name: str, artifact: str, cache: str) -> dict:
    out = os.path.join(directory, f"{name}.json")
    result = run("probe", "--artifact", f"derived={artifact}", "--cache-dir", cache, "--out", out)
    if result.returncode != 0:
        return {"__error__": result.stderr, "__code__": result.returncode}
    with open(out, "r", encoding="utf-8") as handle:
        return json.load(handle)


def test_probing_does_not_modify(directory: str) -> None:
    print("probing does not modify the artifact")
    artifact = synth_elf(os.path.join(directory, "libreadonly.so.1.0.0"), 3)
    with open(artifact, "rb") as handle:
        before = handle.read()
    probe_document(directory, "readonly", [("derived", artifact)])
    with open(artifact, "rb") as handle:
        after = handle.read()
    check("artifact bytes are unchanged", before == after)


def test_requirement_comparison(directory: str) -> None:
    print("provision versus requirement")
    artifact = synth_elf(os.path.join(directory, "libcompare.so.4.1.0"), 3)
    provision = os.path.join(directory, "prov.json")
    run("probe", "--artifact", f"derived={artifact}", "--out", provision)

    def compare(requirements):
        requirement_path = os.path.join(directory, "req.json")
        with open(requirement_path, "w", encoding="utf-8") as handle:
            json.dump({"fields_version": 1, "requirements": requirements}, handle)
        return run("compare", "--provision", provision, "--requirement", requirement_path)

    result = compare([{"kind": "linkage", "value": "shared"}, {"kind": "version", "min_version": "4.1.0"}])
    check("an exact match is accepted", result.returncode == 0, result.stdout.strip() + result.stderr.strip())

    result = compare([{"kind": "linkage", "value": "shared"}])
    check("a strict superset is accepted", result.returncode == 0, result.stdout.strip() + result.stderr.strip())

    result = compare([{"kind": "linkage", "value": "static"}])
    check("a missing requirement is rejected", result.returncode == 2, f"exit {result.returncode}")

    result = compare([{"kind": "version", "min_version": "9.0.0"}, {"kind": "feature", "value": "opengl"}])
    check("the diagnostic names the version requirement", "9.0.0" in result.stdout, result.stdout.strip())
    check("the diagnostic names the provided version", "4.1.0" in result.stdout, result.stdout.strip())
    check("the diagnostic names the artifact", "libcompare" in result.stdout, result.stdout.strip())
    check("the diagnostic names the feature requirement", "opengl" in result.stdout, result.stdout.strip())

    result = compare([{"kind": "symbol_version", "namespace": "GLIBCXX", "min_version": "3.4.29"}])
    check("an unsatisfied symbol namespace is rejected", result.returncode == 2, f"exit {result.returncode}")

    document = json.loads(open(provision, "r", encoding="utf-8").read())
    document["probes"][0]["version"] = {"known": False, "values": [], "reason": "synthetic"}
    unknown_path = os.path.join(directory, "prov_unknown.json")
    with open(unknown_path, "w", encoding="utf-8") as handle:
        json.dump(document, handle)
    requirement_path = os.path.join(directory, "req_v.json")
    with open(requirement_path, "w", encoding="utf-8") as handle:
        json.dump({"requirements": [{"kind": "version", "min_version": "1.0.0"}]}, handle)
    result = run("compare", "--provision", unknown_path, "--requirement", requirement_path)
    check("an unknown fact never satisfies a requirement", result.returncode == 2, f"exit {result.returncode}")
    check("the diagnostic says the fact is unknown", "unknown" in result.stdout, result.stdout.strip())


def test_missing_tool_behaviour(directory: str) -> None:
    print("missing inspection tool")
    module = load_module()
    artifact = synth_pe(os.path.join(directory, "toolcheck.dll"), True)

    original_which = shutil.which
    try:
        module.shutil.which = lambda name, *args, **kwargs: None

        demands = module._abi_demands_pe(artifact, strict=False)
        check("non-strict records unknown instead of failing", demands.get("known") is False, str(demands))
        check("non-strict records why", "PATH" in str(demands.get("reason", "")), str(demands))

        raised = False
        try:
            module._abi_demands_pe(artifact, strict=True)
        except module.MissingToolError as error:
            raised = True
            check("strict names the missing tool", "dumpbin" in str(error) or "llvm-readobj" in str(error), str(error))
        check("strict fails rather than recording unknown", raised)

        out = os.path.join(directory, "strict.json")
        code = module.main(["probe", "--artifact", f"derived={artifact}", "--strict", "--out", out])
        check("strict probing exits non-zero", code == 5, str(code))
    finally:
        module.shutil.which = original_which


def test_available_tools_against_real_artifacts(directory: str) -> None:
    print("tool-backed facts against real artifacts")
    clang = shutil.which("clang")
    source = os.path.join(directory, "fixture.c")
    with open(source, "w", encoding="utf-8") as handle:
        handle.write("int rv_fixture(int x) { return x + 1; }\n")

    if clang:
        elf_object = os.path.join(directory, "fixture_elf.o")
        result = subprocess.run(
            [clang, "--target=x86_64-unknown-linux-gnu", "-c", "-o", elf_object, source], capture_output=True, text=True
        )
        if result.returncode == 0:
            document = probe_document(directory, "real_elf", [("derived", elf_object)])
            probe = document["probes"][0]
            check("a real ELF object is detected", probe["format"] == "elf", str(probe["format"]))
            check("a real ELF object is linked statically", probe["linkage"]["type"] == "static", str(probe["linkage"]))
        else:
            skip("real ELF artifact", "clang could not cross-compile")

        macho_object = os.path.join(directory, "fixture_macho.o")
        result = subprocess.run(
            [clang, "--target=arm64-apple-macos11", "-c", "-o", macho_object, source], capture_output=True, text=True
        )
        if result.returncode == 0:
            document = probe_document(directory, "real_macho", [("derived", macho_object)])
            probe = document["probes"][0]
            check("a real Mach-O object is detected", probe["format"] == "macho", str(probe["format"]))
            check(
                "a real Mach-O object is linked statically", probe["linkage"]["type"] == "static", str(probe["linkage"])
            )
        else:
            skip("real Mach-O artifact", "clang could not cross-compile")
    else:
        skip("real ELF and Mach-O artifacts", "clang is not available")

    system_pe = None
    if os.name == "nt":
        for candidate in (r"C:\Windows\System32\ucrtbase.dll", r"C:\Windows\System32\kernel32.dll"):
            if os.path.isfile(candidate):
                system_pe = candidate
                break
    if system_pe:
        document = probe_document(directory, "real_pe", [("derived", system_pe)])
        probe = document["probes"][0]
        check("a real PE image is detected", probe["format"] == "pe", str(probe["format"]))
        check("a real PE image is shared", probe["linkage"]["type"] == "shared", str(probe["linkage"]))

        # The release/debug decision for PE is inferred from the C runtime import set, so it needs a reader. Without one
        # the configuration is unknown, which is the documented degradation rather than a defect.
        pe_reader = shutil.which("dumpbin") or shutil.which("llvm-readobj")
        if pe_reader:
            check(
                "a real PE image reports a release configuration",
                probe["linkage"]["config"] == "release",
                str(probe["linkage"]),
            )
            check(
                "a real PE image reports its runtime imports",
                bool(probe["abi_demands"].get("values")),
                str(probe["abi_demands"]),
            )
        else:
            check(
                "without a PE reader the linkage configuration degrades to unknown",
                probe["linkage"]["config"] == "unknown",
                str(probe["linkage"]),
            )
            skip("PE runtime imports", "no dumpbin or llvm-readobj on PATH")
    else:
        skip("real PE artifact", "no system PE image available")


def test_framework_directory_is_resolved(directory: str) -> None:
    print("a macOS framework directory resolves to the binary inside it")
    clang = shutil.which("clang")
    source = os.path.join(directory, "framework.c")
    with open(source, "w", encoding="utf-8") as handle:
        handle.write("int rv_framework(int x) { return x * 2; }\n")

    framework = os.path.join(directory, "QtCore.framework")
    inner = os.path.join(framework, "Versions", "A")
    os.makedirs(inner, exist_ok=True)
    binary = os.path.join(inner, "QtCore")

    if (
        clang
        and subprocess.run(
            [clang, "--target=arm64-apple-macos11", "-shared", "-fuse-ld=lld", "-nostdlib", "-o", binary, source],
            capture_output=True,
        ).returncode
        == 0
    ):
        document = probe_document(directory, "framework", [("input", framework)])
        probe = document["probes"][0]
        check("the framework is not recorded as missing", probe.get("content_reference") is not None, str(probe))
        check(
            "the framework binary is what was probed",
            probe["path"].endswith(os.path.join("Versions", "A", "QtCore")),
            probe["path"],
        )
        check("the framework binary is detected as Mach-O", probe["format"] == "macho", str(probe["format"]))
        check("a framework dylib is shared", probe["linkage"]["type"] == "shared", str(probe["linkage"]))

        # The minimum-OS floor must come only from the load command that defines it. A loose match also picks up unrelated
        # "version" fields such as the linker's own version, and because a requirement is checked against the highest
        # candidate, that would make every platform-floor requirement pass spuriously.
        #
        # Only asserted when a Mach-O reader is actually available: a host with clang but no otool or llvm-objdump can build
        # the fixture yet cannot read its load commands, and recording the fact as unknown is the documented behaviour there.
        macho_reader = shutil.which("otool") or shutil.which("llvm-objdump")
        if macho_reader:
            floors = [
                entry for entry in probe["abi_demands"].get("values", []) if entry.get("kind") == "platform-floor"
            ]
            check("exactly one platform floor is reported", len(floors) == 1, str(floors))
            check(
                "the platform floor is the minimum OS, not the linker version",
                bool(floors) and floors[0]["version"].startswith("11"),
                str(floors),
            )
        else:
            check(
                "without a Mach-O reader the floor degrades to unknown rather than being invented",
                probe["abi_demands"].get("known") is False,
                str(probe["abi_demands"]),
            )
            skip("platform floor value", "no otool or llvm-objdump on PATH")
    else:
        # Even without clang, a directory must not be reported as a missing artifact in a way that hides the problem.
        document = probe_document(directory, "framework_nobinary", [("input", framework)])
        probe = document["probes"][0]
        check(
            "a framework without a binary is recorded as unknown rather than crashing",
            probe["features"].get("known") is False,
        )
        skip("real framework binary", "clang could not build a Mach-O dylib")


def test_version_name_parsing(directory: str) -> None:
    print("ELF version names split into namespace and version")
    module = load_module()

    # A version name carries both, e.g. GLIBCXX_3.4.29. Reading the readelf row the other way
    # round records the table index as the version and the whole name as the namespace, which
    # makes every namespace requirement miss.
    cases = {
        "GLIBCXX_3.4.29": ("GLIBCXX", "3.4.29"),
        "GLIBC_2.2.5": ("GLIBC", "2.2.5"),
        "CXXABI_1.3.8": ("CXXABI", "1.3.8"),
        "GCC_4.2.0": ("GCC", "4.2.0"),
        "GLIBCXX_DEBUG_3.4": ("GLIBCXX_DEBUG", "3.4"),
    }
    for name, expected in cases.items():
        check(
            f"{name} splits to {expected}",
            module.split_version_name(name) == expected,
            str(module.split_version_name(name)),
        )

    unversioned = module.split_version_name("libstdc++.so.6")
    check(
        "a name with no version is kept whole with no version",
        unversioned == ("libstdc++.so.6", None),
        str(unversioned),
    )

    # The row shape a real version-needs section produces, including the trailing table index.
    rows = [
        ("GCC_3.0", "3"),
        ("GLIBC_2.2.5", "4"),
        ("GLIBCXX_3.4.29", "71"),
        ("CXXABI_1.3.11", "72"),
    ]
    sample = "".join(f"  0x0010:   Name: {name}  Flags: none  Version: {index}\n" for name, index in rows)
    parsed = []
    for name, _index in module._SYMBOL_VERSION_RE.findall(sample):
        namespace, version = module.split_version_name(name)
        entry = {"kind": "symbol-version", "namespace": namespace, "version": version}
        if entry not in parsed:
            parsed.append(entry)
    namespaces = {entry["namespace"] for entry in parsed}
    check(
        "the table index is not mistaken for a version", all(entry["version"] != "71" for entry in parsed), str(parsed)
    )
    check("GLIBCXX is reported as a namespace", "GLIBCXX" in namespaces, str(sorted(namespaces)))
    check(
        "the GLIBCXX version is the one from the name",
        any(entry["namespace"] == "GLIBCXX" and entry["version"] == "3.4.29" for entry in parsed),
        str(parsed),
    )


def test_requirement_direction(directory: str) -> None:
    print("a demand must not exceed what the environment provides")

    provision = {
        "fields_version": 1,
        "probes": [
            {
                "role": "derived",
                "path": os.path.join(directory, "libcandidate.so.1.0.0"),
                "content_reference": "sha256:" + "a" * 64,
                "linkage": {"known": True, "type": "shared", "config": "release"},
                "version": {"known": True, "value": "1.0.0"},
                "features": {"known": False, "values": [], "reason": "none shipped"},
                "abi_demands": {
                    "known": True,
                    "values": [
                        {"kind": "symbol-version", "namespace": "GLIBCXX", "version": "3.4.20"},
                        {"kind": "symbol-version", "namespace": "GLIBC", "version": "2.28"},
                        {"kind": "platform-floor", "namespace": "minos", "version": "11.0"},
                    ],
                    "source": "synthetic",
                },
            }
        ],
    }
    provision_path = write_json(os.path.join(directory, "dir_provision.json"), provision)

    def compare(requirement):
        requirement_path = write_json(
            os.path.join(directory, "dir_requirement.json"), {"fields_version": 1, "requirements": [requirement]}
        )
        return run("compare", "--provision", provision_path, "--requirement", requirement_path)

    result = compare({"kind": "symbol_version", "namespace": "GLIBCXX", "available_version": "3.4.29"})
    check("demanding less than is available is accepted", result.returncode == 0, result.stdout.strip())

    result = compare({"kind": "symbol_version", "namespace": "GLIBCXX", "available_version": "3.4.20"})
    check("demanding exactly what is available is accepted", result.returncode == 0, result.stdout.strip())

    result = compare({"kind": "symbol_version", "namespace": "GLIBCXX", "available_version": "3.4.19"})
    check("demanding more than is available is rejected", result.returncode == 2, f"exit {result.returncode}")
    check(
        "the rejection shows the demand and the availability",
        "3.4.20" in result.stdout and "3.4.19" in result.stdout,
        result.stdout.strip(),
    )

    result = compare({"kind": "symbol_version", "namespace": "GLIBCXX", "min_version": "3.4.29"})
    check("min_version is accepted as the same quantity", result.returncode == 0, result.stdout.strip())

    result = compare({"kind": "platform_floor", "namespace": "minos", "available_version": "10.9"})
    check("a platform floor newer than the target is rejected", result.returncode == 2, f"exit {result.returncode}")

    result = compare({"kind": "platform_floor", "namespace": "minos", "available_version": "14.0"})
    check("a platform floor older than the target is accepted", result.returncode == 0, result.stdout.strip())

    result = compare({"kind": "version", "min_version": "1.0.0"})
    check("the artifact's own version still means at least", result.returncode == 0, result.stdout.strip())

    result = compare({"kind": "version", "min_version": "2.0.0"})
    check(
        "an artifact older than the required version is rejected", result.returncode == 2, f"exit {result.returncode}"
    )


def write_json(path: str, document) -> str:
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(document, handle, indent=2, sort_keys=True)
    return path


def main() -> int:
    if not os.path.isfile(SCRIPT):
        print(f"probe_artifact.py not found at {SCRIPT}", file=sys.stderr)
        return 1

    with tempfile.TemporaryDirectory() as directory:
        test_container_headers(directory)
        test_unknown_is_recorded_not_omitted(directory)
        test_input_and_derived_are_separate(directory)
        test_content_reference(directory)
        test_probe_cache(directory)
        test_retryable_results_are_not_cached(directory)
        test_metadata_root_is_per_artifact(directory)
        test_probing_does_not_modify(directory)
        test_requirement_comparison(directory)
        test_version_name_parsing(directory)
        test_requirement_direction(directory)
        test_missing_tool_behaviour(directory)
        test_framework_directory_is_resolved(directory)
        test_available_tools_against_real_artifacts(directory)

    print()
    if SKIPPED:
        print(f"{len(SKIPPED)} check group(s) skipped: {', '.join(SKIPPED)}")
    if FAILURES:
        print(f"{len(FAILURES)} check(s) failed:")
        for failure in FAILURES:
            print(f"  - {failure}")
        return 1
    print("all artifact probe checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
