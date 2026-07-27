@echo off
chcp 65001 >nul
REM ============================================================
REM  Установка голосового помощника «Миса» (Windows)
REM ============================================================
setlocal
cd /d "%~dp0"

echo.
echo === [1/4] Проверка Python ===
where python >nul 2>nul
if errorlevel 1 (
    echo Python не найден. Установи Python 3.10+ с https://python.org
    echo и при установке отметь галочку "Add Python to PATH".
    pause
    exit /b 1
)

echo.
echo === [2/4] Создаю виртуальное окружение (.venv) ===
if not exist ".venv" (
    python -m venv .venv
)

echo.
echo === [3/4] Устанавливаю зависимости ===
call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
    echo Ошибка установки зависимостей. Смотри сообщения выше.
    pause
    exit /b 1
)

echo.
echo === [4/4] Скачиваю русскую модель распознавания Vosk ===
python scripts\download_model.py

echo.
echo ============================================================
echo  Установка завершена! Запуск: run.bat
echo ============================================================
pause
