# The dependency store

An opt-in, identity-addressed cache for the dependencies OpenRV builds from source. It exists so
that a second clone, a second build directory, a fresh worktree or a colleague's machine does not
rebuild what the first one already built.

**It is never required.** Building everything from source remains a supported mode on every platform,
and it is the default. With no store configured, nothing about the build changes.

## Enabling it

```bash
cmake -B _build -DRV_DEPS_STORE=$HOME/.cache/rv-deps
```

A relative path is taken relative to the build directory, and a leading `~` is expanded by CMake
itself, because no shell expands it inside a `-D` argument. Backslashes are accepted on Windows.

Installed dependency trees are then placed at

```
<store>/<platform>/<dependency>/<recipe>/install
```

- `<platform>` is a short digest of the build identity (see [build_identity](build_identity.md)),
  together with the platform facts the identity does not carry yet: the macOS architectures and
  deployment target, and the Linux C library version. Two configurations share a slot only when all
  of these are equal — the same compiler, standard library, C++ standard, Qt version, Python ABI
  series and binary baseline — so a configuration cannot be served artifacts built for another one.
- `<recipe>` is a short digest of what the dependency is built from: its version, its download
  hash, its dependency files under `cmake/dependencies/` and the patches they name. Bumping a
  dependency, or changing one of its patches, addresses a new entry, so a store hit only ever
  happens for the same content.

Turning it off is just as direct:

```bash
cmake -B _build -DRV_DEPS_STORE=
```

The next configure returns the tree to the in-build-directory layout, and forgets every cached path
that still names the store: the dependency's own cached directories, what find modules remembered,
and, in dependency sub-builds configured after a stored dependency, what their find modules cached
for it. Moving the store, or bumping a stored dependency, forgets the old location the same way. A
tree that has never used a store gets none of this, and configures exactly as before.

On Windows, staging an install roughly doubles the length of its path, because the staged tree
repeats the entry's path under the store. The digests are kept short for that reason, but keep the
store path short, or enable long paths (`LongPathsEnabled`), if dependencies with deep header
trees are made eligible.

## What is stored, and what is not

Only **installed** dependency trees. Source, build, stamp and download directories stay in the build
directory, because they embed absolute paths; a store on a shared path would otherwise hand one
machine another machine's build state, which is worse than rebuilding.

Only dependencies that have passed the **relocation check** are stored. A store entry is found by
path, so an installed tree that remembers where it was installed works perfectly until it is used
from anywhere else, and then fails somewhere unrelated. A dependency is named eligible only after
that check passes:

```bash
python3 src/build/check_relocation.py \
    --install <store>/<platform>/RV_DEPS_ZLIB/<recipe>/install \
    --package ZLIB --target ZLIB::ZLIB --module \
    --include zlib.h --exercise 'zlibVersion();'
```

The check moves the installed tree aside — renamed, not deleted, so it is always recoverable — and
searches a copy of it for any mention of the path it came from: package and pkg-config files, and
the runtime search paths and install names inside its libraries, in every spelling of the path. It
then builds a consumer against the copy and runs it without pointing the loader at it, so a library
that looks for a sibling or a data file at the original location fails. Moving the tree aside is the
point: a check that leaves the original in place cannot detect a reference to it.

`src/build/test_deps_store_roundtrip.py` runs the check against the zlib the store actually
publishes, on every platform in CI, so zlib's eligibility is re-established rather than recorded
once.

The publish step makes pkg-config files relative to themselves (`${pcfiledir}`), because they name
the absolute install prefix; without that, zlib's `zlib.pc` alone fails the check.

`RV_DEPS_STORE_ELIGIBLE` defaults to `default`, which stands for the dependencies that have passed
the check (`RV_DEPS_STORE_ELIGIBLE_DEFAULT` in `cmake/macros/rv_deps_store.cmake`). Because the list
is not copied into the cache, a tree configured earlier follows it when it changes. Each name in it
was added on its own with the round trip verified: a first build populating the store, and a clean
second build directory reusing it without rebuilding that dependency. To store a dependency of your
own as well:

```bash
cmake -B _build -DRV_DEPS_STORE=$HOME/.cache/rv-deps -DRV_DEPS_STORE_ELIGIBLE="default;RV_DEPS_IMATH"
```

An empty value stores nothing.

A dependency forced to build from source (`-DRV_DEPS_<NAME>_FORCE_BUILD=ON`) is never stored: it
is built and installed in the build directory, and a store entry for it is ignored. That is how to
get away from an entry you do not trust. Dependencies that are force-built because their patches or
private headers matter are never eligible, and keep behaving exactly as before.

A published entry is never modified. What a dependency adjusts after installing — zlib's install
name on macOS, its renamed import library in a Windows Debug build — is applied to the staged tree
before it is published, and consumers stage their own copies.

## Sharing a store between machines

Point several machines at one path over a shared filesystem and they will reuse each other's
dependencies, provided their identities match — which, for a studio on one reference platform with
one toolchain, they will. The Linux C library and the macOS deployment target are part of the slot,
so a Rocky Linux 8 and a Rocky Linux 9 machine sharing a store do not exchange binaries.

Use one common path on every machine. Eligible dependencies have passed the relocation check, which
rejects any reference to the install location, but a dependency you add to the list yourself has
only been checked where you checked it; do not relocate a *store* between differing host paths
without re-running the check for it.

## Partial entries and concurrent builds

An entry appears complete or not at all. Every install stages into a directory of its own under
`<store>/.staging`, held under a lock while it runs, and the finished tree is moved into place with
an atomic rename; the marker that says an entry is published is written only after the tree is in
place. A later configure consumes an entry only when that marker is present, so an interrupted
install leaves nothing usable behind — and a directory that merely exists, because configure
creates each dependency's install directory, is not taken for a finished dependency. A staging
directory left by an install that was killed is removed by the next install, once its lock shows
nobody holds it.

Two configurations may build the same dependency at the same time. They stage separately, and
publishing is serialized per entry by a lock beside it: the first to publish wins, the other's
staged copy is discarded, and the entry is the same dependency either way, because its recipe digest
says so. A published entry is never replaced.

If an entry is deleted from the store, the build directory that produced it notices on its next
configure and runs that dependency's install again, rather than trusting stamps that say it is
installed.

## What it does not do

It does not download prebuilt dependencies. It caches what your own source build produced. It also
does not speed up the first build of an identity: someone has to build it once, and the store pays
off from the second configuration onward.
