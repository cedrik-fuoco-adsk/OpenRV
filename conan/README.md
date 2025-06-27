
# Export openrvcore recipe to Conan cache
conan export openrvcore-conanfile.py

# Create a FFmpeg 6.1.1 package
conan create conan/recipes/ffmpeg/all/conanfile.py --version 6.1.1 --user openrv --build=missing

# Build OpenRV
conan install conanfile.py --build=missing -pr:a ./conan/profiles/x86_64_rocky8
conan build conanfile.py --build=missing -pr:a ./conan/profiles/x86_64_rocky8