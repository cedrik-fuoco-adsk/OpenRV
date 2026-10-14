#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# *****************************************************************************
# Copyright 2026 Autodesk, Inc. All rights reserved.
#
# SPDX-License-Identifier: Apache-2.0
#
# *****************************************************************************

"""Read binary compatibility facts out of an artifact, and compare them.

The probe answers "what does this artifact provide?", and the compare step
answers "is that enough for what a consumer requires?". Both exist so that a
substitution decision rests on measured facts rather than on a version string:
two artifacts of the same version can differ in linkage configuration, feature
set and compiler ABI, and those differences are what break a build.

Facts are read from the artifact itself:

  * format, linkage type and linkage configuration  from the file's own headers
  * symbol-level and platform-floor ABI demands     from the file's own metadata
  * version and feature set                         from metadata the artifact
                                                    ships with it (Qt's own
                                                    configure output, a
                                                    pkg-config file)

There is deliberately no way to declare a fact. A declaration supplied by the
user is exactly what this is meant to replace, so it is not an input.

Only the Python standard library is used for the header-derived facts. The
ABI-demand facts need an inspection tool (readelf, otool, dumpbin, or their
LLVM equivalents); when no tool is available those facts are recorded as
unknown and probing continues, unless ``--strict`` is given in which case
probing fails naming the missing tool.

Subcommands
-----------

``probe``
    Inspect one or more artifacts and write a provision document. Each
    artifact carries a role, so an ingested input artifact and the artifact
    derived from it are probed and retained separately.

``compare``
    Compare a provision document against a requirement document and report
    every requirement the provision does not satisfy.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import struct
import subprocess
import sys

FIELDS_VERSION = 1

# Part of every cache entry's name, so that a change to what is observed, or how, invalidates
# entries written by an earlier probe instead of serving them. Version 2: the metadata root became
# part of the key, after version 1 entries were found carrying another package's metadata.
CACHE_VERSION = 2

ELF_MAGIC = b"\x7fELF"
MACHO_MAGICS = {
    b"\xfe\xed\xfa\xce": "macho32",
    b"\xce\xfa\xed\xfe": "macho32-swapped",
    b"\xfe\xed\xfa\xcf": "macho64",
    b"\xcf\xfa\xed\xfe": "macho64-swapped",
    b"\xca\xfe\xba\xbe": "macho-fat",
    b"\xbe\xba\xfe\xca": "macho-fat-swapped",
}
AR_MAGIC = b"!<arch>\n"

# ELF e_type
_ELF_ET_REL = 1
_ELF_ET_EXEC = 2
_ELF_ET_DYN = 3

# Mach-O filetype
_MACHO_MH_OBJECT = 1
_MACHO_MH_EXECUTE = 2
_MACHO_MH_DYLIB = 6

# PE COFF characteristics
_PE_IMAGE_FILE_DLL = 0x2000

# Imports that indicate an artifact was linked against a debug C runtime.
_DEBUG_CRT_RE = re.compile(
    r"^(msvcp\d+d|vcruntime\d+d|ucrtbased|msvcrtd|libcmtd|python\d+_d|Qt6\w+d)\.(dll|so|dylib)$",
    re.IGNORECASE,
)

_SYMBOL_VERSION_RE = re.compile(r"Name:\s*(\S+)\s+Flags:\s*\S+\s+Version:\s*(\S+)")

# A version name carries both the namespace and the version, e.g. GLIBCXX_3.4.29 or GLIBC_2.2.5.
_VERSION_NAME_RE = re.compile(r"^(?P<namespace>[A-Za-z_][A-Za-z0-9_]*?)_(?P<version>\d+(?:\.\d+)*)$")
# Mach-O load commands. The minimum-OS field is only meaningful inside the load command that declares it, and both `minos` and `version` appear in unrelated load
# commands -- `version 22.1.3` is the linker's own version, not the platform floor. Matching loosely would invent a platform floor higher than the real one, and
# since a requirement is checked against the highest candidate that would make every platform-floor requirement pass spuriously.
_MACHO_CMD_RE = re.compile(r"^\s*cmd\s+(LC_\w+)", re.MULTILINE)
_MACHO_PLATFORM_RE = re.compile(r"^\s*platform\s+(\w+)", re.MULTILINE)
_MACHO_MINOS_FIELD_RE = re.compile(r"^\s*minos\s+(\d+(?:\.\d+)*)", re.MULTILINE)
_MACHO_VERSION_FIELD_RE = re.compile(r"^\s*version\s+(\d+(?:\.\d+)*)", re.MULTILINE)
_MACHO_MIN_NAMESPACE = {
    "macos": "minos",
    "ios": "min-ios",
    "tvos": "min-tvos",
    "watchos": "min-watchos",
    "xros": "min-xros",
    "maccatalyst": "min-catalyst",
}
_LLVM_IMPORT_NAME_RE = re.compile(r"^\s*Name:\s*(\S+\.(?:dll|so|dylib))\s*$", re.IGNORECASE | re.MULTILINE)
_DUMPBIN_DEP_RE = re.compile(r"^\s+(\S+\.dll)\s*$", re.IGNORECASE | re.MULTILINE)

# A debug build of libstdc++ places symbols in a debug version namespace.
_DEBUG_NAMESPACE_RE = re.compile(r"(GLIBCXX|CXXABI).*DEBUG", re.IGNORECASE)

# .so.N.N.N / libfoo-1.2.3.so / foo-1.2.3.dylib
_SO_VERSION_RE = re.compile(r"\.so\.(\d+(?:\.\d+)*)")
_DASHED_VERSION_RE = re.compile(r"[-.][vV]?(\d+\.\d+(?:\.\d+)*)\.(?:so|dylib|dll)$")

_QT_CONFIG_RE = re.compile(r"^\s*QT_CONFIG\s*\+?=\s*(.*)$")
_QT_VERSION_RE = re.compile(r"^\s*QT_VERSION\s*=\s*(\S+)")
_PKG_CONFIG_VERSION_RE = re.compile(r"^Version:\s*(\S+)", re.MULTILINE)
_CMAKE_PACKAGE_VERSION_RE = re.compile(r'set\(PACKAGE_VERSION\s+"?([^")\s]+)"?\)')


def _log(message: str) -> None:
    print(f"[probe_artifact] {message}", file=sys.stderr, flush=True)


def _unknown(reason: str) -> dict:
    """A fact category that could not be determined.

    Undeterminable categories are recorded explicitly rather than omitted, so
    that a consumer can tell "no metadata" apart from "nothing was checked".
    """
    return {"known": False, "values": [], "reason": reason}


def content_reference(path: str) -> str:
    """Hash the artifact's bytes. This is the cache key and the manifest reference."""
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def detect_format(path: str) -> str:
    with open(path, "rb") as handle:
        head = handle.read(16)
    if head.startswith(ELF_MAGIC):
        return "elf"
    if head[:4] in MACHO_MAGICS:
        return "macho"
    if head.startswith(AR_MAGIC):
        return "archive"
    if head[:2] == b"MZ":
        return "pe"
    return "unknown"


