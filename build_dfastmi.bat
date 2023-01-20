nuitka --standalone --python-flag=no_site --show-progress --enable-plugin=pyqt5 --file-reference-choice=runtime dfastmi
pause

rem Unable to load language file 'messages.UK.ini'
mkdir dfastmi.dist\dfastmi
copy dfastmi\messages.*.ini dfastmi.dist\dfastmi
copy dfastmi\*.png dfastmi.dist\dfastmi

rem Unable to load file 'Dutch_rivers.ini'
copy dfastmi\Dutch_rivers.ini dfastmi.dist\dfastmi

rem File "d:\checkouts\D-FAST\D-FAST_Morphological_Impact\dfastmi.dist\pyproj\datadir.py", line 109, in get_data_dir
rem  pyproj.exceptions.DataDirError: Valid PROJ data directory not found. Either set the path using the environmental variable PROJ_LIB or with `pyproj.datadir.set_data_dir`.
mkdir dfastmi.dist\proj
copy .venv\Lib\site-packages\pyproj\proj_dir\share\proj\* dfastmi.dist\proj

rem File "d:\checkouts\D-FAST\D-FAST_Morphological_Impact\dfastmi.dist\rtree\core.py", line 126, in <module rtree.core>
rem  OSError: could not find or load spatialindex_c-64.dll
mkdir dfastmi.dist\Library\bin
copy ..\envs\dfastbe\Library\bin\spatialindex* dfastmi.dist\Library\bin

rem File "d:\checkouts\D-FAST\D-FAST_Morphological_Impact\dfastmi.dist\shapely\geos.py", line 60, in load_dll
rem  OSError: Could not find lib geos_c.dll or load any of its variants [].
mkdir dfastmi.dist\shapely\DLLs
copy ..\envs\dfastbe\Library\bin\geos* dfastmi.dist\shapely\DLLs

rem   File "d:\checkouts\D-FAST\D-FAST_Morphological_Impact\dfastmi.dist\geopandas\datasets\__init__.py", line 6, in <module geopandas.datasets>
rem StopIteration
mkdir dfastmi.dist\geopandas\datasets
copy ..\envs\dfastbe\Lib\site-packages\geopandas\datasets\natural* dfastmi.dist\geopandas\datasets

rem File "d:\checkouts\D-FAST\D-FAST_Morphological_Impact\dfastmi.dist\PyQt5\__init__.py", line 33, in find_qt
rem  ImportError: unable to find Qt5Core.dll on PATH
mkdir dfastmi.dist\PyQt5\Qt\bin
copy .venv\Lib\site-packages\PyQt5\Qt5\bin\Qt5Core* dfastmi.dist\PyQt5\Qt\bin

rem '...\dfastmi_usermanual.pdf' is not recognized as an internal or external command, operable program or batch file.
copy docs\dfastmi_usermanual.pdf dfastmi.dist\dfastmi