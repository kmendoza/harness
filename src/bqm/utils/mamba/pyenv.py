from typing import Any

from jsonschema import validate

from bqm.utils.logconfig import LogFuzz

logger = LogFuzz.make_logger(__name__)


class PyEnvError(Exception):
    pass


class PyEnv:

    def __init__(self, env_json: dict[str, Any]):
        self._json = env_json
        self.__validate()

    def __validate(self):
        schema = {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                },
                "build": {
                    "conda-file": {
                        "type": "string",
                    },
                    "pip-reqs-file": {
                        "type": "string",
                    },
                    "pkg-list": [
                        {
                            "type": "object",
                            "properties": {
                                "name": {
                                    "type": "string",
                                },
                                "ver": {
                                    "type": "string",
                                },
                            },
                        }
                    ],
                    "anyOf": [
                        {"required": ["conda-file"]},
                        {"required": ["pip-reqs-file"]},
                        {"required": ["pkg-list"]},
                    ],
                },
            },
            "required": ["name"],
        }
        validate(instance=self._json, schema=schema)

        def use_existing_only(self) -> bool:
            return True


if __name__ == "__main__":
    env = PyEnv(
        {
            "name": "htest3",
            "build": {
                "conda-file": "/a/b/c",
            },
        },
    )
