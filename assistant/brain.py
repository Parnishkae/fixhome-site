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
        "model": "grok-3",
    },
    # Groq (НЕ Grok!) — быстрый и щедрый бесплатный API, ключ на console.groq.com
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "model": "llama-3.3-70b-versatile",
    },
    # OpenRouter — агрегатор, есть бесплатные модели (openrouter.ai)
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "model": "meta-llama/llama-3.3-70b-instruct:free",
    },
    # Ollama — локально, офлайн, бесплатно (нужен установленный ollama)
    "ollama": {
        "base_url": "http://localhost:11434/v1",
        "model": "llama3.1",
    },
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-4o-mini",
    },
}

# Мультимодальные модели (умеют «видеть» картинку) по провайдерам.
VISION_MODELS = {
    "gemini": "gemini-2.0-flash",
    "grok": "grok-2-vision-1212",
    "groq": "meta-llama/llama-4-scout-17b-16e-instruct",
    "openrouter": "meta-llama/llama-3.2-11b-vision-instruct",
    "ollama": "llama3.2-vision",
    "openai": "gpt-4o-mini",
}

VISION_HINT = """
Сейчас к сообщению приложен СКРИНШОТ экрана пользователя. Смотри на него и
отвечай/действуй по тому, что видишь. Если просят кликнуть по элементу —
верни action click/double_click с координатами "x,y" в пикселях РЕАЛЬНОГО
экрана (его размер указан в сообщении). Координаты — центр нужного элемента.
"""

SYSTEM_PROMPT = """\
Ты — Миса, голосовой помощник на компьютере пользователя с Windows. Ты понимаешь
русскую речь и управляешь ПК. Пользователь говорит тебе фразу, а ты решаешь, что
сделать, и отвечаешь СТРОГО одним объектом JSON без markdown и пояснений.

Формат ответа:
{
  "say": "короткая фраза, которую ты произнесёшь вслух (по-русски, живо)",
  "actions": [ шаги ],           // что выполнить; можно пустой список []
  "learn": null | {              // если стоит запомнить КОМАНДУ (фраза -> действия)
     "phrase": "ключевая фраза",
     "steps": [ шаги ]
  },
  "memory": null | "факт",       // если стоит запомнить ФАКТ о пользователе
  "agent": false                 // true, если это МНОГОШАГОВАЯ задача (см. ниже)
}

Ставь "agent": true, если задача требует нескольких действий с проверкой
результата («открой X, найди Y, сделай Z, сохрани») — тогда её выполнит
пошаговый агент. Для простых одиночных команд — false.

Шаг action — это объект {"type": ..., "value": ...}. Доступные типы:
  {"type":"app",   "value":"<название программы, лучше как в системе: Opera, Steam, Photoshop>"}
  {"type":"site",  "value":"<url или ключ сайта>"}
  {"type":"search","value":"<поисковый запрос>"}
  {"type":"key",   "value":"<горячие клавиши, напр. win+d, ctrl+c>"}
  {"type":"type",  "value":"<текст для набора в активном окне>"}
  {"type":"shell", "value":"<команда Windows cmd/powershell>"}   // полный контроль ПК
  {"type":"wait",  "value":<секунды>}
  {"type":"scenario","value":"<имя готового сценария>"}
  {"type":"click", "value":"x,y"}         // клик мышью по координатам экрана
  {"type":"double_click","value":"x,y"}
  {"type":"right_click","value":"x,y"}
  {"type":"scroll","value":<число, + вверх / - вниз>}

Правила:
- Если это обычный разговор/вопрос — ответь в "say", "actions" пусти пустым.
- Для управления ПК (открыть, найти, громкость, папки, файлы, процессы и т.п.)
  используй подходящие шаги; для нестандартного — "shell".
- Команды shell должны быть безопасны и соответствовать просьбе. Не выполняй
  разрушительных действий, если пользователь явно об этом не попросил.
- Если пользователь просит ЗАПОМНИТЬ команду («когда я говорю X — делай Y»),
  заполни "learn". Если просит запомнить ФАКТ о себе («меня зовут…», «мой
  браузер…», «я работаю…») — заполни "memory" коротким фактом. Иначе — null.
- Учитывай то, что ты уже помнишь о пользователе (блок ниже).
- Отвечай кратко — это озвучивается голосом.
"""


