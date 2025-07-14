#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# *****************************************************************************
# Copyright 2020-2024 Autodesk, Inc. All rights reserved.
#
# SPDX-License-Identifier: Apache-2.0
#
# This script has been refactored to work with pre-built distributions from
# python-build-standalone. It no longer compiles Python from source.
# Its main responsibilities are to install the pre-built package,
# patch it with a sitecustomize.py, install pip packages, and run tests.
# *****************************************************************************


import argparse
import glob
import os
import pathlib
import shutil
import sys
import subprocess
import platform
import tempfile
import uuid

from typing import List
from datetime import datetime

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(ROOT_DIR)

# These globals are set from command-line arguments in main()
SOURCE_DIR = ""
OUTPUT_DIR = ""
TEMP_DIR = ""
VARIANT = ""
ARCH = ""
OPENTIMELINEIO_SOURCE_DIR = ""
PYTHON_VERSION = ""

SITECUSTOMIZE_FILE_CONTENT = f'''
#
# Copyright (c) {datetime.now().year} Autodesk, Inc. All rights reserved.
#
# SPDX-License-Identifier: Apache-2.0
#

"""
Site-level module that ensures OpenSSL will have up to date certificate authorities
on Linux and macOS. It gets imported when the Python interpreter starts up, both
when launching Python as a standalone interpreter or as an embedded one.

The python-build-standalone package ships with its own OpenSSL, and this module
configures it to use the certificates from the 'certifi' package.
"""
import site

try:
    import os
    import sys
    import certifi

    # Do not set SSL_CERT_FILE to our own if it is already set. Someone could
    # have their own certificate authority that they specify with this env var.
    #
    # To learn more about SSL_CERT_FILE and how it is being used by OpenSSL when
    # verifying certificates, visit
    # https://www.openssl.org/docs/man1.1.0/ssl/SSL_CTX_set_default_verify_paths.html
    if "SSL_CERT_FILE" not in os.environ and "DO_NOT_SET_SSL_CERT_FILE" not in os.environ:
        os.environ["SSL_CERT_FILE"] = certifi.where()

except Exception as e:
    print("Failed to set certifi.where() as SSL_CERT_FILE.", file=sys.stderr)
    print(e, file=sys.stderr)
    print("Set DO_NOT_SET_SSL_CERT_FILE to skip this step in RV's Python initialization.", file=sys.stderr)

try:
    import os

    if "DO_NOT_REORDER_PYTHON_PATH" not in os.environ:
        import site
        import sys

        prefixes = list(set(site.PREFIXES))

        # Python libs and site-packages is the first that should be in the PATH
        new_path_list = list(set(site.getsitepackages()))
        new_path_list.insert(0, os.path.dirname(new_path_list[0]))

        # Then any paths in RV's app package
        for path in sys.path:
            for prefix in prefixes:
                if path.startswith(prefix) is False:
                    continue

                if os.path.exists(path):
                    new_path_list.append(path)

        # Then the remaining paths
        for path in sys.path:
            if os.path.exists(path):
                new_path_list.append(path)

        # Save the new sys.path
        sys.path = new_path_list
        site.removeduppaths()

except Exception as e:
    print("Failed to reorder RV's Python search path", file=sys.stderr)
    print(e, file=sys.stderr)
    print("Set DO_NOT_REORDER_PYTHON_PATH to skip this step in RV's Python initialization.", file=sys.stderr)
'''


def get_python_interpreter_args(python_home: str, variant : str) -> List[str]:
    """
    Return the path to the python interpreter given a Python home.

    :param python_home: Python home of a Python package.
    :param variant: Build variant (Debug/Release).
    :return: List of arguments to run the python interpreter.
    """
    is_windows_debug = platform.system() == "Windows" and variant.lower() == "debug"
    python_name_pattern = "python_d*" if is_windows_debug else "python*"

    search_paths = [python_home, os.path.join(python_home, "bin")]
    python_interpreters = []
    for path in search_paths:
        python_interpreters.extend(glob.glob(os.path.join(path, python_name_pattern)))

    # Filter out directories and non-executables
    python_interpreters = [
        p for p in python_interpreters
        if os.path.isfile(p) and os.access(p, os.X_OK)
    ]

    # Sort to get the main interpreter first (e.g., python3.10 before python3.10-config)
    python_interpreters.sort(key=lambda p: (
        '-config' in os.path.basename(p),
        not ('_d' in os.path.basename(p) and is_windows_debug),
        len(os.path.basename(p)), # Shorter names first (python3 vs python3.10)
        os.path.basename(p)
    ))

    if not python_interpreters:
        raise FileNotFoundError(f"Could not find a suitable python interpreter in {python_home}")

    print(f"Found python interpreters: {python_interpreters}")
    python_interpreter = python_interpreters[0]
    print(f"Selected python interpreter: {python_interpreter}")

    return [python_interpreter, "-s", "-E"]


