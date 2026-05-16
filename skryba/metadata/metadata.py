from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import List, Dict, Optional


class CommitMetaData(BaseModel):
    author: str = Field(title="Author of the commit")
    date: str = Field(title="Date of the commit")
    message: str = Field(title="Commit message")

    @field_validator("date")
    def validate_date(cls, v):
        try:
            datetime.strptime(v, "%Y-%m-%d %H:%M:%S%z")
        except ValueError:
            raise ValueError(
                "Invalid date format. Expected format is: YYYY-MM-DD HH:MM:SS+00:00"
            )
        return v


class TagMetaData(BaseModel):
    name: str = Field(title="Tag name")
    message: str = Field(title="Tag message")


class WorkflowMetaData(BaseModel):
    name: str = Field(title="Workflow name")
    file: str = Field(title="Workflow file name")
    jobs: List[str] = Field(title="List of jobs")


class MilestoneMetaData(BaseModel):
    title: str = Field(title="Milestone title")
    number: int = Field(title="Milestone number")
    state: str = Field(title="Milestone state")
    description: Optional[str] = Field(title="Milestone description")
    due_on: Optional[str] = Field(title="Milestone due date")
    created_at: Optional[str] = Field(title="Milestone creation date")


class RepoMetaData(BaseModel):
    repo_name: str = Field(title="Repository name")
    stars: int = Field(title="Number of stars")
    forks: int = Field(title="Number of forks")
    tags: List[TagMetaData] = Field(title="List of tags")
    contributors: List[str] = Field(title="List of contributors")
    commits: List[CommitMetaData] = Field(title="List of commits")
    files: Dict[str, str] = Field(title="Dictionary of file names and contents")
    milestones: List[MilestoneMetaData] = Field(title="List of milestones")
    completed_milestones: List[MilestoneMetaData] = Field(
        title="List of completed milestones"
    )
    workflows: List[WorkflowMetaData] = Field(title="List of workflows")


class ProcessedData(BaseModel):
    repo_name: str = Field(title="Repository name")
    files_structure: List[str] = Field(title="List of files")
    tags: List[Dict[str, str]] = Field(title="List of tags")
    start_date: str = Field(title="Project start date (ISO format)")
    project_duration: str = Field(title="Project duration in human-readable form")
    most_active_period: str = Field(title="Most active period")
    popularity: str = Field(title="Popularity level")
    contributors: List[str] = Field(title="List of contributors")
    most_active_contributor: str = Field(title="Most active contributor")
    least_active_contributor: str = Field(title="Least active contributor")
    programming_languages: List[str] = Field(title="List of detected languages")
    packages: Dict[str, List[str]] = Field(title="Used packages by language")
    readme: Optional[str] = Field(default=None, title="README content if available")
    completed_milestones_info: str = Field(title="Milestones info")
    workflows: List[WorkflowMetaData] = Field(title="List of workflows")
