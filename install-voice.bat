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
echo === [1/4] Устанавливаю PyTorch (CPU-версия, ~200 МБ) ===
REM CPU-индекс, чтобы не тянуть огромную CUDA-сборку.
pip install --index-url https://download.pytorch.org/whl/cpu torch
if errorlevel 1 (
    echo Не удалось установить torch. Смотри сообщения выше.
    pause
    exit /b 1
)

echo.
echo === [2/4] Устанавливаю numpy и num2words ===
pip install numpy num2words

echo.
echo === [3/4] Обновляю comtypes (фикс системного голоса и громкости) ===
pip install -U "comtypes>=1.4.6"

echo.
echo === [4/4] Скачиваю голосовую модель Silero ===
python scripts\download_voice.py
if errorlevel 1 (
    echo.
    echo ВНИМАНИЕ: модель голоса не скачалась. Скачай вручную:
    echo   https://models.silero.ai/models/tts/ru/v4_ru.pt
    echo и положи файл в:  models\silero\v4_ru.pt
)

echo.
echo ============================================================
echo  Голос установлен! Запуск: run.bat
echo  (в config.yaml tts.engine уже стоит "silero")
echo ============================================================
pause