def _read_linkage_from_headers(path: str, fmt: str) -> dict:
    """Determine shared/static from the file's own headers, with no external tool."""
    try:
        with open(path, "rb") as handle:
            data = handle.read(4096)
    except OSError as error:
        return {"type": "unknown", "config": "unknown", "known": False, "reason": str(error)}

    if fmt == "elf":
        if len(data) < 18:
            return {"type": "unknown", "config": "unknown", "known": False, "reason": "truncated ELF header"}
        e_type = struct.unpack_from("<H", data, 16)[0]
        if e_type == _ELF_ET_DYN:
            return {"type": "shared", "config": "unknown", "known": True, "source": "ELF e_type=ET_DYN"}
        if e_type in (_ELF_ET_REL,):
            return {"type": "static", "config": "unknown", "known": True, "source": "ELF e_type=ET_REL"}
        if e_type == _ELF_ET_EXEC:
            return {"type": "executable", "config": "unknown", "known": True, "source": "ELF e_type=ET_EXEC"}
        return {"type": "unknown", "config": "unknown", "known": False, "reason": f"ELF e_type={e_type}"}

    if fmt == "macho":
        magic = data[:4]
        # The magic is written in the file's own byte order, so the big-endian
        # spellings mean the file must be parsed big-endian and vice versa.
        # Getting this backwards silently reads a wrong filetype and reports a
        # shared library as static.
        big_endian = magic in (b"\xfe\xed\xfa\xce", b"\xfe\xed\xfa\xcf", b"\xca\xfe\xba\xbe")
        if magic in (b"\xca\xfe\xba\xbe", b"\xbe\xba\xfe\xca"):
            return {"type": "shared", "config": "unknown", "known": True, "source": "Mach-O universal binary"}
        if len(data) < 16:
            return {"type": "unknown", "config": "unknown", "known": False, "reason": "truncated Mach-O header"}
        filetype = struct.unpack_from(">I" if big_endian else "<I", data, 12)[0]
        if filetype == _MACHO_MH_DYLIB:
            return {"type": "shared", "config": "unknown", "known": True, "source": "Mach-O filetype=MH_DYLIB"}
        if filetype == _MACHO_MH_OBJECT:
            return {"type": "static", "config": "unknown", "known": True, "source": "Mach-O filetype=MH_OBJECT"}
        if filetype == _MACHO_MH_EXECUTE:
            return {"type": "executable", "config": "unknown", "known": True, "source": "Mach-O filetype=MH_EXECUTE"}
        return {"type": "unknown", "config": "unknown", "known": False, "reason": f"Mach-O filetype={filetype}"}

    if fmt == "pe":
        if len(data) < 0x40:
            return {"type": "unknown", "config": "unknown", "known": False, "reason": "truncated DOS header"}
        pe_offset = struct.unpack_from("<I", data, 0x3C)[0]
        if pe_offset + 24 > len(data):
            return {"type": "unknown", "config": "unknown", "known": False, "reason": "PE header outside first page"}
        if data[pe_offset : pe_offset + 4] != b"PE\0\0":
            return {"type": "unknown", "config": "unknown", "known": False, "reason": "missing PE signature"}
        characteristics = struct.unpack_from("<H", data, pe_offset + 22)[0]
        if characteristics & _PE_IMAGE_FILE_DLL:
            return {"type": "shared", "config": "unknown", "known": True, "source": "PE IMAGE_FILE_DLL"}
        return {"type": "executable", "config": "unknown", "known": True, "source": "PE without IMAGE_FILE_DLL"}

    if fmt == "archive":
        return {"type": "static", "config": "unknown", "known": True, "source": "ar archive"}

    return {
        "type": "unknown",
        "config": "unknown",
        "known": False,
        "reason": f"unrecognized container format for {os.path.basename(path)}",
    }


