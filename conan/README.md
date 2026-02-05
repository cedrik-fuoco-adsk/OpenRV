# Conan Integration for OpenRV

This directory contains Conan package manager configuration for building OpenRV with pre-built dependencies.

## Overview

OpenRV supports two build modes controlled by the `RV_USE_PACKAGE_MANAGER` CMake option:

- **Traditional mode** (default, `RV_USE_PACKAGE_MANAGER=OFF`): Builds all dependencies from source using ExternalProject_Add
- **Package manager mode** (`RV_USE_PACKAGE_MANAGER=ON`): Uses pre-built packages from Conan via find_package()

## Directory Structure

```
conan/
├── extensions/
│   └── hooks/
│       └── hook_atomic_ops_source.py    # Conan hook for atomic_ops
├── profiles/
│   ├── arm64_apple_release              # macOS ARM64
│   ├── x86_64_apple_release             # macOS x86_64
│   ├── x86_64_rocky8                    # Linux Rocky 8
│   └── x86_64_windows                   # Windows x64
├── recipes/
│   ├── ffmpeg/                          # Custom FFmpeg recipe with OpenRV options
│   ├── pyside6/                         # Custom PySide6 recipe
│   └── python/                          # Custom Python recipe (VFX-aligned)
└── README.md                            # This file
```

## Quick Start

### 1. Prerequisites

- Conan 2.x (`pip install conan>=2.0`)
- CMake 3.24+
- Qt 6.5.3 (set `QT_HOME` environment variable)

### 2. Export Custom Recipes

```bash
# Export the openrvcore python-requires recipe
conan export openrvcore-conanfile.py

# Export custom Python recipe
conan export conan/recipes/python/all/conanfile.py --version 3.11.9 --user openrv

# Export custom PySide6 recipe
conan export conan/recipes/pyside6/all/conanfile.py --version 6.5.3 --user openrv

# Export custom FFmpeg recipe
conan export conan/recipes/ffmpeg/all/conanfile.py --version 6.1.1 --user openrv
```

### 3. Build with Conan

#### Linux (Rocky 8)
```bash
# Install dependencies
conan install conanfile.py --build=missing -pr:a ./conan/profiles/x86_64_rocky8 -of build/Release

# Configure CMake with package manager mode
cmake -B build -S . \
    -DCMAKE_TOOLCHAIN_FILE=build/Release/generators/conan_toolchain.cmake \
    -DRV_USE_PACKAGE_MANAGER=ON \
    -DRV_VFX_PLATFORM=CY2024

# Build
cmake --build build --target main_executable
```

#### macOS (Apple Silicon)
```bash
conan install conanfile.py --build=missing -pr:a ./conan/profiles/arm64_apple_release -of build/Release
cmake -B build -S . \
    -DCMAKE_TOOLCHAIN_FILE=build/Release/generators/conan_toolchain.cmake \
    -DRV_USE_PACKAGE_MANAGER=ON \
    -DRV_VFX_PLATFORM=CY2024
cmake --build build --target main_executable
```

#### Windows
```bash
conan install conanfile.py --build=missing -pr:a ./conan/profiles/x86_64_windows -of build/Release
cmake -B build -S . -G "Visual Studio 17 2022" ^
    -DCMAKE_TOOLCHAIN_FILE=build/Release/generators/conan_toolchain.cmake ^
    -DRV_USE_PACKAGE_MANAGER=ON ^
    -DRV_VFX_PLATFORM=CY2024
cmake --build build --config Release --target main_executable
```

### 4. Traditional Build (Without Conan)

The traditional build mode remains the default and works exactly as before:

```bash
cmake -B build -S . -DRV_VFX_PLATFORM=CY2024
cmake --build build
```

## Custom Recipes

### Python Recipe (`conan/recipes/python/`)
- VFX Reference Platform aligned (CY2023/CY2024)
- OpenSSL integration for SSL/TLS support
- Relocatable binaries with RPATH handling
- Custom sitecustomize.py for pip configuration

### FFmpeg Recipe (`conan/recipes/ffmpeg/`)
- Granular decoder/encoder control
- Disabled codecs for licensing compliance (Bink, VP9, DNxHD, ProRes, etc.)
- dav1d integration for AV1 support

### PySide6 Recipe (`conan/recipes/pyside6/`)
- Qt6 bindings for Python
- libclang integration
- VFX Platform version matching

## Profiles

Choose the appropriate profile for your platform:

| Platform | Profile |
|----------|---------|
| Linux x86_64 (Rocky 8) | `x86_64_rocky8` |
| macOS x86_64 | `x86_64_apple_release` |
| macOS ARM64 | `arm64_apple_release` |
| Windows x64 | `x86_64_windows` |

## Troubleshooting

### CMAKE_TOOLCHAIN_FILE not set
If you see a warning about `CMAKE_TOOLCHAIN_FILE` not being set:
```
cmake -B build -S . \
    -DCMAKE_TOOLCHAIN_FILE=<build_dir>/generators/conan_toolchain.cmake \
    -DRV_USE_PACKAGE_MANAGER=ON
```

### Package not found
Ensure you've run `conan install` and exported custom recipes before configuring:
```bash
conan export openrvcore-conanfile.py
conan install conanfile.py --build=missing -of build/Release
```

### Version mismatch
The Conan recipes should align with the VFX Reference Platform versions defined in `cmake/defaults/CYCOMMON.cmake` and `cmake/defaults/CY20XX.cmake`.

## Related Files

- `conanfile.py` - Main Conan recipe for OpenRV
- `openrvcore-conanfile.py` - Python-requires base class with common build logic
- `cmake/defaults/rv_options.cmake` - Contains `RV_USE_PACKAGE_MANAGER` option
- `cmake/macros/rv_create_std_deps_vars.cmake` - Helper macros for package staging
