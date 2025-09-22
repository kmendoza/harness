from typing import Any

from jsonschema import validate


class ConfigParser:
    DEFAULT_HTTP_IFCE = "0.0.0.0"
    DEFAULT_HTTP_PORT = 2222

    @staticmethod
    def validate(config: dict[str, Any]):

        schema = {
            "type": "object",
            "properties": {
                "harness": {
                    "type": "object",
                    "properties": {
                        "interface": {
                            "type": "string",
                            "pattern": "^((25[0-5]|2[0-4][0-9]|1?[0-9]{1,2})\\.){3}(25[0-5]|2[0-4][0-9]|1?[0-9]{1,2})$",
                        },
                        "port": {
                            "type": "integer",
                            "minimum": 1024,
                        },
                    },
                    "required": ["interface", "port"],
                },
            },
        }

        validate(instance=config, schema=schema)

    @staticmethod
    def strip(config: dict[str, Any]) -> dict[str, Any]:
        stripped = config.copy()
        stripped.pop("harness", None)
        stripped.pop("logging", None)
        return stripped

    def __init__(self, config: dict[str, Any]):
        ConfigParser.validate(config)
        self._config = config

    def get_iface(self) -> str:
        """
        ip to bind the server to
        """

        if "harness" not in self._config:
            return ConfigParser.DEFAULT_HTTP_IFCE
        if "interface" not in self._config["harness"]:
            return ConfigParser.DEFAULT_HTTP_IFCE

        return self._config["harness"]["interface"]

    def get_port(self) -> str:
        """
        get port to bind on
        """
        if "harness" not in self._config:
            return ConfigParser.DEFAULT_HTTP_PORT
        if "port" not in self._config["harness"]:
            return ConfigParser.DEFAULT_HTTP_PORT

        return self._config["harness"]["port"]
