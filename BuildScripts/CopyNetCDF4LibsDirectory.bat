rem Load netCDF4 files, referenced by Nuitka during its build and used by the tool during usage.
rem Resolves the following error: ImportError: LoadLibraryExW ''C:\CHECKO~1\D-Fast\MI\D-FAST~1\DFASTM~1.DIS\netCDF4\_netCDF4.pyd'' failed: The specified module could not be found.
cd ..
mkdir dfastmi.dist\netCDF4.libs
copy .venv\Lib\site-packages\netCDF4.libs\* dfastmi.dist\netCDF4.libs
cd %~dp0