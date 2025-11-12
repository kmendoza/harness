from pathlib import Path

import yaml

from bqm.utils.logconfig import LogFuzz

logger = LogFuzz.make_logger(__name__)


class EnvRecipeError(Exception):
    pass


class PackageSpec:
    def __init__(self, name: str, version: str | None, build: str | None, channel: str):
        self._name = name
        self._ver = version
        self._build = build
        self._channel = channel

    @staticmethod
    def from_conda_spec(spec: str, channel: str = "conda-forge") -> "PackageSpec":
        name, ver, build = spec.split("=")
        return PackageSpec(name, ver, build, channel)

    def __repr__(self) -> str:
        return f"{self._name} :: {self._ver} :: {self._build} :: {self._channel}"


class EnvRecipe:

    def __init__(self, default_python_version: str = "3.13"):
        """
        python version uneless overriden
        """
        self._py_ver = default_python_version

    def add_conda_file(self, file: Path | str):
        pkgs = CondaFileParser.parse_conda_file(file)
        pass


class CondaFileParser:

    @staticmethod
    def parse_conda_file(file: Path | str) -> list[PackageSpec]:

        fle = Path(file)
        if not fle.exists():
            raise Exception(f"  ❌ File {fle} does not exist")

        with open(fle, "r") as f:
            env = yaml.safe_load(f)

        pkgs = []
        for dep in env.get("dependencies", []):
            if isinstance(dep, dict):
                # Handle pip dependencies
                if "pip" in dep:
                    print("  pip packages:")
                    for pip_pkg in dep["pip"]:
                        print(f"    - {pip_pkg}")
            else:
                ps = PackageSpec.from_conda_spec(dep)
                pkgs.append(ps)
                logger.info(f"conda file spec: {ps}")
        return env
