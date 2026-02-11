from __future__ import annotations
from pathlib import Path
from typing import Any, Optional
import sys

if sys.version_info >= (3, 11):
    import tomllib
else:  
    import tomli as tomllib  


class SettingsLoader:

    _instance: Optional["SettingsLoader"] = None

    def __new__(cls) -> "SettingsLoader":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:

        if hasattr(self, "_initialized") and self._initialized:
            return
        self._initialized = True

        self._config: dict[str, Any] = {}
        self._load_from_pyproject()

    def _load_from_pyproject(self) -> None:
        project_root = Path(__file__).resolve().parents[2]
        pyproject_path = project_root / "pyproject.toml"

        if not pyproject_path.exists():

            self._config = {}
            return

        with pyproject_path.open("rb") as f:
            data = tomllib.load(f)  # [web:440][web:443]

        vt = data.get("tool", {}).get("valutatrade", {})  # наш раздел
        self._config = {
            "project_root": str(project_root),
            "data_dir": vt.get("data_dir", "data"),
            "rates_ttl_seconds": vt.get("rates_ttl_seconds", 300),
            "base_currency": vt.get("base_currency", "USD"),
            "logs_dir": vt.get("logs_dir", "logs"),
            "log_format": vt.get(
                "log_format",
                "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            ),
        }

    def get(self, key: str, default: Any = None) -> Any:
        """Получить значение настройки по ключу."""
        return self._config.get(key, default)

    def reload(self) -> None:
        """Перечитать настройки из pyproject.toml."""
        self._load_from_pyproject()

