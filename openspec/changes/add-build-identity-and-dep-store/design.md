# Design — build identity and shared dependency store

## Context

See `proposal.md` for motivation. The constraints that shape this design come from the
existing build system:

- `RV_DEPS_BASE_DIR` defaults to `${CMAKE_BINARY_DIR}` and **every** CMake dependency
  module derives its `src`/`build`/`install` locations from it:

  ```
  cmake/defaults/rv_options.cmake:14
    SET(RV_DEPS_BASE_DIR "${CMAKE_BINARY_DIR}" CACHE STRING ...)
          └──▶ every cmake/dependencies/*.cmake uses
               ${RV_DEPS_BASE_DIR}/${_target}/{src,build,install}
  ```

  This single funnel is what makes an opt-in store cheap to add, and it is also why
  `rvclean` is destructive.

- A find-first path already exists. `RV_DEPS_PREFER_INSTALLED` plus
  `RV_FIND_DEPENDENCY` lets a dependency be satisfied by `find_package()` instead of
  being built. The Conan layer drives this path today via `CMakeDeps`.

- Conan already has the store property for the packages it manages: `package_id` is an
  identity hash, `~/.conan2/p/` is a store outside the build directory, and the ASWF
  remote distributes artifacts.

- Qt is not a pristine input: `apply_qt_fix.sh` patches files inside `$QT_HOME`, and
  `cmake/dependencies/qt6.cmake` merges QtWebEngine into `$QT_HOME`. RV therefore
  cannot fingerprint Qt by hashing its tree.

- Some dependencies are deliberately force-built from source (for example libtiff, which
  OpenRV patches and whose private headers are used), so store eligibility cannot be
  uniform.

- Relocatability is partly handled and partly not: `SET(CMAKE_SKIP_RPATH ...)`,
  `-DCMAKE_INSTALL_RPATH=` for some dependencies, an RPATH fixup loop in
  `rv_stage.cmake`, and `remove_absolute_rpath.py` at install time. Coverage is
  per-dependency and inconsistent.

## Goals / Non-Goals

**Goals:**

- Give the build one authoritative, machine-readable statement of the platform it
  targets, consumed by both the CMake and Conan paths.
- Make the composition of a build auditable from a single file written at configure time.
- Make dependency reuse possible across configurations, clones and worktrees, without
  changing what a default build does.
- Establish a per-dependency, evidence-based procedure for deciding what may be reused.

**Non-Goals:**

- Deriving Qt, sourcing Python prebuilt, or repointing PySide6. These are later phases
  and must not be reachable from this change.
- Modifying the Conan layer, its profiles, or `packages.yml`.
- Making the store mandatory, default-on, or a prerequisite for any supported platform.
- Removing or deprecating the from-source path.
- Distributing prebuilt store contents from a remote.

## Decisions

### D1: The identity is a shared value, not a per-path check

Each resolution path currently derives its own answer — `conan/profiles/*` hand-write
`compiler.version`, while the CMake path trusts the host compiler. That drift is the
mechanism behind the historical OpenEXR/libstdc++ incident. Computing the tuple once and
publishing it to both consumers removes the class of bug rather than the instance.

```
     ┌──────────────────────────────┐
     │  identity computed ONCE      │
     └──────┬────────────────┬──────┘
            │                │
      conan profile       store key
            │                │
     ┌──────▼──────┐  ┌──────▼────────────┐
     │ C/C++ libs  │  │ CMake-built deps  │
     │ (Conan owns)│  │ (store owns)      │
     └─────────────┘  └───────────────────┘
```

*Alternative considered:* let each path keep its own settings and add a cross-check.
Rejected — a check can only detect drift, not prevent it.

### D2: Conan keeps C/C++; the store covers what Conan does not

Conan already has an identity-addressed cache and a remote. Reimplementing that for the
packages it manages would be duplication. The store's value is the dependencies Conan
does not manage — OIIO, OCIO, FFmpeg, GLEW, Vulkan, crashpad, imgui, gc and similar —
which today are built into `_build` and destroyed by `rvclean`.

*Alternatives considered:* (a) move everything into Conan — rejected, Qt-for-Python style
recipes are heavy to author and maintenance-intensive, and "fetch a prebuilt interpreter
and adapt it" is not a build recipe; (b) one CMake-only store for all dependencies —
rejected, it would orphan working infrastructure.

