#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# *****************************************************************************
# Copyright 2024 Autodesk, Inc. All rights reserved.
#
# SPDX-License-Identifier: Apache-2.0
#
# *****************************************************************************

import argparse
import glob
import os
import re
import pathlib
import shutil
import subprocess
import platform
import tempfile
import uuid

from utils import (
    download_file,
    extract_7z_archive,
    verify_7z_archive,
    source_widows_msvc_env,
    update_env_path,
)
from make_python import get_python_interpreter_args

SOURCE_DIR = ""
OUTPUT_DIR = ""
TEMP_DIR = ""
VARIANT = ""

QT_OUTPUT_DIR = ""
PYTHON_OUTPUT_DIR = ""
OPENSSL_OUTPUT_DIR = ""

LIBCLANG_URL_BASE = "https://mirrors.ocf.berkeley.edu/qt/development_releases/prebuilt/libclang/libclang-release_"


def get_cmake_generator():
    """Get the appropriate CMake generator for the current platform."""
    system = platform.system()
    if system == "Windows":
        return "Ninja"
    elif system == "Darwin":
        return "Ninja"
    else:  # Linux
        return "Ninja"


def get_python_executable():
    """Get the Python executable path."""
    python_interpreter_args = get_python_interpreter_args(str(PYTHON_OUTPUT_DIR), VARIANT)
    return python_interpreter_args[0]


def get_python_cmake_variables():
    """Get comprehensive Python CMake variables for FindPython."""
    python_exe = get_python_executable()
    python_home = str(PYTHON_OUTPUT_DIR)
    
    # Get Python version info
    version_cmd = [python_exe, "-c", "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"]
    python_version = subprocess.check_output(version_cmd, text=True).strip()
    
    # Get Python library path
    if platform.system() == "Windows":
        lib_name = f"python{python_version.replace('.', '')}.lib"
        lib_path = os.path.join(python_home, "libs", lib_name)
        dll_name = f"python{python_version.replace('.', '')}.dll"
        dll_path = os.path.join(python_home, dll_name)
    else:
        lib_name = f"libpython{python_version}.so" if platform.system() == "Linux" else f"libpython{python_version}.dylib"
        lib_path = os.path.join(python_home, "lib", lib_name)
        dll_path = lib_path
    
    # Get Python include directory
    include_dir = os.path.join(python_home, "include")
    if platform.system() == "Windows":
        include_dir = python_home  # On Windows, headers are in the root
    else:
        # Try to find the correct include directory
        python_include = os.path.join(python_home, "include", f"python{python_version}")
        if os.path.exists(python_include):
            include_dir = python_include
    
    # Get site-packages directory
    site_packages_cmd = [python_exe, "-c", "import site; print(site.getsitepackages()[0])"]
    try:
        site_packages = subprocess.check_output(site_packages_cmd, text=True).strip()
    except:
        site_packages = os.path.join(python_home, "lib", f"python{python_version}", "site-packages")
    
    cmake_vars = [
        # Primary Python executable
        f"-DPython_EXECUTABLE={python_exe}",
        
        # Python version
        f"-DPython_VERSION={python_version}",
        f"-DPython_VERSION_MAJOR={python_version.split('.')[0]}",
        f"-DPython_VERSION_MINOR={python_version.split('.')[1]}",
        
        # Python library
        f"-DPython_LIBRARY={lib_path}",
        f"-DPython_LIBRARIES={lib_path}",
        
        # Python include directory
        f"-DPython_INCLUDE_DIR={include_dir}",
        f"-DPython_INCLUDE_DIRS={include_dir}",
        
        # Python root directory
        f"-DPython_ROOT_DIR={python_home}",
        f"-DPython_ROOT={python_home}",
        
        # Site packages
        f"-DPython_SITEARCH={site_packages}",
        f"-DPython_SITELIB={site_packages}",
        
        # Additional Python paths
        f"-DPYTHON_EXECUTABLE={python_exe}",  # Legacy variable
        f"-DPYTHON_LIBRARY={lib_path}",       # Legacy variable
        f"-DPYTHON_INCLUDE_DIR={include_dir}", # Legacy variable
        
        # PySide-specific variables
        f"-DQFP_PYTHON_TARGET_PATH={python_home}",
        f"-DPYSIDE_PYTHON_PATH={python_home}",
    ]
    
    # Add Windows-specific variables
    if platform.system() == "Windows":
        cmake_vars.extend([
            f"-DPython_LIBRARY_RELEASE={lib_path}",
            f"-DPython_RUNTIME_LIBRARY_DIRS={python_home}",
        ])
        # Add DLL path if it exists
        if os.path.exists(dll_path):
            cmake_vars.append(f"-DPython_RUNTIME_LIBRARY={dll_path}")
    
    return cmake_vars


