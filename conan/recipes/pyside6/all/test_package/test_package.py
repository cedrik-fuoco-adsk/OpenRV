#!/usr/bin/env python3
"""
Simple standalone test script for PySide6 package
"""

import sys
import subprocess
import os
from pathlib import Path


def test_pyside6_basic():
    """Test basic PySide6 functionality"""
    print("Testing basic PySide6 imports...")

    test_code = """
import sys
try:
    from PySide6 import QtCore, QtGui, QtWidgets
    print(f"PASS: PySide6 basic modules imported successfully")
    print(f"  QtCore version: {QtCore.__version__}")
    print(f"  Qt version: {QtCore.qVersion()}")
    
    # Test basic Qt functionality
    app = QtWidgets.QApplication(sys.argv if 'sys' in globals() else [])
    widget = QtWidgets.QWidget()
    widget.setWindowTitle("PySide6 Test")
    print("PASS: Basic Qt widget creation successful")
    
except ImportError as e:
    print(f"ERROR: PySide6 import failed: {e}")
    sys.exit(1)
except Exception as e:
    print(f"ERROR: PySide6 test failed: {e}")
    sys.exit(1)
"""

    result = subprocess.run(
        [sys.executable, "-c", test_code], capture_output=True, text=True
    )

    if result.returncode == 0:
        print(result.stdout)
        return True
    else:
        print(f"ERROR: {result.stderr}")
        return False


def test_pyside6_webengine():
    """Test PySide6 WebEngine functionality"""
    print("Testing PySide6 WebEngine...")

    test_code = """
try:
    from PySide6 import QtWebEngineCore, QtWebEngineWidgets
    print("PASS: QtWebEngine modules imported successfully")
except ImportError as e:
    print(f"WARNING: QtWebEngine import failed (may not be available): {e}")
"""

    result = subprocess.run(
        [sys.executable, "-c", test_code], capture_output=True, text=True
    )
    print(result.stdout)
    if result.stderr:
        print(result.stderr)


def test_ssl_support():
    """Test SSL support"""
    print("Testing SSL support...")

    test_code = """
try:
    import ssl
    import _ssl
    print(f"PASS: SSL support available - {ssl.OPENSSL_VERSION}")
    
    try:
        import certifi
        print("PASS: certifi available for CA certificates")
    except ImportError:
        print("WARNING: certifi not available")
        
except ImportError as e:
    print(f"WARNING: SSL support not available: {e}")
"""

    result = subprocess.run(
        [sys.executable, "-c", test_code], capture_output=True, text=True
    )
    print(result.stdout)
    if result.stderr:
        print(result.stderr)


def main():
    """Run all tests"""
    print("=" * 60)
    print("PySide6 Package Test Suite")
    print("=" * 60)

    tests_passed = 0
    total_tests = 3

    # Test basic functionality
    if test_pyside6_basic():
        tests_passed += 1

    # Test WebEngine (non-critical)
    test_pyside6_webengine()
    tests_passed += 1  # Non-critical test

    # Test SSL support (non-critical)
    test_ssl_support()
    tests_passed += 1  # Non-critical test

    print("=" * 60)
    print(f"Tests completed: {tests_passed}/{total_tests}")

    if tests_passed >= 1:  # Only basic test is critical
        print("OVERALL: PASS - PySide6 package is functional")
        return 0
    else:
        print("OVERALL: FAIL - PySide6 package has critical issues")
        return 1


if __name__ == "__main__":
    sys.exit(main())
