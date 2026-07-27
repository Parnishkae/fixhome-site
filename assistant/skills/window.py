"""Управление окнами: свернуть всё, закрыть окно, переключение, рабочие столы."""

from __future__ import annotations

from .. import actions
from ..dispatcher import Context, Intent


def _minimize_all(ctx: Context, text: str):
    actions.press_hotkey("win+d")
    ctx.say("Свернула окна")


def _close_window(ctx: Context, text: str):
    actions.press_hotkey("alt+f4")
    ctx.say("Закрыла окно")


def _switch_window(ctx: Context, text: str):
    actions.press_hotkey("alt+tab")


def _show_desktop_task(ctx: Context, text: str):
    actions.press_hotkey("win+tab")


def build(config) -> list[Intent]:
    return [
        Intent("minimize_all", ["сверни все", "сверни всё", "сверни окна"], _minimize_all),
        Intent("close_window", ["закрой окно", "закрой это окно"], _close_window, priority=3),
        Intent("switch_window", ["переключи окно", "смени окно"], _switch_window),
        Intent("task_view", ["покажи все окна", "переключение окон"], _show_desktop_task),
    ]
