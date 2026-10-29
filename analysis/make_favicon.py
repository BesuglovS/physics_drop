# -*- coding: utf-8 -*-
"""Рисует favicon проекта: мяч, шкала и траектория отскока.

Запуск: python analysis/make_favicon.py
Создаёт favicon.ico, favicon.svg и PNG-размеры рядом со скриптом.
"""
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

A = Path(__file__).resolve().parent
S = 1024


def bezier(p0, p1, p2, p3, n=240):
    pts = []
    for i in range(n + 1):
        t = i / n
        u = 1 - t
        x = u**3 * p0[0] + 3 * u**2 * t * p1[0] + 3 * u * t**2 * p2[0] + t**3 * p3[0]
        y = u**3 * p0[1] + 3 * u**2 * t * p1[1] + 3 * u * t**2 * p2[1] + t**3 * p3[1]
        pts.append((x, y))
    return pts


def dashed(draw, pts, fill, width, on=28, off=18):
    """Рисует пунктир вдоль массива точек."""
    acc = 0.0
    drawing = True
    prev = pts[0]
    for cur in pts[1:]:
        seg = math.hypot(cur[0] - prev[0], cur[1] - prev[1])
        # разбиваем длинный сегмент на части, чтобы переключать пунктир
        steps = max(1, int(seg / 2))
        for k in range(steps):
            t0 = k / steps
            t1 = (k + 1) / steps
            p0 = (prev[0] + (cur[0] - prev[0]) * t0, prev[1] + (cur[1] - prev[1]) * t0)
            p1 = (prev[0] + (cur[0] - prev[0]) * t1, prev[1] + (cur[1] - prev[1]) * t1)
            d = seg / steps
            if drawing:
                draw.line([p0, p1], fill=fill, width=width)
            acc += d
            if drawing and acc >= on:
                drawing = False
                acc = 0.0
            elif not drawing and acc >= off:
                drawing = True
                acc = 0.0
        prev = cur


def main():
    # фон: тёмный сине-серый градиент, как в hero отчёта
    yy, xx = np.mgrid[0:S, 0:S]
    t = np.clip((xx + yy) / (2 * S), 0, 1)
    c1 = np.array([17, 24, 38], dtype=np.float32)
    c2 = np.array([34, 48, 77], dtype=np.float32)
    bg = (c1 + (c2 - c1) * t[..., None]).astype(np.uint8)
    img = Image.fromarray(bg, "RGB").convert("RGBA")

    ov = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)

    # внутренняя рамка
    d.rounded_rectangle([10, 10, S - 11, S - 11], radius=218,
                        outline=(255, 255, 255, 34), width=7)

    # шкала
    scale_x = 214
    d.line([(scale_x, 178), (scale_x, 826)], fill=(103, 232, 249, 255), width=22)
    for i, y in enumerate(range(218, 827, 101)):
        major = i % 2 == 0
        d.line([(scale_x, y), (scale_x + (96 if major else 58), y)],
               fill=(103, 232, 249, 255 if major else 190), width=16 if major else 12)

    # поверхность мата
    d.rounded_rectangle([470, 808, 906, 832], radius=12, fill=(16, 185, 129, 235))

    # траектория: падение и отскок
    fall = bezier((248, 196), (380, 300), (500, 468), (640, 610))
    bounce = bezier((640, 610), (760, 500), (816, 386), (858, 258))
    dashed(d, fall, (147, 197, 253, 220), 16, on=18, off=13)
    dashed(d, bounce, (147, 197, 253, 220), 16, on=18, off=13)

    # стрелка отскока
    tip = (858, 258)
    d.polygon([(tip[0], tip[1] - 46), (tip[0] - 34, tip[1] + 8),
               (tip[0] + 34, tip[1] + 8)], fill=(16, 185, 129, 245))

    # мяч
    cx, cy, r = 640, 610, 152
    d.ellipse([cx - r - 9, cy - r - 9, cx + r + 9, cy + r + 9],
              fill=(255, 255, 255, 235))
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(225, 29, 72, 255))
    d.ellipse([cx - r + 16, cy - r + 16, cx + r - 16, cy + r - 16],
              fill=(244, 63, 94, 255))
    # блик
    d.ellipse([cx - 92, cy - 98, cx - 8, cy - 14], fill=(255, 228, 230, 215))
    d.ellipse([cx - 78, cy - 84, cx - 34, cy - 40], fill=(255, 255, 255, 245))
    img = Image.alpha_composite(img, ov)

    # скруглённая маска
    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, S - 1, S - 1], radius=224, fill=255)
    img.putalpha(mask)

    # PNG-размеры
    for size, name in [(512, "favicon-512.png"), (192, "favicon-192.png"),
                       (180, "apple-touch-icon.png"), (32, "favicon-32.png"),
                       (16, "favicon-16.png")]:
        img.resize((size, size), Image.LANCZOS).save(A / name, optimize=True)

    # ICO с несколькими размерами
    img.resize((256, 256), Image.LANCZOS).save(
        A / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    )

    # SVG-версия (современные браузеры)
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
<title>physics_drop — падение и отскок мяча</title>
<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#111826"/><stop offset="1" stop-color="#22304d"/>
  </linearGradient>
  <radialGradient id="ball" cx="38%" cy="30%" r="78%">
    <stop offset="0" stop-color="#fb7185"/><stop offset=".55" stop-color="#e11d48"/>
    <stop offset="1" stop-color="#be123c"/>
  </radialGradient>
</defs>
<rect x="0" y="0" width="512" height="512" rx="112" fill="url(#bg)"/>
<rect x="5" y="5" width="502" height="502" rx="109" fill="none" stroke="#ffffff" stroke-opacity=".13" stroke-width="3.5"/>
<path d="M107 89 V413" stroke="#67e8f9" stroke-width="11" stroke-linecap="round"/>
<path d="M107 109 H155 M107 160 H136 M107 211 H155 M107 262 H136 M107 313 H155 M107 364 H136 M107 413 H155"
      stroke="#67e8f9" stroke-width="8" stroke-linecap="round"/>
<path d="M235 404 H453" stroke="#10b981" stroke-width="12" stroke-linecap="round"/>
<path d="M124 98 C190 150 250 234 320 305 C380 250 408 193 429 129"
      fill="none" stroke="#93c5fd" stroke-width="8" stroke-linecap="round" stroke-dasharray="10 7" opacity=".9"/>
<path d="M429 129 L412 151 H446 Z" fill="#10b981"/>
<circle cx="320" cy="305" r="85" fill="#ffffff" fill-opacity=".92"/>
<circle cx="320" cy="305" r="76" fill="url(#ball)"/>
<ellipse cx="290" cy="276" rx="24" ry="19" fill="#fff" fill-opacity=".85" transform="rotate(-28 290 276)"/>
</svg>
"""
    (A / "favicon.svg").write_text(svg, encoding="utf-8")
    print("favicon.ico, favicon.svg, favicon-*.png, apple-touch-icon.png — готово")


if __name__ == "__main__":
    main()
