# rvcmds.ps1 - PowerShell build orchestration for OpenRV on Windows
# Usage: . .\rvcmds.ps1

# --- Dot-source guard ---
if ($MyInvocation.InvocationName -ne '.') {
    Write-Warning "This script should be dot-sourced: . .\rvcmds.ps1"
    return
}

$script:SCRIPT_HOME = Split-Path -Parent $MyInvocation.MyCommand.Path

# ============================================================================
# VFX Platform Selection
# ============================================================================

function script:Select-VfxPlatform {
    $validPlatforms = @('CY2023', 'CY2024', 'CY2025', 'CY2026')

    if ($env:RV_VFX_PLATFORM -and $env:RV_VFX_PLATFORM -in $validPlatforms) {
        Write-Host "RV_VFX_PLATFORM already set to $env:RV_VFX_PLATFORM."
        $script:RV_VFX_PLATFORM = $env:RV_VFX_PLATFORM
        return
    }

    if ($env:RV_VFX_PLATFORM) {
        Write-Host "Invalid RV_VFX_PLATFORM: '$env:RV_VFX_PLATFORM'. Please choose a valid option."
        $env:RV_VFX_PLATFORM = $null
    }

    while (-not $script:RV_VFX_PLATFORM) {
        Write-Host "Please select the VFX Platform year to build for:"
        for ($i = 0; $i -lt $validPlatforms.Count; $i++) {
            Write-Host "  $($i + 1)) $($validPlatforms[$i])"
        }
        $choice = Read-Host "Enter a number"
        $idx = 0
        if ([int]::TryParse($choice, [ref]$idx) -and $idx -ge 1 -and $idx -le $validPlatforms.Count) {
            $script:RV_VFX_PLATFORM = $validPlatforms[$idx - 1]
            $env:RV_VFX_PLATFORM = $script:RV_VFX_PLATFORM
            Write-Host "Using VFX Platform: $script:RV_VFX_PLATFORM"
        }
        else {
            Write-Host "Invalid selection. Please try again."
        }
    }
}

Select-VfxPlatform

# ============================================================================
# Windows Defaults
# ============================================================================

$script:CMAKE_GENERATOR = if ($env:CMAKE_GENERATOR) { $env:CMAKE_GENERATOR } else { "Visual Studio 17 2022" }
$script:CMAKE_WIN_ARCH = if ($env:CMAKE_WIN_ARCH) { $env:CMAKE_WIN_ARCH } else { "-A x64" }
$script:RV_TOOLCHAIN = "-T v143,version=14.40"
$script:WIN_PERL = if ($env:WIN_PERL) { $env:WIN_PERL } else { "c:/Strawberry/perl/bin" }
$env:SETUPTOOLS_USE_DISTUTILS = "stdlib"

# ============================================================================
# Qt Path Discovery
# ============================================================================

