from pathlib import Path

def get_abs_path(rootdir,filename):
        return Path(rootdir / filename).resolve()