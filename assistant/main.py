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

from . import learned
from .config import Config
from .dispatcher import Context, Dispatcher
from .executor import run_steps
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


def _init_brain(config, speaker):
    """Поднимает ИИ-мозг, если он включён в конфиге. Иначе None."""
    if not config.get("ai.enabled", False):
        return None
    try:
        from .brain import Brain
        brain = Brain(config)
        print(f"[ai] Мозг подключён: {brain.provider} / {brain.model}")
        return brain
    except Exception as exc:
        print(f"[ai] ИИ недоступен ({exc}). Работаю без него.")
        return None


def _short_ai_error(exc: Exception) -> str:
    """Короткая фраза для озвучки вместо длинного текста ошибки API."""
    text = str(exc).lower()
    if "429" in text or "quota" in text or "resource_exhausted" in text \
            or "rate limit" in text:
        return "Закончился лимит запросов к ИИ. Попробуй позже или смени провайдера"
    if "model not found" in text or "does not exist" in text or "404" in text:
        return "Модель ИИ недоступна. Проверь настройки ключа"
    if "401" in text or "invalid" in text and "key" in text or "api key" in text:
        return "Ключ ИИ не принят. Проверь его в настройках"
    if "connect" in text or "timeout" in text or "getaddrinfo" in text:
        return "Нет связи с ИИ. Проверь интернет"
    return "ИИ не смог ответить"


def _handle_with_brain(brain, context, dispatcher, command: str) -> None:
    """Отдаёт нераспознанную фразу ИИ, исполняет ответ, учит новые команды."""
    try:
        result = brain.think(command)
    except Exception as exc:
        print(f"[ai] Ошибка запроса: {exc}")   # полный текст — в консоль
        context.say(_short_ai_error(exc))       # короткая фраза — голосом
        return

    say = result.get("say")
    if say:
        context.say(str(say))
    run_steps(context, result.get("actions") or [])

    # Саморазвитие: если ИИ решил запомнить команду — сохраняем и
    # регистрируем её как навык прямо сейчас.
    learn = result.get("learn")
    if isinstance(learn, dict) and learn.get("phrase") and learn.get("steps"):
        phrase, steps = str(learn["phrase"]), learn["steps"]
        learned.save_command(phrase, steps)
        dispatcher.register(learned.make_intent(phrase, steps))
        print(f"[ai] Выучена команда: «{phrase}»")


def run(config: Config) -> None:
    # --- Инициализация компонентов ---
    speaker = Speaker(config)

    recognizer = SpeechRecognizer(
        model_path=config.resolve_path("speech.model_path"),
        sample_rate=config.get("speech.sample_rate", 16000),
        input_device=config.get("speech.input_device"),
    )

    context = Context(config, speaker)
    dispatcher = Dispatcher(context)
    dispatcher.register_all(build_intents(config))
    dispatcher.register_all(learned.build_intents())  # выученные команды

    brain = _init_brain(config, speaker)

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
                pass  # выполнила встроенную/выученную команду
            elif brain is not None:
                _handle_with_brain(brain, context, dispatcher, command)
            else:
                speaker.say("Не поняла команду. Включи ИИ, чтобы я понимала свободную речь")
            active_until = now + timeout  # продлеваем окно после любой реакции
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
