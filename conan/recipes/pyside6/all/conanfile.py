from conan import ConanFile
from conan.tools.cmake import CMakeToolchain, cmake_layout
from conan.tools.env import VirtualBuildEnv
from conan.tools.files import get, replace_in_file, copy, rmdir, download
from conan.errors import ConanException
import os
import platform
import shutil
import subprocess
import re
import glob
import tempfile
import uuid
from pathlib import Path


class PySide6Conan(ConanFile):
    name = "pyside6"
    version = "6.5.3"
    license = "LGPL-3.0"
    url = "https://wiki.qt.io/Qt_for_Python"
    description = "Qt for Python (PySide6) - Complete build from source with libclang"
    settings = "os", "arch", "build_type"
    options = {
        "shared": [True, False],
        "with_ssl": [True, False],
        "python_version": ["3.11", "3.10"],
        "vfx_platform": ["2024", "2023"],
    }
    default_options = {
        "shared": True,
        "with_ssl": True,
        "python_version": "3.11",
        "vfx_platform": "2024",
    }
    exports_sources = "patches/*"
    generators = "CMakeDeps"

    def layout(self):
        cmake_layout(self)

    def requirements(self):
        self.requires("zlib/1.3.1", options={"shared": True})

        # Python dependency - use custom OpenRV Python build
        python_version = (
            "3.10.13" if str(self.options.vfx_platform) == "2023" else "3.11.9"
        )
        self.requires(
            f"python/{python_version}@openrv",
            options={
                "vfx_platform": str(self.options.vfx_platform),
                "shared": True,
                "optimizations": True,
                "with_tkinter": True,
                "with_ssl": self.options.with_ssl,
            },
        )

        if self.options.with_ssl:
            if (
                str(self.options.python_version) == "3.10"
                and str(self.options.vfx_platform) == "2023"
            ):
                self.requires("openssl/1.1.1u", options={"shared": True})
            else:
                self.requires("openssl/3.5.0", options={"shared": True})

    def build_requirements(self):
        if not self.settings.os == "Windows":
            self.tool_requires("ninja/1.11.1")

    def source(self):
        # Download PySide6 source from conandata
        sources = self.conan_data.get("sources", {}).get(self.version)
        if not sources:
            raise ConanException(f"No source available for version {self.version}")
        get(self, sources["url"], destination=self.source_folder, strip_root=True)

    def generate(self):
        env = VirtualBuildEnv(self)
        env.generate()

        tc = CMakeToolchain(self)
        tc.cache_variables["CMAKE_BUILD_TYPE"] = str(self.settings.build_type)
        tc.cache_variables["RV_DEPS_QT6_LOCATION"] = self._get_qt_location()
        tc.cache_variables["RV_VFX_PLATFORM"] = f"CY{self.options.vfx_platform}"
        tc.generate()

    def _get_qt_location(self):
        """Get Qt6 location from environment or default paths"""
        qt_location = os.getenv("RV_DEPS_QT6_LOCATION") or os.getenv("QT_HOME")
        if qt_location:
            return qt_location

        # Default Qt paths based on platform
        qt_version = "6.5.3"
        if self.settings.os == "Linux":
            home = os.getenv("HOME")
            return os.path.join(home, f"Qt{qt_version}", qt_version, "gcc_64")
        elif self.settings.os == "Macos":
            home = os.getenv("HOME")
            return os.path.join(home, f"Qt{qt_version}", qt_version, "clang_64")
        elif self.settings.os == "Windows":
            return f"c:/Qt/{qt_version}/msvc2019_64"
        return ""

    def _get_python_interpreter_args(self, python_home):
        """Get python interpreter arguments similar to make_python.py"""
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
                if not os.path.islink(p) and os.access(p, os.X_OK)
            ]
        )

        if not python_interpreters or not os.path.exists(python_interpreters[0]):
            raise FileNotFoundError(f"Python interpreter not found in {python_home}")

        python_interpreter = sorted(python_interpreters)[0]
        return [python_interpreter, "-s", "-E"]

    def _setup_clang(self):
        """Setup libclang for PySide6 build"""
        self.output.info("Setting up Clang...")

        libclang_url_base = "https://mirrors.ocf.berkeley.edu/qt/development_releases/prebuilt/libclang/libclang-release_"
        clang_filename_suffix = ""
        fallback_clang_filename_suffix = None

        if self.settings.os == "Macos":

            def get_clang_version():
                try:
                    version_output = subprocess.getoutput("clang --version")
                    version_search = re.search(
                        r"version (\d+)\.(\d+)\.(\d+)", version_output
                    )
                    if version_search:
                        return version_search.groups()
                except:
                    pass
                return None

            def get_clang_filename_suffix(version):
                version_str = ".".join(version)
                return f"{version_str}-based-macos-universal.7z"

            def get_fallback_clang_filename_suffix(version):
                major_minor = ".".join(version[:2])
                fallbacks = {
                    "14.0": "14.0.3-based-macos-universal.7z",
                    "15.0": "15.0.0-based-macos-universal.7z",
                    "17.0": "17.0.1-based-macos-universal.7z",
                }
                return fallbacks.get(major_minor)

            clang_version = get_clang_version()
            if clang_version:
                clang_filename_suffix = get_clang_filename_suffix(clang_version)
                fallback_clang_filename_suffix = get_fallback_clang_filename_suffix(
                    clang_version
                )
        elif self.settings.os == "Linux":
            clang_filename_suffix = "19.1.0-based-linux-Rhel8.8-gcc10.3-x86_64.7z"
        elif self.settings.os == "Windows":
            clang_filename_suffix = "19.1.0-based-windows-vs2019_64.7z"

        download_url = libclang_url_base + clang_filename_suffix
        libclang_zip = os.path.join(self.build_folder, "temp", "libclang.7z")

        # Create temp directory
        temp_dir = os.path.join(self.build_folder, "temp")
        os.makedirs(temp_dir, exist_ok=True)

        # Download libclang if not exists or corrupted
        if not os.path.exists(libclang_zip) or not self._verify_7z_archive(
            libclang_zip
        ):
            if os.path.exists(libclang_zip):
                os.remove(libclang_zip)

            self.output.info(f"Downloading libclang from {download_url}")
            try:
                download(self, download_url, libclang_zip)
            except Exception as e:
                if fallback_clang_filename_suffix:
                    fallback_url = libclang_url_base + fallback_clang_filename_suffix
                    self.output.warning(
                        f"Failed to download {download_url}, trying fallback {fallback_url}"
                    )
                    download(self, fallback_url, libclang_zip)
                else:
                    raise e

        # Extract libclang
        libclang_extracted = os.path.join(temp_dir, "libclang")
        if not os.path.exists(libclang_extracted):
            libclang_tmp = os.path.join(temp_dir, "libclang-tmp")
            if os.path.exists(libclang_tmp):
                shutil.rmtree(libclang_tmp)

            self._extract_7z_archive(libclang_zip, libclang_tmp)
            shutil.move(libclang_tmp, libclang_extracted)

        # Set environment variables
        libclang_install_dir = os.path.join(libclang_extracted, "libclang")
        os.environ["LLVM_INSTALL_DIR"] = libclang_install_dir
        os.environ["CLANG_INSTALL_DIR"] = libclang_install_dir

        self.output.info(f"Set LLVM_INSTALL_DIR={libclang_install_dir}")

    def _verify_7z_archive(self, archive_path):
        """Verify 7z archive integrity"""
        try:
            # Simple check - if file exists and has reasonable size
            return os.path.exists(archive_path) and os.path.getsize(archive_path) > 1000
        except:
            return False

    def _extract_7z_archive(self, archive_path, extract_path):
        """Extract 7z archive"""
        try:
            # Try using py7zr if available
            import py7zr

            with py7zr.SevenZipFile(archive_path, "r") as z:
                z.extractall(extract_path)
        except ImportError:
            # Fallback to system 7z command
            if shutil.which("7z"):
                subprocess.run(
                    ["7z", "x", archive_path, f"-o{extract_path}"], check=True
                )
            else:
                raise RuntimeError(
                    "Cannot extract 7z archive: py7zr not available and 7z command not found"
                )

    def _patch_shiboken6(self):
        """Patch CMakeLists.txt for shiboken6 to disable LIBXSLT"""
        cmakelist_path = os.path.join(
            self.source_folder, "sources", "shiboken6", "ApiExtractor", "CMakeLists.txt"
        )
        old_cmakelist_path = cmakelist_path + ".old"

        if os.path.exists(cmakelist_path) and not os.path.exists(old_cmakelist_path):
            # Backup original
            shutil.copy2(cmakelist_path, old_cmakelist_path)

            # Apply patch
            replace_in_file(
                self, cmakelist_path, " set(HAS_LIBXSLT 1)", " #set(HAS_LIBXSLT 1)"
            )
            self.output.info("Patched shiboken6 CMakeLists.txt to disable LIBXSLT")

    def _install_numpy(self):
        """Install numpy==1.26.3 required for PySide6 build"""
        python_deps_info = self.dependencies["python"].cpp_info
        python_home = self.dependencies["python"].package_folder
        python_interpreter_args = self._get_python_interpreter_args(python_home)

        install_args = python_interpreter_args + [
            "-m",
            "pip",
            "install",
            "numpy==1.26.3",
        ]
        self.output.info(f"Installing numpy with {install_args}")
        self.run(" ".join(install_args))

    def _setup_openssl_path(self):
        """Setup OpenSSL in PATH if available"""
        if self.options.with_ssl:
            try:
                openssl_deps_info = self.dependencies["openssl"].cpp_info
                openssl_bin_path = os.path.join(
                    self.dependencies["openssl"].package_folder, "bin"
                )
                if os.path.exists(openssl_bin_path):
                    current_path = os.environ.get("PATH", "")
                    os.environ["PATH"] = openssl_bin_path + os.pathsep + current_path
                    self.output.info(f"Added OpenSSL to PATH: {openssl_bin_path}")
            except:
                pass

    def build(self):
        # Setup environment
        self._setup_clang()
        self._setup_openssl_path()
        self._patch_shiboken6()
        self._install_numpy()

        # Get Python info from dependency
        python_deps_info = self.dependencies["python"].cpp_info
        python_home = self.dependencies["python"].package_folder
        python_interpreter_args = self._get_python_interpreter_args(python_home)

        # Get Qt location
        qt_location = self._get_qt_location()
        qtpaths_exe = os.path.join(qt_location, "bin", "qtpaths")
        if self.settings.os == "Windows":
            qtpaths_exe += ".exe"

        if not os.path.exists(qtpaths_exe):
            raise ConanException(f"Qt qtpaths executable not found: {qtpaths_exe}")

        # Build PySide6
        build_args = python_interpreter_args + [
            os.path.join(self.source_folder, "setup.py"),
            "install",
            f"--qtpaths={qtpaths_exe}",
            "--ignore-git",
            "--standalone",
            "--verbose",
            "--verbose-build",
            "--log-level=verbose",
            f"--parallel={os.cpu_count() or 1}",
        ]

        # Add OpenSSL if available
        if self.options.with_ssl:
            try:
                openssl_deps_info = self.dependencies["openssl"].cpp_info
                openssl_bin_path = os.path.join(
                    self.dependencies["openssl"].package_folder, "bin"
                )
                if os.path.exists(openssl_bin_path):
                    build_args.append(f"--openssl={openssl_bin_path}")
            except:
                pass

        # Add debug flag for Windows
        if self.settings.os == "Windows" and self.settings.build_type == "Debug":
            build_args.append("--debug")

        self.output.info(f"Building PySide6 with: {' '.join(build_args)}")
        self.run(" ".join(build_args))

        # Post-build cleanup
        self._post_build_cleanup(python_interpreter_args, python_home)

    def _post_build_cleanup(self, python_interpreter_args, python_home):
        """Cleanup after PySide6 build"""
        # Remove shiboken6_generator
        cleanup_args = python_interpreter_args + [
            "-m",
            "pip",
            "uninstall",
            "-y",
            "shiboken6_generator",
        ]
        self.output.info("Removing shiboken6_generator")
        self.run(" ".join(cleanup_args))

        # Force remove shiboken6_generator files if still present
        python_code = (
            "import os, shutil\n"
            "try:\n"
            "    import shiboken6_generator\n"
            "except Exception:\n"
            "    exit(0)\n"
            "shutil.rmtree(os.path.dirname(shiboken6_generator.__file__))\n"
        )
        cleanup_python_args = python_interpreter_args + ["-c", f'"{python_code}"']
        self.run(" ".join(cleanup_python_args))

        # Copy OpenSSL libraries to PySide6 on Windows
        if self.options.with_ssl and self.settings.os == "Windows":
            self._copy_openssl_libs_windows(python_home)

        # Remove broken shortcuts
        self._remove_broken_shortcuts(python_home)

    def _copy_openssl_libs_windows(self, python_home):
        """Copy OpenSSL libraries to PySide6 folder on Windows"""
        try:
            openssl_deps_info = self.dependencies["openssl"].cpp_info
            openssl_bin_path = os.path.join(
                self.dependencies["openssl"].package_folder, "bin"
            )

            # Find PySide6 folder
            pyside_folders = glob.glob(
                os.path.join(python_home, "**", "site-packages", "PySide6"),
                recursive=True,
            )

            if pyside_folders:
                pyside_folder = pyside_folders[0]
                openssl_libs = glob.glob(os.path.join(openssl_bin_path, "lib*"))

                for lib in openssl_libs:
                    self.output.info(f"Copying {lib} to {pyside_folder}")
                    shutil.copy(lib, pyside_folder)
        except Exception as e:
            self.output.warn(f"Failed to copy OpenSSL libraries: {e}")

    def _remove_broken_shortcuts(self, python_home):
        """Remove broken Python shortcuts that depend on absolute paths"""
        python_version = str(self.options.python_version)

        if self.settings.os == "Windows":
            # Remove all scripts on Windows
            scripts_dir = os.path.join(python_home, "Scripts")
            if os.path.exists(scripts_dir):
                shutil.rmtree(scripts_dir)
                self.output.info("Removed Windows Scripts directory")
        else:
            # Remove scripts except python executables on Unix-like systems
            bin_dir = os.path.join(python_home, "bin")
            if os.path.exists(bin_dir):
                keep_files = ["python", "python3", f"python{python_version}"]
                for filename in os.listdir(bin_dir):
                    filepath = os.path.join(bin_dir, filename)
                    if filename not in keep_files:
                        self.output.info(f"Removing {filepath}")
                        os.remove(filepath)
                    else:
                        self.output.info(f"Keeping {filepath}")

    def package(self):
        # Get Python dependency info to find installation location
        python_deps_info = self.dependencies["python"].cpp_info
        python_home = self.dependencies["python"].package_folder

        # Copy Python installation with PySide6 to package
        copy(
            self,
            pattern="*",
            src=python_home,
            dst=os.path.join(self.package_folder, "python"),
        )

        # Copy any additional files from build
        if os.path.exists(os.path.join(self.source_folder, "dist")):
            copy(
                self,
                pattern="*",
                src=os.path.join(self.source_folder, "dist"),
                dst=os.path.join(self.package_folder, "dist"),
            )

    def package_info(self):
        # Set up package info for consumers
        self.cpp_info.libs = ["PySide6"]

        # Add Python path to environment
        python_path = os.path.join(self.package_folder, "python")
        self.cpp_info.bindirs.append(os.path.join(python_path, "bin"))
        self.cpp_info.libdirs.append(os.path.join(python_path, "lib"))

        # Set runtime environment variables for Python and PySide6
        self.runenv_info.define_path("PYTHONHOME", python_path)
        self.runenv_info.define_path("PYSIDE6_ROOT", python_path)

        # Add Python executable to PATH
        python_bin = os.path.join(python_path, "bin")
        self.runenv_info.prepend_path("PATH", python_bin)

        # Add to Python path
        if self.settings.os == "Windows":
            site_packages = os.path.join(python_path, "Lib", "site-packages")
        else:
            site_packages = os.path.join(
                python_path,
                "lib",
                f"python{self.options.python_version}",
                "site-packages",
            )
        self.runenv_info.prepend_path("PYTHONPATH", site_packages)

        # Also set for build environment (legacy compatibility)
        self.buildenv_info.define_path("PYTHONHOME", python_path)
        self.buildenv_info.define_path("PYSIDE6_ROOT", python_path)
        self.buildenv_info.prepend_path("PATH", python_bin)
        self.buildenv_info.prepend_path("PYTHONPATH", site_packages)

    def test_python_distribution(self, python_home):
        """Test the Python distribution with PySide6"""
        tmp_dir = os.path.join(tempfile.gettempdir(), str(uuid.uuid4()))
        os.makedirs(tmp_dir)

        tmp_python_home = os.path.join(tmp_dir, os.path.basename(python_home))
        try:
            self.output.info(f"Moving {python_home} to {tmp_python_home}")
            shutil.move(python_home, tmp_python_home)

            python_validation_args = self._get_python_interpreter_args(
                tmp_python_home
            ) + ["-c", "from PySide6 import *; from PySide6 import QtWebEngineCore"]
            self.output.info(
                f"Validating PySide6 with: {' '.join(python_validation_args)}"
            )
            self.run(" ".join(python_validation_args))
        finally:
            self.output.info(f"Moving {tmp_python_home} back to {python_home}")
            shutil.move(tmp_python_home, python_home)
