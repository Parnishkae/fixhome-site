@echo off
chcp 65001 >nul
REM Запуск оконного приложения «Миса» с видимой консолью (для отладки).
REM Обычный запуск без консоли — двойной клик по Misa.vbs
setlocal
cd /d "%~dp0"

if not exist ".venv" (
    echo Сначала запусти install.bat
    pause
    exit /b 1
)

call ".venv\Scripts\activate.bat"
python -m assistant.app
if errorlevel 1 pause
