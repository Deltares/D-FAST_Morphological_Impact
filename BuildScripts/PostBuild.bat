@echo off

cd %~dp0

call CopyLanguageFile.bat
call CopyDutchRiversFile.bat
call CopyUserManualFile.bat
call CopyProjDirectory.bat
call CopyShapelyLibsDirectory.bat
call CopyNetCDF4LibsDirectory.bat
call CopyFionaLibsDirectory.bat
call CopyGeoPandasDataSetDirectory.bat
call CopyMatPlotLibLibsDirectory.bat

rem end of post build