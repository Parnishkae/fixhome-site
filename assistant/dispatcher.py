"""Диспетчер команд: сопоставляет распознанный текст с навыками (intents)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

# Обработчик получает контекст и текст команды, возвращает ответ (или None).
Handler = Callable[["Context", str], "str | None"]


@dataclass
class Intent:
    name: str
    patterns: list[str]           # ключевые фразы-триггеры
    handler: Handler
    priority: int = 0             # выше приоритет -> проверяется раньше


class Context:
    """Всё, что нужно навыку для работы: конфиг + голос."""

    def __init__(self, config, speaker):
        self.config = config
        self.speaker = speaker
        # Разрешено ли ИИ/сценариям выполнять произвольные системные команды.
        self.allow_shell = bool(config.get("ai.allow_shell", True))
        # Необязательный хук: интерфейс (окно) получает произнесённый текст.
        self.on_say = None
        self._capture_list = None  # активный сбор ответов (для команд из сети)

    def say(self, text: str) -> str:
        # Если идёт «захват» (команда с телефона) — собираем текст и не
        # озвучиваем на ПК.
        if self._capture_list is not None:
            self._capture_list.append(text)
            return text
        self.speaker.say(text)
        if self.on_say:
            try:
                self.on_say(text)
            except Exception:
                pass
        return text

    def capture(self):
        """Контекст-менеджер: собирает ответы say() в список вместо озвучки."""
        ctx = self

        class _Capture:
            def __enter__(self_inner):
                self_inner.items = []
                ctx._capture_list = self_inner.items
                return self_inner.items

            def __exit__(self_inner, *exc):
                ctx._capture_list = None
                return False

        return _Capture()


class Dispatcher:
    def __init__(self, context: "Context"):
        self.context = context
        self._intents: list[Intent] = []

    def register(self, intent: Intent) -> None:
        self._intents.append(intent)
        # Сортируем: сначала высокий приоритет, потом длинные паттерны
        # (более специфичные фразы обрабатываются раньше общих).
        self._intents.sort(
            key=lambda i: (i.priority, max((len(p) for p in i.patterns), default=0)),
            reverse=True,
        )

    def register_all(self, intents: list[Intent]) -> None:
        for intent in intents:
            self.register(intent)

    def match(self, text: str) -> Intent | None:
        for intent in self._intents:
            if any(pattern in text for pattern in intent.patterns):
                return intent
        return None

    def handle(self, text: str) -> bool:
        """Находит и выполняет подходящий навык. True — если что-то сделали."""
        intent = self.match(text)
        if intent is None:
            return False
        try:
            intent.handler(self.context, text)
        except Exception as exc:
            self.context.say(f"Не получилось выполнить: {exc}")
        return True
