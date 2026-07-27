"""Точка входа: главный цикл голосового помощника «Миса».

Запуск:
    python -m assistant.main
    python -m assistant.main --list-mics     # показать микрофоны
    python -m assistant.main --config path    # свой конфиг
"""

from __future__ import annotations

import argparse
import sys
import time

from .config import Config
from .dispatcher import Context, Dispatcher
from .recognizer import SpeechRecognizer, list_microphones
from .skills import build_intents
from .tts import Speaker

# Фразы, по которым помощник завершает работу.
_EXIT_PHRASES = ("выключись", "завершение работы", "закрой себя", "стоп работа")


def _contains_wake_word(text: str, wake_words: list[str]) -> str | None:
    for word in wake_words:
        if word in text:
            return word
    return None


def _strip_wake_word(text: str, wake_word: str) -> str:
    return " ".join(text.replace(wake_word, " ").split()).strip()


def run(config: Config) -> None:
    # --- Инициализация компонентов ---
    tts_cfg = config.section("tts")
    speaker = Speaker(
        rate=tts_cfg.get("rate", 180),
        volume=tts_cfg.get("volume", 1.0),
        voice_hint=tts_cfg.get("voice_hint", "ru"),
        enabled=config.get("assistant.speak_responses", True),
    )

    recognizer = SpeechRecognizer(
        model_path=config.resolve_path("speech.model_path"),
        sample_rate=config.get("speech.sample_rate", 16000),
        input_device=config.get("speech.input_device"),
    )

    context = Context(config, speaker)
    dispatcher = Dispatcher(context)
    dispatcher.register_all(build_intents(config))

    wake_words = [w.lower() for w in config.get("assistant.wake_words", ["миса"])]
    timeout = float(config.get("assistant.listen_timeout", 8))

    print("=" * 56)
    print(f"  Помощник запущен. Скажи «{wake_words[0].capitalize()}», чтобы разбудить.")
    print("  Ctrl+C — выход.")
    print("=" * 56)
    speaker.say("Я на связи")

    active_until = 0.0  # до какого момента слушаем команды без имени

    try:
        for phrase in recognizer.phrases():
            print(f"👂 распознано: {phrase}")
            now = time.monotonic()

            if any(p in phrase for p in _EXIT_PHRASES):
                speaker.say("Отключаюсь. До встречи")
                break

            wake = _contains_wake_word(phrase, wake_words)
            command = None

            if wake:
                command = _strip_wake_word(phrase, wake)
                if not command:
                    # Только имя — переходим в режим ожидания команды.
                    speaker.say("Слушаю")
                    active_until = now + timeout
                    continue
            elif now < active_until:
                # Мы в активном окне после имени — фраза считается командой.
                command = phrase
            else:
                continue  # спим, имя не прозвучало

            if dispatcher.handle(command):
                active_until = now + timeout  # продлеваем окно после команды
            else:
                speaker.say("Не поняла команду")
                active_until = now + timeout
    except KeyboardInterrupt:
        print("\nОстановлено пользователем.")
    finally:
        speaker.stop()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Голосовой помощник «Миса»")
    parser.add_argument("--config", help="путь к config.yaml")
    parser.add_argument("--list-mics", action="store_true",
                        help="показать доступные микрофоны и выйти")
    args = parser.parse_args(argv)

    if args.list_mics:
        print(list_microphones())
        return 0

    try:
        config = Config.load(args.config)
        run(config)
    except (FileNotFoundError, KeyboardInterrupt) as exc:
        print(f"\n{exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