### D3: The store redirects `RV_DEPS_BASE_DIR`, and the default is re-derived with `FORCE`

When a store location is configured, `RV_DEPS_BASE_DIR` defaults to a store path derived
from the identity; when it is not configured, the default remains `${CMAKE_BINARY_DIR}`.
Because `RV_DEPS_BASE_DIR` is a `CACHE STRING`, the default must be re-derived on every
configure with `FORCE`, otherwise a tree once configured against a store would keep that
path after the store was removed — making "opt out" a lie. The codebase already contains
this exact bug class and its fix, documented for `RV_CPP_STANDARD`:

> "Without it an existing build tree reconfigured to a newer VFX platform would keep the
> standard cached by its first configure and silently build CY2026 with C++17."

An explicitly user-set `RV_DEPS_BASE_DIR` still wins.

### D4: Satisfying a dependency from the store goes through the find path, not the build path

A store entry is consumed by the existing find-first mechanism (`RV_FIND_DEPENDENCY`)
rather than by pre-seeding `ExternalProject` state. This matters because
`ExternalProject` stamps, source trees and build trees embed absolute paths and are not
portable. Only **installed** trees are shared; source and build trees stay local to
whichever configuration produced them.

```
   dependency requested
          │
          ├─ store entry exists for this identity?  ──▶ find_package() against the store  (skip build)
          │
          └─ no ──▶ ExternalProject as today ──▶ install into the store (if eligible)
```

*Alternative considered:* store `ExternalProject` source and build trees as well.
Rejected — non-portable state, and it would make partial write-in-progress much harder
to reason about.

### D5: Store eligibility is per dependency and evidence-based

A dependency becomes store-eligible only after the relocation check passes: install in
one location, relocate the installed tree, link a consumer against the relocated tree,
and run that consumer successfully. Force-built dependencies whose private headers or
patches matter (libtiff being the known case) simply never become eligible, and
therefore keep behaving exactly as today.

*Alternative considered:* enable the store for all dependencies at once behind the flag.
Rejected — a single baked-in absolute reference produces a failure that appears
unrelated to the store, and the resulting bug report is very expensive.

### D6: Probes read artifacts; substitution is a provision-versus-requirement comparison

Version equality is not a safe test, because artifacts with the same version can differ
in linkage configuration, feature set and compiler ABI. The probe therefore records what
an artifact *provides* (version, linkage, features, ABI demands) and the consumer's
*requirement*; substitution is legal only when the provision covers the requirement.

This is deliberately the same information Conan's `package_id` encodes for C/C++
packages, and the same shape as RPM's `Requires`/`Provides`. It also subsumes the one
provenance signal RV already inspects in the code today — the macOS `codesign -dv` check
that distinguishes official Qt builds from re-signed redistributions.

*Alternative considered:* a registry of known-good artifact fingerprints. Rejected for
this change. Content-addressing an ingested artifact already yields a provenance record
with no registry to maintain, and static probing in the provision/requirement model
distinguishes same-version-different-build artifacts without any registry at all.

### D7: Probes run as a separate cached check, not during configure

Probing requires `readelf`, `otool` or `dumpbin`, which a default build must not depend
on. Probe results are cached by artifact content, so the cost is paid once per artifact
rather than once per configure.

*Alternative considered:* probe during configure. Rejected — it slows every configure and
introduces a hard tool dependency into the default path.

### D8: One manifest, referencing the Conan lock and the store

A single manifest per build answers "what is this build made of?" without requiring three
files to be read together. Conan keeps ownership of `conan.lock`; the manifest records
the resolved Conan package set and the content references of store artifacts.

*Alternative considered:* keep separate locks per subsystem. Rejected — the audit
question is asked about the build, not about a subsystem.

### D9: Store location defaults to a user cache, overridable

The default is a per-user cache location, overridden by `RV_DEPS_STORE`. A studio can
point several machines at one shared path; a developer who wants isolation can point it
at a project-local directory.

*Alternative considered:* repo-local store. Rejected as the default because every fresh
clone would pay the full cost again, which is the problem being solved.

