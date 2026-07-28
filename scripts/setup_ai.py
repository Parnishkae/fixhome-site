"""Интерактивная настройка ИИ: спрашивает провайдера и ключ, пишет secrets.yaml.

Запуск:  python scripts/setup_ai.py
"""

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SECRETS = ROOT / "secrets.yaml"


def main() -> int:
    print("=== Настройка ИИ-мозга Мисы ===\n")

    known = ("gemini", "grok", "groq", "openrouter", "ollama", "openai")
    print("Провайдеры: gemini, grok, groq (бесплатный), openrouter, ollama"
          " (локально), openai\n")
    provider = ""
    while provider not in known:
        provider = input("Провайдер: ").strip().lower()
        if provider not in known:
            print(f"  Введи одно из: {', '.join(known)}")

    key = ""
    if provider == "ollama":
        print("Ollama работает локально — ключ не нужен.")
    else:
        while not key:
            key = input(f"Вставь API-ключ ({provider}): ").strip()

    model = input("Модель (Enter — по умолчанию): ").strip()

    data = {"provider": provider, "api_key": key, "model": model}
    with open(SECRETS, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)

    print(f"\nГотово! Ключ сохранён в {SECRETS}")
    print("Файл в git не попадёт (он в .gitignore). Запускай run.bat.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
