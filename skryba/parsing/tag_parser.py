from skryba.parsing.base_parser import BaseParser
from skryba.metadata.metadata import TagMetaData
from structlog.typing import FilteringBoundLogger
from git import Repo, GitCommandError
from git.objects.tag import TagObject
from typing import List


class TagParser(BaseParser):
    def __init__(self, local_repo: Repo, logger_instance: FilteringBoundLogger) -> None:
        super().__init__(logger_instance)
        self.local_repo = local_repo

    def parse(self) -> List[TagMetaData]:
        if self.local_repo is None:
            self.logger.warning("Local repository is unavailable in TagParser.")
            return []

        parsed_tags_info: List[TagMetaData] = []
        self.logger.info("Fetching tags from local repository.")
        try:
            for tag_ref in self.local_repo.tags:
                tag_name = tag_ref.name
                tag_message_content = ""
                try:
                    if isinstance(tag_ref.object, TagObject):
                        tag_object_annotated = tag_ref.object
                        if (
                            hasattr(tag_object_annotated, "message")
                            and tag_object_annotated.message is not None
                        ):
                            tag_message_content = str(
                                tag_object_annotated.message
                            ).strip()
                except (ValueError, GitCommandError, AttributeError) as e_tag_obj:
                    self.logger.warning(
                        f"Cannot access annotated tag object for tag: {tag_name}. It might be a lightweight tag or an issue.",
                        tag_name=tag_name,
                        error=str(e_tag_obj),
                    )

                parsed_tags_info.append(
                    TagMetaData(name=tag_name, message=tag_message_content)
                )
        except (GitCommandError, Exception) as e:
            self.logger.exception("Error while fetching tags.", error=str(e))
            return []
        self.logger.info(f"Fetched {len(parsed_tags_info)} tags.")
        return parsed_tags_info
