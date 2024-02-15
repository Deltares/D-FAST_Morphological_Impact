from dfastmi.io.Reach import Reach


from typing import List


class Branch():
    name : str
    qlocation : str
    reaches : List[Reach]

    def __init__(self, branch_name : str = "Branch"):
        self.name = branch_name
        self.reaches = []