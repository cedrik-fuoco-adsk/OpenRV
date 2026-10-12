# build-identity

## Purpose

Establishes one authoritative description of the platform a build targets, so that every
dependency resolution path agrees on what is compatible with what instead of each
deriving its own answer.

## ADDED Requirements

### Requirement: Identity is computed once per configuration

The build SHALL compute the platform identity a single time during configuration and
SHALL expose that one result to every consumer, including the CMake dependency
resolution path and the Conan profile generation path.

#### Scenario: Both resolution paths read the same identity

- **WHEN** a configuration is generated with the Conan path enabled
- **THEN** the identity values used for CMake dependency resolution and the values written into the Conan profile originate from the same computed record

#### Scenario: A consumer does not re-derive an identity fact

- **WHEN** a dependency resolution path needs a fact such as the compiler version or the C++ standard
- **THEN** it reads that fact from the computed identity rather than detecting it independently

### Requirement: Identity content

The identity SHALL record at minimum: the VFX platform year, the target operating system
and architecture, the toolchain (compiler identifier, compiler version, standard library,
C++ standard), the build configuration, the Python ABI series, and the Qt version.

#### Scenario: Identity is complete

- **WHEN** the identity is computed for a supported platform
- **THEN** it contains a value for every field listed above, with no field left unset

#### Scenario: Unsupported platform is reported

- **WHEN** the identity is requested for a platform the build does not support
- **THEN** configuration fails with a message naming the unsupported platform

### Requirement: Build configuration is part of identity

Release and Debug configurations SHALL produce distinct identities, because the build
configuration changes ABI-relevant compilation such as `NDEBUG` and selects the default
C runtime on Windows.

#### Scenario: Release and Debug do not share an identity

- **WHEN** the same platform is configured once as Release and once as Debug
- **THEN** the two identities differ

### Requirement: The C runtime is part of identity where it is a separate axis

On Windows the identity SHALL record the C runtime library that artifacts link against,
distinguishing a dynamic runtime from a static one and a debug runtime from a release
one, because the runtime is selected independently of the build configuration name. On a
platform where the C runtime is not a separate ABI axis the field SHALL be absent rather
than set to a placeholder.

#### Scenario: A runtime change alone changes identity

- **WHEN** two Windows configurations are otherwise identical and link different C runtimes
- **THEN** their identities differ

#### Scenario: A configuration name does not imply a runtime

- **WHEN** a Windows configuration links a C runtime that its build configuration name does not imply
- **THEN** the identity records the runtime that is linked, not the one the name implies

#### Scenario: The field is absent where it does not apply

- **WHEN** a configuration targets a platform with no separate C runtime axis
- **THEN** the identity carries no C runtime field

### Requirement: Python identity is ABI-granular

The identity SHALL record the Python ABI series rather than the exact patch release,
because the Python C application binary interface is stable within a series.

#### Scenario: A patch difference does not change identity

- **WHEN** two configurations differ only in the Python patch release within the same ABI series
- **THEN** their identities are equal

#### Scenario: A series difference changes identity

- **WHEN** two configurations differ in the Python ABI series
- **THEN** their identities differ

### Requirement: Identity is reported to the user

Configuration SHALL report the computed identity in human-readable form, so that a
developer can see what the build believes it is building against without inspecting
internal state.

#### Scenario: Configure reports the identity

- **WHEN** configuration completes successfully
- **THEN** the reported output includes the computed identity values

### Requirement: Identity computation does not change build behaviour

Computing, reporting and recording the identity SHALL NOT alter dependency resolution
outcomes, output paths, staged layout, or any other observable result of a default
build.

#### Scenario: Default build is unaffected

- **WHEN** a build is configured on a platform where the identity computation reports no mismatch
- **THEN** the build directory layout, dependency install locations and staged output are the same as they would be without the identity computation

### Requirement: Identity computation requires no external tool

Computing and reporting the identity SHALL NOT require any external inspection tool to
be present, so that a default build works on a machine with only the existing toolchain
prerequisites installed.

#### Scenario: Configure without inspection tools

- **WHEN** configuration runs on a machine where binary inspection tools are not installed
- **THEN** identity computation and reporting still succeed
