# -*- coding: utf-8 -*-
"""Готовит версию для сервера: выносит инлайновый <script> в app.js (CSP script-src 'self')."""
import re, os

A = r"C:\projects\video\analysis"
OUT = r"C:\projects\video\analysis\deploy"
os.makedirs(OUT, exist_ok=True)

html = open(A + r"\report.html", encoding="utf-8").read()
m = re.search(r"<script>(.*?)</script>", html, re.S)
assert m, "инлайновый скрипт не найден"
js = m.group(1)
open(OUT + r"\app.js", "w", encoding="utf-8").write(js)

new_html = html[:m.start()] + '<script src="app.js"></script>' + html[m.end():]
# страница должна открываться как /video/
open(OUT + r"\index.html", "w", encoding="utf-8").write(new_html)

print("index.html:", round(len(new_html.encode()) / 1048576, 2), "МБ")
print("app.js    :", round(len(js.encode()) / 1048576, 2), "МБ")
print("осталось инлайновых <script>:", len(re.findall(r"<script(?![^>]*src=)", new_html)))
