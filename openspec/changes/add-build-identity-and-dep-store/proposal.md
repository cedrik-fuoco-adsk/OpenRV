# Build identity and shared dependency store

## Why

OpenRV builds roughly thirty third-party dependencies from source **into the build
directory itself** (`RV_DEPS_BASE_DIR` defaults to `${CMAKE_BINARY_DIR}`), so the same
work is repeated for every build configuration, every fresh clone, and every git
worktree:

- `_build/` (Release) and `_build_debug/` (Debug) each hold a complete, independent
  dependency tree. Switching configuration with `rvdebug`/`rvrelease` rebuilds all of it.
- `rvclean` is destructive: `rm -rf ${RV_BUILD_DIR}` discards every dependency tree,
  because dependencies live inside the directory being deleted.
- Switching `RV_VFX_PLATFORM` loses the previous year's trees entirely.

This is the dominant cost for anyone whose goal is simply *to improve RV* — a studio
building RV against its own pipeline, or an RV developer iterating on the application.

Compounding this, nothing records or checks **what a build is actually made of**. ABI
mismatches between prebuilt artifacts are discovered by humans reading link errors,
not by the build system. The historical example is in the git log:

> "force openexr from source for conan with rocky 8 because of an issue with the
> openexr packages that has a different libstdc++ GLIBCXX"

The project already has partial answers — Conan with platform profiles, and the
`prototype-pbs` branch that sources Python and PySide6 prebuilt — but there is no
shared vocabulary for *which components are allowed to disagree*, and no way to check it.

## What Changes

This change is **phase 0 and phase 1** of a larger effort. Neither phase changes
today's build. With no new variable set, configuration and output are identical to
the current behaviour.

- **Phase 0 — observe (on by default, read-only).** Compute a single build identity
  tuple at configure time; probe dependency artifacts for the ABI facts they provide;
  write a build manifest recording what the build is made of. This phase reroutes no
  paths, creates no store, and requires no new external tool at configure time.
- **Phase 1 — shared dependency store (opt-in, default off).** Introduce
  `RV_DEPS_STORE`. When set, CMake-built dependencies are placed in an
  identity-addressed store outside the build directory instead of inside it.
  Unsetting the variable restores today's layout exactly.
- **Per-dependency rollout.** Dependencies move into the store **one at a time**, each
  gated by a relocation check (build in location A, relocate to B, link, run). Store
  eligibility is proven per dependency, never assumed.
- **The from-source path is a permanent supported mode.** It is not a transitional
  fallback. The store is an accelerator; it is never required.
- **Conan is not modified.** Conan keeps ownership of the C/C++ packages it already
  manages, via its own cache and `package_id`. The store covers the dependencies Conan
  does not manage.

Explicitly **not** in this change: the derived-Qt artifact, the PBS Python fast path,
and making the identity a CI gate. Those remain phases 2–4 and must not be reachable
from this work.

## Capabilities

### New Capabilities

- `build-identity`: computing the platform identity tuple once (VFX platform, target,
  toolchain, Qt, Python) and exposing it consistently to both the CMake and Conan
  paths, so the two cannot drift apart.
- `dependency-abi-probe`: reading ABI facts from an artifact rather than from a
  declaration — version, linkage configuration, feature set, and symbol-level demands
  — with separate probes for an ingested input and a derived artifact, and a
  requirement/provision comparison that decides whether substitution is legal.
- `build-manifest`: emitting a single manifest per build recording the identity, the
  Conan package set, and the artifacts used, so "what is this build made of?" has one
  auditable answer.
- `dependency-store`: the opt-in identity-addressed store for CMake-built dependencies,
  including per-dependency eligibility, the relocation check that gates it, and
  preservation of the existing in-build-directory layout when the store is unset.

### Modified Capabilities

None. No existing capability has spec-level behaviour that changes; the default
configuration behaves exactly as it does today.

## Impact

- `cmake/defaults/rv_options.cmake` — new `RV_DEPS_STORE` and identity options;
  `RV_DEPS_BASE_DIR` default becomes conditional, re-derived with `FORCE` so opting out
  is a clean opt-out after a tree has been configured once.
- `cmake/macros/` — new macros for identity computation, artifact probing, manifest
  emission, and the relocation check.
- `cmake/dependencies/*.cmake` — per-dependency opt-in into the store, one dependency
  at a time. No dependency behaviour changes unless the store is enabled.
- `rvcmds.sh` — surfaces the new environment variables. No alias changes; default
  behaviour is unchanged.
- `.github/workflows/` — publishes the phase 0 identity and manifest report as a build
  artifact. No gate is introduced in this change.
- `docs/build_system/` — documents the identity, the store, and the opt-out.
- External tooling: `readelf`/`otool`/`dumpbin` are used by the probe, but only by the
  opt-in store path and the reporting path — never as a hard configure-time dependency
  of a default build.
