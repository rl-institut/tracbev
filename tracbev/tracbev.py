import utility


class TracBEV:
    """
    Sets up an object from input scenario.
    :param scenario_name: name of the directory
    :type scenario_name: str
    """

    def __init__(self, scenario_name):
        self.config = utility.parse_data(scenario_name)

    def run(self):
        utility.run_tracbev(self.config)
