import argparse
import glob
import os
import pathlib
import shutil
import subprocess
import platform
import tempfile
import uuid
from typing import List

# Global variables (updated to reflect new usage)
SOURCE_DIR = ""  # No longer directly used for CPython source
OUTPUT_DIR = ""
TEMP_DIR = ""
VARIANT = ""
ARCH = ""
PERL_ROOT = ""
LIB_DIR = ""
VFX_PLATFORM = ""
PYTHON_VERSION = "" # Added for consistency with other scripts

SITECUSTOMIZE_FILE_CONTENT = """
import os
import sys

# Set SSL_CERT_FILE environment variable for Python's SSL module
# This is crucial for applications that rely on SSL certificates,
# especially when running in environments where certifi is used.
if "DO_NOT_SET_SSL_CERT_FILE" not in os.environ:
    try:
        import certifi
        os.environ["SSL_CERT_FILE"] = certifi.where()
    except ImportError:
        pass # certifi is not available, SSL_CERT_FILE will not be set

# Add the 'DLLs' directory to PATH on Windows for Python modules
# that depend on DLLs not directly in the Python executable's directory.
if sys.platform == "win32":
    dlls_path = os.path.join(sys.prefix, "DLLs")
    if os.path.isdir(dlls_path):
        os.environ["PATH"] = dlls_path + os.path.pathsep + os.environ.get("PATH", "")
"""

def get_python_interpreter_args(python_home: str, variant: str) -> List[str]:
    """
    Returns the arguments needed to invoke the Python interpreter.

    Args:
        python_home (str): The root directory of the Python installation.
        variant (str): The build variant (e.g., "Debug", "Release").

    Returns:
        List[str]: A list of strings representing the Python interpreter command.
    """
    if platform.system() == "Windows":
        # On Windows, the executable might be python_d.exe in Debug builds
        python_exe_name = "python.exe"
        if variant == "Debug":
            python_exe_name = "python_d.exe"
        python_executable = os.path.join(python_home, "bin", python_exe_name)
    else:
        # On Linux/macOS, it's typically python3
        python_executable = os.path.join(python_home, "bin", "python3")

    if not os.path.exists(python_executable):
        raise FileNotFoundError(f"Python executable not found at: {python_executable}")

    return [python_executable]

def patch_python_distribution(python_home: str) -> None:
    """
    Performs post-installation patching and setup for the Python distribution.
    This includes installing sitecustomize.py.

    Args:
        python_home (str): The root directory of the Python installation.
    """
    print(f"Patching Python distribution at {python_home}")

    # Ensure pip and other essential packages are installed/upgraded
    python_interpreter_args = get_python_interpreter_args(python_home, VARIANT)
    # -I : isolate Python from the user's environment
    python_interpreter_args.append("-I")

    # Ensure pip is available
    ensure_pip_args = python_interpreter_args + ["-m", "ensurepip"]
    print(f"Ensuring pip with {ensure_pip_args}")
    subprocess.run(ensure_pip_args, check=True)

    # Upgrade essential packages
    pip_args = python_interpreter_args + ["-m", "pip"]
    for package in ["pip", "certifi", "six", "wheel", "packaging", "requests"]:
        package_install_args = pip_args + [
            "install",
            "--upgrade",
            "--force-reinstall",
            package,
        ]
        print(f"Installing {package} with {package_install_args}")
        subprocess.run(package_install_args, check=True)

    # Install wheel again for good measure
    wheel_install_args = pip_args + [
        "install",
        "--upgrade",
        "--force-reinstall",
        "wheel",
    ]
    print(f"Installing wheel with {wheel_install_args}")
    subprocess.run(wheel_install_args, check=True)

    # Install sitecustomize.py
    site_packages = glob.glob(
        os.path.join(python_home, "**", "site-packages"), recursive=True
    )
    if not site_packages:
        raise FileNotFoundError("Site-packages directory not found in Python installation.")
    site_packages = site_packages[0] # Take the first one found

    site_customize_path = os.path.join(site_packages, "sitecustomize.py")
    if os.path.exists(site_customize_path):
        print(f"Found existing sitecustomize.py at {site_customize_path}, overwriting.")
        os.remove(site_customize_path)
    print(f"Installing sitecustomize.py payload at {site_customize_path}")
    with open(site_customize_path, "w") as sitecustomize_file:
        sitecustomize_file.write(SITECUSTOMIZE_FILE_CONTENT)

