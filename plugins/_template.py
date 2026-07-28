"""ШАБЛОН Python-плагина (не активен — имя начинается с "_").

Чтобы включить: скопируй в файл без "_", например  my_plugin.py

Python-плагин даёт полную свободу: своя логика, любые библиотеки.
Точка входа — функция register(api).
"""

from __future__ import annotations

# Готовые действия помощника можно переиспользовать:
from assistant import actions


def register(api):
    # 1) Команда из готовых шагов (как в YAML):
    api.add_command(
        ["скажи привет", "поздоровайся"],
        steps=[{"say": "Привет! Я Миса."}],
    )

    # 2) Команда со своей логикой. handler(ctx, text):
    #    ctx.say(...) — сказать;  ctx.config — доступ к настройкам.
    def battery(ctx, text):
        try:
            import psutil
            p = psutil.sensors_battery()
            if p is None:
                ctx.say("Не вижу батарею, похоже это ПК")
            else:
                ctx.say(f"Заряд батареи {int(p.percent)} процентов")
        except Exception as exc:
            ctx.say(f"Не смогла проверить батарею: {exc}")

    api.add_command(["сколько заряда", "уровень батареи"], handler=battery)

    # 3) Добавить инструкцию/знания в ИИ (влияет на ответы ИИ):
    api.add_prompt("Ты дружелюбная и отвечаешь с лёгким юмором.")

    # 4) Можно дергать действия напрямую:
    def open_notes(ctx, text):
        actions.open_app(ctx.config, "notepad.exe")
        ctx.say("Открыла заметки")

    api.add_command("открой заметки", handler=open_notes)
