from skryba.parsing.base_parser import BaseParser
from skryba.metadata.metadata import MilestoneMetaData
from github import GithubException
from github.Repository import Repository
from typing import List


class MilestoneParser(BaseParser):
    def __init__(self, api_repo: Repository, logger_instance):
        super().__init__(logger_instance)
        self.api_repo = api_repo

    def parse(self) -> List[MilestoneMetaData]:
        if self.api_repo is None:
            self.logger.warning(
                "api_repo object is unavailable, cannot fetch milestones."
            )
            return []

        processed_milestones: List[MilestoneMetaData] = []
        self.logger.info("Fetching milestones from GitHub API.")
        try:
            milestones_from_api = self.api_repo.get_milestones(state="all")
            for milestone in milestones_from_api:
                try:
                    milestone_obj = MilestoneMetaData(
                        title=milestone.title,
                        number=milestone.number,
                        state=milestone.state,
                        description=milestone.description
                        if milestone.description is not None
                        else "",
                        due_on=milestone.due_on.isoformat() if milestone.due_on else "",
                        created_at=milestone.created_at.isoformat()
                        if milestone.created_at
                        else "",
                    )
                    processed_milestones.append(milestone_obj)
                except Exception as e_pydantic:
                    self.logger.warning(
                        f"Could not create MilestoneMetaData for milestone: {milestone.title} (number: {milestone.number}). Error: {e_pydantic}",
                        title=milestone.title,
                        number=milestone.number,
                        error=str(e_pydantic),
                    )
            self.logger.info(f"Fetched {len(processed_milestones)} milestones.")
            return processed_milestones
        except GithubException as e:
            self.logger.error(
                "Error fetching milestones from GitHub API.", error=str(e)
            )
            return []
