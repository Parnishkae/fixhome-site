"""Преобразование путей в ASCII-совместимый вид для C++-библиотек.

Vosk и PyTorch открывают файлы через узкий (ANSI) fopen и не находят их,
если путь содержит не-ASCII символы (например, кириллическое имя
пользователя Windows). Решение — «короткое» имя пути 8.3, оно всегда ASCII.
"""

from __future__ import annotations

import ctypes
import os
from pathlib import Path


def native_path(path: str | Path) -> str:
    """Возвращает путь, который умеют открыть C++-движки (Vosk, torch).

    На Windows пытается получить короткое имя 8.3 (C:\\Users\\DANKA~1\\...).
    На других ОС и при неудаче возвращает путь как есть.
    """
    p = str(path)
    if os.name != "nt":
        return p
    try:
        buf = ctypes.create_unicode_buffer(4096)
        if ctypes.windll.kernel32.GetShortPathNameW(p, buf, 4096):
            return buf.value
    except Exception:
        pass
    return p
