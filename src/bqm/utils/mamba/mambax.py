import json
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from bqm.utils.logconfig import make_logger
from bqm.utils.mamba.package import PackageList

logger = make_logger(__name__)


class MambaError(Exception):
    pass


class Mamba:

    def __init__(
        self,
        miniforge_path: str = "/opt/miniforge3",
    ):
        self.__check_miniforge_instl(miniforge_path)
        self._miniforge_path = miniforge_path
        self._rc_file = self.__make_resource_file()
        if not Path(self._rc_file).exists():
            raise MambaError(f"Resrouce file created but does not exist: {self._rc_file}")

        self.test_mamba()
        self.__refresh_env_list()
        pass

    def __check_miniforge_instl(self, mf_path: str):
        """
        do some cursory checks that miniforge exists and looks roughly sensible
        """

        mfp = Path(mf_path)
        if not mfp.exists():
            raise MambaError(f"Specified Miniforge path {mfp} does not exist")

        mfp_bin = mfp / "bin"
        if not mfp_bin.exists():
            raise MambaError(f"bins path {mfp_bin} does not exist")

        mamba_path = mfp_bin / "mamba"
        if not mamba_path.exists():
            raise MambaError(f"Specified mamba path {mamba_path} does not exist")

    def __mamba_exec(
        self, conda_cmd: str, env: str | None = None, capture_output: bool = True, use_conda: bool = False
    ) -> subprocess.CompletedProcess:
        """
        launch a mamba command subprocess
        always load the mamba rc
        if provided, also activate the environment
        optionally use conda (if, e.g. mamba doesnt implement the conda command)
        equivalent of:
            source <rcfile> && activate -n <env> && mamba|conda <mamba_cmd>
        """

        mamba = "mamba" if not use_conda else "conda"
        activate_env = f" && {mamba} activate {env}" if env else ""
        result = subprocess.run(
            ["bash", "-c", f"source {self._rc_file} {activate_env} && {mamba} {conda_cmd}"],
            executable="/bin/bash",
            capture_output=capture_output,
            text=True,
        )
        return result

    def __pip_exec(self, pip_cmd: str, env: str) -> subprocess.CompletedProcess:
        result = subprocess.run(
            ["bash", "-c", f"source {self._rc_file} && mamba activate {env} && pip {pip_cmd}"],
            executable="/bin/bash",
            capture_output=True,
            text=True,
        )
        return result

    def __refresh_env_list(self):
        """
        when adding or deleting envs
        """
        self._existing_envs = self.existing_environments()

    def __as_list(self, strs: str | list[str]):
        if isinstance(strs, str):
            return [strs]
        elif isinstance(strs, list):
            return strs
        else:
            raise MambaError(f"strs must be a string or a list of strings: {strs}")

    def __line_up_packagespecs(
        self,
        package: str | list[str],
        version: str | list[str] | None,
        build: str | list[str] | None,
    ) -> list[tuple[str, str, str]]:
        pkgs = self.__as_list(package)
        if version:
            vers = self.__as_list(version)
            if build:
                blds = self.__as_list(build)
            else:
                blds = [None for x in pkgs]
        else:
            vers = [None for x in pkgs]
            blds = [None for x in pkgs]

        if len(pkgs) == len(vers) == len(blds):
            pkgs = [x.strip() if x else x for x in pkgs]
            vers = [x.strip() if x else x for x in vers]
            blds = [x.strip() if x else x for x in blds]
            return zip(pkgs, vers, blds)
        else:
            raise MambaError(f"Lists must be of same length. You have packages: {len(pkgs)}, versions: {len(vers)} and builds: {len(blds)}")

    def __check_pip_reqs(
        self,
        reqs_file: str | Path | None,
        reqs_str: str | None,
    ) -> str:

        if reqs_str and not reqs_file:
            checked_file = tempfile.mkstemp()
            with open(checked_file, "w") as f:
                f.write(reqs_str)
            return checked_file
        elif not reqs_str and reqs_file:
            checked_file = Path(reqs_file)
            if not checked_file.exists():
                raise MambaError(f"Specified requirements file {reqs_file} does NOT exist?")
            return checked_file.as_posix()
        else:
            raise MambaError(f"Provide reqs file or string, not BOTH. You provided {reqs_str} and {reqs_file} - dont know which one to use.")

    def test_mamba(self):
        """
        verify mamba can be run
        """
        res = self.__mamba_exec("--version")
        if res.returncode != 0:
            raise MambaError("Mamba cannot be called")

    def existing_environments(self) -> list[str]:
        """
        mamba env list
        """
        res = self.__mamba_exec("env list")
        if res.returncode != 0:
            logger.error(res.stderr)
            raise MambaError("Failed to list environemnts")
        return [re.sub("\\ .*$", "", ln) for ln in res.stdout.split("\n") if len(ln) > 0 and not ln.strip().startswith("#")]

    def env_exists(self, env: str) -> bool:
        """
        does a conda environemt already exist
        """
        if env in self._existing_envs:
            return True
        else:
            return False

    def env_has_pip(self, env: str) -> bool:
        """
        check if target env has pip installed
        """
        installed_pkgs = self.list_packages(env)
        return installed_pkgs.contains("pip")

    def create_env(self, env: str, python_version: str | None = None):
        """
        mamba create -n <env>
        """
        if self.env_exists(env):
            raise MambaError(f"Target environment {env} already exists")

        res = self.__mamba_exec(f"create -n {env}")
        if res.returncode != 0:
            logger.error(res.stderr)
            raise MambaError(f"Failed to create environment {env}")

        self.__refresh_env_list()

        if python_version:
            self.install(env=env, package="python", version=python_version)

    def list_packages(self, env: str):
        """
        mamba list -n <env>
        """
        if not self.env_exists(env):
            raise MambaError(f"Target environment {env} does NOT exist")

        cmd = f"list -n {env} --json"

        res = self.__mamba_exec(cmd)
        if res.returncode != 0:
            logger.error(res.stderr)
            raise MambaError(f"Failed to create environment {env}")
        else:
            return PackageList(json.loads(res.stdout))

        # package_lines = [l.split() for l in res.stdout.split("\n") if l.strip() and not l.strip().startswith("#")]
        # return {l[0]: {"package": l[0], "version": l[1], "build": l[2], "channel": l[3]} for l in package_lines}

    def install(
        self,
        env: str,
        package: str | list[str],
        version: str | list[str] | None = None,
        build: str | list[str] | None = None,
        channel: str | None = None,
    ) -> dict[str, Any]:
        """
        mamba install -n <env> -c <channel> [<pacakge>=<version>_<build>]
        """

        def mk_pkg_str(pspec: tuple[str, str, str]) -> str:
            ver_str = f"={pspec[1]}" if pspec[1] else ""
            return f"{pspec[0]}{ver_str}"

        if not self.env_exists(env):
            raise MambaError(f"Target environment {env} does NOT exist")

        pspecs = self.__line_up_packagespecs(package, version, build)

        pck_spec_str = " ".join(mk_pkg_str(p) for p in pspecs)

        channel = f"-c {channel}" if channel else ""
        cmd = f"install -n {env} {channel} {pck_spec_str} -y  --json"

        res = self.__mamba_exec(cmd)

        if res.returncode != 0:
            logger.error(res.stderr)
            raise MambaError(f"Error during pakcage install command: {cmd}")
        else:
            self._last_install_log = json.loads(res.stdout)
            if not self._last_install_log["success"]:
                raise MambaError(f"Error during MAMBA pakcage install command: {cmd}")
            return self._last_install_log

    def run(
        self,
        env: str | None,
        file: str | Path,
    ):
        if not Path(file).exists():
            raise MambaError(f"File {file} does not exist.")

        envv = f"-n {env}" if env else ""
        cmd = f"run {envv} python {file}"

        res = self.__mamba_exec(cmd, capture_output=False)

        if res.returncode != 0:
            raise MambaError(f"Error {res.returncode} while trying to run python file {cmd}")

    def run_code(
        self,
        env: str | None,
        code: str,
    ):

        envv = f"-n {env}" if env else ""
        cmd = f"run {envv} python -c '{code}'"

        res = self.__mamba_exec(cmd, capture_output=False)

        if res.returncode != 0:
            raise MambaError(f"Error {res.returncode} while trying to run python file {cmd}")

    def pip_install(
        self,
        env: str,
        package: str | list[str],
        version: str | list[str] | None = None,
        index_url: str | None = None,
    ) -> str:
        """
        mamba install -n <env> -c <channel> [<pacakge>=<version>_<build>]
        """

        def mk_pkg_str(pspec: tuple[str, str]) -> str:
            ver_str = f"=={pspec[1]}" if pspec[1] else ""
            return f"{pspec[0]}{ver_str}"

        if not self.env_exists(env):
            raise MambaError(f"Target environment {env} does NOT exist")

        installed = self.list_packages(env)
        if "pip" not in installed.all():
            raise MambaError(f"Target environment {env} does not have pip installed. Install first.")

        pspecs = self.__line_up_packagespecs(package, version, None)
        pck_spec_str = " ".join(mk_pkg_str(p) for p in pspecs)

        pkg_index = f"--index-url {index_url}" if index_url else ""

        cmd = f"install {pkg_index} {pck_spec_str} "

        res = self.__pip_exec(cmd, env)

        if res.returncode != 0:
            logger.error(res.stderr)
            raise MambaError(f"Error during PIP pakcage install command: {cmd}")
        else:
            return res.stdout

    def pip_install_reqs(
        self,
        env: str,
        reqs_file: str | Path | None = None,
        reqs_str: str | None = None,
    ) -> str:
        """
        pip install -r <reqs filw> -c <channel> [<pacakge>=<version>_<build>]
        """
        if not self.env_exists(env):
            raise MambaError(f"Target environment {env} does NOT exist")

        checked_file = self.__check_pip_reqs(reqs_file, reqs_str)

        cmd = f"install -r {checked_file}"

        res = self.__pip_exec(cmd, env)

        if res.returncode != 0:
            logger.error(res.stderr)
            raise MambaError(f"Error during PIP pakcage install command: {cmd}")
        else:
            return res.stdout

    def pip_list(self, env: str) -> dict[str, str]:
        """
        pip list
        """
        if not self.env_exists(env):
            raise MambaError(f"Target environment {env} does NOT exist")

        if not self.env_has_pip(env):
            raise MambaError(f"Target environment {env} does not have PIP installed")

        cmd = "list"
        res = self.__pip_exec(cmd, env)

        if res.returncode != 0:
            logger.error(res.stderr)
            raise MambaError(f"Error during PIP pakcage install command: {cmd}")
        else:
            parsed = dict(l.split() for l in res.stdout.split("\n") if l and not l.startswith("------"))
            if "Package" in parsed:
                parsed.pop("Package")

            return parsed

    def pip_verify_reqs(
        self,
        env: str,
        reqs_file: str | Path | None = None,
        reqs_str: str | None = None,
    ) -> bool:
        """
        verify that an environment has requisite reqs installed
        """

        def prs_pkg(ln: str) -> tuple[str, str]:
            """
            parse the pip freeze format, NOT pip list format
            """
            if "==" in ln:
                vals = [v.strip() for v in ln.split("==")]
                return vals[0], vals[1]
            elif "@" in ln:
                return ln.split("@")[0].strip(), None
            else:
                raise Exception(f"Dont know how to interpret requiremets line: {ln}")

        with open(self.__check_pip_reqs(reqs_file, reqs_str), "r") as rf:
            expected_pkgs = dict(prs_pkg(ln.strip()) for ln in rf.readlines() if ln.strip())

        installed_PIP_pkgs = self.pip_list(env)
        for p, v in expected_pkgs.items():
            if p not in installed_PIP_pkgs:
                logger.warning(f"Required package {p} is missing from pip installed packages into env: {env}")
                return False
            if v:
                if not installed_PIP_pkgs[p].startswith(v):
                    logger.warning(f"Required package {p}=={v} has a version mismatch. V {installed_PIP_pkgs[p]} is installed.")
                    return False
        return True

    def remove_env(self, env: str, waive_safety: bool = False):
        """
        mamba env remove -n <env>
        """
        if not waive_safety:
            raise MambaError(f"Dangerous operation - conda environment {env} will be deleted. You must set the 'waive_safety' flag explicitly.")

        if not self.env_exists(env):
            raise MambaError(f"Target environment {env} doesn NOT exist.")

        res = self.__mamba_exec(f"env remove -n {env} -y")
        if res.returncode != 0:
            logger.error(res.stderr)
            raise MambaError(f"Failed to create environment {env}")

        self.__refresh_env_list()

    def __make_resource_file(self) -> str:
        rc_file = tempfile.mktemp()
        with open(rc_file, "w") as f:
            f.write(self.__init_string())
        return rc_file

    def __init_string(self) -> str:
        return f"""
            # >>> conda initialize >>>
            # !! Contents within this block are managed by 'conda init' !!
            __conda_setup="$('{self._miniforge_path}/bin/conda' 'shell.bash' 'hook' 2> /dev/null)"
            if [ $? -eq 0 ]; then
                eval "$__conda_setup"
            else
                if [ -f "{self._miniforge_path}/etc/profile.d/conda.sh" ]; then
                    . "{self._miniforge_path}/etc/profile.d/conda.sh"
                else
                    export PATH="{self._miniforge_path}/bin:$PATH"
                fi
            fi 
            unset __conda_setup

            if [ -f "{self._miniforge_path}/etc/profile.d/mamba.sh" ]; then
                . "{self._miniforge_path}/etc/profile.d/mamba.sh"
            fi
            # <<< conda initialize <<<
        """
