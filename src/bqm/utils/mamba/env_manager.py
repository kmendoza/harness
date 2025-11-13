from pathlib import Path
from typing import Any

from jsonschema import validate

from bqm.utils.logconfig import LogFuzz
from bqm.utils.mamba.env_recipe import EnvRecipe
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
            "dependentRequired": {
                "verify": ["recipe"],
            },
            "additionalProperties": False,
        }
        validate(instance=self._json, schema=schema)

    def name(self) -> str:
        return self._json["name"]

    def __tst_val(self, name: str, value: Any) -> bool:
        return name in self._json and self._json[name] == value

    def __use_existing_only(self) -> bool:
        # return "create" not in self._json or self._json["create"] == "never"
        return not self.__create()

    def __create(self) -> bool:
        return self.__tst_val("create", "always")

    def __debug(self) -> bool:
        return self.__tst_val("debug", True)

    def __verify(self) -> bool:
        return self.__tst_val("verify", True)

    def __has_recipe(self) -> bool:
        return "recipe" in self._json

    def __get_recipe(self) -> bool:
        if self.__has_recipe():
            return self._json["recipe"]
        else:
            return None

    def __get_conda_file(self) -> Path | None:
        rcp = self.__get_recipe()
        if rcp and "conda-file" in rcp:
            return Path(rcp["conda-file"])
        else:
            return None

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
            mmb = Mamba()
            if mmb.env_exists(env_name):
                pass
            else:
                pass

            # mmb.create_env()
            recipe = EnvRecipe(env_name)
            conda_env_file = self.__get_conda_file()
            if conda_env_file:
                recipe.add_conda_file(conda_env_file)
                pass

            recipe.create()

        pass


if __name__ == "__main__":
    logger.info("=== START ===")
    env = EnvManager(
        {
            "name": "htest3_1",
            # "create": "never",
            "create": "always",
            "verify": True,
            "debug": True,
            "recipe": {
                "conda-file": "/home/iztok/work/hwork/harness_test/env/env_conda_basic.yaml",
                "pip-reqs-file": "sadf",
                "pkg-list": [],
            },
        },
    )
    env.setup()
    logger.info("=== DONE ===")
