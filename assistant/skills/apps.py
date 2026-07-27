"""Запуск и закрытие программ."""

from __future__ import annotations

from .. import actions
from ..dispatcher import Context, Intent

_OPEN_TRIGGERS = ["открой", "запусти", "включи"]
_CLOSE_TRIGGERS = ["закрой", "заверши"]


def _strip(text: str, triggers: list[str]) -> str:
    """Убирает слово-триггер и служебные слова, оставляя название программы."""
    result = text
    for t in triggers:
        result = result.replace(t, " ")
    for noise in ["программу", "приложение", "мне", "пожалуйста"]:
        result = result.replace(noise, " ")
    return " ".join(result.split()).strip()


def _open_app(ctx: Context, text: str):
    apps = ctx.config.section("apps")
    sites = ctx.config.section("sites")
    target = _strip(text, _OPEN_TRIGGERS + ["сайт"])
    # Сначала программы, потом сайты — оба по самому длинному совпавшему ключу.
    match = _best_key(apps, target)
    if match:
        actions.open_app(ctx.config, match)
        ctx.say(f"Открываю {match}")
        return
    site_key = _best_key(sites, target)
    if site_key:
        actions.open_site(ctx.config, site_key)
        ctx.say(f"Открываю {site_key}")
        return
    ctx.say(f"Не знаю «{target}». Добавь её в config.yaml, раздел apps или sites")


def _close_app(ctx: Context, text: str):
    import psutil

    apps = ctx.config.section("apps")
    target = _strip(text, _CLOSE_TRIGGERS)
    match = _best_key(apps, target) or target
    command = apps.get(match, match)
    # Достаём имя исполняемого файла из команды вида "start chrome" / "notepad.exe".
    exe = command.replace("start", "").strip().split()[-1].split("\\")[-1]
    exe_name = exe if exe.endswith(".exe") else exe + ".exe"

    killed = 0
    for proc in psutil.process_iter(["name"]):
        try:
            if (proc.info["name"] or "").lower() == exe_name.lower():
                proc.terminate()
                killed += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    ctx.say(f"Закрыла {match}" if killed else f"Не нашла запущенный {match}")


def _best_key(mapping: dict, target: str) -> str | None:
    """Возвращает самый длинный ключ mapping, входящий в target."""
    candidates = [k for k in mapping if k in target]
    return max(candidates, key=len) if candidates else None


def build(config) -> list[Intent]:
    return [
        Intent("close_app", _CLOSE_TRIGGERS, _close_app, priority=2),
        Intent("open_app", _OPEN_TRIGGERS, _open_app, priority=1),
    ]
