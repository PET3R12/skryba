from pathlib import Path
from typing import List
from skryba.utils.data_handler import load_json


class ListOfFiles:
    def __init__(self, files_path: Path):
        self.files_path = files_path
        self.files_names = self._load_files()

    def _load_files(self) -> dict:
        data = load_json(self.files_path)
        return data.get("files", {})

    def get_files_structure(self) -> List[str]:
        return [element for element in self.files_names.keys()]


if __name__ == "__main__":
    files_path = Path("../parsing/raw_repo/raw_data.json")
    lof = ListOfFiles(files_path=files_path)
    print(lof.get_files_structure())