### D10: Debug configurations are a distinct identity

Release and Debug differ in ABI-relevant compilation (`NDEBUG`, and on Windows the C
runtime), so they must not share store entries. Debug continues to build from source,
which is compatible with the store: Debug simply occupies its own identity slot and,
once built, is reused from there rather than rebuilt.

### D11: Phasing, with phase 0 read-only and phase 1 opt-in

```
P0  OBSERVE    identity, probe, manifest      default ON, read-only, reroutes nothing
P1  STORE      RV_DEPS_STORE opt-in           default OFF, per-dependency
```

The invariant that makes the phasing safe, and that continuous integration must assert:

```
With no new variable set:
  ✓ configure and build behave as today
  ✓ dependencies land in <build_dir>/RV_DEPS_*
  ✓ rvcmds.sh aliases behave identically
  ✓ no store is created, read or required
  ✓ no new external tool is required at configure time
```

*Alternative considered:* land observe and store together, default-on. Rejected — the
user-visible promise is that nothing changes until each phase is proven.

### D12: Store membership is invisible to the packaged output

The store changes where a dependency is built and cached, never how it is staged or
installed. A dependency served from the store passes through the same install-time and
staging-time path normalization as the same dependency built inside the build directory,
so the packaged result never references the store location.

This is what preserves the distribution guarantee: `cmake install` output must run on any
machine of the same platform, which is a requirement of the product, not of the build
cache. Relocatability of the shipped artifact is produced by the install and staging
steps, and must not become conditional on where a dependency happened to be cached.

*Alternative considered:* treat store-sourced dependencies as already normalized and skip
the fixup for them. Rejected — it would make the shipped output's relocatability depend on
cache state, which is a silent difference the store must not introduce.

### D13: The Conan documents reach CMake by convention, not through the generator

The Conan generate step writes `conan-identity.json` and `conan-packages.json` and passes their
paths to CMake as cache variables. That works only for the generators where `CMakeToolchain` writes
cache variables into `conan_toolchain.cmake`: with Visual Studio, a multi-config generator, they are
written to `CMakePresets.json` instead, which a configure driven by `-DCMAKE_TOOLCHAIN_FILE` never
reads. On Windows the paths would therefore never arrive, and the manifest's Conan section would be
silently empty -- indistinguishable from "this build did not use Conan".

CMake therefore defaults both paths to the build directory, where Conan writes the documents on
every generator, and treats the cache variable as an override.

*Alternative considered:* depend on the cache variables and document the generator requirement.
Rejected: it fails silently on one of the three supported platforms, in a way that looks like an
absence of information rather than like a defect.

### D14: The identity records the C runtime, not the build configuration name

On Windows, `CMAKE_MSVC_RUNTIME_LIBRARY` selects `/MD` or `/MT` independently of the build
configuration, so `build_config` alone does not say which runtime an artifact links
against. Two configurations identical except for that choice produced the same identity,
which for the store means one can be served the other's artifacts. On MSVC that is a link
error at best, and memory allocated in one heap and freed in another at worst.

The identity therefore carries `crt` on Windows -- `dynamic` or `static`, each optionally
`-debug` -- resolved from the compiler's own runtime selection rather than from an option
name, so that it tracks what the build does even when a user overrides it. The CMake side
resolves the generator expression CMake's own default contains; an expression it cannot
resolve is recorded verbatim rather than resolved wrongly, so the identity differs from a
resolved one instead of silently matching it.

On Linux and macOS the field is **absent** rather than defaulted: there is no correct
value to invent on a platform where the C runtime is not a separate ABI axis, and a
placeholder would be read as a fact.

Because this changes every identity hash, `FIELDS_VERSION` moved to 2, so an identity
computed under the old rules can never be confused with one computed under the new ones.

The Windows Conan profile states `compiler.runtime_type` explicitly rather than leaning on
the default. An unset runtime type follows the build type, so stating it changes no package
ID -- checked against zlib, openssl, boost, pcre2 and openexr -- but it is what lets the
comparison see this field at all, because the profile must state both halves before the
field is emitted. While it stated only the runtime, the C runtime axis was compared as
unstated on the one platform where it is a real ABI axis.

