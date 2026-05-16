import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any
import structlog
from collections import defaultdict
from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv

from skryba.utils.data_handler import save_json, load_json
from skryba.metadata.metadata import ProcessedData
from skryba.parsing.parsing_pipeline import RepoParser
from skryba.processing.dependency_selector import DependencySelector
from skryba.processing.popularity_level import PopularityLevel
from skryba.processing.activity_period import ActivityPeriod
from skryba.processing.list_of_files import ListOfFiles


structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(indent=4, sort_keys=True),
    ]
)
logger = structlog.get_logger()


class RepoDataProcessor:
    _COMMIT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S%z"

    def __init__(
        self,
        raw_data_path: Path = Path(r"../parsing/raw_repo/raw_data.json"),
        language_map_path: Path = Path(r"extension_language_map.json"),
        irrelevant_packages_path: Path = Path(r"irrelevant_packages.json"),
    ):
        try:
            self.data = load_json(raw_data_path)
            if not isinstance(self.data, dict):
                logger.error("Raw data is not a dictionary", path=str(raw_data_path))
                raise ValueError("Invalid raw data format: not a dictionary.")
            self.extension_language_map = load_json(language_map_path)
            if not isinstance(self.extension_language_map, dict):
                logger.error(
                    "Language map is not a dictionary", path=str(language_map_path)
                )
                raise ValueError("Invalid language map format: not a dictionary.")
            self.irrelevant_packages = load_json(irrelevant_packages_path)
            if not isinstance(self.irrelevant_packages, dict):
                logger.error(
                    "Irrelevant packages is not a list",
                    path=str(irrelevant_packages_path),
                )
                raise ValueError("Invalid irrelevant packages format: not a list.")
        except (FileNotFoundError, json.JSONDecodeError, IOError, RuntimeError) as e:
            logger.critical(
                "Failed to initialize Processing due to data loading error",
                error=str(e),
                raw_data_path=str(raw_data_path),
                language_map=str(language_map_path),
                irrelevant_packages=str(irrelevant_packages_path),
            )
            raise ValueError(
                f"Initialization failed: Could not load necessary data. Error: {str(e)}"
            ) from e

        self.commits = self.data.get("commits", [])
        self.first_commit = self.commits[-1] if self.commits else None
        self.last_commit = self.commits[0] if self.commits else None
        self.files = self.data.get("files", {})
        self.popularity = self.get_popularity_level()
        self._normalized_files = None
        self.readme = self.get_readme_content()
        self.programming_languages = self.get_languages()
        self.files_structure = ListOfFiles(raw_data_path).get_files_structure()

        selector = DependencySelector(
            self.files, self.extension_language_map, self.irrelevant_packages
        )
        self.packages = selector.extract_dependencies()
        self._contributors_activity = self.make_contributors_activity_dictionary()
        self.most_active_contributor = self.get_most_active_contributor()
        self.least_active_contributor = self.get_least_active_contributor()

    def _get_normalized_files(self):
        """
         Retrieves a dictionary of files with filenames normalized to lowercase.
        Returns:
            dict: A dictionary mapping lowercased filenames (str) to their content.
            Returns an empty dict if `self.files` is empty/None or has no string filenames.
        """
        if self._normalized_files is None:
            self._normalized_files = {}
            if self.files:
                for filename, content in self.files.items():
                    if isinstance(filename, str):
                        self._normalized_files[filename.lower()] = content
        return self._normalized_files

    def get_readme_content(self) -> Optional[str]:
        normalized_files = self._get_normalized_files()

        if not normalized_files:
            logger.info("No files data to search for README.")
            return None

        content = normalized_files.get("readme.md")

        if content is not None:
            return content if isinstance(content, str) else None

        logger.info("README.md not found in files.")
        return None

    def make_contributors_activity_dictionary(self) -> dict:
        author_count = defaultdict(int)

        if not self.commits:
            return author_count

        for commit in self.commits:
            author = commit["author"]
            author_count[author] += 1

        return author_count

    def get_least_active_contributor(self) -> str:
        if not self._contributors_activity:
            return "N/a"
        return min(self._contributors_activity, key=self._contributors_activity.get)

    def get_most_active_contributor(self) -> str:
        if not self._contributors_activity:
            return "N/a"
        return max(self._contributors_activity, key=self._contributors_activity.get)

    @staticmethod
    def _format_plural(value: int, singular_unit: str, plural_unit: str) -> str:
        abs_value = abs(value)
        if abs_value == 1:
            return f"1 {singular_unit}"
        return f"{abs_value} {plural_unit}"

    def get_project_duration(self) -> str:
        if not self.first_commit or not self.last_commit:
            first_date = datetime.strptime(
                self.first_commit["date"], self._COMMIT_DATE_FORMAT
            )
            last_date = datetime.strptime(
                self.last_commit["date"], self._COMMIT_DATE_FORMAT
            )
            delta = relativedelta(last_date, first_date)
            parts = []
            if abs(delta.years) > 0:
                parts.append(self._format_plural(delta.years, "year", "years"))
            if abs(delta.months) > 0:
                parts.append(self._format_plural(delta.months, "month", "months"))
            if abs(delta.days) > 0:
                parts.append(self._format_plural(delta.days, "day", "days"))
            if not parts:
                return "Less than 1 day"

            return ", ".join(parts)
        else:
            return "N/a"

    def get_most_active_period(
        self, period: ActivityPeriod = ActivityPeriod.MONTH
    ) -> str:
        """
        Finds the most active period based on number of commits using an Enum for period type.
        """
        if not self.commits:
            logger.info("No commits data to determine most active period.")
            return "No commit data to determine the most active period."

        commit_counts = defaultdict(int)

        for commit_data in self.commits:
            date = datetime.strptime(commit_data["date"], self._COMMIT_DATE_FORMAT)

            key = period.get_date_key(date)
            commit_counts[key] += 1

        if not commit_counts:
            return "No commit data to determine the most active period."

        most_active_period_key = max(commit_counts, key=commit_counts.get)
        commit_number = commit_counts[most_active_period_key]

        return f"Most active period: {most_active_period_key} ({commit_number} commits)"

    def get_languages(self) -> List[str]:
        """
        Analyzes the files and returns a sorted list of programming languages
        used in the project based on the file extensions.
        """
        if not self.files:
            logger.info("No files data to determine languages.")
            return []

        exts = {
            os.path.splitext(fname)[1].lower()
            for fname in self.files.keys()
            if isinstance(fname, str)
        }

        langs = set()
        for ext in exts:
            language = self.extension_language_map.get(ext)
            if language:
                langs.add(language)

        return list(langs)

    def get_popularity_level(self) -> str:
        """
        Determines popularity level based on stars and forks.
        """
        stars = self.data.get("stars", 0)
        forks = self.data.get("forks", 0)
        score = stars + 2 * forks

        popularity_enum_member = PopularityLevel.from_score(score)

        return popularity_enum_member.value

    def get_milestones_info(self) -> str:
        """
        Generates a summary of completed milestones.
        :return: A string summarizing the completed milestones and listing their titles.
        """
        cm = self.data.get("completed_milestones", [])
        m = self.data.get("milestones", [])

        if not isinstance(cm, list) or not isinstance(m, list):
            logger.warning("Milestones data is not in list format.")
            return "Milestone data unavailable or malformed."

        titles = []
        for milestone in cm:
            if isinstance(milestone, dict):
                titles.append(milestone.get("title", "Untitled Milestone"))
            else:
                logger.warning(
                    "Non-dict item found in completed_milestones list.", item=milestone
                )

        titles = [milestone["title"] for milestone in cm]
        if len(cm) != 0:
            return f"Successfully completed: {len(cm)} out of {len(m)} milestones: {titles}"
        return f"Successfully completed: {len(cm)} out of {len(m)} milestones"

    def extract_processed_data(self):
        start_date_val = "N/A"
        if self.first_commit and isinstance(self.first_commit, dict):
            start_date_val = self.first_commit.get("date", "N/A")
        elif self.first_commit:
            logger.warning(
                "first_commit is not a dictionary.",
                first_commit_type=type(self.first_commit),
            )

        contributors_val = self.data.get("contributors", ["N/A"])
        if not (
            isinstance(contributors_val, list)
            and all(isinstance(c, str) for c in contributors_val)
        ):
            logger.warning(
                "Contributors data is not a list of strings. Using default.",
                data=contributors_val,
            )
            contributors_val = ["N/A"]

        return ProcessedData(
            repo_name=self.data.get("repo_name", "N/A"),
            files_structure=self.files_structure,
            start_date=start_date_val,
            contributors=contributors_val,
            popularity=self.get_popularity_level(),
            most_active_contributor=self.most_active_contributor,
            least_active_contributor=self.least_active_contributor,
            project_duration=self.get_project_duration(),
            readme=self.readme,
            programming_languages=self.programming_languages,
            packages=self.packages,
            tags=self.data.get("tags", []),
            workflows=self.data.get("workflows", []),
            most_active_period=self.get_most_active_period(period=ActivityPeriod.MONTH),
            completed_milestones_info=self.get_milestones_info(),
        )

    def __call__(self) -> Dict[str, Any]:
        processed_data_obj = self.extract_processed_data()
        return processed_data_obj.model_dump(mode="json")


def main() -> None:
    load_dotenv()
    token = os.getenv("GITHUB_TOKEN", "")
    repo = "https://github.com/bleachbit/bleachbit"
    parser = RepoParser(token=token, repo_url=repo)
    save_json(parser(), Path("../parsing/raw_repo/raw_data.json"))
    processor = RepoDataProcessor()
    save_json(
        processor(),
        Path("../processing/processed_repo/processed_data.json"),
    )


if __name__ == "__main__":
    main()
