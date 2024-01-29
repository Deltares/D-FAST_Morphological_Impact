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
 --company-name=Deltares ^
 --file-version=3.0.0 ^
 --product-version=2024.01.3.0 ^
 --product-name="D-FAST Morphological Impact" ^
 --file-description="A Python tool to perform a morphological impact analysis based on a number of D-Flow FM simulations." ^
 --trademarks="All indications and logos of, and references to, \"D-FAST\", \"D-FAST Morphological Impact\" and \"D-FAST MI\" are registered trademarks of Stichting Deltares, and remain the property of Stichting Deltares. All rights reserved." ^
 --copyright="Copyright (C) 2020 Stichting Deltares." ^
 dfastmi

cd %~dp0
call PostBuild.bat

rem end of build