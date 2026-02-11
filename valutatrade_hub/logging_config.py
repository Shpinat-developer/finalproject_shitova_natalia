from __future__ import annotations
import logging
from logging.handlers import RotatingFileHandler  # [web:452][web:450]
from pathlib import Path
from typing import Optional
from valutatrade_hub.infra.settings import SettingsLoader


_LOGGING_CONFIGURED = False


def setup_logging(force: bool = False) -> None:
    """Инициализация логирования приложения.

    Вызывается один раз при старте (например, из main.py).
    """
    global _LOGGING_CONFIGURED
    if _LOGGING_CONFIGURED and not force:
        return

    settings = SettingsLoader()

    project_root = Path(settings.get("project_root"))
    logs_dir = project_root / settings.get("logs_dir", "logs")
    logs_dir.mkdir(parents=True, exist_ok=True)

    log_path = logs_dir / "actions.log"

    log_format = settings.get(
        "log_format",
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    # Базовый конфиг
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Удаляем старые хендлеры, чтобы при повторном вызове не дублировать вывод
    logger.handlers.clear()

    # Хендлер ротации файла: ~1 МБ, 5 резервных копий [web:450][web:457]
    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=1_000_000,
        backupCount=5,
        encoding="utf-8",
    )
    file_formatter = logging.Formatter(
        fmt=log_format,
        datefmt="%Y-%m-%dT%H:%M:%S",  # ISO-подобный формат [web:456][web:459]
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # Параллельно выводим в консоль (удобно при отладке)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(file_formatter)
    logger.addHandler(console_handler)

    _LOGGING_CONFIGURED = True

