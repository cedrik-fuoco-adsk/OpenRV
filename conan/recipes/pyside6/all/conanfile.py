from conan import ConanFile
from conan.tools.cmake import CMakeToolchain, cmake_layout
from conan.tools.env import VirtualBuildEnv
from conan.tools.files import get, replace_in_file, copy, rmdir, download
from conan.errors import ConanException
import os
import platform
import shlex
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
        """Get python interpreter arguments exactly matching make_python.py get_python_interpreter_args()"""
        # Following make_python.py logic exactly - check for Windows Debug pattern
        build_opentimelineio = (
            self.settings.os == "Windows" and self.settings.build_type == "Debug"
        )
        python_name_pattern = "python*" if not build_opentimelineio else "python_d*"

        python_interpreters = glob.glob(
            os.path.join(python_home, python_name_pattern), recursive=True
        )
        python_interpreters += glob.glob(
            os.path.join(python_home, "bin", python_name_pattern)
        )

        # Sort and filter executable files - exactly matching make_python.py logic
        python_interpreters = sorted(
            [
                p
                for p in python_interpreters
                if not os.path.islink(p) and os.access(p, os.X_OK)
            ]
        )

        if not python_interpreters or not os.path.exists(python_interpreters[0]):
            raise FileNotFoundError(f"Python interpreter not found in {python_home}")

        self.output.info(f"Found python interpreters {python_interpreters}")

        python_interpreter = sorted(python_interpreters)[0]

        # Return exactly the same flags as make_python.py: [python_interpreter, "-s", "-E"]
        return [python_interpreter, "-s", "-E"]

    def _get_python_interpreter_args_with_isolation(self, python_home):
        """Get python interpreter args with -I flag for pip operations (following make_pyside6.py line 227)"""
        base_args = self._get_python_interpreter_args(python_home)
        # Add -I flag for isolation during pip operations (following make_python.py patch_python_distribution)
        return base_args + ["-I"]

    def _setup_msvc_environment(self):
        """Setup MSVC environment on Windows"""
        if self.settings.os != "Windows":
            return

        # Try to find and setup Visual Studio environment
        vs_paths = [
            r"C:\Program Files\Microsoft Visual Studio\2022\Enterprise\VC\Auxiliary\Build\vcvars64.bat",
            r"C:\Program Files\Microsoft Visual Studio\2022\Professional\VC\Auxiliary\Build\vcvars64.bat",
            r"C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat",
            r"C:\Program Files (x86)\Microsoft Visual Studio\2019\Enterprise\VC\Auxiliary\Build\vcvars64.bat",
            r"C:\Program Files (x86)\Microsoft Visual Studio\2019\Professional\VC\Auxiliary\Build\vcvars64.bat",
            r"C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\VC\Auxiliary\Build\vcvars64.bat",
        ]

        vcvars_bat = None
        for path in vs_paths:
            if os.path.exists(path):
                vcvars_bat = path
                break

        if not vcvars_bat:
            # Try to find vcvars64.bat using vswhere
            try:
                vswhere_output = subprocess.check_output(
                    [
                        r"C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe",
                        "-latest",
                        "-property",
                        "installationPath",
                    ],
                    text=True,
                ).strip()

                if vswhere_output:
                    potential_vcvars = os.path.join(
                        vswhere_output, "VC", "Auxiliary", "Build", "vcvars64.bat"
                    )
                    if os.path.exists(potential_vcvars):
                        vcvars_bat = potential_vcvars
            except (subprocess.CalledProcessError, FileNotFoundError):
                pass

        if vcvars_bat:
            self.output.info(f"Found Visual Studio environment setup: {vcvars_bat}")
            # Get environment variables after running vcvars64.bat
            try:
                # Use proper command formatting for Windows batch file execution
                cmd = f'call "{vcvars_bat}" && set'
                result = subprocess.run(cmd, capture_output=True, text=True, shell=True)

                if result.returncode == 0:
                    # Parse environment variables and set them
                    for line in result.stdout.splitlines():
                        if "=" in line:
                            key, value = line.split("=", 1)
                            # Only set important variables, avoid overriding system vars
                            if key.upper() in [
                                "PATH",
                                "INCLUDE",
                                "LIB",
                                "LIBPATH",
                                "VCINSTALLDIR",
                                "WINDOWSSDKDIR",
                                "WINDOWSSDKVERSION",
                                "CL",
                                "LINK",
                            ]:
                                if key.upper() == "PATH":
                                    # Prepend to existing PATH
                                    existing_path = os.environ.get("PATH", "")
                                    os.environ["PATH"] = (
                                        value + os.pathsep + existing_path
                                    )
                                else:
                                    os.environ[key] = value

                    self.output.info("MSVC environment variables set successfully")
                    # Verify cl.exe is now available
                    try:
                        subprocess.run(["cl.exe"], capture_output=True, check=False)
                        self.output.info("cl.exe is now available in PATH")
                    except FileNotFoundError:
                        self.output.warning(
                            "cl.exe still not found after setting MSVC environment"
                        )
                else:
                    self.output.warning(
                        f"Failed to setup MSVC environment: {result.stderr}"
                    )
            except Exception as e:
                self.output.warning(f"Error setting up MSVC environment: {e}")
        else:
            self.output.warning("Could not find Visual Studio vcvars64.bat")
            # Alternative: try to set basic compiler paths
            self._try_alternative_msvc_setup()

    def _try_alternative_msvc_setup(self):
        """Alternative method to setup MSVC when vcvars64.bat is not found"""
        # Try to find cl.exe in common locations
        cl_paths = [
            r"C:\Program Files\Microsoft Visual Studio\2022\Enterprise\VC\Tools\MSVC\*\bin\Hostx64\x64\cl.exe",
            r"C:\Program Files\Microsoft Visual Studio\2022\Professional\VC\Tools\MSVC\*\bin\Hostx64\x64\cl.exe",
            r"C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Tools\MSVC\*\bin\Hostx64\x64\cl.exe",
            r"C:\Program Files (x86)\Microsoft Visual Studio\2019\Enterprise\VC\Tools\MSVC\*\bin\Hostx64\x64\cl.exe",
            r"C:\Program Files (x86)\Microsoft Visual Studio\2019\Professional\VC\Tools\MSVC\*\bin\Hostx64\x64\cl.exe",
            r"C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\VC\Tools\MSVC\*\bin\Hostx64\x64\cl.exe",
        ]

        cl_exe = None
        for pattern in cl_paths:
            matches = glob.glob(pattern)
            if matches:
                cl_exe = matches[0]  # Take the first (usually latest version)
                break

        if cl_exe:
            cl_dir = os.path.dirname(cl_exe)
            current_path = os.environ.get("PATH", "")
            os.environ["PATH"] = cl_dir + os.pathsep + current_path

            # Set CMAKE compilers explicitly
            os.environ["CMAKE_C_COMPILER"] = cl_exe
            os.environ["CMAKE_CXX_COMPILER"] = cl_exe

            self.output.info(f"Added cl.exe to PATH: {cl_dir}")
            self.output.info(f"Set CMAKE_CXX_COMPILER to: {cl_exe}")
        else:
            self.output.warning(
                "Could not find cl.exe in standard Visual Studio locations"
            )

    def _setup_clang(self):
        """Setup libclang for PySide6 build"""
        # IMPORTANT: Setup OpenSSL PATH first (following make_pyside6.py order)
        self._setup_openssl_path_for_clang()

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

        # Download libclang if not exists or corrupted (following make_pyside6.py logic)
        # Check for failed download and clean up first
        if (
            os.path.exists(libclang_zip)
            and self._verify_7z_archive(libclang_zip) is False
        ):
            self.output.warning("Removing corrupted libclang archive")
            os.remove(libclang_zip)

        # Download if necessary
        if not os.path.exists(libclang_zip):
            self.output.info(f"Downloading libclang from {download_url}")
            download_ok = False

            try:
                download(self, download_url, libclang_zip)
                download_ok = True
            except Exception as e:
                self.output.warning(f"Failed to download {download_url}: {e}")
                download_ok = False

            # Try fallback if primary download failed
            if not download_ok and fallback_clang_filename_suffix:
                fallback_url = libclang_url_base + fallback_clang_filename_suffix
                self.output.warning(
                    f"Could not download or version does not exist: {download_url}"
                )
                self.output.warning(
                    f"Attempting to fallback on known version: {fallback_url}..."
                )

                try:
                    download(self, fallback_url, libclang_zip)
                    download_ok = True
                except Exception as e:
                    self.output.warning(f"Fallback download also failed: {e}")
                    download_ok = False

            if not download_ok:
                raise ConanException(
                    f"Could not download or version does not exist: {download_url}"
                )

            # Verify downloaded archive
            if not self._verify_7z_archive(libclang_zip):
                raise ConanException(
                    f"Downloaded libclang archive is corrupted: {libclang_zip}"
                )

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

    def _setup_openssl_path_for_clang(self):
        """Setup OpenSSL PATH before clang setup (following make_pyside6.py prepare() order)"""
        if self.options.with_ssl:
            try:
                openssl_deps_info = self.dependencies["openssl"].cpp_info
                openssl_bin_path = os.path.join(
                    self.dependencies["openssl"].package_folder, "bin"
                )
                if os.path.exists(openssl_bin_path):
                    # Following make_pyside6.py lines 159-167: set PATH before clang setup
                    current_path = os.environ.get("PATH", "")
                    os.environ["PATH"] = os.pathsep.join(
                        [openssl_bin_path, current_path]
                    )
                    self.output.info(
                        f"Set OpenSSL PATH before clang setup: {openssl_bin_path}"
                    )
                    self.output.info(f"PATH={os.environ['PATH']}")
            except Exception as e:
                self.output.warning(f"Could not setup OpenSSL PATH for clang: {e}")

    def _verify_7z_archive(self, archive_path):
        """Verify 7z archive integrity - following make_pyside6.py logic"""
        if not os.path.exists(archive_path):
            return False

        try:
            # First check file size
            if os.path.getsize(archive_path) < 1000:
                return False

            # Try to test archive integrity using py7zr if available
            try:
                import py7zr

                with py7zr.SevenZipFile(archive_path, "r") as z:
                    # Test archive by trying to list contents
                    z.list()
                return True
            except ImportError:
                # Fallback to 7z command if available
                if shutil.which("7z"):
                    try:
                        result = subprocess.run(
                            ["7z", "t", archive_path],
                            capture_output=True,
                            text=True,
                            check=False,
                        )
                        return result.returncode == 0
                    except:
                        pass

                # Final fallback - just check file size (like original simple check)
                return (
                    os.path.getsize(archive_path) > 10000
                )  # Larger threshold for safety

        except Exception as e:
            self.output.warning(f"Archive verification failed: {e}")
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
        """Install numpy==1.26.3 required for PySide6 build - following make_pyside6.py logic"""
        python_deps_info = self.dependencies["python"].cpp_info
        python_home = self.dependencies["python"].package_folder
        # Use isolation flags for pip operations (following make_pyside6.py)
        python_interpreter_args = self._get_python_interpreter_args_with_isolation(
            python_home
        )

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
        self._setup_msvc_environment()

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

        # Following make_pyside6.py line 265: print the exact command being executed
        self.output.info(f"Executing {build_args}")
        self.run(" ".join(build_args))

        # Post-build cleanup
        self._post_build_cleanup(python_interpreter_args, python_home)

    def _post_build_cleanup(self, python_interpreter_args, python_home):
        """Cleanup after PySide6 build - following make_pyside6.py cleanup logic exactly"""
        # Remove shiboken6_generator using same approach as make_pyside6.py lines 268-277
        cleanup_args = python_interpreter_args + [
            "-m",
            "pip",
            "uninstall",
            "-y",
            "shiboken6_generator",
        ]
        self.output.info(f"Executing {cleanup_args}")
        self.run(" ".join(cleanup_args))

        # Force remove shiboken6_generator files if still present - following make_pyside6.py lines 280-295
        # Use the same approach as the original make_pyside6.py without shell escaping the multiline script
        python_script = "\n".join(
            [
                "import os, shutil",
                "try:",
                "  import shiboken6_generator",
                "except:",
                "  exit(0)",
                "shutil.rmtree(os.path.dirname(shiboken6_generator.__file__))",
            ]
        )

        try:
            # Use subprocess directly like make_pyside6.py, avoiding shell interpretation issues
            import subprocess

            generator_cleanup_args = python_interpreter_args + ["-c", python_script]
            self.output.info(
                f"Executing shiboken6_generator cleanup with args: {generator_cleanup_args}"
            )
            result = subprocess.run(
                generator_cleanup_args, capture_output=True, text=True
            )
            if result.returncode != 0:
                self.output.warning(
                    f"shiboken6_generator cleanup failed with return code {result.returncode}"
                )
                self.output.warning(f"stdout: {result.stdout}")
                self.output.warning(f"stderr: {result.stderr}")
                # Try alternative approach with temporary file on Windows
                if self.settings.os == "Windows":
                    self.output.info(
                        "Attempting cleanup using temporary file approach..."
                    )
                    self._cleanup_shiboken6_generator_with_tempfile(
                        python_interpreter_args
                    )
                # Don't fail the build if cleanup fails - it's not critical
            else:
                self.output.info("shiboken6_generator cleanup completed successfully")
        except Exception as e:
            self.output.warning(f"Failed to cleanup shiboken6_generator: {e}")
            # Try alternative approach with temporary file on Windows
            if self.settings.os == "Windows":
                self.output.info("Attempting cleanup using temporary file approach...")
                self._cleanup_shiboken6_generator_with_tempfile(python_interpreter_args)
            # Continue with build - cleanup failure is not critical

        # Copy OpenSSL libraries to PySide6 on Windows
        if self.options.with_ssl and self.settings.os == "Windows":
            self._copy_openssl_libs_windows(python_home)

        # Remove broken shortcuts
        self._remove_broken_shortcuts(python_home)

    def _cleanup_shiboken6_generator_with_tempfile(self, python_interpreter_args):
        """Alternative cleanup approach using temporary file - more reliable on Windows"""
        try:
            import subprocess
            import tempfile

            # Create the cleanup script content
            cleanup_script = """import os, shutil
try:
    import shiboken6_generator
except:
    exit(0)
shutil.rmtree(os.path.dirname(shiboken6_generator.__file__))
"""

            # Write to temporary file
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".py", delete=False
            ) as temp_file:
                temp_file.write(cleanup_script)
                temp_file_path = temp_file.name

            try:
                # Execute the temporary file
                cleanup_args = python_interpreter_args + [temp_file_path]
                self.output.info(f"Executing cleanup script: {temp_file_path}")
                result = subprocess.run(cleanup_args, capture_output=True, text=True)

                if result.returncode == 0:
                    self.output.info(
                        "shiboken6_generator cleanup via temporary file completed successfully"
                    )
                else:
                    self.output.warning(
                        f"Temporary file cleanup failed with return code {result.returncode}"
                    )
                    self.output.warning(f"stdout: {result.stdout}")
                    self.output.warning(f"stderr: {result.stderr}")

            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_file_path)
                except Exception as cleanup_err:
                    self.output.warning(
                        f"Failed to remove temporary file {temp_file_path}: {cleanup_err}"
                    )

        except Exception as e:
            self.output.warning(
                f"Failed to cleanup shiboken6_generator using temporary file: {e}"
            )

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
        """Remove broken Python shortcuts - following make_pyside6.py remove_broken_shortcuts() exactly"""
        # Extract python version (major.minor) from dependency
        python_version = str(self.options.python_version)

        if self.settings.os == "Windows":
            # All executables inside Scripts have a hardcoded absolute path to python
            # which can't be relied upon, so remove all scripts. (following make_pyside6.py lines 215-219)
            scripts_dir = os.path.join(python_home, "Scripts")
            if os.path.exists(scripts_dir):
                shutil.rmtree(scripts_dir)
                self.output.info("Removed Windows Scripts directory")
        else:
            # Aside from the python executables, every other file in the build
            # is a script that does not support relocation (following make_pyside6.py lines 220-234)
            bin_dir = os.path.join(python_home, "bin")
            if os.path.exists(bin_dir):
                keep_files = [
                    "python",
                    "python3",
                    f"python{python_version}",
                ]
                for filename in os.listdir(bin_dir):
                    filepath = os.path.join(bin_dir, filename)
                    if filename not in keep_files:
                        self.output.info(f"Removing {filepath}...")
                        os.remove(filepath)
                    else:
                        self.output.info(f"Keeping {filepath}...")

    def package(self):
        # Get Python dependency info to find where PySide6 was installed
        python_home = self.dependencies["python"].package_folder

        # Determine site-packages location where PySide6 was installed
        if self.settings.os == "Windows":
            site_packages_dir = os.path.join(python_home, "Lib", "site-packages")
        else:
            site_packages_dir = os.path.join(
                python_home,
                "lib",
                f"python{self.options.python_version}",
                "site-packages",
            )

        # Package only PySide6 and shiboken6 modules (not the entire Python installation)
        pyside6_src = os.path.join(site_packages_dir, "PySide6")
        shiboken6_src = os.path.join(site_packages_dir, "shiboken6")

        package_site_packages = os.path.join(self.package_folder, "site-packages")

        if os.path.exists(pyside6_src):
            self.output.info(f"Packaging PySide6 from {pyside6_src}")
            copy(
                self,
                pattern="*",
                src=pyside6_src,
                dst=os.path.join(package_site_packages, "PySide6"),
            )
        else:
            self.output.warning(f"PySide6 not found at {pyside6_src}")

        if os.path.exists(shiboken6_src):
            self.output.info(f"Packaging shiboken6 from {shiboken6_src}")
            copy(
                self,
                pattern="*",
                src=shiboken6_src,
                dst=os.path.join(package_site_packages, "shiboken6"),
            )
        else:
            self.output.warning(f"shiboken6 not found at {shiboken6_src}")

        # Also look for .egg-info directories
        for egg_pattern in ["PySide6*.egg-info", "shiboken6*.egg-info"]:
            egg_dirs = glob.glob(os.path.join(site_packages_dir, egg_pattern))
            for egg_dir in egg_dirs:
                if os.path.exists(egg_dir):
                    egg_name = os.path.basename(egg_dir)
                    self.output.info(f"Packaging {egg_name}")
                    copy(
                        self,
                        pattern="*",
                        src=egg_dir,
                        dst=os.path.join(package_site_packages, egg_name),
                    )

    def package_info(self):
        # PySide6 is a Python package, not a linkable C++ library
        # Do not declare cpp_info.libs - this was causing the CMake error

        # Point to the packaged site-packages directory containing PySide6
        site_packages = os.path.join(self.package_folder, "site-packages")

        # Set include directories so CMake can find the package location
        # This allows python.cmake to use GET_TARGET_PROPERTY for INTERFACE_INCLUDE_DIRECTORIES
        self.cpp_info.includedirs = [site_packages]

        # Set PySide6 root for CMake integration
        self.runenv_info.define_path("PYSIDE6_ROOT", site_packages)
        self.runenv_info.prepend_path("PYTHONPATH", site_packages)

        # Also set for build environment (legacy compatibility)
        self.buildenv_info.define_path("PYSIDE6_ROOT", site_packages)
        self.buildenv_info.prepend_path("PYTHONPATH", site_packages)

        # Set package directories for CMake
        self.cpp_info.builddirs = ["site-packages"]

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
