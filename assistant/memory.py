"""Долгая память помощника: факты о пользователе, сохраняемые между запусками.

Хранится в data/memory.yaml. Факты подмешиваются в системную подсказку ИИ,
поэтому помощник «помнит» тебя даже после перезапуска.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from .config import ROOT

MEMORY_PATH = ROOT / "data" / "memory.yaml"
_MAX_FACTS = 100


def load() -> list[str]:
    if not MEMORY_PATH.exists():
        return []
    data = yaml.safe_load(open(MEMORY_PATH, encoding="utf-8")) or []
    return [str(x) for x in data] if isinstance(data, list) else []


def _save(facts: list[str]) -> None:
    MEMORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(MEMORY_PATH, "w", encoding="utf-8") as f:
        yaml.safe_dump(facts, f, allow_unicode=True, sort_keys=False)


def add_fact(fact: str) -> None:
    """Добавляет факт (без дубликатов)."""
    fact = " ".join(str(fact).split()).strip()
    if not fact:
        return
    facts = load()
    if fact.lower() not in (f.lower() for f in facts):
        facts.append(fact)
        _save(facts[-_MAX_FACTS:])


def clear() -> None:
    _save([])


def as_prompt() -> str:
    """Блок фактов для системной подсказки ИИ (пусто, если памяти нет)."""
    facts = load()
    if not facts:
        return ""
    lines = "\n".join(f"- {f}" for f in facts)
    return "Что ты помнишь о пользователе:\n" + lines
