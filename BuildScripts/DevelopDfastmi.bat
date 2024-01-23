@echo off
SET CONDA_INSTALL_DIR=%UserProfile%\Miniconda3
SET CONDA_ENV_NAME=py_3_9_12-dfastmi
setlocal EnableExtensions DisableDelayedExpansion

:START
where conda > nul 2>nul
if %errorlevel% neq 0 (
GOTO INSTALLCONDA
) else (
    echo Conda is installed on this PC.
)
GOTO INSTALLENVIRONMENTS
)
GOTO INSTALLEXTENSIONSVSCODE

:INSTALLCONDA
echo Conda is not installed on this PC.
echo Please install Conda and try again.
SET /P AREYOUSURE=Are you sure you want to install conda now (Y/[N])?
IF /I "%AREYOUSURE%" NEQ "Y" GOTO END
CALL %~dp0CondaInstall.bat %CONDA_INSTALL_DIR%
SET PATH=%PATH%;%CONDA_INSTALL_DIR%;%CONDA_INSTALL_DIR%\Scripts;%CONDA_INSTALL_DIR%\Library\bin
CALL conda init --user cmd.exe
echo Please restart script to continue configuration.
echo Conda is installed, but the command prompt will need to be refreshed.
pause
GOTO END

:INSTALLENVIRONMENTS
CALL conda deactivate
CALL conda remove -v -y --name %CONDA_ENV_NAME% --all
CALL conda create -v -y -n %CONDA_ENV_NAME% python=3.9.12
CALL conda activate %CONDA_ENV_NAME%
CALL python -m pip install --upgrade pip
CALL python -m pip install poetry
CALL python -m poetry install --no-root

:INSTALLEXTENSIONSVSCODE
where code > nul 2>nul
if %errorlevel% neq 0 (
    echo visual studio code is not installed on this PC.
    echo Please install visual studio code and try again.
GOTO INSTALLVSCODE
) else (
    echo visual studio code is installed on this PC.

	CALL code --install-extension Cameron.vscode-pytest --force
	CALL code --install-extension donjayamanne.python-environment-manager --force
	CALL code --install-extension hbenl.vscode-test-explorer --force
	CALL code --install-extension littlefoxteam.vscode-python-test-adapter --force
	CALL code --install-extension ms-python.pylint --force
	CALL code --install-extension ms-python.python --force
	CALL code --install-extension ms-python.vscode-pylance --force
	CALL code --install-extension ms-vscode.test-adapter-converter --force
	CALL code --install-extension ryanluker.vscode-coverage-gutters --force
GOTO END
)

:INSTALLVSCODE
SET /P AREYOUSUREVSCODE=Are you sure you want to install conda now (Y/[N])?
IF /I "%AREYOUSUREVSCODE%" NEQ "Y" GOTO END
CALL VSCodeInstall.bat
echo VSCode has been installed on this PC.

:END
endlocal