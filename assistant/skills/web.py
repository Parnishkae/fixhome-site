"""Открытие сайтов и поиск в интернете."""

from __future__ import annotations

import urllib.parse
import webbrowser

from .. import actions
from ..dispatcher import Context, Intent

_SITE_TRIGGERS = ["зайди на", "перейди на", "открой сайт"]
_SEARCH_TRIGGERS = ["найди", "загугли", "поиск", "погугли", "найди в интернете"]


def _open_site(ctx: Context, text: str):
    sites = ctx.config.section("sites")
    target = text
    for t in _SITE_TRIGGERS:
        target = target.replace(t, " ")
    target = " ".join(target.split()).strip()
    key = next((k for k in sorted(sites, key=len, reverse=True) if k in target), None)
    actions.open_site(ctx.config, key or target)
    ctx.say(f"Открываю {key or target}")


def _search(ctx: Context, text: str):
    query = text
    for t in _SEARCH_TRIGGERS:
        query = query.replace(t, " ")
    for noise in ["в интернете", "в гугле", "в яндексе"]:
        query = query.replace(noise, " ")
    query = " ".join(query.split()).strip()
    if not query:
        ctx.say("Что найти?")
        return
    url = "https://www.google.com/search?q=" + urllib.parse.quote(query)
    webbrowser.open(url)
    ctx.say(f"Ищу {query}")


def build(config) -> list[Intent]:
    return [
        Intent("search_web", _SEARCH_TRIGGERS, _search, priority=3),
        Intent("open_site", _SITE_TRIGGERS, _open_site, priority=3),
    ]
