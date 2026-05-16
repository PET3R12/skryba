from pathlib import Path


def test_file_exists():
    """Check that extension_language_map.json exists."""
    file_path = Path("../skryba/processing/extension_language_map.json")
    assert file_path.is_file(), f"{file_path} doesn't exist!"
