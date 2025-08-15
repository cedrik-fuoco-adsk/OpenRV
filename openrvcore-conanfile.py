import os
from conan import ConanFile
from conan.tools.apple import is_apple_os
from conan.tools.cmake import CMake, CMakeDeps, cmake_layout, CMakeToolchain
from conan.tools.env import VirtualBuildEnv

# The comment below is relevant for WINDOWS only because of the usage of MSYS2.

# The Python path should be pre-appended to the PATH environment variables in the
# buildenv section of the profile used to build the recipe.
# It will ensure that the Python path is the first path in the environment variable.
# This is a special case because of the way that MSYS2 merges the PATH environment variables.
# (MSYS2 PATH = MSYS2 PATH + CMD PATH)
#
# Here's an example of a buildenv section (also, see example under conan/profiles):
#
# [buildenv]
# PATH=+(path)/c/Program Files/Python310
#


class OpenRVBase:
    setuptools_use_distutils = ""

    def layout(self):
        cmake_layout(self)

    def build_requirements(self):
        if self.settings.os == "Windows":
            self.win_bash = True
            if not self.conf.get("tools.microsoft.bash:path", check_type=str):
                pkgs = [
                    "mingw-w64-x86_64-autotools",
                    "mingw-w64-x86_64-cmake",
                    "mingw-w64-x86_64-cmake-cmcldeps",
                    "mingw-w64-x86_64-glew",
                    "mingw-w64-x86_64-libarchive",
                    "mingw-w64-x86_64-make",
                    "mingw-w64-x86_64-meson",
                    "mingw-w64-x86_64-python-pip",
                    "mingw-w64-x86_64-python-psutil",
                    "mingw-w64-x86_64-toolchain",
                    "autoconf",
                    "automake",
                    "bison",
                    "flex",
                    "git",
                    "libtool",
                    "nasm",
                    "p7zip",
                    "patch",
                ]
                pkgsStr = " ".join(pkgs)
                self.tool_requires(
                    "msys2/cci.latest", options={"additional_packages": pkgsStr}
                )
        else:
            self.tool_requires("ninja/1.11.1")

    def requirements(self):

        self.requires("zlib/1.3.1", force=True, options={"shared": True})

        if is_apple_os(self):
            # The link for the source code is wrong in the recipe on conan center.
            # Since it has to be built for MacOS, we need a custom recipe.
            # TODO: Will probably have to expand the if condition to include all the debug builds
            #       since they are not hosted on conan center I think.
            self.requires("libatomic_ops/7.8.2@openrv", options={"shared": False})
        else:
            # For Linux, the binaries are available.
            # TBD for Windows
            self.requires("libatomic_ops/7.8.2", options={"shared": False})

        # Version conflict: ffmpeg/4.4.3->libwebp/1.3.2, ->libwebp/1.2.1
        # Webp >=1.3.0 depends on sharpyuv and it causes issues with OIIO.
        self.requires("libwebp/1.2.1", force=True, options={"shared": False})

        self.requires("dav1d/1.4.3", force=True, options={"shared": False})

        self.requires(
            "libjpeg-turbo/2.1.4",
            force=True,
            options={
                "shared": True,
            },
        )

        # Override openssl version for ffmpeg, but do not use it for OpenRV right now.
        self.requires(
            "openssl/3.5.0", force=True, options={"shared": True, "no_zlib": True}
        )

        # Override boost version for other dependencies.
        self.requires(
            "boost/1.82.0#7053477b271b8c39e046f784405b402f",
            force=True,
            options={"shared": True, "extra_b2_flags": "-d+0 -s NO_LZMA=1"},
        )

        # Override imath version for other dependencies.
        self.requires("imath/3.1.6", force=True, options={"shared": True})

        # Python ported from make_python.py.
        # This package is customized for RV.
        self.requires(
            "python/3.11.9@openrv",
            options={
                # These options are the default for the vfx_platform 2024.
                "vfx_platform": "2024",
                "shared": True,
                "optimizations": True,
                "with_tkinter": True,
                "with_ssl": True,
            },
        )

        # PySide6 for Qt6 bindings - replaces manual build in python.cmake
        self.requires(
            "pyside6/6.5.3@openrv",
            options={
                "python_version": "3.11",
                "vfx_platform": "2024",
                "shared": True,
                "with_ssl": True,
            },
        )

    def generate(self):
        buildenv = VirtualBuildEnv(self)
        buildenv.generate()

        deps = CMakeDeps(self)
        deps.generate()

        # Setup CMakeToolchain generator.
        if not self.settings.os == "Windows":
            tc = CMakeToolchain(self, generator="Ninja")
        else:
            tc = CMakeToolchain(self)

        # Setup variables for CMake's cached variables.
        # TODO: Find a way to get the Qt location without hardcoding it.
        qt_version = os.getenv("QT_VERSION", "6.5.3")
        if not self.settings.os == "Windows":
            home = os.getenv("HOME")
            if home:
                qt_dir = os.path.join(home, "Qt6.5.3", qt_version)

        if self.settings.os == "Linux":
            qt_home = os.getenv("QT_HOME", os.path.join(qt_dir, "gcc_64"))
        elif self.settings.os == "Macos":
            qt_home = os.getenv("QT_HOME", os.path.join(qt_dir, "clang_64"))
        elif self.settings.os == "Windows":
            qt_home = os.getenv("QT_HOME", f"c:/Qt/{qt_version}/msvc2019_64")
            win_perl_location = os.getenv("WIN_PERL", "c:/Strawberry/perl/bin")
            self.setuptools_use_distutils = "stdlib"

        # TODO: Add option to select CY2023 or CY2024
        tc.cache_variables["RV_VFX_PLATFORM"] = "CY2024"

        # Set up CMake's cached variables.
        tc.cache_variables["RV_DEPS_QT6_LOCATION"] = qt_home
        if self.settings.os == "Windows":
            tc.cache_variables["RV_DEPS_WIN_PERL_ROOT"] = win_perl_location

        tc.cache_variables["CMAKE_BUILD_PARALLEL_LEVEL"] = str(os.cpu_count())

        # Make sure that CMAKE_BUILD_TYPE is specified in the cmake command that Conan use.
        # It seems needed on Windows for MS Visual Studio (multi-config generator).
        tc.cache_variables["CMAKE_BUILD_TYPE"] = str(self.settings.build_type)

        tc.cache_variables["CMAKE_FIND_PACKAGE_TARGETS_GLOBAL"] = "ON"

        # Generate the CMake's toolchain and preset files.
        tc.generate()

    def build(self):
        command = f"python3 -m pip install --user --upgrade -r requirements.txt"
        if self.settings.os == "Windows":
            command = (
                f"SETUPTOOLS_USE_DISTUTILS={self.setuptools_use_distutils} {command}"
            )
        self.run(command, cwd=self.source_folder)

        cmake = CMake(self)
        cmake.configure()
        cmake.build(target="main_executable")


class PyReq(ConanFile):
    name = "openrvcore"
    version = "1.0.0"
    package_type = "python-require"
