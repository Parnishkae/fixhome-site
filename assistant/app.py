"""Оконное приложение «Миса»: окно статуса + журнал + значок в трее.

Запуск без консоли (двойной клик по Misa.vbs) или:
    pythonw -m assistant.app

Движок помощника крутится в фоновом потоке и шлёт события в окно.
Значок в трее (pystray) — необязателен: если его нет, просто окно.
"""

from __future__ import annotations

import os
import queue
import threading
import tkinter as tk
from datetime import datetime
from tkinter import scrolledtext

from .config import Config
from .engine import Assistant

# Статус -> (иконка+текст, цвет)
_STATUS = {
    "sleep":  ("😴  Сплю",      "#7a8290"),
    "listen": ("🎤  Слушаю",    "#2ecc71"),
    "think":  ("🧠  Думаю",     "#9b59b6"),
    "work":   ("⚙️  Выполняю",  "#3498db"),
}

_BG = "#1e2229"
_PANEL = "#262b33"
_TEXT = "#e6e9ef"
_MUTED = "#9aa3b2"


class MisaApp:
    def __init__(self):
        self._events: "queue.Queue[tuple[str, str]]" = queue.Queue()
        self._assistant: Assistant | None = None
        self._tray = None

        self.root = tk.Tk()
        self.root.title("Миса")
        self.root.geometry("460x560")
        self.root.minsize(380, 420)
        self.root.configure(bg=_BG)
        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ------------------------------------------------------------------ UI
    def _build_ui(self) -> None:
        header = tk.Frame(self.root, bg=_BG)
        header.pack(fill="x", padx=16, pady=(16, 8))
        tk.Label(header, text="Миса", font=("Segoe UI Semibold", 20),
                 bg=_BG, fg=_TEXT).pack(side="left")

        # Индикатор статуса
        self.status_var = tk.StringVar(value=_STATUS["sleep"][0])
        self.status_lbl = tk.Label(
            self.root, textvariable=self.status_var,
            font=("Segoe UI", 15, "bold"), bg=_STATUS["sleep"][1], fg="white",
            pady=14)
        self.status_lbl.pack(fill="x", padx=16, pady=8)

        # Журнал
        self.log = scrolledtext.ScrolledText(
            self.root, wrap="word", font=("Segoe UI", 10),
            bg=_PANEL, fg=_TEXT, insertbackground=_TEXT, relief="flat",
            borderwidth=0, padx=10, pady=10, state="disabled")
        self.log.pack(fill="both", expand=True, padx=16, pady=8)
        self.log.tag_config("heard", foreground="#8fd3ff")
        self.log.tag_config("say", foreground="#a7f3c0")
        self.log.tag_config("info", foreground=_MUTED)
        self.log.tag_config("time", foreground=_MUTED, font=("Segoe UI", 8))

        # Низ: подсказка + выход
        bottom = tk.Frame(self.root, bg=_BG)
        bottom.pack(fill="x", padx=16, pady=(0, 14))
        self.hint = tk.Label(bottom, text="Скажи «Миса…»", bg=_BG, fg=_MUTED,
                             font=("Segoe UI", 9))
        self.hint.pack(side="left")
        tk.Button(bottom, text="Выход", command=self._quit, bg=_PANEL,
                  fg=_TEXT, relief="flat", padx=14, pady=4,
                  activebackground="#3a4048", activeforeground=_TEXT).pack(
            side="right")

    def _log_line(self, text: str, tag: str) -> None:
        self.log.configure(state="normal")
        self.log.insert("end", datetime.now().strftime("%H:%M  "), "time")
        self.log.insert("end", text + "\n", tag)
        self.log.see("end")
        self.log.configure(state="disabled")

    # -------------------------------------------------------------- события
    def on_event(self, kind: str, text: str) -> None:
        """Вызывается из потока движка — просто кладём в очередь."""
        self._events.put((kind, text))

    def _drain(self) -> None:
        try:
            while True:
                kind, text = self._events.get_nowait()
                self._apply(kind, text)
        except queue.Empty:
            pass
        self.root.after(120, self._drain)

    def _apply(self, kind: str, text: str) -> None:
        if kind == "status":
            label, color = _STATUS.get(text, _STATUS["sleep"])
            self.status_var.set(label)
            self.status_lbl.configure(bg=color)
        elif kind == "heard":
            self._log_line(f"👂  {text}", "heard")
        elif kind == "say":
            self._log_line(f"🔊  {text}", "say")
        elif kind == "info":
            self._log_line(f"ℹ️  {text}", "info")

    # --------------------------------------------------------------- запуск
    def _start_engine(self) -> None:
        def worker():
            try:
                self._assistant = Assistant(
                    Config.load(), on_event=self.on_event)
                self._assistant.run()
            except Exception as exc:
                self.on_event("info", f"Ошибка запуска: {exc}")

        threading.Thread(target=worker, daemon=True).start()

    def _setup_tray(self) -> None:
        try:
            import pystray
            from PIL import Image, ImageDraw
        except Exception:
            return  # трея нет — работаем просто окном

        img = Image.new("RGB", (64, 64), _STATUS["listen"][1])
        d = ImageDraw.Draw(img)
        d.ellipse((16, 14, 48, 46), fill="white")
        d.rectangle((29, 40, 35, 52), fill="white")

        menu = pystray.Menu(
            pystray.MenuItem("Показать", lambda: self.root.after(0, self._show)),
            pystray.MenuItem("Выход", lambda: self.root.after(0, self._quit)),
        )
        self._tray = pystray.Icon("misa", img, "Миса", menu)
        threading.Thread(target=self._tray.run, daemon=True).start()

    def _show(self) -> None:
        self.root.deiconify()
        self.root.lift()

    def _on_close(self) -> None:
        # Есть трей — прячемся туда; нет — выходим.
        if self._tray is not None:
            self.root.withdraw()
        else:
            self._quit()

    def _quit(self) -> None:
        if self._assistant is not None:
            self._assistant.stop()
        if self._tray is not None:
            try:
                self._tray.stop()
            except Exception:
                pass
        self.root.destroy()
        os._exit(0)  # глушим фоновые потоки (микрофон, tts)

    def run(self) -> None:
        self._setup_tray()
        self._start_engine()
        self.root.after(120, self._drain)
        self.root.mainloop()


def main() -> int:
    MisaApp().run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
