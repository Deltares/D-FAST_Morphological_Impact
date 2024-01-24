@echo off

cd %~dp0
cd..

START /B /WAIT poetry run nuitka ^
 --standalone ^
 --assume-yes-for-downloads ^
 --python-flag=no_site ^
 --python-flag=no_asserts ^
 --python-flag=no_docstrings ^
 --show-progress ^
 --nofollow-import-to=*.tests ^
 --nofollow-import-to=*test* ^
 --follow-stdlib ^
 --enable-plugin=pyqt5 ^
 --include-package=pyproj ^
 --include-package=shapely ^
 --include-package=netCDF4 ^
 --include-package=geopandas ^
 --include-package-data=geopandas.datasets ^
 --include-package=fiona ^
 --include-data-files=dfastmi/Dutch_rivers.ini=Dutch_rivers.ini ^
 --include-data-files=dfastmi/messages.NL.ini=messages.NL.ini^
 --include-data-files=dfastmi/messages.UK.ini=messages.UK.ini^
 --include-data-files=dfastmi/open.png=open.png^
 --include-data-files=docs/dfastmi_usermanual.pdf=dfastmi_usermanual.pdf^
 --output-dir=dfastmi.install ^
 --company-name=Deltares ^
 --file-version=3.0.0 ^
 --product-version=2024.01.3.0 ^
 --product-name="D-FAST Morphological Impact" ^
 --file-description="A Python to perform a morphological impact analysis based on a number of D-Flow FM simulations." ^
 --trademarks="All indications and logos of, and references to, \"D-FAST\", \"D-FAST Morphological Impact\" and \"D-FAST MI\" are registered trademarks of Stichting Deltares, and remain the property of Stichting Deltares. All rights reserved." ^
 --copyright="Copyright (C) 2020 Stichting Deltares." ^
 --force-dll-dependency-cache-update ^
 dfastmi

cd %~dp0/../dfastmi.install
rem --onefile ^
rem --windows-force-stderr-spec=%PROGRAM%logs.txt ^
rem --windows-force-stdout-spec=%PROGRAM%output.txt ^
rem --verbose ^
rem --verbose-output=buildLog.txt ^
rem --report=compilation-report.xml ^
 
