# The dependency store

An opt-in, identity-addressed cache for the dependencies OpenRV builds from source. It exists so
that a second clone, a second build directory, a fresh worktree or a colleague's machine does not
rebuild what the first one already built.

**It is never required.** Building everything from source remains a supported mode on every platform,
and it is the default. With no store configured, nothing about the build changes.

## Enabling it

```bash
cmake -B _build -DRV_DEPS_STORE=~/.cache/rv-deps
```

Installed dependency trees are then placed at `<store>/<identity>/<dependency>/install`, where
`<identity>` is the build identity (see [build_identity](build_identity.md)). Two configurations
share a dependency only when their identities are equal, which means the same compiler, standard
library, C++ standard, Qt version and Python ABI series — so a configuration cannot be served
artifacts built for another one. A different identity gets a different directory, and nothing needs
to notice, because it is a different path.

Turning it off is just as direct:

```bash
cmake -B _build -DRV_DEPS_STORE=
```

The next configure returns the tree to the in-build-directory layout. That works because the install
location is re-derived on every configure rather than remembered, so a tree that has used a store
does not keep pointing at it.

## What is stored, and what is not

Only **installed** dependency trees. Source, build, stamp and download directories stay in the build
directory, because they embed absolute paths; a store on a shared path would otherwise hand one
machine another machine's build state, which is worse than rebuilding.

Only dependencies that have passed the **relocation check** are stored. A store entry is found by
path, so an installed tree that remembers where it was installed works perfectly until it is used
from anywhere else, and then fails somewhere unrelated. A dependency is named in
`RV_DEPS_STORE_ELIGIBLE` only after that check passes:

```bash
python3 src/build/check_relocation.py \
    --install <store>/<identity>/RV_DEPS_ZLIB/install \
    --package ZLIB --target ZLIB::ZLIB --module \
    --include zlib.h --exercise 'zlibVersion();'
```

The check moves the installed tree aside — renamed, not deleted, so it is always recoverable — builds
a consumer against a copy at a different path, runs it, and searches what was built for any mention
of the path the tree came from. Moving the tree aside is the point: a check that leaves the original
in place cannot detect a reference to it.

The default list is deliberately short, and each name in it was added on its own with the round trip
verified: a first build populating the store, and a clean second build directory reusing it without
rebuilding that dependency. To store a dependency of your own, add it:

```bash
cmake -B _build -DRV_DEPS_STORE=~/.cache/rv-deps -DRV_DEPS_STORE_ELIGIBLE="RV_DEPS_ZLIB;RV_DEPS_IMATH"
```

Dependencies that are force-built because their patches or private headers matter are never eligible,
and keep behaving exactly as before.

## Sharing a store between machines

Point several machines at one path over a shared filesystem and they will reuse each other's
dependencies, provided their identities match — which, for a studio on one reference platform with
one toolchain, they will. Use one common path: generated CMake package files may contain absolute
include and library paths, and although the relocation check rejects a dependency that cannot be used
from a different path, do not relocate a *store* between differing host paths without re-running the
check.

## Partial entries and concurrent builds

An entry appears complete or not at all. Installs are staged inside the store entry and moved into
place with an atomic rename, and the marker that says an entry is published is written only after the
tree is in place. A later configure consumes an entry only when that marker is present, so an
interrupted install leaves nothing usable behind — and a directory that merely exists, because
configure creates each dependency's install directory, is not taken for a finished dependency.

Two configurations may build the same dependency at the same time. They stage separately and both
attempt the rename; the first published entry wins, the other staged copy is discarded, and the entry
is the same dependency for the same identity either way.

## What it does not do

It does not download prebuilt dependencies. It caches what your own source build produced. It also
does not speed up the first build of an identity: someone has to build it once, and the store pays
off from the second configuration onward.
