@echo off

rem Define common paths
set ICONS_SRC=dfastmi
set ICONS_DEST=dfastmi
set LOG_DATA_SRC=dfastmi
set LOG_DATA_DEST=dfastmi
set DOCS_SRC=docs
set DOCS_DEST=dfastmi

rem redirect output and error logs to files when --no-console is specified
if "%1" == "--no-console" (
    set cmd_box_args=--windows-force-stderr-spec=%PROGRAM%logs.txt --windows-force-stdout-spec=%PROGRAM%output.txt --windows-disable-console
) else (
    set cmd_box_args=
)

rem get version number
for /f "tokens=*" %%i in ('poetry version -s') do set VERSION=%%i

echo.
echo Version: %VERSION%
echo.

cd %~dp0
cd..

echo Starting Nuitka build...
echo.

START /B /WAIT python -m nuitka ^
 --standalone ^
 --mingw64 ^
 --assume-yes-for-downloads ^
 --python-flag=no_site ^
 --python-flag=no_asserts ^
 --python-flag=no_docstrings ^
 --nofollow-import-to=*.tests ^
 --enable-plugin=anti-bloat ^
 --report=compilation-report.xml ^
 --show-progress ^
 --enable-plugin=pyqt5 ^
 --file-reference-choice=runtime ^
 --include-package=unittest ^
 --include-package=numpy ^
 --include-package=pyproj ^
 --include-module=shapely ^
 --include-package=matplotlib ^
 --include-package=netCDF4 ^
 --include-package=cftime ^
 --include-module=geopandas ^
 --include-package-data=geopandas.datasets ^
 --include-module=fiona ^
 --company-name=Deltares ^
 --file-version=%VERSION% ^
 --product-version=2026.01 ^
 --product-name="D-FAST Morphological Impact" ^
 --file-description="A Python tool to perform a morphological impact analysis based on a number of D-Flow FM simulations." ^
 --trademarks="All indications and logos of, and references to, \"D-FAST\", \"D-FAST Morphological Impact\" and \"D-FAST MI\" are registered trademarks of Stichting Deltares, and remain the property of Stichting Deltares. All rights reserved." ^
 --copyright="Copyright (C) 2026 Stichting Deltares." ^
 --windows-icon-from-ico=%ICONS_SRC%/D-FASTMI.png ^
 --include-data-files=%LOG_DATA_SRC%/Dutch_rivers_v1.ini=%LOG_DATA_DEST%/Dutch_rivers_v1.ini ^
 --include-data-files=%LOG_DATA_SRC%/Dutch_rivers_v3_config1.ini=%LOG_DATA_DEST%/Dutch_rivers_v3_config1.ini ^
 --include-data-files=%LOG_DATA_SRC%/Dutch_rivers_v3.ini=%LOG_DATA_DEST%/Dutch_rivers_v3.ini ^
 --include-data-files=%LOG_DATA_SRC%/messages.NL.ini=dfastmi/messages.NL.ini ^
 --include-data-files=%LOG_DATA_SRC%/messages.UK.ini=dfastmi/messages.UK.ini ^
 --include-data-files=%LOG_DATA_SRC%/D-FASTMI.png=%ICONS_DEST%/D-FASTMI.png ^
 --include-data-files=%ICONS_SRC%/open.png=%ICONS_DEST%/open.png ^
 --include-data-files=LICENSE.md=LICENSE.md ^
 --include-data-files=%DOCS_SRC%/dfastmi_usermanual.pdf=%DOCS_DEST%/dfastmi_usermanual.pdf ^
 --include-data-files=%DOCS_SRC%/dfastmi_techref.pdf=%DOCS_DEST%/dfastmi_techref.pdf ^
 --include-data-files=%DOCS_SRC%/dfastmi_release_notes.pdf=%DOCS_DEST%/dfastmi_release_notes.pdf ^
 --include-data-files=%DOCS_SRC%/dfastmi_validation.pdf=%DOCS_DEST%/dfastmi_validation.pdf ^
 %cmd_box_args% ^
 dfastmi

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Nuitka build failed with error code %ERRORLEVEL%
    echo.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo Nuitka build completed successfully
echo.

rem include example files into the distribution
echo Collecting example files...
call BuildScripts\Collect_Examples.bat

echo.
echo Build completed successfully!
echo.

rem end of build
