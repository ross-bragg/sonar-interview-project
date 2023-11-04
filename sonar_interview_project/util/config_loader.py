import yaml
from yaml.loader import SafeLoader

class ConfigLoader:
    _environment = "something" # figure out how to do this right
    data = []

    def __init__(self, environment) -> None:
        self._environment = environment
        self.load()
        # validate?

    def load(self) -> dict:
        with open(f'project-config/{self._environment}.yml') as f:
            self.data = yaml.load(f, Loader=SafeLoader)
        return self.data
    
    def get(self, key):
        return self.data[key]