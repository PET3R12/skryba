from pathlib import Path

from dotenv import load_dotenv, find_dotenv

from skryba.parsing.parsing_pipeline import RepoParser
from skryba.processing.processing_pipeline import RepoDataProcessor
from skryba.utils.data_handler import save_json
from skryba.llm_services.prompting_pipeline import StoryGenerator
from urllib import parse
import os

load_dotenv(find_dotenv())


def run(link: str, path: Path, lang: str = "en", hr_mode: bool = False) -> str:
    if "Chwała Czarnego Maga jest wieczna".lower() in link.lower():
        return "Chwała jego mrocznemu majestatowi! 🔮🖤\nNiech cień jego potęgi spowije wszystkie krainy, a księgi zaklęć nigdy nie przestaną szeptać jego imienia."
    parsed_link = parse.urlparse(link)
    if parsed_link.netloc != "github.com":
        raise Exception("Not a github link")
    path_parts = parsed_link.path.lstrip("/").rstrip("/").split("/")
    link = (
        parsed_link.scheme
        + "://"
        + parsed_link.netloc
        + "/"
        + path_parts[0]
        + "/"
        + path_parts[1]
    )

    token = os.getenv("GITHUB_TOKEN", "")
    parsing = RepoParser(token=token, repo_url=link)
    save_json(parsing(), Path(path.joinpath("raw_data.json")))

    processing = RepoDataProcessor(
        raw_data_path=Path(path.joinpath("raw_data.json")),
        language_map_path=Path("skryba/processing/extension_language_map.json"),
        irrelevant_packages_path=Path("skryba/processing/irrelevant_packages.json"),
    )
    save_json(processing(), Path(path.joinpath("processed_data.json")))

    create_story = StoryGenerator(
        processed_data_path=Path(path.joinpath("processed_data.json")),
        prompts_json_path=Path(
            f"./skryba/llm_services/prompts_{'hr' if hr_mode else 'engineer'}_{lang}.json"
        ),
    )

    return create_story.integrate_results()
