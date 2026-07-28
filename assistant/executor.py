"""Единая «исполнялка» шагов-действий.

Используется и сценариями из config.yaml, и ИИ-мозгом, и выученными
командами. Понимает два формата шага:

    {app: "браузер"}                  — как в config.yaml (ключ: значение)
    {"type": "app", "value": "..."}   — как возвращает ИИ

Типы: say, app, site, search, key, type, wait, run/shell, scenario.
"""

from __future__ import annotations

from . import actions


def _parse_step(step: dict):
    if "type" in step:
        return str(step.get("type", "")).lower(), step.get("value")
    action, value = next(iter(step.items()))
    return str(action).lower(), value


def run_step(context, step: dict) -> None:
    if not isinstance(step, dict) or not step:
        return
    action, value = _parse_step(step)
    cfg = context.config

    if action in ("say", "speak"):
        context.say(str(value))
    elif action == "app":
        actions.open_app(cfg, str(value))
    elif action == "site":
        actions.open_site(cfg, str(value))
    elif action in ("search", "web", "google"):
        actions.search_web(str(value))
    elif action == "key":
        actions.press_hotkey(str(value))
    elif action == "type":
        actions.type_text(str(value))
    elif action == "wait":
        actions.wait(value)
    elif action in ("run", "shell", "cmd"):
        if getattr(context, "allow_shell", True):
            actions.run_shell(str(value))
        else:
            context.say("Выполнение системных команд отключено в настройках")
    elif action == "scenario":
        run_named_scenario(context, str(value))
    else:
        context.say(f"Неизвестный шаг: {action}")


def run_steps(context, steps) -> None:
    for step in steps or []:
        try:
            run_step(context, step)
        except Exception as exc:
            context.say(f"Шаг не выполнился: {exc}")


def run_named_scenario(context, name: str) -> None:
    """Запускает сценарий по имени из config.yaml (scenarios)."""
    scenarios = context.config.section("scenarios")
    steps = scenarios.get(name.strip().lower()) or scenarios.get(name)
    if isinstance(steps, list):
        run_steps(context, steps)
    else:
        context.say(f"Сценарий «{name}» не найден")