def _parse_macho_minimum_platform(output: str):
    """Extract the minimum-platform floor from Mach-O load commands.

    Only the min-OS field of the load command that defines it counts:
    ``minos`` inside ``LC_BUILD_VERSION``, or ``version`` inside an
    ``LC_VERSION_MIN_*`` command. Everything else that happens to be called
    "version" is a different fact about a different load command.
    """
    values = []
    blocks = re.split(r"(?=^\s*cmd\s+LC_)", output, flags=re.MULTILINE)
    for block in blocks:
        command_match = _MACHO_CMD_RE.search(block)
        if not command_match:
            continue
        command = command_match.group(1)

        if command == "LC_BUILD_VERSION":
            field = _MACHO_MINOS_FIELD_RE.search(block)
            if not field:
                continue
            platform_match = _MACHO_PLATFORM_RE.search(block)
            platform = platform_match.group(1).lower() if platform_match else "macos"
            namespace = _MACHO_MIN_NAMESPACE.get(platform, "minos")
        elif command.startswith("LC_VERSION_MIN_"):
            field = _MACHO_VERSION_FIELD_RE.search(block)
            if not field:
                continue
            namespace = "minos" if "MACOSX" in command else "min-" + command[len("LC_VERSION_MIN_") :].lower()
        else:
            continue

        entry = {"kind": "platform-floor", "namespace": namespace, "version": field.group(1)}
        if entry not in values:
            values.append(entry)
    return values


def _version_from_filename(path: str) -> dict:
    name = os.path.basename(path)
    match = _SO_VERSION_RE.search(name)
    if match:
        return {"value": match.group(1), "known": True, "source": "filename version suffix"}
    match = _DASHED_VERSION_RE.search(name)
    if match:
        return {"value": match.group(1), "known": True, "source": "filename version suffix"}
    return {
        "value": None,
        "known": False,
        "reason": "no version in the artifact filename and no version metadata found",
    }


