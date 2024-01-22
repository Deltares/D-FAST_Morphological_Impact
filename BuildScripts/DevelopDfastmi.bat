@echo on
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
GOTO END

:INSTALLCONDA
echo Conda is not installed on this PC.
echo Please install Conda and try again.
SET /P AREYOUSURE=Are you sure you want to install conda now (Y/[N])?
IF /I "%AREYOUSURE%" NEQ "Y" GOTO END
CALL CondaInstall.bat 
SET PATH=%PATH%;%UserProfile%\Miniconda3;%UserProfile%\Miniconda3\Scripts;%UserProfile%\Miniconda3\Library\bin
GOTO START

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
) else (
    echo visual studio code is installed on this PC.

	CALL code --install-extension Cameron.vscode-pytest --force
	CALL code --install-extension donjayamanne.python-environment-manager --force
	CALL code --install-extension hbenl.vscode-test-explorer --force
	CALL code --install-extension littlefoxteam.vscode-python-test-adapter --force
	CALL code --install-extension ms-python.pylint --force
	CALL code --install-extension ms-python.python --force
	CALL code --install-extension ms-python.vscode-pylance --force
	#CALL code --install-extension ms-toolsai.jupyter --force
	#CALL code --install-extension ms-toolsai.jupyter-keymap --force
	#CALL code --install-extension ms-toolsai.jupyter-renderers --force
	#CALL code --install-extension ms-toolsai.vscode-jupyter-cell-tags --force
	#CALL code --install-extension ms-toolsai.vscode-jupyter-slideshow --force
	#CALL code --install-extension ms-vscode.live-server --force
	CALL code --install-extension ms-vscode.test-adapter-converter --force
	CALL code --install-extension ryanluker.vscode-coverage-gutters --force
)

:END
endlocal