def get_qt_cmake_path():
    """Get the Qt CMake path."""
    return os.path.join(str(QT_OUTPUT_DIR), "lib", "cmake")


def get_cmake_build_type():
    """Get the CMake build type based on variant."""
    return "Debug" if VARIANT == "Debug" else "Release"


def configure_cmake():
    """Configure PySide6 using CMake directly."""
    build_dir = os.path.join(TEMP_DIR, "pyside6_build")
    if os.path.exists(build_dir):
        shutil.rmtree(build_dir)
    os.makedirs(build_dir)
    
    # Determine platform-specific executable extension
    exe_ext = ".exe" if platform.system() == "Windows" else ""
    
    cmake_args = [
        "cmake",
        str(SOURCE_DIR),  # Convert PosixPath to string
        "-G", get_cmake_generator(),
        f"-DCMAKE_BUILD_TYPE={get_cmake_build_type()}",
        f"-DCMAKE_INSTALL_PREFIX={OUTPUT_DIR}",
        f"-DCMAKE_PREFIX_PATH={get_qt_cmake_path()}",
        f"-DQT_HOST_PATH={QT_OUTPUT_DIR}",
        f"-DQFP_QT_HOST_PATH={QT_OUTPUT_DIR}",
        "-DPYSIDE_STANDALONE=ON",
        "-DSETUPTOOLS_IGNORE_GIT=ON",
        "-DCMAKE_VERBOSE_MAKEFILE=ON",
        "-DLOG_LEVEL=VERBOSE",
        f"-DCMAKE_JOB_POOLS=all={os.cpu_count() or 1}",
        f"--debug-find-pkg=Python",
        f"--debug-find-pkg=Python3",
        f"--trace-source=FindPython.cmake",
        f"--trace-source=FindPython3.cmake",
    ]
    
    # Add comprehensive Python variables
    python_cmake_vars = get_python_cmake_variables()
    cmake_args.extend(python_cmake_vars)
    
    # Add OpenSSL support if available
    if OPENSSL_OUTPUT_DIR:
        cmake_args.extend([
            f"-DOPENSSL_ROOT_DIR={OPENSSL_OUTPUT_DIR}",
            f"-DOPENSSL_LIBRARIES={os.path.join(str(OPENSSL_OUTPUT_DIR), 'lib')}",
            f"-DOPENSSL_INCLUDE_DIR={os.path.join(str(OPENSSL_OUTPUT_DIR), 'include')}",
        ])
    
    # Platform-specific configurations
    if platform.system() == "Windows":
        cmake_args.extend([
            "-DCMAKE_CXX_COMPILER=cl",
            "-DCMAKE_C_COMPILER=cl",
        ])
    
    print(f"Configuring with CMake: {' '.join(cmake_args)}")
    
    # Change to build directory and run cmake
    original_cwd = os.getcwd()
    try:
        os.chdir(build_dir)
        subprocess.run(cmake_args).check_returncode()
    finally:
        os.chdir(original_cwd)
    
    return build_dir


def build_cmake(build_dir):
    """Build PySide6 using CMake."""
    cmake_build_args = [
        "cmake",
        "--build", build_dir,
        "--config", get_cmake_build_type(),
        "--parallel", str(os.cpu_count() or 1),
        "--verbose"
    ]
    
    print(f"Building with CMake: {' '.join(cmake_build_args)}")
    subprocess.run(cmake_build_args).check_returncode()


def install_cmake(build_dir):
    """Install PySide6 using CMake."""
    cmake_install_args = [
        "cmake",
        "--install", build_dir,
        "--config", get_cmake_build_type(),
        "--verbose"
    ]
    
    print(f"Installing with CMake: {' '.join(cmake_install_args)}")
    subprocess.run(cmake_install_args).check_returncode()


def test_python_distribution(python_home: str) -> None:
    """
    Test the Python distribution.

    :param python_home: Package root of an Python package
    """
    tmp_dir = os.path.join(tempfile.gettempdir(), str(uuid.uuid4()))
    os.makedirs(tmp_dir)

    tmp_python_home = os.path.join(tmp_dir, os.path.basename(python_home))
    try:
        print(f"Moving {python_home} to {tmp_python_home}")
        shutil.move(python_home, tmp_python_home)

        python_validation_args = get_python_interpreter_args(tmp_python_home, VARIANT) + [
            "-c",
            "\n".join(
                [
                    "from PySide6 import *",
                    "from PySide6 import QtWebEngineCore",
                ]
            ),
        ]
        print(f"Validating the PySide package with {python_validation_args}")
        subprocess.run(python_validation_args).check_returncode()
    finally:
        print(f"Moving {tmp_python_home} to {python_home}")
        shutil.move(tmp_python_home, python_home)


