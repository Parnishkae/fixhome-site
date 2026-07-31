@echo off
chcp 65001 >nul
REM ============================================================
REM  Сборка настоящего приложения Misa.exe (PyInstaller)
REM ============================================================
setlocal
cd /d "%~dp0"

if not exist ".venv" (
    echo Сначала запусти install.bat
    pause
    exit /b 1
)
call ".venv\Scripts\activate.bat"

echo === Ставлю PyInstaller ===
pip install pyinstaller

echo === Собираю Misa.exe ===
pyinstaller --noconfirm Misa.spec
if errorlevel 1 (
    echo Сборка не удалась. Смотри сообщения выше.
    pause
    exit /b 1
)

echo === Копирую настройки и данные рядом с exe ===
copy /Y config.yaml "dist\Misa\config.yaml" >nul
if exist secrets.yaml copy /Y secrets.yaml "dist\Misa\secrets.yaml" >nul
xcopy /E /I /Y plugins "dist\Misa\plugins" >nul
if exist models xcopy /E /I /Y models "dist\Misa\models" >nul
if exist data xcopy /E /I /Y data "dist\Misa\data" >nul

echo.
echo ============================================================
echo  Готово! Приложение здесь:  dist\Misa\Misa.exe
echo  Можно перенести папку dist\Misa куда угодно и запускать
echo  двойным кликом по Misa.exe (Python больше не нужен).
echo ============================================================
pause
