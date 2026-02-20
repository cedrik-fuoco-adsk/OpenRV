#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# *****************************************************************************
# Copyright 2025 Autodesk, Inc. All rights reserved.
#
# SPDX-License-Identifier: Apache-2.0
#
# *****************************************************************************

import os
import shutil
import glob
import subprocess

from conan import ConanFile
from conan.tools.cmake import cmake_layout
from conan.tools.files import get, save
from conan.tools.system import package_manager
from conan.errors import ConanException


class PythonConan(ConanFile):
    name = "python"
    license = "Python-2.0"
    author = "Autodesk RV Team"
    url = "https://github.com/python/cpython"
    description = "OpenRV's custom Python build with SSL certificate handling and relocatable binaries"
    topics = ("python", "interpreter", "vfx", "openrv")

    settings = "os", "compiler", "build_type", "arch"
    exports = "sitecustomize.py"
    exports_sources = "patches/*"

    options = {
        "vfx_platform": ["CY2023", "CY2024"],
        "shared": [True, False],
        "optimizations": [True, False],
        "with_tkinter": [True, False],
        "with_ssl": [True, False],
    }

    default_options = {
        "vfx_platform": "CY2024",
        "shared": True,
        "optimizations": True,
        "with_tkinter": True,
        "with_ssl": True,
    }

    def configure(self):
        """Configure version and dependencies based on VFX platform"""
        # Only auto-configure version if it matches the expected pattern
        if self.options.vfx_platform == "CY2023" and (not hasattr(self, "version") or self.version == "3.11.9"):
            self.version = "3.10.13"
        elif self.options.vfx_platform == "CY2024" and (not hasattr(self, "version") or self.version == "3.10.13"):
            self.version = "3.11.9"

        # Python is always shared in OpenRV
        self.options.shared = True

        # Optimizations are enabled for Release builds
        if self.settings.build_type == "Release":
            self.options.optimizations = True
        else:
            self.options.optimizations = False

    def requirements(self):
        """Define package dependencies"""
        # Zlib is always required (following Conan Center Index pattern)
        # Use shared=True to match OpenRV's main project configuration
        self.requires("zlib/1.3.1", options={"shared": True})

        if self.options.with_ssl:
            # Use OpenSSL 1.1.1 for Python 3.10 + VFX 2023, OpenSSL 3.x for 3.11/2024
            if str(self.version).startswith("3.10") and str(self.options.vfx_platform) == "CY2023":
                self.requires("openssl/1.1.1u", options={"shared": True, "no_zlib": True})
            else:
                self.requires("openssl/3.5.0", options={"shared": True, "no_zlib": True})

    def system_requirements(self):
        """Define system package requirements"""
        if self.settings.os == "Linux":
            package_manager.Apt(self).install(
                [
                    "build-essential",
                    "zlib1g-dev",
                    "libncurses5-dev",
                    "libgdbm-dev",
                    "libnss3-dev",
                    "libssl-dev",
                    "libreadline-dev",
                    "libffi-dev",
                    "libsqlite3-dev",
                    "wget",
                    "libbz2-dev",
                    "uuid-dev",
                    "tk-dev",
                ]
            )
        elif self.settings.os == "Macos":
            # macOS dependencies are handled via Homebrew in the build method
            pass
        elif self.settings.os == "Windows":
            # Windows dependencies are typically handled via vcpkg or bundled
            # Visual Studio Build Tools are required
            pass

    def layout(self):
        cmake_layout(self)

    def source(self):
        """Download and extract Python source"""
        # Use conandata.yml for source information
        data = self.conan_data["sources"][self.version]
        get(
            self,
            data["url"],
            destination=self.source_folder,
            sha256=data["sha256"],
            strip_root=True,
        )

    def _get_lib_dir(self):
        """Get the library directory for the Python installation itself.
        Python built from source uses 'lib' as the default PLATLIBDIR
        (unless --with-platlibdir is passed to configure, which we don't do).
        Note: For dependency lib dirs (OpenSSL, zlib), use _get_dep_lib_dir() instead."""
        if self.settings.os == "Windows":
            return "libs"
        return "lib"

    def _get_dep_lib_dir(self, dep_name):
        """Get the library directory for a dependency by checking what actually exists."""
        dep = self.dependencies[dep_name]
        pkg = dep.package_folder
        for candidate in ("lib64", "lib"):
            if os.path.isdir(os.path.join(pkg, candidate)):
                return candidate
        return "lib"

    def _get_python_version_short(self):
        """Get short Python version (e.g., '3.11')"""
        major, minor = self.version.split(".")[:2]
        return f"{major}.{minor}"

    def _get_python_version_nodot(self):
        """Get Python version without dots (e.g., '311')"""
        major, minor = self.version.split(".")[:2]
        return f"{major}{minor}"

    def _install_homebrew_deps_macos(self):
        """Install macOS dependencies via Homebrew"""
        if self.settings.os != "Macos":
            return

        deps = ["readline", "tcl-tk@8", "python-tk", "xz"]
        for dep in deps:
            try:
                subprocess.run(["brew", "install", dep], check=True, capture_output=True)
            except subprocess.CalledProcessError:
                # Dependency might already be installed
                pass

    def _get_macos_configure_flags(self):
        """Get macOS-specific configure flags and environment variables"""
        if self.settings.os != "Macos":
            return [], {}

        try:
            # Get Homebrew prefixes
            readline_prefix = subprocess.run(
                ["brew", "--prefix", "readline"],
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()

            tcl_prefix = subprocess.run(
                ["brew", "--prefix", "tcl-tk@8"],
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()

            python_tk_prefix = subprocess.run(
                ["brew", "--prefix", "python-tk"],
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()

            xz_prefix = subprocess.run(
                ["brew", "--prefix", "xz"], capture_output=True, text=True, check=True
            ).stdout.strip()

            sdk_prefix = subprocess.run(
                ["xcrun", "--show-sdk-path"], capture_output=True, text=True, check=True
            ).stdout.strip()

            # Build CPPFLAGS and LDFLAGS
            include_dirs = [
                os.path.join(readline_prefix, "include"),
                os.path.join(tcl_prefix, "include"),
                os.path.join(xz_prefix, "include"),
                os.path.join(sdk_prefix, "usr", "include"),
                os.path.join(python_tk_prefix, "include"),
            ]

            lib_dirs = [
                os.path.join(readline_prefix, "lib"),
                os.path.join(tcl_prefix, "lib"),
                os.path.join(xz_prefix, "lib"),
                os.path.join(sdk_prefix, "usr", "lib"),
                os.path.join(python_tk_prefix, "lib"),
            ]

            cppflags = " ".join([f"-I{d}" for d in include_dirs])
            ldflags = " ".join([f"-L{d}" for d in lib_dirs])

            pkg_config_path = os.path.join(tcl_prefix, "lib", "pkgconfig")

            env_vars = {
                "CPPFLAGS": cppflags,
                "LDFLAGS": ldflags,
                "PKG_CONFIG_PATH": pkg_config_path,
            }

            return [], env_vars

        except subprocess.CalledProcessError as e:
            self.output.warning(f"Failed to get Homebrew prefixes: {e}")
            return [], {}

    def _create_sitecustomize_content(self):
        """Load sitecustomize.py content from the exported file (mirrors make_python.py approach)."""
        template_path = os.path.join(self.recipe_folder, "sitecustomize.py")
        with open(template_path, "r") as f:
            return f.read()

    def _setup_openssl_environment(self, build_env, configure_args):
        """Setup OpenSSL environment following Conan Center Index approach"""
        openssl_dep = self.dependencies["openssl"]
        openssl_root = openssl_dep.package_folder
        openssl_lib_dir = os.path.join(openssl_root, self._get_dep_lib_dir("openssl"))
        openssl_pkgconfig_dir = os.path.join(openssl_lib_dir, "pkgconfig")

        self.output.info(f"Setting up OpenSSL environment with root: {openssl_root}")

        # Primary configure argument - matches Conan Center Index approach
        configure_args.append(f"--with-openssl={openssl_root}")

        # For Python >= 3.11, patch configure to add zlib dependency
        # (following Conan Center Index pattern)
        if self.version.startswith("3.11"):
            configure_path = os.path.join(self.source_folder, "configure")
            if os.path.exists(configure_path):
                try:
                    with open(configure_path, "r") as f:
                        content = f.read()
                    if (
                        'OPENSSL_LIBS="-lssl -lcrypto"' in content
                        and 'OPENSSL_LIBS="-lssl -lcrypto -lz"' not in content
                    ):
                        content = content.replace(
                            'OPENSSL_LIBS="-lssl -lcrypto"',
                            'OPENSSL_LIBS="-lssl -lcrypto -lz"',
                        )
                        with open(configure_path, "w") as f:
                            f.write(content)
                        self.output.info("Patched configure script to add zlib to OpenSSL libs")
                except Exception as e:
                    self.output.warning(f"Could not patch configure script: {e}")

        # On Linux, add RPATH argument
        if self.settings.os == "Linux":
            configure_args.append(f"--with-openssl-rpath={openssl_lib_dir}")

        # Set PKG_CONFIG_PATH to help configure find OpenSSL
        current_pkg_config = build_env.get("PKG_CONFIG_PATH", "")
        if os.path.exists(openssl_pkgconfig_dir):
            if current_pkg_config:
                build_env["PKG_CONFIG_PATH"] = f"{openssl_pkgconfig_dir}:{current_pkg_config}"
            else:
                build_env["PKG_CONFIG_PATH"] = openssl_pkgconfig_dir

        # For macOS, also combine with system dependencies
        if self.settings.os == "Macos":
            macos_flags, macos_env = self._get_macos_configure_flags()
            if "PKG_CONFIG_PATH" in macos_env:
                pkg_config_paths = [openssl_pkgconfig_dir, macos_env["PKG_CONFIG_PATH"]]
                build_env["PKG_CONFIG_PATH"] = ":".join(pkg_config_paths)

        self.output.info(
            f"Added OpenSSL configure arguments: {[arg for arg in configure_args if 'openssl' in arg.lower()]}"
        )

    def _patch_setup_py_for_openssl(self):
        """Patch setup.py following Conan Center Index approach for SSL detection"""
        if not self.options.with_ssl or "openssl" not in self.dependencies:
            return

        setup_py_path = os.path.join(self.source_folder, "setup.py")
        if not os.path.exists(setup_py_path):
            return

        openssl_dep = self.dependencies["openssl"]
        openssl_info = openssl_dep.cpp_info.aggregated_components()

        # Get zlib info for combined SSL libraries (following Conan Center Index pattern)
        zlib_info = None
        if "zlib" in self.dependencies:
            zlib_info = self.dependencies["zlib"].cpp_info.aggregated_components()

        # Read the original setup.py
        with open(setup_py_path, "r") as f:
            content = f.read()

        original_content = content

        # For Python < 3.11, patch openssl variables directly (Conan Center Index approach)
        if self.version.startswith("3.11") or self.version.startswith("3.10"):
            # Patch openssl_includes
            openssl_includes = openssl_info.includedirs
            if zlib_info:
                openssl_includes = openssl_includes + zlib_info.includedirs

            if "openssl_includes = " in content:
                content = content.replace("openssl_includes = ", f"openssl_includes = {openssl_includes} #")
                self.output.info(f"Patched openssl_includes: {openssl_includes}")

            # Patch openssl_libdirs
            openssl_libdirs = openssl_info.libdirs
            if zlib_info:
                openssl_libdirs = openssl_libdirs + zlib_info.libdirs

            if "openssl_libdirs = " in content:
                content = content.replace("openssl_libdirs = ", f"openssl_libdirs = {openssl_libdirs} #")
                self.output.info(f"Patched openssl_libdirs: {openssl_libdirs}")

            # Patch openssl_libs
            openssl_libs = openssl_info.libs
            if zlib_info:
                openssl_libs = openssl_libs + zlib_info.libs

            if "openssl_libs = " in content:
                content = content.replace("openssl_libs = ", f"openssl_libs = {openssl_libs} #")
                self.output.info(f"Patched openssl_libs: {openssl_libs}")

        # Write back the patched content if changes were made
        if content != original_content:
            with open(setup_py_path, "w") as f:
                f.write(content)
            self.output.info("Successfully patched setup.py for OpenSSL integration using Conan Center Index approach")
        else:
            self.output.info("No setup.py patching needed or patterns not found")

    def _patch_makefile_for_rpath(self, makefile_path):
        """Patch the Makefile to use proper RPATH settings.
        Matches make_python.py: line-by-line processing to only modify lines
        starting with LINKFORSHARED=, and apply install_name replacement on macOS."""
        if not os.path.exists(makefile_path):
            return

        old_makefile_path = makefile_path + ".old"
        os.rename(makefile_path, old_makefile_path)

        with open(old_makefile_path, "r") as old_file:
            with open(makefile_path, "w") as new_file:
                for line in old_file:
                    # On macOS, change install_name to use @rpath
                    if self.settings.os == "Macos":
                        line = line.replace(
                            "-Wl,-install_name,$(prefix)/lib/libpython$(",
                            "-Wl,-install_name,@rpath/libpython$(",
                        )

                    # Only append RPATH flags to lines that start with LINKFORSHARED=
                    if line.startswith("LINKFORSHARED="):
                        if self.settings.os == "Linux":
                            new_file.write(line.rstrip() + " -Wl,-rpath,'$$ORIGIN/../lib',-rpath,'$$ORIGIN/../Qt'\n")
                        elif self.settings.os == "Macos":
                            new_file.write(
                                line.rstrip() + " -Wl,-rpath,@executable_path/../lib,-rpath,@executable_path/../Qt\n"
                            )
                        else:
                            new_file.write(line)
                    else:
                        new_file.write(line)

    # Package installation (OTIO, PyOpenGL, cryptography, etc.) is handled by
    # cmake/dependencies/python.cmake via requirements.txt, not by this recipe.
    # This matches make_python.py's patch_python_distribution() which only runs ensurepip.

    def _verify_ssl_support(self, python_executable):
        """Verify that SSL modules were built correctly"""
        try:
            # Test SSL module import
            ssl_test = subprocess.run(
                [
                    python_executable,
                    "-c",
                    "import ssl; print(f'SSL version: {ssl.OPENSSL_VERSION}'); import _ssl, _hashlib; print('SSL modules: OK')",
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            self.output.info("SSL verification successful:")
            self.output.info(ssl_test.stdout.strip())

        except subprocess.CalledProcessError as e:
            self.output.warning("SSL verification failed:")
            self.output.warning(f"stdout: {e.stdout}")
            self.output.warning(f"stderr: {e.stderr}")

            # Try to get more details about what's missing
            try:
                missing_test = subprocess.run(
                    [
                        python_executable,
                        "-c",
                        "import sys; print('Missing modules:'); "
                        "modules = ['ssl', '_ssl', '_hashlib']; "
                        "for m in modules: "
                        "    try: __import__(m); print(f'  {m}: OK') "
                        "    except ImportError as e: print(f'  {m}: MISSING - {e}')",
                    ],
                    capture_output=True,
                    text=True,
                )

                self.output.info("Module availability check:")
                self.output.info(missing_test.stdout)

            except subprocess.CalledProcessError:
                self.output.warning("Could not perform detailed SSL module check")

    def _install_python_packages(self, python_executable):
        """Ensure pip is available — matches make_python.py's patch_python_distribution().
        Actual package installation (OTIO, PyOpenGL, etc.) is handled by
        cmake/dependencies/python.cmake via requirements.txt."""
        self.output.info("Running ensurepip...")
        subprocess.run(
            [python_executable, "-s", "-E", "-I", "-m", "ensurepip"],
            check=True,
        )

    def _install_sitecustomize(self, python_home):
        """Install sitecustomize.py for SSL certificate handling"""
        site_packages_dirs = glob.glob(os.path.join(python_home, "**", "site-packages"), recursive=True)

        if not site_packages_dirs:
            raise ConanException("Could not find site-packages directory")

        site_packages = site_packages_dirs[0]
        sitecustomize_path = os.path.join(site_packages, "sitecustomize.py")

        if os.path.exists(sitecustomize_path):
            os.remove(sitecustomize_path)

        save(self, sitecustomize_path, self._create_sitecustomize_content())

    def _copy_openssl_libs(self, python_home):
        """Copy OpenSSL libraries to Python installation"""
        if not self.options.with_ssl:
            return

        openssl_dep = self.dependencies["openssl"]
        openssl_lib_dir = os.path.join(openssl_dep.package_folder, self._get_dep_lib_dir("openssl"))

        if self.settings.os == "Macos":
            # Copy dylibs and update install names
            openssl_libs = glob.glob(os.path.join(openssl_lib_dir, "lib*.dylib*"))
            openssl_libs = [lib for lib in openssl_libs if not os.path.islink(lib)]

            python_lib_dir = os.path.join(python_home, "lib")

            for lib_path in openssl_libs:
                lib_name = os.path.basename(lib_path)
                dest_path = os.path.join(python_lib_dir, lib_name)
                shutil.copy2(lib_path, dest_path)

                # Update install names in Python modules
                python_modules = glob.glob(os.path.join(python_home, "lib", "**", "*.so"), recursive=True)
                for module in python_modules:
                    try:
                        subprocess.run(
                            [
                                "install_name_tool",
                                "-change",
                                lib_path,
                                f"@rpath/{lib_name}",
                                module,
                            ],
                            check=True,
                            capture_output=True,
                        )
                    except subprocess.CalledProcessError:
                        pass  # Some modules might not link to this library

        elif self.settings.os == "Linux":
            # Copy .so files
            openssl_libs = glob.glob(os.path.join(openssl_lib_dir, "lib*.so*"))
            python_lib_dir = os.path.join(python_home, self._get_lib_dir())

            for lib_path in openssl_libs:
                shutil.copy2(lib_path, python_lib_dir)

        elif self.settings.os == "Windows":
            # Copy DLLs and libs
            openssl_bin_dir = os.path.join(openssl_dep.package_folder, "bin")
            openssl_dlls = glob.glob(os.path.join(openssl_bin_dir, "lib*"))

            python_bin_dir = os.path.join(python_home, "bin")
            for dll_path in openssl_dlls:
                shutil.copy2(dll_path, python_bin_dir)

            openssl_libs = glob.glob(os.path.join(openssl_lib_dir, "lib*"))
            python_libs_dir = os.path.join(python_home, "libs")
            for lib_path in openssl_libs:
                shutil.copy2(lib_path, python_libs_dir)

    def _fix_failed_ssl_modules(self):
        """Fix SSL modules that were marked as failed during Python build"""
        # The Python build marks some .so files as _failed if it cannot load OpenSSL during build tests.
        # This is expected with our OpenSSL package which works with RPATH, but RPATH isn't set during build tests.
        # If the lib failed for other reasons, it will fail later in our verification.

        for failed_lib in glob.glob(
            os.path.join(self.package_folder, "lib", "**", "*_failed.so"),
            recursive=True,
        ):
            if "ssl" in failed_lib or "hashlib" in failed_lib:
                fixed_lib = failed_lib.replace("_failed.so", ".so")
                self.output.info(f"Fixing failed SSL module: {failed_lib} -> {fixed_lib}")
                shutil.move(failed_lib, fixed_lib)

    def build(self):
        """Build Python from source"""
        if self.settings.os == "Windows":
            self._build_windows()
        else:
            self._build_unix()

    def _build_windows(self):
        """Build Python on Windows using MSBuild"""
        import subprocess

        # Apply Windows-specific patches if needed
        self._apply_windows_patches()

        # Build using PCBuild
        pcbuild_dir = os.path.join(self.source_folder, "PCBuild")

        # Determine build configuration
        build_config = "Debug" if self.settings.build_type == "Debug" else "Release"
        platform_name = "x64" if self.settings.arch == "x86_64" else "Win32"

        # Build arguments
        build_args = [
            os.path.join(pcbuild_dir, "build.bat"),
            "-c",
            build_config,
            "-p",
            platform_name,
            "-t",
            "Rebuild",
        ]

        self.output.info(f"Building Python with: {build_args}")

        # Set up environment variables (following make_python.py approach)
        import sys

        path_env = os.path.pathsep.join(
            [
                os.path.dirname(sys.executable),
                os.environ.get("PATH", ""),
            ]
        )

        subprocess_env = {**os.environ, "PYTHON": sys.executable, "PATH": path_env}

        # Add OpenSSL configuration via environment variables if available
        if self.options.with_ssl and "openssl" in self.dependencies:
            openssl_dep = self.dependencies["openssl"]
            openssl_root = openssl_dep.package_folder
            subprocess_env["LC_RPATH"] = os.path.join(openssl_root, "lib")

        subprocess.run(build_args, cwd=self.source_folder, env=subprocess_env, check=True)

        # Install using VFX platform-specific method
        if self.options.vfx_platform == "CY2023":
            self._install_windows_vfx2023()
        else:  # VFX 2024
            self._install_windows_layout()

    def _apply_windows_patches(self):
        """Apply Windows-specific patches for Python 3.11"""
        if self.version.startswith("3.11"):
            # Apply patches for OpenSSL integration
            patches = [
                "python.3.11.openssl.props.patch",
                "python.3.11.python.props.patch",
                "python.3.11.get_externals.bat.patch",
            ]

            for patch_file in patches:
                patch_path = os.path.join(self.source_folder, "..", "patches", patch_file)
                if os.path.exists(patch_path):
                    try:
                        subprocess.run(
                            ["patch", "-p1", "-i", patch_path],
                            cwd=self.source_folder,
                            check=True,
                        )
                        self.output.info(f"Applied patch: {patch_file}")
                    except subprocess.CalledProcessError as e:
                        self.output.warning(f"Failed to apply patch {patch_file}: {e}")

    def _install_windows_vfx2023(self):
        """Install Python on Windows using VFX 2023 approach (manual file copying)"""
        build_dir = os.path.join(self.source_folder, "PCBuild", "amd64")

        # include
        src_dir = os.path.join(self.source_folder, "Include")
        dst_dir = os.path.join(self.package_folder, "include")
        shutil.copytree(src_dir, dst_dir)
        src_file = os.path.join(self.source_folder, "PC", "pyconfig.h")
        dst_file = os.path.join(dst_dir, "pyconfig.h")
        shutil.copyfile(src_file, dst_file)

        # lib
        src_dir = os.path.join(self.source_folder, "Lib")
        dst_dir = os.path.join(self.package_folder, "lib")
        shutil.copytree(src_dir, dst_dir)

        # libs - required by pyside2
        dst_dir = os.path.join(self.package_folder, "libs")
        os.makedirs(dst_dir, exist_ok=True)
        python_libs = glob.glob(os.path.join(build_dir, "python*.lib"))
        for python_lib in python_libs:
            shutil.copy(python_lib, dst_dir)

        # bin
        src_dir = build_dir
        dst_dir = os.path.join(self.package_folder, "bin")
        shutil.copytree(src_dir, dst_dir)

        # Create a python3.exe file to mimic Mac+Linux
        python_exe = "python_d.exe" if self.settings.build_type == "Debug" else "python.exe"
        src_file = os.path.join(dst_dir, python_exe)
        dst_file = os.path.join(dst_dir, "python3.exe")
        shutil.copyfile(src_file, dst_file)

        # Post-install Windows-specific setup
        self._post_install_windows_setup()

    def _install_windows_layout(self):
        """Install Python on Windows using the layout script"""
        # Get build output directory
        build_dir = os.path.join(self.source_folder, "PCBuild", "amd64")

        # Determine Python executable name
        python_exe = "python_d.exe" if self.settings.build_type == "Debug" else "python.exe"
        python_executable = os.path.join(build_dir, python_exe)

        if not os.path.exists(python_executable):
            raise ConanException(f"Python executable not found: {python_executable}")

        # Create temporary directory for layout
        temp_dir = os.path.join(self.source_folder, "..", "temp")
        os.makedirs(temp_dir, exist_ok=True)

        # Layout script arguments
        layout_script = os.path.join(self.source_folder, "PC", "layout", "main.py")
        install_args = [
            python_executable,
            layout_script,
            "-vv",
            "--source",
            self.source_folder,
            "--build",
            build_dir,
            "--copy",
            self.package_folder,
            "--temp",
            temp_dir,
            "--preset-default",
            "--include-dev",
            "--include-symbols",
            "--include-tcltk",
            "--include-tests",
            "--include-venv",
        ]

        if self.settings.build_type == "Debug":
            install_args.append("--debug")

        self.output.info(f"Installing Python with layout script: {install_args}")
        subprocess.run(install_args, cwd=self.source_folder, check=True)

        # VFX 2024 specific file handling (following make_python.py install_python_vfx2024)
        self._handle_vfx2024_windows_files(build_dir)

        # Post-install Windows-specific setup
        self._post_install_windows_setup()

    def _handle_vfx2024_windows_files(self, build_dir):
        """Handle VFX 2024 specific file operations (following make_python.py install_python_vfx2024)"""
        # Create necessary directories
        bin_dir = os.path.join(self.package_folder, "bin")
        libs_dir = os.path.join(self.package_folder, "libs")
        os.makedirs(bin_dir, exist_ok=True)
        os.makedirs(libs_dir, exist_ok=True)

        # Create python3.exe file to mimic Mac+Linux
        python_exe = "python_d.exe" if self.settings.build_type == "Debug" else "python.exe"
        src_file = os.path.join(self.package_folder, python_exe)
        dst_file = os.path.join(bin_dir, "python3.exe")

        if os.path.exists(src_file):
            self.output.info(f"Copy {src_file} to {dst_file}")
            shutil.copyfile(src_file, dst_file)

        # Move files under root directory into the bin folder
        for filename in os.listdir(self.package_folder):
            file_path = os.path.join(self.package_folder, filename)
            if os.path.isfile(file_path) and not filename.startswith("."):
                dst_path = os.path.join(bin_dir, filename)
                if not os.path.exists(dst_path):
                    shutil.move(file_path, dst_path)

        # Manually copy python3.lib and python{version}.lib because the layout script may not copy them
        python_version_nodot = self._get_python_version_nodot()
        python3_lib = "python3_d.lib" if self.settings.build_type == "Debug" else "python3.lib"
        python_version_lib = (
            f"python{python_version_nodot}_d.lib"
            if self.settings.build_type == "Debug"
            else f"python{python_version_nodot}.lib"
        )

        for lib_name in [python3_lib, python_version_lib]:
            src_lib = os.path.join(build_dir, lib_name)
            if os.path.exists(src_lib):
                # Copy to both bin and libs directories
                dst_bin = os.path.join(bin_dir, lib_name)
                dst_libs = os.path.join(libs_dir, lib_name)
                shutil.copy(src_lib, dst_bin)
                shutil.copy(src_lib, dst_libs)

        # Copy Tcl and Tk DLLs for Debug builds (following make_python.py logic)
        if self.settings.build_type == "Debug":
            for dll_name in ["tcl86t.dll", "tk86t.dll"]:
                src_dll = os.path.join(build_dir, dll_name)
                if os.path.exists(src_dll):
                    dst_dll = os.path.join(bin_dir, dll_name)
                    shutil.copyfile(src_dll, dst_dll)
                    self.output.info(f"Copied {dll_name} for Debug build")

    def _post_install_windows_setup(self):
        """Perform Windows-specific post-installation setup"""
        # Create bin directory and move files
        bin_dir = os.path.join(self.package_folder, "bin")
        libs_dir = os.path.join(self.package_folder, "libs")
        os.makedirs(bin_dir, exist_ok=True)
        os.makedirs(libs_dir, exist_ok=True)

        # Create python3.exe symlink for compatibility
        python_exe = "python_d.exe" if self.settings.build_type == "Debug" else "python.exe"
        src_python = os.path.join(self.package_folder, python_exe)
        dst_python = os.path.join(bin_dir, "python3.exe")

        if os.path.exists(src_python):
            shutil.copy2(src_python, dst_python)
            self.output.info(f"Created python3.exe: {dst_python}")

        # Move root-level files to bin directory
        for item in os.listdir(self.package_folder):
            item_path = os.path.join(self.package_folder, item)
            if os.path.isfile(item_path) and item.endswith((".exe", ".dll", ".pyd")):
                dst_path = os.path.join(bin_dir, item)
                if not os.path.exists(dst_path):
                    shutil.move(item_path, dst_path)

        # Copy OpenSSL libraries if available
        self._copy_openssl_libs_windows()

        # Ensure pip is available and install sitecustomize.py.
        # Actual package installation (OTIO, PyOpenGL, etc.) is handled by
        # cmake/dependencies/python.cmake via requirements.txt.
        python_executable = dst_python if os.path.exists(dst_python) else src_python
        self._install_python_packages(python_executable)

        # Install sitecustomize.py
        self._install_sitecustomize(self.package_folder)

    def _copy_openssl_libs_windows(self):
        """Copy OpenSSL libraries for Windows"""
        if not self.options.with_ssl or "openssl" not in self.dependencies:
            return

        openssl_dep = self.dependencies["openssl"]
        openssl_bin_dir = os.path.join(openssl_dep.package_folder, "bin")
        openssl_lib_dir = os.path.join(openssl_dep.package_folder, self._get_dep_lib_dir("openssl"))

        python_bin_dir = os.path.join(self.package_folder, "bin")
        python_libs_dir = os.path.join(self.package_folder, "libs")

        # Copy DLLs to bin directory
        for dll_pattern in ["libssl*.dll", "libcrypto*.dll", "*.dll"]:
            for dll_path in glob.glob(os.path.join(openssl_bin_dir, dll_pattern)):
                if "ssl" in os.path.basename(dll_path).lower() or "crypto" in os.path.basename(dll_path).lower():
                    dst_path = os.path.join(python_bin_dir, os.path.basename(dll_path))
                    shutil.copy2(dll_path, dst_path)
                    self.output.info(f"Copied OpenSSL DLL: {os.path.basename(dll_path)}")

        # Copy import libraries to libs directory
        for lib_pattern in ["libssl*.lib", "libcrypto*.lib", "ssl*.lib", "crypto*.lib"]:
            for lib_path in glob.glob(os.path.join(openssl_lib_dir, lib_pattern)):
                dst_path = os.path.join(python_libs_dir, os.path.basename(lib_path))
                shutil.copy2(lib_path, dst_path)
                self.output.info(f"Copied OpenSSL lib: {os.path.basename(lib_path)}")

    # OpenTimelineIO and other package installations (including Windows Debug OTIO)
    # are handled by cmake/dependencies/python.cmake via requirements.txt.

    def _build_unix(self):
        """Build Python on Unix-like systems (macOS, Linux)"""
        # Install macOS dependencies if needed
        if self.settings.os == "Macos":
            self._install_homebrew_deps_macos()

        # Prepare configure arguments
        configure_args = [
            os.path.join(self.source_folder, "configure"),
            f"--srcdir={self.source_folder}",
            f"--prefix={self.package_folder}",
            f"--exec-prefix={self.package_folder}",
        ]

        if self.options.shared:
            configure_args.append("--enable-shared")

        if self.options.optimizations and self.settings.build_type == "Release":
            configure_args.append("--enable-optimizations")

        # Get platform-specific environment
        extra_args, env_vars = self._get_macos_configure_flags()
        configure_args.extend(extra_args)

        # Setup environment
        build_env = os.environ.copy()
        build_env.update(env_vars)

        # Configure OpenSSL integration before configure step
        if self.options.with_ssl:
            self._setup_openssl_environment(build_env, configure_args)

        # Configure
        self.output.info("Configuring Python...")

        # Make configure script executable
        configure_script = os.path.join(self.source_folder, "configure")
        if os.path.exists(configure_script):
            os.chmod(configure_script, 0o755)

        subprocess.run(configure_args, cwd=self.source_folder, env=build_env, check=True)

        # Patch Makefile for RPATH
        makefile_path = os.path.join(self.source_folder, "Makefile")
        self._patch_makefile_for_rpath(makefile_path)

        # Build
        self.output.info("Building Python...")
        cpu_count = os.cpu_count() or 1
        make_args = ["make", f"-j{cpu_count}"]

        # Ensure OpenSSL and zlib libraries are findable during runtime
        if self.settings.os == "Macos":
            openssl_lib_dir = os.path.join(
                self.dependencies["openssl"].package_folder, self._get_dep_lib_dir("openssl")
            )
            zlib_lib_dir = os.path.join(self.dependencies["zlib"].package_folder, self._get_dep_lib_dir("zlib"))
            build_env["DYLD_LIBRARY_PATH"] = (
                f"{openssl_lib_dir}:{zlib_lib_dir}:{build_env.get('DYLD_LIBRARY_PATH', '')}"
            )

        subprocess.run(make_args, cwd=self.source_folder, env=build_env, check=True)

        # Install
        self.output.info("Installing Python...")
        install_args = ["make", "install"]
        subprocess.run(install_args, cwd=self.source_folder, env=build_env, check=True)

        # Post-install setup
        self._post_install_setup()

    def _post_install_setup(self):
        """Perform post-installation setup — matches make_python.py's patch_python_distribution().
        Package installation and comprehensive testing happen later in the CMake build phase
        via cmake/dependencies/python.cmake and src/build/test_python.py."""
        # Get Python executable first
        if self.settings.os == "Windows":
            python_exe = os.path.join(self.package_folder, "bin", "python.exe")
        else:
            python_exe = os.path.join(self.package_folder, "bin", "python3")

        # Step 1: Create python symlink (matches make_python.py)
        if self.settings.os != "Windows":
            python3_path = os.path.realpath(os.path.join(self.package_folder, "bin", "python3"))
            python_path = os.path.join(os.path.dirname(python3_path), "python")

            if not os.path.exists(python_path):
                os.symlink(os.path.basename(python3_path), python_path)

        # Step 2: Fix _failed.so files — Python build marks SSL modules as failed
        # if OpenSSL wasn't loadable during build tests (expected with RPATH builds)
        self._fix_failed_ssl_modules()

        # Step 3: Copy OpenSSL libraries and set up proper RPATH/library paths
        self._copy_openssl_libs(self.package_folder)

        # Step 4: Ensure pip is available (ensurepip)
        self._install_python_packages(python_exe)

        # Step 5: Install sitecustomize.py
        self._install_sitecustomize(self.package_folder)

        # Step 6: Verify SSL modules were built correctly
        self._verify_ssl_support(python_exe)

    def package(self):
        """Package the built Python"""
        # Everything is already installed to package_folder during build
        pass

    def package_info(self):
        """Define package information for consumers"""
        # Set up library and include paths
        self.cpp_info.libs = []  # Python is typically linked dynamically

        lib_dir = self._get_lib_dir()

        if self.settings.os == "Windows":
            self.cpp_info.libdirs = ["libs"]
            self.cpp_info.bindirs = ["bin", "Scripts"]
            self.cpp_info.includedirs = ["include"]

            # Python library name
            python_version_nodot = self._get_python_version_nodot()
            debug_suffix = "_d" if self.settings.build_type == "Debug" else ""
            python_lib = f"python{python_version_nodot}{debug_suffix}"
            self.cpp_info.libs = [python_lib]

        else:
            self.cpp_info.libdirs = [lib_dir]
            self.cpp_info.bindirs = ["bin"]

            python_version_short = self._get_python_version_short()
            self.cpp_info.includedirs = [f"include/python{python_version_short}"]

            # Python library name
            python_lib = f"python{python_version_short}"
            self.cpp_info.libs = [python_lib]

        # Set environment variables
        self.cpp_info.set_property("cmake_find_mode", "both")
        self.cpp_info.set_property("cmake_file_name", "Python")
        self.cpp_info.set_property("cmake_target_name", "Python::Python")

        # Python executable path
        if self.settings.os == "Windows":
            python_exe = os.path.join(self.package_folder, "bin", "python.exe")
        else:
            python_exe = os.path.join(self.package_folder, "bin", "python3")

        self.cpp_info.set_property("python_executable", python_exe)

        # Environment variables for runtime
        self.env_info.PATH.append(os.path.join(self.package_folder, "bin"))
        if self.settings.os != "Windows":
            self.env_info.LD_LIBRARY_PATH.append(os.path.join(self.package_folder, lib_dir))

        # Additional properties for CMake integration
        self.cpp_info.set_property("python_version", self.version)
        self.cpp_info.set_property("python_version_short", self._get_python_version_short())
