rem Load Shapely files, referenced by Nuitka during its build and used by the tool during usage.
rem Resolves the following error: ImportError: LoadLibraryExW 'C:\CHECKO~1\D-Fast\MI\D-FAST~1\DFASTM~1.DIS\shapely\lib.pyd' failed: The specified module could not be found.
cd ..
mkdir dfastmi.dist\shapely.libs
copy .venv\Lib\site-packages\shapely.libs\* dfastmi.dist\shapely.libs
cd %~dp0