AGENT_SYSTEM = """\
Ты — Миса, автономный агент на компьютере с Windows. Тебе дают ЦЕЛЬ, и ты
достигаешь её ПО ШАГАМ, сам решая, что делать дальше по результатам.

На каждом шаге отвечай СТРОГО одним объектом JSON без markdown:
{
  "thought": "коротко: что делаю и зачем",
  "action": null | {"type": ..., "value": ...},   // ОДНО действие за шаг
  "observe_screen": true|false,   // нужен ли скриншот экрана перед след. шагом
  "say": "короткая реплика вслух о прогрессе (можно пустую)",
  "done": true|false,             // цель достигнута?
  "result": "итоговый ответ пользователю, когда done=true"
}

Типы action: app, site, search, key, type, shell, wait, click, double_click,
right_click, scroll (как обычно). Для сложного используй shell — тебе вернётся
его вывод как наблюдение. Ставь observe_screen=true, когда нужно проверить
результат глазами (после этого получишь скриншот).

Правила:
- Делай по ОДНОМУ действию за шаг и жди наблюдения.
- Опирайся на наблюдения из истории (вывод команд, скриншоты).
- Не выполняй разрушительных действий без явной просьбы.
- Как только цель достигнута — done=true и заполни result.
- Если застрял или невозможно — done=true и честно опиши в result.
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


def _memory_prompt() -> str:
    from . import memory
    return memory.as_prompt()


def _format_log(log: list[dict]) -> str:
    """История шагов агента в компактный текст."""
    if not log:
        return "(пока пусто — это первый шаг)"
    lines = []
    for i, step in enumerate(log, 1):
        action = step.get("action")
        obs = step.get("observation", "")
        lines.append(f"{i}. мысль: {step.get('thought', '')}")
        if action:
            lines.append(f"   действие: {action}")
        if obs:
            lines.append(f"   наблюдение: {obs}")
    return "\n".join(lines)


def _extract_json(text: str) -> dict:
    """Достаёт JSON-объект из ответа модели (снимает ```json ... ```)."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.MULTILINE).strip()
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end != -1 and end > start:
        text = text[start:end + 1]
    return json.loads(text)


