"""Показывает модели, доступные по твоему ключу (провайдер из secrets.yaml).

Запуск:  python scripts/list_models.py
Потом впиши нужную модель: python scripts/setup_ai.py (в поле «Модель»).
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from assistant.brain import PROVIDERS  # noqa: E402

SECRETS = ROOT / "secrets.yaml"


def main() -> int:
    if not SECRETS.exists():
        print("Нет secrets.yaml. Сначала: python scripts\\setup_ai.py")
        return 1
    secrets = yaml.safe_load(open(SECRETS, encoding="utf-8")) or {}
    provider = str(secrets.get("provider", "gemini")).lower()
    key = secrets.get("api_key") or ""
    preset = PROVIDERS.get(provider, PROVIDERS["gemini"])

    from openai import OpenAI

    client = OpenAI(base_url=preset["base_url"], api_key=key)
    print(f"Провайдер: {provider}. Доступные модели:\n")
    try:
        for m in client.models.list().data:
            print(f"  {m.id}")
    except Exception as exc:
        print(f"Не удалось получить список: {exc}")
        return 1
    print("\nВыбери одну и впиши её в setup_ai.py (поле «Модель»).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
