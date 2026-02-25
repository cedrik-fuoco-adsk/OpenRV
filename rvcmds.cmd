@echo off
REM rvcmds.cmd - CMD batch build orchestration for OpenRV on Windows
REM Usage: call rvcmds.cmd          (initialize environment + register aliases)
REM        call rvcmds.cmd __rvXXX  (run a specific command)

setlocal enabledelayedexpansion

REM --- Dispatch if called with a command argument ---
if "%~1" neq "" (
    call :%~1 %2 %3 %4 %5 %6 %7 %8 %9
    exit /b %ERRORLEVEL%
)

REM ============================================================================
REM Initialization (no arguments = first-time setup)
REM ============================================================================
endlocal

set "RV_SCRIPT_HOME=%~dp0"
REM Remove trailing backslash
if "%RV_SCRIPT_HOME:~-1%"=="\" set "RV_SCRIPT_HOME=%RV_SCRIPT_HOME:~0,-1%"

REM --- VFX Platform Selection ---
call :__select_vfx_platform
if errorlevel 1 exit /b 1

REM --- Qt Discovery ---
call :__find_qt

REM --- Defaults ---
if not defined CMAKE_GENERATOR set "CMAKE_GENERATOR=Visual Studio 17 2022"
if not defined CMAKE_WIN_ARCH set "CMAKE_WIN_ARCH=-A x64"
set "RV_TOOLCHAIN=-T v143,version=14.40"
if not defined WIN_PERL set "WIN_PERL=c:/Strawberry/perl/bin"
set "SETUPTOOLS_USE_DISTUTILS=stdlib"

if not defined RV_HOME set "RV_HOME=%RV_SCRIPT_HOME%"
if not defined RV_BUILD_PARALLELISM set "RV_BUILD_PARALLELISM=%NUMBER_OF_PROCESSORS%"

REM --- Register DOSKEY aliases ---
doskey rvenv=call "%~dp0rvcmds.cmd" __rvenv
doskey rvsetup=call "%~dp0rvcmds.cmd" __rvsetup
doskey rvcfg=call "%~dp0rvcmds.cmd" __rvcfg
doskey rvbuild=call "%~dp0rvcmds.cmd" __rvbuild
doskey rvbuildt=call "%~dp0rvcmds.cmd" __rvbuildt $*
doskey rvtest=call "%~dp0rvcmds.cmd" __rvtest
doskey rvmk=call "%~dp0rvcmds.cmd" __rvmk
doskey rvbootstrap=call "%~dp0rvcmds.cmd" __rvbootstrap
doskey rvdebug=call "%~dp0rvcmds.cmd" __rvdebug
doskey rvrelease=call "%~dp0rvcmds.cmd" __rvrelease
doskey rvinst=call "%~dp0rvcmds.cmd" __rvinst
doskey rvrun=call "%~dp0rvcmds.cmd" __rvrun
doskey rvclean=call "%~dp0rvcmds.cmd" __rvclean
doskey rvappdir=call "%~dp0rvcmds.cmd" __rvappdir
doskey rvhomedir=call "%~dp0rvcmds.cmd" __rvhomedir
doskey rverrors=call "%~dp0rvcmds.cmd" __rverrors
doskey rverrsummary=call "%~dp0rvcmds.cmd" __rverrsummary

REM --- Default to Release ---
if "%RV_BUILD_TYPE%"=="Debug" (
    call :__set_debug
) else (
    REM Auto-detect: if _build_debug exists but _build doesn't, default to debug
    if exist "%RV_HOME%\_build_debug" (
        if not exist "%RV_HOME%\_build" (
            call :__set_debug
        ) else (
            call :__set_release
        )
    ) else (
        call :__set_release
    )
)

echo.
echo Please ensure you have installed any required dependencies from docs/build_system/config_windows.md
echo.
echo CMake parameters:
echo   RV_BUILD_PARALLELISM = %RV_BUILD_PARALLELISM%
echo   RV_HOME              = %RV_HOME%
echo   RV_BUILD_DIR         = %RV_BUILD_DIR%
echo   RV_INST_DIR          = %RV_INST_DIR%
echo   CMAKE_GENERATOR      = %CMAKE_GENERATOR%
echo   QT_HOME              = %QT_HOME%
echo   WIN_PERL             = %WIN_PERL%
echo.
echo Use 'rvrelease' (default) or 'rvdebug' to switch between build configurations.
echo Call 'rvbootstrap' if it's your first time building or after calling rvclean.
echo After 'rvbootstrap', use 'rvbuild' or 'rvmk' for incremental builds.
echo.
echo If build fails, use 'rverrsummary' to see error summary or 'rverrors' to view full log.
echo.
exit /b 0

