# build-manifest

## Purpose

Records a single auditable answer to the question "what is this build made of?", so
that support, release validation and licence review do not depend on reconstructing a
build's composition from logs.

## ADDED Requirements

### Requirement: A manifest is written for every configured build

Configuration SHALL write a build manifest into the build directory, without requiring
network access and without requiring the dependency store to be enabled.

#### Scenario: Manifest exists after configure

- **WHEN** configuration completes successfully
- **THEN** a manifest file exists in the build directory

#### Scenario: Manifest is written without the store

- **WHEN** the dependency store is disabled
- **THEN** the manifest is still written

### Requirement: Manifest content

The manifest SHALL record the computed build identity, the set of packages resolved
through the Conan path with their versions, and each prebuilt or derived artifact used
with the facts that were probed from it.

#### Scenario: Identity appears in the manifest

- **WHEN** the manifest is written
- **THEN** it contains every field of the computed build identity

#### Scenario: Conan package set appears in the manifest

- **WHEN** the manifest is written for a configuration that resolved packages through the Conan path
- **THEN** it lists those packages with their resolved versions and the identity of the Conan profile used

#### Scenario: Probed facts appear next to the artifact they describe

- **WHEN** an artifact has been probed
- **THEN** the manifest records that artifact's probed facts alongside a reference to the artifact

### Requirement: Manifest reference format

Artifacts referenced by the manifest SHALL be identified by a content-derived reference,
so that two builds referencing the same artifact are recognisable as such without
comparing host paths.

#### Scenario: Same artifact referenced identically from different locations

- **WHEN** two builds use the same artifact content obtained at different host paths
- **THEN** their manifests reference that artifact by the same content-derived reference

#### Scenario: Different content is referenced differently

- **WHEN** two artifacts differ in content
- **THEN** their content-derived references differ

### Requirement: Manifest writing does not fail a build

A failure to write or complete the manifest SHALL be reported as a warning and SHALL NOT
fail configuration or the build.

#### Scenario: Unwritable manifest location

- **WHEN** the manifest cannot be written
- **THEN** the build reports a warning and continues

### Requirement: Manifest is deterministic for the same inputs

For the same identity and the same resolved artifacts, the manifest content SHALL be
identical across repeated configurations, excluding fields documented as
non-deterministic such as timestamps and host-specific paths.

#### Scenario: Repeated configuration produces an identical manifest

- **WHEN** the same configuration is generated twice on the same machine with no artifacts changed
- **THEN** the two manifests are identical after excluding documented non-deterministic fields

### Requirement: Manifest does not embed credentials

The manifest SHALL NOT contain credentials, access tokens, or Conan remote
authentication values.

#### Scenario: Authenticated remote does not leak into the manifest

- **WHEN** packages are resolved from an authenticated remote
- **THEN** the manifest records the remote name but no credential material
