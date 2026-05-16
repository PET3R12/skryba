import json
from pathlib import Path
from typing import Any, Dict, Union, List
import structlog

logger = structlog.get_logger()


def load_json(file_path: Path) -> Union[Dict[str, Any], List[Any]]:
    """
    Loads and parses data from a JSON file.
    Args:
        file_path: Path object pointing to the JSON file.
    Returns:
        Parsed data as a dictionary or list.
    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file content is not valid JSON.
        IOError: For other file reading errors (e.g., permissions).
        Exception: For other unexpected errors.
    """
    logger.debug("Attempting to load JSON", path=str(file_path))
    if not file_path.is_file():
        logger.error("File not found for loading", path=str(file_path))
        raise FileNotFoundError(f"JSON file not found at {file_path}")
    try:
        with file_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        logger.info("Successfully loaded JSON", path=str(file_path))
        if not isinstance(data, (dict, list)):
            logger.warning(
                "Loaded JSON is neither dict nor list",
                path=str(file_path),
                type=type(data),
            )
        return data
    except json.JSONDecodeError as e:
        logger.error(
            "Failed to decode JSON",
            path=str(file_path),
            error=str(e),
            position=e.pos,
            line=e.lineno,
            column=e.colno,
        )
        raise json.JSONDecodeError(
            f"Error decoding JSON from {file_path}: {e.msg}", e.doc, e.pos
        ) from e
    except IOError as e:
        logger.error("I/O error loading JSON", path=str(file_path), error=str(e))
        raise IOError(
            f"An I/O error occurred while loading {file_path}: {str(e)}"
        ) from e
    except Exception as e:
        logger.error("Unexpected error loading JSON", path=str(file_path), error=str(e))
        raise RuntimeError(
            f"An unexpected error occurred while loading {file_path}: {str(e)}"
        ) from e


def save_json(
    data: Any, file_path: Path, indent: int = 4, ensure_ascii: bool = False
) -> None:
    """
    Saves Python data (dict, list, etc.) to a JSON file.
    Creates parent directories if they don't exist.
    Args:
        data: The Python object to serialize and save.
        file_path: Path object indicating where to save the file.
        indent: Indentation level for pretty-printing. Defaults to 4.
        ensure_ascii: If False, allows non-ASCII characters directly in the output. Defaults to False.
    Raises:
        TypeError: If the data is not JSON serializable.
        IOError: For file writing errors (e.g., permissions).
        Exception: For other unexpected errors during saving.
    """
    logger.debug("Attempting to save JSON", path=str(file_path))
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with file_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent, ensure_ascii=ensure_ascii)  # type: ignore[arg-type]
        logger.info("Successfully saved JSON", path=str(file_path))
    except TypeError as e:
        logger.error(
            "Data is not JSON serializable",
            path=str(file_path),
            error=str(e),
            data_type=type(data),
        )
        raise TypeError(
            f"Data provided is not JSON serializable for path {file_path}: {str(e)}"
        ) from e
    except IOError as e:
        logger.error("I/O error saving JSON", path=str(file_path), error=str(e))
        raise IOError(
            f"An I/O error occurred while saving to {file_path}: {str(e)}"
        ) from e
    except Exception as e:
        logger.error("Unexpected error saving JSON", path=str(file_path), error=str(e))
        raise RuntimeError(
            f"An unexpected error occurred while saving to {file_path}: {str(e)}"
        ) from e
