@echo off
REM rvcmds.bat - Redirects to rvcmds.cmd (full CMD batch build orchestration)
REM For PowerShell users: . .\rvcmds.ps1
@call "%~dp0rvcmds.cmd" %*
