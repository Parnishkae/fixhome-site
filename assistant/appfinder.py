"""Поиск установленных программ по названию — чтобы «открой оперу» работало
без ручной настройки путей.

Сканирует ярлыки меню «Пуск» (.lnk), сопоставляет с запросом (в т.ч. с
транслитерацией рус->англ и нечётким поиском), возвращает путь к ярлыку/exe.
"""

from __future__ import annotations

import difflib
import os
from functools import lru_cache

_START_MENU_DIRS = [
    os.path.join(os.environ.get("APPDATA", ""),
                 r"Microsoft\Windows\Start Menu\Programs"),
    os.path.join(os.environ.get("PROGRAMDATA", ""),
                 r"Microsoft\Windows\Start Menu\Programs"),
]

# Простая транслитерация рус -> лат (опера -> opera).
_TRANSLIT = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e",
    "ж": "zh", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m",
    "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
    "ф": "f", "х": "h", "ц": "c", "ч": "ch", "ш": "sh", "щ": "sch",
    "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
}


def _translit(text: str) -> str:
    return "".join(_TRANSLIT.get(ch, ch) for ch in text.lower())


@lru_cache(maxsize=1)
def _index() -> dict[str, str]:
    """{имя ярлыка в нижнем регистре: путь к .lnk}."""
    items: dict[str, str] = {}
    for base in _START_MENU_DIRS:
        if not base or not os.path.isdir(base):
            continue
        for root, _dirs, files in os.walk(base):
            for f in files:
                if f.lower().endswith((".lnk", ".url")):
                    name = os.path.splitext(f)[0].lower()
                    items.setdefault(name, os.path.join(root, f))
    return items


def refresh() -> None:
    _index.cache_clear()


def find_app(name: str) -> str | None:
    """Ищет установленную программу по названию. Возвращает путь или None."""
    name = name.strip().lower()
    if not name:
        return None
    idx = _index()
    if not idx:
        return None

    # 1) точное совпадение
    if name in idx:
        return idx[name]

    # 2) подстрока (в обе стороны), плюс вариант с транслитерацией
    variants = {name, _translit(name)}
    matches = [p for key, p in idx.items()
               if any(v and (v in key or key in v) for v in variants)]
    if matches:
        return min(matches, key=lambda p: len(os.path.basename(p)))

    # 3) нечёткий поиск (опечатки/близкие написания)
    for v in variants:
        close = difflib.get_close_matches(v, list(idx.keys()), n=1, cutoff=0.7)
        if close:
            return idx[close[0]]
    return None
