# Tasks — build identity and shared dependency store

## 1. Identity computation (phase 0)

- [x] 1.1 Add the identity and store options to `cmake/defaults/rv_options.cmake`, defaulting to today's behaviour, and verify a default configure produces no change in dependency paths by diffing the generated cache against a pre-change baseline
- [x] 1.2 Implement identity computation producing the full tuple (VFX platform, target OS and architecture, compiler identifier and version, standard library, C++ standard, build configuration, Python ABI series, Qt version), and verify the tuple is recorded in the build directory
- [x] 1.3 Record the Python ABI series rather than the exact patch release, and verify two configurations differing only in Python patch level produce equal identities
- [x] 1.4 Report the computed identity in configure output, and verify the report names every field of the tuple
- [x] 1.5 Fail configuration with a message naming the platform when identity is requested for an unsupported target, and verify the failure message
- [x] 1.6 Record the C runtime library on Windows, where it is selected independently of the build configuration name, and verify a runtime change alone produces a different identity

## 2. Identity as the single shared input (phase 0)

- [x] 2.1 Emit the computed identity to a machine-readable file in the build directory, and verify the file is present and parseable after configure
- [x] 2.2 Make the Conan `generate` step read the emitted identity and report a mismatch against the profile's compiler, standard library, C++ standard and build type, and verify a deliberately mismatched profile produces the mismatch report
- [x] 2.3 Verify that with a matching profile the Conan path produces identical generated files to the pre-change baseline

## 3. Artifact probing (phase 0 / opt-in path)

- [x] 3.1 Implement probing of version, linkage configuration, feature set and ABI demands for Linux, macOS and Windows, and verify each fact category is populated for a known shared library on each platform
- [x] 3.2 Record undeterminable fact categories as explicitly unknown rather than omitting them, and verify a synthetic artifact with a stripped metadata section produces unknown rather than an error
- [x] 3.3 Support separate probe results for an ingested input artifact and a derived artifact, and verify both results are retained when a derived artifact is produced
- [x] 3.4 Implement the provision-versus-requirement comparison and verify it accepts an exact match, accepts a strict superset, and rejects a missing requirement
- [x] 3.5 Implement the rejection diagnostic naming the unsatisfied requirement, the provided value and the artifact location, and verify the message content on a rejected substitution
- [x] 3.6 Cache probe results keyed by artifact content, and verify a second configure against an unchanged artifact performs no inspection while a modified artifact is re-probed
- [x] 3.7 Verify probed artifacts are byte-identical before and after probing
- [x] 3.8 Verify a default configure and build succeed on a machine without binary inspection tools, and that the store path fails with a message naming the missing tool instead

## 4. Build manifest (phase 0)

- [x] 4.1 Write a manifest into the build directory at configure time, and verify it exists after configure with the store disabled
- [x] 4.2 Include the full identity, the resolved Conan package set with the profile identity, and content-derived references for probed artifacts, and verify each section is present
- [x] 4.3 Verify two artifacts with identical content referenced from different host paths produce the same content-derived reference, and that differing content produces differing references
- [x] 4.4 Verify manifest content is identical across two configurations with unchanged inputs, excluding documented non-deterministic fields
- [x] 4.5 Verify a manifest write failure produces a warning and the build continues
- [x] 4.6 Verify the manifest contains no credential material when packages are resolved from an authenticated remote

## 5. Store foundation (phase 1)

- [x] 5.1 Add `RV_DEPS_STORE` and place the installed trees of eligible dependencies at an identity-derived path when it is set, re-derived with `FORCE` on every configure, with dependency source, build and stamp trees staying local, and verify an explicit install root still wins
- [x] 5.2 Derive the store path from the build identity and verify two configurations with different identities sharing one store location place dependencies at different paths
- [x] 5.3 Consume a store entry through the find-first path so the dependency is found rather than built, and verify a dependency with no published entry is still built
- [x] 5.4 Publish store entries atomically by producing in a private location and moving into place, and verify an interrupted publish leaves no consumable partial entry
- [x] 5.5 Verify two concurrent configurations building the same dependency into one store location both complete and leave the store consistent
- [x] 5.6 Verify removing a build configuration leaves the store intact and that the next configuration reuses its artifacts

## 6. Opt-out guarantees (phase 1)

- [ ] 6.1 Verify that reconfiguring a tree that used a store, with the store location removed, resolves dependencies back to the build-directory layout
- [ ] 6.2 Verify that after removing the store location no dependency is resolved from the removed path, including in a tree reused from a prior configure
- [ ] 6.3 Verify a default configure with no store location creates no store directory and consults no store location

## 7. Relocation check and first eligible dependency (phase 1)

- [ ] 7.1 Implement the relocation check: install a dependency in one location, relocate the installed tree, link a consumer against the relocated tree, and run it, and verify the check passes for a known relocatable dependency
- [ ] 7.2 Verify the check fails for a dependency whose installed tree embeds an absolute reference to its original location
- [ ] 7.3 Verify the check does not accept a consumer that resolves a library or data file from the original, removed location
- [x] 7.4 Run the relocation check for one dependency and mark it store-eligible, and verify it is built into the store and reused from a separate build directory with the same identity
- [ ] 7.5 Verify a dependency whose relocation check fails remains built inside the build directory while other eligible dependencies are still served from the store

## 8. Dependency rollout (phase 1)

- [ ] 8.1 Record the relocation check result for each CMake-built dependency and produce the list of eligible and ineligible dependencies
- [x] 8.2 Mark eligible dependencies store-eligible one dependency per change, verifying for each that a first build populates the store and a clean second build reuses it without rebuilding that dependency
- [ ] 8.3 Confirm the deliberately force-built dependencies (including libtiff) stay ineligible and continue to build from source unchanged

## 9. Regression guard and continuous integration

- [ ] 9.1 Add an invariance check asserting that a default configure and build produces the same dependency locations, staged layout and build output as the pre-change baseline, and verify it passes on each supported platform
- [x] 9.2 Add one store-disabled configuration per supported platform to the build matrix and verify each succeeds
- [x] 9.3 Add one store-enabled configuration per supported platform to the build matrix and verify each succeeds and populates the store
- [x] 9.4 Publish the identity and manifest from a continuous integration build as a build artifact and verify both are retrievable
- [x] 9.5 Verify no continuous integration configuration fails a build on an identity mismatch in this change, confirming the report is not yet enforced
- [ ] 9.6 Verify a dependency served from the store is normalized by the same staging and install steps as one built in the build directory, and that the staged artifacts contain no reference to the store location
- [ ] 9.7 Add a packaging check that installs to a prefix different from the build directory and runs from that prefix, and verify it passes both for a store-enabled build and for a build that did not use the store

## 10. Documentation

- [x] 10.1 Document the identity tuple, its fields and how to read the reported values, in `docs/build_system/`
- [x] 10.2 Document the store: how to enable it with `RV_DEPS_STORE`, how to opt out, what is and is not eligible, and the recommendation to use one common store path when sharing between machines
- [x] 10.3 Document that building entirely from source is a permanent supported mode and that the store is never required
- [x] 10.4 Document the class of incompatibility that static probing cannot detect and name the functional validation that covers it
