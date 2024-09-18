@echo off

set target_root = dfastmi.dist

rem ===============================================
echo Copying the backward compatibility tests ...
set target_root = %target_root%\examples_compatibility
mkdir %target_root%

set target = "%target_root%\01 - GentseWaard\"
copy "tests\c01 - GentseWaardNevengeul\c01.cfg" %target%
copy "tests\c01 - GentseWaardNevengeul\*.xyz" %target%

set target = "%target_root%\02 - DeLymen\"
copy "tests\c02 - DeLymen\c02.cfg" %target%
copy "tests\c02 - DeLymen\*.xyz" %target%


rem ===============================================
echo Copying the examples/validation cases ...
xcopy /E examples %target_root%\examples\
