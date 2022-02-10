nuitka --standalone --python-flag=no_site --show-progress --plugin-enable=numpy --plugin-enable=qt-plugins --file-reference-choice=runtime dfastmi
rem pause

rem Unable to load language file 'messages.UK.ini'
mkdir dfastmi.dist\dfastmi
copy dfastmi\messages.*.ini dfastmi.dist\dfastmi
copy dfastmi\*.png dfastmi.dist\dfastmi

rem Unable to load file 'Dutch_rivers.ini'
copy dfastmi\Dutch_rivers.ini dfastmi.dist\dfastmi

rem '...\dfastmi_usermanual.pdf' is not recognized as an internal or external command, operable program or batch file.
copy docs\dfastmi_usermanual.pdf dfastmi.dist\dfastmi