def _read_metadata(path: str, metadata_root: str):
    """Read version and features from metadata the artifact ships with it.

    These are the artifact's own distributed files: Qt's configure output, or a
    pkg-config file installed alongside the library. Nothing here is a
    declaration supplied by the caller.
    """
    version = {"value": None, "known": False, "reason": "no version metadata found in the artifact"}
    features = {"known": False, "values": [], "reason": "no feature metadata found in the artifact"}

    roots = []
    if metadata_root:
        roots.append(metadata_root)
    # A library's own directory may carry metadata for the package it belongs to.
    for parent in (os.path.dirname(os.path.abspath(path)), os.path.dirname(os.path.dirname(os.path.abspath(path)))):
        if parent and parent not in roots:
            roots.append(parent)

    for root in roots:
        # Qt: the CONFIG line of Qt's own qconfig.pri, written by Qt's configure.
        qconfig = os.path.join(root, "mkspecs", "qconfig.pri")
        if os.path.isfile(qconfig):
            collected = []
            found_version = None
            try:
                with open(qconfig, "r", encoding="utf-8", errors="replace") as handle:
                    for line in handle:
                        version_match = _QT_VERSION_RE.match(line)
                        if version_match:
                            found_version = version_match.group(1)
                        config_match = _QT_CONFIG_RE.match(line)
                        if config_match:
                            collected.extend(config_match.group(1).split())
            except OSError:
                pass
            if found_version and not version["known"]:
                version = {"value": found_version, "known": True, "source": "mkspecs/qconfig.pri QT_VERSION"}
            if collected:
                features = {
                    "known": True,
                    "values": sorted(set(collected)),
                    "source": "mkspecs/qconfig.pri QT_CONFIG",
                }
                return version, features

        # A Qt CMake package records the version Qt's own build declared.
        for candidate in (
            os.path.join(root, "lib", "cmake", "Qt6", "Qt6ConfigVersion.cmake"),
            os.path.join(root, "lib", "cmake", "Qt6Core", "Qt6CoreConfigVersion.cmake"),
        ):
            if os.path.isfile(candidate) and not version["known"]:
                try:
                    with open(candidate, "r", encoding="utf-8", errors="replace") as handle:
                        match = _CMAKE_PACKAGE_VERSION_RE.search(handle.read())
                    if match:
                        version = {"value": match.group(1), "known": True, "source": os.path.relpath(candidate, root)}
                except OSError:
                    pass

        # pkg-config file installed alongside the library.
        for pkgconfig_dir in (os.path.join(root, "lib", "pkgconfig"), os.path.join(root, "lib64", "pkgconfig")):
            if not os.path.isdir(pkgconfig_dir):
                continue
            try:
                entries = sorted(os.listdir(pkgconfig_dir))
            except OSError:
                continue
            for entry in entries:
                if not entry.endswith(".pc"):
                    continue
                try:
                    with open(os.path.join(pkgconfig_dir, entry), "r", encoding="utf-8", errors="replace") as handle:
                        match = _PKG_CONFIG_VERSION_RE.search(handle.read())
                except OSError:
                    continue
                if match and not version["known"]:
                    version = {
                        "value": match.group(1),
                        "known": True,
                        "source": os.path.join("lib", "pkgconfig", entry),
                    }
                if version["known"]:
                    break

        if version["known"]:
            break

    return version, features


def _find_tool(names):
    for name in names:
        found = shutil.which(name)
        if found:
            return name, found
    return None, None


def _run(command):
    try:
        completed = subprocess.run(command, capture_output=True, text=True, errors="replace", timeout=120)
    except (OSError, subprocess.SubprocessError) as error:
        return None, str(error)
    if completed.returncode != 0:
        return None, (completed.stderr or "").strip() or f"exit code {completed.returncode}"
    return completed.stdout, None


def split_version_name(name: str):
    """Split a version name into its namespace and version: GLIBCXX_3.4.29 -> (GLIBCXX, 3.4.29).

    A version-needs row from readelf reads ``Name: <version name> Flags: ... Version: <index>``.
    The name carries both the namespace and the version, and the trailing ``Version:`` is an
    index into the version table with no ABI meaning. Reading the row the other way round
    records the index as the version and the whole name as the namespace, so a requirement on
    a namespace never matches anything.
    """
    match = _VERSION_NAME_RE.match(name)
    if match:
        return match.group("namespace"), match.group("version")
    return name, None


def _abi_demands_elf(path: str, strict: bool):
    candidates = (
        ("readelf", ["readelf", "-W", "--version-info", path]),
        ("llvm-readobj", ["llvm-readobj", "--elf-output-style=GNU", "--version-info", path]),
    )
    attempted = []
    for tool_name, command in candidates:
        if not shutil.which(command[0]):
            continue
        attempted.append(tool_name)
        output, error = _run(command)
        if output is None:
            continue
        values = []
        for name, _index in _SYMBOL_VERSION_RE.findall(output):
            namespace, version = split_version_name(name)
            entry = {"kind": "symbol-version", "namespace": namespace, "version": version}
            if entry not in values:
                values.append(entry)
        return {"known": True, "values": values, "source": f"{tool_name} --version-info"}
    if attempted:
        return _unreadable(f"{', '.join(attempted)} could not read version information from this artifact", strict)
    return _missing_tool("ELF version-info reader (readelf or llvm-readobj)", strict)


def _abi_demands_macho(path: str, strict: bool):
    if not shutil.which("otool"):
        # llvm-objdump can read Mach-O load commands on hosts without Xcode tools.
        if shutil.which("llvm-objdump"):
            output, _ = _run(["llvm-objdump", "--macho", "--all-headers", path])
            if output is not None:
                values = _parse_macho_minimum_platform(output)
                if values:
                    return {"known": True, "values": values, "source": "llvm-objdump --macho --all-headers"}
        return _missing_tool("otool or llvm-objdump", strict)

    output, error = _run(["otool", "-l", path])
    if output is None:
        return _unreadable(f"otool -l could not read this artifact: {error}", strict)
    values = _parse_macho_minimum_platform(output)
    if not values:
        return _unknown("otool -l reported no minimum platform version")
    return {"known": True, "values": values, "source": "otool -l"}


