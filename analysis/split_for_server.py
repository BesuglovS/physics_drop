# -*- coding: utf-8 -*-
"""Готовит версию для сервера: выносит инлайновый <script> в app.js
(CSP script-src 'self') и складывает рядом файлы, которые раздаются по ссылкам
из раздела «Файлы».

Важно: app.js отдаётся nginx с Cache-Control immutable на 30 дней, поэтому
в index.html добавляется версия (?v=<hash>), иначе браузер может держать старый JS.
"""
import hashlib
import re
import shutil
from pathlib import Path

A = Path(__file__).resolve().parent
OUT = A / "deploy"
if OUT.is_dir():
    shutil.rmtree(OUT)
OUT.mkdir()

html = (A / "report.html").read_text(encoding="utf-8")
m = re.search(r"<script>(.*?)</script>", html, re.S)
assert m, "инлайновый скрипт не найден"
js = m.group(1)
(OUT / "app.js").write_text(js, encoding="utf-8")
js_ver = hashlib.sha256(js.encode("utf-8")).hexdigest()[:12]

new_html = (
    html[:m.start()]
    + f'<script src="app.js?v={js_ver}"></script>'
    + html[m.end():]
)
(OUT / "index.html").write_text(new_html, encoding="utf-8")

EXTRA = [
    "report.md", "frames.csv", "params.json", "school_physics.md",
    "school_physics.html", "AUDIT.md",
    "trajectory.png", "key_frames.png", "contact_sheet.png", "audio.wav",
    "meta.json", "final_analysis.py", "make_html.py", "make_report.py",
    "make_school_html.py", "meta.py", "check_velocity.py", "selftest.py",
    "split_for_server.py",
]
for name in EXTRA:
    shutil.copy2(A / name, OUT / name)

# На сервере отчёт называется index.html (report.html не выкладывается:
# он содержит инлайновый script, который запрещён CSP script-src 'self').
# Правим ссылки в сопутствующих документах, чтобы они не вели в 404.
for name in ("school_physics.html", "school_physics.md", "report.md", "AUDIT.md"):
    p = OUT / name
    if not p.exists():
        continue
    txt = p.read_text(encoding="utf-8")
    txt = txt.replace("report.html", "index.html")
    p.write_text(txt, encoding="utf-8")

total = sum(p.stat().st_size for p in OUT.iterdir() if p.is_file())
print("index.html:", round(len(new_html.encode()) / 1048576, 2), "МБ")
print("app.js    :", round(len(js.encode()) / 1048576, 2), "МБ")
print("файлов в deploy:", len(list(OUT.iterdir())), "| всего", round(total / 1048576, 2), "МБ")
print("осталось инлайновых <script>:", len(re.findall(r"<script(?![^>]*src=)", new_html)))
