
setlocal EnableExtensions DisableDelayedExpansion
rem Set the Miniconda installer file name
set INSTALLER_FILENAME=Miniconda3-latest-Windows-x86_64.exe

rem Download the Miniconda installer
curl -O https://repo.anaconda.com/miniconda/%INSTALLER_FILENAME%

rem Run the installer with silent/unattended installation
CALL %INSTALLER_FILENAME% /S /InstallationType=JustMe /AddToPath=1 /RegisterPython=0 /NoRegistry=1 /NoDesktop=1 /D=%~1

rem Clean up the installer file
del %INSTALLER_FILENAME%
endlocal
