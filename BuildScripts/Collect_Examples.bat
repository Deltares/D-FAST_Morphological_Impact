@echo off
setlocal EnableDelayedExpansion

set target_root=dfastmi.dist

rem ===============================================
echo Copying the backward compatibility tests ...
set target_compatibility=%target_root%\examples_compatibility
echo Creating %target_compatibility%
mkdir %target_compatibility%

set target=%target_compatibility%\01 - Gendtse Waard\
echo Copying case to %target%
mkdir "%target%"
copy "tests\c01 - GendtseWaardNevengeul\c01*.cfg" "%target%"
copy "tests\c01 - GendtseWaardNevengeul\*.xyz" "%target%"
copy "tests\c01 - GendtseWaardNevengeul\*map.nc" "%target%"

set target=%target_compatibility%\02 - De Lymen\
echo Copying case to %target%
mkdir "%target%"
copy "tests\c02 - DeLymen\c02*.cfg" "%target%"
copy "tests\c02 - DeLymen\*.xyz" "%target%"
set target_subdir=%target%\reference_sds\
mkdir "%target_subdir%"
copy "tests\c02 - DeLymen\reference_sds\*map.nc" "%target_subdir%"
set target_subdir=%target%\variant_sds\
mkdir "%target_subdir%"
copy "tests\c02 - DeLymen\variant_sds\*map.nc" "%target_subdir%"


rem ===============================================
echo.
echo Copying the examples/validation cases ...
xcopy /E examples %target_root%\examples\
