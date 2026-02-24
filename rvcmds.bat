@echo off
REM rvcmds.bat - Thin CMD wrapper that launches PowerShell with rvcmds.ps1
REM Usage: rvcmds.bat
powershell -NoExit -ExecutionPolicy Bypass -Command ". '%~dp0rvcmds.ps1'"
