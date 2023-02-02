rem Load language file 'messages.UK.ini'
rem Resolves the following error: Unable to load language file 'messages.UK.ini'
cd ..
mkdir dfastmi.dist\dfastmi
copy dfastmi\messages.*.ini dfastmi.dist\dfastmi
copy dfastmi\*.png dfastmi.dist\dfastmi
cd %~dp0