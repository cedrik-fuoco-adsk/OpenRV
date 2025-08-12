# Python Conan Recipe for OpenRV

This Conan 2 recipe builds a custom Python distribution optimized for OpenRV with SSL certificate handling, relocatable binaries, and all required dependencies.

## Features

- **VFX Platform Support**: Supports both CY2023 (Python 3.10.13) and CY2024 (Python 3.11.9)
- **SSL Certificate Handling**: Includes automatic SSL certificate configuration via sitecustomize.py
- **Relocatable Binaries**: Uses proper RPATH settings for relocatable installations
- **OpenTimelineIO Integration**: Includes OpenTimelineIO from the main GitHub branch
- **Complete Package Set**: Includes all Python packages required by OpenRV

## Options

| Option | Values | Default | Description |
|--------|--------|---------|-------------|
| `vfx_platform` | `"2023"`, `"2024"` | `"2024"` | VFX Platform year (determines Python version) |
| `shared` | `True`, `False` | `True` | Build shared libraries (always True for OpenRV) |
| `optimizations` | `True`, `False` | `True` | Enable Python optimizations (Release builds only) |
| `with_tkinter` | `True`, `False` | `True` | Include Tkinter support |
| `with_ssl` | `True`, `False` | `True` | Include SSL support via OpenSSL |

## Requirements

- **OpenSSL**: Required when `with_ssl=True`
- **System Dependencies**: Automatically installed via system package manager

### macOS Dependencies (via Homebrew)
- readline
- tcl-tk@8  
- python-tk
- xz

### Windows Dependencies
- Visual Studio Build Tools 2019 or later
- Windows SDK
- MSBuild (included with Visual Studio)
- Optional: vcpkg for additional libraries
- build-essential
- zlib1g-dev
- libncurses5-dev
- libgdbm-dev
- libnss3-dev
- libssl-dev
- libreadline-dev
- libffi-dev
- libsqlite3-dev
- libbz2-dev
- uuid-dev
- tk-dev

## Usage

### Basic Usage

```bash
# Create a conanfile.txt or conanfile.py with:
[requires]
python/3.11.9@

[options]
python:vfx_platform=2024
python:with_ssl=True

# Install the package
conan install . --build=missing
```

### In a conanfile.py

```python
from conan import ConanFile

class MyProject(ConanFile):
    requires = "python/3.11.9"
    
    def configure(self):
        self.options["python"].vfx_platform = "2024"
        self.options["python"].with_ssl = True
```

### CMake Integration

The recipe provides a `Python::Python` target for CMake:

```cmake
find_package(Python REQUIRED)
target_link_libraries(my_target Python::Python)

# Python executable is available as:
# ${PYTHON_EXECUTABLE}
```

## Package Contents

The built package includes:

### Python Packages
- pip, setuptools, wheel
- certifi (for SSL certificates)
- six, packaging, requests
- cryptography
- PyOpenGL, PyOpenGL_accelerate (platform dependent)
- OpenTimelineIO (from GitHub main branch)

### Special Features
- **sitecustomize.py**: Automatically sets SSL_CERT_FILE and reorders Python path
- **Relocatable binaries**: Uses @rpath on macOS and $ORIGIN on Linux
- **SSL integration**: OpenSSL libraries are copied and properly linked
- **Windows Debug Support**: Special handling for OpenTimelineIO in Debug builds
- **Windows Patches**: Includes patches for OpenSSL integration on Windows

## Building from Source

```bash
# Clone or copy the recipe
conan create . --build=missing

# For specific VFX platform
conan create . -o vfx_platform=2023 --build=missing

# For debug builds (includes special OpenTimelineIO handling on Windows)
conan create . -s build_type=Debug --build=missing

# For Windows with specific profile
conan create . --profile=profiles/openrv-windows --build=missing
```

## Platform Support

| Platform | Status | Notes |
|----------|--------|-------|
| macOS | ✅ Supported | Uses Homebrew for dependencies |
| Linux | ✅ Supported | Uses apt for dependencies |
| Windows | ✅ Supported | Uses MSBuild with PCBuild, includes OpenTimelineIO debug build support |

## Integration with OpenRV Build System

This recipe is designed to replace the existing `python3.cmake` and `make_python.py` build system. To integrate:

1. Replace Python dependency in CMake with Conan:
   ```cmake
   find_package(Python REQUIRED)
   # Use Python::Python target instead of manual Python setup
   ```

2. Update build scripts to use Conan:
   ```bash
   conan install . --build=missing
   # Python is now available via Conan
   ```

## Compatibility

This recipe maintains compatibility with the existing OpenRV Python build by:
- Using identical Python versions for each VFX platform
- Installing the same set of Python packages  
- Applying the same RPATH and SSL certificate configurations
- Providing the same sitecustomize.py behavior

## Testing

Run the test package to verify the recipe:

```bash
python test_package.py
```

This validates:
- Recipe instantiation and configuration
- Version handling for different VFX platforms
- Helper method functionality
- Package content verification

## Troubleshooting

### SSL Certificate Issues
If you encounter SSL certificate errors, ensure:
- OpenSSL is properly built and linked
- `DO_NOT_SET_SSL_CERT_FILE` environment variable is not set
- certifi package is installed and accessible

### RPATH Issues
If libraries are not found at runtime:
- Verify RPATH settings in the built binaries
- Check that OpenSSL libraries are copied correctly
- Ensure the appropriate environment variables are set

### Missing Dependencies
If system dependencies are missing:
- Check that system package manager can install required packages
- Verify Homebrew is available and working on macOS
- Ensure you have appropriate permissions for package installation

## License

This recipe is licensed under Apache-2.0, same as the OpenRV project.
