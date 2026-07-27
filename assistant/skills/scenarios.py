"""Сценарии (алгоритмы действий): фраза -> последовательность шагов из config."""

from __future__ import annotations

from .. import actions
from ..dispatcher import Context, Intent


def _run_steps(steps: list[dict]):
    """Возвращает обработчик, выполняющий шаги сценария по порядку."""

    def handler(ctx: Context, text: str):
        for step in steps:
            if not isinstance(step, dict) or not step:
                continue
            action, value = next(iter(step.items()))
            action = str(action).lower()
            try:
                if action == "say":
                    ctx.say(str(value))
                elif action == "app":
                    actions.open_app(ctx.config, str(value))
                elif action == "site":
                    actions.open_site(ctx.config, str(value))
                elif action == "key":
                    actions.press_hotkey(str(value))
                elif action == "type":
                    actions.type_text(str(value))
                elif action == "wait":
                    actions.wait(value)
                elif action == "run":
                    actions.run_shell(str(value))
                else:
                    ctx.say(f"Неизвестный шаг сценария: {action}")
            except Exception as exc:
                ctx.say(f"Шаг «{action}» не выполнился: {exc}")

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
                handler=_run_steps(steps),
                priority=10,  # сценарии важнее одиночных команд
            )
        )
    return intents
