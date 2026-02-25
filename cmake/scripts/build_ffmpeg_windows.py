#!/usr/bin/env python3
#
# Copyright (C) 2024  Autodesk, Inc. All Rights Reserved.
#
# SPDX-License-Identifier: Apache-2.0
#

"""
Windows FFmpeg build wrapper for OpenRV.

Requires MSYS2 for a fully consistent GNU toolchain — bash, make, awk, sed,
and grep all from the same runtime.  This is mandatory; no other toolchain
combination (e.g. Git for Windows + MinGW make) is supported.

The MSYS2 root is resolved in this order:
  1. MSYS2_ROOT environment variable (override for non-standard installs)
  2. C:\\msys64   (default choco / manual install location)
  3. C:\\msys32

Usage:
    python3 build_ffmpeg_windows.py --action configure --install-dir DIR \\
        --pkg-config-path "path1|path2" -- [configure options...]
    python3 build_ffmpeg_windows.py --action build --jobs N
    python3 build_ffmpeg_windows.py --action install
"""

import argparse
import os
import subprocess
import sys


# ---------------------------------------------------------------------------
# MSYS2 discovery
# ---------------------------------------------------------------------------

MSYS2_CANDIDATE_ROOTS = [
    os.environ.get("MSYS2_ROOT", ""),
    r"C:\msys64",
    r"C:\msys32",
]

_MSYS2_ERROR = (
    "ERROR: MSYS2 not found. "
    r"Install MSYS2 to C:\msys64 or set the MSYS2_ROOT environment variable."
)


def find_msys2_tools():
    """Return (msys2_root, bash_path, make_path), or exit with an error.

    All three are sourced from the same MSYS2 installation so that awk, sed,
    grep, etc. invoked by FFmpeg's Makefiles resolve to the same GNU runtime.
    Mixing runtimes (e.g. MinGW make + Git-for-Windows awk) causes awk
    backslash syntax errors during the FFmpeg build.
    """
    for root in MSYS2_CANDIDATE_ROOTS:
        if not root or not os.path.isdir(root):
            continue
        usr_bin = os.path.join(root, "usr", "bin")
        bash = os.path.join(usr_bin, "bash.exe")
        make = os.path.join(usr_bin, "make.exe")
        if os.path.isfile(bash) and os.path.isfile(make):
            return root, bash, make

    print(_MSYS2_ERROR, file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# Path conversion helpers
# ---------------------------------------------------------------------------

def win_to_unix_path(win_path):
    """Convert a Windows path to a Unix path for use inside MSYS2 bash.

    Examples:
        C:\\foo\\bar  -> /c/foo/bar
        C:/foo/bar   -> /c/foo/bar
        /already/unix -> /already/unix
    """
    path = win_path.replace("\\", "/")
    if len(path) >= 2 and path[1] == ":":
        drive = path[0].lower()
        path = "/" + drive + path[2:]
    return path


def convert_pkg_config_path(raw_paths):
    """Convert pipe-separated Windows paths to colon-separated Unix paths.

    Uses "|" as delimiter because CMake treats ";" as a list separator,
    which would split the value into multiple command arguments.
    """
    if not raw_paths:
        return ""
    elements = [p.strip() for p in raw_paths.split("|") if p.strip()]
    return ":".join(win_to_unix_path(p) for p in elements)


# ---------------------------------------------------------------------------
# Environment helper
# ---------------------------------------------------------------------------

def _make_msys2_env():
    """Return an env dict with MSYS2 usr/bin and mingw64/bin prepended to PATH.

    Prepending MSYS2 paths ensures that make, awk, sed, grep, etc. always
    resolve to MSYS2 GNU versions, regardless of what else is on PATH.
    """
    root, _bash, _make = find_msys2_tools()
    env = os.environ.copy()
    prepend = os.pathsep.join([
        os.path.join(root, "usr", "bin"),
        os.path.join(root, "mingw64", "bin"),
    ])
    env["PATH"] = prepend + os.pathsep + env.get("PATH", "")
    return env


# ---------------------------------------------------------------------------
# Actions
# ---------------------------------------------------------------------------

def action_configure(args, extra_args):
    """Run FFmpeg's ./configure via MSYS2 bash with proper path conversion."""
    _root, bash, _make = find_msys2_tools()
    install_prefix = win_to_unix_path(args.install_dir)
    pkg_config = convert_pkg_config_path(args.pkg_config_path or "")

    configure_cmd = "./configure --prefix=" + install_prefix
    if extra_args:
        configure_cmd += " " + " ".join(extra_args)

    env = _make_msys2_env()
    if pkg_config:
        env["PKG_CONFIG_PATH"] = pkg_config

    print(f"[build_ffmpeg_windows.py] configure: {configure_cmd}", flush=True)
    if pkg_config:
        print(f"[build_ffmpeg_windows.py] PKG_CONFIG_PATH={pkg_config}", flush=True)

    result = subprocess.run([bash, "-c", configure_cmd], env=env)
    sys.exit(result.returncode)


def action_build(args, _extra_args):
    """Run MSYS2 make with an explicit SHELL override pointing to MSYS2 bash.

    Using MSYS2 make + MSYS2 bash (both from the same runtime) ensures that
    all Makefile recipe tools — awk, sed, grep — also resolve to MSYS2
    binaries through the prepended PATH.
    """
    _root, bash, make = find_msys2_tools()
    env = _make_msys2_env()

    cmd = [make, f"-j{args.jobs}", f"SHELL={bash}"]
    print(f"[build_ffmpeg_windows.py] build: {' '.join(cmd)}", flush=True)

    result = subprocess.run(cmd, env=env)
    sys.exit(result.returncode)


def action_install(_args, _extra_args):
    """Run MSYS2 make install with SHELL override (see action_build docstring)."""
    _root, bash, make = find_msys2_tools()
    env = _make_msys2_env()

    cmd = [make, "install", f"SHELL={bash}"]
    print(f"[build_ffmpeg_windows.py] install: {' '.join(cmd)}", flush=True)

    result = subprocess.run(cmd, env=env)
    sys.exit(result.returncode)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Windows FFmpeg build wrapper for OpenRV"
    )
    parser.add_argument(
        "--action",
        required=True,
        choices=["configure", "build", "install"],
        help="Build action to perform",
    )
    parser.add_argument(
        "--install-dir",
        help="Installation prefix directory (configure action)",
    )
    parser.add_argument(
        "--pkg-config-path",
        help="Pipe-separated PKG_CONFIG_PATH entries (configure action)",
    )
    parser.add_argument(
        "--jobs",
        type=int,
        default=1,
        help="Number of parallel build jobs (build action)",
    )

    args, extra = parser.parse_known_args()

    # Remove leading '--' separator if present
    if extra and extra[0] == "--":
        extra = extra[1:]

    actions = {
        "configure": action_configure,
        "build": action_build,
        "install": action_install,
    }
    actions[args.action](args, extra)


if __name__ == "__main__":
    main()
    
