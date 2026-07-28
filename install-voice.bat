@echo off
chcp 65001 >nul
REM ============================================================
REM  Установка нейросетевого голоса Silero (красивый русский голос)
REM  Запускать ПОСЛЕ основного install.bat
REM ============================================================
setlocal
cd /d "%~dp0"

if not exist ".venv" (
    echo Сначала запусти install.bat
    pause
    exit /b 1
)

call ".venv\Scripts\activate.bat"

echo.
echo === [1/3] Устанавливаю PyTorch (CPU-версия, ~200 МБ) ===
REM CPU-индекс, чтобы не тянуть огромную CUDA-сборку.
pip install --index-url https://download.pytorch.org/whl/cpu torch
if errorlevel 1 (
    echo Не удалось установить torch. Смотри сообщения выше.
    pause
    exit /b 1
)

echo.
echo === [2/3] Устанавливаю num2words (числа -^> слова) ===
pip install num2words

echo.
echo === [3/3] Скачиваю голосовую модель Silero ===
python scripts\download_voice.py

echo.
echo ============================================================
echo  Голос установлен! Запуск: run.bat
echo  (в config.yaml tts.engine уже стоит "silero")
echo ============================================================
pause
