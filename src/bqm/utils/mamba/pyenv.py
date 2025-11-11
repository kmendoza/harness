from typing import Any

from jsonschema import validate

from bqm.utils.logconfig import LogFuzz
from bqm.utils.mamba.mambax import Mamba

logger = LogFuzz.make_logger(__name__)


class EnvManagerError(Exception):
    pass


class EnvManager:

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
                "create": {
                    "create": "string",
                    "enum": [
                        "never",
                        "always",
                    ],
                },
                "recipe": {
                    "type": "object",
                    "properties": {
                        "conda-file": {
                            "type": "string",
                        },
                        "pip-reqs-file": {
                            "type": "string",
                        },
                        "pkg-list": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "version": {"type": "string"},
                                },
                                "required": ["name"],
                                "additionalProperties": False,
                            },
                        },
                    },
                    "anyOf": [
                        {"required": ["conda-file"]},
                        {"required": ["pip-reqs-file"]},
                        {"required": ["pkg-list"]},
                    ],
                    "additionalProperties": False,
                },
            },
            "required": ["name"],
        }
        validate(instance=self._json, schema=schema)

    def __use_existing_only(self) -> bool:
        return "create" not in self._json or self._json["create"] == "never"

    def install(self):
        mmb = Mamba()
        if self.__use_existing_only():
            env_name = self._json["name"]
            logger.info(f" ⌛  Checking for existing [conda] environment {env_name}")
            if not mmb.env_exists(env_name):
                msg = f" ❌  Required [conda] env {env_name} does not exist"
                logger.error(msg)
                raise EnvManagerError(msg)

            logger.info(f" 🚀  Targeet [conda] environment {env_name} exists")
            pkgs = mmb.list_packages(env=env_name)
            pass
        pass


if __name__ == "__main__":
    logger.info("=== START ===")
    env = EnvManager(
        {
            "name": "htest3",
            "create": "never",
            "recipe": {
                "conda-file": "/home/iztok/work/hwork/harness_test/env/harness_test.yml",
                "pip-reqs-file": "sadf",
                "pkg-list": [],
            },
        },
    )
    env.install()
    logger.info("=== DONE ===")