REM ============================================================================
REM Internal: VFX Platform Selection
REM ============================================================================
:__select_vfx_platform
if "%RV_VFX_PLATFORM%"=="CY2023" goto :__vfx_ok
if "%RV_VFX_PLATFORM%"=="CY2024" goto :__vfx_ok
if "%RV_VFX_PLATFORM%"=="CY2025" goto :__vfx_ok
if "%RV_VFX_PLATFORM%"=="CY2026" goto :__vfx_ok

if defined RV_VFX_PLATFORM (
    echo Invalid RV_VFX_PLATFORM: '%RV_VFX_PLATFORM%'. Please choose a valid option.
    set "RV_VFX_PLATFORM="
)

:__vfx_prompt
echo Please select the VFX Platform year to build for:
echo   1^) CY2023
echo   2^) CY2024
echo   3^) CY2025
echo   4^) CY2026
set /p "RV_VFX_CHOICE=Enter a number: "
if "%RV_VFX_CHOICE%"=="1" set "RV_VFX_PLATFORM=CY2023" & goto :__vfx_ok
if "%RV_VFX_CHOICE%"=="2" set "RV_VFX_PLATFORM=CY2024" & goto :__vfx_ok
if "%RV_VFX_CHOICE%"=="3" set "RV_VFX_PLATFORM=CY2025" & goto :__vfx_ok
if "%RV_VFX_CHOICE%"=="4" set "RV_VFX_PLATFORM=CY2026" & goto :__vfx_ok
echo Invalid selection. Please try again.
goto :__vfx_prompt

:__vfx_ok
echo Using VFX Platform: %RV_VFX_PLATFORM%
exit /b 0

REM ============================================================================
REM Internal: Qt Path Discovery
REM ============================================================================
:__find_qt
if defined QT_HOME (
    echo Using Qt installation already set at %QT_HOME%
    exit /b 0
)

echo Searching for Qt installation...

set "QT_SEARCH_PATTERN="
if "%RV_VFX_PLATFORM%"=="CY2026" set "QT_SEARCH_PATTERN=6.8"
if "%RV_VFX_PLATFORM%"=="CY2025" set "QT_SEARCH_PATTERN=6.5"
if "%RV_VFX_PLATFORM%"=="CY2024" set "QT_SEARCH_PATTERN=6.5"
if "%RV_VFX_PLATFORM%"=="CY2023" set "QT_SEARCH_PATTERN=5.15"

REM Search C:\Qt*\<version>*\msvc2019_64
for /d %%R in (C:\Qt*) do (
    for /d %%V in ("%%R\%QT_SEARCH_PATTERN%*") do (
        if exist "%%V\msvc2019_64" (
            set "QT_HOME=%%V\msvc2019_64"
        )
    )
)

if defined QT_HOME (
    echo Found Qt installation at %QT_HOME%
) else (
    echo Error: %RV_VFX_PLATFORM% requires a Qt %QT_SEARCH_PATTERN% installation, but none was found.
    echo Please set QT_HOME to the correct path in your environment variables.
)
exit /b 0

REM ============================================================================
REM Internal: Set build configuration
REM ============================================================================
:__set_release
set "RV_BUILD_TYPE=Release"
set "RV_PATH_SUFFIX="
call :__update_paths
exit /b 0

:__set_debug
set "RV_BUILD_TYPE=Debug"
set "RV_PATH_SUFFIX=_debug"
call :__update_paths
exit /b 0

:__update_paths
set "RV_BUILD_DIR=%RV_HOME%\_build%RV_PATH_SUFFIX%"
set "RV_INST_DIR=%RV_HOME%\_install%RV_PATH_SUFFIX%"
set "RV_APP_DIR=%RV_BUILD_DIR%\stage\app\bin"
exit /b 0

REM ============================================================================
REM Public Commands
REM ============================================================================

:__rvenv
cd /d "%RV_HOME%"
if defined VIRTUAL_ENV (
    call deactivate 2>nul
)
if not exist ".venv" (
    python3 -m venv .venv
)
call .venv\Scripts\activate.bat
exit /b 0

:__rvsetup
call :__rvenv
python3 -m pip install --upgrade -r "%RV_HOME%\requirements.txt"
exit /b %ERRORLEVEL%

