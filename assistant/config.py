"""Загрузка и доступ к конфигурации из config.yaml."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

# Корень проекта = папка на уровень выше пакета assistant/
ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG_PATH = ROOT / "config.yaml"
# Секреты (API-ключи) — отдельный файл, НЕ попадает в git (.gitignore).
SECRETS_PATH = ROOT / "secrets.yaml"


class Config:
    """Тонкая обёртка над словарём из YAML с удобным доступом по точке."""

    def __init__(self, data: dict[str, Any], path: Path):
        self._data = data
        self.path = path

    @classmethod
    def load(cls, path: str | os.PathLike | None = None) -> "Config":
        cfg_path = Path(path) if path else DEFAULT_CONFIG_PATH
        if not cfg_path.exists():
            raise FileNotFoundError(
                f"Не найден файл конфигурации: {cfg_path}\n"
                "Скопируй config.yaml из репозитория рядом с проектом."
            )
        with open(cfg_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return cls(data, cfg_path)

    def get(self, dotted_key: str, default: Any = None) -> Any:
        """Достаёт значение по ключу вида 'speech.model_path'."""
        node: Any = self._data
        for part in dotted_key.split("."):
            if not isinstance(node, dict) or part not in node:
                return default
            node = node[part]
        return node

    def section(self, name: str) -> dict[str, Any]:
        value = self._data.get(name, {})
        return value if isinstance(value, dict) else {}

    def resolve_path(self, dotted_key: str, default: str = "") -> Path:
        """Возвращает путь, относительный — от корня проекта."""
        raw = self.get(dotted_key, default)
        p = Path(raw)
        return p if p.is_absolute() else (ROOT / p)

    @staticmethod
    def load_secrets() -> dict[str, Any]:
        """Читает secrets.yaml (API-ключи и т.п.). Нет файла -> пустой dict."""
        if not SECRETS_PATH.exists():
            return {}
        with open(SECRETS_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
