"""ИИ-мозг: понимает свободную речь через облачную LLM (Gemini/Grok).

Вызывается, когда встроенная команда не совпала. LLM возвращает JSON с
речевым ответом и списком действий, которые исполняет executor. Может
также «выучить» новую команду — она сохранится и дальше сработает без ИИ.

Ключ и провайдер берутся из secrets.yaml (в git не попадает).
"""

from __future__ import annotations

import json
import re

# Пресеты провайдеров, работающих по OpenAI-совместимому протоколу.
PROVIDERS = {
    "gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "model": "gemini-2.0-flash",
    },
    "grok": {
        "base_url": "https://api.x.ai/v1",
        "model": "grok-2-latest",
    },
}

SYSTEM_PROMPT = """\
Ты — Миса, голосовой помощник на компьютере пользователя с Windows. Ты понимаешь
русскую речь и управляешь ПК. Пользователь говорит тебе фразу, а ты решаешь, что
сделать, и отвечаешь СТРОГО одним объектом JSON без markdown и пояснений.

Формат ответа:
{
  "say": "короткая фраза, которую ты произнесёшь вслух (по-русски, живо)",
  "actions": [ шаги ],           // что выполнить; можно пустой список []
  "learn": null | {              // если стоит запомнить команду на будущее
     "phrase": "ключевая фраза",
     "steps": [ шаги ]
  }
}

Шаг action — это объект {"type": ..., "value": ...}. Доступные типы:
  {"type":"app",   "value":"<название программы или команда запуска>"}
  {"type":"site",  "value":"<url или ключ сайта>"}
  {"type":"search","value":"<поисковый запрос>"}
  {"type":"key",   "value":"<горячие клавиши, напр. win+d, ctrl+c>"}
  {"type":"type",  "value":"<текст для набора в активном окне>"}
  {"type":"shell", "value":"<команда Windows cmd/powershell>"}   // полный контроль ПК
  {"type":"wait",  "value":<секунды>}
  {"type":"scenario","value":"<имя готового сценария>"}

Правила:
- Если это обычный разговор/вопрос — ответь в "say", "actions" пусти пустым.
- Для управления ПК (открыть, найти, громкость, папки, файлы, процессы и т.п.)
  используй подходящие шаги; для нестандартного — "shell".
- Команды shell должны быть безопасны и соответствовать просьбе. Не выполняй
  разрушительных действий, если пользователь явно об этом не попросил.
- Если пользователь просит ЗАПОМНИТЬ команду («запомни», «научись», «на будущее»),
  заполни "learn": фразу-триггер и шаги. Иначе "learn": null.
- Отвечай кратко — это озвучивается голосом.
"""


def _capabilities_block(apps, sites, scenarios) -> str:
    """Список известных программ/сайтов/сценариев для подсказки модели."""
    return (
        "Известные программы (ключи для type=app): "
        f"{', '.join(apps) or 'нет'}\n"
        "Известные сайты (ключи для type=site): "
        f"{', '.join(sites) or 'нет'}\n"
        "Известные сценарии: "
        f"{', '.join(scenarios) or 'нет'}"
    )


def _extract_json(text: str) -> dict:
    """Достаёт JSON-объект из ответа модели (снимает ```json ... ```)."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.MULTILINE).strip()
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end != -1 and end > start:
        text = text[start:end + 1]
    return json.loads(text)


class Brain:
    def __init__(self, config):
        from openai import OpenAI  # импорт только когда ИИ реально включён

        secrets = config.load_secrets()
        provider = str(secrets.get("provider", "gemini")).lower()
        api_key = secrets.get("api_key") or ""
        if not api_key:
            raise RuntimeError(
                "нет API-ключа. Запусти: python scripts\\setup_ai.py")
        preset = PROVIDERS.get(provider, PROVIDERS["gemini"])

        self.provider = provider
        self.model = secrets.get("model") or preset["model"]
        self.temperature = float(config.get("ai.temperature", 0.3))
        self._client = OpenAI(base_url=preset["base_url"], api_key=api_key)

        apps = list(config.section("apps").keys())
        sites = list(config.section("sites").keys())
        scenarios = list(config.section("scenarios").keys())
        self._system = SYSTEM_PROMPT + "\n" + _capabilities_block(
            apps, sites, scenarios)
        self._history: list[dict] = []  # короткая память диалога

    def think(self, text: str) -> dict:
        """Отправляет фразу в LLM, возвращает разобранный ответ (dict)."""
        messages = [{"role": "system", "content": self._system}]
        messages += self._history[-6:]
        messages.append({"role": "user", "content": text})

        resp = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
        )
        content = (resp.choices[0].message.content or "").strip()

        try:
            data = _extract_json(content)
        except Exception:
            # Модель ответила не-JSON — считаем это простым разговором.
            data = {"say": content or "Не поняла", "actions": [], "learn": None}

        # Обновляем память диалога.
        self._history.append({"role": "user", "content": text})
        self._history.append({"role": "assistant", "content": content})
        self._history = self._history[-12:]
        return data
