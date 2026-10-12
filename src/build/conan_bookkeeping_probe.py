#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# *****************************************************************************
# Copyright 2026 Autodesk, Inc. All rights reserved.
#
# SPDX-License-Identifier: Apache-2.0
#
# *****************************************************************************

"""A Conan consumer used only to exercise the OpenRVBase generate step cheaply.

This is not part of the build. It exists because the identity and package bookkeeping in
``openrvcore-conanfile.py`` lives in ``generate()``, which the real Conan build only reaches
after an hour of dependency installation -- and by then a wrong Conan API call has already
broken ``conan install`` on every platform.

Subclassing OpenRVBase with a single small requirement runs the same code path in about a
minute: the identity is written from the profile, and the resolved dependency is enumerated
through the package reference.

The first version of the package bookkeeping called ``dependency.package_id``, which does not
exist in Conan 2 -- the identifier is on the package reference. A stub cannot catch that; only
real Conan can, which is why this runs against real Conan in CI.

It has to be copied to the repository root before use, because the base class resolves its
helper scripts relative to the recipe folder.
"""

from conan import ConanFile


class ConanBookkeepingProbe(ConanFile):
    name = "conanbookkeepingprobe"
    version = "0.1.0"
    python_requires = "openrvcore/1.0.0"
    python_requires_extend = "openrvcore.OpenRVBase"

    settings = "os", "compiler", "build_type", "arch"
    options = {"vfx_platform": ["CY2023", "CY2024", "CY2025", "CY2026"]}
    default_options = {"vfx_platform": "CY2025"}

    def requirements(self):
        # One real dependency, so the enumeration loop actually runs. Kept tiny: the point is
        # the bookkeeping, not the dependency.
        self.requires("zlib/1.3.2")

    def build_requirements(self):
        # The real recipe pulls an MSYS2 toolchain on Windows, which is far more than this needs.
        pass
