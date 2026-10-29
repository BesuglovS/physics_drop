# -*- coding: utf-8 -*-
"""Готовит версию для сервера: выносит инлайновый <script> в app.js (CSP script-src 'self')
и складывает рядом файлы, которые раздаются по ссылкам из раздела «Файлы»."""
import re, os, shutil

A = r"C:\projects\video\analysis"
OUT = r"C:\projects\video\analysis\deploy"
if os.path.isdir(OUT):
    shutil.rmtree(OUT)
os.makedirs(OUT)

html = open(A + r"\report.html", encoding="utf-8").read()
m = re.search(r"<script>(.*?)</script>", html, re.S)
assert m, "инлайновый скрипт не найден"
js = m.group(1)
open(OUT + r"\app.js", "w", encoding="utf-8").write(js)

new_html = html[:m.start()] + '<script src="app.js"></script>' + html[m.end():]
open(OUT + r"\index.html", "w", encoding="utf-8").write(new_html)

EXTRA = ["report.md", "frames.csv", "trajectory.png", "key_frames.png", "contact_sheet.png",
         "audio.wav", "meta.json", "final_analysis.py", "make_html.py", "make_report.py",
         "meta.py", "check_velocity.py", "split_for_server.py"]
for name in EXTRA:
    shutil.copy2(os.path.join(A, name), os.path.join(OUT, name))

total = sum(os.path.getsize(os.path.join(OUT, f)) for f in os.listdir(OUT))
print("index.html:", round(len(new_html.encode()) / 1048576, 2), "МБ")
print("app.js    :", round(len(js.encode()) / 1048576, 2), "МБ")
print("файлов в deploy:", len(os.listdir(OUT)), "| всего", round(total / 1048576, 2), "МБ")
print("осталось инлайновых <script>:", len(re.findall(r"<script(?![^>]*src=)", new_html)))
