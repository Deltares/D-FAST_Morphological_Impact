@echo off
setlocal EnableDelayedExpansion

set target_root=dfastmi.dist

rem ===============================================
echo Copying the backward compatibility tests ...
set target_compatibility=%target_root%\examples_compatibility
echo Creating %target_compatibility%
mkdir %target_compatibility%

set target=%target_compatibility%\01 - GentseWaard\
echo Copying case to %target%
mkdir "%target%"
rem Using "c01.cf?" instead of "c01.cfg" to make sure that copy prints the name of the file copied
copy "tests\c01 - GendtseWaardNevengeul\c01.cf?" "%target%"
copy "tests\c01 - GendtseWaardNevengeul\*.xyz" "%target%"

set target=%target_compatibility%\02 - DeLymen\
echo Copying case to %target%
mkdir "%target%"
rem Using "c02.cf?" instead of "c02.cfg" to make sure that copy prints the name of the file copied
copy "tests\c02 - DeLymen\c02.cf?" "%target%"
copy "tests\c02 - DeLymen\*.xyz" "%target%"


rem ===============================================
echo.
echo Copying the examples/validation cases ...
xcopy /E examples %target_root%\examples\
