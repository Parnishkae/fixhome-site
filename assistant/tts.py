"""Синтез речи (озвучка ответов). Офлайн через pyttsx3 / SAPI5 на Windows.

Работает в отдельном потоке, чтобы озвучка не блокировала распознавание.
Если синтез недоступен — молча деградирует до печати в консоль.
"""

from __future__ import annotations

import queue
import threading

try:
    import pyttsx3
except Exception:  # pragma: no cover - библиотека может быть не установлена
    pyttsx3 = None


class Speaker:
    def __init__(self, rate: int = 180, volume: float = 1.0,
                 voice_hint: str = "ru", enabled: bool = True):
        self.enabled = enabled and pyttsx3 is not None
        self._queue: "queue.Queue[str | None]" = queue.Queue()
        self._rate = rate
        self._volume = volume
        self._voice_hint = (voice_hint or "").lower()
        self._engine = None
        self._thread: threading.Thread | None = None
        if self.enabled:
            self._thread = threading.Thread(target=self._worker, daemon=True)
            self._thread.start()

    def _init_engine(self):
        engine = pyttsx3.init()
        engine.setProperty("rate", self._rate)
        engine.setProperty("volume", self._volume)
        if self._voice_hint:
            for voice in engine.getProperty("voices"):
                haystack = f"{voice.id} {voice.name}".lower()
                if self._voice_hint in haystack:
                    engine.setProperty("voice", voice.id)
                    break
        return engine

    def _worker(self):
        try:
            self._engine = self._init_engine()
        except Exception as exc:  # синтез не поднялся — работаем молча
            print(f"[tts] Синтез речи недоступен: {exc}")
            self.enabled = False
            return
        while True:
            text = self._queue.get()
            if text is None:
                break
            try:
                self._engine.say(text)
                self._engine.runAndWait()
            except Exception as exc:
                print(f"[tts] Ошибка озвучки: {exc}")

    def say(self, text: str) -> None:
        """Ставит фразу в очередь на озвучку. Всегда печатает её в консоль."""
        if not text:
            return
        print(f"🔊 Миса: {text}")
        if self.enabled:
            self._queue.put(text)

    def stop(self) -> None:
        if self.enabled:
            self._queue.put(None)