def test_python_distribution(python_home: str) -> None:
    """
    Tests the Python distribution to ensure core modules and functionalities are working.

    Args:
        python_home (str): The root directory of the Python installation.
    """
    tmp_dir = os.path.join(tempfile.gettempdir(), str(uuid.uuid4()))
    os.makedirs(tmp_dir)
    tmp_python_home = os.path.join(tmp_dir, os.path.basename(python_home))
    OPENTIMELINEIO_SOURCE_DIR = "" # Define or pass if needed for OTIO testing

    try:
        print(f"Moving {python_home} to {tmp_python_home} for testing.")
        shutil.move(python_home, tmp_python_home)

        python_interpreter_args = get_python_interpreter_args(tmp_python_home, VARIANT)

        # Build and test OpenTimelineIO if on Windows Debug (as per original logic)
        build_opentimelineio = platform.system() == "Windows" and VARIANT == "Debug"
        if build_opentimelineio and OPENTIMELINEIO_SOURCE_DIR: # Ensure OPENTIMELINEIO_SOURCE_DIR is defined
            print("Building opentimelineio for testing.")
            my_env = os.environ.copy()
            my_env["OTIO_CXX_DEBUG_BUILD"] = "1"
            python_include_dirs = os.path.join(tmp_python_home, "include")
            python_lib = os.path.join(
                tmp_python_home, "libs", f"python{PYTHON_VERSION}_d.lib"
            )
            my_env["CMAKE_ARGS"] = (
                f"-DPython_LIBRARY={python_lib} -DCMAKE_INCLUDE_PATH={python_include_dirs}"
            )
            opentimelineio_install_arg = python_interpreter_args + [
                "-m",
                "pip",
                "install",
                ".",
            ]
            subprocess.run(
                opentimelineio_install_arg, env=my_env, cwd=OPENTIMELINEIO_SOURCE_DIR, check=True
            )
            otio_module_dir = os.path.join(
                tmp_python_home, "lib", "site-packages", "opentimelineio"
            )
            for _file in os.listdir(otio_module_dir):
                if _file.endswith("pyd"):
                    otio_lib_name_split = os.path.basename(_file).split(".")
                    if len(otio_lib_name_split) > 2:
                        new_otio_lib_name = (
                            otio_lib_name_split[0].replace("d_d", "_d") + ".pyd"
                        )
                        src_file = os.path.join(otio_module_dir, _file)
                        dst_file = os.path.join(otio_module_dir, new_otio_lib_name)
                        shutil.copyfile(src_file, dst_file)

        # Validate installation of a wheel (e.g., cryptography or opentimelineio)
        wheel_install_arg = python_interpreter_args + ["-m", "pip", "install", "cryptography"]
        if not build_opentimelineio:
            # Only add opentimelineio if it wasn't built/installed above
            wheel_install_arg.append("opentimelineio")
        print(f"Validating wheel installation with {wheel_install_arg}")
        subprocess.run(wheel_install_arg, check=True)

        # Run a series of Python imports and assertions to validate the environment
        python_validation_args = python_interpreter_args + [
            "-c",
            "\n".join(
                [
                    "try:",
                    " import tkinter",
                    "except:",
                    " import Tkinter as tkinter",
                    "import certifi",
                    "import os",
                    "assert certifi.where() == os.environ['SSL_CERT_FILE']",
                    "import ssl",
                    "import sqlite3",
                    "import ctypes",
                    "import ssl",
                    "import _ssl",
                    "import zlib",
                ]
            ),
        ]
        print(f"Validating the python package with {python_validation_args}")
        subprocess.run(python_validation_args, check=True)

        # Test SSL_CERT_FILE environment variable handling
        dummy_ssl_file = os.path.join("Path", "To", "Dummy", "File")
        python_validation2_args = python_interpreter_args + [
            "-c",
            "\n".join(
                [
                    "import os",
                    f"assert os.environ['SSL_CERT_FILE'] == '{dummy_ssl_file}'",
                ]
            ),
        ]
        print(f"Validating SSL_CERT_FILE override with {python_validation2_args}")
        subprocess.run(
            python_validation2_args, env={**os.environ, "SSL_CERT_FILE": dummy_ssl_file}, check=True
        )

        python_validation3_args = python_interpreter_args + [
            "-c",
            "\n".join(
                [
                    "import os",
                    "assert 'SSL_CERT_FILE' not in os.environ",
                ]
            ),
        ]
        print(f"Validating DO_NOT_SET_SSL_CERT_FILE with {python_validation3_args}")
        subprocess.run(
            python_validation3_args, env={**os.environ, "DO_NOT_SET_SSL_CERT_FILE": "bleh"}, check=True
        )

    finally:
        print(f"Moving {tmp_python_home} back to {python_home}.")
        shutil.move(tmp_python_home, python_home)
        # Clean up the temporary directory
        if os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir)