def prepare() -> None:
    """
    Run the clean step of the build. Removes everything.
    """
    if os.path.exists(TEMP_DIR) is False:
        os.makedirs(TEMP_DIR)

    # PySide6 requires Clang 13+.
    print("Setting up Clang...")
    clang_filename_suffix = ""
    fallback_clang_filename_suffix = None

    system = platform.system()
    if system == "Darwin":

        def get_clang_version():
            version_output = os.popen("clang --version").read()
            version_search = re.search(r"version (\d+)\.(\d+)\.(\d+)", version_output)
            if version_search:
                return version_search.groups()
            print(f"ERROR: Could not extract clang --version")
            return None

        def get_clang_filename_suffix(version):
            version_str = ".".join(version)
            return f"{version_str}-based-macos-universal.7z"

        def get_fallback_clang_filename_suffix(version):
            major_minor_version_str = ".".join(version[:2])
            if major_minor_version_str == "14.0":
                return "14.0.3-based-macos-universal.7z"
            elif major_minor_version_str == "17.0":
                return "17.0.1-based-macos-universal.7z"
            return None

        clang_version = get_clang_version()
        if clang_version:
            clang_filename_suffix = get_clang_filename_suffix(clang_version)
            fallback_clang_filename_suffix = get_fallback_clang_filename_suffix(
                clang_version
            )

    elif system == "Linux":
        clang_filename_suffix = "19.1.0-based-linux-Rhel8.8-gcc10.3-x86_64.7z"
    elif system == "Windows":
        clang_filename_suffix = "19.1.0-based-windows-vs2019_64.7z"

    download_url = LIBCLANG_URL_BASE + clang_filename_suffix
    libclang_zip = os.path.join(TEMP_DIR, "libclang.7z")

    # if we have a failed download, clean it up and redownload.
    # checking for False since it can return None when archive doesn't have a CRC
    if os.path.exists(libclang_zip) and verify_7z_archive(libclang_zip) is False:
        os.remove(libclang_zip)

    # download it if necessary
    if os.path.exists(libclang_zip) is False:
        download_ok = download_file(download_url, libclang_zip)
        if not download_ok and fallback_clang_filename_suffix:
            fallback_download_url = LIBCLANG_URL_BASE + fallback_clang_filename_suffix
            print(
                f"WARNING: Could not download or version does not exist: {download_url}"
            )
            print(
                f"WARNING: Attempting to fallback on known version: {fallback_download_url}..."
            )
            download_ok = download_file(fallback_download_url, libclang_zip)
        if not download_ok:
            print(
                f"ERROR: Could not download or version does not exist: {download_url}"
            )

    # clean up previous failed extraction
    libclang_tmp = os.path.join(TEMP_DIR, "libclang-tmp")
    if os.path.exists(libclang_tmp) is True:
        shutil.rmtree(libclang_tmp)

    # extract to a temp location and only move if successful
    libclang_extracted = os.path.join(TEMP_DIR, "libclang")
    if os.path.exists(libclang_extracted) is False:
        extract_7z_archive(libclang_zip, libclang_tmp)
        shutil.move(libclang_tmp, libclang_extracted)

    libclang_install_dir = os.path.join(libclang_extracted, "libclang")
    if OPENSSL_OUTPUT_DIR:
        os.environ["PATH"] = os.path.pathsep.join(
            [
                os.path.join(OPENSSL_OUTPUT_DIR, "bin"),
                os.environ.get("PATH", ""),
            ]
        )

    print(f"PATH={os.environ['PATH']}")

    os.environ["LLVM_INSTALL_DIR"] = libclang_install_dir
    os.environ["CLANG_INSTALL_DIR"] = libclang_install_dir

    # PySide6 build requires numpy 1.26.3
    install_numpy_args = get_python_interpreter_args(PYTHON_OUTPUT_DIR, VARIANT) + [
        "-m",
        "pip",
        "install",
        "numpy==1.26.3",
    ]
    print(f"Installing numpy with {install_numpy_args}")
    subprocess.run(install_numpy_args).check_returncode()

    # Patch CMakeLists.txt to disable libxslt
    cmakelist_path = os.path.join(
        SOURCE_DIR, "sources", "shiboken6", "ApiExtractor", "CMakeLists.txt"
    )
    old_cmakelist_path = os.path.join(
        SOURCE_DIR, "sources", "shiboken6", "ApiExtractor", "CMakeLists.txt.old"
    )
    if os.path.exists(old_cmakelist_path):
        os.remove(old_cmakelist_path)

    os.rename(cmakelist_path, old_cmakelist_path)
    with open(old_cmakelist_path) as old_cmakelist:
        with open(cmakelist_path, "w") as cmakelist:
            for line in old_cmakelist:
                new_line = line.replace(
                    " set(HAS_LIBXSLT 1)",
                    " #set(HAS_LIBXSLT 1)",
                )
                cmakelist.write(new_line)


