# dependency-store

## Purpose

Provides an opt-in, identity-addressed location for CMake-built dependencies, so that
dependency builds are reused across configurations, clones and worktrees instead of
being repeated inside each build directory.

## ADDED Requirements

### Requirement: The store is opt-in and disabled by default

When no store location is configured, the build SHALL place dependencies in the build
directory as it does today, and SHALL NOT read from or write to any store.

#### Scenario: Default configuration uses the build directory

- **WHEN** a build is configured without a store location
- **THEN** dependency source, build and install trees are located inside the build directory

#### Scenario: Default configuration creates no store

- **WHEN** a build is configured without a store location
- **THEN** no store directory is created and no store location is consulted

### Requirement: Store placement is derived from the build identity

When a store location is configured, each dependency SHALL be placed at a path derived
from the build identity, so that artifacts produced under one identity are never served
to a build targeting another.

#### Scenario: Distinct identities are placed apart

- **WHEN** two configurations with different identities share a store location
- **THEN** their dependencies are placed at different paths and neither reads the other's artifacts

#### Scenario: Equal identities share artifacts

- **WHEN** two configurations with equal identities share a store location
- **THEN** the second configuration reuses the first configuration's dependency artifacts without rebuilding them

### Requirement: Opting out is a complete opt-out

Reconfiguring an existing build tree with the store location removed SHALL return that
tree to the in-build-directory dependency layout, and SHALL NOT continue to use a
previously configured store location.

#### Scenario: Reconfigure returns to the build directory

- **WHEN** a tree configured with a store location is reconfigured with that location removed
- **THEN** dependencies resolve to the build directory layout

#### Scenario: A cached location does not persist

- **WHEN** a store location is removed after having been used in an existing build tree
- **THEN** no dependency is resolved from the removed location

### Requirement: Store eligibility is decided per dependency

A dependency SHALL be served from the store only after it has passed the relocation
check. Dependencies that have not passed the check SHALL continue to be built in the
build directory, even when a store location is configured.

#### Scenario: Eligible dependency is stored

- **WHEN** a dependency has passed the relocation check and a store location is configured
- **THEN** that dependency is built into the store and reused from it on subsequent configurations

#### Scenario: Ineligible dependency stays local

- **WHEN** a dependency has not passed the relocation check and a store location is configured
- **THEN** that dependency is built inside the build directory as before

#### Scenario: Partial rollout is supported

- **WHEN** some dependencies have passed the relocation check and others have not
- **THEN** the build succeeds, with each dependency resolved from the location its eligibility permits

### Requirement: The relocation check proves an installed tree is position independent

The relocation check SHALL install the dependency in one location, relocate its
installed tree to a different location, link a consumer against the relocated tree, and
execute that consumer successfully.

#### Scenario: Relocatable dependency passes

- **WHEN** a dependency's installed tree is relocated and a consumer linked against it runs successfully
- **THEN** the dependency is marked eligible for the store

#### Scenario: Dependency with a baked-in absolute reference fails

- **WHEN** a dependency's installed tree embeds an absolute reference to its original location such that a consumer fails after relocation
- **THEN** the dependency is not marked eligible and is reported as ineligible

#### Scenario: Linking against a stale location is not accepted

- **WHEN** a consumer links and runs but resolves a library or data file from the original, now removed, location
- **THEN** the check does not treat the dependency as relocatable

### Requirement: Store contents survive clean operations

Removing a build configuration SHALL NOT remove store contents.

#### Scenario: Clean leaves the store intact

- **WHEN** a build configuration that used the store is removed
- **THEN** the store remains and a subsequent configuration reuses its artifacts

### Requirement: The store is relocatable

Installed artifacts within the store SHALL resolve their runtime library and data
references relative to the artifact's own location, so that relocating the store itself
does not break them.

#### Scenario: Store moved between host paths

- **WHEN** a populated store is moved to a different host path and a build is configured against the new path
- **THEN** dependencies resolve and the build links and runs without rebuilding them

### Requirement: Concurrent use of a shared store is safe

Two configurations using the same store location concurrently SHALL NOT corrupt shared
artifacts or observe partially written ones.

#### Scenario: Concurrent configurations do not corrupt the store

- **WHEN** two configurations build the same dependency into the same store location concurrently
- **THEN** the store is left in a consistent state and both configurations complete successfully

#### Scenario: A partially populated location is not consumed

- **WHEN** a configuration observes a store location for a dependency that another configuration is still producing
- **THEN** it waits for completion or produces the dependency itself, and does not consume an incomplete artifact

### Requirement: A store is never required

Every dependency the build manages SHALL remain buildable without a store location, so
that building entirely from source remains a supported configuration for every supported
platform.

#### Scenario: Full from-source build remains available

- **WHEN** a build is configured with no store location on any supported platform
- **THEN** all dependencies are built from source and the build succeeds

#### Scenario: Store-disabled configuration is tested

- **WHEN** continuous integration runs its build matrix
- **THEN** at least one configuration per platform runs with the store disabled

### Requirement: Store membership is invisible to the packaged output

A dependency served from the store SHALL pass through the same install-time and
staging-time path normalization as the same dependency built inside the build directory,
so that the packaged output does not reference the store location.

#### Scenario: Staged output does not reference the store

- **WHEN** a dependency is served from the store and the build is installed
- **THEN** the staged and installed artifacts contain no reference to the store location

#### Scenario: Store-sourced and locally built dependencies stage equivalently

- **WHEN** the same dependency is built inside the build directory in one build and served from the store in another build of equal identity
- **THEN** the resulting staged artifacts are equivalent

### Requirement: Packaged output is relocatable

The packaged output SHALL run from an installation prefix that differs from the build
directory, so that a build produced on one machine runs on any machine of the same
platform regardless of whether the store was used.

#### Scenario: Installed output runs from a different prefix

- **WHEN** the build is installed to a prefix different from the build directory and executed from that prefix
- **THEN** it runs without requiring the build directory or any store location to be present

#### Scenario: Relocatability holds for a store-enabled build

- **WHEN** a build that used the store is packaged and installed to a different prefix
- **THEN** it runs under the same guarantee as a build that did not use the store
