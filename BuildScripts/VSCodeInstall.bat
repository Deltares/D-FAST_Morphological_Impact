@echo off
setlocal EnableExtensions DisableDelayedExpansion

rem Set the VS Code installer file name
set INSTALLER_FILENAME=VSCodeSetup.exe

rem Download the VS Code installer
curl -o %INSTALLER_FILENAME% -L "https://code.visualstudio.com/sha/download?build=stable&os=win32-x64-user"

rem Run the installer with unattended installation
start /wait %INSTALLER_FILENAME% /NORESTART

rem Clean up the installer file
del %INSTALLER_FILENAME%

endlocal
