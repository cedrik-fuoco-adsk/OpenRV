# dependency-abi-probe

## Purpose

Determines what binary compatibility an artifact actually provides by reading the
artifact itself, so that decisions about substituting a prebuilt artifact rest on
measured facts rather than on version numbers or declarations.

## ADDED Requirements

### Requirement: Facts are read from the artifact

The probe SHALL derive its facts by reading the artifact's own contents, and SHALL NOT
rely on a declaration supplied by the user, on a name or path convention, or on an
external registry of known-good artifacts.

#### Scenario: Two artifacts with the same version but different builds are distinguished

- **WHEN** two artifacts of the same package version are probed, having been produced by different toolchains or with different build configuration
- **THEN** the probe reports facts that distinguish them

#### Scenario: No declaration is consulted

- **WHEN** an artifact is probed
- **THEN** the reported facts are unchanged whether or not any provenance declaration was supplied for it

### Requirement: Probed fact set

The probe SHALL report, at minimum: the artifact's version, its linkage configuration
(shared or static, and release or debug), the feature set the artifact was built with,
and the symbol-level ABI demands the artifact places on its runtime environment.

#### Scenario: All fact categories are reported

- **WHEN** an artifact is probed successfully
- **THEN** the result contains a version, a linkage configuration, a feature set and a set of ABI demands

#### Scenario: Missing facts are reported as unknown, not omitted

- **WHEN** a fact category cannot be determined for an artifact
- **THEN** the result records that category as unknown rather than silently omitting it

### Requirement: Input and derived artifacts are probed separately

When an artifact is produced by adapting an input artifact, the probe SHALL record the
input's facts and the derived artifact's facts as separate results, so that the
adaptation step cannot silently change what is provided.

#### Scenario: Both probe results are retained

- **WHEN** a derived artifact is produced from an input artifact
- **THEN** the recorded facts include both the input probe result and the derived probe result

#### Scenario: Adaptation changing a fact is visible

- **WHEN** an adaptation step changes a probed fact, such as a linkage configuration
- **THEN** the difference between the input result and the derived result is visible in the recorded facts

### Requirement: Substitution legality is a provision-versus-requirement comparison

A substitution SHALL be treated as legal only when every fact the consumer requires is
provided by the artifact, and SHALL be treated as illegal otherwise. Requirement facts
and provision facts SHALL be compared as sets rather than as equal version strings.

#### Scenario: Provision satisfies requirement

- **WHEN** an artifact provides every fact that the consumer requires
- **THEN** the substitution is accepted

#### Scenario: Provision is a strict superset

- **WHEN** an artifact provides facts beyond those the consumer requires, and no required fact is missing
- **THEN** the substitution is accepted

#### Scenario: Provision is missing a required fact

- **WHEN** an artifact lacks at least one fact that the consumer requires
- **THEN** the substitution is rejected

### Requirement: Demands are ceilings and artifact versions are floors

A demand the artifact places on its runtime environment SHALL be evaluated as a ceiling: the
substitution is legal only when the artifact does not demand more than that environment
provides, and an artifact that demands less SHALL be accepted. The artifact's own version SHALL
be evaluated as a floor: it SHALL be accepted only when it is at least the required version.

#### Scenario: A demand below what is available is accepted

- **WHEN** an artifact demands GLIBCXX 3.4.20 and the environment provides GLIBCXX 3.4.29
- **THEN** the requirement is satisfied

#### Scenario: A demand equal to what is available is accepted

- **WHEN** an artifact demands GLIBCXX 3.4.20 and the environment provides GLIBCXX 3.4.20
- **THEN** the requirement is satisfied

#### Scenario: A demand above what is available is rejected

- **WHEN** an artifact demands GLIBCXX 3.4.29 and the environment provides GLIBCXX 3.4.20
- **THEN** the requirement is not satisfied

#### Scenario: A platform floor newer than the target is rejected

