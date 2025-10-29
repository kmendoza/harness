import sys
from pathlib import Path
from typing import Any

from bqm.harness.conf.service_config import ServiceConfig
from bqm.harness.launcher import Launcher
from bqm.utils.entry.runner import EntryPointScanner
from bqm.utils.entry.wrapper import CallableWrapper
from bqm.utils.gitx import GitRepo
from bqm.utils.logconfig import init_logging, make_logger

logger = make_logger(__name__)


class CallableRepoLauncherClassError(Exception):
    pass


class CallableRepoLauncherClass(type):

    @classmethod
    def make_invocation_script(cls, entry_points: list[type[CallableWrapper]], tgt_entry_pt: str | None):
        # def call_in_conda_env(env_name, callable_path, config):
        #     """Returns the result as a Python object (deserializes from JSON)"""
        #     module_path, function_name = callable_path.split(':')
        #     config_json = json.dumps(config)

        #     code = f"""
        # import json
        # from {module_path} import {function_name}

        # config = json.loads('''{config_json}''')
        # result = {function_name}(config)
        # # Return result as JSON
        # print(json.dumps(result))
        # """

        #     result = subprocess.run(
        #         ['conda', 'run', '-n', env_name, 'python', '-c', code],
        #         capture_output=True,
        #         text=True
        #     )

        #     if result.returncode != 0:
        #         raise RuntimeError(f"Error:\n{result.stderr}")

        #     # Parse the JSON result back to Python object
        #     return json.loads(result.stdout.strip())
        pass

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
                pass
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
