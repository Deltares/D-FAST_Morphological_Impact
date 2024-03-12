
from dfastmi.batch.DFastUtils import get_progloc

class Test_DFastUtils():
    class Test_get_progloc():
        def test_get_program_location(self):
            """
            Get the location of the program.
            """
            assert get_progloc() != ""