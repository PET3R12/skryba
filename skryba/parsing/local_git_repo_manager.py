from structlog.typing import FilteringBoundLogger
from pathlib import Path
from typing import Optional
from git import Repo, GitCommandError
import shutil
import os
import stat


class LocalGitRepoManager:
    def __init__(
        self, repo_url: str, repo_path: Path, logger_instance: FilteringBoundLogger
    ) -> None:
        self.repo_url = repo_url
        self.repo_path = repo_path
        self.logger = logger_instance
        self.repo: Optional[Repo] = None

    def clone_repo(self) -> Repo:
        self.logger.info(
            "Cloning repository", repo_url=self.repo_url, path=str(self.repo_path)
        )
        self.repo_path.parent.mkdir(parents=True, exist_ok=True, mode=0o777)

        if self.repo_path.exists():
            self.logger.info(
                "Removing existing repository before cloning.", path=str(self.repo_path)
            )
            self._remove_repo_internal()

        try:
            self.repo = Repo.clone_from(self.repo_url, self.repo_path)
            if self.repo is None:
                raise RuntimeError(
                    "Cloning finished unexpectedly without creating a repo object."
                )
            self.logger.info(
                "Repository cloned successfully.", path=str(self.repo_path)
            )
            return self.repo
        except GitCommandError as e:
            self.logger.error(
                "Failed to clone repository.", repo_url=self.repo_url, error=str(e)
            )
            raise RuntimeError(f"Failed to clone repository: {e}") from e

    def _handle_remove_error(self, func, path, exc_info) -> None:
        _, exc_value, _ = exc_info
        if isinstance(exc_value, PermissionError):
            try:
                self.logger.warning(
                    "Permission error during removal, attempting to change permissions.",
                    path=path,
                )
                os.chmod(path, stat.S_IWRITE | stat.S_IREAD | stat.S_IEXEC)
                func(path)
            except Exception as e_chmod:
                self.logger.error(
                    "Failed to change permissions or remove file/directory after permission error.",
                    path=path,
                    error=str(e_chmod),
                )
        elif isinstance(exc_value, FileNotFoundError):
            self.logger.info(
                "File/directory not found during removal, likely already deleted.",
                path=path,
            )
        else:
            self.logger.error(
                "Unexpected error during removal.", path=path, error=str(exc_value)
            )

    def _remove_repo_internal(self):
        if self.repo_path.exists():
            try:
                shutil.rmtree(self.repo_path, onerror=self._handle_remove_error)
                self.logger.info(
                    "Repository directory has been removed.", path=str(self.repo_path)
                )
            except Exception as e:
                self.logger.error(
                    "Failed to remove repository directory.",
                    path=str(self.repo_path),
                    error=str(e),
                )
        else:
            self.logger.info(
                "Repository directory does not exist, skipping removal.",
                path=str(self.repo_path),
            )

    def cleanup(self):
        if self.repo:
            repo_to_close = self.repo
            self.repo = None
            try:
                if hasattr(repo_to_close, "git") and hasattr(
                    repo_to_close.git, "clear_cache"
                ):
                    repo_to_close.git.clear_cache()
                if hasattr(repo_to_close, "close"):
                    repo_to_close.close()
                del repo_to_close
            except Exception as e:
                self.logger.warning(
                    "Error closing Git repository handle during cleanup.", error=str(e)
                )
        self._remove_repo_internal()