*Alternative considered:* derive `crt` from `build_config`. Rejected -- that inference is
exactly what was wrong, and it fails on the case that matters, a Release build told to use
the static runtime.

*Alternative considered:* require `CMAKE_MSVC_RUNTIME_LIBRARY` to be left unset so that
the configuration name does imply the runtime. Rejected -- it removes a legitimate option
from users instead of fixing the identity.

### D15: The generated-file comparison pins the interpreter's hash seed

Conan's CMakeDeps renders a generated file's variable blocks by iterating
`set([file_name] + additional_prefixes)` (`conan/tools/cmake/cmakedeps/templates/config.py`),
and CPython randomises string hashing per process. `WebPConfig.cmake` therefore swaps its
`WebP_*` and `WEBP_*` blocks on roughly half of installs -- 60 fresh processes split 34 to 26,
and pinning the seed to 0 makes the order stable, which is the shape of a hash-order
dependency. Two installs of an unmodified tree therefore disagree, and a determinism control
can only sample that rather than detect it.

The comparison runs its installs with `PYTHONHASHSEED=0`, so both trees render in the same
order and the difference cannot arise. The reordering tolerance stays as a safety net, for
another generator doing the same thing or for an install run without the seed.

*Alternative considered:* rely on the control alone. Rejected -- that is what produced a
failure for a change that made no difference, because a control observes non-determinism by
sampling and can miss what it does not happen to see.

## Risks / Trade-offs

- **[Baked-in absolute paths make a stored dependency unusable from a different store
  path]** → This is scoped to the **build-time cache, not the shipped product**: the store
  is consumed through the find path, so these paths affect configure and link only, while
  the packaged output is normalized by the existing install and staging steps (see D12).
  → Mitigation: the relocation check is the gate for eligibility and is per dependency;
  dependencies that fail stay local. Document that machines sharing a store should use one
  common `RV_DEPS_STORE` path, since generated CMake package files may contain absolute
  include and library paths. Do not relocate a store between differing host paths without
  re-running the check.

- **[A store hit silently masks a dependency change]** → Content-derived references mean
  a changed artifact produces a different reference, so a hit can only occur for
  identical content. The manifest records the reference actually used.

- **[Probing cannot see layout-only incompatibilities]** → Explicitly documented, with a
  functional validation reserved for the phases that introduce prebuilt Qt and PySide6
  bindings. This change does not claim static probing is sufficient for grouping that
  involves C++ object layout.

- **[Concurrent configurations corrupt a shared store]** → Requirements cover waiting or
  building independently rather than consuming a partially written artifact. The
  implementation must make the publish step atomic (produce in a private location,
  then move into place).

- **[Disk growth from retained identities]** → Accepting retained identities is the point
  (that is what makes switching configurations cheap), but the store needs an eviction
  policy eventually. Deferred; see Open Questions.

- **[Phase 0 adds configure output that users may treat as a gate]** → Identity is
  reported, never enforced, in this change. Enforcement is a later phase.

## Migration Plan

1. **P0 lands default-on.** No migration: it writes a report into the build directory and
   reroutes nothing. Rollback is trivial because nothing depends on it.

2. **P1 lands default-off.** `RV_DEPS_STORE` unset means today's behaviour. Enabling it is
   a single-variable opt-in; disabling it after use returns the tree to the build-directory
   layout, which the `FORCE` re-derivation in D3 guarantees.

3. **Dependencies become eligible one at a time**, each in its own change, each with its
   relocation check result recorded. At no point is the build required to use the store.

4. **Continuous integration gains a store-disabled configuration per platform** so the
   permanent from-source path stays honestly tested rather than nominally supported.

## What went wrong, and what phase 1 inherits from it

The verification work for phase 0 produced a list of mistakes worth keeping, because phase 1 needs
its own checks -- the relocation check above all -- and every one of these would apply to them.

**Stubbing an external API and calling the result verified.** The Conan package bookkeeping called
`dependency.package_id`, which does not exist on Conan 2's `ConanFileInterface`; the identifier is
on the package reference. A hand-written stub declared that attribute, so the stub passed and the
real run failed `conan install` on all four platforms. A stub models an assumption about an API, so
it can only confirm what is already believed. Phase 1 must exercise real Conan -- which is what
`src/build/conan_bookkeeping_probe.py` is for -- and stubs may be trusted for pure logic only.

