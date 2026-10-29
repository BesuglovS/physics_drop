# -*- coding: utf-8 -*-
"""Покадровый анализ падения мяча в drop.mp4."""
import numpy as np, csv
from PIL import Image, ImageDraw, ImageFont

A = r"C:\projects\video\analysis"
def load_frames():
    import os, glob
    cache = A + r"\frames.npy"
    if os.path.exists(cache):
        return np.load(cache).astype(np.float32)
    files = sorted(glob.glob(A + r"\frames\*.png"))
    return np.stack([np.asarray(Image.open(f).convert("RGB")) for f in files]).astype(np.float32)

F = load_frames()
TOTAL = len(F)
FPS = 30.0

# ---------- 1. КАЛИБРОВКА (метки 10..160 см на бумажной шкале) ----------
CAL = np.array([-4.19292717e-03, 6.50323880e+00, 1.58616071e+02])  # y = a*Y^2+b*Y+c
def px2cm(y):
    r = np.roots([CAL[0], CAL[1], CAL[2] - y])
    r = r[np.isreal(r)].real
    return float(r.min())
def cm2px(Y):
    return float(np.polyval(CAL, Y))

# ---------- 2. ДЕТЕКЦИЯ МЯЧА ----------
R, G, B = F[..., 0], F[..., 1], F[..., 2]
red = (R - np.maximum(G, B) > 45) & (R > 110)
yy_, xx_ = np.mgrid[0:1280, 0:720]
red &= (xx_ > 250) & (xx_ < 470)

def red_blob(i):
    m = red[i]
    y, x = np.nonzero(m)
    if len(y) < 20:
        return None
    return float(y.mean()), (int(y.min()), int(y.max())), (int(x.min()), int(x.max())), len(y)

# фон для дифференциальной детекции (мяч в кадрах 1-30 прижат к верху шкалы)
g0 = F.mean(axis=3)
X0, X1 = 315, 425
BG = np.median(g0[0:30, :, X0:X1], axis=0)

def diff_pos(i, pred, half=80):
    f = g0[i, :, X0:X1]
    off = float(np.median(f[300:1100] - BG[300:1100]))
    d = np.clip(f - BG - off, 0, None).sum(axis=1)
    d[:300] = 0
    d[1160:] = 0
    lo, hi = max(300, int(pred - half)), min(1160, int(pred + half))
    seg = np.convolve(d[lo:hi], np.ones(9) / 9, 'same')
    k = lo + int(np.argmax(seg))
    w = np.clip(d[k - 16:k + 17], 0, None)
    return float((w * np.arange(k - 16, k + 17)).sum() / max(w.sum(), 1e-6)), float(seg.max())

# ---------- 3. ТРАЕКТОРИЯ ----------
meas = {}                                   # frame -> (y, method)
for f in range(1, 41):
    b = red_blob(f - 1)
    if b: meas[f] = (b[0], 'red')

fall_model = lambda f: 141.3 + 3.14 * (f - 32) + 0.5 * 5.91 * (f - 32) ** 2
bounce_model = lambda f: 924.8 - 41.25 * (f - 55) + 0.5 * 6.13 * (f - 55) ** 2

for f in range(41, 50):
    y, _ = diff_pos(f - 1, fall_model(f))
    meas[f] = (y, 'diff')
for f in range(53, 57):
    y, _ = diff_pos(f - 1, bounce_model(f), half=60)
    meas[f] = (y, 'diff')
for f in range(57, 74):
    b = red_blob(f - 1)
    if b: meas[f] = (b[0], 'red')
# кадры 74+ : мяч ушёл с линии шкалы (пол/мат), положение не измеряется

# ---------- 4. ПОДГОНКА ПАРАБОЛ ----------
def fit(pts, tref):
    t = np.array([p[0] - tref for p in pts], float)
    y = np.array([p[1] for p in pts], float)
    M = np.vstack([np.ones_like(t), t, 0.5 * t * t]).T
    c = np.linalg.lstsq(M, y, rcond=None)[0]
    return c, float(np.sqrt((((M @ c) - y) ** 2).mean()))

fall_pts = [(f, meas[f][0]) for f in range(32, 50)]
boun_pts = [(f, meas[f][0]) for f in range(57, 74)]
cf, rf = fit(fall_pts, 32)
cb, rb = fit(boun_pts, 55)

