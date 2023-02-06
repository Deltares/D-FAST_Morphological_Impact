rem Load file 'dfastmi_usermanual.pdf'
rem Resolves the following error: ...\dfastmi_usermanual.pdf' is not recognized as an internal or external command, operable program or batch file.
cd ..
copy docs\dfastmi_usermanual.pdf dfastmi.dist\dfastmi
cd %~dp0