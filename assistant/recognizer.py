"""Офлайн-распознавание речи через Vosk + захват микрофона (sounddevice)."""

from __future__ import annotations

import json
import queue
import sys
from pathlib import Path

import sounddevice as sd
from vosk import KaldiRecognizer, Model, SetLogLevel

SetLogLevel(-1)  # приглушаем внутренние логи Vosk


def list_microphones() -> str:
    """Строка со списком доступных устройств ввода (для --list-mics)."""
    lines = ["Доступные устройства ввода:"]
    for idx, dev in enumerate(sd.query_devices()):
        if dev.get("max_input_channels", 0) > 0:
            lines.append(f"  [{idx}] {dev['name']}")
    return "\n".join(lines)


class SpeechRecognizer:
    """Непрерывно слушает микрофон и выдаёт распознанные фразы."""

    def __init__(self, model_path: str | Path, sample_rate: int = 16000,
                 input_device: int | None = None):
        model_path = Path(model_path)
        if not model_path.exists():
            raise FileNotFoundError(
                f"Модель Vosk не найдена: {model_path}\n"
                "Скачай русскую модель и распакуй её (см. README, «Установка»):\n"
                "  https://alphacephei.com/vosk/models"
            )
        self.sample_rate = sample_rate
        self.input_device = input_device
        self._model = Model(str(model_path))
        self._rec = KaldiRecognizer(self._model, sample_rate)
        self._audio_q: "queue.Queue[bytes]" = queue.Queue()

    def _callback(self, indata, frames, time_info, status):
        if status:
            print(f"[mic] {status}", file=sys.stderr)
        self._audio_q.put(bytes(indata))

    def phrases(self):
        """Генератор: выдаёт финальные распознанные фразы (строки в нижнем регистре)."""
        with sd.RawInputStream(
            samplerate=self.sample_rate,
            blocksize=8000,
            dtype="int16",
            channels=1,
            device=self.input_device,
            callback=self._callback,
        ):
            while True:
                data = self._audio_q.get()
                if self._rec.AcceptWaveform(data):
                    result = json.loads(self._rec.Result())
                    text = result.get("text", "").strip()
                    if text:
                        yield text.lower()

    def reset(self) -> None:
        """Сбрасывает состояние распознавателя между сессиями."""
        self._rec = KaldiRecognizer(self._model, self.sample_rate)