def read_pe_imports(path: str):
    """The DLLs a PE image imports, read from its import directory; None if the headers cannot be read.

    Only the names are needed, so they are read directly rather than through llvm-readobj or dumpbin, which are often not
    on PATH -- dumpbin only inside a Visual Studio developer prompt.
    """
    try:
        with open(path, "rb") as handle:
            data = handle.read()
        pe = struct.unpack_from("<I", data, 0x3C)[0]
        if data[pe : pe + 4] != b"PE\0\0":
            return None
        sections = struct.unpack_from("<H", data, pe + 6)[0]
        optional_size = struct.unpack_from("<H", data, pe + 20)[0]
        optional = pe + 24
        # The data directories follow the optional header's fixed part, which is longer in PE32+.
        directories = optional + (112 if struct.unpack_from("<H", data, optional)[0] == 0x20B else 96)
        import_rva = struct.unpack_from("<I", data, directories + 8)[0]
        table = optional + optional_size

        def offset(rva):
            for index in range(sections):
                virtual_size, address, raw_size, raw = struct.unpack_from("<IIII", data, table + index * 40 + 8)
                if address <= rva < address + max(virtual_size, raw_size):
                    return rva - address + raw
            return None

        imports = []
        position = offset(import_rva) if import_rva else None
        while position is not None:
            name_rva = struct.unpack_from("<I", data, position + 12)[0]
            if not name_rva:
                break
            start = offset(name_rva)
            if start is None:
                return None
            imports.append(data[start : data.index(b"\0", start)].decode("ascii", errors="replace").lower())
            position += 20
        return imports
    except (OSError, struct.error, ValueError):
        return None


def _abi_demands_pe(path: str, strict: bool):
    attempted = []

    if shutil.which("llvm-readobj"):
        attempted.append("llvm-readobj")
        output, _ = _run(["llvm-readobj", "--coff-imports", path])
        if output is not None:
            values = []
            for name in _LLVM_IMPORT_NAME_RE.findall(output):
                entry = {"kind": "import", "namespace": "import", "version": name.lower()}
                if entry not in values:
                    values.append(entry)
            return {"known": True, "values": values, "source": "llvm-readobj --coff-imports"}

    if shutil.which("dumpbin"):
        attempted.append("dumpbin")
        output, _ = _run(["dumpbin", "/nologo", "/dependents", path])
        if output is not None:
            values = []
            for name in _DUMPBIN_DEP_RE.findall(output):
                entry = {"kind": "import", "namespace": "import", "version": name.lower()}
                if entry not in values:
                    values.append(entry)
            return {"known": True, "values": values, "source": "dumpbin /dependents"}

    imports = read_pe_imports(path)
    if imports is not None:
        values = []
        for name in imports:
            entry = {"kind": "import", "namespace": "import", "version": name}
            if entry not in values:
                values.append(entry)
        return {"known": True, "values": values, "source": "PE import directory"}

    if attempted:
        # The tool exists but could not read this file. That is a different
        # problem from the tool being absent, and must not be reported as one.
        return _unreadable(f"{', '.join(attempted)} could not read imports from this artifact", strict)
    return _missing_tool("PE import reader (llvm-readobj or dumpbin)", strict)


def _retryable(reason: str) -> dict:
    """An unknown that says nothing about the artifact: the inspection itself did not happen.

    A missing tool, a tool that timed out or could not read the file, may all be different on the
    next configure, so such a result is never cached -- see _probe_one.
    """
    result = _unknown(reason)
    result["retryable"] = True
    return result


def _unreadable(what: str, strict: bool):
    """A tool was present but could not read the artifact."""
    reason = f"{what}"
    if strict:
        raise MissingToolError(reason)
    _log(f"warning: {reason}; recording ABI demands as unknown")
    return _retryable(reason)


def _missing_tool(what: str, strict: bool):
    reason = f"no {what} is available on PATH"
    if strict:
        raise MissingToolError(reason)
    _log(f"warning: {reason}; recording ABI demands as unknown")
    return _retryable(reason)


class MissingToolError(RuntimeError):
    """Raised in strict mode when a required inspection tool is absent."""


