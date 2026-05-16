from skryba.parsing.base_parser import BaseParser
from structlog.typing import FilteringBoundLogger
from pathlib import Path
from typing import Dict


class FileContentParser(BaseParser):
    def __init__(self, repo_path: Path, logger_instance: FilteringBoundLogger) -> None:
        super().__init__(logger_instance)
        self.repo_path = repo_path
        self.code_extensions = (
            ".py",
            ".c",
            ".cpp",
            ".cs",
            ".java",
            ".js",
            ".ts",
            ".go",
            ".php",
            ".rb",
            ".swift",
            ".kt",
            ".rs",
            ".m",
            ".h",
            ".scala",
            ".pl",
            ".sh",
            ".bat",
            ".md",
        )

    def parse(self) -> Dict[str, str]:
        if not self.repo_path.is_dir():
            self.logger.warning(
                "Local repository path invalid in FileContentParser.",
                path=str(self.repo_path),
            )
            return {}

        files: Dict[str, str] = {}
        self.logger.info(
            "Starting to parse files in repository.", path=str(self.repo_path)
        )
        try:
            for file_path in self.repo_path.rglob("*"):
                if ".git" in file_path.parts:
                    continue
                if (
                    file_path.is_file()
                    and file_path.suffix.lower() in self.code_extensions
                ):
                    try:
                        relative_path = str(file_path.relative_to(self.repo_path))
                        with file_path.open(
                            mode="r", encoding="utf-8", errors="ignore"
                        ) as f:
                            files[relative_path] = f.read()
                    except (IOError, OSError, UnicodeDecodeError, ValueError) as e_file:
                        self.logger.warning(
                            f"Error reading file: {file_path}", error=str(e_file)
                        )
        except OSError as e_glob:
            self.logger.error(
                "Error searching repository directory for files.",
                path=str(self.repo_path),
                error=str(e_glob),
            )
            return {}
        self.logger.info(f"Parsed {len(files)} files.")
        return files
