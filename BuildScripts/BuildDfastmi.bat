@echo off

cd %~dp0
cd..

START /B /WAIT poetry run nuitka ^
 --standalone ^
 --assume-yes-for-downloads ^
 --python-flag=no_site ^
 --python-flag=no_asserts ^
 --python-flag=no_docstrings ^
 --nofollow-import-to=*.tests ^
 --nofollow-import-to=*unittest* ^
 --report=compilation-report.xml ^
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
 --product-version=2024.01 ^
 --product-name="D-FAST Morphological Impact" ^
 --file-description="A Python tool to perform a morphological impact analysis based on a number of D-Flow FM simulations." ^
 --trademarks="All indications and logos of, and references to, \"D-FAST\", \"D-FAST Morphological Impact\" and \"D-FAST MI\" are registered trademarks of Stichting Deltares, and remain the property of Stichting Deltares. All rights reserved." ^
 --copyright="Copyright (C) 2024 Stichting Deltares." ^
 --windows-icon-from-ico=dfastmi/D-FASTMI.png ^
 --include-data-files=dfastmi/Dutch_rivers_v1.ini=dfastmi/Dutch_rivers_v1.ini ^
 --include-data-files=dfastmi/Dutch_rivers_v2.ini=dfastmi/Dutch_rivers_v2.ini ^
 --include-data-files=dfastmi/messages.NL.ini=dfastmi/messages.NL.ini ^
 --include-data-files=dfastmi/messages.UK.ini=dfastmi/messages.UK.ini ^
 --include-data-files=dfastmi/open.png=dfastmi/open.png ^
 --include-data-files=docs/dfastmi_usermanual.pdf=dfastmi/dfastmi_usermanual.pdf ^
 dfastmi

rem end of build