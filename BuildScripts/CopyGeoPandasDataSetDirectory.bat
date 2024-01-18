rem Load geopandas datasets files, referenced by Nuitka during its build and used by the tool during usage.
rem Resolves the following error: File "C:\CHECKO~1\D-Fast\MI\D-FAST~1\DFASTM~1.DIS\geopandas\datasets\__init__.py", line 8, in <module geopandas.datasets> StopIteration
rem this script might not be needed anymore with geopandas > v0.14.2, since it is removed in "https://github.com/geopandas/geopandas/pull/3084" which was pushed on 6th of jan 2023,but v0.14.2 was released on 4th of jan 2023.
cd ..
mkdir dfastmi.dist\geopandas
mkdir dfastmi.dist\geopandas\datasets
copy .venv\Lib\site-packages\geopandas\datasets\* dfastmi.dist\geopandas\datasets
cd %~dp0