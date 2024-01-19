@echo off

cd %~dp0
cd..

START /B /WAIT poetry run nuitka ^
 --standalone ^
 --assume-yes-for-downloads ^
 --python-flag=no_site ^
 --show-progress ^
 --enable-plugin=pyqt5 ^
 --file-reference-choice=runtime ^
 --include-package=pyproj ^
 --include-package=pyproj.proj_dir ^
 --include-module=shapely ^
 --include-package=matplotlib ^
 --include-package=netCDF4 ^
 --include-module=geopandas ^
 --include-package-data=geopandas.datasets ^
 --include-module=fiona ^
 dfastmi

cd %~dp0
call PostBuild.bat

rem end of build