function script:Find-QtInstallation {
    $qtVersion = switch ($script:RV_VFX_PLATFORM) {
        'CY2026' { '6.8' }
        'CY2025' { '6.5' }
        'CY2024' { '6.5' }
        'CY2023' { '5.15' }
    }

    if (-not $env:QT_HOME) {
        Write-Host "Searching for Qt installation..."

        $searchPattern = switch ($script:RV_VFX_PLATFORM) {
            'CY2026' { '6.8*' }
            { $_ -in 'CY2025', 'CY2024' } { '6.5*' }
            'CY2023' { '5.15*' }
        }

        # Search common Qt install locations
        $found = $null
        foreach ($qtRoot in (Get-ChildItem -Path "C:\" -Filter "Qt*" -Directory -ErrorAction SilentlyContinue)) {
            $candidates = Get-ChildItem -Path $qtRoot.FullName -Filter $searchPattern -Directory -ErrorAction SilentlyContinue |
                Sort-Object Name |
                ForEach-Object {
                    $msvcDir = Join-Path $_.FullName "msvc2019_64"
                    if (Test-Path $msvcDir) { $msvcDir }
                }
            if ($candidates) {
                $found = $candidates | Select-Object -Last 1
            }
        }

        if ($found) {
            $env:QT_HOME = $found
            $script:QT_HOME = $found
            Write-Host "Found Qt $qtVersion installation at $found"
        }
        else {
            Write-Host "Error: $script:RV_VFX_PLATFORM requires a Qt $qtVersion installation, but none was found."
            Write-Host "Could not find required Qt installation. Please set QT_HOME to the correct path in your environment variables."
        }
    }
    else {
        $script:QT_HOME = $env:QT_HOME

        if ($env:QT_HOME -match '6\.8') {
            Write-Host "Using Qt 6.8 installation already set at $env:QT_HOME"
            if ($script:RV_VFX_PLATFORM -ne 'CY2026') {
                Write-Host "Warning: QT_HOME is set to a Qt 6.8 path, but RV_VFX_PLATFORM is $script:RV_VFX_PLATFORM."
            }
        }
        elseif ($env:QT_HOME -match '6\.5') {
            Write-Host "Using Qt 6.5 installation already set at $env:QT_HOME"
            if ($script:RV_VFX_PLATFORM -notin 'CY2024', 'CY2025') {
                Write-Host "Warning: QT_HOME is set to a Qt 6.5 path, but RV_VFX_PLATFORM is $script:RV_VFX_PLATFORM."
            }
        }
        elseif ($env:QT_HOME -match '5\.15') {
            Write-Host "Using Qt 5.15 installation already set at $env:QT_HOME"
            if ($script:RV_VFX_PLATFORM -ne 'CY2023') {
                Write-Host "Warning: QT_HOME is set to a Qt5 path, but RV_VFX_PLATFORM is $script:RV_VFX_PLATFORM."
            }
        }
        else {
            Write-Host "Warning: Could not determine Qt version from path: $env:QT_HOME. Assuming it is compatible."
        }
    }
}

Find-QtInstallation

# ============================================================================
# Script Variables
# ============================================================================

$script:RV_HOME = if ($env:RV_HOME) { $env:RV_HOME } else { $script:SCRIPT_HOME }
$script:RV_BUILD_PARALLELISM = if ($env:RV_BUILD_PARALLELISM) { $env:RV_BUILD_PARALLELISM } else { [Environment]::ProcessorCount }

# Capture current build type before resetting
$script:INIT_BUILD_TYPE = $env:RV_BUILD_TYPE

$script:RV_BUILD_TYPE = ""
$script:RV_BUILD_DIR = ""
$script:RV_INST_DIR = ""
$script:RV_APP_DIR = ""
$script:RV_PATH_SUFFIX = ""

# Deactivate virtual environment if active
if ($env:VIRTUAL_ENV) {
    try { deactivate } catch {}
}

# Save original prompt
if (-not $script:RV_CLEAN_PROMPT) {
    $script:RV_CLEAN_PROMPT = (Get-Item function:prompt -ErrorAction SilentlyContinue).ScriptBlock
}

# ============================================================================
# Internal Helpers
# ============================================================================

function script:Update-RvPaths {
    $script:RV_BUILD_DIR = Join-Path $script:RV_HOME "_build$($script:RV_PATH_SUFFIX)"
    $script:RV_INST_DIR = Join-Path $script:RV_HOME "_install$($script:RV_PATH_SUFFIX)"
    $script:RV_APP_DIR = Join-Path $script:RV_BUILD_DIR "stage\app\bin"
}

function script:Install-PreCommitHooks {
    $gitDir = Join-Path $script:RV_HOME ".git"
    if (-not (Test-Path $gitDir)) { return }

    $hookFile = Join-Path $gitDir "hooks\pre-commit"
    if ((Test-Path $hookFile) -and (Select-String -Path $hookFile -Pattern "pre-commit" -Quiet -ErrorAction SilentlyContinue)) {
        return
    }

    Write-Host "Installing pre-commit hooks..."
    try {
        & pre-commit install 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  Pre-commit hooks installed successfully."
        }
        else {
            Write-Host "  Failed to install pre-commit hooks."
        }
    }
    catch {
        Write-Host "  Failed to install pre-commit hooks."
    }
}

function script:Set-RvPrompt {
    $buildType = $script:RV_BUILD_TYPE
    $buildDir = $script:RV_BUILD_DIR

    function global:prompt {
        $prefix = if ($script:RV_BUILD_TYPE -eq "Debug") { "dbg" } else { "rel" }
        $venvTag = if ($env:VIRTUAL_ENV) { "(.venv) " } else { "" }
        "$prefix $venvTag$($executionContext.SessionState.Path.CurrentLocation)> "
    }
}