# точка соударения = пересечение двух парабол
t = np.linspace(-2, 30, 400001)
yf = cf[0] + cf[1] * t + 0.5 * cf[2] * t * t
yb = cb[0] + cb[1] * (t - 23) + 0.5 * cb[2] * (t - 23) ** 2
k = int(np.argmin(np.abs(yf - yb)))
t_hit, y_hit = t[k], 0.5 * (yf[k] + yb[k])
f_hit = 32 + t_hit
v_in = abs(cf[1] + cf[2] * t_hit)
v_out = abs(cb[1] + cb[2] * (t_hit - 23))
apex_u = -cb[1] / cb[2]
f_apex, y_apex = 55 + apex_u, cb[0] - 0.5 * cb[1] ** 2 / cb[2]
# второе соударение
u2 = np.roots([0.5 * cb[2], cb[1], cb[0] - y_hit])
u2 = float(u2[np.isreal(u2)].real.max())
f_hit2 = 55 + u2

# ---------- 5. МИРОВЫЕ ЕДИНИЦЫ ----------
S = 5.70           # px/см в плоскости мяча (по диаметру мяча и шкале)
GM = 900.0
g_fall = cf[2] / S * GM / 100      # м/с^2
g_boun = cb[2] / S * GM / 100
Y_rel, Y_hit, Y_apex = px2cm(141.3), px2cm(y_hit), px2cm(y_apex)
drop_cm = Y_hit - Y_rel
rise_cm = Y_hit - Y_apex
e_vel = v_out / v_in
e_h = np.sqrt(rise_cm / drop_cm)

print(f"fall   : y0={cf[0]:.1f} v0={cf[1]:+.2f} a={cf[2]:.2f} px/f^2 rms={rf:.2f}")
print(f"bounce : y0={cb[0]:.1f} v0={cb[1]:+.2f} a={cb[2]:.2f} px/f^2 rms={rb:.2f}")
print(f"hit frame {f_hit:.2f} ({f_hit/FPS:.3f}s) y={y_hit:.1f}px  Y={Y_hit:.1f}cm")
print(f"apex frame {f_apex:.2f} ({f_apex/FPS:.3f}s) y={y_apex:.1f}px Y={Y_apex:.1f}cm")
print(f"hit2 frame {f_hit2:.2f} ({f_hit2/FPS:.3f}s)")
print(f"drop {drop_cm:.1f} cm  rise {rise_cm:.1f} cm  e_vel={e_vel:.3f} e_h={e_h:.3f}")
print(f"v_in={v_in/S*FPS/100:.2f} m/s  v_out={v_out/S*FPS/100:.2f} m/s")
print(f"g_fall={g_fall:.2f}  g_bounce={g_boun:.2f} m/s^2")

# ---------- 6. ТАБЛИЦА ----------
rows = []
for f in range(1, TOTAL + 1):
    if f in meas:
        y, meth = meas[f]
        rows.append((f, (f - 1) / FPS, y, px2cm(y), meth))
    elif f <= 31:
        rows.append((f, (f - 1) / FPS, 141.3, px2cm(141.3), 'rest'))
    elif f in (50, 51, 52):
        y = fall_model(f) if f == 50 else bounce_model(f)
        rows.append((f, (f - 1) / FPS, y, px2cm(y), 'model'))
    else:
        rows.append((f, (f - 1) / FPS, None, None, 'n/a'))

with open(A + r"\frames.csv", 'w', newline='', encoding='utf-8-sig') as fh:
    w = csv.writer(fh, delimiter=';')
    w.writerow(['кадр', 't_с', 'y_пикс', 'Y_см_по_шкале', 'метод'])
    for r in rows:
        w.writerow([r[0], f'{r[1]:.3f}', '' if r[2] is None else f'{r[2]:.1f}',
                    '' if r[3] is None else f'{r[3]:.1f}', r[4]])

# ---------- 7. ГРАФИК ----------
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams['font.size'] = 9

H0 = px2cm(y_hit)                       # отметка точки удара по шкале, см
def T(f):                               # номер кадра -> время, с
    return (f - 1) / FPS
def pos_of(f):                          # модель y(f) в пикселях
    if f < f_hit:
        return cf[0] + cf[1] * (f - 32) + 0.5 * cf[2] * (f - 32) ** 2
    return cb[0] + cb[1] * (f - 55) + 0.5 * cb[2] * (f - 55) ** 2
def vel_of(f):                          # модель v(f), м/с, «+» — вверх
    if f < f_hit:
        return -(cf[1] + cf[2] * (f - 32)) / S * FPS / 100
    return -(cb[1] + cb[2] * (f - 55)) / S * FPS / 100

