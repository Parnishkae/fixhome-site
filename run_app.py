"""Точка входа для сборки в .exe (PyInstaller). Запускает оконное приложение."""

from assistant.app import main

if __name__ == "__main__":
    raise SystemExit(main())
