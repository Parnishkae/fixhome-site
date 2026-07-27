"""Скачивает и распаковывает русскую модель Vosk в папку models/.

Устойчив к оборванной загрузке: проверяет целостность модели и архива,
при необходимости качает заново.

Запуск:  python scripts/download_model.py
"""

from __future__ import annotations

import shutil
import sys
import urllib.request
import zipfile
from pathlib import Path

MODEL_NAME = "vosk-model-small-ru-0.22"
MODEL_URL = f"https://alphacephei.com/vosk/models/{MODEL_NAME}.zip"
ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = ROOT / "models"


def _is_valid_model(path: Path) -> bool:
    """Модель считается валидной, если внутри есть папки am/ и conf/."""
    return (path / "am").is_dir() and (path / "conf").is_dir()


def _find_valid_model(root: Path) -> Path | None:
    """Ищет валидную модель в root и на один уровень вложенности глубже."""
    if _is_valid_model(root):
        return root
    for child in root.iterdir() if root.exists() else []:
        if child.is_dir() and _is_valid_model(child):
            return child
    return None


def _progress(block_num, block_size, total_size):
    if total_size <= 0:
        return
    done = min(block_num * block_size, total_size)
    pct = done * 100 // total_size
    mb, total_mb = done / 1048576, total_size / 1048576
    sys.stdout.write(f"\r  Загрузка: {pct:3d}%  ({mb:.1f}/{total_mb:.1f} МБ)")
    sys.stdout.flush()


def _download(url: str, dest: Path) -> None:
    """Скачивает файл с браузерным User-Agent (некоторые серверы блокируют urllib)."""
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as resp:
        total = int(resp.headers.get("Content-Length", 0))
        read = 0
        with open(dest, "wb") as out:
            while True:
                chunk = resp.read(65536)
                if not chunk:
                    break
                out.write(chunk)
                read += len(chunk)
                _progress(read // 65536, 65536, total)
    print()


def _manual_hint() -> None:
    print("\nСкачай модель вручную и распакуй так, чтобы получилось")
    print(f"  {MODELS_DIR / MODEL_NAME}\\am, \\conf, \\graph ...")
    print(f"Ссылка: {MODEL_URL}")
    print("(в браузере: правый клик -> Сохранить как)")


def main() -> int:
    target = MODELS_DIR / MODEL_NAME

    # Уже установлена и валидна?
    if _is_valid_model(target):
        print(f"Модель уже на месте: {target}")
        return 0

    # Была неполная/битая папка — убираем, чтобы скачать начисто.
    if target.exists():
        print("Найдена неполная модель — удаляю и качаю заново.")
        shutil.rmtree(target, ignore_errors=True)

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    archive = MODELS_DIR / f"{MODEL_NAME}.zip"

    print(f"Скачиваю модель Vosk (~45 МБ):\n  {MODEL_URL}")
    try:
        _download(MODEL_URL, archive)
    except Exception as exc:
        print(f"\nНе удалось скачать: {exc}")
        _manual_hint()
        return 1

    # Проверяем, что скачался именно zip, а не страница с ошибкой.
    if not zipfile.is_zipfile(archive):
        print("Скачанный файл повреждён или это не архив.")
        archive.unlink(missing_ok=True)
        _manual_hint()
        return 1

    print("Распаковываю…")
    try:
        with zipfile.ZipFile(archive, "r") as zf:
            zf.extractall(MODELS_DIR)
    except Exception as exc:
        print(f"Ошибка распаковки: {exc}")
        _manual_hint()
        return 1
    finally:
        archive.unlink(missing_ok=True)

    # Иногда архив распаковывается во вложенную папку — находим и нормализуем.
    found = _find_valid_model(MODELS_DIR)
    if found and found != target:
        if target.exists():
            shutil.rmtree(target, ignore_errors=True)
        found.rename(target)

    if _is_valid_model(target):
        print(f"Готово: {target}")
        return 0

    print("Модель распаковалась, но нужные файлы не найдены.")
    _manual_hint()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
