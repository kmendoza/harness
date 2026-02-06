import json
from typing import Any

from jsonschema import validate

from bqm.utils.logconfig import LogFuzz

logger = LogFuzz.make_logger(__name__)


class PackageError(Exception):
    pass


class Package:

    def __init__(self, pkg_json: dict[str, Any]):
        self._json = pkg_json

    def name(self) -> str:
        return self._json["name"]

    def version(self) -> str:
        return self._json["version"]

    def v_major(self) -> str:
        return self._json["version"].split["."][0]

    def v_minor(self) -> str:
        return self._json["version"].split["."][1]

    def v_patch(self) -> str:
        return self._json["version"].split["."][2]

    def build(self) -> str:
        return self._json["build_string"]

    def build_number(self) -> str:
        return self._json["build_number"]

    def channel(self) -> str:
        return self._json["channel"]

    def platform(self) -> str:
        return self._json["platform"]

    def is_pip(self) -> bool:
        return self.channel() == "pypi"

    def install_string(self, accuracy: str | None = None) -> str:
        """
        generate package install string to varying degree of precision, from none to build

        """
        eq = "==" if self.is_pip() else "="
        if not accuracy:
            return self.name()
        elif accuracy.lower() == "major":
            return f"{self.name()}{eq}{self.v_major()}"
        elif accuracy.lower() == "minor":
            return f"{self.name()}{eq}{self.v_major()}.{self.v_minor()}"
        elif accuracy.lower() == "patch":
            return f"{self.name()}{eq}{self.version()}"
        elif accuracy.lower() == "build":
            if self.is_pip():
                # pip doesnt support installing builds, go patch level instead
                return self.install_string(accuracy="patch")
            else:
                return f"{self.name()}={self.version()}={self.build()}"
        else:
            raise PackageError(f"incorrect accuracy provided: {accuracy}. Specify any of [None, 'major', 'minor', 'patch', 'build']")

    def __repr__(self) -> str:
        return json.dumps(self._json, indent=2)

    def __str__(self) -> str:
        return json.dumps(self._json)


class PackageList:
    def validate(self, config: dict[str, Any]):
        """
        [
            {
                'base_url': 'https://conda.anaconda.org/conda-forge',
                'build_number': 0,
                'build_string': 'py312hfb8ada1_0',
                'channel': 'conda-forge',
                'dist_name': 'pandas-2.2.0-py312hfb8ada1_0',
                'name': 'pandas',
                'platform': 'linux-64',
                'version': '2.2.0'
            }, ...
        ]
        """

        schema = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                    },
                    "version": {
                        "type": "string",
                    },
                    "base_url": {
                        "type": "string",
                    },
                    "build_number": {
                        "type": "integer",
                    },
                    "build_string": {
                        "type": "string",
                    },
                    "channel": {
                        "type": "string",
                    },
                    "dist_name": {
                        "type": "string",
                    },
                    "platform": {
                        "type": "string",
                    },
                },
                "required": ["base_url", "build_number", "build_string", "channel", "dist_name", "name", "platform", "version"],
            },
        }

        validate(instance=config, schema=schema)

    def __init__(self, package_spec_json: dict[str, Any]):
        self.validate(package_spec_json)
        self._packages = {pck.name(): pck for pck in [Package(p) for p in package_spec_json]}

    def contains(self, package: str) -> bool:
        return package in self._packages

    def all(self) -> list[str]:
        return list(self._packages.keys())

    def get(self, package: str) -> Package:
        if self.contains(package):
            return self._packages[package]
        else:
            raise PackageError(f"Package {package} not present in the pacakge list")

    def packages(self) -> list[Package]:
        return self._packages.copy()
