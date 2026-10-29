# -*- coding: utf-8 -*-
"""Координаты мяча по X для каждого кадра (для интерактивного маркера)."""
import glob, json
import numpy as np
from PIL import Image

A = r"C:\projects\video\analysis"
files = sorted(glob.glob(A + r"\frames\*.png"))
N = len(files)
xs = np.full(N, np.nan)

for i, f in enumerate(files):
    im = np.asarray(Image.open(f).convert("RGB")).astype(np.int16)
    R, G, B = im[..., 0], im[..., 1], im[..., 2]
    m = (R - np.maximum(G, B) > 45) & (R > 110)
    yy, xx = np.nonzero(m)
    k = (xx > 250) & (xx < 470)
    if k.sum() >= 20:
        xs[i] = xx[k].mean()

idx = np.arange(N)
good = ~np.isnan(xs)
xs_filled = np.interp(idx, idx[good], xs[good])
out = [round(float(v), 1) for v in xs_filled]
json.dump({"x": out}, open(A + r"\meta.json", "w"), ensure_ascii=False)
print("кадров с прямой детекцией:", int(good.sum()), "из", N)
print("x: min %.0f max %.0f" % (np.nanmin(xs), np.nanmax(xs)))
