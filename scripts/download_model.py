"""Скачивает и распаковывает русскую модель Vosk в папку models/.

Запуск:  python scripts/download_model.py
"""

from __future__ import annotations

import sys
import urllib.request
import zipfile
from pathlib import Path

MODEL_NAME = "vosk-model-small-ru-0.22"
MODEL_URL = f"https://alphacephei.com/vosk/models/{MODEL_NAME}.zip"
ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = ROOT / "models"


def _progress(block_num, block_size, total_size):
    if total_size <= 0:
        return
    done = min(block_num * block_size, total_size)
    pct = done * 100 // total_size
    mb = done / 1024 / 1024
    total_mb = total_size / 1024 / 1024
    sys.stdout.write(f"\r  Загрузка: {pct:3d}%  ({mb:.1f}/{total_mb:.1f} МБ)")
    sys.stdout.flush()


def main() -> int:
    target = MODELS_DIR / MODEL_NAME
    if target.exists():
        print(f"Модель уже на месте: {target}")
        return 0

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    archive = MODELS_DIR / f"{MODEL_NAME}.zip"

    print(f"Скачиваю модель Vosk (~45 МБ) с {MODEL_URL}")
    try:
        urllib.request.urlretrieve(MODEL_URL, archive, _progress)
        print()
    except Exception as exc:
        print(f"\nНе удалось скачать: {exc}")
        print("Скачай вручную и распакуй в папку models/:")
        print(f"  {MODEL_URL}")
        return 1

    print("Распаковываю…")
    with zipfile.ZipFile(archive, "r") as zf:
        zf.extractall(MODELS_DIR)
    archive.unlink(missing_ok=True)
    print(f"Готово: {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
