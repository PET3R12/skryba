from skryba.parsing.base_parser import BaseParser
from skryba.metadata.metadata import WorkflowMetaData
from structlog.typing import FilteringBoundLogger
from pathlib import Path
from typing import List
import yaml
import os


class WorkflowParser(BaseParser):
    def __init__(self, repo_path: Path, logger_instance: FilteringBoundLogger) -> None:
        super().__init__(logger_instance)
        self.repo_path = repo_path

    def parse(self) -> List[WorkflowMetaData]:
        workflow_dir = self.repo_path / ".github/workflows"
        parsed_workflows: List[WorkflowMetaData] = []
        if not workflow_dir.is_dir():
            self.logger.info(
                ".github/workflows directory does not exist.", path=str(workflow_dir)
            )
            return []

        self.logger.info("Parsing workflows.", path=str(workflow_dir))
        try:
            for filename in os.listdir(workflow_dir):
                if filename.lower().endswith((".yml", ".yaml")):
                    file_path = workflow_dir / filename
                    try:
                        with file_path.open(mode="r", encoding="utf-8") as f:
                            content = yaml.safe_load(f)
                            if content and isinstance(content, dict):
                                workflow_obj = WorkflowMetaData(
                                    name=content.get("name", filename),
                                    file=filename,
                                    jobs=list(content.get("jobs", {}).keys()),
                                )
                                parsed_workflows.append(workflow_obj)
                    except (yaml.YAMLError, IOError, OSError) as e_file:
                        self.logger.warning(
                            f"Error reading/parsing workflow file: {filename}",
                            error=str(e_file),
                        )
        except OSError as e_dir:
            self.logger.error(
                "Error listing workflows directory.",
                path=str(workflow_dir),
                error=str(e_dir),
            )
            return []
        self.logger.info(f"Parsed {len(parsed_workflows)} workflows.")
        return parsed_workflows
