from dfastmi.batch.DFastUtils import get_progloc


class TestGetProgloc:
    def test_get_program_location(self):
        """
        Get the location of the program.
        """
        assert str(get_progloc()).endswith("dfastmi")