def remove_broken_shortcuts(python_home: str) -> None:
    """
    Remove broken Python shortcuts that depend on the absolute
    location of the Python executable.

    Note that this method will also remove scripts like
    pip, easy_install and wheel that were left around by
    previous steps of the build pipeline.

    :param str python_home: Path to the Python folder.
    """
    if platform.system() == "Windows":
        # All executables inside Scripts have a hardcoded
        # absolute path to the python, which can't be relied
        # upon, so remove all scripts.
        scripts_dir = os.path.join(python_home, "Scripts")
        if os.path.exists(scripts_dir):
            shutil.rmtree(scripts_dir)
    else:
        # Aside from the python executables, every other file
        # in the build is a script that does not support
        bin_dir = os.path.join(python_home, "bin")
        if os.path.exists(bin_dir):
            for filename in os.listdir(bin_dir):
                filepath = os.path.join(bin_dir, filename)
                if filename not in [
                    "python",
                    "python3",
                    f"python{PYTHON_VERSION}",
                ]:
                    print(f"Removing {filepath}...")
                    os.remove(filepath)
                else:
                    print(f"Keeping {filepath}...")


def cleanup_shiboken_generator():
    """Remove shiboken6_generator after build."""
    python_interpreter_args = get_python_interpreter_args(str(PYTHON_OUTPUT_DIR), VARIANT)
    
    generator_cleanup_args = python_interpreter_args + [
        "-m",
        "pip",
        "uninstall",
        "-y",
        "shiboken6_generator",
    ]

    print(f"Executing {generator_cleanup_args}")
    subprocess.run(generator_cleanup_args).check_returncode()

    # Even if we remove shiboken6_generator from pip, the files stay... for some reasons
    generator_cleanup_args = python_interpreter_args + [
        "-c",
        "\n".join(
            [
                "import os, shutil",
                "try:",
                "  import shiboken6_generator",
                "except:",
                "  exit(0)",
                "shutil.rmtree(os.path.dirname(shiboken6_generator.__file__))",
            ]
        ),
    ]

    print(f"Executing {generator_cleanup_args}")
    subprocess.run(generator_cleanup_args).check_returncode()


def copy_openssl_libraries():
    """Copy OpenSSL libraries to PySide6 folder on Windows."""
    if OPENSSL_OUTPUT_DIR and platform.system() == "Windows":
        pyside_folders = glob.glob(
            os.path.join(str(PYTHON_OUTPUT_DIR), "**", "site-packages", "PySide6"), recursive=True
        )
        if pyside_folders:
            pyside_folder = pyside_folders[0]
            openssl_libs = glob.glob(os.path.join(str(OPENSSL_OUTPUT_DIR), "bin", "lib*"))

            for lib in openssl_libs:
                print(f"Copying {lib} into {pyside_folder}")
                shutil.copy(lib, pyside_folder)


def build() -> None:
    """
    Run the build step using CMake directly instead of setup.py.
    """
    # Configure CMake
    build_dir = configure_cmake()
    
    # Build with CMake
    build_cmake(build_dir)
    
    # Install with CMake
    install_cmake(build_dir)
    
    # Post-build cleanup
    cleanup_shiboken_generator()
    copy_openssl_libraries()
    remove_broken_shortcuts(str(PYTHON_OUTPUT_DIR))
    
    # Test the distribution
    test_python_distribution(str(PYTHON_OUTPUT_DIR))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--prepare", dest="prepare", action="store_true")
    parser.add_argument("--build", dest="build", action="store_true")

    parser.add_argument("--source-dir", dest="source", type=pathlib.Path, required=True)
    parser.add_argument("--python-dir", dest="python", type=pathlib.Path, required=True)
    parser.add_argument("--qt-dir", dest="qt", type=pathlib.Path, required=True)
    parser.add_argument(
        "--openssl-dir", dest="openssl", type=pathlib.Path, required=False
    )
    parser.add_argument("--temp-dir", dest="temp", type=pathlib.Path, required=True)
    parser.add_argument("--output-dir", dest="output", type=pathlib.Path, required=True)

    parser.add_argument("--variant", dest="variant", type=str, required=True)

    # Major and minor version with dots.
    parser.add_argument(
        "--python-version", dest="python_version", type=str, required=True, default=""
    )

    parser.set_defaults(prepare=False, build=False)

    args = parser.parse_args()

    SOURCE_DIR = args.source
    OUTPUT_DIR = args.output
    TEMP_DIR = args.temp
    OPENSSL_OUTPUT_DIR = args.openssl
    PYTHON_OUTPUT_DIR = args.python
    QT_OUTPUT_DIR = args.qt
    VARIANT = args.variant
    PYTHON_VERSION = args.python_version
    print(args)

    if args.prepare:
        prepare()

    if args.build:
        build()
