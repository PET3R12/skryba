from collections import defaultdict
import os
import re
from typing import Dict, List, Set, Optional
import structlog

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(indent=4, sort_keys=True),
    ]
)
logger = structlog.get_logger()


class DependencySelector:
    _JS_TS_IMPORT_PATTERNS = [
        r'require\(["\']([a-zA-Z0-9_\-/]+)["\']\)',
        r'import .* from ["\']([a-zA-Z0-9_\-/]+)["\']',
    ]
    _C_CPP_H_INCLUDE_PATTERN = [r'#include\s+[<"]([a-zA-Z0-9_\.\/]+)[">"]']
    _JAVA_LIKE_IMPORT_PATTERN = [r"import\s+([a-zA-Z0-9_.]+);"]
    _CSHARP_USING_PATTERN = [r"using\s+([a-zA-Z0-9_.]+);"]

    PATTERNS_BY_EXTENSION = {
        ".py": [r"^\s*(?:import|from)\s+([a-zA-Z0-9_\.]+)"],
        ".js": _JS_TS_IMPORT_PATTERNS,
        ".ts": _JS_TS_IMPORT_PATTERNS,
        ".java": _JAVA_LIKE_IMPORT_PATTERN,
        ".pl": [r"use\s+([a-zA-Z0-9_:]+)"],
    }

    def __init__(
        self,
        files_content: Dict[str, str],
        extension_language_map: Dict[str, str],
        irrelevant_modules: Optional[List[str]],
    ):
        """
        :param files_content: Słownik mapujący nazwę pliku na jego treść (string).
        :param extension_language_map: Słownik mapujący rozszerzenie pliku na język programowania.
        """
        self.files_content = files_content
        self.extension_language_map = extension_language_map
        self._internal_modules_cache: Optional[Set[str]] = None
        self.irrelevant_modules = irrelevant_modules

    def _get_internal_modules(self) -> Set[str]:
        if self._internal_modules_cache is None:
            self._internal_modules_cache = {
                os.path.splitext(path)[0]
                .replace("/", ".")
                .replace("\\", ".")
                .lstrip(".")
                for path in self.files_content.keys()
            }
        return self._internal_modules_cache

    def _is_internal_package(self, package_name: str) -> bool:
        package_name = package_name.strip(".")
        internal_modules = self._get_internal_modules()
        return any(
            package_name == mod or package_name.startswith(mod + ".")
            for mod in internal_modules
        )

    def _detect_in_file(self, content: str, extension: str) -> Set[str]:
        detected = set()
        if not isinstance(content, str):
            return detected

        if extension in self.PATTERNS_BY_EXTENSION:
            for pattern_str in self.PATTERNS_BY_EXTENSION[extension]:
                try:
                    matches = re.findall(pattern_str, content, re.MULTILINE)
                    detected.update(matches)
                except re.error as e:
                    logger.error(
                        "Regex error during package detection",
                        pattern=pattern_str,
                        error=str(e),
                    )

        language = self.extension_language_map.get(extension)
        irrelevant = set(self.irrelevant_modules.get(language, []))

        return {
            pkg
            for pkg in detected
            if pkg
            and not pkg.startswith(".")
            and not pkg.isdigit()
            and pkg not in irrelevant
        }

    def extract_dependencies(self) -> Dict[str, List[str]]:
        """
        Scans the source files to detect the packages/libraries used.
        """
        project_packages: Dict[str, Set[str]] = defaultdict(set)

        for filename, content in self.files_content.items():
            ext = os.path.splitext(filename)[1].lower()
            language = self.extension_language_map.get(ext)

            if not language:
                continue

            detected_for_file = self._detect_in_file(content, ext)
            if detected_for_file:
                external_packages = {
                    pkg
                    for pkg in detected_for_file
                    if not self._is_internal_package(pkg)
                    and pkg not in self.irrelevant_modules
                }
                if external_packages:
                    project_packages[language].update(external_packages)

        return {lang: list(pkgs) for lang, pkgs in project_packages.items()}