function script:Switch-RvConfig {
    if (-not $env:VIRTUAL_ENV) {
        Set-RvPrompt
    }
    else {
        if (Test-Path $script:RV_BUILD_DIR) {
            rvcfg
        }
        else {
            try { deactivate } catch {}
            Set-RvPrompt
        }
    }
}

# ============================================================================
# Build Error Reporting
# ============================================================================

function script:Invoke-RvBuildWithErrors {
    param([string]$Target)

    $buildLog = Join-Path $script:RV_BUILD_DIR "build_errors.log"
    $errorSummary = Join-Path $script:RV_BUILD_DIR "error_summary.txt"

    Write-Host "Building target: $Target"
    Write-Host "Build errors will be logged to: $buildLog"
    Write-Host ""

    # Run cmake build, capturing output
    & cmake --build $script:RV_BUILD_DIR --config $script:RV_BUILD_TYPE -v `
        "--parallel=$($script:RV_BUILD_PARALLELISM)" --target $Target 2>&1 |
        Tee-Object -FilePath $buildLog

    $exitCode = $LASTEXITCODE
    Write-Host ""

    if ($exitCode -eq 0) {
        Write-Host "Build completed successfully!"
        Remove-Item $errorSummary -ErrorAction SilentlyContinue
        return
    }

    Write-Host ""
    Write-Host ("=" * 64)
    Write-Host "BUILD FAILED - Error Summary"
    Write-Host ("=" * 64)
    Write-Host ""

    if (Test-Path $buildLog) {
        $errors = Select-String -Path $buildLog `
            -Pattern '(error C\d+:|error LNK\d+:|: error :|error:|fatal error:|undefined reference|undefined symbol|unresolved external symbol|FAILED:|CMake Error)' |
            Where-Object { $_.Line -notmatch 'warnings being treated as errors' -and $_.Line -notmatch '0 error' } |
            Select-Object -First 50 -ExpandProperty Line

        if ($errors) {
            $errors | Out-File -FilePath $errorSummary -Encoding utf8
            Write-Host "Compilation Errors Found:"
            Write-Host ("-" * 64)
            $errors | ForEach-Object { Write-Host $_ }
            Write-Host ("-" * 64)
            Write-Host ""
            Write-Host "Full build log: $buildLog"
            Write-Host "Error summary:  $errorSummary"
        }
        else {
            Write-Host "Build failed but no specific errors extracted."
            Write-Host "Check the full build log: $buildLog"
            Write-Host ""
            Write-Host "Last 30 lines of build output:"
            Write-Host ("-" * 64)
            Get-Content $buildLog -Tail 30 | ForEach-Object { Write-Host $_ }
            Write-Host ("-" * 64)
        }
    }

    Write-Host ""
    Write-Host "Tips:"
    Write-Host "  - Review the error summary above"
    Write-Host "  - Check full log: Get-Content $buildLog | more"
    Write-Host "  - Search for specific errors: Select-String -Path $buildLog -Pattern 'your_error'"
    Write-Host ("=" * 64)
    Write-Host ""
}

# ============================================================================
# Public Functions
# ============================================================================

function global:rvenv {
    Set-Location $script:RV_HOME

    # Deactivate existing venv
    if ($env:VIRTUAL_ENV) {
        try { deactivate } catch {}
    }

    if (-not (Test-Path ".venv")) {
        python3 -m venv .venv
    }

    . .\.venv\Scripts\Activate.ps1
    Set-RvPrompt
    Install-PreCommitHooks
}

function global:rvsetup {
    rvenv
    & python3 -m pip install --upgrade -r (Join-Path $script:RV_HOME "requirements.txt")
}

function global:rvcfg {
    Set-Location $script:RV_HOME
    rvenv

    $cmakeArgs = @(
        "-B", $script:RV_BUILD_DIR
        "-G", $script:CMAKE_GENERATOR
    )

    # Split compound args so cmake sees them as separate tokens
    $cmakeArgs += $script:RV_TOOLCHAIN -split ' '
    $cmakeArgs += $script:CMAKE_WIN_ARCH -split ' '

    $cmakeArgs += @(
        "-DCMAKE_BUILD_TYPE=$($script:RV_BUILD_TYPE)"
        "-DRV_DEPS_QT_LOCATION=$($script:QT_HOME)"
        "-DRV_VFX_PLATFORM=$($script:RV_VFX_PLATFORM)"
        "-DRV_DEPS_WIN_PERL_ROOT=$($script:WIN_PERL)"
    )

    & cmake @cmakeArgs
}

