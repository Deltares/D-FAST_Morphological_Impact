@echo off

cd %~dp0

call CopyLanguageFile.bat
call CopyDutchRiversFile.bat
call CopyUserManualFile.bat
call CopyProjDirectory.bat

rem end of post build