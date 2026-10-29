# -*- coding: utf-8 -*-
"""Сверка модельной скорости с конечными разностями по измеренным кадрам."""
import numpy as np, csv

A = r"C:\projects\video\analysis"
rows = {int(r['кадр']): r for r in csv.DictReader(open(A + r"\frames.csv", encoding="utf-8-sig"), delimiter=';')}
meas = {}
for f, r in rows.items():
    if r['y_пикс'] and r['метод'] in ('red', 'diff'):
        meas[f] = float(r['y_пикс'])

cf = (141.3, 3.16, 5.91); cb = (924.8, -41.25, 6.13)
S, FPS, f_hit, f_hit2 = 5.70, 30.0, 50.29, 73.18
def model(f):
    if f < f_hit:
        return -(cf[1] + cf[2] * (f - 32)) / S * FPS / 100
    return -(cb[1] + cb[2] * (f - 55)) / S * FPS / 100

errs_fall, errs_bounce = [], []
for f in range(34, 73):
    if f - 2 < f_hit < f + 2 or f - 2 < f_hit2 < f + 2:
        continue
    if not all(k in meas for k in (f - 2, f + 2)):
        continue
    fd = -((meas[f + 2] - meas[f - 2]) / 4.0) / S * FPS / 100
    d = fd - model(f)
    (errs_fall if f < f_hit else errs_bounce).append(d)

for name, e in (('падение', errs_fall), ('отскок', errs_bounce)):
    e = np.array(e)
    print(f"{name}: точек {len(e)}, среднее смещение {e.mean():+.2f} м/с, "
          f"СКО {e.std():.2f} м/с, макс |откл| {np.abs(e).max():.2f} м/с")
