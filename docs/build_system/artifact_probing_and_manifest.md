# Artifact probing and the build manifest

Two related pieces of build bookkeeping:

- **Artifact probing** reads what a prebuilt artifact actually provides — its version,
  linkage configuration, feature set and ABI demands — so that a decision to use it rests
  on measured facts rather than on a version string.
- **The build manifest** records the identity, the resolved Conan package set and every
  probed artifact in one file, so "what is this build made of?" has a single auditable
  answer.

Both are read-only. Neither reroutes a dependency path.

The manifest is written on every configure. Probing is **off by default**
(`RV_DEPS_PROBE_ARTIFACTS=OFF`), because inspecting binaries on every configure is a
slowdown a default build should not pay; a configuration with a dependency store probes
regardless, because a store entry must be verified before it is used. Turn it on with
`-DRV_DEPS_PROBE_ARTIFACTS=ON` to record probed facts in the manifest.

## Why version equality is not enough

Two artifacts can carry the same version and still be incompatible: different compiler,
different standard library, static instead of shared, a different feature set. The
substitution test is therefore a comparison of what an artifact **provides** against
what a consumer **requires**, not a string comparison.

```
   provision (read from the artifact)             requirement (declared by the consumer)
   ──────────────────────────────────────         ──────────────────────────────────────
   linkage.type    = shared                 =      linkage.type    = shared
   linkage.config  = release                =      linkage.config  = release
   version.value   = 6.5.3                  ≥      version         ≥ 6.5.0
   features        = [opengl, shared, …]    ∋      feature         = opengl
   abi_demands     = [GLIBCXX 3.4.20, …]    ≤      symbol_version  available 3.4.29
   abi_demands     = [minos 11.0]           ≤      platform_floor  available 14.0
                                                  ──────────────────────────────────────
                     legal only when every requirement is met
```

Note the deliberate asymmetry, which is easy to get backwards:

- The artifact's **own version** is a floor — it must be at least what is required.
- **ABI demands** are ceilings — the artifact must not require more of its runtime
  environment than that environment provides. An artifact demanding *less* is fine, and an
  artifact demanding something newer is not usable. So a library that needs `GLIBCXX
  3.4.20` is usable where `3.4.29` is available, and not usable where `3.4.19` is.

An **unknown** fact never satisfies a requirement. "We could not determine this" is not
the same as "this is fine".

## Where facts come from

| Fact | Source |
| ---- | ------ |
| format, linkage type | The file's own headers, parsed directly. No external tool |
| version, feature set | Metadata the artifact ships with: Qt's `mkspecs/qconfig.pri`, or a pkg-config file installed alongside the library. A metadata root given for one artifact applies to that artifact only — Qt's root is never consulted for any other library |
| ABI demands | Tool-backed: `readelf` or `llvm-readobj` on ELF, `otool` or `llvm-objdump` on Mach-O, `llvm-readobj` or `dumpbin` on PE |

ABI demands are recorded as `(namespace, version)` pairs. On ELF a `readelf` version-needs row
reads `Name: GLIBCXX_3.4.29  Flags: none  Version: 71`, where the name carries **both** the
namespace and the version and the trailing `Version:` is a table index with no ABI meaning —
so `GLIBCXX_3.4.29` is recorded as namespace `GLIBCXX`, version `3.4.29`, and the index is
discarded. On Mach-O the floor comes from the `minos` field of the load command that declares
it, never from any other field that happens to be called `version`; on PE the demands are the
runtime imports.

There is deliberately **no way to declare a fact**. A declaration supplied by the user is
what this exists to replace, so it is not an input. A plain shared library that ships no
feature metadata legitimately reports its feature set as unknown.

Facts that cannot be determined are recorded as unknown *with a reason*, never omitted —
that is how "no metadata" stays distinguishable from "nothing was checked".

### Probing needs no tool in a default build

Header-derived facts need nothing but Python. The ABI-demand facts need an inspection
tool, and when one is missing:

