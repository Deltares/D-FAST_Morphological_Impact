rem Load matplotlib files, referenced by Nuitka during its build and used by the tool during usage.
rem Resolves the following error: ImportError: LoadLibraryExW 'C:\CHECKO~1\D-Fast\MI\D-FAST~1\DFASTM~1.DIS\matplotlib\_path.pyd' failed: The specified module could not be found.
cd ..
mkdir dfastmi.dist\matplotlib.libs
copy .venv\Lib\site-packages\matplotlib.libs\* dfastmi.dist\matplotlib.libs
cd %~dp0