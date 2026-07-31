# PyInstaller spec для сборки Misa.exe (оконное приложение без консоли).
# Сборка:  build.bat   (или)   pyinstaller Misa.spec

# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

hiddenimports = (
    collect_submodules("openai")
    + collect_submodules("edge_tts")
    + ["miniaudio", "sounddevice", "numpy", "pystray", "PIL",
       "pyautogui", "psutil", "yaml", "num2words"]
)

datas = collect_data_files("sounddevice") + collect_data_files("num2words")

a = Analysis(
    ["run_app.py"],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=["torch", "vosk"],  # не нужны при whisper+edge (уменьшаем размер)
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name="Misa",
    console=False,          # без чёрного окна консоли
    icon=None,
)
coll = COLLECT(
    exe, a.binaries, a.datas,
    name="Misa",            # папка dist/Misa со всем содержимым
)
