rem Load Proj files, referenced by Nuitka during its build and used by the tool during usage.
cd ..
mkdir dfastmi.dist\proj
copy .venv\Lib\site-packages\pyproj\proj_dir\share\proj\* dfastmi.dist\proj
cd %~dp0