def _apply_linkage_config(linkage: dict, fmt: str, demands: dict) -> dict:
    """Decide release or debug linkage, naming the evidence used.

    The two directions are not equally strong. Finding a debug marker proves a
    debug build. Not finding one is good evidence of a release build but is not
    proof, so the evidence is recorded next to the value rather than presented
    as certainty.
    """
    if not linkage.get("known"):
        linkage["config"] = "unknown"
        return linkage

    values = demands.get("values", []) if demands.get("known") else []

    for entry in values:
        if _DEBUG_NAMESPACE_RE.search(str(entry.get("namespace", ""))):
            linkage["config"] = "debug"
            linkage["config_source"] = "debug symbol-version namespace present"
            return linkage

    if fmt == "pe":
        for entry in values:
            if entry.get("kind") == "import" and _DEBUG_CRT_RE.match(str(entry.get("version", ""))):
                linkage["config"] = "debug"
                linkage["config_source"] = "debug C runtime import present"
                return linkage
        if demands.get("known"):
            linkage["config"] = "release"
            linkage["config_source"] = "PE C runtime import set contains no debug runtime"
            return linkage

    if fmt == "elf" and demands.get("known"):
        linkage["config"] = "release"
        linkage["config_source"] = "no debug symbol-version namespace present"
        return linkage

    linkage["config"] = "unknown"
    linkage["config_reason"] = "the format carries no reliable debug marker and none was found"
    return linkage


def _observe(path: str, metadata_root: str, strict: bool) -> dict:
    """Facts derived from the artifact's contents. This is the cacheable part."""
    fmt = detect_format(path)
    linkage = _read_linkage_from_headers(path, fmt)

    if fmt == "elf":
        demands = _abi_demands_elf(path, strict)
    elif fmt == "macho":
        demands = _abi_demands_macho(path, strict)
    elif fmt == "pe":
        demands = _abi_demands_pe(path, strict)
    else:
        demands = _unknown(f"no ABI reader exists for the {fmt} format")

    linkage = _apply_linkage_config(linkage, fmt, demands)

    version, features = _read_metadata(path, metadata_root)
    if not version["known"]:
        filename_version = _version_from_filename(path)
        if filename_version["known"]:
            version = filename_version

    return {"format": fmt, "linkage": linkage, "version": version, "features": features, "abi_demands": demands}


def _cache_path(cache_dir: str, reference: str, metadata_root: str) -> str:
    """The cache entry for an artifact observed with a given metadata root.

    The root is part of the key because version and features are read from it: the same bytes
    observed against a different root are a different observation.
    """
    name = f"v{CACHE_VERSION}_" + reference.replace(":", "_")
    if metadata_root:
        root = os.path.normcase(os.path.abspath(metadata_root))
        name += "_" + hashlib.sha256(root.encode("utf-8")).hexdigest()[:16]
    return os.path.join(cache_dir, name + ".json")


def _is_retryable(observed: dict) -> bool:
    return any(isinstance(fact, dict) and fact.get("retryable") for fact in observed.values())


def resolve_artifact_path(path: str) -> str:
    """Resolve an artifact path to the file that carries the facts.

    On macOS a Qt module is distributed as a framework *directory*, and CMake's
    imported location for it can be that directory rather than the binary inside.
    Probing the directory would fail the file check and record everything as
    unknown, so the framework is resolved to its binary here.
    """
    if not os.path.isdir(path) or not path.endswith(".framework"):
        return path
    name = os.path.basename(path)[: -len(".framework")]
    for candidate in (os.path.join(path, "Versions", "A", name), os.path.join(path, name)):
        if os.path.isfile(candidate):
            return candidate
    return path


def _probe_one(path: str, role: str, metadata_root: str, cache_dir: str, strict: bool) -> dict:
    reference = content_reference(path)

    observed = None
    inspection = "performed"
    if cache_dir:
        cached = _cache_path(cache_dir, reference, metadata_root)
        if os.path.isfile(cached):
            try:
                with open(cached, "r", encoding="utf-8") as handle:
                    observed = json.load(handle)
                inspection = "cached"
            except (OSError, json.JSONDecodeError):
                observed = None
        # Retryable results are not written, so one here came from somewhere else. It is never
        # trusted, and in particular never satisfies a strict probe, which must inspect.
        if observed is not None and _is_retryable(observed):
            observed = None
            inspection = "performed"

    if observed is None:
        observed = _observe(path, metadata_root, strict)
        if cache_dir and not _is_retryable(observed):
            try:
                os.makedirs(cache_dir, exist_ok=True)
                with open(_cache_path(cache_dir, reference, metadata_root), "w", encoding="utf-8") as handle:
                    json.dump(observed, handle, indent=2, sort_keys=True)
                    handle.write("\n")
            except OSError as error:
                _log(f"warning: could not write probe cache entry for {path}: {error}")

    entry = dict(observed)
    entry["path"] = os.path.abspath(path)
    entry["role"] = role
    entry["content_reference"] = reference
    entry["inspection"] = inspection
    return entry


