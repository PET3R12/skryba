from skryba.parsing.base_parser import BaseParser
from skryba.metadata.metadata import CommitMetaData
from structlog.typing import FilteringBoundLogger
from git import Repo, GitCommandError
from github import GithubException
from typing import List


class CommitParser(BaseParser):
    def __init__(
        self,
        local_repo: Repo,
        api_repo: FilteringBoundLogger,
        logger_instance: FilteringBoundLogger,
    ) -> None:
        super().__init__(logger_instance)
        self.local_repo = local_repo
        self.api_repo = api_repo

    def parse(self) -> List[CommitMetaData]:
        if self.local_repo is None or self.api_repo is None:
            self.logger.warning("Required repo references unavailable in CommitParser.")
            return []

        commits_metadata = []
        try:
            branch_name = self.api_repo.default_branch
            self.logger.info("Fetching commits from branch.", branch=branch_name)

            if branch_name not in self.local_repo.heads:
                remote_branch = f"origin/{branch_name}"
                if remote_branch not in self.local_repo.references:
                    self.logger.warning(
                        f"Default branch {branch_name} (remote: {remote_branch}) not found locally."
                    )
                    commits_iter = self.local_repo.iter_commits()
                else:
                    commits_iter = self.local_repo.iter_commits(
                        f"refs/remotes/origin/{branch_name}"
                    )
            else:
                commits_iter = self.local_repo.iter_commits(branch_name)

            for commit in commits_iter:
                author_name = (
                    str(commit.author.name) if commit.author else "Unknown Author"
                )
                commit_date = (
                    str(commit.committed_datetime)
                    if commit.committed_datetime
                    else "Unknown Date"
                )
                commit_message = str(commit.message).strip() if commit.message else ""
                commits_metadata.append(
                    CommitMetaData(
                        author=author_name, date=commit_date, message=commit_message
                    )
                )
        except (GitCommandError, GithubException, AttributeError, Exception) as e:
            self.logger.exception("Error while fetching commits.", error=str(e))
            return []
        self.logger.info(f"Fetched {len(commits_metadata)} commits.")
        return commits_metadata
