"""Распознавание речи через Whisper API (Groq/OpenAI) — точнее, чем Vosk.

Слушает микрофон, простым детектором громкости (VAD) вырезает фразы
(речь между паузами) и отправляет каждую в Whisper на расшифровку.
Интерфейс тот же, что у SpeechRecognizer: метод phrases() — генератор строк.
Требует интернет.
"""

from __future__ import annotations

import io
import queue
import wave

import numpy as np
import sounddevice as sd


class WhisperRecognizer:
    def __init__(self, base_url: str, api_key: str,
                 model: str = "whisper-large-v3-turbo",
                 sample_rate: int = 16000, input_device=None,
                 language: str = "ru", vad_threshold: int = 500,
                 silence_sec: float = 0.8, min_speech_sec: float = 0.3,
                 max_speech_sec: float = 15.0):
        from openai import OpenAI

        self._client = OpenAI(base_url=base_url, api_key=api_key)
        self._model = model
        self.sample_rate = sample_rate
        self.input_device = input_device
        self.language = language
        self._threshold = vad_threshold
        self._silence_sec = silence_sec
        self._min_speech_sec = min_speech_sec
        self._max_speech_sec = max_speech_sec
        self._q: "queue.Queue[bytes]" = queue.Queue()

    def _callback(self, indata, frames, time_info, status):
        self._q.put(bytes(indata))

    def _transcribe(self, pcm: bytes) -> str:
        buf = io.BytesIO()
        with wave.open(buf, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(self.sample_rate)
            w.writeframes(pcm)
        buf.seek(0)
        buf.name = "speech.wav"
        try:
            resp = self._client.audio.transcriptions.create(
                model=self._model, file=buf, language=self.language,
                temperature=0)
            return (resp.text or "").strip()
        except Exception as exc:
            print(f"[whisper] ошибка расшифровки: {exc}")
            return ""

    def phrases(self):
        blocksize = int(self.sample_rate * 0.03)  # блок ~30 мс
        speech = bytearray()
        in_speech = False
        silence = 0.0

        with sd.RawInputStream(samplerate=self.sample_rate, blocksize=blocksize,
                               dtype="int16", channels=1,
                               device=self.input_device, callback=self._callback):
            while True:
                data = self._q.get()
                arr = np.frombuffer(data, dtype=np.int16)
                if arr.size == 0:
                    continue
                rms = float(np.sqrt(np.mean(arr.astype(np.float32) ** 2)))
                block_sec = arr.size / self.sample_rate

                if rms >= self._threshold:
                    in_speech = True
                    silence = 0.0
                    speech += data
                elif in_speech:
                    speech += data
                    silence += block_sec
                    if silence >= self._silence_sec:
                        text = self._flush(speech)
                        speech, in_speech, silence = bytearray(), False, 0.0
                        if text:
                            yield text

                # предохранитель на слишком длинную фразу
                if len(speech) / 2 / self.sample_rate > self._max_speech_sec:
                    text = self._flush(speech)
                    speech, in_speech, silence = bytearray(), False, 0.0
                    if text:
                        yield text

    def _flush(self, speech: bytearray) -> str:
        if len(speech) / 2 / self.sample_rate < self._min_speech_sec:
            return ""
        text = self._transcribe(bytes(speech))
        return text.lower().strip(" .,!?") if text else ""

    def reset(self) -> None:
        pass
