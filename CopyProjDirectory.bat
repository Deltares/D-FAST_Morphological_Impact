rem File "d:\checkouts\D-FAST\D-FAST_Morphological_Impact\dfastmi.dist\pyproj\datadir.py", line 109, in get_data_dir
rem  pyproj.exceptions.DataDirError: Valid PROJ data directory not found. Either set the path using the environmental variable PROJ_LIB or with `pyproj.datadir.set_data_dir`.
mkdir dfastmi.dist\proj
copy .venv\Lib\site-packages\pyproj\proj_dir\share\proj\* dfastmi.dist\proj