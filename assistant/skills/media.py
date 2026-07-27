"""Управление медиа: пауза/воспроизведение, следующий/предыдущий трек."""

from __future__ import annotations

from ..dispatcher import Context, Intent


def _press(key: str):
    import pyautogui
    pyautogui.press(key)


def _play_pause(ctx: Context, text: str):
    _press("playpause")
    ctx.say("Готово")


def _next(ctx: Context, text: str):
    _press("nexttrack")
    ctx.say("Следующий трек")


def _prev(ctx: Context, text: str):
    _press("prevtrack")
    ctx.say("Предыдущий трек")


def _stop(ctx: Context, text: str):
    _press("stop")
    ctx.say("Остановила")


def build(config) -> list[Intent]:
    return [
        Intent("media_next", ["следующий трек", "следующая песня", "переключи трек"], _next),
        Intent("media_prev", ["предыдущий трек", "предыдущая песня"], _prev),
        Intent("media_stop", ["останови музыку", "стоп музыка"], _stop),
        Intent("media_play_pause",
               ["поставь на паузу", "пауза", "продолжи", "включи музыку", "играй"],
               _play_pause),
    ]
