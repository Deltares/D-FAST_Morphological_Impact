@echo off

cd %~dp0
cd..

START /B /WAIT poetry run nuitka --standalone --assume-yes-for-downloads --python-flag=no_site --show-progress --enable-plugin=pyqt5 --file-reference-choice=runtime dfastmi

cd %~dp0
call PostBuild.bat

rem end of build