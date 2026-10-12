#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# *****************************************************************************
# Copyright 2026 Autodesk, Inc. All rights reserved.
#
# SPDX-License-Identifier: Apache-2.0
#
# *****************************************************************************

"""Self-verifying tests for compare_conan_generators.py.

Run directly:

    python3 src/build/test_compare_conan_generators.py

Exits non-zero if any check fails.
"""

import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "compare_conan_generators.py")

FAILURES = []
SKIPPED = []


def skip(description: str, why: str) -> None:
    print(f"  skip {description} ({why})")
    SKIPPED.append(description)


# The differences the identity work is allowed to introduce in a Conan generator directory.
ALLOW_ADDED = [r"conan-identity\.json", r"conan-identity\.inputs", r"conan-packages\.json"]
ALLOW_CHANGED = [r"conan_toolchain\.cmake"]
ALLOW_LINES = [r"RV_CONAN_IDENTITY_FILE", r"RV_CONAN_PACKAGES_FILE"]


def check(description: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"  ok   {description}")
    else:
        print(f"  FAIL {description}{(': ' + detail) if detail else ''}")
        FAILURES.append(description)


def write(root: str, relative: str, content: str) -> None:
    path = os.path.join(root, relative)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(content)


def run(*args):
    return subprocess.run([sys.executable, SCRIPT, *args], capture_output=True, text=True)


def make_trees(directory: str, current_tree: str | None = None):
    """A minimal stand-in for two Conan generator directories.

    The generated files embed the tree's own absolute path, exactly as Conan's do, so that
    normalization has something real to normalize.
    """
    baseline = os.path.join(directory, "baseline")
    current = os.path.join(directory, "current")
    for root in (baseline, current):
        write(
            root, "conan_toolchain.cmake", f'set(CMAKE_PREFIX_PATH "{root}/generators")\nset(CMAKE_CXX_STANDARD "17")\n'
        )
        write(root, "openexr-Target-release.cmake", "# identical generated dependency file\n")
        write(root, "zlib.pc", f"prefix={root}/generators\nName: zlib\n")
        write(root, "conanbuild.sh", "#!/bin/sh\necho build\n")
    if current_tree == "with-identity":
        write(current, "conan-identity.json", '{"compiler_id": "gcc"}\n')
        write(current, "conan-packages.json", '{"packages": []}\n')
        write(
            current,
            "conan_toolchain.cmake",
            f'set(CMAKE_PREFIX_PATH "{current}/generators")\nset(CMAKE_CXX_STANDARD "17")\n'
            f'set(RV_CONAN_IDENTITY_FILE "{current}/conan-identity.json" CACHE INTERNAL "")\n'
            f'set(RV_CONAN_PACKAGES_FILE "{current}/conan-packages.json" CACHE INTERNAL "")\n',
        )
    return baseline, current


def base_args(baseline: str, current: str, normalize: bool = True):
    args = ["--baseline", baseline, "--current", current]
    if normalize:
        # Both trees embed their own absolute path, so comparing them at all requires this.
        args += ["--normalize", f"{baseline}=<TREE>", "--normalize", f"{current}=<TREE>"]
    for pattern in ALLOW_ADDED:
        args += ["--allow-added", pattern]
    for pattern in ALLOW_CHANGED:
        args += ["--allow-changed", pattern]
    for pattern in ALLOW_LINES:
        args += ["--allow-changed-line", pattern]
    return args


def test_expected_differences_only(directory: str) -> None:
    print("only the named differences are present")
    baseline, current = make_trees(directory, "with-identity")
    result = run(*base_args(baseline, current))
    check("the comparison passes", result.returncode == 0, result.stdout.strip() + result.stderr.strip())
    check("it reports the added documents", "conan-identity.json" in result.stdout, result.stdout.strip())
    check("it reports the toolchain as changed", "conan_toolchain.cmake" in result.stdout, result.stdout.strip())


def test_path_normalization_is_what_makes_it_comparable(directory: str) -> None:
    print("without normalization the embedded paths would look like differences")
    baseline, current = make_trees(os.path.join(directory, "nonorm"), "with-identity")
    result = run(*base_args(baseline, current, normalize=False))
    check(
        "unnormalized trees are reported as differing",
        result.returncode == 2,
        f"exit {result.returncode}: {result.stderr.strip()}",
    )
    check(
        "the difference is named",
        "conan_toolchain.cmake" in result.stdout or "zlib.pc" in result.stdout,
        result.stdout.strip() + result.stderr.strip(),
    )