- **WHEN** an artifact declares a minimum platform of 11.0 and the target platform is 10.9
- **THEN** the requirement is not satisfied

#### Scenario: A platform floor older than the target is accepted

- **WHEN** an artifact declares a minimum platform of 11.0 and the target platform is 14.0
- **THEN** the requirement is satisfied

#### Scenario: An artifact version below the requirement is rejected

- **WHEN** an artifact's version is 1.0.0 and the requirement is at least 2.0.0
- **THEN** the requirement is not satisfied

### Requirement: A demand is recorded as a namespace and a version

Where a platform states a demand as a single string carrying both a namespace and a version, the
probe SHALL record the namespace and the version separately, and SHALL NOT record a value as a
version when its meaning is not an ABI version at all.

#### Scenario: An ELF version name is split into its parts

- **WHEN** a version-needs row names `GLIBCXX_3.4.29`
- **THEN** the recorded demand is namespace `GLIBCXX` with version `3.4.29`

#### Scenario: A table index is not mistaken for a version

- **WHEN** a version-needs row also carries a trailing table index
- **THEN** that index does not appear as the demand's version

#### Scenario: A demand with no version still satisfies a namespace requirement

- **WHEN** an artifact demands a namespace without a version, and a requirement names only that namespace
- **THEN** the requirement is satisfied on the namespace alone

### Requirement: Rejection produces an actionable diagnostic

When a substitution is rejected, the build SHALL report which requirement was not
satisfied, what the artifact provided instead, and which artifact was inspected.

#### Scenario: Mismatch names the requirement and the provision

- **WHEN** a substitution is rejected
- **THEN** the report names the unsatisfied requirement, the value the artifact provided for it, and the artifact's location

#### Scenario: Mismatch is detected before linking

- **WHEN** an incompatible artifact is about to be used
- **THEN** the rejection is reported at the point the artifact is evaluated, rather than surfacing later as a link or load failure

### Requirement: Probe results are cached by artifact content

Probing SHALL be performed at most once per distinct artifact content, with results
reused for subsequent configurations that reference the same content.

#### Scenario: Repeated configuration does not re-probe

- **WHEN** a configuration is generated twice against the same unmodified artifact
- **THEN** the artifact is inspected only once and the second configuration uses the cached result

#### Scenario: Modified artifact is re-probed

- **WHEN** an artifact's content changes
- **THEN** it is probed again rather than served from the cache

### Requirement: Probing does not modify the artifact

The probe SHALL treat artifacts as read-only and SHALL NOT alter, relocate or re-sign
the artifact it inspects.

#### Scenario: Artifact is unchanged after probing

- **WHEN** an artifact is probed
- **THEN** its content is byte-identical to its content before probing

### Requirement: Probing is not required for a default build

The probe SHALL be restricted to the paths that consume prebuilt or derived artifacts.
A default build SHALL NOT fail, and SHALL NOT be slowed by a mandatory probe, when no
such artifact is involved.

#### Scenario: Default build without inspection tools

- **WHEN** a default build runs on a machine where binary inspection tools are absent
- **THEN** configuration and build succeed

#### Scenario: Store path without inspection tools

- **WHEN** the store path is enabled on a machine where binary inspection tools are absent
- **THEN** configuration fails with a message naming the missing tool rather than silently skipping verification

### Requirement: Static probing limitations are explicit

The build SHALL document that static probing cannot detect incompatibilities that leave
every symbol and feature unchanged while altering a binary layout, and SHALL designate a
functional validation — loading the binding and exercising an object shared with the
application — as the check for that class of incompatibility.

#### Scenario: Limitation is documented

- **WHEN** a developer reads the probe documentation
- **THEN** the class of incompatibility that static probing cannot detect is stated, together with the functional check that covers it

#### Scenario: Functional check is not claimed as a substitute

- **WHEN** the functional validation passes for an artifact
- **THEN** no guarantee is claimed for artifacts of the same version and toolchain that were not themselves functionally validated