function global:rvbuildt {
    param([Parameter(Mandatory)][string]$Target)
    rvenv
    Invoke-RvBuildWithErrors -Target $Target
}

function global:rvbuild {
    rvenv
    Invoke-RvBuildWithErrors -Target "main_executable"
}

function global:rvtest {
    rvenv
    & ctest --test-dir $script:RV_BUILD_DIR -C $script:RV_BUILD_TYPE --extra-verbose
}

function global:rvinst {
    rvenv
    & cmake --install $script:RV_BUILD_DIR --prefix $script:RV_INST_DIR --config $script:RV_BUILD_TYPE
}

function global:rvclean {
    Set-Location $script:RV_HOME

    if ($env:VIRTUAL_ENV) {
        try { deactivate } catch {}
    }

    if (Test-Path $script:RV_BUILD_DIR) {
        Remove-Item $script:RV_BUILD_DIR -Recurse -Force
    }
    if (Test-Path ".venv") {
        Remove-Item ".venv" -Recurse -Force
    }

    Set-RvPrompt
}

function global:rvmk {
    rvcfg
    rvbuild
}

function global:rvbootstrap {
    rvsetup
    rvmk
}

function global:rvdebug {
    $script:RV_BUILD_TYPE = "Debug"
    $script:RV_PATH_SUFFIX = "_debug"
    Update-RvPaths
    Switch-RvConfig
}

function global:rvrelease {
    $script:RV_BUILD_TYPE = "Release"
    $script:RV_PATH_SUFFIX = ""
    Update-RvPaths
    Switch-RvConfig
}

function global:rvrun {
    Set-Location $script:RV_APP_DIR
    & .\rv.exe
}

function global:rvappdir { Set-Location $script:RV_APP_DIR }
function global:rvhomedir { Set-Location $script:RV_HOME }

function global:rverrors {
    $logFile = Join-Path $script:RV_BUILD_DIR "build_errors.log"
    if (Test-Path $logFile) {
        Get-Content $logFile | more
    }
    else {
        Write-Host "No build log found at $logFile"
    }
}

function global:rverrsummary {
    $summaryFile = Join-Path $script:RV_BUILD_DIR "error_summary.txt"
    if (Test-Path $summaryFile) {
        Get-Content $summaryFile
    }
    else {
        Write-Host "No error summary found. Build may have succeeded or not run yet."
    }
}

# ============================================================================
# Initialization
# ============================================================================

Update-RvPaths

Write-Host "Please ensure you have installed any required dependencies from docs/build_system/config_windows.md"
Write-Host ""
Write-Host "CMake parameters:"
Write-Host "RV_BUILD_PARALLELISM is $($script:RV_BUILD_PARALLELISM)"
Write-Host "RV_HOME is $($script:RV_HOME)"
Write-Host "RV_BUILD_DIR is $($script:RV_BUILD_DIR)"
Write-Host "RV_INST_DIR is $($script:RV_INST_DIR)"
Write-Host "CMAKE_GENERATOR is $($script:CMAKE_GENERATOR)"
Write-Host "QT_HOME is $($script:QT_HOME)"
Write-Host "WIN_PERL is $($script:WIN_PERL)"
Write-Host ""
Write-Host "To override any of them, set the corresponding environment variable and re-dot-source this script."
Write-Host ""
Write-Host "Use 'rvrelease' (default) or 'rvdebug' to switch between build configurations."
Write-Host "Call 'rvbootstrap' if it's your first time building or after calling rvclean."
Write-Host "After 'rvbootstrap', use 'rvbuild' or 'rvmk' for incremental builds."
Write-Host ""
Write-Host "If build fails, use 'rverrsummary' to see error summary or 'rverrors' to view full log."
Write-Host ""

# Initialize with appropriate build mode
if ($script:INIT_BUILD_TYPE -eq "Debug") {
    rvdebug
}
else {
    $debugBuildDir = Join-Path $script:RV_HOME "_build_debug"
    $releaseBuildDir = Join-Path $script:RV_HOME "_build"
    if ((Test-Path $debugBuildDir) -and -not (Test-Path $releaseBuildDir)) {
        rvdebug
    }
    else {
        rvrelease
    }
}
