#!/usr/bin/env python3

import os
import sys
import subprocess
from pathlib import Path


def find_python_packages():
    """Find all Python packages in Conan cache"""
    try:
        result = subprocess.run(
            ["conan", "list", "python:*", "--format=text"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode != 0:
            return []

        packages = []
        lines = result.stdout.split("\n")
        current_version = None
        current_package_id = None
        current_vfx_platform = None

        for line in lines:
            line_stripped = line.strip()

            # Look for version (e.g., "python/3.10.13")
            if line_stripped.startswith("python/"):
                current_version = line_stripped.split("/")[1]
                current_package_id = None
                current_vfx_platform = None

            # Look for package IDs (40-character alphanumeric strings)
            elif (
                len(line_stripped) == 40 and line_stripped.isalnum() and current_version
            ):
                current_package_id = line_stripped

            # Look for VFX platform in options
            elif current_package_id and "vfx_platform:" in line:
                vfx_platform = line.split(":")[1].strip()
                packages.append(
                    {
                        "version": current_version,
                        "package_id": current_package_id,
                        "vfx_platform": vfx_platform,
                    }
                )

        return packages

    except Exception as e:
        print(f"Error finding packages: {e}")
        return []


def test_package_ssl_and_otio(package_info):
    """Test SSL and OpenTimelineIO functionality for a specific package"""
    version = package_info["version"]
    package_id = package_info["package_id"]
    vfx_platform = package_info["vfx_platform"]

    print(f"\nTesting Python {version} (VFX {vfx_platform})...")

    try:
        # Get package path
        package_ref = f"python/{version}:{package_id}"
        result = subprocess.run(
            ["conan", "cache", "path", package_ref],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode != 0:
            print(f"  ERROR: Could not get package path")
            return False

        package_path = result.stdout.strip()
        python_exe = os.path.join(package_path, "bin", "python3")

        if not os.path.exists(python_exe):
            print(f"  ERROR: Python executable not found at {python_exe}")
            return False

        # Test script for SSL and OTIO
        test_script = """
import sys

# Test SSL
try:
    import ssl
    import _ssl
    import _hashlib
    import certifi
    
    ssl_version = ssl.OPENSSL_VERSION
    context = ssl.create_default_context()
    cert_path = certifi.where()
    
    print("SSL:OK")
    print(f"SSL_VERSION:{ssl_version}")
    
except Exception as e:
    print(f"SSL:ERROR:{e}")

# Test OpenTimelineIO
try:
    import opentimelineio as otio
    
    # Test basic OTIO functionality
    timeline = otio.schema.Timeline(name="test_timeline")
    track = otio.schema.Track(name="test_track")
    timeline.tracks.append(track)
    
    print("OTIO:OK")
    print(f"OTIO_VERSION:{otio.__version__}")
    
except Exception as e:
    print(f"OTIO:ERROR:{e}")
"""

        result = subprocess.run(
            [python_exe, "-c", test_script], capture_output=True, text=True, timeout=30
        )

        if result.returncode != 0:
            print(f"  ERROR: Test script failed: {result.stderr}")
            return False

        # Parse results
        ssl_ok = False
        otio_ok = False
        ssl_version = None
        otio_version = None

        for line in result.stdout.strip().split("\n"):
            if line == "SSL:OK":
                ssl_ok = True
            elif line.startswith("SSL_VERSION:"):
                ssl_version = line.split(":", 1)[1]
            elif line.startswith("SSL:ERROR:"):
                print(f"  ERROR: SSL Error: {line.split(':', 2)[2]}")
            elif line == "OTIO:OK":
                otio_ok = True
            elif line.startswith("OTIO_VERSION:"):
                otio_version = line.split(":", 1)[1]
            elif line.startswith("OTIO:ERROR:"):
                print(f"  ERROR: OTIO Error: {line.split(':', 2)[2]}")

        # Report results
        if ssl_ok:
            print(f"  PASS: SSL: {ssl_version}")
        else:
            print(f"  FAIL: SSL: Failed")

        if otio_ok:
            print(f"  PASS: OpenTimelineIO: {otio_version}")
        else:
            print(f"  FAIL: OpenTimelineIO: Failed")

        success = ssl_ok and otio_ok
        if success:
            print(f"  All tests passed!")

        return success

    except subprocess.TimeoutExpired:
        print(f"  ERROR: Test timed out")
        return False
    except Exception as e:
        print(f"  ERROR: Test error: {e}")
        return False


def test_built_packages():
    """Test SSL and OTIO integration in all built Python packages"""
    print("=" * 60)
    print("PYTHON PACKAGE VALIDATION")
    print("Testing SSL and OpenTimelineIO Integration")
    print("=" * 60)

    packages = find_python_packages()

    if not packages:
        print("ERROR: No Python packages found in Conan cache")
        return False

    print(f"Found {len(packages)} Python package(s):")
    for pkg in packages:
        print(
            f"  • Python {pkg['version']} (VFX {pkg['vfx_platform']}) - {pkg['package_id'][:8]}..."
        )

    all_passed = True

    for package_info in packages:
        success = test_package_ssl_and_otio(package_info)
        if not success:
            all_passed = False

    return all_passed


if __name__ == "__main__":
    try:
        success = test_built_packages()

        print("\n" + "=" * 60)
        if success:
            print("ALL TESTS PASSED!")
        else:
            print("SOME TESTS FAILED!")
        print("=" * 60)

        sys.exit(0 if success else 1)

    except Exception as e:
        print(f"\nERROR: Test failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
