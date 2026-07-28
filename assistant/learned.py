"""Выученные команды: фраза -> шаги, сохранённые ИИ на будущее.

Хранятся в data/learned.yaml. При старте загружаются как обычные навыки,
поэтому уже выученная фраза срабатывает мгновенно, без обращения к ИИ.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from .config import ROOT
from .dispatcher import Context, Intent
from .executor import run_steps

LEARNED_PATH = ROOT / "data" / "learned.yaml"


def load() -> dict:
    if not LEARNED_PATH.exists():
        return {}
    with open(LEARNED_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def save_command(phrase: str, steps: list) -> None:
    """Добавляет/обновляет выученную команду и пишет файл."""
    phrase = phrase.strip().lower()
    data = load()
    data[phrase] = steps
    LEARNED_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LEARNED_PATH, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)


def _make_intent(phrase: str, steps: list) -> Intent:
    def handler(ctx: Context, text: str):
        run_steps(ctx, steps)

    return Intent(
        name=f"learned:{phrase}",
        patterns=[phrase.strip().lower()],
        handler=handler,
        priority=8,  # ниже сценариев, но выше одиночных команд
    )


def build_intents() -> list[Intent]:
    return [_make_intent(p, s) for p, s in load().items()
            if isinstance(s, list)]


def make_intent(phrase: str, steps: list) -> Intent:
    """Для регистрации только что выученной команды на лету."""
    return _make_intent(phrase, steps)