def test_a_reordering_is_not_a_difference(directory: str) -> None:
    print("a generated file carrying the same lines in a different order is not a difference")
    baseline, current = make_trees(os.path.join(directory, "reorder"), "with-identity")
    # The exact shape Conan produced for libwebp: two blocks of independently-assigned variables
    # whose relative order varies between installs of one tree. Reproduced from a failing run.
    webp = (
        'set(WebP_VERSION_STRING "1.2.4")\n'
        "set(WebP_INCLUDE_DIRS ${libwebp_INCLUDE_DIRS_RELEASE} )\n"
        "set(WebP_DEFINITIONS ${libwebp_DEFINITIONS_RELEASE} )\n"
        "\n"
    )
    webp_upper = (
        'set(WEBP_VERSION_STRING "1.2.4")\n'
        "set(WEBP_INCLUDE_DIRS ${libwebp_INCLUDE_DIRS_RELEASE} )\n"
        "set(WEBP_DEFINITIONS ${libwebp_DEFINITIONS_RELEASE} )\n"
        "\n"
    )
    write(baseline, "WebPConfig.cmake", webp + webp_upper)
    write(current, "WebPConfig.cmake", webp_upper + webp)

    result = run(*base_args(baseline, current))
    check("the comparison passes", result.returncode == 0, result.stdout.strip() + result.stderr.strip())
    check("the reordering is reported rather than hidden", "WebPConfig.cmake" in result.stdout, result.stdout.strip())
    check("it is named as reordered", "reordered" in result.stdout, result.stdout.strip())

    # The tolerance must not extend one line further: the same file, reordered and also altered.
    write(current, "WebPConfig.cmake", webp_upper + webp + 'set(WEBP_EXTRA "added")\n')
    result = run(*base_args(baseline, current))
    check("a reordering that also adds a line still fails", result.returncode == 2, f"exit {result.returncode}")
    check("and the file is named", "WebPConfig.cmake" in result.stdout, result.stdout.strip())

    # And a reordering that alters a value in place, which keeps the line count identical.
    write(current, "WebPConfig.cmake", webp_upper.replace('"1.2.4"', '"9.9.9"') + webp)
    result = run(*base_args(baseline, current))
    check("a reordering that changes a value still fails", result.returncode == 2, f"exit {result.returncode}")


def test_an_unexpected_change_is_a_violation(directory: str) -> None:
    print("an unexpected change fails the comparison")
    baseline, current = make_trees(os.path.join(directory, "unexpected"), "with-identity")
    # A dependency's generated config file must not change.
    write(current, "openexr-Target-release.cmake", "# DIFFERENT generated dependency file\n")
    result = run(*base_args(baseline, current))
    check("the comparison fails", result.returncode == 2, f"exit {result.returncode}")
    check("the changed file is named", "openexr-Target-release.cmake" in result.stdout, result.stdout.strip())


def test_an_unexpected_line_change_is_a_violation(directory: str) -> None:
    print("a change to a file allowed to change, on a line that is not allowed, fails")
    baseline, current = make_trees(os.path.join(directory, "linechange"), "with-identity")
    write(
        current,
        "conan_toolchain.cmake",
        f'set(CMAKE_PREFIX_PATH "{current}/generators")\nset(CMAKE_CXX_STANDARD "20")\n'
        f'set(RV_CONAN_IDENTITY_FILE "{current}/conan-identity.json" CACHE INTERNAL "")\n',
    )
    result = run(*base_args(baseline, current))
    check("the comparison fails", result.returncode == 2, f"exit {result.returncode}")
    check("the offending line is named", "CMAKE_CXX_STANDARD" in result.stdout, result.stdout.strip())


def test_a_removed_file_is_a_violation(directory: str) -> None:
    print("a file that disappears fails the comparison")
    baseline, current = make_trees(os.path.join(directory, "removed"), "with-identity")
    os.remove(os.path.join(current, "zlib.pc"))
    result = run(*base_args(baseline, current))
    check("the comparison fails", result.returncode == 2, f"exit {result.returncode}")
    check("the removed file is named", "zlib.pc" in result.stdout, result.stdout.strip())