class Brain:
    def __init__(self, config, extra_prompt: str = ""):
        from openai import OpenAI  # импорт только когда ИИ реально включён

        secrets = config.load_secrets()
        provider = str(secrets.get("provider", "gemini")).lower()
        api_key = secrets.get("api_key") or ""
        # Ollama работает локально без ключа — подставим заглушку.
        if provider == "ollama" and not api_key:
            api_key = "ollama"
        if not api_key:
            raise RuntimeError(
                "нет API-ключа. Запусти: python scripts\\setup_ai.py")
        preset = PROVIDERS.get(provider, PROVIDERS["gemini"])

        self.config = config
        self.provider = provider
        self.model = secrets.get("model") or preset["model"]
        self.temperature = float(config.get("ai.temperature", 0.3))
        self._client = OpenAI(base_url=preset["base_url"], api_key=api_key)

        apps = list(config.section("apps").keys())
        sites = list(config.section("sites").keys())
        scenarios = list(config.section("scenarios").keys())
        self._system = SYSTEM_PROMPT + "\n" + _capabilities_block(
            apps, sites, scenarios)
        if extra_prompt and extra_prompt.strip():
            self._system += "\n\nДополнительно от плагинов:\n" + extra_prompt.strip()
        self._history: list[dict] = []  # короткая память диалога

        # --- Зрение (мультимодальная модель) ---
        self.vision_enabled = bool(config.get("ai.vision.enabled", True))
        self.vision_model = (config.get("ai.vision.model")
                             or VISION_MODELS.get(provider) or self.model)
        self.vision_max_width = int(config.get("ai.vision.max_width", 1280))
        self.has_vision = self.vision_enabled and bool(self.vision_model)

    def _complete(self, messages: list, model: str) -> dict:
        """Запрос к модели + разбор JSON + запись в память диалога."""
        resp = self._client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=self.temperature,
        )
        content = (resp.choices[0].message.content or "").strip()
        try:
            data = _extract_json(content)
        except Exception:
            data = {"say": content or "Не поняла", "actions": [], "learn": None}
        return data

    def _system_messages(self, extra: str = "") -> list[dict]:
        """Системные сообщения: правила + актуальная память о пользователе."""
        from . import memory

        content = self._system + (("\n" + extra) if extra else "")
        msgs = [{"role": "system", "content": content}]
        mem = memory.as_prompt()
        if mem:
            msgs.append({"role": "system", "content": mem})
        return msgs

    def think(self, text: str) -> dict:
        """Отправляет фразу в LLM (без картинки)."""
        messages = self._system_messages()
        messages += self._history[-6:]
        messages.append({"role": "user", "content": text})

        data = self._complete(messages, self.model)

        self._history.append({"role": "user", "content": text})
        self._history.append(
            {"role": "assistant", "content": json.dumps(data, ensure_ascii=False)})
        self._history = self._history[-12:]
        return data

    def look(self, text: str) -> dict:
        """Делает скриншот и отправляет его в мультимодальную модель вместе
        с фразой пользователя. Возвращает такой же ответ, как think()."""
        from .screen import capture_data_uri

        data_uri, (w, h) = capture_data_uri(self.vision_max_width)
        user_text = f"{text}\n\n(Размер реального экрана: {w}x{h} пикселей.)"
        messages = self._system_messages(VISION_HINT)
        messages.append({"role": "user", "content": [
            {"type": "text", "text": user_text},
            {"type": "image_url", "image_url": {"url": data_uri}},
        ]})
        return self._complete(messages, self.vision_model)

    def to_steps(self, description: str) -> list:
        """Преобразует устное описание действия в список шагов (для обучения)."""
        instruction = (
            "Пользователь описывает действие для команды. Верни СТРОГО JSON "
            '{"steps": [ {"type":..., "value":...}, ... ]} — шаги для выполнения '
            "этого на Windows. Типы: app, site, search, key, type, shell, wait, "
            "click, scroll, say. Без пояснений, только JSON."
        )
        messages = [
            {"role": "system", "content": self._system + "\n" + instruction},
            {"role": "user", "content": description},
        ]
        data = self._complete(messages, self.model)
        steps = data.get("steps") or data.get("actions") or []
        return steps if isinstance(steps, list) else []

    def agent_step(self, goal: str, log: list[dict],
                   screenshot_uri: str | None = None) -> dict:
        """Один шаг автономного агента.

        goal — цель; log — история [{thought, action, observation}];
        screenshot_uri — скриншот, если на прошлом шаге просили observe_screen.
        """
        system = AGENT_SYSTEM + "\n" + _capabilities_block(
            list(self.config.section("apps").keys()),
            list(self.config.section("sites").keys()),
            list(self.config.section("scenarios").keys()),
        )
        user_text = f"ЦЕЛЬ: {goal}\n\nИстория шагов:\n{_format_log(log)}\n\n" \
                    "Твой следующий шаг (JSON):"

        messages = [{"role": "system", "content": system}]
        mem = _memory_prompt()
        if mem:
            messages.append({"role": "system", "content": mem})

        if screenshot_uri:
            messages.append({"role": "user", "content": [
                {"type": "text", "text": user_text},
                {"type": "image_url", "image_url": {"url": screenshot_uri}},
            ]})
            model = self.vision_model
        else:
            messages.append({"role": "user", "content": user_text})
            model = self.model

        return self._complete(messages, model)
