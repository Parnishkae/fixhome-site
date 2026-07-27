"""Навыки помощника. build_intents() собирает все навыки в один список."""

from __future__ import annotations

from ..dispatcher import Intent
from . import apps, media, system, web, window
from . import scenarios


def build_intents(config) -> list[Intent]:
    intents: list[Intent] = []
    # Сценарии — с высоким приоритетом: пользовательские фразы важнее общих команд.
    intents += scenarios.build(config)
    intents += system.build(config)
    intents += apps.build(config)
    intents += web.build(config)
    intents += media.build(config)
    intents += window.build(config)
    return intents
