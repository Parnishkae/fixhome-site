"""Локальный HTTP-сервер: приём команд по сети (с телефона/приложения).

Эндпоинты:
  GET  /ping                      -> {"ok": true}
  POST /command {token, text}     -> {"reply": "..."}

Ответ формируется тем же движком, что и голос. Токен защищает от посторонних.
Это фундамент под мобильное приложение (и любой другой клиент).
"""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


def start_server(assistant, port: int, token: str, on_info=None):
    def info(msg: str):
        if on_info:
            on_info(msg)

    class Handler(BaseHTTPRequestHandler):
        def _send(self, code: int, obj: dict) -> None:
            body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Headers", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.end_headers()
            self.wfile.write(body)

        def do_OPTIONS(self):
            self._send(200, {"ok": True})

        def do_GET(self):
            if self.path.rstrip("/") in ("/ping", ""):
                self._send(200, {"ok": True, "name": "Misa"})
            else:
                self._send(404, {"error": "not found"})

        def do_POST(self):
            length = int(self.headers.get("Content-Length", "0") or 0)
            raw = self.rfile.read(length) if length else b""
            try:
                data = json.loads(raw.decode("utf-8") or "{}")
            except Exception:
                self._send(400, {"error": "bad json"})
                return
            if token and str(data.get("token", "")) != token:
                self._send(403, {"error": "forbidden"})
                return
            if self.path.rstrip("/") == "/command":
                text = str(data.get("text", ""))
                try:
                    reply = assistant.process_text(text)
                except Exception as exc:
                    self._send(500, {"error": str(exc)})
                    return
                self._send(200, {"reply": reply or "Готово"})
            else:
                self._send(404, {"error": "not found"})

        def log_message(self, *args):
            pass  # не шумим в консоль

    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    info(f"Сервер для телефона слушает порт {port}")
    return server
