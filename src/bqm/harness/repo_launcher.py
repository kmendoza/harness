from pathlib import Path
from typing import Any
import sys

from bqm.utils.logconfig import init_logging, make_logger
from bqm.utils.git_delete import GitRepo
from bqm.harness.conf.service_config import ServiceConfig
from bqm.utils.entry.parser import EntryPointParser

logger = make_logger(__name__)


class CallableRepoLauncherClassError(Exception):
    pass


class CallableRepoLauncherClass(type):
    def __call__(
        cls,
        config: dict[str, Any] | Path | str | None = None,
    ) -> int:

        conf = ServiceConfig.get_config(config)

        if "logging" in conf:
            init_logging(conf["logging"])

        # check out the repo
        src_conf = conf["source"]
        repo = GitRepo(
            repo_url=src_conf["repo"],
            branch=src_conf["branch"],
            workdir=src_conf["workdir"],
        )
        repo.print_info()

        # create path to source within the repo
        subfolder = src_conf.get("root-subfolder", ".")
        target_file = src_conf['file-to-run']

        checkout_path = repo.local_dir() / subfolder 
        src_path = checkout_path / target_file
        # src_path = Path(src_conf["workdir"]) / 'harness_test' / subfolder / target_file
        if not src_path.exists():
            raise CallableRepoLauncherClassError(
                f"Inferred root source path does not exist: {src_path}. Most likely the root_subfolder {subfolder} does not exist within the repo {src_conf['repo']} "
            )

        sys.path.insert(0, checkout_path.as_posix())
        ep = EntryPointParser()
        analysis = ep.analyze_file(src_path.as_posix())

        pass


class RepoLauncher(metaclass=CallableRepoLauncherClass):
    pass