fig, (ax, ax2) = plt.subplots(2, 1, figsize=(10, 7.6), dpi=140, sharex=True,
                              gridspec_kw={'height_ratios': [2.1, 1.15]})

# --- панель 1: координата
Tt = np.array([r[1] for r in rows])
Yv = np.array([np.nan if r[3] is None else H0 - r[3] for r in rows])
ax.plot(Tt, Yv, 'o-', ms=3, lw=1, color='#1f77b4', label='измерение по кадрам')

ff = np.linspace(31.5, f_hit, 300)
ax.plot([T(f) for f in ff], [H0 - px2cm(pos_of(f)) for f in ff], '--', color='#d62728', lw=1.2,
        label='подгонка: свободное падение, g = 9,3 м/с²')
fb = np.linspace(f_hit, f_hit2, 300)
ax.plot([T(f) for f in fb], [H0 - px2cm(pos_of(f)) for f in fb], '--', color='#2ca02c', lw=1.2,
        label='подгонка: отскок, g = 9,7 м/с²')

for fv_, lab, xy in [(f_hit, 'удар 1', (T(f_hit), 3)), (f_apex, 'вершина', (T(f_apex), rise_cm)),
                     (f_hit2, 'удар 2', (T(f_hit2), 3))]:
    ax.axvline(T(fv_), color='gray', ls=':', lw=0.8)
    ax.annotate(lab, xy, textcoords='offset points',
                xytext=(7, 22) if 'удар' in lab else (8, 10), fontsize=8)
ax.axhline(0, color='black', lw=.6)
ax.set_ylabel('высота центра мяча\nнад поверхностью отскока, см')
ax.set_title('drop.mp4 — вертикальная координата и скорость мяча по кадрам (30 к/с)')
ax.grid(alpha=.3); ax.legend(loc='upper right', fontsize=8)
ax.set_ylim(-8, 200)

# --- панель 2: скорость
fv = np.linspace(31.5, f_hit, 200)
ax2.plot([T(f) for f in fv], [vel_of(f) for f in fv], color='#7c3aed', lw=1.6,
         label='модель: производная подогнанной параболы')
fv2 = np.linspace(f_hit, f_hit2, 200)
ax2.plot([T(f) for f in fv2], [vel_of(f) for f in fv2], color='#7c3aed', lw=1.6)

# численная проверка: центральные разности по измеренным кадрам
fd_t, fd_v = [], []
for f in range(34, 73):
    if f - 2 < f_hit < f + 2 or f - 2 < f_hit2 < f + 2:      # окно не должно пересекать удар
        continue
    if all(k in meas for k in (f - 2, f + 2)):
        fd_t.append(T(f))
        fd_v.append(-((meas[f + 2][0] - meas[f - 2][0]) / 4.0) / S * FPS / 100)
ax2.plot(fd_t, fd_v, 'o', ms=3.3, color='#0f172a', alpha=.5,
         label='центральная разность y(f±2) — по кадрам')

ax2.axhline(0, color='black', lw=.6)
ax2.axvline(T(f_hit), color='gray', ls=':', lw=0.8)
ax2.axvline(T(f_hit2), color='gray', ls=':', lw=0.8)
ax2.plot([T(f_hit), T(f_hit)], [-v_in / S * FPS / 100, v_out / S * FPS / 100],
         color='#e11d48', lw=1, ls=(0, (2, 2)), alpha=.8)
ax2.annotate(f'−{v_in / S * FPS / 100:.1f} м/с', (T(f_hit), -v_in / S * FPS / 100),
             textcoords='offset points', xytext=(-58, -4), fontsize=8, color='#b3122f')
ax2.annotate(f'+{v_out / S * FPS / 100:.1f} м/с', (T(f_hit), v_out / S * FPS / 100),
             textcoords='offset points', xytext=(6, 2), fontsize=8, color='#0b7a44')
ax2.set_xlabel('время, с')
ax2.set_ylabel('вертикальная скорость, м/с\n(«+» — вверх)')
ax2.grid(alpha=.3)
ax2.set_ylim(-7.2, 5.2)
ax2.legend(loc='lower left', fontsize=7.5, framealpha=.9)
ax2.set_xlim(0.95, 2.55)

fig.tight_layout()
fig.savefig(A + r"\trajectory.png")
plt.close(fig)

