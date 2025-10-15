from pathlib import Path
from typing import Any
import sys

from bqm.utils.logconfig import init_logging, make_logger
from bqm.utils.gitx import GitRepo
from bqm.harness.conf.service_config import ServiceConfig
from bqm.utils.entry.runner import EntryPointScanner
from bqm.utils.entry.wrapper import CallableWrapper

logger = make_logger(__name__)


class CallableRepoLauncherClassError(Exception):
    pass


class CallableRepoLauncherClass(type):

    @classmethod
    def select_entry_point(cls, entry_points: list[type[CallableWrapper]]):
        for ep_type in entry_points:
            ep_instance = ep_type()
            logger.info(f"Found viable entry point : {ep_instance.get_info()}")
        if len(entry_points) < 1:
            raise CallableRepoLauncherClassError(
                f"Inferred root source path does not exist: 1. Most likely the root_subfolder "
            )

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
        # src_path = Path(src_conf["workdir"]) / 'harness_test' / subfolder / target_file
        if not src_path.exists():
            raise CallableRepoLauncherClassError(
                f"Inferred root source path does not exist: {src_path}. Most likely the root_subfolder "
                f"{subfolder} does not exist within the repo {src_conf['repo']} "
            )

        sys.path.insert(0, checkout_path.as_posix())
        epr = EntryPointScanner()
        _, entry_points = epr.scan(src_path)
        ep = cls.select_entry_point(entry_points)

        # ep = EntryPointParser()
        # ep.analyze_and_prepare("/home/iztok/work/trading/harness/tests/dynamic_launcher/arbitrary_function.py")

        pass


class RepoLauncher(metaclass=CallableRepoLauncherClass):
    pass