def patch_python_distribution(python_home: str) -> None:
    """
    Patch the python distribution to install required packages and add a
    sitecustomize.py module.

    :param python_home: Home of the Python installation to patch.
    """
    # With python-build-standalone, we no longer need to patch OpenSSL libraries.
    # The distribution is self-contained and relocatable.

    python_interpreter_args = get_python_interpreter_args(python_home, VARIANT)

    # -I : isolate Python from the user's environment
    python_interpreter_args.append("-I")

    # Ensure pip is installed and up-to-date
    ensure_pip_args = python_interpreter_args + ["-m", "ensurepip", "--upgrade"]
    print(f"Ensuring pip with: {' '.join(ensure_pip_args)}")
    subprocess.run(ensure_pip_args, check=True)

    pip_args = python_interpreter_args + ["-m", "pip"]

    # Install essential packages
    for package in ["pip", "certifi", "six", "wheel", "packaging", "requests"]:
        package_install_args = pip_args + [
            "install",
            "--upgrade",
            "--force-reinstall",
            package,
        ]
        print(f"Installing '{package}' with: {' '.join(package_install_args)}")
        subprocess.run(package_install_args, check=True)

    # Find the site-packages directory to install our custom module
    site_packages_list = glob.glob(
        os.path.join(python_home, "**", "site-packages"), recursive=True
    )
    if not site_packages_list:
        raise FileNotFoundError(f"Could not find site-packages directory in {python_home}")

    site_packages = site_packages_list[0]
    print(f"Site packages found at: {site_packages}")

    # Write the sitecustomize.py module
    site_customize_path = os.path.join(site_packages, "sitecustomize.py")
    if os.path.exists(site_customize_path):
        print(f"Overwriting existing sitecustomize.py at {site_customize_path}")
        os.remove(site_customize_path)

    print(f"Installing sitecustomize.py payload at {site_customize_path}")
    with open(site_customize_path, "w") as sitecustomize_file:
        sitecustomize_file.write(SITECUSTOMIZE_FILE_CONTENT)


def test_python_distribution(python_home: str) -> None:
    """
    Test the Python distribution to ensure it's relocatable and works as expected.

    :param python_home: Package root of a Python package.
    """
    # Test for relocatability by moving the installation to a temporary directory
    tmp_dir = os.path.join(tempfile.gettempdir(), str(uuid.uuid4()))
    os.makedirs(tmp_dir)
    tmp_python_home = os.path.join(tmp_dir, "python_test_install")
    
    try:
        print(f"Testing relocatability by moving {python_home} to {tmp_python_home}")
        shutil.move(python_home, tmp_python_home)

        python_interpreter_args = get_python_interpreter_args(tmp_python_home, VARIANT)

        # Note: We need to build opentimelineio from sources in Windows+Debug
        # because the official wheel links with the release version of
        # python while RV uses the debug version.
        build_opentimelineio = platform.system() == "Windows" and VARIANT == "Debug"
        if build_opentimelineio:
            print("Building opentimelineio from source for Windows Debug build")
            my_env = os.environ.copy()
            my_env["OTIO_CXX_DEBUG_BUILD"] = "1"
            python_lib = os.path.join(tmp_python_home, "libs", f"python{PYTHON_VERSION}_d.lib")
            my_env["CMAKE_ARGS"] = f"-DPython_LIBRARY={python_lib} -DCMAKE_INCLUDE_PATH={os.path.join(tmp_python_home, 'include')}"
            
            otio_install_args = python_interpreter_args + ["-m", "pip", "install", "."]
            subprocess.run(otio_install_args, env=my_env, cwd=OPENTIMELINEIO_SOURCE_DIR, check=True)

        # Install a package with C extensions to test the toolchain
        wheel_install_arg = python_interpreter_args + ["-m", "pip", "install", "cryptography"]
        if not build_opentimelineio:
            wheel_install_arg.append("opentimelineio")

        print(f"Validating wheel installation with: {' '.join(wheel_install_arg)}")
        subprocess.run(wheel_install_arg, check=True)

        # Run a series of import tests to validate the standard library
        validation_script = """
import os, sys, ssl, ctypes, zlib, sqlite3
# Test tkinter
try:
    import tkinter
except ImportError:
    import Tkinter as tkinter
# Test certifi and SSL env var
import certifi
print(f"Certifi path: {certifi.where()}")
print(f"SSL_CERT_FILE: {os.environ.get('SSL_CERT_FILE')}")
assert certifi.where() == os.environ['SSL_CERT_FILE']
# Test SSL context
ctx = ssl.create_default_context()
assert ctx.get_ca_certs()
print("Python validation script completed successfully!")
"""
        python_validation_args = python_interpreter_args + ["-c", validation_script]
        print(f"Validating python package with: {' '.join(python_validation_args)}")
        subprocess.run(python_validation_args, check=True)

    finally:
        print(f"Moving {tmp_python_home} back to {python_home}")
        if os.path.exists(tmp_python_home):
            shutil.move(tmp_python_home, python_home)
        if os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir)


