from skryba.parsing.base_parser import BaseParser
from structlog.typing import FilteringBoundLogger
from github import GithubException
from github.Repository import Repository
from typing import List


class ContributorParser(BaseParser):
    def __init__(
        self, api_repo: Repository, logger_instance: FilteringBoundLogger
    ) -> None:
        super().__init__(logger_instance)
        self.api_repo = api_repo

    def parse(self) -> List[str]:
        if self.api_repo is None:
            self.logger.warning(
                "api_repo object is unavailable, cannot fetch contributors."
            )
            return []
        self.logger.info("Fetching contributors from GitHub API.")
        try:
            contributors = self.api_repo.get_contributors()
            contributor_logins = [contributor.login for contributor in contributors]
            self.logger.info(f"Fetched {len(contributor_logins)} contributors.")
            return contributor_logins
        except GithubException as e:
            self.logger.error(
                "Error fetching contributors from GitHub API.", error=str(e)
            )
            return []