def _parse_artifact_argument(value: str):
    if "=" in value and not os.path.exists(value):
        role, path = value.split("=", 1)
        return role.strip(), path
    return "derived", value


def _same_path(left: str, right: str) -> bool:
    return os.path.normcase(os.path.abspath(left)) == os.path.normcase(os.path.abspath(right))


def cmd_probe(args: argparse.Namespace) -> int:
    # A metadata root belongs to one artifact, not to a role: Qt's root carries Qt's version and
    # features, and handing it to every other input artifact recorded them all as Qt.
    artifact_roots = [(path, directory) for path, directory in args.artifact_metadata_root or []]

    probes = []
    try:
        for raw in args.artifact:
            role, path = _parse_artifact_argument(raw)
            metadata_root = args.metadata_root
            for root_path, directory in artifact_roots:
                if _same_path(root_path, path):
                    metadata_root = directory
            path = resolve_artifact_path(path)
            if not os.path.isfile(path):
                _log(f"warning: artifact not found, recording it as unknown: {path}")
                probes.append(
                    {
                        "path": os.path.abspath(path),
                        "role": role,
                        "content_reference": None,
                        "format": "unknown",
                        "linkage": {
                            "known": False,
                            "type": "unknown",
                            "config": "unknown",
                            "reason": "artifact not found",
                        },
                        "version": _unknown("artifact not found"),
                        "features": _unknown("artifact not found"),
                        "abi_demands": _unknown("artifact not found"),
                        "inspection": "not-performed",
                    }
                )
                continue
            probes.append(_probe_one(path, role, metadata_root, args.cache_dir, args.strict))
    except MissingToolError as error:
        print(f"artifact probing failed: {error}", file=sys.stderr)
        return 5

    document = {"fields_version": FIELDS_VERSION, "probes": probes}
    body = json.dumps(document, indent=2, sort_keys=True) + "\n"

    if args.out:
        try:
            directory = os.path.dirname(os.path.abspath(args.out))
            if directory:
                os.makedirs(directory, exist_ok=True)
            with open(args.out, "w", encoding="utf-8") as handle:
                handle.write(body)
        except OSError as error:
            print(f"could not write probe document to {args.out}: {error}", file=sys.stderr)
            return 4

    if args.print or not args.out:
        sys.stdout.write(body)
    return 0


def _version_key(value):
    return [int(piece) for piece in re.findall(r"\d+", str(value))] or [0]


def _numeric_ge(provided: str, required: str) -> bool:
    """True when ``provided`` is at least ``required``, compared as dotted numbers."""
    left, right = _version_key(provided), _version_key(required)
    length = max(len(left), len(right))
    left += [0] * (length - len(left))
    right += [0] * (length - len(right))
    return left >= right


def _numeric_less_or_equal(demand: str, available: str) -> bool:
    """True when a demand is no greater than what is available."""
    return _numeric_ge(available, demand)


def _evaluate_requirement(requirement: dict, provision: dict):
    """Return (satisfied, provided_description)."""
    kind = requirement.get("kind")
    linkage = provision.get("linkage", {})

    if kind == "linkage":
        if not linkage.get("known"):
            return False, "unknown (linkage could not be determined)"
        return linkage.get("type") == requirement.get("value"), str(linkage.get("type"))

    if kind == "linkage_config":
        if not linkage.get("known") or linkage.get("config") in (None, "unknown"):
            return False, "unknown (linkage configuration could not be determined)"
        return linkage.get("config") == requirement.get("value"), str(linkage.get("config"))

    if kind == "feature":
        features = provision.get("features", {})
        if not features.get("known"):
            return False, "unknown (the artifact ships no feature metadata)"
        return requirement.get("value") in features.get("values", []), ",".join(features.get("values", [])) or "<none>"

    if kind == "version":
        # The artifact's own version: it must be at least what is required.
        version = provision.get("version", {})
        if not version.get("known"):
            return False, "unknown (no version metadata found in the artifact)"
        return _numeric_ge(str(version.get("value", "0")), str(requirement.get("min_version", "0"))), str(
            version.get("value")
        )

    if kind in ("symbol_version", "platform_floor"):
        # A demand the artifact places on its runtime environment, not a version of the artifact
        # itself. It is usable only if it does not require more than that environment provides;
        # demanding less is fine, so the most demanding candidate decides.
        demands = provision.get("abi_demands", {})
        if not demands.get("known"):
            return False, "unknown (ABI demands could not be read)"
        wanted_namespace = requirement.get("namespace")
        candidates = [d for d in demands.get("values", []) if d.get("namespace") == wanted_namespace]
        if not candidates:
            present = ",".join(sorted({d.get("namespace", "?") for d in demands.get("values", [])})) or "<none>"
            return False, present
        if any(d.get("version") is None for d in candidates):
            return True, "unversioned"
        # "available_version" is what the consumer's environment provides. "min_version" is accepted
        # as a fallback name for the same quantity, so that an existing requirement document written
        # before this was named clearly still means the same thing.
        available = str(requirement.get("available_version", requirement.get("min_version", "0")))
        worst = max(candidates, key=lambda d: _version_key(d.get("version")))
        return _numeric_less_or_equal(str(worst.get("version", "0")), available), str(worst.get("version"))

    if kind == "import":
        demands = provision.get("abi_demands", {})
        if not demands.get("known"):
            return False, "unknown (imports could not be read)"
        wanted = str(requirement.get("value", "")).lower()
        present = [d.get("version") for d in demands.get("values", []) if d.get("kind") == "import"]
        return wanted in present, ",".join(sorted(present)) or "<none>"

    return False, f"unsupported requirement kind {kind!r}"


