from skryba.parsing.parsing_pipeline import RepoParser
from skryba.processing.processing_pipeline import RepoDataProcessor
from skryba.utils.data_handler import save_json, load_json
from skryba.utils.chunking import readme_chunker

from pathlib import Path
import json
from dotenv import load_dotenv, find_dotenv
import os
from typing import Any, Dict, Optional, List, Type
import structlog

from skryba.llm_services.baseLLM import BaseLLM
from skryba.llm_services.llm_groq import GroqLLM
from skryba.llm_services.llm_google import GoogleLLM
from skryba.llm_services.llm_openrouter import OpenRouterLLM

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(indent=4, sort_keys=True),
    ]
)
logger = structlog.get_logger()

load_dotenv(find_dotenv())


class StoryGenerator:
    def __init__(
        self,
        processed_data_path: Optional[Path] = None,
        prompts_json_path: Optional[Path] = Path("prompts_engineer_en.json"),
    ):
        self.preprocessed_data: Optional[Dict[str, Any]] = None
        self.prompt_templates: Dict[str, Any] = {}

        if processed_data_path:
            loaded_data = load_json(processed_data_path)
            if not isinstance(loaded_data, dict):
                raise ValueError("Preprocessed data must be a dictionary.")
            self.preprocessed_data = loaded_data

        if prompts_json_path:
            self.prompt_templates = self._load_prompts_from_json_file(prompts_json_path)

        self._base_info_cache: Optional[str] = None
        self._specified_info_cache: Optional[str] = None
        self._readme_info_cache: Optional[str] = None
        self._files_structure_cache: Optional[str] = None
        self.available_llm_classes: List[Type[BaseLLM]] = [
            GoogleLLM,
            GroqLLM,
            OpenRouterLLM,
        ]  # kolejność providerów
        logger.info("StoryGenerator initialized")

    @staticmethod
    def _load_prompts_from_json_file(
        json_path: Path,
    ) -> Dict[str, Any]:  # ZMIANA: Zaktualizowano typowanie
        prompts_data = load_json(json_path)
        if not isinstance(prompts_data, dict):
            logger.error(
                "Prompts file does not contain a dictionary", path=str(json_path)
            )
            raise ValueError(f"Prompts file {json_path} must contain a dictionary.")
        logger.debug("Prompts loaded successfully", path=str(json_path))
        return prompts_data

    @property
    def base_info(self) -> str:
        if not self.preprocessed_data:
            raise ValueError("Preprocessed data not loaded. Cannot generate base_info.")
        if self._base_info_cache is None:
            logger.debug("Generating base_info (cache miss)")
            context_vars = {
                "repo_name": json.dumps(self.preprocessed_data.get("repo_name", "N/A")),
                "start_date": json.dumps(
                    self.preprocessed_data.get("start_date", "N/A")
                ),
                "contributors": json.dumps(
                    self.preprocessed_data.get("contributors", [])
                ),
                "project_duration": json.dumps(
                    self.preprocessed_data.get("project_duration", "N/A")
                ),
                "popularity": json.dumps(self.preprocessed_data.get("popularity", {})),
                "tags": json.dumps(self.preprocessed_data.get("tags", 0)),
            }
            self._base_info_cache = self._run_on_any_llm("base_info", context_vars)
        else:
            logger.debug("Returning base_info from cache")
        return self._base_info_cache

    @property
    def specified_info(self) -> str:
        if not self.preprocessed_data:
            raise ValueError(
                "Preprocessed data not loaded. Cannot generate specified_info."
            )
        if self._specified_info_cache is None:
            logger.debug("Generating specified_info (cache miss)")
            context_vars = {
                "packages": json.dumps(self.preprocessed_data.get("packages", [])),
                "programming_languages": json.dumps(
                    self.preprocessed_data.get("programming_languages", {})
                ),
            }
            self._specified_info_cache = self._run_on_any_llm(
                "specified_info", context_vars
            )
        else:
            logger.debug("Returning specified_info from cache")
        return self._specified_info_cache

    def readme_info(self, max_chars: int = 10_000) -> str:
        if not self.preprocessed_data:
            raise ValueError(
                "Preprocessed data not loaded. Cannot generate readme_info."
            )
        if self._readme_info_cache is not None:
            logger.debug("Returning readme_info from cache")
            return self._readme_info_cache

        markdown_content = self.preprocessed_data.get("readme", "")
        if not markdown_content:
            raise ValueError("No readme content found in preprocessed_data.")

        chunks = readme_chunker(markdown_content)
        if not chunks:
            raise RuntimeError("No chunks generated from readme content.")

        total_text = "\n\n".join(chunks)
        chunk_groups = (
            [chunks[: len(chunks) // 2], chunks[len(chunks) // 2 :]]
            if len(total_text) > max_chars
            else [chunks]
        )

        results = []
        for group in chunk_groups:
            group_text = "\n\n".join(group)
            context_vars = {
                "readme": group_text,
                "instructions": (
                    "Ignore repeated patterns, deeply nested headings (like 1.1.1.1.1...), "
                    "and extract only meaningful content like project purpose, usage, installation, dependencies."
                ),
            }
            result = self._run_on_any_llm("readme_info", context_vars)
            results.append(result.strip())

        self._readme_info_cache = "\n\n---\n\n".join(results)
        return self._readme_info_cache

    def files_structure_info(self, max_chunk_chars: int = 8_000) -> str:
        if not self.preprocessed_data:
            raise ValueError(
                "Preprocessed data not loaded. Cannot generate files_structure_info."
            )
        if self._files_structure_cache is not None:
            logger.debug("Returning files_structure_info from cache")
            return self._files_structure_cache

        logger.debug("Generating files_structure_info (cache miss)")
        fs_content = self.preprocessed_data.get("files_structure", {})

        if not fs_content:
            logger.warning("No files_structure content found in preprocessed_data.")
            return ""

        try:
            content_str = json.dumps(fs_content, indent=2)
        except TypeError as e:
            logger.error(f"Failed to serialize files_structure: {e}")
            return ""  # Zwróć pusty string

        if not content_str:
            return ""

        chunks = []
        for i in range(0, len(content_str), max_chunk_chars):
            chunks.append(content_str[i : i + max_chunk_chars])

        if not chunks:
            return ""

        results = []
        for chunk in chunks:
            context_vars = {
                "files_structure": chunk,
            }
            result = self._run_on_any_llm("files_structure", context_vars)
            results.append(result.strip())

        self._files_structure_cache = "\n\n".join(results)
        return self._files_structure_cache

    def integrate_results(self) -> str:
        if not self.preprocessed_data:
            raise ValueError(
                "Preprocessed data not loaded. Cannot integrate repo results."
            )

        logger.info("Integrating repository-specific results")

        context_vars = {
            "base": self.base_info,
            "specified": self.specified_info,
            "readme": self.readme_info(),
            "files_structure": self.files_structure_info(),
        }

        return self._run_on_any_llm("integrate_results", context_vars)

    def _run_on_any_llm(self, prompt_key: str, context: Dict[str, Any]) -> str:
        if not self.available_llm_classes:
            logger.error("No available LLMs left to try.")
            raise RuntimeError("No available LLMs left to try.")

        last_exception = None

        for llm_cls in self.available_llm_classes[:]:  # iterujemy po kopii listy
            try:
                logger.info(f"Trying LLM: {llm_cls.__name__}")
                llm = llm_cls()
                return llm.generate(context, self.prompt_templates[prompt_key])

            except Exception as e:
                logger.warning(f"LLM {llm_cls.__name__} failed: {str(e)}")
                last_exception = e

                error_message = str(e).lower()
                if (
                    "token" in error_message
                    and ("limit" in error_message or "exceeded" in error_message)
                ) or (
                    "rate limit" in error_message
                    or "429" in error_message
                    or "too many requests" in error_message
                ):
                    logger.info(
                        f"Removing {llm_cls.__name__} from available LLMs due to rate limit or token limit error"
                    )
                    if llm_cls in self.available_llm_classes:
                        self.available_llm_classes.remove(llm_cls)

        logger.error("All LLMs failed.")
        raise RuntimeError(f"All LLMs failed. Last error: {last_exception}")


def main() -> None:
    load_dotenv()
    token = os.getenv("GITHUB_TOKEN", "")
    repo = "https://github.com/knsiczarnamagia/wave4-skryba"
    parser = RepoParser(token=token, repo_url=repo)
    save_json(parser(), Path("../parsing/raw_repo/raw_data.json"))

    processor = RepoDataProcessor(
        language_map_path=Path("../processing/extension_language_map.json"),
        irrelevant_packages_path=Path("../processing/irrelevant_packages.json"),
    )
    save_json(processor(), Path("../processing/processed_repo/processed_data.json"))

    generator = StoryGenerator(
        processed_data_path=Path("../processing/processed_repo/processed_data.json"),
        prompts_json_path=Path("prompts_engineer_pl.json"),
    )

    print(generator.integrate_results())


if __name__ == "__main__":
    main()
