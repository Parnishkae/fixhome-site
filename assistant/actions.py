"""Низкоуровневые действия над ПК, общие для навыков и сценариев."""

from __future__ import annotations

import os
import subprocess
import time
import webbrowser


def run_shell(command: str) -> None:
    """Запускает shell-команду не блокируя помощника (Windows: shell=True)."""
    subprocess.Popen(command, shell=True)


def run_shell_capture(command: str, timeout: int = 30) -> str:
    """Выполняет команду и возвращает её вывод (для агента). Обрезает длинный."""
    try:
        proc = subprocess.run(command, shell=True, capture_output=True,
                              text=True, timeout=timeout, errors="replace")
        out = (proc.stdout or "") + (proc.stderr or "")
        out = out.strip() or f"(код возврата {proc.returncode}, вывода нет)"
    except subprocess.TimeoutExpired:
        out = "(команда не завершилась за отведённое время)"
    except Exception as exc:
        out = f"(ошибка запуска: {exc})"
    return out[:1500]  # не раздуваем контекст


def open_app(config, key_or_cmd: str) -> str:
    """Открывает программу. Порядок поиска:
    1) ключ из config.apps (если прописан явно);
    2) путь к существующему файлу (запуск напрямую, пробелы не ломают);
    3) автопоиск установленной программы по названию (ярлыки меню «Пуск»);
    4) как есть — через shell.
    """
    apps = config.section("apps")
    raw = key_or_cmd.strip()

    # 1) явно прописанная программа
    if raw in apps:
        command = apps[raw]
        path = command.strip().strip('"')
        if os.path.isfile(path) and hasattr(os, "startfile"):
            os.startfile(path)
        else:
            run_shell(command)
        return raw

    # 2) сразу путь к файлу
    if os.path.isfile(raw) and hasattr(os, "startfile"):
        os.startfile(raw)
        return raw

    # 3) автопоиск среди установленных программ (по названию)
    if hasattr(os, "startfile"):
        try:
            from .appfinder import find_app
            found = find_app(raw)
            if found:
                os.startfile(found)
                return raw
        except Exception:
            pass

    # 4) последняя попытка — запустить как команду
    run_shell(raw)
    return raw


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