def test_identical_trees_pass(directory: str) -> None:
    print("two identical trees pass with nothing to report")
    baseline, current = make_trees(os.path.join(directory, "identical"))
    result = run(*base_args(baseline, current))
    check("the comparison passes", result.returncode == 0, result.stdout.strip() + result.stderr.strip())
    document = json.loads(run(*base_args(baseline, current), "--json").stdout)
    check("nothing was added", document["added"] == [], str(document["added"]))
    check("nothing was removed", document["removed"] == [], str(document["removed"]))
    check("nothing changed", document["changed"] == [], str(document["changed"]))
    check("there are no violations", document["violations"] == [], str(document["violations"]))


def test_missing_directory(directory: str) -> None:
    print("a missing directory is an error, not a pass")
    baseline, current = make_trees(os.path.join(directory, "missing"))
    result = run("--baseline", os.path.join(directory, "does-not-exist"), "--current", current)
    check("the comparison errors out", result.returncode == 4, f"exit {result.returncode}")
    check("the message names the directory", "does-not-exist" in result.stderr, result.stderr.strip())


def test_json_is_compared_semantically(directory: str) -> None:
    print("JSON is compared semantically, not as text")
    baseline, current = make_trees(os.path.join(directory, "jsonsem"))
    # Adding a key also changes the preceding line's comma, so a line-level allowance could never
    # permit this; and reformatting moves every line without changing anything.
    write(
        current,
        "CMakePresets.json",
        '{\n  "version": 4,\n  "configurePresets": [\n    {\n      "name": "conan-release",\n      "cacheVariables": {\n        "CMAKE_CXX_STANDARD": "17",\n        "RV_CONAN_IDENTITY_FILE": "x"\n      }\n    }\n  ]\n}\n',
    )
    write(
        baseline,
        "CMakePresets.json",
        '{\n  "version": 4,\n  "configurePresets": [\n    {\n      "name": "conan-release",\n      "cacheVariables": {\n        "CMAKE_CXX_STANDARD": "17"\n      }\n    }\n  ]\n}\n',
    )

    args = base_args(baseline, current)
    result = run(*args)
    check("a JSON key addition is a difference by default", result.returncode == 2, f"exit {result.returncode}")

    result = run(*args, "--json-ignore-key", "RV_CONAN_IDENTITY_FILE")
    check(
        "ignoring that key makes the files compare equal",
        result.returncode == 0,
        result.stdout.strip() + result.stderr.strip(),
    )

    # Reformatting alone must not register as a change.
    write(
        current,
        "CMakePresets.json",
        '{"version": 4, "configurePresets": [{"name": "conan-release", "cacheVariables": {"CMAKE_CXX_STANDARD": "17"}}]}',
    )
    result = run(*args)
    check(
        "reformatting alone is not a difference", result.returncode == 0, result.stdout.strip() + result.stderr.strip()
    )

    # Ignoring a key must not hide a different value elsewhere.
    write(
        current,
        "CMakePresets.json",
        '{\n  "version": 4,\n  "configurePresets": [\n    {\n      "name": "conan-release",\n      "cacheVariables": {\n        "CMAKE_CXX_STANDARD": "20",\n        "RV_CONAN_IDENTITY_FILE": "x"\n      }\n    }\n  ]\n}\n',
    )
    result = run(*args, "--json-ignore-key", "RV_CONAN_IDENTITY_FILE")
    check("ignoring a key does not hide another difference", result.returncode == 2, f"exit {result.returncode}")


