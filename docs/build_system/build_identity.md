# Build identity

Every configure computes a **build identity**: a single machine-readable description of
the platform the build targets. It exists because the same ABI facts used to be derived
in two places — a Conan profile states `compiler.version=11` by hand, while the CMake
path trusts whatever compiler is on the machine — and the two could disagree silently.
The identity is computed once and both paths read it.

This is read-only. Computing, reporting and recording the identity reroutes nothing: no
dependency path changes, no dependency is resolved differently, and no external tool is
required.

## Where it comes from

`src/build/build_identity.py` is the single implementation of the normalization and
hashing rules. It is invoked by:

- `cmake/macros/rv_build_identity.cmake`, from the CMake configure path
- `openrvcore-conanfile.py`, from the Conan `generate` step

Both invoke the same script with the same field names, so the two cannot drift into
disagreeing about what a compiler version or a build type is called.

## The fields

| Field | Example | Notes |
| ----- | ------- | ----- |
| `vfx_platform` | `CY2025` | From `RV_VFX_PLATFORM` |
| `target_os` | `linux` | `linux`, `macos` or `windows` |
| `target_arch` | `x86_64` | `x86_64` or `arm64` |
| `compiler_id` | `gcc` | `gcc`, `clang`, `apple-clang` or `msvc` |
| `compiler_version` | `11.2.1` | Full version. A Conan profile usually carries only the major, so comparisons use the major; for MSVC that is the toolset series, so `19.44.35229.0` compares equal to a profile's `194` |
| `stdlib` | `libstdc++11` | `libstdc++11`, `libc++` or `msvc` |
| `cxx_standard` | `17` | Derived from `RV_VFX_PLATFORM` |
| `build_config` | `Release` | `Release` or `Debug`, from `CMAKE_BUILD_TYPE` — also with Visual Studio and Xcode, because RV builds its dependencies with `--config ${CMAKE_BUILD_TYPE}` |
| `crt` | `dynamic` | **Windows only.** `dynamic` or `static`, each optionally `-debug`. Absent elsewhere |
| `python_abi` | `3.11` | **The ABI series, not the patch release** — see below |
| `qt_version` | `6.5.3` | The Qt version `RV_VFX_PLATFORM` specifies — see below |
| `fields_version` | `2` | Bumped when the normalization rules change |
| `hash` | `sha256:…` | Over the canonical form of the fields above |

### Python is recorded at ABI-series granularity

The CPython C application binary interface is stable within a series, so `3.11.9` and
`3.11.14` produce **the same identity**. That is deliberate: it is what allows an
artifact built against one 3.11 patch release to be reused for another.

### Release and Debug are different identities

`NDEBUG`, and on Windows the C runtime, change what an artifact's binary interface
actually is. Release and Debug therefore never share an identity, and never share a
store slot once the dependency store exists.

### The C runtime is recorded, not inferred from the configuration

On Windows the configuration name does **not** determine which C runtime is linked.
`CMAKE_MSVC_RUNTIME_LIBRARY` chooses `/MD` or `/MT` independently of it, so a Release
build against the static runtime and one against the dynamic runtime are different
builds that a configuration name alone describes identically. `crt` therefore records
what the build actually links:

```
crt = dynamic       # /MD   — the default
crt = dynamic-debug # /MDd  — the default for a Debug configuration
crt = static        # /MT
crt = static-debug  # /MTd
```

On Linux and macOS there is no such axis — the C++ standard library is already carried
by `stdlib` and the C library is part of the platform — so the field is **absent**
rather than set to a placeholder, because a placeholder would read as a fact.

A Conan profile expresses this as two settings, `compiler.runtime` and
`compiler.runtime_type`. An unset `runtime_type` follows `build_type` — Conan's default
profile plugin fills it in that way, and the `generate` step applies the same rule for a
plugin that does not — so the profiles need not state it for the runtime to be compared.
A profile with no `compiler.runtime` states no C runtime at all.

### The Qt version is the configured one

The identity is computed before any dependency is configured, because a store location
is derived from it. At that point the Qt that will be found is not yet known, so
`qt_version` is the version `RV_VFX_PLATFORM` specifies. When `QT_HOME` points at a
different Qt, configuration warns once Qt has been found, naming both versions, and the
build manifest records the found one under `found.qt_version` beside the identity.

## Reading it

Configuration prints every field:

```
-- Build identity (sha256:5e1bde81…):
--     vfx_platform: CY2025
--     target_os: linux
--     target_arch: x86_64
--     compiler_id: gcc
--     compiler_version: 11.2.1
--     stdlib: libstdc++11
--     cxx_standard: 17
--     build_config: Release
--     python_abi: 3.11
--     qt_version: 6.5.3
```

On Windows the field list additionally carries `crt`, which is absent everywhere else.

The canonical document is written to `<build-dir>/build-identity.json`, and the raw
inputs it was computed from to `<build-dir>/build-identity.inputs`.

## Checking a Conan profile against it

When the Conan path is used, its `generate` step writes the profile's own view of the
platform to `<build-dir>/conan-identity.json` and hands the path to CMake. CMake then
compares the two and reports every field that disagrees. On a re-install into a build
folder that has already been configured, the `generate` step makes the same comparison
itself, against the `build-identity.json` that configure left there, before any package
is built:

```
-- Build identity: the Conan profile disagrees with the computed identity (reported, not enforced):
build identity mismatch on 2 of 7 compared fields:
  compiler_version: computed=11.2.1  conan-profile=13
  cxx_standard: computed=17  conan-profile=20
```

A Conan profile cannot know the Python ABI series or the Qt version, so those fields are
omitted from the profile's document and are not compared. The profile's document is
marked `"partial": true` to make that explicit rather than looking like missing data.

**This is reported, not enforced.** A mismatch warns and the build continues. Making it
a gate is left for later.

To compare by hand:

```bash
python3 src/build/build_identity.py emit --inputs <raw-inputs> --out /tmp/identity.json
python3 src/build/build_identity.py compare \
    --left /tmp/identity.json --right <build-dir>/conan-identity.json
```

`--version-granularity exact` compares compiler versions exactly rather than by major;
with it, a profile that carries only `11` against a compiler that reports `11.2.1`
reports a difference that does not exist.

## Turning it off

```bash
cmake -B _build -DRV_BUILD_IDENTITY=OFF …
```

With it off, no identity is computed, nothing is reported, and no identity document is
written; one left by an earlier configure is removed, so it cannot be mistaken for this
configure's. The build otherwise behaves as it would without the identity: no dependency
path depends on it unless a store is configured.

Configuration fails with a message naming the platform if an identity is requested for a
target the build does not support. Set `-DRV_BUILD_IDENTITY=OFF` to configure on such a
platform without one. That is the only identity failure that stops a configure: a missing
interpreter, or an input that cannot be normalized, warns and the build continues without
an identity.

## The Python interpreter

The identity, the probe and the manifest run under `RV_BUILD_PYTHON`. When it is not set,
the first interpreter on `PATH` that actually runs as Python 3 is used, trying `python3`
then `python` in each directory. On Windows this skips the WindowsApps aliases, which are
stubs that open the Store, and finds a python.org install that provides only
`python.exe`. An interpreter given explicitly is validated but never replaced.

## Tests

```bash
python3 src/build/test_build_identity.py
```

The CMake-side resolution of the runtime into the `crt` field is CMake string logic, so
the Python checks cannot reach it and it is checked separately, on every platform rather
than only on Windows:

```bash
cmake -P cmake/macros/test_rv_build_identity_crt.cmake
```
