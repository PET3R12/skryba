from skryba.metadata.metadata import RepoMetaData, MilestoneMetaData
from skryba.utils.data_handler import save_json
from skryba.parsing.github_connector import GitHubConnector
from skryba.parsing.local_git_repo_manager import LocalGitRepoManager
from skryba.parsing.commit_parser import CommitParser
from skryba.parsing.file_content_parser import FileContentParser
from skryba.parsing.workflow_parser import WorkflowParser
from skryba.parsing.tag_parser import TagParser
from skryba.parsing.milestone_parser import MilestoneParser
from skryba.parsing.contributor_parser import ContributorParser
from skryba.parsing.repo_stats_parser import RepoStatsParser

from structlog.typing import FilteringBoundLogger
import structlog
import os
from dotenv import load_dotenv
from git import Repo, GitCommandError
from pathlib import Path
from github import GithubException
from typing import Optional, Dict, Any, List


structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(indent=4, sort_keys=True),
    ]
)
logger = structlog.get_logger()


class RepoParser:
    def __init__(
        self,
        repo_url: str,
        token: str,
        repo_path: Path = Path("../parsing/cloned_repo_refactored"),
        logger_instance: FilteringBoundLogger = logger,
    ) -> None:
        self.repo_url = repo_url
        self.token = token
        self.repo_path = repo_path
        self.logger = logger_instance
        self.repo_full_name = self._get_name_from_url(repo_url)

        self.github_connector = GitHubConnector(
            token=self.token,
            repo_full_name=self.repo_full_name,
            logger_instance=self.logger,
        )
        self.local_repo_manager = LocalGitRepoManager(
            repo_url=self.repo_url,
            repo_path=self.repo_path,
            logger_instance=self.logger,
        )

        self.api_repo: Optional[Any] = None
        self.local_git_repo: Optional[Repo] = None

    @staticmethod
    def _get_name_from_url(repo_url: str) -> str:
        repo_name_part = repo_url.rstrip("/").split("github.com/")[-1]
        if repo_name_part.endswith(".git"):
            repo_name_part = repo_name_part[:-4]
        return repo_name_part

    @staticmethod
    def _get_completed_milestones(
        all_milestones: List[MilestoneMetaData],
    ) -> List[MilestoneMetaData]:
        return [m for m in all_milestones if m.state == "closed"]

    def extract_repo_metadata(self) -> RepoMetaData:
        try:
            self.logger.info(f"Starting metadata extraction for {self.repo_full_name}")

            self.api_repo = self.github_connector.parse()
            if not self.api_repo:
                self.logger.critical("Failed to get API repo object. Aborting.")
                raise RuntimeError(
                    "Failed to get API repo object from GitHubConnector."
                )

            self.local_git_repo = self.local_repo_manager.clone_repo()
            if not self.local_git_repo:
                self.logger.critical("Failed to clone local repository. Aborting.")
                raise RuntimeError(
                    "Failed to clone local repository via LocalGitRepoManager."
                )

            commit_parser = CommitParser(
                local_repo=self.local_git_repo,
                api_repo=self.api_repo,
                logger_instance=self.logger,
            )
            file_parser = FileContentParser(
                repo_path=self.repo_path, logger_instance=self.logger
            )
            workflow_parser = WorkflowParser(
                repo_path=self.repo_path, logger_instance=self.logger
            )
            tag_parser = TagParser(
                local_repo=self.local_git_repo, logger_instance=self.logger
            )
            milestone_parser = MilestoneParser(
                api_repo=self.api_repo, logger_instance=self.logger
            )
            contributor_parser = ContributorParser(
                api_repo=self.api_repo, logger_instance=self.logger
            )
            repo_stats_parser = RepoStatsParser(
                api_repo=self.api_repo, logger_instance=self.logger
            )
            commits_data = commit_parser.parse()
            files_data = file_parser.parse()
            tags_data = tag_parser.parse()
            workflows_data = workflow_parser.parse()
            all_milestones_data = milestone_parser.parse()
            contributors_data = contributor_parser.parse()
            repo_stats = repo_stats_parser.parse()
            completed_milestones_data = self._get_completed_milestones(
                all_milestones_data
            )

            metadata_obj = RepoMetaData(
                repo_name=self.repo_full_name,
                stars=repo_stats.get("stars", 0),
                forks=repo_stats.get("forks", 0),
                commits=commits_data,
                files=files_data,
                contributors=contributors_data,
                tags=tags_data,
                milestones=all_milestones_data,
                completed_milestones=completed_milestones_data,
                workflows=workflows_data,
            )
            self.logger.info(
                f"Successfully extracted metadata for {self.repo_full_name}"
            )
            return metadata_obj
        except Exception as e:
            self.logger.exception(
                f"Critical failure during metadata extraction for {self.repo_full_name}",
                error=str(e),
            )
            raise
        finally:
            self.logger.info(f"Cleaning up resources for {self.repo_full_name}")
            self.local_repo_manager.cleanup()
            self.local_git_repo = None

    def __call__(self) -> Dict[str, Any]:
        return self.extract_repo_metadata().model_dump(mode="json")


def main() -> None:
    load_dotenv()
    token = os.getenv("GITHUB_TOKEN", "")
    if not token:
        logger.warning("GITHUB_TOKEN not found in environment variables.")

    repo = "https://github.com/bleachbit/bleachbit"
    output_path = Path("../parsing/raw_repo/raw_data.json")

    try:
        parsing = RepoParser(token=token, repo_url=repo)
        metadata_dictionary = parsing()
        save_json(metadata_dictionary, output_path)
        logger.info("Successfully saved metadata.", output_file=str(output_path))
    except RuntimeError as e_init:
        logger.critical(
            "Critical error during Parsing object initialization.", error=str(e_init)
        )
    except TypeError as e_type:
        logger.critical("Serialization error occurred.", error=str(e_type))
    except (GitCommandError, GithubException, Exception) as e_main:
        logger.critical(
            "Unhandled error during main parsing process.", error=str(e_main)
        )


if __name__ == "__main__":
    main()
