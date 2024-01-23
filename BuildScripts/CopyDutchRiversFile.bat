rem Load file 'Dutch_rivers.ini'
rem Resolves the following error: Unable to load file 'Dutch_rivers.ini'
cd ..
copy dfastmi\Dutch_rivers.ini dfastmi.dist\dfastmi
copy dfastmi\Dutch_rivers_v1.ini dfastmi.dist\dfastmi
cd %~dp0
