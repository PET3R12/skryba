from skryba.parsing.base_parser import BaseParser
from structlog.typing import FilteringBoundLogger
from github import Github, GithubException, Auth
from typing import Any


class GitHubConnector(BaseParser):
    def __init__(
        self, token: str, repo_full_name: str, logger_instance: FilteringBoundLogger
    ) -> None:
        super().__init__(logger_instance)
        self.token = token
        self.repo_full_name = repo_full_name
        self.github_api = Github(auth=Auth.Token(token), per_page=100)

    def parse(self) -> Any:
        self.logger.info(
            "Accessing repository via GitHub API.", repo_name=self.repo_full_name
        )
        try:
            api_repo = self.github_api.get_repo(self.repo_full_name)
            return api_repo
        except GithubException as e:
            self.logger.error(
                "Cannot access repository via GitHub API.",
                repo_name=self.repo_full_name,
                error=str(e),
            )
            raise RuntimeError(
                f"Cannot initialize GitHub API connection for {self.repo_full_name}: {e}"
            ) from e
