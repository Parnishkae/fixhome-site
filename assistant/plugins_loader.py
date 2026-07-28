"""Загрузчик плагинов из папки plugins/.

Плагин расширяет помощника без правки ядра. Три вида:

1. Python-плагин  plugins/имя.py  — функция register(api):
       def register(api):
           api.add_command(["скажи привет"], steps=[{"say": "Привет!"}])
           api.add_command("моя команда", handler=my_func)   # handler(ctx, text)
           api.add_prompt("Ты также эксперт по Excel.")

2. YAML-плагин    plugins/имя.yaml:
       name: Мой плагин
       prompt: "Доп. инструкция для ИИ"
       commands:
         "фраза триггер":
           - say: "..."
           - app: "..."

3. Промпт — поле prompt в YAML или api.add_prompt(...) в Python — добавляет
   текст в системную подсказку ИИ (характер, знания, стиль).

Плагины с именем на "_" пропускаются. Ошибка в одном плагине не роняет
остальные — она попадает в api.errors.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import yaml

from .config import ROOT
from .dispatcher import Intent
from .executor import run_steps

PLUGINS_DIR = ROOT / "plugins"


class PluginAPI:
    """Передаётся в register(api). Через него плагин добавляет возможности."""

    def __init__(self, config):
        self.config = config
        self.intents: list[Intent] = []
        self.prompts: list[str] = []
        self.errors: list[str] = []

    def add_command(self, patterns, steps=None, handler=None,
                    priority: int = 6, name: str | None = None) -> None:
        """Добавляет голосовую команду.

        patterns — фраза-триггер (строка) или список фраз.
        steps    — список шагов (как в сценариях) ИЛИ
        handler  — функция handler(ctx, text) для своей логики.
        """
        if isinstance(patterns, str):
            patterns = [patterns]
        patterns = [p.lower() for p in patterns]

        if handler is None:
            if steps is None:
                raise ValueError("нужно указать steps или handler")

            def handler(ctx, text, _steps=steps):
                run_steps(ctx, _steps)

        self.intents.append(
            Intent(name or f"plugin:{patterns[0]}", patterns, handler, priority))

    def add_prompt(self, text: str) -> None:
        if text and str(text).strip():
            self.prompts.append(str(text).strip())


def _load_py(path: Path, api: PluginAPI) -> None:
    spec = importlib.util.spec_from_file_location(f"misa_plugin_{path.stem}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if hasattr(module, "register"):
        module.register(api)
    else:
        api.errors.append(f"{path.name}: нет функции register(api)")


def _load_yaml(path: Path, api: PluginAPI) -> None:
    data = yaml.safe_load(open(path, encoding="utf-8")) or {}
    api.add_prompt(data.get("prompt", ""))
    commands = data.get("commands", {}) or {}
    for phrase, steps in commands.items():
        if isinstance(steps, list):
            api.add_command(str(phrase), steps=steps)


def load_plugins(config) -> PluginAPI:
    api = PluginAPI(config)
    if not PLUGINS_DIR.exists():
        return api

    files = sorted(PLUGINS_DIR.glob("*.py")) + \
        sorted(PLUGINS_DIR.glob("*.yaml")) + sorted(PLUGINS_DIR.glob("*.yml"))
    for path in files:
        if path.name.startswith("_"):
            continue
        try:
            if path.suffix == ".py":
                _load_py(path, api)
            else:
                _load_yaml(path, api)
        except Exception as exc:
            api.errors.append(f"{path.name}: {exc}")
    return api
