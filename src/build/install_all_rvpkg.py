#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse
import os
import pathlib
import subprocess
import sys
from typing import Generator


def get_packages_from_dir(
    packages_source_folder: pathlib.Path,
) -> Generator[pathlib.Path, None, None]:
    for file in sorted(packages_source_folder.iterdir()):
        if file.is_file() and file.suffix == ".rvpkg":
            yield file.resolve()


def install_rvpkg_packages(
    *,
    rvpkg_path: pathlib.Path,
    packages_source_folder: pathlib.Path,
    packages_destination_folder: pathlib.Path,
) -> None:
    # Convert all Path objects to strings to avoid issues with different Python environments
    # This is especially important when running in Conan builds with custom Python installations
    command = [
        str(rvpkg_path),
        "-force",
        "-install",
        "-add",
        str(packages_destination_folder.resolve()),
        *[str(pkg) for pkg in get_packages_from_dir(packages_source_folder)],
    ]

    print(f"Installing RV packages with command: {' '.join(command)}")
    print(f"Python executable: {sys.executable}")
    print(f"Working directory: {os.getcwd()}")

    # Set up environment for rvpkg.exe to find its dependencies
    env = os.environ.copy()

    # Add the directory containing rvpkg.exe to PATH so it can find its DLLs
    rvpkg_dir = str(pathlib.Path(rvpkg_path).parent)
    if "PATH" in env:
        env["PATH"] = f"{rvpkg_dir};{env['PATH']}"
    else:
        env["PATH"] = rvpkg_dir

    # Add common library paths that rvpkg might need
    stage_lib_dir = str(pathlib.Path(rvpkg_dir).parent / "lib")
    if pathlib.Path(stage_lib_dir).exists():
        env["PATH"] = f"{stage_lib_dir};{env['PATH']}"
        print(f"Added lib directory to PATH: {stage_lib_dir}")

    # Set LANG to C to avoid locale issues (as done in the wrapper script)
    env["LANG"] = "C"
    env["LC_ALL"] = "C"

    print(f"Environment PATH: {env.get('PATH', 'Not set')[:200]}...")
    print(f"Environment LANG: {env.get('LANG', 'Not set')}")

    # List files in the rvpkg.exe directory for debugging
    rvpkg_parent = pathlib.Path(rvpkg_path).parent
    print(f"Files in rvpkg.exe directory ({rvpkg_parent}):")
    try:
        files_in_dir = list(rvpkg_parent.iterdir())
        if files_in_dir:
            # Show first 20 files to avoid too much output
            files_in_dir.sort(key=lambda x: x.name.lower())
            for i, file_path in enumerate(files_in_dir[:20]):
                if file_path.is_file():
                    size = file_path.stat().st_size
                    print(f"  {file_path.name} ({size:,} bytes)")
                elif file_path.is_dir():
                    print(f"  {file_path.name}/ (directory)")
            if len(files_in_dir) > 20:
                print(f"  ... and {len(files_in_dir) - 20} more files/directories")
        else:
            print("  (directory is empty)")
    except Exception as e:
        print(f"  ERROR: Could not list directory contents: {e}")

    # First, test if rvpkg.exe can run at all (with --help or similar)
    print("Testing if rvpkg.exe can execute...")
    try:
        test_result = subprocess.run(
            [str(rvpkg_path), "-help"],
            capture_output=True,
            text=True,
            timeout=30,  # Don't wait too long
            env=env,
        )
        print(f"rvpkg.exe test run return code: {test_result.returncode}")
        if test_result.stdout:
            print(
                f"rvpkg.exe test stdout (first 500 chars): {test_result.stdout[:500]}"
            )
        if test_result.stderr:
            print(
                f"rvpkg.exe test stderr (first 500 chars): {test_result.stderr[:500]}"
            )
    except subprocess.TimeoutExpired:
        print("WARNING: rvpkg.exe test run timed out")
    except Exception as e:
        print(f"WARNING: rvpkg.exe test run failed: {e}")

    try:
        # Use more robust subprocess call with better error handling
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,  # Don't raise exception immediately, handle it ourselves
            env=env,  # Pass the modified environment
        )

        if result.returncode != 0:
            print(f"ERROR: rvpkg command failed with return code {result.returncode}")
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
            print(f"Command that failed: {' '.join(command)}")

            # If we got the same access violation error, try a different approach
            if result.returncode == 3221225781:
                print(
                    "Detected access violation error (3221225781). This usually means:"
                )
                print("1. Missing DLL dependencies (Qt, MSVC runtime, etc.)")
                print("2. Incompatible runtime environment")
                print("3. Memory access issues in the executable")
                print("")
                print("Troubleshooting information:")
                print(f"- rvpkg.exe path: {rvpkg_path}")
                print(f"- rvpkg.exe exists: {pathlib.Path(rvpkg_path).exists()}")
                print(
                    f"- rvpkg.exe size: {pathlib.Path(rvpkg_path).stat().st_size if pathlib.Path(rvpkg_path).exists() else 'N/A'} bytes"
                )

                # List all files in the rvpkg.exe directory
                rvpkg_parent = pathlib.Path(rvpkg_path).parent
                print(f"- Directory contents of {rvpkg_parent}:")
                try:
                    files_in_dir = list(rvpkg_parent.iterdir())
                    if files_in_dir:
                        # Sort files by name for easier reading
                        files_in_dir.sort(key=lambda x: x.name.lower())
                        for file_path in files_in_dir:
                            if file_path.is_file():
                                size = file_path.stat().st_size
                                print(f"    {file_path.name} ({size:,} bytes)")
                            elif file_path.is_dir():
                                print(f"    {file_path.name}/ (directory)")
                    else:
                        print("    (directory is empty)")
                except Exception as e:
                    print(f"    ERROR: Could not list directory contents: {e}")

                # Check for common DLL dependencies specifically
                print("- Common DLL dependency check:")
                common_dlls = [
                    "Qt6Core.dll",
                    "msvcp140.dll",
                    "vcruntime140.dll",
                    "Qt6Gui.dll",
                    "Qt6Widgets.dll",
                ]
                for dll in common_dlls:
                    dll_path = rvpkg_parent / dll
                    if dll_path.exists():
                        size = dll_path.stat().st_size
                        print(f"    {dll}: EXISTS ({size:,} bytes)")
                    else:
                        print(f"    {dll}: MISSING")

            raise subprocess.CalledProcessError(
                result.returncode, command, result.stdout, result.stderr
            )
        else:
            print("RV packages installed successfully")
            if result.stdout:
                print(f"STDOUT: {result.stdout}")

    except FileNotFoundError as e:
        print(f"ERROR: Could not find executable: {command[0]}")
        print(f"Full command: {' '.join(command)}")
        print(f"Error: {e}")
        raise
    except Exception as e:
        print(f"ERROR: Unexpected error during package installation: {e}")
        print(f"Command: {' '.join(command)}")
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--rvpkg", dest="rvpkg_path", type=pathlib.Path, required=True)
    parser.add_argument(
        "--source", dest="packages_source_folder", type=pathlib.Path, required=True
    )
    parser.add_argument(
        "--destination",
        dest="packages_destination_folder",
        type=pathlib.Path,
        required=True,
    )

    install_rvpkg_packages(**vars(parser.parse_args()))