def _requirement_detail(requirement: dict) -> str:
    """A short human-readable description of what a requirement asked for.

    Included in the rejection diagnostic so the report says what was wanted as well as what was
    found; without the available version the message does not explain why the artifact failed.
    """
    kind = requirement.get("kind")
    if kind == "version":
        return f">= {requirement.get('min_version')}"
    if kind in ("symbol_version", "platform_floor"):
        available = requirement.get("available_version", requirement.get("min_version"))
        return f"{requirement.get('namespace')} (available {available})"
    return str(requirement.get("value") or requirement.get("namespace") or "")


def cmd_compare(args: argparse.Namespace) -> int:
    try:
        with open(args.provision, "r", encoding="utf-8") as handle:
            provision_document = json.load(handle)
        with open(args.requirement, "r", encoding="utf-8") as handle:
            requirement_document = json.load(handle)
    except (OSError, json.JSONDecodeError) as error:
        print(f"could not read a probe or requirement document: {error}", file=sys.stderr)
        return 4

    probes = provision_document.get("probes", [])
    # Prefer the derived artifact when a document carries both roles.
    ordered = sorted(probes, key=lambda p: 0 if p.get("role") == "derived" else 1)
    if not ordered:
        print("provision document contains no probes", file=sys.stderr)
        return 4
    provision = ordered[0]

    rejections = []
    for requirement in requirement_document.get("requirements", []):
        satisfied, provided = _evaluate_requirement(requirement, provision)
        if not satisfied:
            rejections.append({"requirement": requirement, "provided": provided})

    if args.json:
        print(
            json.dumps(
                {
                    "legal": not rejections,
                    "artifact": provision.get("path"),
                    "content_reference": provision.get("content_reference"),
                    "checked": len(requirement_document.get("requirements", [])),
                    "rejections": rejections,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0 if not rejections else 2

    if not rejections:
        print(f"substitution is legal: {provision.get('path')} satisfies all requirements")
        return 0

    print(f"substitution is not legal for {provision.get('path')}:")
    for rejection in rejections:
        requirement = rejection["requirement"]
        print(
            f"  requirement {requirement.get('kind')} {_requirement_detail(requirement)} is not satisfied; the artifact provides {rejection['provided']}"
        )
    return 2


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    subparsers = parser.add_subparsers(dest="command", required=True)

    probe = subparsers.add_parser("probe", help="inspect artifacts and write a provision document")
    probe.add_argument(
        "--artifact",
        action="append",
        default=[],
        metavar="[ROLE=]PATH",
        help="artifact to inspect; repeatable. Prefix with a role such as input= or derived= "
        "so an ingested artifact and the one derived from it are retained separately.",
    )
    probe.add_argument("--metadata-root", help="root of the artifact's own installation, where its metadata lives")
    probe.add_argument(
        "--artifact-metadata-root",
        action="append",
        nargs=2,
        default=[],
        metavar=("PATH", "DIR"),
        help="metadata root for the artifact at PATH, as given to --artifact, overriding --metadata-root; repeatable",
    )
    probe.add_argument("--cache-dir", help="cache inspected facts here, keyed by artifact content")
    probe.add_argument(
        "--strict", action="store_true", help="fail naming the missing tool instead of recording unknown"
    )
    probe.add_argument("--out", help="path of the provision document to write")
    probe.add_argument("--print", action="store_true", help="also write the document to stdout")
    probe.set_defaults(func=cmd_probe)

    compare = subparsers.add_parser("compare", help="compare a provision against a requirement")
    compare.add_argument("--provision", required=True, help="provision document produced by 'probe'")
    compare.add_argument("--requirement", required=True, help="requirement document to evaluate")
    compare.add_argument("--json", action="store_true")
    compare.set_defaults(func=cmd_compare)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
