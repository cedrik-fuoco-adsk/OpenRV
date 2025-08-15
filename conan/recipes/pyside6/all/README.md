# PySide6 Conan Recipe

A comprehensive Conan recipe for building PySide6 (Qt for Python) from source with complete functionality replicating the behavior of `make_pyside6.py` from the OpenRV build system.

## Features

This recipe provides a complete PySide6 build including:

- **Full PySide6 build from source** with all Qt6 bindings
- **Automatic libclang setup** for all platforms (Windows, macOS, Linux)
- **OpenSSL integration** for secure networking
- **Qt WebEngine support** for web content rendering
- **VFX Platform compatibility** (2023/2024)
- **Platform-specific optimizations** and patches
- **Comprehensive testing** with validation scripts

## Requirements

### System Requirements
- **Qt6** installation (6.5.3 recommended)
- **Python** (3.10 for VFX 2023, 3.11 for VFX 2024)
- **OpenSSL** (optional, for SSL support)
- **Ninja** build system (except Windows)

### Environment Variables
- `QT_HOME` or `RV_DEPS_QT6_LOCATION`: Path to Qt6 installation
- `PYTHONHOME`: Path to Python installation (if custom)

## Usage

### Basic Usage

```bash
# Install PySide6 for VFX Platform 2024 (Python 3.11)
conan create . --build=missing

# Install for VFX Platform 2023 (Python 3.10)
conan create . --build=missing -o vfx_platform=2023 -o python_version=3.10
```

### Advanced Options

```bash
# Build with SSL support disabled
conan create . --build=missing -o with_ssl=False

# Build debug version (Windows only)
conan create . --build=missing -s build_type=Debug

# Custom Qt location
export QT_HOME=/path/to/qt6.5.3
conan create . --build=missing
```

### Profile Example

```ini
[settings]
os=Linux
arch=x86_64
build_type=Release

[options]
pyside6:vfx_platform=2024
pyside6:python_version=3.11
pyside6:with_ssl=True

[buildenv]
QT_HOME=/opt/Qt/6.5.3/gcc_64
```

## Options

| Option | Values | Default | Description |
|--------|--------|---------|-------------|
| `shared` | [True, False] | True | Build shared libraries |
| `with_ssl` | [True, False] | True | Enable OpenSSL support |
| `python_version` | ["3.11", "3.10"] | "3.11" | Python version to use |
| `vfx_platform` | ["2024", "2023"] | "2024" | VFX Platform year |

## Build Process

The recipe performs the following steps:

1. **Environment Setup**: Configure build environment and dependencies
2. **Libclang Download**: Automatically download platform-specific libclang
3. **Source Preparation**: Download PySide6 source and apply patches
4. **Dependencies**: Install numpy and other Python build requirements
5. **Compilation**: Build PySide6 with all Qt6 bindings
6. **Post-Processing**: Clean up generators and broken shortcuts
7. **Packaging**: Package the complete Python installation with PySide6

### Platform-Specific Behavior

#### macOS
- Detects system clang version and downloads matching libclang
- Uses fallback versions for known clang releases
- Preserves native macOS packaging

#### Linux
- Uses Rocky Linux 8.8 compatible libclang
- Maintains symlinks and permissions
- GCC 10.3 compatible build

#### Windows
- Uses Visual Studio 2019 compatible libclang
- Handles debug/release library naming
- Copies OpenSSL DLLs to PySide6 directory

## Dependencies

The recipe automatically manages these dependencies:

- **Python** (custom OpenRV build with SSL support)
- **Qt6** (external installation required)
- **OpenSSL** (1.1.1u for VFX 2023, 3.5.2 for VFX 2024)
- **zlib** (1.3.1)
- **libclang** (automatically downloaded)
- **numpy** (1.26.3, required for build)

## Testing

The recipe includes comprehensive testing:

```bash
# Run package tests
conan create . --build=missing

# Run standalone test script
cd test_package
python test_package.py
```

Tests validate:
- Basic PySide6 imports and functionality
- Qt WebEngine availability
- SSL support and OpenSSL integration
- Certificate authority support (certifi)

## Integration with OpenRV

This recipe is designed to replace the PySide6 build logic from:
- `cmake/dependencies/python.cmake` 
- `src/build/make_pyside6.py`

### Migration from CMake Build

Replace the CMake PySide6 build with:

```cmake
# Remove old PySide6 build logic
# Add Conan dependency
conan_cmake_run(REQUIRES pyside6/6.5.3@openrv)
```

### Environment Integration

The packaged PySide6 sets up the environment:
- `PYTHONHOME`: Points to the Python installation
- `PYTHONPATH`: Includes PySide6 site-packages
- `PYSIDE6_ROOT`: Root of the PySide6 installation

## Troubleshooting

### Common Issues

1. **Qt6 not found**: Ensure `QT_HOME` environment variable points to Qt6 installation
2. **Libclang download fails**: Check internet connectivity; recipe will try fallback versions
3. **SSL errors**: Verify OpenSSL dependency is available
4. **Build timeout**: Increase system resources; PySide6 compilation is resource-intensive

### Debug Mode

Enable verbose output:
```bash
conan create . --build=missing -v
```

### Clean Build

Force complete rebuild:
```bash
conan create . --build=pyside6 --build=missing
```

## Contributing

This recipe follows Conan 2.0 best practices and OpenRV coding standards. When modifying:

1. Test on all supported platforms (Windows, macOS, Linux)
2. Verify VFX Platform compatibility (2023/2024)
3. Run the complete test suite
4. Update documentation for any new options or features

## License

This recipe is licensed under Apache 2.0, matching the OpenRV project license.
The PySide6 software itself is licensed under LGPL-3.0.