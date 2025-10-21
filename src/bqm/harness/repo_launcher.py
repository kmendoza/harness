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
    def select_entry_point(
        cls, entry_points: list[type[CallableWrapper]], tgt_entry_pt: str | None
    ):
        ep_instances = {}
        for ep_type in entry_points:
            ep_instance = ep_type()
            ep_info = ep_instance.get_info()
            ep_instances[ep_info["name"]] = ep_instance
            logger.info(f"➡️  Found viable entry point : {ep_info}")

        # if EP was named and exists, done...
        if tgt_entry_pt in ep_instances:
            logger.info(f"🚀  Looking for entry point {tgt_entry_pt}. Found it!")
            return ep_instances[tgt_entry_pt]

        # if __main__ in entry points ...
        if "__main__" in ep_instances:
            logger.info(f"🚀  No Entry point specified. Found __main__!")
            return ep_instances["__main__"]

        if len(entry_points) == 1:
            ep = ep_instances.keys()[0]
            logger.info(f"🚀  No entry point specified. __main__ not found. Found a single entry point: {ep}!")
            return ep_instances[ep]
        
        raise CallableRepoLauncherClassError(
                f"Expected esactly 1 entry point. got {len(entry_points)} "
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
        target_entry_point = src_conf.get("entry-point", None)

        checkout_path = repo.local_dir() / subfolder
        src_path = checkout_path / target_file
        # src_path = Path(src_conf["workdir"]) / 'harness_test' / subfolder / target_file
        if not src_path.exists():
            raise CallableRepoLauncherClassError(
                f"Inferred root source path does not exist: {src_path}. Most likely the root_subfolder "
                f"{subfolder} does not exist within the repo {src_conf['repo']} "
            )

        # insesrt the root of the checked out source into python path
        sys.path.insert(0, checkout_path.as_posix())
        epr = EntryPointScanner()
        _, entry_points = epr.scan(src_path)
        selected_entry_point  = cls.select_entry_point(entry_points, target_entry_point)

        logger.info('STARTING target process')
        from bqm.harness.launcher import Launcher
        Launcher(job=selected_entry_point, config=conf)
        # selected_entry_point()
        logger.info('FINISHED target process')

class RepoLauncher(metaclass=CallableRepoLauncherClass):
    pass