# ---------- 8. КОНТАКТНЫЙ ЛИСТ ВСЕХ КАДРОВ ----------
from PIL import ImageFont
FNT12 = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 12)
FNT13 = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 13)
FNT11 = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 11)

H_MAP = {r[0]: (Y_hit - r[3]) if r[3] is not None else None for r in rows}
def h_lbl(f, unit=True):
    h = H_MAP.get(f)
    if h is None:
        return '—'
    return str(int(round(h))) + (' см' if unit else '')

def sheet(frames_idx, cols, w, h, path, marks=None):
    rows_n = (len(frames_idx) + cols - 1) // cols
    LBL, GAP = 22, 12                     # полоса подписи и зазор с разделителем
    rowh = h + LBL + GAP
    sh = Image.new('RGB', (cols * w, rows_n * rowh), '#0b1220')
    d = ImageDraw.Draw(sh)
    for i, f in enumerate(frames_idx):
        r, c = divmod(i, cols)
        y = r * rowh
        if r > 0:                         # разделитель между рядами
            d.line([(0, y - GAP // 2), (cols * w, y - GAP // 2)], fill='#3b4a63', width=2)
        im = Image.fromarray(F[f - 1].astype(np.uint8)).resize((w, h), Image.LANCZOS)
        sh.paste(im, (c * w, y + LBL))
        d.rectangle([c * w, y + LBL, c * w + w - 1, y + LBL + h - 1], outline='#22314a')
        t = str(f)
        tw = d.textlength(t, font=FNT12)
        d.rectangle([c * w + 3, y + 4, c * w + 11 + tw, y + 19], fill='#111c33', outline='#2f4463')
        d.text((c * w + 6, y + 4), t, fill=(125, 211, 252), font=FNT12)
        hv = h_lbl(f)
        hx = c * w + 17 + tw
        d.text((hx, y + 6), hv, fill=(148, 163, 184), font=FNT11)
        if marks and f in marks:
            hw = d.textlength(hv, font=FNT11)
            d.text((hx + hw + 7, y + 4), marks[f], fill=(253, 224, 71), font=FNT12)
    sh.save(path)
    print(path, sh.size)

marks = {31: 'старт', 50: 'удар 1', 62: 'вершина', 73: 'удар 2'}
sheet(list(range(1, TOTAL + 1)), 11, 118, 210, A + r"\contact_sheet.png", marks)

# ---------- 9. КЛЮЧЕВЫЕ КАДРЫ С ПОДПИСЯМИ ----------
key = [31, 38, 44, 49, 50, 54, 58, 62, 68, 73, 74, 82]
w, h = 240, 427
LBL, GAP = 26, 14
rowh = h + LBL + GAP
sh = Image.new('RGB', (6 * w, 2 * rowh), '#0b1220')
d = ImageDraw.Draw(sh)
for i, f in enumerate(key):
    im = Image.fromarray(F[f - 1].astype(np.uint8)).resize((w, h), Image.LANCZOS).convert('RGB')
    dd = ImageDraw.Draw(im)
    if f in meas or f in (50, 51, 52):
        yb_ = meas[f][0] if f in meas else (fall_model(f) if f == 50 else bounce_model(f))
        dd.ellipse([120 - 26, yb_ * h / 1280 - 26, 120 + 26, yb_ * h / 1280 + 26], outline=(0, 255, 0), width=2)
    r, c = divmod(i, 6)
    y = r * rowh
    if r > 0:
        d.line([(0, y - GAP // 2), (6 * w, y - GAP // 2)], fill='#3b4a63', width=2)
    sh.paste(im, (c * w, y + LBL))
    d.rectangle([c * w, y + LBL, c * w + w - 1, y + LBL + h - 1], outline='#22314a')
    # бейдж «кадр N» + параметры
    badge = f'кадр {f}'
    bw = d.textlength(badge, font=FNT13)
    d.rectangle([c * w + 4, y + 4, c * w + 14 + bw, y + 22], fill='#111c33', outline='#2f4463')
    d.text((c * w + 8, y + 5), badge, fill=(125, 211, 252), font=FNT13)
    tail = 't = ' + f'{((f - 1) / FPS):.2f}'.replace('.', ',') + ' с'
    if f in meas:
        tail += '  ·  h = ' + h_lbl(f)
    d.text((c * w + 16 + bw, y + 5), tail, fill=(148, 163, 184), font=FNT13)
sh.save(A + r"\key_frames.png")
print(A + r"\key_frames.png", sh.size)
