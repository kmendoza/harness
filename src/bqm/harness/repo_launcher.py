from pathlib import Path
from typing import Any

from bqm.utils.logconfig import init_logging, make_logger
from bqm.utils.gitx import GitRepo
from bqm.harness.conf.service_config import ServiceConfig

logger = make_logger(__name__)


class CallableLauncherClass(type):
    def __call__(
        cls,
        config: dict[str, Any] | Path | str | None = None,
    ) -> int:

        conf = ServiceConfig.get_config(config)

        if "logging" in conf:
            init_logging(conf["logging"])

        src_conf = conf["source"]
        repo = GitRepo(
            repo_url=src_conf["repo"],
            branch=src_conf["branch"],
            workdir=src_conf["workdir"],
        )
        repo.print_info()
        pass


class RepoLauncher(metaclass=CallableLauncherClass):
    pass
