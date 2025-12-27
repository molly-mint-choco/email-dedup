import tomllib

class Config:
    def __init__(self) -> None:
        self.CONFIG_FILE_PATH = "settings.toml"
        self._load_config()

    def _load_config(self):
        with open(self.CONFIG_FILE_PATH, "rb") as f:
            self.data = tomllib.load(f)

    def reload(self):
        self._load_config()