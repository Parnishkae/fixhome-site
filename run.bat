@echo off
chcp 65001 >nul
REM Запуск голосового помощника «Миса»
setlocal
cd /d "%~dp0"

if not exist ".venv" (
    echo Сначала запусти install.bat
    pause
    exit /b 1
)

call ".venv\Scripts\activate.bat"
python -m assistant.main %*