:__rvcfg
cd /d "%RV_HOME%"
call :__rvenv
cmake -B "%RV_BUILD_DIR%" -G "%CMAKE_GENERATOR%" %RV_TOOLCHAIN% %CMAKE_WIN_ARCH% -DCMAKE_BUILD_TYPE=%RV_BUILD_TYPE% -DRV_DEPS_QT_LOCATION="%QT_HOME%" -DRV_VFX_PLATFORM=%RV_VFX_PLATFORM% -DRV_DEPS_WIN_PERL_ROOT="%WIN_PERL%"
exit /b %ERRORLEVEL%

:__rvbuildt
call :__rvenv
set "_target=%~1"
if not defined _target (
    echo Usage: rvbuildt ^<target^>
    exit /b 1
)
call :__build_with_errors %_target%
exit /b %ERRORLEVEL%

:__rvbuild
call :__rvenv
call :__build_with_errors main_executable
exit /b %ERRORLEVEL%

:__rvtest
call :__rvenv
ctest --test-dir "%RV_BUILD_DIR%" -C %RV_BUILD_TYPE% --extra-verbose
exit /b %ERRORLEVEL%

:__rvinst
call :__rvenv
cmake --install "%RV_BUILD_DIR%" --prefix "%RV_INST_DIR%" --config %RV_BUILD_TYPE%
exit /b %ERRORLEVEL%

:__rvclean
cd /d "%RV_HOME%"
if defined VIRTUAL_ENV (
    call deactivate 2>nul
)
if exist "%RV_BUILD_DIR%" rmdir /s /q "%RV_BUILD_DIR%"
if exist ".venv" rmdir /s /q ".venv"
echo Cleaned build directory and virtual environment.
exit /b 0

:__rvmk
call :__rvcfg
if errorlevel 1 exit /b %ERRORLEVEL%
call :__rvbuild
exit /b %ERRORLEVEL%

:__rvbootstrap
call :__rvsetup
if errorlevel 1 exit /b %ERRORLEVEL%
call :__rvmk
exit /b %ERRORLEVEL%

:__rvdebug
call :__set_debug
echo Switched to Debug configuration.
echo   RV_BUILD_DIR = %RV_BUILD_DIR%
exit /b 0

:__rvrelease
call :__set_release
echo Switched to Release configuration.
echo   RV_BUILD_DIR = %RV_BUILD_DIR%
exit /b 0

:__rvrun
cd /d "%RV_APP_DIR%"
rv.exe
exit /b %ERRORLEVEL%

:__rvappdir
cd /d "%RV_APP_DIR%"
exit /b 0

:__rvhomedir
cd /d "%RV_HOME%"
exit /b 0

:__rverrors
set "_logfile=%RV_BUILD_DIR%\build_errors.log"
if exist "%_logfile%" (
    more "%_logfile%"
) else (
    echo No build log found at %_logfile%
)
exit /b 0

:__rverrsummary
set "_summaryfile=%RV_BUILD_DIR%\error_summary.txt"
if exist "%_summaryfile%" (
    type "%_summaryfile%"
) else (
    echo No error summary found. Build may have succeeded or not run yet.
)
exit /b 0

REM ============================================================================
REM Internal: Build with error reporting
REM ============================================================================
:__build_with_errors
set "_build_target=%~1"
set "_build_log=%RV_BUILD_DIR%\build_errors.log"
set "_error_summary=%RV_BUILD_DIR%\error_summary.txt"

echo Building target: %_build_target%
echo Build errors will be logged to: %_build_log%
echo.

REM Run cmake build, capturing output to log file
cmake --build "%RV_BUILD_DIR%" --config %RV_BUILD_TYPE% -v --parallel=%RV_BUILD_PARALLELISM% --target %_build_target% > "%_build_log%" 2>&1
set "_exit_code=%ERRORLEVEL%"

REM Show the log output
type "%_build_log%"

if %_exit_code% equ 0 (
    echo.
    echo Build completed successfully!
    if exist "%_error_summary%" del "%_error_summary%"
    exit /b 0
)

echo.
echo ================================================================
echo BUILD FAILED - Error Summary
echo ================================================================
echo.

if exist "%_build_log%" (
    findstr /i /r "error C[0-9]*: error LNK[0-9]*: FAILED: CMake.Error fatal.error:" "%_build_log%" > "%_error_summary%" 2>nul
    if exist "%_error_summary%" (
        for %%A in ("%_error_summary%") do if %%~zA gtr 0 (
            echo Compilation Errors Found:
            echo ----------------------------------------------------------------
            type "%_error_summary%"
            echo ----------------------------------------------------------------
            echo.
            echo Full build log: %_build_log%
            echo Error summary:  %_error_summary%
            exit /b %_exit_code%
        )
    )
    echo Build failed but no specific errors extracted.
    echo Check the full build log: %_build_log%
)

exit /b %_exit_code%
