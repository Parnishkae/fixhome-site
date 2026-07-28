"""Синтез речи (озвучка ответов). Два движка, оба офлайн:

  * silero — нейросетевой русский голос (красиво, требует torch + модель);
  * sapi5  — системный голос Windows (быстро, но роботно).

Движок выбирается в config.yaml -> tts.engine. Если выбранный движок не
поднялся, происходит откат: silero -> sapi5 -> только текст в консоли.

Работает в отдельном потоке, чтобы озвучка не блокировала распознавание.
"""

from __future__ import annotations

import queue
import re
import threading


# --------------------------------------------------------------------------
#  Нормализация текста перед синтезом (числа -> слова)
# --------------------------------------------------------------------------
def _normalize(text: str) -> str:
    """Заменяет числа словами: «14 часов» -> «четырнадцать часов»."""
    try:
        from num2words import num2words
    except Exception:
        return text
    return re.sub(r"\d+", lambda m: num2words(int(m.group()), lang="ru"), text)


# --------------------------------------------------------------------------
#  Движки синтеза. У каждого метод speak(text) — блокирующий, вызывается
#  из рабочего потока Speaker.
# --------------------------------------------------------------------------
class SileroBackend:
    """Нейросетевой русский голос Silero (офлайн, на CPU)."""

    def __init__(self, model_path: str, speaker: str = "baya",
                 sample_rate: int = 48000):
        import torch  # тяжёлый импорт — только если движок реально нужен

        from .winpath import native_path

        self._torch = torch
        torch.set_num_threads(max(1, (torch.get_num_threads() or 4)))
        # torch (C++) не открывает файлы по путям с кириллицей — берём
        # короткое ASCII-имя (как для модели Vosk).
        safe_path = native_path(model_path)
        if not safe_path.isascii():
            raise RuntimeError(
                "путь к модели содержит кириллицу, torch не может её открыть: "
                f"{safe_path}"
            )
        self._model = torch.package.PackageImporter(safe_path).load_pickle(
            "tts_models", "model")
        self._model.to(torch.device("cpu"))
        self._speaker = speaker
        self._sample_rate = sample_rate

    def speak(self, text: str) -> None:
        import sounddevice as sd

        audio = self._model.apply_tts(
            text=text,
            speaker=self._speaker,
            sample_rate=self._sample_rate,
            put_accent=True,
            put_yo=True,
        )
        sd.play(audio.numpy(), self._sample_rate)
        sd.wait()


class Sapi5Backend:
    """Системный голос Windows через pyttsx3/SAPI5."""

    def __init__(self, rate: int = 180, volume: float = 1.0,
                 voice_hint: str = "ru"):
        import pyttsx3

        self._engine = pyttsx3.init()
        self._engine.setProperty("rate", rate)
        self._engine.setProperty("volume", volume)
        hint = (voice_hint or "").lower()
        if hint:
            for voice in self._engine.getProperty("voices"):
                if hint in f"{voice.id} {voice.name}".lower():
                    self._engine.setProperty("voice", voice.id)
                    break

    def speak(self, text: str) -> None:
        self._engine.say(text)
        self._engine.runAndWait()


def _build_backend(config):
    """Создаёт движок по конфигу с откатом silero -> sapi5 -> None."""
    tts = config.section("tts")
    engine = str(tts.get("engine", "silero")).lower()

    if engine == "silero":
        try:
            model_path = config.resolve_path("tts.silero_model",
                                             "models/silero/v4_ru.pt")
            backend = SileroBackend(
                model_path=str(model_path),
                speaker=tts.get("speaker", "baya"),
                sample_rate=int(tts.get("sample_rate", 48000)),
            )
            print("[tts] Голос: Silero (нейросетевой)")
            return backend
        except Exception as exc:
            print(f"[tts] Silero недоступен ({exc}). Пробую системный голос.")
            engine = "sapi5"

    if engine == "sapi5":
        try:
            backend = Sapi5Backend(
                rate=int(tts.get("rate", 180)),
                volume=float(tts.get("volume", 1.0)),
                voice_hint=tts.get("voice_hint", "ru"),
            )
            print("[tts] Голос: системный (SAPI5)")
            return backend
        except Exception as exc:
            print(f"[tts] Системный голос недоступен ({exc}). Только текст.")

    return None


# --------------------------------------------------------------------------
#  Speaker — очередь фраз + рабочий поток
# --------------------------------------------------------------------------
class Speaker:
    def __init__(self, config):
        self.enabled = bool(config.get("assistant.speak_responses", True))
        self._config = config
        self._queue: "queue.Queue[str | None]" = queue.Queue()
        self._thread: threading.Thread | None = None
        if self.enabled:
            self._thread = threading.Thread(target=self._worker, daemon=True)
            self._thread.start()

    def _worker(self):
        # Движок создаём внутри потока: загрузка модели долгая, а SAPI5
        # требует инициализации и работы в одном потоке.
        backend = _build_backend(self._config)
        if backend is None:
            self.enabled = False
            return
        while True:
            text = self._queue.get()
            if text is None:
                break
            try:
                backend.speak(_normalize(text))
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
