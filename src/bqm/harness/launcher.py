import asyncio
import sys
from pathlib import Path
from typing import Any, Callable

from bqm.harness.conf.service_config import ServiceConfig
from bqm.harness.cradle import Cradle
from bqm.harness.proc_impl import ProcessHarness
from bqm.utils.logconfig import init_logging, make_logger

logger = make_logger(__name__)


class LauncherError(Exception):
    pass


class CallableLauncherClass(type):
    def __call__(
        cls,
        job: Cradle | Callable,
        config: dict[str, Any] | Path | str | None = None,
        exit_on_completion: bool = False,
    ) -> int:

        conf = ServiceConfig.get_config(config)

        if isinstance(job, Cradle):
            target = job
        elif isinstance(job, Callable):
            target = type("AnonymousCradle", (Cradle,), {"run": job})()
        else:
            raise LauncherError(f"Job must be a Cradle or a Callable. Dont know how to run {type(job)}")

        if "logging" in conf:
            init_logging(conf["logging"])

        target._config = conf.get("target-config", {})

        exit_code = asyncio.run(ProcessHarness(config=conf).main(target))

        if exit_on_completion:
            sys.exit(exit_code)
        else:
            logger.info("Harness finishing without EXIT")
            return exit_code


class Launcher(metaclass=CallableLauncherClass):
    pass
