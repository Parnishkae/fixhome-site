"""Сценарии (алгоритмы действий): фраза -> последовательность шагов из config."""

from __future__ import annotations

from ..dispatcher import Context, Intent
from ..executor import run_steps


def _make_handler(steps: list[dict]):
    def handler(ctx: Context, text: str):
        run_steps(ctx, steps)
    return handler


def build(config) -> list[Intent]:
    scenarios = config.section("scenarios")
    intents: list[Intent] = []
    for phrase, steps in scenarios.items():
        if not isinstance(steps, list):
            continue
        intents.append(
            Intent(
                name=f"scenario:{phrase}",
                patterns=[str(phrase).lower()],
                handler=_make_handler(steps),
                priority=10,  # сценарии важнее одиночных команд
            )
        )
    return intents
