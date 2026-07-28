"""Низкоуровневые действия над ПК, общие для навыков и сценариев."""

from __future__ import annotations

import os
import subprocess
import time
import webbrowser


def run_shell(command: str) -> None:
    """Запускает shell-команду не блокируя помощника (Windows: shell=True)."""
    subprocess.Popen(command, shell=True)


def open_app(config, key_or_cmd: str) -> str:
    """Открывает программу по ключу из config.apps или как сырую команду.

    Если значение — путь к существующему файлу (даже с пробелами, напр.
    ...\\Opera GX\\opera.exe), запускаем его напрямую, чтобы пробелы в пути
    не ломали команду.
    """
    apps = config.section("apps")
    command = apps.get(key_or_cmd.strip(), key_or_cmd.strip())

    path = command.strip().strip('"')
    if os.path.isfile(path) and hasattr(os, "startfile"):
        os.startfile(path)  # Windows: корректно открывает путь с пробелами
    else:
        run_shell(command)
    return key_or_cmd


def search_web(query: str) -> str:
    """Открывает поиск Google по запросу."""
    import urllib.parse

    url = "https://www.google.com/search?q=" + urllib.parse.quote(query.strip())
    webbrowser.open(url)
    return url


def open_site(config, key_or_url: str) -> str:
    """Открывает сайт по ключу из config.sites или как готовый URL."""
    sites = config.section("sites")
    value = key_or_url.strip()
    url = sites.get(value, value)
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    webbrowser.open(url)
    return url


def press_hotkey(hotkey: str) -> None:
    """Нажимает сочетание клавиш, напр. 'win+d', 'ctrl+shift+esc'."""
    import pyautogui

    keys = [k.strip() for k in hotkey.replace("-", "+").split("+") if k.strip()]
    pyautogui.hotkey(*keys)


def type_text(text: str) -> None:
    import pyautogui

    pyautogui.typewrite(text, interval=0.02)


def wait(seconds: float) -> None:
    time.sleep(float(seconds))
