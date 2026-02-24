#!/usr/bin/env python3
#
# Copyright (C) 2024  Autodesk, Inc. All Rights Reserved.
#
# SPDX-License-Identifier: Apache-2.0
#

"""
Windows FFmpeg build wrapper for OpenRV.

Replaces the MSYS2 dependency for FFmpeg builds by finding bash from
Git for Windows (or MSYS2 as fallback) and handling Windows-to-Unix
path conversion for PKG_CONFIG_PATH.

Usage:
    python3 build_ffmpeg_windows.py --action configure --install-dir DIR \\
        --pkg-config-path "path1;path2" -- [configure options...]
    python3 build_ffmpeg_windows.py --action build --jobs N
    python3 build_ffmpeg_windows.py --action install
"""

import argparse
import os
import shutil
import subprocess
import sys


def find_bash():
    """Find bash.exe: Git for Windows first, then PATH fallback (MSYS2)."""
    git_bash_candidates = [
        os.path.join(
            os.environ.get("ProgramFiles", r"C:\Program Files"),
            "Git",
            "bin",
            "bash.exe",
        ),
        os.path.join(
            os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"),
            "Git",
            "bin",
            "bash.exe",
        ),
        os.path.join(
            os.environ.get("LOCALAPPDATA", ""),
            "Programs",
            "Git",
            "bin",
            "bash.exe",
        ),
    ]
    for path in git_bash_candidates:
        if path and os.path.isfile(path):
            return path

    # PATH fallback — picks up MSYS2 bash when present
    bash = shutil.which("bash")
    if bash:
        return bash

    print(
        "ERROR: Cannot find bash.exe. "
        "Install Git for Windows or add bash to PATH.",
        file=sys.stderr,
    )
    sys.exit(1)


def find_make():
    """Find GNU make on PATH."""
    make = shutil.which("make")
    if make:
        return make

    print(
        "ERROR: Cannot find 'make'. "
        "Install GNU Make (e.g., choco install make).",
        file=sys.stderr,
    )
    sys.exit(1)


def win_to_unix_path(win_path):
    """Convert a Windows path to a Unix path for use inside bash.

    Examples:
        C:\\foo\\bar  -> /c/foo/bar
        C:/foo/bar   -> /c/foo/bar
        /already/unix -> /already/unix
    """
    path = win_path.replace("\\", "/")
    # Handle drive letter: C:/foo -> /c/foo
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
    unix_elements = [win_to_unix_path(p) for p in elements]
    return ":".join(unix_elements)


def action_configure(args, extra_args):
    """Run FFmpeg's ./configure via bash with proper path conversion."""
    bash = find_bash()
    install_prefix = win_to_unix_path(args.install_dir)
    pkg_config = convert_pkg_config_path(args.pkg_config_path or "")

    configure_cmd = "./configure --prefix=" + install_prefix
    if extra_args:
        configure_cmd += " " + " ".join(extra_args)

    env = os.environ.copy()
    if pkg_config:
        env["PKG_CONFIG_PATH"] = pkg_config

    cmd = [bash, "-c", configure_cmd]
    print(f"[build_ffmpeg_windows.py] configure: {configure_cmd}", flush=True)
    if pkg_config:
        print(f"[build_ffmpeg_windows.py] PKG_CONFIG_PATH={pkg_config}", flush=True)

    result = subprocess.run(cmd, env=env)
    sys.exit(result.returncode)


def action_build(args, _extra_args):
    """Run make -j<jobs>."""
    make = find_make()
    cmd = [make, f"-j{args.jobs}"]
    print(f"[build_ffmpeg_windows.py] build: {' '.join(cmd)}", flush=True)

    result = subprocess.run(cmd)
    sys.exit(result.returncode)


def action_install(_args, _extra_args):
    """Run make install."""
    make = find_make()
    cmd = [make, "install"]
    print(f"[build_ffmpeg_windows.py] install: {' '.join(cmd)}", flush=True)

    result = subprocess.run(cmd)
    sys.exit(result.returncode)


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
        help="Semicolon-separated PKG_CONFIG_PATH entries (configure action)",
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
