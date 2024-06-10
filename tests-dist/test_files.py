import pytest
from pathlib import Path

# dfast binary path relative to root
dfastdir = "dfastmi.dist/"

class Test_files_included:

    @pytest.mark.parametrize(
        "filename",
        [
            "LICENSE.md",
            "dfastmi.exe",
            "dfastmi/dfastmi_usermanual.pdf",
            "dfastmi/D-FASTMI.png",
            "dfastmi/open.png",
            "dfastmi/Dutch_rivers_v1.ini",
            "dfastmi/Dutch_rivers_v3.ini",
            "dfastmi/messages.UK.ini",
        ]
    )
    def test_included(self, filename: str):
        """
        Test whether a specific file is included.
        """
        assert Path(dfastdir + filename).is_file()
