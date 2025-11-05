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
from bqm.utils.logconfig import init_logging, make_logger
from bqm.utils.mamba.mambax import Mamba

logger = make_logger(__name__)


class CallableRepoLauncherClassError(Exception):
    pass


class CallableRepoLauncherClass(type):

    @classmethod
    def save_config(cls, cfg: dict[str, Any]) -> Path:
        f = tempfile.NamedTemporaryFile(delete=False)
        with open(f.name, "w") as cfg_file:
            cfg_file.write(json.dumps(cfg))
        return f.name

    @classmethod
    def make_delegated_launcher_script(cls, cfg: dict[str, Any]) -> str:
        cfg_file = CallableRepoLauncherClass.save_config(cfg)
        return f"""
from bqm.harness.file_launcher import FileLauncher
FileLauncher(config="{cfg_file}")
"""

    def __call__(
        cls,
        config: dict[str, Any] | Path | str | None = None,
    ) -> int:

        conf = ServiceConfig.get_config(config)

        if "logging" in conf:
            init_logging(conf["logging"])

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
                # cfg_file = CallableRepoLauncherClass.save_config(config)
                # FileLauncher(config=cfg_file)
                auto_code = cls.make_delegated_launcher_script(conf)
                mamba = Mamba()
                res = mamba.run_code(env=target_env, code=auto_code)
            else:
                raise CallableRepoLauncherClassError("Expecting environment name key (env.name) in config. Not found")
        # # create path to source within the repo
        # subfolder = src_conf.get("src-subfolder", ".")
        # target_file = src_conf["file-to-run"]
        # target_entry_point = src_conf.get("entry-point", None)

        # checkout_path = repo.local_dir() / subfolder
        # src_path = checkout_path / target_file
        # # src_path = Path(src_conf["workdir"]) / 'harness_test' / subfolder / target_file
        # if not src_path.exists():
        #     raise CallableRepoLauncherClassError(
        #         f"Inferred root source path does not exist: {src_path}. Most likely the root_subfolder "
        #         f"{subfolder} does not exist within the repo {src_conf['repo']} "
        #     )

        # # insesrt the root of the checked out source into python path
        # sys.path.insert(0, checkout_path.as_posix())
        # epr = EntryPointScanner()
        # _, entry_points = epr.scan(src_path)
        # selected_entry_point = cls.select_entry_point(entry_points, target_entry_point)

        # logger.info("STARTING target process")
        # Launcher(job=selected_entry_point, config=conf)
        # # selected_entry_point()
        # logger.info("FINISHED target process")


class RepoLauncher(metaclass=CallableRepoLauncherClass):
    pass
