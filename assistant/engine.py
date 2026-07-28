"""Движок помощника: распознавание -> имя -> команда -> действие -> ответ.

Отделён от интерфейса. События (статус, что услышал, что ответил)
отдаёт через callback on_event(kind, text), поэтому один и тот же движок
работает и в консоли (main.py), и в окне (app.py).

kind:  "status" (sleep|listen|think|work) | "heard" | "say" | "info"
"""

from __future__ import annotations

import time
from typing import Callable

from . import learned, memory
from .config import Config
from .dispatcher import Context, Dispatcher
from .executor import run_steps
from .recognizer import SpeechRecognizer
from .skills import build_intents
from .tts import Speaker

_EXIT_PHRASES = ("выключись", "завершение работы", "закрой себя", "стоп работа")
_RELOAD_PHRASES = ("перезагрузи настройки", "обнови настройки",
                   "перечитай конфиг", "перезагрузи конфиг")
# Фразы, при которых помощник смотрит на экран (делает скриншот для ИИ).
_FORGET_PHRASES = ("забудь всё", "забудь все", "очисти память", "сотри память")
_VISION_PHRASES = (
    "на экране", "что это", "что тут", "что здесь", "посмотри", "прочитай",
    "переведи", "опиши экран", "что открыто", "что видишь", "нажми на",
    "кликни", "найди на экране", "что написано", "разбери ошибку",
)

EventCallback = Callable[[str, str], None]


def _contains_wake_word(text: str, wake_words: list[str]) -> str | None:
    for word in wake_words:
        if word in text:
            return word
    return None


def _strip_wake_word(text: str, wake_word: str) -> str:
    return " ".join(text.replace(wake_word, " ").split()).strip()


def _short_ai_error(exc: Exception) -> str:
    text = str(exc).lower()
    if any(s in text for s in ("429", "quota", "resource_exhausted", "rate limit")):
        return "Закончился лимит запросов к ИИ. Попробуй позже или смени провайдера"
    if any(s in text for s in ("model not found", "does not exist", "404")):
        return "Модель ИИ недоступна. Проверь настройки ключа"
    if "401" in text or "api key" in text or ("invalid" in text and "key" in text):
        return "Ключ ИИ не принят. Проверь его в настройках"
    if any(s in text for s in ("connect", "timeout", "getaddrinfo")):
        return "Нет связи с ИИ. Проверь интернет"
    return "ИИ не смог ответить"


class Assistant:
    def __init__(self, config: Config, on_event: EventCallback | None = None):
        self.config = config
        self._on_event = on_event or (lambda kind, text: None)
        self._stop = False

        self.speaker = Speaker(config)
        self.recognizer = SpeechRecognizer(
            model_path=config.resolve_path("speech.model_path"),
            sample_rate=config.get("speech.sample_rate", 16000),
            input_device=config.get("speech.input_device"),
        )
        # Ответы помощника (через Context.say) дублируем в интерфейс.
        self.context = Context(config, self.speaker)
        self.context.on_say = lambda text: self._emit("say", text)

        self.dispatcher = Dispatcher(self.context)
        self.dispatcher.register_all(build_intents(config))
        self.dispatcher.register_all(learned.build_intents())

        self.brain = self._init_brain()

        self.wake_words = [w.lower() for w in
                           config.get("assistant.wake_words", ["миса"])]
        self.timeout = float(config.get("assistant.listen_timeout", 8))

    # --- события интерфейсу ---
    def _emit(self, kind: str, text: str = "") -> None:
        try:
            self._on_event(kind, text)
        except Exception:
            pass

    def _init_brain(self):
        if not self.config.get("ai.enabled", False):
            return None
        try:
            from .brain import Brain
            brain = Brain(self.config)
            self._emit("info", f"Мозг подключён: {brain.provider} / {brain.model}")
            return brain
        except Exception as exc:
            self._emit("info", f"ИИ недоступен: {exc}")
            return None

    def _run_brain(self, command: str, vision: bool = False) -> None:
        self._emit("status", "think")
        try:
            if vision and self.brain.has_vision:
                self._emit("info", "Смотрю на экран…")
                result = self.brain.look(command)
            else:
                result = self.brain.think(command)
        except Exception as exc:
            print(f"[ai] Ошибка запроса: {exc}")
            self.context.say(_short_ai_error(exc))
            return
        say = result.get("say")
        if say:
            self.context.say(str(say))
        run_steps(self.context, result.get("actions") or [])
        learn = result.get("learn")
        if isinstance(learn, dict) and learn.get("phrase") and learn.get("steps"):
            phrase, steps = str(learn["phrase"]), learn["steps"]
            learned.save_command(phrase, steps)
            self.dispatcher.register(learned.make_intent(phrase, steps))
            self._emit("info", f"Выучена команда: «{phrase}»")

        fact = result.get("memory")
        if isinstance(fact, str) and fact.strip():
            memory.add_fact(fact)
            self._emit("info", f"Запомнила: {fact}")

    def _reload_config(self) -> None:
        """Перечитывает config.yaml и выученные команды без перезапуска."""
        self.config = Config.load()
        self.context.config = self.config
        self.context.allow_shell = bool(self.config.get("ai.allow_shell", True))
        self.dispatcher = Dispatcher(self.context)
        self.dispatcher.register_all(build_intents(self.config))
        self.dispatcher.register_all(learned.build_intents())
        self.wake_words = [w.lower() for w in
                           self.config.get("assistant.wake_words", ["миса"])]
        self.timeout = float(self.config.get("assistant.listen_timeout", 8))
        self._emit("info", "Настройки перезагружены")
        self.context.say("Настройки перезагружены")

    def stop(self) -> None:
        self._stop = True

    def run(self) -> None:
        self.speaker.say("Я на связи")
        active_until = 0.0
        status = "sleep"
        self._emit("status", "sleep")

        for phrase in self.recognizer.phrases():
            if self._stop:
                break
            now = time.monotonic()
            self._emit("heard", phrase)

            if any(p in phrase for p in _EXIT_PHRASES):
                self.context.say("Отключаюсь. До встречи")
                break

            wake = _contains_wake_word(phrase, self.wake_words)
            command = None

            if wake:
                command = _strip_wake_word(phrase, wake)
                if not command:
                    self.context.say("Слушаю")
                    active_until = now + self.timeout
                    status = "listen"
                    self._emit("status", "listen")
                    continue
            elif now < active_until:
                command = phrase
            else:
                if status != "sleep":
                    status = "sleep"
                    self._emit("status", "sleep")
                continue

            wants_vision = any(p in command for p in _VISION_PHRASES)

            if any(p in command for p in _FORGET_PHRASES):
                self._emit("status", "work")
                memory.clear()
                self.context.say("Хорошо, всё забыла")
            elif any(p in command for p in _RELOAD_PHRASES):
                self._emit("status", "work")
                self._reload_config()
            elif wants_vision and self.brain is not None and self.brain.has_vision:
                # «Экранные» команды идут в зрение, минуя встроенные навыки.
                self._run_brain(command, vision=True)
            elif self.dispatcher.handle(command):
                self._emit("status", "work")
            elif self.brain is not None:
                self._run_brain(command)
            else:
                self.context.say("Не поняла команду. Включи ИИ для свободной речи")

            active_until = now + self.timeout
            status = "listen"
            self._emit("status", "listen")

        self.speaker.stop()
