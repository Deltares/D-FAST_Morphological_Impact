@echo off

cd %~dp0

START /B /WAIT poetry run nuitka --standalone --python-flag=no_site --show-progress --enable-plugin=pyqt5 --file-reference-choice=runtime dfastmi

call PostBuild.bat

rem end of build