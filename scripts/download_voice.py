"""Скачивает нейросетевую голосовую модель Silero (русский, v4) в models/silero/.

Запуск:  python scripts/download_voice.py
"""

from __future__ import annotations

import sys
import urllib.request
import zipfile
from pathlib import Path

MODEL_URL = "https://models.silero.ai/models/tts/ru/v4_ru.pt"
ROOT = Path(__file__).resolve().parent.parent
TARGET = ROOT / "models" / "silero" / "v4_ru.pt"


def _progress(read: int, total: int) -> None:
    if total <= 0:
        return
    pct = read * 100 // total
    mb, total_mb = read / 1048576, total / 1048576
    sys.stdout.write(f"\r  Загрузка: {pct:3d}%  ({mb:.1f}/{total_mb:.1f} МБ)")
    sys.stdout.flush()


def main() -> int:
    # Модель Silero — это torch-архив (zip). Считаем валидной, если это zip.
    if TARGET.exists() and zipfile.is_zipfile(TARGET):
        print(f"Голосовая модель уже на месте: {TARGET}")
        return 0

    TARGET.parent.mkdir(parents=True, exist_ok=True)
    print(f"Скачиваю голос Silero (~60 МБ):\n  {MODEL_URL}")
    req = urllib.request.Request(MODEL_URL, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req) as resp:
            total = int(resp.headers.get("Content-Length", 0))
            read = 0
            with open(TARGET, "wb") as out:
                while True:
                    chunk = resp.read(65536)
                    if not chunk:
                        break
                    out.write(chunk)
                    read += len(chunk)
                    _progress(read, total)
        print()
    except Exception as exc:
        print(f"\nНе удалось скачать: {exc}")
        print("Скачай вручную и положи файл сюда:")
        print(f"  {TARGET}")
        print(f"Ссылка: {MODEL_URL}")
        return 1

    if not zipfile.is_zipfile(TARGET):
        print("Файл скачался повреждённым. Попробуй ещё раз.")
        TARGET.unlink(missing_ok=True)
        return 1

    print(f"Готово: {TARGET}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
