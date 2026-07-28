"""Захват экрана для «зрения» помощника.

Делает скриншот, ужимает по ширине (чтобы быстрее и дешевле уходило в ИИ)
и кодирует в data-URI (base64 PNG) для отправки в мультимодальную модель.
"""

from __future__ import annotations

import base64
import io


def capture_data_uri(max_width: int = 1280) -> tuple[str, tuple[int, int]]:
    """Возвращает (data_uri, (ширина, высота) реального экрана).

    Реальный размер экрана отдаём отдельно — по нему модель может назвать
    координаты для клика, даже если картинку мы ужали.
    """
    from PIL import ImageGrab

    img = ImageGrab.grab()
    real_w, real_h = img.size

    if max_width and real_w > max_width:
        ratio = max_width / real_w
        img = img.resize((max_width, int(real_h * ratio)))

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/png;base64,{b64}", (real_w, real_h)
