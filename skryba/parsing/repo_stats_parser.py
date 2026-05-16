from skryba.parsing.base_parser import BaseParser
from structlog.typing import FilteringBoundLogger
from github import GithubException
from github.Repository import Repository
from typing import Dict


class RepoStatsParser(BaseParser):
    def __init__(
        self, api_repo: Repository, logger_instance: FilteringBoundLogger
    ) -> None:
        super().__init__(logger_instance)
        self.api_repo = api_repo

    def parse(self) -> Dict[str, int]:
        if self.api_repo is None:
            self.logger.warning(
                "api_repo object is unavailable, cannot fetch repo stats."
            )
            return {"stars": 0, "forks": 0}

        self.logger.info("Fetching repository stats (stars, forks) from GitHub API.")
        try:
            stars = self.api_repo.stargazers_count
            forks = self.api_repo.forks_count
            self.logger.info(f"Fetched stats: Stars - {stars}, Forks - {forks}.")
            return {"stars": stars, "forks": forks}
        except GithubException as e:
            self.logger.error(
                "Error fetching repo stats from GitHub API.", error=str(e)
            )
            return {"stars": 0, "forks": 0}
