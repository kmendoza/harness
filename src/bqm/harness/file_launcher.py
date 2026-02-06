import sys
from pathlib import Path
from typing import Any

from bqm.harness.conf.service_config import ServiceConfig
from bqm.harness.launcher import Launcher
from bqm.utils.entry.runner import EntryPointScanner
from bqm.utils.entry.wrapper import CallableWrapper
from bqm.utils.gitx import GitRepo
from bqm.utils.logconfig import LogFuzz

logger = LogFuzz.make_logger(__name__)


class CallableFileLauncherClassError(Exception):
    pass


class CallableFileLauncherClass(type):

    @classmethod
    def select_entry_point(cls, entry_points: list[type[CallableWrapper]], tgt_entry_pt: str | None):
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
            logger.info("🚀  No Entry point specified. Found __main__!")
            return ep_instances["__main__"]

        if len(entry_points) == 1:
            ep = ep_instances.keys()[0]
            logger.info(f"🚀  No entry point specified. __main__ not found. Found a single entry point: {ep}!")
            return ep_instances[ep]

        raise CallableFileLauncherClassError(f"Expected esactly 1 entry point. got {len(entry_points)} ")

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
            raise CallableFileLauncherClassError(msg)

        src_conf = conf["source"]
        repo = GitRepo(
            repo_url=src_conf["repo"],
            branch=src_conf["branch"],
            workdir=src_conf["workdir"],
            force_offline=True,
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
            raise CallableFileLauncherClassError(
                f"Inferred root source path does not exist: {src_path}. Most likely the root_subfolder "
                f"{subfolder} does not exist within the repo {src_conf['repo']} "
            )

        # insesrt the root of the checked out source into python path
        sys.path.insert(0, checkout_path.as_posix())
        epr = EntryPointScanner()
        _, entry_points = epr.scan(src_path)
        selected_entry_point = cls.select_entry_point(entry_points, target_entry_point)

        logger.info("STARTING target process")
        Launcher(job=selected_entry_point, config=conf)
        logger.info("FINISHED target process")


class FileLauncher(metaclass=CallableFileLauncherClass):
    pass
