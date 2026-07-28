"""Точка входа (консоль): главный цикл голосового помощника «Миса».

Запуск:
    python -m assistant.main
    python -m assistant.main --list-mics     # показать микрофоны
    python -m assistant.main --config path    # свой конфиг

Для оконного приложения без консоли используй:  python -m assistant.app
"""

from __future__ import annotations

import argparse
import sys

from .config import Config
from .engine import Assistant
from .recognizer import list_microphones


def _console_event(kind: str, text: str) -> None:
    if kind == "heard":
        print(f"👂 распознано: {text}")
    elif kind == "info":
        print(f"[ai] {text}")
    # "say" уже печатается самим Speaker; "status" в консоли не показываем.


def run(config: Config) -> None:
    print("=" * 56)
    wake = (config.get("assistant.wake_words") or ["миса"])[0]
    print(f"  Помощник запущен. Скажи «{wake.capitalize()}», чтобы разбудить.")
    print("  Ctrl+C — выход.")
    print("=" * 56)
    assistant = Assistant(config, on_event=_console_event)
    try:
        assistant.run()
    except KeyboardInterrupt:
        print("\nОстановлено пользователем.")
        assistant.stop()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Голосовой помощник «Миса»")
    parser.add_argument("--config", help="путь к config.yaml")
    parser.add_argument("--list-mics", action="store_true",
                        help="показать доступные микрофоны и выйти")
    args = parser.parse_args(argv)

    if args.list_mics:
        print(list_microphones())
        return 0

    try:
        config = Config.load(args.config)
        run(config)
    except (FileNotFoundError, KeyboardInterrupt) as exc:
        print(f"\n{exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
