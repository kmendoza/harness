from pathlib import Path

import yaml

from bqm.utils.logconfig import LogFuzz

logger = LogFuzz.make_logger(__name__)


class EnvRecipeError(Exception):
    pass


class PackageSpec:
    def __init__(self, spec: str, name: str, version: str | None, build: str | None, channel: str):
        self._spec = spec
        self._name = name
        self._ver = version
        self._build = build
        self._channel = channel

    @staticmethod
    def from_conda_spec(spec: str, channel: str = "conda-forge") -> "CondaPackageSpec":
        return CondaPackageSpec(spec, channel)

    @staticmethod
    def from_pip_spec(spec: str, channel: str = "pypi") -> "PipPackageSpec":
        return PipPackageSpec(spec, channel)

    def __repr__(self) -> str:
        return f"{self._name} :: {self._ver} :: {self._build} :: {self._channel}"

    def spec(self) -> str:
        return self._spec

    def channel(self) -> str:
        return self._channel

    def name(self) -> str:
        return self._name

    def version(self) -> str:
        return self._ver

    def build(self) -> str:
        return self._build


class CondaPackageSpec(PackageSpec):
    def __init__(self, spec: str, channel: str):
        name, ver, build = spec.split("=")
        PackageSpec.__init__(self, spec, name, ver, build, channel)


class PipPackageSpec(PackageSpec):
    def __init__(self, spec: str, channel: str):
        name, ver = spec.split("==")
        PackageSpec.__init__(self, spec, name, ver, None, channel)


class EnvRecipe:

    def __init__(self, default_python_version: str = "3.13"):
        """
        python version uneless overriden
        """
        self._py_ver = default_python_version
        self._all_pkgs = []

    def pkgs_by_channel(self):
        pkgs = {}
        for p in pkgs:
            pckg_chnl = p.channel()
            if pckg_chnl in pkgs:
                self._pkgs[pckg_chnl] = []
            self._pkgs[pckg_chnl].append(p)
        return pkgs

    def add_conda_file(self, file: Path | str):
        self._all_pkgs.extend(CondaFileParser.parse_conda_file(file))

    def summarise(self, file: Path | str):
        python_pkg = [p for p in self._all_pkgs if p.name() == "python"]
        if len(python_pkg) > 1:
            raise EnvRecipeError(f"Found more than one python package spec. {python_pkg}")
        if len(python_pkg) < 1:
            self._all_pkgs.append(PackageSpec.from_conda_spec(f"python={self._py_ver}"))


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
                        ps = PackageSpec.from_pip_spec(pip_pkg)
                        pkgs.append(ps)
                        logger.info(f"conda [pip] file spec: {pip_pkg}")
            else:
                ps = PackageSpec.from_conda_spec(dep)
                pkgs.append(ps)
                logger.info(f"conda file spec: {dep}")
        return pkgs