def clean() -> None:
    """
    Run the clean step of the build. Removes output and temp directories.
    """
    if os.path.exists(OUTPUT_DIR):
        print(f"Removing output directory: {OUTPUT_DIR}")
        shutil.rmtree(OUTPUT_DIR)

    if os.path.exists(TEMP_DIR):
        print(f"Removing temp directory: {TEMP_DIR}")
        shutil.rmtree(TEMP_DIR)


def install() -> None:
    """
    Run the install step. It copies the extracted python-build-standalone
    files to the output directory and then patches and tests the installation.
    """
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR)

    # python-build-standalone archives extract their contents into a 'python' subdirectory.
    extracted_python_dir = SOURCE_DIR
    if not os.path.exists(extracted_python_dir):
        raise FileNotFoundError(
            f"Could not find the extracted 'python' directory in {SOURCE_DIR}. "
            f"Please check the archive structure."
        )

    print(f"Copying Python distribution from {extracted_python_dir} to {OUTPUT_DIR}")
    shutil.copytree(extracted_python_dir, OUTPUT_DIR, dirs_exist_ok=True)

    # On non-Windows, create a `python` symlink to `python3` for convenience.
    if platform.system() != "Windows":
        bin_dir = os.path.join(OUTPUT_DIR, "bin")
        python3_executable = os.path.join(bin_dir, "python3.11")
        python_symlink = os.path.join(bin_dir, "python")
        python3_symlink = os.path.join(bin_dir, "python3")
        if os.path.exists(python3_executable) and not os.path.lexists(python_symlink):
            print(f"Creating symlink: {python_symlink} -> python3")
            os.symlink("python3.11", python_symlink)
            os.symlink("python3.11", python3_symlink)

    files = os.listdir(bin_dir)
    print("cedrik", files)

    patch_python_distribution(OUTPUT_DIR)
    test_python_distribution(OUTPUT_DIR)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Build script for Python using python-build-standalone."
    )

    # Actions
    parser.add_argument("--clean", dest="clean", action="store_true", help="Clean build directories.")
    parser.add_argument("--install", dest="install", action="store_true", help="Install the Python distribution.")

    # Paths
    parser.add_argument("--source-dir", dest="source", type=pathlib.Path, required=True, help="Directory where the Python archive was extracted.")
    parser.add_argument("--temp-dir", dest="temp", type=pathlib.Path, required=True, help="Directory for temporary build files.")
    parser.add_argument("--output-dir", dest="output", type=pathlib.Path, required=True, help="Final installation directory for Python.")
    
    # Configuration
    parser.add_argument("--variant", dest="variant", type=str, required=True, choices=["Release", "Debug"], help="Build variant.")
    parser.add_argument("--arch", dest="arch", type=str, required=False, default="", help="Target architecture.")
    parser.add_argument("--vfx_platform", dest="vfx_platform", type=int, required=True, help="VFX Platform year (e.g., 2023, 2024).")
    
    # Optional Dependencies
    parser.add_argument("--opentimelineio-source-dir", dest="otio_source_dir", type=str, required=False, default="", help="Source directory for OpenTimelineIO (for Windows Debug builds).")

    if platform.system() == "Windows":
        parser.add_argument("--python-version", dest="python_version", type=str, required=True, help="Major and minor Python version, e.g., '310' for 3.10.")

    args = parser.parse_args()

    # Set global variables from arguments
    SOURCE_DIR = args.source
    OUTPUT_DIR = args.output
    TEMP_DIR = args.temp
    VARIANT = args.variant
    ARCH = args.arch

    files = os.listdir(SOURCE_DIR)
    print("cedrik", files)
    
    OPENTIMELINEIO_SOURCE_DIR = args.otio_source_dir
    if platform.system() == "Windows":
        PYTHON_VERSION = args.python_version

    # Execute requested actions
    if args.clean:
        clean()

    if args.install:
        install()

    if not args.clean and not args.install:
        print("No action specified. Use --install or --clean.")
        parser.print_help()
    