def clean() -> None:
    """
    Cleans up the output and temporary directories.
    """
    if os.path.exists(OUTPUT_DIR):
        print(f"Removing output directory: {OUTPUT_DIR}")
        shutil.rmtree(OUTPUT_DIR)
    if os.path.exists(TEMP_DIR):
        print(f"Removing temporary directory: {TEMP_DIR}")
        shutil.rmtree(TEMP_DIR)
    # No git clean needed for source as we're not building from source anymore.

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--clean", dest="clean", action="store_true")
    # Removed --configure, --build, --install as they are no longer handled here
    parser.add_argument("--source-dir", dest="source", type=pathlib.Path, required=False, default="") # No longer required for CPython build
    parser.add_argument("--output-dir", dest="output", type=pathlib.Path, required=True)
    parser.add_argument("--temp-dir", dest="pathlib.Path", required=True)
    parser.add_argument("--arch", dest="arch", type=str, required=False, default="")
    parser.add_argument("--perlroot", dest="perlroot", type=str, required=False, default="")
    parser.add_argument("--vfx_platform", dest="vfx_platform", type=int, required=True)
    parser.add_argument("--python-version", dest="python_version", type=str, required=True, default="")
    parser.add_argument("--variant", dest="variant", type=str, required=True)
    parser.add_argument("--opentimelineio-source-dir", dest="opentimelineio_source_dir", type=pathlib.Path, required=False)

    parser.set_defaults(clean=False)
    args = parser.parse_args()

    # Assign global variables from parsed arguments
    SOURCE_DIR = str(args.source) # Keep as str for consistency with os.path
    OUTPUT_DIR = str(args.output)
    TEMP_DIR = str(args.temp)
    ARCH = args.arch
    PERL_ROOT = args.perlroot
    VFX_PLATFORM = args.vfx_platform
    PYTHON_VERSION = args.python_version
    # Removed OPENSSL_OUTPUT_DIR assignment
    VARIANT = args.variant
    OPENTIMELINEIO_SOURCE_DIR = str(args.opentimelineio_source_dir) if args.opentimelineio_source_dir else ""

    if platform.system() == "Darwin":
        LIB_DIR = "lib"
    else:
        if VFX_PLATFORM == 2023:
            LIB_DIR = "lib"
        elif VFX_PLATFORM == 2024:
            LIB_DIR = "lib64"

    if args.clean:
        clean()

    # The configure, build, install steps for CPython are now handled by CMake directly
    # downloading and extracting python-build-standalone.
    # This script now primarily serves utility functions for other build steps (e.g., PySide).
    # You might call patch_python_distribution or test_python_distribution from here
    # if they are still needed as standalone steps after the CMake ExternalProject.
    # For this refactoring, the calls are moved to CMake's POST_BUILD or custom commands.

    # Example of how you *would* call these if needed as a standalone script:
    # if args.install: # Assuming 'install' now means post-extraction setup
    #     patch_python_distribution(OUTPUT_DIR)
    #     test_python_distribution(OUTPUT_DIR)
