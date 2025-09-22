import json
from pathlib import Path
from typing import Any

from jsonschema import validate

from bqm.utils.logconfig import make_logger
from bqm.utils.consulx import ConsulConfig

logger = make_logger(__name__)


class ServiceConfigError(Exception):
    pass


class ServiceConfig:

    @staticmethod
    def __get_conf_json(config: dict[str, Any] | Path | str) -> dict[str, Any]:
        if isinstance(config, dict):
            # 1. supplied a dict, assume its json
            return config
        elif isinstance(config, str):
            # 2. supplied a string, seems to be a valid path - read json from file
            if Path(config).exists():
                try:
                    return json.load(config)
                except Exception as e:
                    raise ServiceConfigError(f"Path {config} exists but does not contain valid JSON. Load error {e}")
            else:
                # 3. supplied a string, BUT NOT a valid path - assume its json
                try:
                    return json.loads(config)
                except Exception as e:
                    raise ServiceConfigError(
                        f"You passed a string config but the string is neither a valid file path nor a parsable json string : {config}.\n"
                        f"There was an error parsing it: {e}"
                    )
        elif isinstance(config, Path):
            if Path(config).exists():
                try:
                    return json.load(config.as_posix())
                except Exception as e:
                    raise ServiceConfigError(f"Path {config} exists but does not contain valid JSON. Load error {e}")
            else:
                raise ServiceConfigError(f"Config file does not exist: {config}.")
        else:
            raise ServiceConfigError(f"The config object {config} is a valid type (dict, str, PATH, None).")

    @staticmethod
    def validate_consul_descriptor(config: dict[str, Any]):

        schema = {
            "type": "object",
            "properties": {
                "consul": {
                    "type": "object",
                    "properties": {
                        "host": {"type": "string"},
                        "port": {"type": "integer"},
                        "service-config": {"type": "string"},
                    },
                    "required": ["host", "port", "service-config"],
                },
            },
        }

        validate(instance=config, schema=schema)

    @staticmethod
    def is_consul_descriptor(config: dict[str, Any]) -> bool:
        if "consul" in config:
            return True

    @staticmethod
    def load_from_consul(descriptor: dict[str, Any]) -> dict[str, Any]:
        if not ServiceConfig.is_consul_descriptor(descriptor):
            raise ServiceConfigError(f"The descriptor does not seem to be a valid consul config descriptor: {descriptor}")

        ServiceConfig.validate_consul_descriptor(descriptor)

        cc = ConsulConfig(host=descriptor["consul"]["host"], port=descriptor["consul"]["port"])

        return {
            "harness": cc.get_json_value(f'{descriptor["consul"]["service-config"]}/harness'),
            "target-config": cc.get_json_value(f'{descriptor["consul"]["service-config"]}/target-config'),
            "logging": cc.get_json_value(f'{descriptor["consul"]["service-config"]}/logging'),
        }

    @staticmethod
    def get_config(config: dict[str, Any] | Path | str | None = None) -> dict[str, Any]:

        if not config:
            logger.warning("----------")
            logger.warning("No config supplied. Using defaults. NOT SUITABLE FOR PRDUCTION")
            logger.warning("NOT sutiable for production")
            logger.warning("----------")
            return {}

        # get the json config
        json_config = ServiceConfig.__get_conf_json(config)

        # if the json is a consul descriptor, convert
        # the descriptor into actual config json
        if ServiceConfig.is_consul_descriptor(json_config):
            return ServiceConfig.load_from_consul(json_config)
        else:
            return json_config
