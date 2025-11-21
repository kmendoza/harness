from pathlib import Path
from typing import Sequence

import yaml

from bqm.utils.logconfig import LogFuzz
from bqm.utils.mamba.mambax import Mamba

logger = LogFuzz.make_logger(__name__)


class EnvRecipeError(Exception):
    pass


class NotionalPackage:
    """
    a simplified encapsulation of a package (name/version)
    """

    def __init__(self, name: str, ver: str):
        self._name = name
        self._ver = ver.split(".")

    def name(self) -> str:
        return self._name

    def ver(self) -> Sequence[str]:
        return self._ver

    def __repr__(self) -> str:
        return f"{self._name}::{'.'.join(self._ver)}"


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

    def notional(self) -> str:
        return NotionalPackage(name=self._name, ver=self._ver)

    def __str__(self) -> str:
        return self.spec()


class CondaPackageSpec(PackageSpec):
    def __init__(self, spec: str, channel: str):
        name, ver, build = (spec.split("=") + [None])[:3]
        PackageSpec.__init__(self, spec, name, ver, build, channel)


class PipPackageSpec(PackageSpec):
    def __init__(self, spec: str, channel: str):
        name, ver = spec.split("==")
        PackageSpec.__init__(self, spec, name, ver, None, channel)


class EnvironmentCheckeer:
    """
    evaluate how well the target envirobnment matches the desired environment
    by evaluating lists of respective packge names and versions
    """

    def __init__(
        self,
        target: list[NotionalPackage],
        desired: list[NotionalPackage],
    ):
        self._target = {p.name(): p for p in target}
        self._desired = {p.name(): p for p in desired}
        self.__analyse()
        pass

    def target_sufficient(self) -> bool:
        return False

    def __analyse(self):
        missing = []
        installed = {}
        for n, p in self._desired.items():
            if n in self._target:
                des_ver = p.ver()
                tgt_ver = self._target[n].ver()
                if des_ver == tgt_ver:
                    installed[p] = 0
                elif des_ver < tgt_ver:
                    installed[p] = 1
                else:  # des_ver > tgt_ver
                    installed[p] = -1
            else:
                missing.append(n)
        pass


class EnvRecipe:

    def __init__(
        self,
        name: str,
        path: str | Path | None = None,
        default_python_version: str = "3.13",
    ):
        """
        python version uneless overriden
        """
        self._py_ver = default_python_version
        self._all_pkgs = []
        self._name = name

    def add_conda_file(self, file: Path | str):
        self._all_pkgs.extend(CondaFileParser.parse(file))

    def add_reqs_file(self, file: Path | str):
        self._all_pkgs.extend(PipReqsParser.parse(file))

    def __check_python(self):
        all_pkgs = self._all_pkgs.copy()
        python_pkg = [p for p in all_pkgs if p.name() == "python"]
        if len(python_pkg) > 1:
            raise EnvRecipeError(f"Found more than one python package spec. {python_pkg}")
        if len(python_pkg) < 1:
            # if no python in recipe, addconda spec for default version
            all_pkgs.append(PackageSpec.from_conda_spec(f"python={self._py_ver}"))

        return all_pkgs

    def get_spec_list(self, check_python: bool = False):
        if check_python:
            all_pkgs = self.__check_python()
        else:
            all_pkgs = self._all_pkgs.copy()

        pkgs_by_channel = {}
        for p in all_pkgs:
            pckg_chnl = p.channel()
            if pckg_chnl not in pkgs_by_channel:
                pkgs_by_channel[pckg_chnl] = []
            pkgs_by_channel[pckg_chnl].append(p)
        return pkgs_by_channel

    def create(self):
        if len(self._all_pkgs) < 1:
            logger.warning("WARNING. no packages specified. Creating and empty environment")
        mamba = Mamba()
        if mamba.env_exists(self._name):
            logger.warning(f" 💀 WARNING. Deleting existing environment: {self._name}")
            mamba.remove_env(self._name, waive_safety=True)

        logger.info(f" 🚀 Recreating new empty environment: {self._name}")
        mamba.create_env(self._name)

        pks_by_channel = self.get_spec_list(check_python=True)

        for ch in ["conda-forge", "pypi"]:
            if ch not in pks_by_channel:
                continue
            spcs = pks_by_channel[ch]
            if ch == "conda-forge":
                mamba.install_specs(self._name, spcs, ch)
            elif ch == "pypi":
                mamba.pip_install_specs(self._name, spcs)
            else:
                logger.error(f" ERROR. Unkown channel type: {ch}. This is likely a BUG")

    def verify(self) -> bool:
        mamba = Mamba()
        if not mamba.env_exists(self._name):
            logger.into(f" ⭕ WARNING. Target environment does not exist: {self._name}")

        logger.info(f" 🚀 Target envionment already exists: {self._name}. Matching!")

        installed_pkgs = mamba.list_packages(self._name).packages()
        pks_by_channel = self.get_spec_list(check_python=True)

        ips = [NotionalPackage(n, p.version()) for n, p in installed_pkgs.items()]
        rps = [NotionalPackage(rp.name(), rp.version()) for rp in self._all_pkgs]

        chcker = EnvironmentCheckeer(ips, rps)

        pass


class CondaFileParser:

    @staticmethod
    def parse(file: Path | str) -> list[PackageSpec]:

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
                    logger.info("parsing conda pip section:")
                    for pip_pkg in dep["pip"]:
                        ps = PackageSpec.from_pip_spec(pip_pkg)
                        pkgs.append(ps)
                        logger.info(f"conda [pip] package spec: {pip_pkg}")
            else:
                ps = PackageSpec.from_conda_spec(dep)
                pkgs.append(ps)
                logger.info(f"conda [forge] package spec: {dep}")
        return pkgs


class PipReqsParser:

    @staticmethod
    def parse(file: Path | str) -> list[PackageSpec]:

        fle = Path(file)
        if not fle.exists():
            raise Exception(f"  ❌ File {fle} does not exist")

        with open(fle, "r") as f:
            specs = f.readlines()

        pkgs = []
        for spec in specs:
            ps = PackageSpec.from_pip_spec(spec.strip())
            pkgs.append(ps)
            logger.info(f"pip reqs package spec: {spec}")
        return pkgs
