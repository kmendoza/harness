import shutil
import tempfile
from pathlib import Path
from typing import Any

import git

from bqm.utils.logconfig import make_logger

logger = make_logger(__name__)


class GitOperatorError(Exception):
    pass


class GitRepo:
    def __init__(
        self,
        repo_url: str,
        branch: str = "main",
        workdir: str | Path | None = None,
        depth: int | None = None,
        always_clone: bool = False,
    ):
        self._repo_url = repo_url
        self._branch = branch
        self._work_dir = Path(workdir) if workdir else Path(tempfile.mkdtemp())
        self._repo_name = repo_url.split("/")[-1].replace(".git", "")
        self._repo_dir = self._work_dir / self._repo_name
        self._depth = depth
        self._force_clone = always_clone
        self._cloned = False
        
        if not always_clone:
            self._repo = self.__checkout_or_clone()
        else:
            self._repo = self.__clone()

    def __checkout_or_clone(self) -> git.Repo:
        '''
        If directory exists, check if 
        '''

        logger.info(f"Smart checkout of repo: {self._repo_url}")
        
        self._work_dir.mkdir(parents=True, exist_ok=True)
        
        # Check if repo exists and is valid
        if self._repo_dir.exists() and (self._repo_dir / '.git').exists():
            logger.info(f"Repository exists at {self._repo_dir}")
            
            try:
                
                # Verify remote URL matches
                existing_repo = git.Repo(self._repo_dir)
                if not self.__verify_remote_url(existing_repo):
                    msg = f"❌ Target directory {self._repo_dir} exists but already has another repo checkout - fix manually"
                    logger.warning(msg)
                    raise GitOperatorError(msg)
                
                # Update existing repo
                self._repo = existing_repo
                return self.__update_existing_repo()
                
            except git.InvalidGitRepositoryError:
                msg = f"❌Directory {self._repo_dir} exists but is not a valid git repository - fix manually"
                logger.warning(msg)
                raise GitOperatorError(msg)
        else:
            # Clone fresh
            return self.__clone()

    def __verify_remote_url(self, repo:git.Repo) -> bool:
        """Verify the local repo's remote URL matches expected URL"""
        try:
            if not repo.remotes:
                return False
            
            local_url = repo.remotes.origin.url
            
            # Normalize URLs for comparison (handle .git suffix)
            def normalize_url(url: str) -> str:
                return url.rstrip('/').replace('.git', '')
            
            if normalize_url(local_url) != normalize_url(self._repo_url):
                logger.warning(f"📛 local and remote URL mismatch:")
                logger.warning(f"  local url: {local_url}")
                logger.warning(f"  expeected: {self._repo_url}")
                return False
            
            return True
            
        except Exception as e:
            logger.warning(f"Error verifying remote URL: {e}")
            return False

    def __update_existing_repo(self) -> git.Repo:
        """Update existing repository to latest version"""
        try:
            origin = self._repo.remotes.origin
            
            logger.info(f"Fetching latest changes from remote...")
            origin.fetch()
            
            # Check if desired branch exists locally
            if self._branch not in self._repo.heads:
                logger.info(f"Creating local branch '{self._branch}' to track remote")
                if self._branch in [ref.name.split('/')[-1] for ref in origin.refs]:
                    self._repo.create_head(self._branch, origin.refs[self._branch])
                else:
                    logger.error(f"Branch '{self._branch}' not found on remote")
                    raise GitOperatorError(f"Branch '{self._branch}' does not exist on remote")
            
            # Checkout branch
            self._repo.heads[self._branch].checkout()
            
            # Check if update needed
            local_commit = self._repo.head.commit
            remote_ref = f"origin/{self._branch}"
            
            if remote_ref not in [ref.name for ref in origin.refs]:
                logger.warning(f"Remote branch {remote_ref} not found")
                self._cloned = True
                return self._repo
            
            remote_commit = origin.refs[self._branch].commit
            
            if local_commit.hexsha != remote_commit.hexsha:
                # Check if we can fast-forward
                merge_base = self._repo.merge_base(local_commit, remote_commit)
                
                if merge_base and merge_base[0] == local_commit:
                    logger.info(f"Local branch is behind remote. Pulling changes...")
                    origin.pull(self._branch)
                    logger.info(f"✅ Repository updated successfully")
                    logger.info(f"🚀 Current commit: {self._repo.head.commit.hexsha[:8]} - {self._repo.head.commit.message.strip()}")
                else:
                    logger.warning("Local branch has diverged from remote")
                    logger.warning("⭕ Performing hard reset to remote branch")
                    self._repo.head.reset(remote_commit, index=True, working_tree=True)
                    logger.info("🚀 Repository reset to remote state")
            else:
                logger.info("🚀 Repository is already up-to-date")
            
            self._cloned = True
            return self._repo
            
        except Exception as e:
            logger.error(f"Error updating repository: {e}")
            logger.info("Falling back to fresh clone")
            shutil.rmtree(self._repo_dir)
            return self.__clone()

    def __clone(self) -> git.Repo:
        """Clone repository fresh (original behavior)"""
        logger.info(f"Cloning repo: {self._repo_url}")

        # if repo target directory exists 
        if self._repo_dir.exists():
            # check that this is a git repo and that it matches the repo we are trying to check ou
            repo_config = self._repo_dir /'.git'/'config'
            if repo_config.exists():
                if self.__verify_remote_url(git.Repo(self._repo_dir)):
                    logger.warning(f'Target locataion is already a git repo but url is the same as your target url : {self._repo_url} ')
                    logger.warning(f'⭕ Deleting local repo dir: {self._repo_dir} ')
                    shutil.rmtree(self._repo_dir)
                else:
                    msg = f"❌ Target directory {self._repo_dir} exists but already has another repo checkout - fix manually"
                    logger.warning(msg)
                    raise GitOperatorError(msg)
        else:
            self._work_dir.mkdir(parents=True, exist_ok=True)
    
        try:
            logger.info(f"Cloning {self._repo_url} (branch: {self._branch})")
            self._repo = git.Repo.clone_from(
                url=self._repo_url,
                to_path=self._repo_dir.as_posix(),
                branch=self._branch,
                depth=self._depth,
            )
            
            self._cloned = True

            logger.info(f"✅ Repository cloned to: {self._repo_dir}")
            logger.info(f"🚀 Current commit: {self._repo.head.commit.hexsha[:8]} - {self._repo.head.commit.message.strip()}")

            return self._repo

        except git.exc.GitCommandError as e:
            raise RuntimeError(f"Failed to clone repository: {e}")
        except git.exc.InvalidGitRepositoryError as e:
            raise RuntimeError(f"Invalid Git repository: {e}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error during clone: {e}")

    def __check_local(self):
        """Verify local repository exists and is valid"""
        if not self._repo_dir.exists():
            raise GitOperatorError(f"ERROR. Local repo dir does not exist {self._repo_dir}")
        if not (self._repo_dir / ".git").exists():
            raise GitOperatorError(f"ERROR. Local repo dir exists {self._repo_dir} but does not seem to be a git repo.")

    def force_update(self):
        """Force update from remote (fetch and reset to remote HEAD)"""
        self.__check_local()
        
        try:
            logger.info("Force updating repository...")
            origin = self._repo.remotes.origin
            origin.fetch()
            
            remote_ref = f"origin/{self._branch}"
            if remote_ref in [ref.name for ref in origin.refs]:
                remote_commit = origin.refs[self._branch].commit
                self._repo.head.reset(remote_commit, index=True, working_tree=True)
                logger.info("✓ Repository force updated to remote state")
            else:
                logger.error(f"Remote branch {remote_ref} not found")
                
        except Exception as e:
            logger.error(f"Error force updating: {e}")
            raise GitOperatorError(f"Could not force update: {e}")

    def local_dir(self) -> Path:
        """Get path to local repository directory"""
        self.__check_local()
        return self._repo_dir

    def checkout_commit(self, hash: str):
        """Checkout a specific commit by hash"""
        self.__check_local()

        try:
            logger.info(f"Checking out commit: {hash}")
            self._repo.git.checkout(hash)
        except Exception as e:
            logger.warning(f"Could not checkout commit: {e}")
            raise GitOperatorError(f"Could not checkout commit: {e}")

    def checkout_branch(self, branch: str):
        """Checkout a specific branch"""
        self.__check_local()
        
        try:
            logger.info(f"Checking out branch: {branch}")
            
            if branch in self._repo.heads:
                self._repo.heads[branch].checkout()
            elif f"origin/{branch}" in [ref.name for ref in self._repo.remotes.origin.refs]:
                self._repo.create_head(branch, self._repo.remotes.origin.refs[branch])
                self._repo.heads[branch].checkout()
            else:
                raise GitOperatorError(f"Branch '{branch}' not found locally or on remote")
                
        except Exception as e:
            logger.error(f"Could not checkout branch: {e}")
            raise GitOperatorError(f"Could not checkout branch: {e}")

    def info(self) -> dict[str, Any]:
        """Get detailed repository information"""
        self.__check_local()

        try:
            info = {
                "url": self._repo_url,
                "branch": "DETACHED HEAD" if self._repo.head.is_detached else self._repo.active_branch.name,
                "commit_hash": self._repo.head.commit.hexsha,
                "commit_message": self._repo.head.commit.message.strip(),
                "author": str(self._repo.head.commit.author),
                "commit_date": self._repo.head.commit.committed_datetime.isoformat(),
                "is_dirty": self._repo.is_dirty(),
                "untracked_files": self._repo.untracked_files,
            }

            return info

        except Exception as e:
            logger.warning(f"Could not get repository info: {e}")
            raise GitOperatorError(f"Could not get repository info: {e}")

    def print_info(self):
        """Print formatted repository information"""
        inf = self.info()
        logger.info("+----------------------")
        logger.info(f"| repo url       : {inf['url']}")
        logger.info(f"| branch         : {inf['branch']}")
        logger.info(f"| commit message : {inf['commit_message']}")
        logger.info(f"| commit hash    : {inf['commit_hash']}")
        logger.info(f"| commit author  : {inf['author']}")
        logger.info(f"| commit date    : {inf['commit_date']}")
        logger.info(f"| dirty          : {inf['is_dirty']}")
        logger.info(f"| changes        : {inf['untracked_files']}")
        logger.info("+----------------------")


if __name__ == "__main__":
    # Example with smart update enabled (default)
    repo = GitRepo(
        repo_url="git@github.com:kmendoza/harness_test.git",
        branch="test-branch",
        workdir="/data/tst/",
        always_clone=False,
    )
    repo.print_info()
    
    # Example without smart update (original behavior)
    # repo = GitRepo(
    #     repo_url="git@github.com:kmendoza/harness_test.git",
    #     branch="cleanup_creation",
    #     workdir="/tmp/",
    #     smart_update=False,  # Always clone fresh
    # )
    
    # repo.checkout_commit("8698792d02ff2f139dd4eb72b5cb5a225c24b29a")
    # repo.print_info()
    
    # repo.checkout_commit("29e6bb154a36c825f0b7b3ea211f6278aad55517")
    # repo.print_info()