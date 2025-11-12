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
                "debug": {
                    "type": "boolean",
                },
                "verify": {
                    "type": "boolean",
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
            "additionalProperties": False,
        }
        validate(instance=self._json, schema=schema)

    def name(self) -> str:
        return self._json["name"]

    def __use_existing_only(self) -> bool:
        return "create" not in self._json or self._json["create"] == "never"

    def __tst_val(self, name: str, value: Any) -> bool:
        return name in self._json and self._json[name] == value

    def __create(self) -> bool:
        return self.__tst_val("create", "always")
        # return "create" in self._json and self._json["create"] == "always"

    def __debug(self) -> bool:
        return self.__tst_val("debug", True)
        # return "debug" in self._json and self._json["debug"]

    def __verify(self) -> bool:
        return self.__tst_val("verify", True)

    def setup(self):
        mmb = Mamba()
        env_name = self.name()
        if self.__use_existing_only():
            logger.info(f" ⌛  Checking for existing [conda] environment {env_name}")
            if not mmb.env_exists(env_name):
                msg = f" ❌  Required [conda] env {env_name} does not exist"
                logger.error(msg)
                raise EnvManagerError(msg)

            logger.info(f" ✅  Targeet [conda] environment {env_name} exists")

            if self.__verify():
                pkgs = mmb.list_packages(env=env_name)
                logger.info(f" ❔  Validating env {env_name} against the recipe")

            if self.__debug():
                logger.info(" 📖 Listing env contents")
                pkgs = mmb.list_packages(env=env_name) if not pkgs else pkgs
                for p_nm in sorted(pkgs.all()):
                    p = pkgs.get(p_nm)
                    logger.info(f"    📘  {p.name()}=={p.version()}: {p.channel()}")

            logger.info(f" 🚀  You are good to go with env {env_name} ")
        elif self.__create():
            pass
        pass


if __name__ == "__main__":
    logger.info("=== START ===")
    env = EnvManager(
        {
            "name": "htest3",
            "create": "never",
            "verify": True,
            "debug": True,
            # "create": "always",
            "recipe": {
                "conda-file": "/home/iztok/work/hwork/harness_test/env/harness_test.yml",
                "pip-reqs-file": "sadf",
                "pkg-list": [],
            },
        },
    )
    env.setup()
    logger.info("=== DONE ===")
