import json
import consul
from typing import Any
from bqm.utils.logconfig import make_logger

logger = make_logger(__name__)

class ConsulConfigError(Exception):
    pass

class ConsulConfig:
    def __init__(self, host="localhost", port=8500, token=None):
        """
        Initialize Consul client

        Args:
            host: Consul server host
            port: Consul server port
            token: ACL token if authentication is required
        """
        self.client = consul.Consul(host=host, port=port, token=token)

    def get_value(self, key: str) -> str | None:
        """
        Get a single value from Consul KV store

        Args:
            key: The key to retrieve

        Returns:
            The value as a string, or None if key doesn't exist
        """
        try:
            index, data = self.client.kv.get(key)
            if data is None:
                logger.warning(f"Key '{key}' not found")
                return None

            # Consul stores values as base64, but python-consul handles decoding
            return data["Value"].decode("utf-8") if isinstance(data["Value"], bytes) else data["Value"]

        except Exception as e:
            logger.error(f"Error retrieving key '{key}': {e}")
            return None

    def get_json_value(self, key: str) -> dict[Any, Any] | None:
        """
        Get a JSON value from Consul KV store and parse it

        Args:
            key: The key to retrieve

        Returns:
            Parsed JSON as dictionary, or None if key doesn't exist or invalid JSON
        """
        value = self.get_value(key)
        if value is None:
            return None

        try:
            return json.loads(value)
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON for key '{key}': {e}")
            # return None
            raise  ConsulConfigError(f'failed to JSON parse value: {value}')

    def get_all_keys_with_prefix(self, prefix: str) -> dict[str, str]:
        """
        Get all key-value pairs with a given prefix

        Args:
            prefix: The prefix to search for

        Returns:
            Dictionary of key-value pairs
        """
        try:
            index, data = self.client.kv.get(prefix, recurse=True)
            if data is None:
                return {}

            result = {}
            for item in data:
                key = item["Key"]
                value = item["Value"]
                if value is not None:
                    result[key] = value.decode("utf-8") if isinstance(value, bytes) else value

            return result

        except Exception as e:
            logger.error(f"Error retrieving keys with prefix '{prefix}': {e}")
            return {}

    def get_config_section(self, prefix: str, strip_prefix: bool = True) -> dict[str, str]:
        """
        Get configuration section and optionally strip the prefix from keys

        Args:
            prefix: Configuration section prefix (e.g., 'config/myapp/')
            strip_prefix: Whether to remove the prefix from returned keys

        Returns:
            Dictionary of configuration key-value pairs
        """
        all_configs = self.get_all_keys_with_prefix(prefix)

        if not strip_prefix:
            return all_configs

        # Strip prefix from keys
        stripped_configs = {}
        for key, value in all_configs.items():
            if key.startswith(prefix):
                stripped_key = key[len(prefix) :]
                stripped_configs[stripped_key] = value

        return stripped_configs

    def watch_key(self, key: str, callback_func):
        """
        Watch a key for changes (blocking operation)

        Args:
            key: The key to watch
            callback_func: Function to call when key changes
        """
        index = None

        logger.info(f"Watching key '{key}' for changes...")

        while True:
            try:
                # Blocking query - waits until key changes or timeout
                index, data = self.client.kv.get(key, index=index, wait="30s")

                if data is not None:
                    value = data["Value"].decode("utf-8") if isinstance(data["Value"], bytes) else data["Value"]
                    callback_func(key, value)

            except KeyboardInterrupt:
                logger.error("Stopping watch...")
                break
            except Exception as e:
                logger.error(f"Error watching key '{key}': {e}")
                break


def simple_test():
    config = ConsulConfig()

    print("=== Single Key Retrieval ===")
    db_host = config.get_value("config/myapp/database/host")
    print(f"Database host: {db_host}")

    db_port = config.get_value("config/myapp/database/port")
    print(f"Database port: {db_port}")

    print("\n=== JSON Configuration ===")
    app_settings = config.get_json_value("config/myapp/settings")
    if app_settings:
        print(f"App settings: {app_settings}")
        print(f"Debug mode: {app_settings.get('debug', False)}")

    print("\n=== Configuration Section ===")
    db_config = config.get_config_section("config/myapp/database/")
    print("Database configuration:")
    for key, value in db_config.items():
        print(f"  {key}: {value}")

    print("\n=== All Keys with Prefix ===")
    all_app_config = config.get_all_keys_with_prefix("config/myapp/")
    print("All application configuration:")
    for key, value in all_app_config.items():
        print(f"  {key}: {value}")


def watch_test():
    def on_config_change(key, value):
        print(f"Configuration changed - {key}: {value}")
        # Here you could reload your application configuration

    config = ConsulConfig()

    # This will block and watch for changes
    config.watch_key("config/myapp/feature_flags", on_config_change)


if __name__ == "__main__":
    watch_test()
