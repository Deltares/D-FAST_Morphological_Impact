from dfastmi.io.Reach import ObservableReachList, Reach


class Branch():
    name : str
    qlocation : str
    reaches : ObservableReachList

    def __init__(self, branch_name : str = "Branch"):
        self.name = branch_name
        self.reaches = ObservableReachList()
        self.reaches.add_observer(self)

    def notify(self, reach:Reach):
        print(f"reach '{reach.name}' with (config_key) index '{reach.config_key_index}' was appended to the reaches list of branch {self.name}.")
        reach.parent_branch_name = self.name