def test_conan_cache_churn_is_normalized(directory: str) -> None:
    print("a rebuilt package's folder hash is not a generated-file difference")
    baseline, current = make_trees(os.path.join(directory, "churn"))
    # Rocky 8 forces openexr to be rebuilt on every install, so its package folder hash changes and
    # every generated file mentioning it churns. Left alone, that exempts those files from being
    # compared at all, because the control sees the same churn.
    write(baseline, "OpenEXR.pc", "prefix=/github/home/.conan2/p/b/openeb5948c307c65e/p\n")
    write(current, "OpenEXR.pc", "prefix=/github/home/.conan2/p/b/opene5b2717bf0f54c/p\n")
    write(baseline, "conanrunenv.sh", 'LD_LIBRARY_PATH="/github/home/.conan2/p/openeb5948c307c65e/p/lib"\n')
    write(current, "conanrunenv.sh", 'LD_LIBRARY_PATH="/github/home/.conan2/p/opene5b2717bf0f54c/p/lib"\n')

    args = base_args(baseline, current)
    result = run(*args)
    check(
        "un-normalized package folder churn looks like a difference",
        result.returncode == 2,
        f"exit {result.returncode}",
    )

    result = run(*args, "--normalize-regex", r"/\.conan2/p/(?:b/)?[^/\"]+/p=<PKG>")
    check(
        "normalizing the cache folder makes it equal",
        result.returncode == 0,
        result.stdout.strip() + result.stderr.strip(),
    )

    # Normalizing the cache location must not hide a real content change inside the same file.
    write(current, "OpenEXR.pc", "prefix=/github/home/.conan2/p/b/opene5b2717bf0f54c/p\nLibs: -lSomethingElse\n")
    result = run(*args, "--normalize-regex", r"/\.conan2/p/(?:b/)?[^/\"]+/p=<PKG>")
    check("normalizing the cache does not hide a real change", result.returncode == 2, f"exit {result.returncode}")

    missing_equals = run(*args, "--normalize-regex", "no-equals-sign")
    check(
        "a malformed normalization is an error, not a silent pass",
        missing_equals.returncode == 4,
        f"exit {missing_equals.returncode}",
    )


def test_workflow_invocation_matches_the_script(directory: str) -> None:
    """Guard the seam between the workflow's shell and this script's argument list.

    Three attempts in a row got this wrong in three different ways -- a missing fourth directory, a
    backslash-n where bash needed a line continuation, and a silently unmatched edit -- and each
    cost an hour of CI. The failure is cheap to detect statically, so it is detected here instead.
    """
    print("the workflow passes the arguments this script expects")
    repo = os.path.dirname(os.path.dirname(HERE))
    workflow = os.path.join(repo, ".github", "workflows", "conan.yml")
    if not os.path.isfile(workflow):
        skip("workflow invocation shape", "conan.yml is not present")
        return

    lines = [
        line for line in open(workflow, encoding="utf-8").read().splitlines() if line.strip().startswith("python3 - ")
    ]
    invocation = [line for line in lines if "generators" in line]
    check("the invocation is a single line with no continuations", len(invocation) == 1, f"found {len(invocation)}")
    if len(invocation) != 1:
        return
    line = invocation[0]

    check(
        "no literal backslash-n, which bash would turn into a stray argument",
        "\\n" not in line,
        "a backslash-n here injects an 'n' argument between each path",
    )
    for name in ("OUT_B1", "OUT_B2", "OUT_B3", "OUT_CURRENT"):
        check(f"{name} is passed as a generator directory", f'"${name}/build/Release/generators"' in line)
    check(
        "four roots are passed alongside the four generator directories",
        line.count('"$OUT_') == 8,
        f"found {line.count(chr(36) + 'OUT_')} OUT_ references",
    )
    check("the heredoc is opened", line.rstrip().endswith("<<'PY'"), line[-20:])

    text = open(workflow, encoding="utf-8").read()
    check(
        "the script guards its own argument count",
        "expected 4 generator directories and 4 roots" in text,
        "without the guard a mismatch fails as 'not enough values to unpack'",
    )


def main() -> int:
    if not os.path.isfile(SCRIPT):
        print(f"compare_conan_generators.py not found at {SCRIPT}", file=sys.stderr)
        return 1

    with tempfile.TemporaryDirectory() as directory:
        test_expected_differences_only(directory)
        test_path_normalization_is_what_makes_it_comparable(directory)
        test_an_unexpected_change_is_a_violation(directory)
        test_a_reordering_is_not_a_difference(directory)
        test_an_unexpected_line_change_is_a_violation(directory)
        test_a_removed_file_is_a_violation(directory)
        test_identical_trees_pass(directory)
        test_json_is_compared_semantically(directory)
        test_conan_cache_churn_is_normalized(directory)
        test_workflow_invocation_matches_the_script(directory)
        test_missing_directory(directory)

    print()
    if SKIPPED:
        print(f"{len(SKIPPED)} check group(s) skipped: {', '.join(SKIPPED)}")
    if FAILURES:
        print(f"{len(FAILURES)} check(s) failed:")
        for failure in FAILURES:
            print(f"  - {failure}")
        return 1
    print("all Conan generator comparison checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
