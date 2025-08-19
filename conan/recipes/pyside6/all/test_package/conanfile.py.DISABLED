import os
import shlex
import shutil
import subprocess
import glob
from conan import ConanFile
from pathlib import Path


class TestPackageConan(ConanFile):
    settings = "os", "arch", "build_type"
    test_type = "explicit"
    generators = "VirtualBuildEnv", "VirtualRunEnv"

    def build_requirements(self):
        self.test_requires(self.tested_reference_str)

    def test(self):
        self.output.info("Testing PySide6 package...")

        # Find the PySide6 package info
        package_info = self._find_pyside6_package()
        if not package_info:
            self.output.error("ERROR: Could not find PySide6 package")
            return

        # Test PySide6 imports and functionality
        self.test_pyside6_imports(package_info)

        # Test SSL functionality if with_ssl is enabled
        if self._get_option_value("with_ssl", True):
            self.test_ssl_functionality(package_info)

        # Test Qt WebEngine if available
        self.test_qt_webengine(package_info)

        self.output.info("All PySide6 tests completed")

    def _find_pyside6_package(self):
        """Find PySide6 package installation details"""
        try:
            # Use Python dependency - PySide6 modules are available via PYTHONPATH
            python_dep = self.dependencies["python"]
            if python_dep:
                return {"path": python_dep.package_folder, "type": "package"}
        except Exception as e:
            self.output.info(f"Could not find Python dependency: {e}")

        # Fallback to system Python
        return {"path": "/usr", "type": "system"}

    def _get_python_interpreter_args(self, python_home):
        """Get python interpreter arguments"""
        python_name_pattern = "python*"

        python_interpreters = glob.glob(
            os.path.join(python_home, python_name_pattern), recursive=True
        )
        python_interpreters += glob.glob(
            os.path.join(python_home, "bin", python_name_pattern)
        )

        # Sort and filter executable files
        python_interpreters = sorted(
            [
                p
                for p in python_interpreters
                if not os.path.islink(p)
                and os.access(p, os.X_OK)
                and "python" in os.path.basename(p)
            ]
        )

        if python_interpreters:
            return [python_interpreters[0], "-s", "-E"]
        else:
            # Fallback to system python
            python_exe = shutil.which("python3") or shutil.which("python")
            return [python_exe] if python_exe else ["python3"]

    def _get_option_value(self, option_name, default_value):
        """Get option value safely"""
        try:
            return getattr(self.options, option_name, default_value)
        except:
            return default_value

    def test_pyside6_imports(self, package_info):
        """Test basic PySide6 imports"""
        self.output.info("Testing PySide6 imports...")

        # Get PySide6 package location from Conan package
        pyside6_dep = self.dependencies["pyside6"]
        pyside6_site_packages = os.path.join(
            pyside6_dep.package_folder, "site-packages"
        )

        python_args = self._get_python_interpreter_args(package_info["path"])
        test_command = python_args + [
            "-c",
            "from PySide6 import QtCore, QtGui, QtWidgets; print('PASS: Basic PySide6 modules import OK')",
        ]

        self.output.info(f"Using PySide6 from: {pyside6_site_packages}")

        try:
            # Source the Conan environment and run the test with proper shell escaping
            escaped_command = " ".join(shlex.quote(arg) for arg in test_command)
            shell_command = f"source conanrun.sh && {escaped_command}"
            result = subprocess.run(
                shell_command, shell=True, capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                self.output.info(result.stdout.strip())
            else:
                self.output.error(
                    f"ERROR: PySide6 basic test failed: {result.stderr.strip()}"
                )
                raise Exception("PySide6 basic import test failed")
        except subprocess.TimeoutExpired:
            self.output.error("ERROR: PySide6 import test timed out")
            raise Exception("PySide6 import test timed out")
        except Exception as e:
            self.output.error(f"ERROR: PySide6 import test exception: {e}")
            raise

    def test_qt_webengine(self, package_info):
        """Test Qt WebEngine functionality"""
        self.output.info("Testing Qt WebEngine...")

        # Get PySide6 package location from Conan package
        pyside6_dep = self.dependencies["pyside6"]
        pyside6_site_packages = os.path.join(
            pyside6_dep.package_folder, "site-packages"
        )

        python_args = self._get_python_interpreter_args(package_info["path"])
        test_command = python_args + [
            "-c",
            "try:\n  from PySide6 import QtWebEngineCore, QtWebEngineWidgets\n  print('PASS: Qt WebEngine modules import OK')\nexcept ImportError as e:\n  print(f'WARNING: Qt WebEngine import failed: {e}')",
        ]

        try:
            # Source the Conan environment and run the test with proper shell escaping
            escaped_command = " ".join(shlex.quote(arg) for arg in test_command)
            shell_command = f"source conanrun.sh && {escaped_command}"
            result = subprocess.run(
                shell_command, shell=True, capture_output=True, text=True, timeout=30
            )
            self.output.info(result.stdout.strip())
            if result.stderr.strip():
                self.output.warning(result.stderr.strip())
        except subprocess.TimeoutExpired:
            self.output.warning("WARNING: Qt WebEngine test timed out")
        except Exception as e:
            self.output.warning(f"WARNING: Qt WebEngine test exception: {e}")

    def test_ssl_functionality(self, package_info):
        """Test SSL functionality"""
        self.output.info("Testing SSL functionality...")

        python_args = self._get_python_interpreter_args(package_info["path"])
        test_command = python_args + [
            "-c",
            "try:\n  import ssl, _ssl\n  print(f'PASS: SSL modules OK - {ssl.OPENSSL_VERSION}')\nexcept ImportError as e:\n  print(f'ERROR: SSL import failed: {e}')\n  exit(1)\ntry:\n  import certifi\n  print('PASS: certifi module OK')\nexcept ImportError as e:\n  print(f'WARNING: certifi import failed: {e}')",
        ]

        try:
            # Source the Conan environment and run the test with proper shell escaping
            escaped_command = " ".join(shlex.quote(arg) for arg in test_command)
            shell_command = f"source conanrun.sh && {escaped_command}"
            result = subprocess.run(
                shell_command, shell=True, capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                self.output.info(result.stdout.strip())
            else:
                self.output.error(f"ERROR: SSL test failed: {result.stderr.strip()}")
                raise Exception("SSL test failed")
        except subprocess.TimeoutExpired:
            self.output.error("ERROR: SSL test timed out")
            raise Exception("SSL test timed out")
        except Exception as e:
            self.output.error(f"ERROR: SSL test exception: {e}")
            raise
