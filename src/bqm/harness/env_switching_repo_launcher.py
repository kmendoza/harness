import json
import sys
import tempfile
from pathlib import Path
from typing import Any

from bqm.harness.conf.service_config import ServiceConfig
from bqm.harness.file_launcher import FileLauncher
from bqm.harness.launcher import Launcher
from bqm.utils.entry.runner import EntryPointScanner
from bqm.utils.entry.wrapper import CallableWrapper
from bqm.utils.gitx import GitRepo
from bqm.utils.logconfig import LogFuzz
from bqm.utils.mamba.mambax import Mamba

logger = LogFuzz.make_logger(__name__)


class CallableRepoLauncherClassError(Exception):
    pass


class CallableEnvSwitchingRepoLauncherClass(type):

    @classmethod
    def save_config(cls, cfg: dict[str, Any]) -> Path:
        f = tempfile.NamedTemporaryFile(delete=False)
        with open(f.name, "w") as cfg_file:
            cfg_file.write(json.dumps(cfg))
        return f.name

    @classmethod
    def make_delegated_launcher_script(cls, cfg: dict[str, Any]) -> tuple[str, str]:
        cfg_file = CallableEnvSwitchingRepoLauncherClass.save_config(cfg)
        return (
            f"""
from bqm.harness.file_launcher import FileLauncher
FileLauncher(config="{cfg_file}")
""",
            cfg_file,
        )

    def __call__(
        cls,
        config: dict[str, Any] | Path | str | None = None,
    ) -> int:

        conf = ServiceConfig.get_config(config)

        if "logging" in conf:
            LogFuzz.init_logging(conf["logging"])
        else:
            LogFuzz.init_logging_default()

        # check out the repo
        if "source" not in conf:
            msg = "ERROR. Expecting 'source' in config"
            logger.error(msg)
            raise CallableRepoLauncherClassError(msg)

        src_conf = conf["source"]
        repo = GitRepo(
            repo_url=src_conf["repo"],
            branch=src_conf["branch"],
            workdir=src_conf["workdir"],
            force_offline=src_conf.get("use-local", "."),
        )
        repo.print_info()

        # create path to source within the repo
        subfolder = src_conf.get("src-subfolder", ".")
        target_file = src_conf["file-to-run"]
        checkout_path = repo.local_dir() / subfolder
        src_path = checkout_path / target_file

        if "env" in conf:
            env_conf = conf["env"]
            if "name" in env_conf:
                target_env = env_conf["name"]
                auto_code, tmp_cfg_file = cls.make_delegated_launcher_script(conf)
                mamba = Mamba()
                res = mamba.run_code(env=target_env, code=auto_code)
                Path(tmp_cfg_file).unlink()
            else:
                raise CallableRepoLauncherClassError("Expecting environment name key (env.name) in config. Not found")
        else:
            FileLauncher(config=config)


class EnvSwitchingRepoLauncher(metaclass=CallableEnvSwitchingRepoLauncherClass):
    """
    Entry point launcher which:
       0. obtains the launch config
       1. checks out or updates the code from repo
       2. creates or verifies the target environment
       3. launches the target file using a python procesws with the required target environment

       Usage: EnvSwitchingRepoLauncher(config) where config is some json containing either the config itself or the config descriptor

    """

    pass
