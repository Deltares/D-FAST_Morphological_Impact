@echo off

cd %~dp0

call CopyLanguageFile.bat
call CopyDutchRiversFile.bat

rem end of post build