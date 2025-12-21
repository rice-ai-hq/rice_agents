import os
import sys
from typing import Any

try:
    import tomllib
except ImportError:
    # Fallback for older python versions if necessary,
    # but project requires >=3.11 so tomllib should be there.
    # Just in case user is on 3.10 and ignored warnings.
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None


class Config:
    _instance = None
    _config: dict[str, Any] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self):
        # Look for rice_agents.toml in current directory
        config_path = os.path.join(os.getcwd(), "rice_agents.toml")
        if os.path.exists(config_path):
            if tomllib:
                try:
                    with open(config_path, "rb") as f:
                        self._config = tomllib.load(f)
                except Exception as e:
                    print(f"Error loading config file: {e}")
            else:
                print(
                    "Warning: tomllib not available (Python < 3.11?). Config file ignored."
                )
        else:
            # Default config
            self._config = {}

    @property
    def data(self) -> dict[str, Any]:
        return self._config

    def get_container_config(self, container_name: str) -> dict[str, Any]:
        containers = self._config.get("containers", {})
        if container_name == "default":
            # merge top level defaults if they exist
            defaults = self._config.get("default_container", {})
            return defaults

        return containers.get(container_name, {})


# Global accessor
config = Config()
