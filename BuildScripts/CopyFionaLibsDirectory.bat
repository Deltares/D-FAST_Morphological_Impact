rem Load Fiona files, referenced by Nuitka during its build and used by the tool during usage.
rem Resolves the following error: ImportError: LoadLibraryExW ''C:\CHECKO~1\D-Fast\MI\D-FAST~1\DFASTM~1.DIS\Fiona'' failed: The specified module could not be found.
cd ..
mkdir dfastmi.dist\fiona.libs
copy .venv\Lib\site-packages\fiona.libs\* dfastmi.dist\fiona.libs
cd %~dp0