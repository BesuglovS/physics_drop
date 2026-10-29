# -*- coding: utf-8 -*-
"""Быстрая самопроверка результатов и собранного HTML.

Запуск: python analysis/selftest.py
Не заменяет полноценные тесты, но ловит грубые регрессии.
"""
import csv
import json
import sys
from pathlib import Path

A = Path(__file__).resolve().parent
errors = []


def check(cond, msg):
    if not cond:
        errors.append(msg)


params = json.loads((A / "params.json").read_text(encoding="utf-8"))
rows = list(csv.DictReader(open(A / "frames.csv", encoding="utf-8-sig"), delimiter=";"))

check(params["frames"] == 109, "ожидалось 109 кадров")
check(len(rows) == 109, "в frames.csv должно быть 109 строк")
check(9.0 < params["values"]["g_fall"] < 10.0, "g_fall вне разумного диапазона")
check(9.0 < params["values"]["g_bounce"] < 10.0, "g_bounce вне разумного диапазона")
check(1.6 < params["values"]["drop_m"] < 2.0, "высота падения вне диапазона")
check(0.6 < params["values"]["e_vel"] < 0.7, "e_vel вне диапазона")
check(0.6 < params["values"]["e_h"] < 0.7, "e_h вне диапазона")
check(0.5 < params["values"]["time_between_hits"] < 1.0, "интервал между ударами вне диапазона")
check(50.0 < params["events"]["hit_frame"] < 51.0, "кадр первого удара вне диапазона")
check(61.0 < params["events"]["apex_frame"] < 63.0, "кадр вершины вне диапазона")
check(72.0 < params["events"]["hit2_frame"] < 75.0, "кадр второго удара вне диапазона")

h = A / "report.html"
if h.exists():
    html = h.read_text(encoding="utf-8")
    check("@@" not in html, "в report.html остались незаменённые @@...@@")
    check('id="school"' in html, "в report.html нет раздела #school")
    check('id="sim-free"' in html, "в report.html нет интерактива #sim-free")
    check("school_physics.md" in html, "в report.html нет ссылки на school_physics.md")
else:
    errors.append("report.html не найден — запустите make_html.py")

school = A / "school_physics.html"
if school.exists():
    sh = school.read_text(encoding="utf-8")
    check("@@" not in sh, "в school_physics.html остались незаменённые @@...@@")
    check('class="toc"' in sh, "в school_physics.html нет содержания")
    check('id="s1"' in sh, "в school_physics.html нет якорей разделов")
else:
    errors.append("school_physics.html не найден — запустите make_school_html.py")

if errors:
    print("ОШИБКИ:")
    for e in errors:
        print(" -", e)
    sys.exit(1)

print("OK: параметры, frames.csv и report.html согласованы.")