- the fact is recorded as unknown and a warning is printed, and the build continues
- unless strict probing is on, in which case configuration fails naming the missing tool

Strict probing is for a configuration that must not use an artifact whose facts cannot be
verified, such as the dependency store that follows in a separate change. A default build leaves it off so that a machine without
`readelf`/`otool`/`dumpbin` still builds.

### Results are cached by artifact content

An artifact is inspected at most once per distinct content. The cache lives in
`<build-dir>/rv-probe-cache/`, keyed by a hash of the artifact's bytes and of the metadata
root it was observed with, and by a cache version that is bumped when what is observed
changes. Changing an artifact produces a different key, so a stale result can never be
served for changed bytes.

A result whose inspection did not happen — the tool was missing, timed out, or could not
read the file — is marked `"retryable": true` and never cached, so a tool installed later,
or a strict probe, inspects again instead of inheriting the unknown.

## The build manifest

Written to `<build-dir>/build-manifest.json` at configure time.

```json
{
  "fields_version": 1,
  "identity": { "compiler_id": "gcc", "hash": "sha256:…", "…": "…" },
  "artifacts": {
    "probes": [
      { "role": "input", "content_reference": "sha256:…",
        "linkage": { "type": "shared", "config": "release" }, "…": "…" }
    ]
  },
  "conan": {
    "identity": { "compiler_version": "11", "partial": "true", "…": "…" },
    "packages": [{ "name": "openexr", "version": "3.3.6", "package_id": "…" }]
  }
}
```

Properties worth relying on:

- **Content-derived references.** Artifacts are identified by `content_reference`, a hash
  of their bytes, so two builds using the same artifact are recognisable as such without
  comparing host paths, and differing content always produces a differing reference.
- **Deterministic.** Sorted keys and no timestamp, so two configurations with unchanged
  inputs produce byte-identical manifests and a diff between them is meaningful. How a
  probe result was obtained — inspected or read from the cache — is left out for that
  reason.
- **What was found.** `found` records facts known only after the identity was computed
  and that can differ from it, such as `found.qt_version` when `QT_HOME` points at a Qt
  other than the one `RV_VFX_PLATFORM` specifies.
- **No credentials.** Packages are recorded by name, version, reference, package ID and
  recipe revision; no remote URL, token or password is.
- **Never fatal.** A section that cannot be read, or a manifest that cannot be written,
  is a warning and the build continues. Sections that are absent are listed under
  `omitted` with a reason.

## Known limitation: static probing cannot see everything

Static probing compares version, linkage, feature set and ABI demands. It **cannot**
detect an incompatibility that leaves every symbol and every feature unchanged while
altering a binary layout — for instance two builds of the same Qt version whose class
layouts differ while their exported symbols do not.

That class of incompatibility is only detectable by **running** something: loading the
binding and exercising an object shared with the application (RV passes a `QMainWindow *`
to Python and hands it to `shiboken.wrapInstance`, so the wrapped object's layout must be
the one RV compiled against). That functional check is the designated coverage for this
class of problem, and it belongs with the changes that introduce prebuilt Qt and PySide6
bindings.

A functional check that passes for one artifact says nothing about a same-version
artifact that was not itself checked.

## Turning it off

```bash
cmake -B _build -DRV_BUILD_MANIFEST=OFF …              # no manifest
cmake -B _build -DRV_DEPS_PROBE_ARTIFACTS=ON …         # probe prebuilt artifacts (off by default)
```

## Tests

```bash
python3 src/build/test_probe_artifact.py
python3 src/build/test_build_manifest.py
```

The Conan side is exercised against real Conan by CI rather than by a stub. A stub cannot catch a
wrong Conan API call — the first version of the package bookkeeping used `dependency.package_id`,
which does not exist in Conan 2, and a stub happily accepted it while the real run failed
`conan install` on every platform. `src/build/conan_bookkeeping_probe.py` is a minimal consumer
that runs the same `generate()` path with one small dependency, in about a minute; CI copies it to
the repository root (where the base class expects the consumer recipe) and runs it against real
Conan.
