# Two upstream defects found while validating this change

Neither is caused by this change and neither is fixed by it. They are recorded because each cost
time during validation by failing in a way that pointed somewhere else, and both are the same
defect: **a failed network fetch that is masked, so it surfaces later as an unrelated error**.

## 1. breakpad's `linux-syscall-support` clone is masked by `|| true`

`cmake/dependencies/breakpad.cmake:94-95`

```cmake
PATCH_COMMAND git clone https://github.com/google/googletest.git ${_source_dir}/src/testing || true
COMMAND git clone https://chromium.googlesource.com/linux-syscall-support ${_source_dir}/src/third_party/lss || true
```

breakpad is downloaded as `github.com/google/breakpad/archive/<tag>.tar.gz`, and a GitHub source
archive never contains submodules, so `third_party/lss` has to be cloned separately. When that clone
fails — it comes from `chromium.googlesource.com`, a different host from every other dependency — the
`|| true` discards the failure, and the build then dies somewhere else entirely:

```text
breakpad-v2024.02.16/src/common/memory_allocator.h:49:10: fatal error:
third_party/lss/linux_syscall_support.h: No such file or directory
```

Observed on Rocky Linux 8 in the Conan workflow, in `Build OpenRV main executable`, after the
generated-file comparison had already passed.

**Suggested fix:** the `|| true` is presumably there because `PATCH_COMMAND` can run again over an
existing source tree, where `git clone` fails with "destination path already exists". Keep tolerating
*that* case, then assert the header is present, so a genuine fetch failure fails at the fetch:

```cmake
COMMAND sh -c "test -d ${_source_dir}/src/third_party/lss || git clone --depth=1 https://chromium.googlesource.com/linux-syscall-support ${_source_dir}/src/third_party/lss"
COMMAND test -f ${_source_dir}/src/third_party/lss/linux_syscall_support.h
```

## 2. The pyenv installer's fetch is masked by the pipeline

`.github/workflows/conan.yml:185-192`

```yaml
      - name: Install pyenv
        run: |
          curl https://pyenv.run | bash

          export PYENV_ROOT="$HOME/.pyenv"
          echo "$PYENV_ROOT/shims" >> $GITHUB_PATH
          echo "$PYENV_ROOT/bin" >> $GITHUB_PATH
```

The step sets no `pipefail`, so the pipeline reports `bash`'s exit status and a failed `curl` is
invisible: the step succeeds, having added `$HOME/.pyenv/bin` to `PATH` while nothing installed
pyenv into it. The next step then fails with exit 127, on a line that names neither the fetch nor
the host:

```text
/github/home/.pyenv/bin:/github/home/.pyenv/shims:/opt/rh/gcc-toolset-11/root/usr/bin:...
/__w/_temp/....sh: line 2: pyenv: command not found
##[error]Process completed with exit code 127.
```

Observed on Rocky Linux 8 in run 38281461266, and earlier in the same job as
`curl: (6) Could not resolve host: pyenv.run`.

**Suggested fix:** fail in the step that fetched, and say what was expected to exist:

```yaml
      - name: Install pyenv
        run: |
          set -euo pipefail
          curl -fsSL https://pyenv.run | bash
          test -x "$HOME/.pyenv/bin/pyenv"
```

## Also, in Conan itself

`conan/tools/cmake/cmakedeps/templates/config.py` builds the prefixes it renders a generated file's
variable blocks from as `list(set([self.file_name] + prefix_list))`, so the block order follows set
iteration, which CPython randomises per process. `WebPConfig.cmake` therefore swaps its `WebP_*` and
`WEBP_*` blocks on roughly half of installs — 60 fresh processes split 34 to 26 — and two installs of
an unmodified tree disagree, which is why the same tree passed the comparison in one run and failed
in another. `sorted(...)` fixes it.

This one is worked around inside this change rather than only recorded: see D15 in `design.md`.