**Reasoning from a mechanism to a conclusion.** `lcms` renders its directories relatively when Conan
decides its binary is not needed, and that was observed. From it came the conclusion "therefore this
difference is noise", which was wrong: the control later showed the rendering is deterministic per
cache state. A mechanism explains a difference; it does not establish that the difference is benign.

**A check that passes for a weak reason.** Attribution keyed on `(kind, path)` meant any file the
control also saw churn was exempt from the tree comparison -- on Rocky 8 that was 24 files,
effectively the whole generated tree -- and the comparison reported OK while having checked almost
nothing. It was not wrong, it was empty, which is worse than a failure because it looks like
success. Phase 1's relocation check must never treat "could not compare" as "compatible".

**Comparing two things under different conditions.** The first version compared the current tree's
install, which ran early while the cache was still filling, against baseline installs that ran
later. Install order and cache state alone accounted for the differences. Both trees are now
installed at the same point from the same cache state, and the determinism control measures where
the comparison actually happens.

**Hand-threading escapes across too many layers.** The shell-to-Python seam was wrong three times in
three different ways: a missing argument from an edit that silently did not match, then two flavours
of backslash escaping, one of which injected a stray `n` argument per continuation. The invocation is
now a single line with no continuations, its shape is asserted by a test in
`test_compare_conan_generators.py`, and the script guards its own argument count so a mismatch says
what it expected. Anything crossing YAML to bash to Python should be checked rather than carefully
written.

**Editing programmatically without asserting the edit applied.** A `str.replace` silently did
nothing, which is how the missing argument above happened. Edits to the workflow now assert that
the anchor exists and is unique, and that assertion immediately caught a further ambiguity in the
same change.

**Trusting a green run without knowing what it compared.** The comparison's first success was the
vacuous one. A pass is evidence only once it is known which files were actually compared and on what
basis.

**Dismissing a hypothesis with a test that could not falsify it.** `PYTHONHASHSEED` was the right
explanation for Conan's varying `WebPConfig.cmake` from the start, and it was ruled out by a test
that did not hold the right thing constant. The cause is exactly that -- a generator iterating a set
of strings, whose order follows the per-process seed. A hypothesis is not dismissed by a test that
fails to confirm it; only by one that could have falsified it.

The technical findings these produced are recorded next to the code they constrain rather than here
-- CMake's `RETURN()` inside a macro returning from the caller's file, `CACHE INTERNAL` implying
`FORCE`, cache variables being unable to hold a newline, and `find_package(Python3)` colliding with
the project's own Python handling -- so that they cannot drift away from the code that depends on
them.

## Open Questions

- Building dependencies Release while RV itself is Debug, on Linux and macOS only, where the two
  are link-compatible. **Deferred, not rejected.** It is unusually cheap to do: the dependencies
  live in a subdirectory (`ADD_SUBDIRECTORY(cmake/dependencies)`) that contains no compiled targets,
  so one directory-scoped variable would reach all 50 uses of the build configuration, most of which
  are conditionals inside dependency files selecting debug patches, per-configuration library names
  and opt files -- not flag-passing that could be changed in one place and missed in another. With
  the default it is a literal no-op, which the invariance check in task 9.1 is what proves. Two
  things constrain it: on Windows it must be refused, because `/MD` and `/MDd` objects cannot be
  mixed, which is what the `crt` field exists to encode; and a dependency whose public headers differ
  under `NDEBUG` is a real ODR hazard when mixed. It would also change what `build_config` in the
  identity means -- the configuration the dependency artifacts were built with, which is what a Conan
  profile's `build_type` already means -- and would need to land before anything is keyed on the
  store, or the store gets re-keyed afterwards.
- Store eviction: when and how retained identities are pruned, and whether a
  size-bounded policy should exist. Deferred — no requirement depends on it.

- Whether the manifest is consumed by an external licence or SBOM tool, or remains
  human-read. Deferred — the content is already specified; the consumer does not change
  the format decision.

- Windows probe tooling: `dumpbin` is only on `PATH` inside a Visual Studio developer
  prompt. Since probing is confined to the opt-in store path, this can be resolved when
  the Windows store rollout begins.
