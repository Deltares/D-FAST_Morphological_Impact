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
 --include-module=shapely ^
 --include-package=matplotlib ^
 --include-package=netCDF4 ^
 --include-module=geopandas ^
 --include-package-data=geopandas.datasets ^
 --include-module=fiona ^
 --include-data-files=dfastmi/Dutch_rivers_v1.ini=dfastmi/Dutch_rivers_v1.ini ^
 --include-data-files=dfastmi/Dutch_rivers_v2.ini=dfastmi/Dutch_rivers_v2.ini ^
 --include-data-files=dfastmi/messages.NL.ini=dfastmi/messages.NL.ini ^
 --include-data-files=dfastmi/messages.UK.ini=dfastmi/messages.UK.ini ^
 --include-data-files=dfastmi/open.png=dfastmi/open.png ^
 --include-data-files=docs/dfastmi_usermanual.pdf=dfastmi/dfastmi_usermanual.pdf ^
 dfastmi

rem end of build