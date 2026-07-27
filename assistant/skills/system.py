"""Системные команды: громкость, скриншот, блокировка, выключение, время."""

from __future__ import annotations

import datetime as _dt
import os
import subprocess
from pathlib import Path

from ..dispatcher import Context, Intent

# Русские названия дней/месяцев для команды «который час / какое число».
_DAYS = ["понедельник", "вторник", "среда", "четверг",
         "пятница", "суббота", "воскресенье"]
_MONTHS = ["января", "февраля", "марта", "апреля", "мая", "июня", "июля",
           "августа", "сентября", "октября", "ноября", "декабря"]


# ---------- Громкость (pycaw, с запасным вариантом на медиа-клавиши) ----------
def _volume_interface():
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    from ctypes import cast, POINTER

    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    return cast(interface, POINTER(IAudioEndpointVolume))


def _set_volume_delta(delta: float) -> None:
    try:
        vol = _volume_interface()
        current = vol.GetMasterVolumeLevelScalar()
        vol.SetMasterVolumeLevelScalar(min(1.0, max(0.0, current + delta)), None)
    except Exception:
        # Запасной путь — системные медиа-клавиши.
        import pyautogui
        key = "volumeup" if delta > 0 else "volumedown"
        for _ in range(3):
            pyautogui.press(key)


def _volume_up(ctx: Context, text: str):
    _set_volume_delta(+0.15)
    ctx.say("Сделала громче")


def _volume_down(ctx: Context, text: str):
    _set_volume_delta(-0.15)
    ctx.say("Сделала тише")


def _mute(ctx: Context, text: str):
    try:
        vol = _volume_interface()
        vol.SetMute(not vol.GetMute(), None)
    except Exception:
        import pyautogui
        pyautogui.press("volumemute")
    ctx.say("Готово")


# ---------- Скриншот ----------
def _screenshot(ctx: Context, text: str):
    import pyautogui

    folder = Path.home() / "Pictures" / "Screenshots"
    folder.mkdir(parents=True, exist_ok=True)
    name = _dt.datetime.now().strftime("screenshot_%Y%m%d_%H%M%S.png")
    path = folder / name
    pyautogui.screenshot(str(path))
    ctx.say(f"Скриншот сохранён")


# ---------- Питание / блокировка ----------
def _lock(ctx: Context, text: str):
    ctx.say("Блокирую")
    subprocess.Popen("rundll32.exe user32.dll,LockWorkStation", shell=True)


def _sleep_pc(ctx: Context, text: str):
    ctx.say("Ухожу в сон")
    subprocess.Popen(
        "rundll32.exe powrprof.dll,SetSuspendState 0,1,0", shell=True)


def _shutdown(ctx: Context, text: str):
    ctx.say("Выключаю компьютер через минуту. Скажи «отмена выключения», чтобы прервать")
    subprocess.Popen("shutdown /s /t 60", shell=True)


def _restart(ctx: Context, text: str):
    ctx.say("Перезагружаю компьютер через минуту. Скажи «отмена выключения», чтобы прервать")
    subprocess.Popen("shutdown /r /t 60", shell=True)


def _cancel_shutdown(ctx: Context, text: str):
    subprocess.Popen("shutdown /a", shell=True)
    ctx.say("Отменила выключение")


# ---------- Время и дата ----------
def _time(ctx: Context, text: str):
    now = _dt.datetime.now()
    ctx.say(f"Сейчас {now.hour} часов {now.minute} минут")


def _date(ctx: Context, text: str):
    now = _dt.datetime.now()
    ctx.say(f"Сегодня {_DAYS[now.weekday()]}, {now.day} {_MONTHS[now.month - 1]}")


def build(config) -> list[Intent]:
    return [
        Intent("volume_up", ["громче", "прибавь звук", "прибавь громкость"], _volume_up),
        Intent("volume_down", ["тише", "убавь звук", "убавь громкость"], _volume_down),
        Intent("mute", ["выключи звук", "без звука", "включи звук", "звук"], _mute),
        Intent("screenshot", ["скриншот", "сделай снимок экрана", "снимок экрана"], _screenshot),
        Intent("lock", ["заблокируй", "блокировка"], _lock),
        Intent("sleep", ["спящий режим", "уйти в сон", "усни"], _sleep_pc),
        # Отмена выключения — выше по приоритету, чтобы «отмена» ловилась раньше «выключи».
        Intent("cancel_shutdown", ["отмена выключения", "не выключай", "отмени выключение"],
               _cancel_shutdown, priority=5),
        Intent("shutdown", ["выключи компьютер", "выключи пк", "выключение"], _shutdown),
        Intent("restart", ["перезагрузи", "перезагрузка"], _restart),
        Intent("time", ["который час", "сколько времени", "текущее время"], _time),
        Intent("date", ["какое сегодня число", "какая дата", "какой сегодня день"], _date),
    ]
