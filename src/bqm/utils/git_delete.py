# import shutil
# import tempfile
# from pathlib import Path
# from typing import Any

# import git

# from bqm.utils.logconfig import LogFuzz

# logger = LogFuzz.make_logger(__name__)


# class GitOperatorError(Exception):
#     pass


# class GitRepo:
#     def __init__(
#         self,
#         repo_url: str,
#         branch: str = "main",
#         workdir: str | Path | None = None,
#         depth: int | None = None,
#         use_local:bool = False,
#     ):
#         self._repo_url = repo_url
#         self._branch = branch
#         self._work_dir = Path(workdir) if workdir else Path(tempfile.mkdtemp())
#         self._repo_name = repo_url.split("/")[-1].replace(".git", "")
#         self._repo_dir = self._work_dir / self._repo_name
#         self._depth = depth
#         self._cloned = False
#         self.__clone()

#     def __clone(self) -> git.Repo:
#         logger.info(f"checking out repo : {self._repo_url}")

#         self._work_dir.mkdir(parents=True, exist_ok=True)

#         if self._repo_dir.exists():
#             shutil.rmtree(self._repo_dir)

#         try:
#             # Clone the repository using GitPython
#             logger.info(f"cloning {self._repo_url} (branch: {self._branch})")
#             self._repo = git.Repo.clone_from(
#                 url=self._repo_url,
#                 to_path=self._repo_dir.as_posix(),
#                 branch=self._branch,
#                 depth=self._depth,
#             )

#             self._cloned = True

#             logger.info(f"Repository cloned to: {self._repo_dir}")
#             logger.info(f"Current commit: {self._repo.head.commit.hexsha[:8]} - {self._repo.head.commit.message.strip()}")

#             return self._repo

#         except git.exc.GitCommandError as e:
#             raise RuntimeError(f"Failed to clone repository: {e}")
#         except git.exc.InvalidGitRepositoryError as e:
#             raise RuntimeError(f"Invalid Git repository: {e}")
#         except Exception as e:
#             raise RuntimeError(f"Unexpected error during clone: {e}")

#     def __check_local(self):
#         if not self._repo_dir.exists():
#             raise GitOperatorError(f"ERROR. Local repo dir does not exist {self._repo_dir}")
#         if not (self._repo_dir / ".git").exists():
#             raise GitOperatorError(f"ERROR. Local repo dir exists {self._repo_dir} but does not seem to be a git repo.")

#     def local_dir(self) -> Path:
#         self.__check_local()
#         return self._repo_dir

#     def checkout_commit(self, hash: str):
#         self.__check_local()

#         try:
#             self._repo.git.checkout(hash)
#         except Exception as e:
#             logger.warning(f"Could not get repository info: {e}")
#             raise GitOperatorError(f"Could not get repository info: {e}")

#     def info(self) -> dict[str, Any]:
#         self.__check_local()

#         try:
#             info = {
#                 "url": self._repo_url,
#                 "branch": "DETACHED HEAD" if self._repo.head.is_detached else self._repo.active_branch.name,
#                 "commit_hash": self._repo.head.commit.hexsha,
#                 "commit_message": self._repo.head.commit.message.strip(),
#                 "author": str(self._repo.head.commit.author),
#                 "commit_date": self._repo.head.commit.committed_datetime.isoformat(),
#                 "is_dirty": self._repo.is_dirty(),
#                 "untracked_files": self._repo.untracked_files,
#             }

#             return info

#         except Exception as e:
#             logger.warning(f"Could not get repository info: {e}")
#             raise GitOperatorError(f"Could not get repository info: {e}")

#     def print_info(self):
#         inf = self.info()
#         logger.info("+----------------------")
#         logger.info(f"| repo url       : {inf['url']}")
#         logger.info(f"| branch         : {inf['branch']}")
#         logger.info(f"| commit message : {inf['commit_message']}")
#         logger.info(f"| commit hash    : {inf['commit_hash']}")
#         logger.info(f"| commit author  : {inf['author']}")
#         logger.info(f"| commit date    : {inf['commit_date']}")
#         logger.info(f"| dirty          : {inf['is_dirty']}")
#         logger.info(f"| changes        : {inf['untracked_files']}")
#         logger.info("+----------------------")


# if __name__ == "__main__":

#     repo = GitRepo(
#         repo_url="git@github.com:kmendoza/harness_test.git",
#         #repo_url="git@bitbucket.org:bqmrepo/harness.git",
#         workdir="/tmp/",
#     )
#     repo.print_info()
#     repo.checkout_commit("8698792d02ff2f139dd4eb72b5cb5a225c24b29a")
#     repo.print_info()
#     repo.checkout_commit("29e6bb154a36c825f0b7b3ea211f6278aad55517")
#     repo.print_info()
