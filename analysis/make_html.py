# -*- coding: utf-8 -*-
"""Сборка интерактивного автономного HTML-отчёта."""
import base64, csv, io, json
import numpy as np
from PIL import Image

A = r"C:\projects\video\analysis"
rows_csv = list(csv.DictReader(open(A + r"\frames.csv", encoding="utf-8-sig"), delimiter=';'))
XS = json.load(open(A + r"\meta.json"))["x"]

CAL = np.array([-4.19292717e-03, 6.50323880e+00, 1.58616071e+02])
def px2cm(y):
    r = np.roots([CAL[0], CAL[1], CAL[2] - y]); r = r[np.isreal(r)].real
    return float(r.min())

cf = (141.3, 3.16, 5.91); cb = (924.8, -41.25, 6.13)
S, FPS = 5.70, 30.0
f_hit, f_apex, f_hit2 = 50.29, 61.73, 73.18
Y_hit, Y_rel, Y_apex = px2cm(1187.3), px2cm(141.3), px2cm(786.0)
V_IN, V_OUT = 5.86, 3.69
E = V_OUT / V_IN
DROP, RISE = Y_hit - Y_rel, Y_hit - Y_apex

# ---------------- данные для JS ----------------
def v_of(f):
    if f < f_hit:
        return -(cf[1] + cf[2] * (f - 32)) / S * FPS / 100
    return -(cb[1] + cb[2] * (f - 55)) / S * FPS / 100

ROWS = []
for r in rows_csv:
    f = int(r['кадр']); t = round(float(r['t_с']), 3)
    if r['y_пикс'] == '':
        ROWS.append(dict(f=f, t=t, y=None, Y=None, h=None, v=None, ph='вне шкалы', cls='none'))
        continue
    y = float(r['y_пикс']); Y = float(r['Y_см_по_шкале'])
    if f < 32:   ph, cls, v = 'покой', 'rest', 0.0
    elif f <= f_hit: ph, cls, v = 'падение', 'fall', v_of(f)
    else:        ph, cls, v = 'отскок', 'bounce', v_of(f)
    if f in (50, 51, 52): ph += ' *'
    ROWS.append(dict(f=f, t=t, y=round(y, 1), Y=round(Y, 1), h=round(Y_hit - px2cm(y), 2),
                     v=round(v, 2), ph=ph, cls=cls))

def b64(path, fmt='JPEG', maxw=None, q=86, size=None):
    im = Image.open(path).convert('RGB')
    if maxw and im.width > maxw:
        im = im.resize((maxw, round(im.height * maxw / im.width)), Image.LANCZOS)
    if size:
        im = im.resize(size, Image.LANCZOS)
    buf = io.BytesIO(); im.save(buf, fmt, quality=q, optimize=True)
    return 'data:image/' + ('jpeg' if fmt == 'JPEG' else 'png') + ';base64,' + base64.b64encode(buf.getvalue()).decode()

import os
VIDEO_B64 = base64.b64encode(open(r"C:\projects\video\drop.mp4", "rb").read()).decode()
print("видео:", round(len(VIDEO_B64) / 1048576, 2), "МБ base64")

img_key = b64(A + r"\key_frames.png", maxw=1400, q=88)
img_sheet = b64(A + r"\contact_sheet.png", maxw=1300, q=80)
thumbs = [b64(A + rf"\frames\f_{i:03d}.png", 'JPEG', size=(280, 498), q=70) for i in range(1, 110)]
print("миниатюры:", round(sum(len(t) for t in thumbs) / 1048576, 2), "МБ base64")

# ---------------- таблица ----------------
def ru(x, nd=0):
    s = f"{x:.{nd}f}".replace('.', ',').replace('-', '\u2212')
    return '0' if s in ('-0', '+0', '\u22120') else s

tr = []
phase_ru = {'rest': 'покой', 'fall': 'падение', 'bounce': 'отскок', 'none': 'вне шкалы'}
for d in ROWS:
    if d['y'] is None:
        tr.append(f"""<tr class="r-none" data-f="{d['f']}" data-ph="none"><td class="num">{d['f']}</td><td class="num">{ru(d['t'],2)}</td>
<td class="num">—</td><td class="num">—</td><td class="num">—</td><td class="num">—</td><td class="bar-cell"></td>
<td><span class="badge b-none">вне шкалы</span></td></tr>""")
        continue
    bar = min(abs(d['v'] or 0) / 6, 1) * 100
    tr.append(f"""<tr class="r-{d['cls']}" data-f="{d['f']}" data-ph="{d['cls']}"><td class="num">{d['f']}</td><td class="num">{ru(d['t'],2)}</td>
<td class="num">{ru(d['y'])}</td><td class="num">{ru(d['Y'])}</td><td class="num">{ru(d['h'])}</td>
<td class="num vnum">{ru(d['v'],2) if d['v'] is not None else '—'}</td>
<td class="bar-cell"><div class="bar" style="width:{bar:.1f}%"></div></td>
<td><span class="badge b-{d['cls']}">{d['ph']}</span></td></tr>""")
TABLE = "\n".join(tr)

ROWS_JS = json.dumps(ROWS, ensure_ascii=False, separators=(',', ':'))
FR_JS = json.dumps(thumbs, separators=(',', ':'))
XS_JS = json.dumps(XS, separators=(',', ':'))

html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Покадровый анализ падения мяча — drop.mp4</title>
<style>
:root{{
  --bg:#eef1f6; --card:#ffffff; --ink:#141a25; --muted:#5b6678; --line:#dfe4ec;
  --blue:#2563eb; --red:#e11d48; --green:#0f9d58; --amber:#c2761a; --violet:#7c3aed;
  --shadow:0 1px 2px rgba(16,24,40,.06),0 8px 24px -12px rgba(16,24,40,.25);
}}
*{{box-sizing:border-box}}
html{{scroll-behavior:smooth}}
body{{margin:0;background:var(--bg);color:var(--ink);
  font:16px/1.62 "Inter","Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;
  -webkit-font-smoothing:antialiased}}
.wrap{{max-width:1120px;margin:0 auto;padding:0 22px 80px}}
button{{font:inherit;cursor:pointer}}

/* --- hero --- */
header.hero{{background:radial-gradient(1200px 400px at 85% -10%,#3b5bdb33,transparent),
  linear-gradient(160deg,#111826,#1d2740 55%,#22304d);color:#fff;padding:56px 0 46px;margin-bottom:34px}}
header.hero .wrap{{padding-bottom:0}}
.eyebrow{{font-size:13px;letter-spacing:.14em;text-transform:uppercase;color:#8fb0ff;font-weight:700}}
h1{{font-size:clamp(28px,4.4vw,44px);line-height:1.12;margin:10px 0 14px;letter-spacing:-.02em;font-weight:800}}
h1 small{{display:block;font-size:.42em;font-weight:500;color:#a9b6cf;letter-spacing:0;margin-top:12px;line-height:1.5}}
.chips{{display:flex;flex-wrap:wrap;gap:8px;margin-top:26px}}
.chip{{background:#ffffff1a;border:1px solid #ffffff2e;border-radius:999px;padding:6px 13px;font-size:13px;color:#dfe7f7}}
.chip b{{color:#fff;font-weight:700}}

/* --- metric cards --- */
.metrics{{display:grid;grid-template-columns:repeat(6,1fr);gap:13px;margin:-58px 0 34px;position:relative;z-index:2}}
.metric{{background:var(--card);border-radius:16px;padding:16px 18px;box-shadow:var(--shadow);border:1px solid #fff;min-width:0}}
.metric .k,.metric .s{{overflow-wrap:anywhere}}
.metric .k{{font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);font-weight:700}}
.metric .v{{font-size:24px;font-weight:800;letter-spacing:-.02em;margin:6px 0 2px;font-variant-numeric:tabular-nums}}
.metric .s{{font-size:13px;color:var(--muted)}}
.metric.acc .v{{color:var(--blue)}} .metric.red .v{{color:var(--red)}}
.metric.green .v{{color:var(--green)}} .metric.amber .v{{color:var(--amber)}}

/* --- sections --- */
section{{background:var(--card);border:1px solid var(--line);border-radius:18px;padding:26px 28px;margin:0 0 22px;box-shadow:var(--shadow)}}
h2{{font-size:21px;margin:0 0 16px;letter-spacing:-.01em;display:flex;align-items:center;gap:10px}}
h2 .n{{display:inline-grid;place-items:center;min-width:28px;height:28px;padding:0 6px;border-radius:9px;background:#e8efff;color:var(--blue);font-size:14px;font-weight:800}}
h3{{font-size:16px;margin:24px 0 10px}}
p{{margin:0 0 12px}}
.muted{{color:var(--muted)}}
code{{background:#f1f4f9;border:1px solid var(--line);border-radius:6px;padding:1px 6px;font-size:13.5px;
  font-family:"JetBrains Mono",Consolas,monospace}}
figure{{margin:16px 0 4px}}
figure img{{width:100%;border-radius:12px;border:1px solid var(--line);display:block}}
figcaption{{font-size:13px;color:var(--muted);margin-top:8px;text-align:center}}

/* --- player --- */
.player{{display:grid;grid-template-columns:minmax(200px,300px) 1fr;gap:24px;align-items:start}}
.stage{{position:relative;width:100%;aspect-ratio:720/1280;border-radius:14px;overflow:hidden;
  background:#0b1220;box-shadow:0 10px 30px -14px rgba(11,18,32,.7)}}
.stage img{{width:100%;height:100%;object-fit:cover;display:block;image-rendering:auto}}
.level{{position:absolute;left:0;right:0;border-top:2px dashed #22d3ee;filter:drop-shadow(0 0 4px #22d3ee88)}}
.level i{{position:absolute;right:6px;top:-20px;background:#0b1220cc;color:#67e8f9;font-size:11px;
  font-style:normal;padding:1px 6px;border-radius:5px;white-space:nowrap}}
.level i.lblL{{right:auto;left:6px;color:#86efac}}
.ballmark{{position:absolute;width:24px;height:24px;margin:-12px 0 0 -12px;border:2px solid #22c55e;
  border-radius:50%;box-shadow:0 0 0 3px #22c55e33,0 0 12px #22c55e66;transition:top .05s linear,left .05s linear}}
.vec{{position:absolute;inset:0;width:100%;height:100%;pointer-events:none}}
#vline{{stroke-width:5;stroke-linecap:round}}
#vtext{{font-size:30px;font-weight:800;stroke:#0b1220;stroke-width:6;paint-order:stroke;letter-spacing:-.5px}}
.ctrl{{display:flex;flex-direction:column;gap:14px}}
.readouts{{display:grid;grid-template-columns:repeat(5,1fr);gap:8px}}
.ro{{background:#f8fafd;border:1px solid var(--line);border-radius:11px;padding:8px 10px}}
.ro .k{{font-size:11px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);font-weight:700}}
.ro b{{display:block;font-size:19px;font-variant-numeric:tabular-nums;letter-spacing:-.02em;margin-top:2px}}
.ro .n{{display:block;font-size:10.5px;line-height:1.25;color:var(--muted);margin-top:1px}}
.ro.v b{{color:var(--violet)}}
.phase{{align-self:flex-start;font-size:12.5px;font-weight:700;padding:3px 11px;border-radius:999px;
  background:#eef2f7;color:#5b6678}}
.phase.fall{{background:#e6efff;color:#1d4ed8}} .phase.bounce{{background:#e4f7ec;color:#0b7a44}}
.phase.none{{background:#f1f3f7;color:#8a94a6}}
input[type=range]{{-webkit-appearance:none;appearance:none;width:100%;height:26px;background:transparent}}
input[type=range]::-webkit-slider-runnable-track{{height:6px;border-radius:4px;background:#dbe3ee}}
input[type=range]::-webkit-slider-thumb{{-webkit-appearance:none;width:18px;height:18px;margin-top:-6px;
  border-radius:50%;background:var(--blue);border:2px solid #fff;box-shadow:0 1px 4px #2563eb66}}
input[type=range]::-moz-range-track{{height:6px;border-radius:4px;background:#dbe3ee}}
input[type=range]::-moz-range-thumb{{width:16px;height:16px;border-radius:50%;background:var(--blue);border:2px solid #fff}}
.btns{{display:flex;flex-wrap:wrap;gap:8px;align-items:center}}
.btn{{border:1px solid var(--line);background:#fff;border-radius:10px;padding:7px 12px;font-weight:600;
  font-size:14px;transition:.15s;color:var(--ink)}}
.btn:hover{{border-color:#b9c6dd;background:#f7faff}}
.btn.primary{{background:var(--blue);border-color:var(--blue);color:#fff;min-width:54px}}
.btn.primary:hover{{background:#1d4ed8}}
.speed{{margin-left:auto;display:flex;gap:4px;align-items:center;font-size:13px;color:var(--muted)}}
.speed .btn{{padding:5px 9px;font-size:13px;font-weight:600}}
.speed .btn.on{{background:#e8efff;border-color:#bcd0f7;color:#1d4ed8}}
.jump{{display:flex;flex-wrap:wrap;gap:6px}}
.jump .btn{{font-size:12px;padding:4px 8px;border-radius:8px;display:inline-flex;align-items:center}}
.jump .btn b{{color:var(--muted);font-weight:600;margin-left:6px;padding-left:6px;border-left:1px solid var(--line);
  font-size:11px;white-space:nowrap}}
.hint{{font-size:12.5px;color:var(--muted);margin:0}}

/* --- chart --- */
.chartbox{{position:relative;margin-top:18px}}
.chart-cap{{font-size:13px;line-height:1.55;color:var(--muted);margin:0 0 8px;max-width:860px}}
.chart-cap b{{color:#334155}}
#chart{{width:100%;height:auto;display:block;touch-action:none}}
#chart text{{font-family:inherit;font-size:11px;fill:#7b8798}}
#chart .ax{{stroke:#c9d3e2;stroke-width:1}}
#chart .grid{{stroke:#eef1f6;stroke-width:1}}
.tt{{position:absolute;pointer-events:none;background:#0f172a;color:#fff;font-size:12px;
  padding:6px 9px;border-radius:8px;white-space:nowrap;transform:translate(-50%,-130%);opacity:0;
  transition:opacity .1s;z-index:5}}
.tt b{{color:#93c5fd}}

/* --- timeline --- */
.tl{{list-style:none;margin:0;padding:0;position:relative}}
.tl:before{{content:"";position:absolute;left:9px;top:8px;bottom:8px;width:2px;background:#cfd8e6}}
.tl li{{position:relative;padding:0 0 16px 34px;cursor:pointer;border-radius:8px}}
.tl li:hover{{background:#f7faff}}
.tl li:before{{content:"";position:absolute;left:3px;top:6px;width:14px;height:14px;border-radius:50%;
  background:#fff;border:3px solid var(--blue);box-shadow:0 0 0 4px #fff}}
.tl li.hit:before{{border-color:var(--red)}} .tl li.apex:before{{border-color:var(--green)}}
.tl li.rest:before{{border-color:#94a3b8}}
.tl .ttl{{font-weight:700}} .tl .sub{{color:var(--muted);font-size:14px}}
.tl .fr{{font-variant-numeric:tabular-nums;font-size:12.5px;color:var(--muted);background:#f3f6fb;
  border:1px solid var(--line);border-radius:7px;padding:1px 8px;margin-left:8px;white-space:nowrap}}

/* --- two col --- */
.cols{{display:grid;grid-template-columns:1fr 1fr;gap:18px}}
.panel{{background:#f8fafd;border:1px solid var(--line);border-radius:14px;padding:18px 20px}}
.panel h4{{margin:0 0 12px;font-size:15px;display:flex;align-items:center;gap:8px}}
.panel .dot{{width:9px;height:9px;border-radius:50%;background:var(--blue)}}
.panel.g .dot{{background:var(--green)}}
.fml{{display:grid;gap:6px;margin:0 0 12px}}
.fml code{{display:block;font-size:13.5px;padding:5px 8px;background:#eef2f9}}
.fml code em{{font-style:normal;color:var(--muted);font-size:12.5px;margin-left:6px}}
.fml span{{display:block;font-size:11.5px;color:var(--muted);margin:-4px 0 2px 2px}}
.kv{{display:grid;grid-template-columns:1fr auto;gap:6px 14px;font-size:14.5px;margin:0}}
.kv dt{{color:var(--muted)}} .kv dd{{margin:0;font-weight:700;font-variant-numeric:tabular-nums}}

/* --- tables --- */
table{{width:100%;border-collapse:separate;border-spacing:0;font-size:14px}}
th,td{{padding:8px 10px;border-bottom:1px solid var(--line);text-align:left;vertical-align:middle}}
th{{background:#f6f8fb;font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);
  position:sticky;top:0;z-index:2;border-bottom:1px solid var(--line)}}
tbody tr{{cursor:pointer}}
tbody tr:hover{{background:#f7faff}}
tbody tr.on{{background:#e8efff !important;box-shadow:inset 3px 0 0 var(--blue)}}
.num{{font-variant-numeric:tabular-nums;text-align:right;white-space:nowrap}}
.vnum{{font-weight:700}}
.r-fall .vnum{{color:#1d4ed8}} .r-bounce .vnum{{color:#0b7a44}}
.r-rest .vnum{{color:#8a94a6}}
.tscroll{{max-height:560px;overflow:auto;border:1px solid var(--line);border-radius:12px;margin-top:8px}}
.hscroll{{overflow-x:auto;-webkit-overflow-scrolling:touch}}
.bar-cell{{width:130px;padding-right:16px}}
.bar{{height:7px;border-radius:4px;background:linear-gradient(90deg,#93c5fd,#2563eb);min-width:2px}}
.r-bounce .bar{{background:linear-gradient(90deg,#86efac,#0f9d58)}}
.r-rest .bar,.r-none .bar{{background:#e2e8f2}}
.badge{{display:inline-block;font-size:12px;font-weight:700;padding:2px 9px;border-radius:999px;white-space:nowrap}}
.b-rest{{background:#eef2f7;color:#5b6678}}
.b-fall{{background:#e6efff;color:#1d4ed8}}
.b-bounce{{background:#e4f7ec;color:#0b7a44}}
.b-none{{background:#f1f3f7;color:#8a94a6}}
.filters{{display:flex;flex-wrap:wrap;gap:7px;margin:14px 0 6px}}
.fchip{{border:1px solid var(--line);background:#fff;border-radius:999px;padding:5px 12px;font-size:13px;font-weight:600;color:var(--muted)}}
.fchip.on{{background:#1d2740;border-color:#1d2740;color:#fff}}
tr.hide{{display:none}}

/* check table */
.check{{border-collapse:collapse;border:1px solid var(--line);border-radius:12px;overflow:hidden}}
.check th,.check td{{padding:9px 14px;border-bottom:1px solid var(--line)}}
.check th{{background:#f3f6fb;color:#5b6678}}
.check td+td,.check th+th{{border-left:1px solid var(--line)}}
.check th:nth-child(1),.check td:nth-child(1){{width:44%;text-align:left}}
.check th:nth-child(2),.check th:nth-child(3),
.check td:nth-child(2),.check td:nth-child(3){{text-align:right;font-variant-numeric:tabular-nums;width:19%}}
.check th:nth-child(4),.check td:nth-child(4){{text-align:center;width:18%}}
.check tbody tr:nth-child(even){{background:#fafbfe}}
.check tbody tr:hover{{background:#f4f8ff}}
.check tbody tr:last-child td{{border-bottom:0}}
.ok{{color:#0b7a44;font-weight:700;white-space:nowrap}}
@media(max-width:700px){{ .check th,.check td{{padding:7px 8px;font-size:13px}} .check th:nth-child(1),.check td:nth-child(1){{width:auto}} }}

ol.concl{{margin:0;padding-left:22px}} ol.concl li{{margin-bottom:10px}}
.files{{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:10px}}
.file{{border:1px solid var(--line);border-radius:12px;padding:11px 34px 11px 13px;background:#fbfcfe;font-size:14px;
  display:block;text-align:left;text-decoration:none;color:inherit;cursor:pointer;font-family:inherit;
  position:relative;transition:.15s;width:100%}}
a.file:hover,button.file:hover{{border-color:#b9c6dd;background:#f3f8ff;transform:translateY(-1px);
  box-shadow:0 8px 18px -12px #1d2740aa}}
a.file:after,button.file:after{{content:"↓";position:absolute;right:12px;top:50%;transform:translateY(-50%);
  color:var(--blue);font-weight:800;font-size:15px;opacity:.5}}
.file b{{display:block;font-family:"JetBrains Mono",Consolas,monospace;font-size:13px;color:var(--blue)}}
.file span{{color:var(--muted);font-size:13px}}
.imp{{margin-top:16px;background:#f8fafd;border:1px solid var(--line);border-radius:14px;padding:16px 18px}}
.imp h4{{margin:0 0 6px;font-size:15px}}
.imp-tabs{{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:12px}}
.imp-tabs .btn{{font-size:12.5px;padding:6px 11px}}
.imp-tabs .btn.on{{background:#e8efff;border-color:#bcd0f7;color:#1d4ed8;font-weight:700}}
.imp-row{{display:flex;flex-wrap:wrap;align-items:center;gap:14px}}
.imp-row label{{font-size:13px;color:var(--muted);display:flex;gap:7px;align-items:baseline;white-space:nowrap}}
.imp-row output{{font-weight:800;color:var(--ink);font-size:15px;font-variant-numeric:tabular-nums}}
#impSlider{{flex:1 1 160px;max-width:300px}}
.imp-out{{margin-left:auto;display:flex;gap:8px;align-items:baseline;font-variant-numeric:tabular-nums}}
.imp-out span{{font-size:11.5px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);font-weight:700}}
.imp-out span.dv{{text-transform:none;font-size:12.5px;letter-spacing:0}}
.imp-out b{{font-size:19px;color:var(--violet);margin-right:8px}}
.dl{{display:flex;flex-wrap:wrap;gap:10px;align-items:center}}
.dl .btn{{padding:10px 16px;font-size:14.5px}}
.dl .btn.primary{{min-width:0}}
.dl-note{{font-size:13px;color:var(--green);font-weight:600}}
footer{{text-align:center;color:var(--muted);font-size:13px;padding:10px 0 0}}

@media(max-width:1040px){{ .metrics{{grid-template-columns:repeat(3,1fr);margin-top:24px}} }}
@media(max-width:700px){{
  .metrics{{grid-template-columns:repeat(2,1fr);gap:10px}}
  .metric{{padding:13px 14px}} .metric .v{{font-size:20px}}
  h2{{font-size:18px}} .wrap{{padding:0 16px 60px}}
  header.hero{{padding:38px 0 34px}}
}}
@media(max-width:860px){{
  .player{{grid-template-columns:1fr}}
  .stage{{max-width:320px;margin:0 auto}}
  .readouts{{grid-template-columns:repeat(3,1fr)}}
  .cols{{grid-template-columns:1fr}}
  section{{padding:20px 18px;border-radius:14px}}
  .bar-cell{{width:70px}}
}}
@media print{{
  body{{background:#fff}} header.hero{{background:#1d2740 !important;-webkit-print-color-adjust:exact}}
  section{{box-shadow:none;break-inside:avoid}} .tscroll{{max-height:none;overflow:visible}}
  th{{position:static}} .ctrl,.filters,.hint{{display:none}}
}}
</style>
</head>
<body>

<header class="hero">
  <div class="wrap">
    <div class="eyebrow">Компьютерный анализ видео · физика</div>
    <h1>Покадровый анализ падения мяча
      <small>drop.mp4 — свободное падение вдоль бумажной шкалы, удар о мат и отскок.
      109 кадров, 30 к/с, 3,63 с.</small>
    </h1>
    <div class="chips">
      <span class="chip">720 × 1280</span>
      <span class="chip"><b>30,000</b> к/с</span>
      <span class="chip"><b>109</b> кадров</span>
      <span class="chip">3,63 с</span>
      <span class="chip">H.264 + AAC</span>
      <span class="chip">1,18 МБ</span>
    </div>
  </div>
</header>

<div class="wrap">

  <div class="metrics">
    <div class="metric acc"><div class="k">Высота падения</div><div class="v">1,82 м</div><div class="s">отпущен без начальной скорости</div></div>
    <div class="metric"><div class="k">Время падения</div><div class="v">0,63 с</div><div class="s">теория 0,61 с</div></div>
    <div class="metric red"><div class="k">Скорость у мата</div><div class="v">5,9 м/с</div><div class="s">≈21 км/ч</div></div>
    <div class="metric green"><div class="k">Высота отскока</div><div class="v">75 см</div><div class="s">42 % от высоты падения</div></div>
    <div class="metric amber"><div class="k">Коэф. восстановления</div><div class="v">0,63</div><div class="s">потеря энергии 60 %</div></div>
    <div class="metric acc"><div class="k">Ускорение g</div><div class="v">9,5 ± 0,5</div><div class="s">м/с², два участка</div></div>
  </div>

  <section id="player-sec">
    <h2><span class="n">1</span>Интерактивный просмотр</h2>
    <div class="player">
      <div class="stage" id="stage">
        <img id="shot" alt="кадр видео" src="">
        <div class="level" id="level" style="top:-100px"><i class="lblL" id="levelLabelL"></i><i id="levelLabel"></i></div>
        <div class="ballmark" id="ballmark" style="display:none"></div>
        <svg class="vec" id="vec" viewBox="0 0 720 1280" aria-hidden="true">
          <g id="vgrp" opacity="0">
            <line id="vline" x1="0" y1="0" x2="0" y2="0"/>
            <polygon id="vhead" points=""/>
            <text id="vtext" x="0" y="0" dominant-baseline="middle">0</text>
          </g>
        </svg>
      </div>
      <div class="ctrl">
        <div class="readouts">
          <div class="ro"><span class="k">кадр</span><b id="roFrame">1</b></div>
          <div class="ro"><span class="k">t, с</span><b id="roTime">0,00</b></div>
          <div class="ro" title="координата центра мяча по бумажной шкале (0 — верхний край шкалы)">
            <span class="k">Y, см</span><b id="roY">−3</b><span class="n">координата по шкале</span></div>
          <div class="ro" title="реальная высота центра мяча над поверхностью отскока (мат)">
            <span class="k">h, см</span><b id="roH">181</b><span class="n">высота над матом</span></div>
          <div class="ro v"><span class="k">v, м/с</span><b id="roV">0,00</b></div>
        </div>
        <span class="phase" id="roPhase">покой</span>
        <input type="range" id="slider" min="1" max="109" value="1" step="1" aria-label="кадр">
        <div class="btns">
          <button class="btn" id="bPrev" title="предыдущий кадр (←)">◀</button>
          <button class="btn primary" id="bPlay" title="пауза / воспроизведение (пробел)">▶</button>
          <button class="btn" id="bNext" title="следующий кадр (→)">▶❘</button>
          <span class="speed">скорость
            <button class="btn on" data-rate="0.1">0,1×</button>
            <button class="btn" data-rate="0.25">0,25×</button>
            <button class="btn" data-rate="0.5">0,5×</button>
            <button class="btn" data-rate="1">1×</button>
          </span>
        </div>
        <div class="jump">
          <button class="btn" data-f="31" title="кадр 31">отпускание<b>кадр 31</b></button>
          <button class="btn" data-f="44" title="кадр 44">середина падения<b>кадр 44</b></button>
          <button class="btn" data-f="50" title="кадр 50">удар 1<b>кадр 50</b></button>
          <button class="btn" data-f="62" title="кадр 62">вершина<b>кадр 62</b></button>
          <button class="btn" data-f="73" title="кадр 73">удар 2<b>кадр 73</b></button>
        </div>
        <p class="hint">← → — покадрово, пробел — пауза. Клик по графику, строке таблицы или пункту хронологии
          переводит плеер на нужный кадр. Стрелка у мяча — вектор скорости: длина пропорциональна |v|,
          красная — движение вниз, зелёная — вверх.</p>
      </div>
    </div>

    <div class="chartbox">
      <p class="chart-cap">Ниже два синхронных графика: <b>верхний — высота</b> мяча над матом (см),
        <b>нижний — вертикальная скорость</b> (м/с, «+» вверх). Точки — измерения по кадрам, пунктир — подогнанные
        параболы, красная линия — текущий кадр. Клик по графику переводит плеер на этот кадр.</p>
      <div class="tt" id="tt"></div>
      <svg id="chart" viewBox="0 0 1000 430" role="img" aria-label="график высоты и скорости"></svg>
    </div>
    <noscript><p class="muted">Для интерактивных элементов нужен JavaScript. Статичные графики — в файлах
      <code>trajectory.png</code> и <code>contact_sheet.png</code>.</p></noscript>
  </section>

  <section>
    <h2><span class="n">2</span>Что происходит в кадре</h2>
    <p>Съёмка в учебном кабинете. На дверце шкафа вертикально закреплена бумажная мерная шкала
      (метки 10…160 см, оцифровка через 10 см, цена деления 1 см). Женщина стоит справа, поднимает руку
      и прижимает небольшой красно-белый мяч к верхнему краю шкалы (примерно к отметке «0»), затем разжимает пальцы.</p>
    <p>Мяч падает вдоль шкалы, ударяется о тёмный резиновый мат на полу, отскакивает примерно до отметки
      <b>103 см по шкале</b> — это <b>≈75 см над полом</b> (высота считается от поверхности мата, который лежит
      на полу) — снова падает и после второго удара остаётся на полу. В конце записи женщина наклоняется
      и поднимает мяч. Диаметр мяча на резких кадрах 23–24 px — при масштабе 5,7 px/см это <b>≈4,1 см</b>.</p>
    <figure>
      <img src="{img_key}" alt="Ключевые кадры">
      <figcaption>12 ключевых кадров; зелёным обведён мяч, подписаны координата по шкале и время.</figcaption>
    </figure>
  </section>

  <section>
    <h2><span class="n">3</span>Хронология</h2>
    <ul class="tl">
      <li class="rest" data-f="1"><span class="ttl">Удержание</span><span class="fr">кадры 1–31 · 0,00–1,00 с</span>
        <div class="sub">мяч неподвижен у верхнего края шкалы, y ≈ 141 px (отметка «0»), колебания ±2 px</div></li>
      <li data-f="31"><span class="ttl">Отпускание</span><span class="fr">кадры 31–32 · 1,00–1,03 с</span>
        <div class="sub">мяч отрывается от руки, начальная скорость ≈ 0</div></li>
      <li data-f="36"><span class="ttl">Свободное падение</span><span class="fr">кадры 32–50 · 1,03–1,64 с</span>
        <div class="sub">скорость растёт линейно до 5,9 м/с; на быстрых кадрах мяч смазан в штрих</div></li>
      <li class="hit" data-f="50"><span class="ttl">Удар 1 — мат</span><span class="fr">кадр ≈50,3 · t ≈ 1,64 с</span>
        <div class="sub">y ≈ 1187 px, отметка ≈179 см; скорость 5,86 м/с, длительность контакта — доли кадра</div></li>
      <li data-f="54"><span class="ttl">Подъём после отскока</span><span class="fr">кадры 51–61 · 1,67–2,00 с</span>
        <div class="sub">скорость падает линейно с 3,69 до 0 м/с</div></li>
      <li class="apex" data-f="62"><span class="ttl">Вершина отскока</span><span class="fr">кадр ≈61,7 · t ≈ 2,02 с</span>
        <div class="sub">y = 786 px, отметка 103 см — 75 см над матом</div></li>
      <li data-f="67"><span class="ttl">Повторное падение</span><span class="fr">кадры 62–73 · 2,03–2,40 с</span>
        <div class="sub">ускорение снова направлено вниз</div></li>
      <li class="hit" data-f="73"><span class="ttl">Удар 2</span><span class="fr">кадр ≈73,2 · t ≈ 2,41 с</span>
        <div class="sub">мяч уходит за край мата и частично перекрыт; интервал между ударами 0,76 с</div></li>
      <li class="rest" data-f="80"><span class="ttl">Затухание</span><span class="fr">кадры 74–109 · 2,43–3,60 с</span>
        <div class="sub">мяч остаётся на полу, женщина наклоняется и берёт его</div></li>
    </ul>
  </section>

  <section>
    <h2><span class="n">4</span>Физика</h2>
    <div class="cols">
      <div class="panel">
        <h4><span class="dot"></span>Свободное падение (кадры 32–49)</h4>
        <div class="fml">
          <code>h(t) = 1,815 − 4,63·t² <em>м</em></code><span>t — время в секундах от момента отпускания</span>
        </div>
        <dl class="kv">
          <dt>Ускорение</dt><dd>5,91 px/кадр²</dd>
          <dt>→ g</dt><dd>9,3 м/с²</dd>
          <dt>Начальная скорость</dt><dd>≈ 0</dd>
          <dt>Высота</dt><dd>1,82 м</dd>
          <dt>Время</dt><dd>0,63 с</dd>
          <dt>Скорость у мата</dt><dd>5,86 м/с</dd>
        </dl>
      </div>
      <div class="panel g">
        <h4><span class="dot"></span>Отскок (кадры 57–73)</h4>
        <div class="fml">
          <code>h(t) = 3,69·t − 4,86·t² <em>м</em></code><span>t — время в секундах от удара о мат</span>
        </div>
        <dl class="kv">
          <dt>Ускорение</dt><dd>6,13 px/кадр²</dd>
          <dt>→ g</dt><dd>9,7 м/с²</dd>
          <dt>Скорость после удара</dt><dd>3,69 м/с</dd>
          <dt>Высота отскока</dt><dd>75,4 см</dd>
          <dt>Время полёта</dt><dd>0,76 с</dd>
          <dt>Коэф. восстановления</dt><dd>0,63</dd>
        </dl>
      </div>
    </div>
    <p class="muted" style="margin-top:14px;font-size:13px">
      В формулах <b>t</b> — время в секундах, коэффициент при t² — это ½g: 4,63 → 9,3 м/с², 4,86 → 9,7 м/с².
      Высоты h считаны по бумажной шкале, а скорости и ускорения — из покадровой подгонки; расхождение этих
      двух путей до 5–7 % — та самая систематика масштаба, о которой сказано в §7.</p>
    <p style="margin-top:16px">Удар неупругий: <b>e = v↑/v↓ = 3,69 / 5,86 = 0,63</b>, по высотам
      e = √(75,4 / 181,5) = 0,64 — два независимых способа дают одно и то же. Доля потерянной
      кинетической энергии 1 − e² ≈ <b>60 %</b>.</p>

    <div class="imp">
      <h4>Импульс при ударе</h4>
      <p class="muted" style="margin:0 0 10px;font-size:13.5px">Масса мяча по видео не измеряется — задайте её сами.
        Импульс равен изменению количества движения: <code>J = m·(v↓ + v↑)</code>.</p>
      <div class="imp-tabs">
        <button class="btn on" data-imp="1">удар 1 · v↓ 5,86 · v↑ 3,69 м/с</button>
        <button class="btn" data-imp="2">удар 2 · v↓ 3,69 · v↑ 2,33 м/с</button>
      </div>
      <div class="imp-row">
        <label>масса мяча <output id="impM">5,0 г</output></label>
        <input type="range" id="impSlider" min="1" max="50" step="0.1" value="5">
        <div class="imp-out"><span class="dv">Δv</span><b id="impDv">9,55 м/с</b>
          <span>импульс J</span><b id="impJ">0,048 Н·с</b></div>
      </div>
      <p class="muted" style="margin:10px 0 0;font-size:12.5px">Для второго удара скорость падения та же (мяч
        возвращается с той же высоты 75 см), а скорость отскока взята как e·v↓ = 0,63 · 3,69 = 2,33 м/с.</p>
    </div>

    <p class="muted" style="margin-top:16px">Звуковая дорожка подтверждает кинематику независимо: два резких хлопка на 1,68 с
      и 2,46 с, интервал 0,776 с против 0,763 с по видео (расхождение 1,7 % — типичная задержка аудиокодека).</p>

    <h3>Проверка согласованности</h3>
    <div class="hscroll"><table class="check">
      <thead><tr><th>Величина</th><th>Измерено</th><th>Теория</th><th>Расхождение</th></tr></thead>
      <tbody>
        <tr><td>Ускорение на падении</td><td>9,3 м/с²</td><td>9,81</td><td class="ok">−5 %</td></tr>
        <tr><td>Ускорение на отскоке</td><td>9,7 м/с²</td><td>9,81</td><td class="ok">−1 %</td></tr>
        <tr><td>Время падения 1,815 м</td><td>0,63 с</td><td>0,61 с</td><td class="ok">+3 %</td></tr>
        <tr><td>Скорость у мата</td><td>5,86 м/с</td><td>5,97 м/с</td><td class="ok">−2 %</td></tr>
        <tr><td>Время полёта после отскока</td><td>0,76 с</td><td>0,75 с</td><td class="ok">+2 %</td></tr>
        <tr><td>Коэф. восстановления</td><td>0,63</td><td>0,64 (по высотам)</td><td class="ok">−2 %</td></tr>
      </tbody>
    </table></div>
    <p class="muted" style="margin-top:12px">Небольшое систематическое занижение g объясняется сопротивлением
      воздуха: мяч разгоняется до ~7 м/с, для лёгкого полого мяча поправка составляет несколько процентов.</p>
  </section>

  <section>
    <h2><span class="n">5</span>Таблица по кадрам</h2>
    <p class="muted" style="font-size:14px">
      <b>Y</b> — координата центра мяча по бумажной шкале (0 — верхний край);
      <b>h</b> — высота над поверхностью отскока; <b>v</b> — вертикальная скорость («+» — вверх, как и высота).
      Кадры, помеченные <b>*</b>, восстановлены по модели: мяч полностью смазан в момент удара.
      Клик по строке — переход к кадру.</p>
    <div class="filters" id="filters">
      <button class="fchip on" data-ph="all">все 109</button>
      <button class="fchip" data-ph="fall">падение</button>
      <button class="fchip" data-ph="bounce">отскок</button>
      <button class="fchip" data-ph="rest">покой</button>
      <button class="fchip" data-ph="none">вне шкалы</button>
    </div>
    <div class="tscroll" id="tscroll">
      <table id="ftable">
        <thead><tr><th>Кадр</th><th>t, с</th><th>y, px</th><th>Y, см</th><th>h, см</th><th>v, м/с</th><th>|v|</th><th>Фаза</th></tr></thead>
        <tbody>
{TABLE}
        </tbody>
      </table>
    </div>
  </section>

  <section>
    <h2><span class="n">6</span>Методика</h2>
    <ol style="padding-left:22px;margin:0 0 8px">
      <li><b>Декодирование.</b> imageio-ffmpeg (FFmpeg 7.1) → 109 кадров PNG, покадрово, без интерполяции.</li>
      <li><b>Детекция мяча</b> — три способа: по цвету (кадры 1–40 и 57–73, маска
        <code>R − max(G,B) &gt; 45</code>); по разности с фоном там, где мяч смазан движением
        (кадры 41–56, фон — медиана кадров 1–30); по модели для момента удара (кадры 50–52).</li>
      <li><b>Калибровка.</b> Положения меток 10…160 см считаны с кадров и аппроксимированы квадратичной
        зависимостью <code>y(см) = 158,6 + 6,503·Y − 0,004193·Y²</code>, СКО остатков 2,5 px (≈0,4 см).
        Квадратичный член нужен потому, что шкала не идеально плоская: её видимый масштаб меняется
        от 6,53 px/см у отметки 0 до 5,16 px/см у отметки 160. Для мяча взят постоянный масштаб
        <b>S = 5,70 px/см</b>.</li>
      <li><b>Подгонка.</b> Два участка полёта аппроксимированы параболами
        <code>y = y₀ + v₀t + ½at²</code>; точка удара — пересечение парабол.</li>
    </ol>
  </section>

  <section>
    <h2><span class="n">7</span>Погрешности и ограничения</h2>
    <ul style="padding-left:22px;margin:0">
      <li><b>Масштаб</b> — главный источник ошибки. Шкала не плоская (видимый масштаб меняется на ~25 %
        по длине), а мяч летит в другой плоскости: систематика до ±5 % по расстояниям и ±0,5 м/с по скоростям.
        Итоговая оценка <b>g = 9,5 ± 0,5 м/с²</b>.</li>
      <li><b>Дискретность.</b> 30 к/с — шаг 33 мс; субпиксельная интерполяция парабол уточняет моменты
        ударов до ±5 мс.</li>
      <li><b>Смазывание.</b> На кадрах 41–56 мяч движется до 110 px/кадр и превращается в штрих 30–50 px —
        центр определяется с точностью ±5…8 px (±1…1,5 см).</li>
      <li><b>Дрожание камеры</b> (до ±6 px за запись) — медленный дрейф, смещает абсолютные высоты на ±1 см.</li>
      <li>Возможен <b>роллинг-шаттер</b> на быстрых кадрах, поэтому 48–52 использованы как вспомогательные.</li>
      <li>Горизонтально мяч дрейфует: ~8 см/с влево при падении и ~18 см/с вправо после удара; на вертикальную
        динамику не влияет.</li>
    </ul>
  </section>

  <section>
    <h2><span class="n">8</span>Выводы</h2>
    <ol class="concl">
      <li>Мяч падает <b>свободно</b> (начальная скорость ≈ 0) с высоты <b>≈1,82 м</b>; время падения <b>0,63 с</b>.</li>
      <li>Ускорение свободного падения по двум независимым участкам — <b>9,3 и 9,7 м/с²</b>
        (среднее 9,5 ± 0,5), что согласуется с 9,81 м/с² в пределах погрешности метода.</li>
      <li>Скорость в момент удара о мат <b>≈5,9 м/с</b> (21 км/ч).</li>
      <li>Удар неупругий: <b>e ≈ 0,63</b>, отскок на <b>75 см</b>, потеряно <b>≈60 %</b> кинетической энергии.</li>
      <li>Второй удар — через <b>0,76 с</b> после первого; дальше мяч заметно не подпрыгивает и остаётся на полу.</li>
    </ol>
  </section>

  <section>
    <h2><span class="n">9</span>Раскадровка</h2>
    <figure>
      <img src="{img_sheet}" alt="Раскадровка — все кадры видео подряд">
      <figcaption>Все 109 кадров подряд (11 в ряд); отмечены старт, удар 1, вершина и удар 2.</figcaption>
    </figure>
  </section>

  <section>
    <h2><span class="n">10</span>Файлы</h2>
    <p class="muted" style="font-size:13.5px;margin:0 0 14px">Клик по карточке — скачивание файла.
      Отчёт и видео отдаются прямо из страницы, остальные файлы лежат рядом с ней.</p>
    <div class="files">
      <button class="file" data-act="report"><b>report.html</b><span>этот отчёт целиком, автономный</span></button>
      <button class="file" data-act="video"><b>drop.mp4</b><span>исходное видео, 1,2 МБ</span></button>
      <a class="file" href="report.md" download><b>report.md</b><span>та же версия в Markdown</span></a>
      <a class="file" href="frames.csv" download><b>frames.csv</b><span>покадровая таблица, 109 строк</span></a>
      <a class="file" href="trajectory.png" download><b>trajectory.png</b><span>график высоты и скорости</span></a>
      <a class="file" href="key_frames.png" download><b>key_frames.png</b><span>12 ключевых кадров</span></a>
      <a class="file" href="contact_sheet.png" download><b>contact_sheet.png</b><span>раскадровка всех кадров</span></a>
      <a class="file" href="audio.wav" download><b>audio.wav</b><span>звук для проверки ударов</span></a>
      <a class="file" href="meta.json" download><b>meta.json</b><span>координаты мяча по X</span></a>
      <a class="file" href="final_analysis.py" download><b>final_analysis.py</b><span>детекция, калибровка, подгонка</span></a>
      <a class="file" href="make_html.py" download><b>make_html.py</b><span>сборка этого отчёта</span></a>
      <a class="file" href="make_report.py" download><b>make_report.py</b><span>сборка report.md</span></a>
      <a class="file" href="meta.py" download><b>meta.py</b><span>координаты мяча по X по кадрам</span></a>
      <a class="file" href="check_velocity.py" download><b>check_velocity.py</b><span>сверка скорости по кадрам</span></a>
      <a class="file" href="split_for_server.py" download><b>split_for_server.py</b><span>сборка версии для сервера</span></a>
    </div>
    <p class="muted" style="font-size:12.5px;margin:12px 0 0">Каталог <code>frames/</code> (109 исходных PNG, ~100 МБ)
      не выкладывается — он за секунды восстанавливается из drop.mp4 командой
      <code>ffmpeg -i drop.mp4 -vsync 0 frames/f_%03d.png</code>.</p>
  </section>

  <section id="download">
    <h2><span class="n">↓</span>Скачать отчёт</h2>
    <p>Файл автономный: кадры, график, стили и скрипты уже внутри, интернет не нужен —
      можно сохранить копию, переслать или открыть на другом компьютере.</p>
    <div class="dl">
      <button class="btn primary" id="dlHtml">Скачать отчёт (HTML)</button>
      <button class="btn" id="dlCsv">Скачать таблицу кадров (CSV)</button>
      <button class="btn" id="dlVideo">Скачать оригинальное видео (MP4)</button>
      <span class="dl-note" id="dlNote"></span>
    </div>
    <p class="muted" style="font-size:13px;margin:12px 0 0">
      HTML — вся страница целиком (≈@@SIZE@@ МБ, работает без интернета). CSV — 109 строк с координатами,
      высотой, скоростью и фазой; открывается в Excel и LibreOffice (разделитель «;», десятичная запятая).
      MP4 — исходный файл drop.mp4 (1,2 МБ), встроен в отчёт base64, поэтому скачивается и без сети.</p>
  </section>

  <footer>Отчёт собран автоматически из кадров drop.mp4 · масштаб 5,70 px/см · 30 к/с</footer>
</div>

<script>
(function(){{
"use strict";
const ROWS = {ROWS_JS};
const FR = {FR_JS};
const XS = {XS_JS};
const N = ROWS.length;

/* --- геометрия графика --- */
const CW=1000, CH=430, PADL=62, PADR=26, T0=0.95, T1=2.55;
const hTop=34, hBot=246, hMax=190;
const vTop=292, vBot=414, vMin=-7, vMax=5;
const S=5.70, FPS=30, fHit=50.29, fApex=61.73, fHit2=73.18;
const cf=[141.3,3.16,5.91], cb=[924.8,-41.25,6.13];
const CA=-4.19292717e-3, CB=6.5032388, CC=158.616071;

const xOf = t => PADL + (t-T0)/(T1-T0)*(CW-PADL-PADR);
const yH  = h => hBot - (h/hMax)*(hBot-hTop);
const yV  = v => vBot - (v-vMin)/(vMax-vMin)*(vBot-vTop);
const px2cm = y => (-CB + Math.sqrt(CB*CB - 4*CA*(CC-y)))/(2*CA);
const mY = f => f<fHit ? cf[0]+cf[1]*(f-32)+0.5*cf[2]*(f-32)**2
                      : cb[0]+cb[1]*(f-55)+0.5*cb[2]*(f-55)**2;
const mH = f => px2cm(1187.3) - px2cm(mY(f));
const mV = f => (f<fHit ? -(cf[1]+cf[2]*(f-32)) : -(cb[1]+cb[2]*(f-55)))/S*FPS/100;
const fmt = (x,d=0) => x==null ? '—' : x.toFixed(d).replace('.',',').replace('-','\\u2212');

/* --- SVG --- */
const NS='http://www.w3.org/2000/svg';
const svg = document.getElementById('chart');
const el = (t,a,p) => {{ const e=document.createElementNS(NS,t);
  for(const k in a) e.setAttribute(k,a[k]); (p||svg).appendChild(e); return e; }};

function buildChart(){{
  // сетка: высота
  for(let h=0; h<=175; h+=25){{
    const y=yH(h);
    el('line',{{x1:PADL,x2:CW-PADR,y1:y,y2:y,class:'grid'}});
    el('text',{{x:PADL-8,y:y+4,'text-anchor':'end'}}).textContent=h;
  }}
  el('text',{{x:PADL-2,y:hTop-16,'font-weight':800,'font-size':13,fill:'#334155'}})
    .textContent='График высоты — высота мяча над матом, см';
  // сетка: скорость
  for(let v=-6; v<=4; v+=2){{
    const y=yV(v);
    el('line',{{x1:PADL,x2:CW-PADR,y1:y,y2:y,class:'grid'}});
    el('text',{{x:PADL-8,y:y+4,'text-anchor':'end'}}).textContent=v;
  }}
  el('text',{{x:PADL-2,y:vTop-16,'font-weight':800,'font-size':13,fill:'#334155'}})
    .textContent='График скорости — вертикальная скорость, м/с («+» вверх)';
  // ось времени
  el('line',{{x1:PADL,x2:CW-PADR,y1:hBot,y2:hBot,class:'ax'}});
  el('line',{{x1:PADL,x2:CW-PADR,y1:vBot,y2:vBot,class:'ax'}});
  el('line',{{x1:PADL,x2:CW-PADR,y1:yV(0),y2:yV(0),class:'ax'}});
  for(let t=1.0; t<=2.5001; t+=0.2){{
    const x=xOf(t);
    el('line',{{x1:x,x2:x,y1:hBot,y2:hBot+5,class:'ax'}});
    el('line',{{x1:x,x2:x,y1:vBot,y2:vBot+5,class:'ax'}});
    el('text',{{x:x,y:vBot+18,'text-anchor':'middle'}}).textContent=fmt(t,1);
  }}
  el('text',{{x:CW-PADR,y:vBot+18,'text-anchor':'end'}}).textContent='с';

  // линии ударов и вершины
  [[fHit,'удар 1'],[fApex,'вершина'],[fHit2,'удар 2']].forEach(([f,lab])=>{{
    const t=(f-1)/FPS, x=xOf(t);
    el('line',{{x1:x,x2:x,y1:hTop-6,y2:vBot,stroke:'#c7d0de','stroke-dasharray':'4 4'}});
    const tx=el('text',{{x:x+5,y:hTop-10,fill:'#7b8798'}}); tx.textContent=lab;
  }});

  // модель: высота
  const hp=[]; for(let f=31.5; f<=fHit; f+=0.25) hp.push(xOf((f-1)/FPS).toFixed(1)+','+yH(mH(f)).toFixed(1));
  el('polyline',{{points:hp.join(' '),fill:'none',stroke:'#d62728','stroke-width':1.6,'stroke-dasharray':'5 4'}});
  const hp2=[]; for(let f=fHit; f<=fHit2; f+=0.25) hp2.push(xOf((f-1)/FPS).toFixed(1)+','+yH(mH(f)).toFixed(1));
  el('polyline',{{points:hp2.join(' '),fill:'none',stroke:'#2ca02c','stroke-width':1.6,'stroke-dasharray':'5 4'}});

  // модель: скорость
  const v1=[]; for(let f=31.5; f<=fHit; f+=0.25) v1.push(xOf((f-1)/FPS).toFixed(1)+','+yV(mV(f)).toFixed(1));
  el('polyline',{{points:v1.join(' '),fill:'none',stroke:'#7c3aed','stroke-width':1.8}});
  const v2=[]; for(let f=fHit; f<=fHit2; f+=0.25) v2.push(xOf((f-1)/FPS).toFixed(1)+','+yV(mV(f)).toFixed(1));
  el('polyline',{{points:v2.join(' '),fill:'none',stroke:'#7c3aed','stroke-width':1.8}});

  // точки измерений
  ROWS.forEach(r=>{{
    if(r.y==null || r.t<T0 || r.t>T1) return;
    el('circle',{{cx:xOf(r.t),cy:yH(r.h),r:2.6,fill:'#1f77b4',opacity:.85}});
    if(Math.abs(r.v)<6) el('circle',{{cx:xOf(r.t),cy:yV(r.v),r:2.6,fill:'#0f172a',opacity:.35}});
  }});

  // курсор воспроизведения
  window.cur = el('g',{{opacity:0}});
  el('line',{{x1:0,x2:0,y1:hTop-6,y2:vBot,stroke:'#e11d48','stroke-width':1.5}},window.cur);
  window.curDotH = el('circle',{{r:5,fill:'#e11d48',stroke:'#fff','stroke-width':1.5}},window.cur);
  window.curDotV = el('circle',{{r:5,fill:'#e11d48',stroke:'#fff','stroke-width':1.5}},window.cur);
  // курсор наведения
  window.hov = el('g',{{opacity:0}});
  el('line',{{x1:0,x2:0,y1:hTop-6,y2:vBot,stroke:'#94a3b8','stroke-width':1,'stroke-dasharray':'3 3'}},window.hov);
}}

/* --- плеер --- */
const img=document.getElementById('shot');
const slider=document.getElementById('slider');
const bPlay=document.getElementById('bPlay');
const level=document.getElementById('level');
const levelLabel=document.getElementById('levelLabel');
const vgrp=document.getElementById('vgrp'), vline=document.getElementById('vline'),
      vhead=document.getElementById('vhead'), vtext=document.getElementById('vtext');
const levelLabelL=document.getElementById('levelLabelL');
const ball=document.getElementById('ballmark');
const tt=document.getElementById('tt');
let i=0, playing=false, rate=0.1, timer=null;

const trMap = {{}};
document.querySelectorAll('#ftable tbody tr').forEach(tr=>trMap[+tr.dataset.f]=tr);

function paint(n){{
  const r=ROWS[n];
  img.src=FR[n];
  slider.value=r.f;
  document.getElementById('roFrame').textContent=r.f;
  document.getElementById('roTime').textContent=fmt(r.t,2);
  document.getElementById('roY').textContent=fmt(r.Y);
  document.getElementById('roH').textContent=fmt(r.h);
  document.getElementById('roV').textContent=fmt(r.v,2);
  const ph=document.getElementById('roPhase');
  ph.textContent=r.ph; ph.className='phase '+r.cls;

  // вектор скорости
  if(r.y==null || r.v==null || Math.abs(r.v) < 0.15){{
    vgrp.setAttribute('opacity',0);
  }} else {{
    const bx=XS[n], vy=r.v, col = vy<0 ? '#ef4444' : '#10b981';
    const len = Math.min(Math.abs(vy)*34, 330);
    let tip = r.y + (vy>0 ? -len : len);
    tip = Math.max(30, Math.min(1250, tip));
    const dir = tip>r.y ? 1 : -1, hl=19, hw=12;
    const y0 = r.y + dir*13;                       // начало — у края мяча
    vline.setAttribute('x1',bx); vline.setAttribute('y1',y0);
    vline.setAttribute('x2',bx); vline.setAttribute('y2',tip-dir*hl*0.75);
    vline.setAttribute('stroke',col);
    vhead.setAttribute('points', bx+','+tip+' '+(bx-hw)+','+(tip-dir*hl)+' '+(bx+hw)+','+(tip-dir*hl));
    vhead.setAttribute('fill',col);
    vtext.setAttribute('x',bx+26);
    vtext.setAttribute('y',Math.max(34,Math.min(1246,tip)));
    vtext.setAttribute('fill',col);
    vtext.textContent=fmt(Math.abs(vy),1)+' м/с';
    vgrp.setAttribute('opacity',1);
  }}

  if(r.y==null){{
    level.style.opacity=0; ball.style.display='none';
  }} else {{
    level.style.opacity=1;
    level.style.top=(r.y/1280*100)+'%';
    levelLabel.textContent='Y = '+fmt(r.Y)+' см';
    levelLabelL.textContent='h = '+fmt(r.h)+' см';
    ball.style.display='block';
    ball.style.left=(XS[n]/720*100)+'%';
    ball.style.top=(r.y/1280*100)+'%';
  }}
  // подсветка строки
  for(const f in trMap) trMap[f].classList.remove('on');
  if(trMap[r.f]) trMap[r.f].classList.add('on');

  // курсор на графике
  if(r.y==null){{ cur.setAttribute('opacity',0); }}
  else {{
    const x=xOf(r.t);
    cur.setAttribute('opacity',1);
    cur.firstChild.setAttribute('x1',x); cur.firstChild.setAttribute('x2',x);
    curDotH.setAttribute('cx',x); curDotH.setAttribute('cy',yH(r.h));
    curDotV.setAttribute('cx',x); curDotV.setAttribute('cy',yV(r.v));
  }}
}}

function go(n, silent){{ i=Math.max(0,Math.min(N-1,n)); paint(i);
  if(!silent){{ try{{ history.replaceState(null,'','#f'+ROWS[i].f); }}catch(e){{}} }} }}

function play(){{
  if(playing) return;
  if(i>=N-1) go(0, true);
  playing=true; bPlay.textContent='❚❚';
  timer=setInterval(()=>{{
    if(i>=N-1){{ pause(); return; }}
    go(i+1, true);
  }}, 1000/(FPS*rate));
}}
function pause(){{ playing=false; bPlay.textContent='▶'; if(timer){{ clearInterval(timer); timer=null; }} }}

bPlay.onclick = () => playing ? pause() : play();
document.getElementById('bPrev').onclick = () => {{ pause(); go(i-1); }};
document.getElementById('bNext').onclick = () => {{ pause(); go(i+1); }};
slider.oninput = e => {{ pause(); go(+e.target.value-1); }};
document.querySelectorAll('[data-rate]').forEach(b=>b.onclick=()=>{{
  rate=+b.dataset.rate;
  document.querySelectorAll('[data-rate]').forEach(x=>x.classList.toggle('on', x===b));
  if(playing){{ pause(); play(); }}
}});
document.querySelectorAll('.jump [data-f]').forEach(b=>b.onclick=()=>{{ pause(); go(+b.dataset.f-1); }});
document.querySelectorAll('.tl li[data-f]').forEach(li=>li.onclick=()=>{{ pause(); go(+li.dataset.f-1); }});
document.querySelectorAll('#ftable tbody tr').forEach(tr=>tr.onclick=()=>{{ pause(); go(+tr.dataset.f-1); sl(tr); }});
function sl(tr){{ const box=document.getElementById('tscroll');
  const rb=tr.getBoundingClientRect(), bb=box.getBoundingClientRect();
  if(rb.top<bb.top || rb.bottom>bb.bottom){{
    box.scrollTop += (rb.top-bb.top) - (bb.height-rb.height)/2;
  }} }}

document.addEventListener('keydown', e=>{{
  if(e.target.tagName==='INPUT') return;
  if(e.key==='ArrowRight'){{ e.preventDefault(); pause(); go(i+1); }}
  else if(e.key==='ArrowLeft'){{ e.preventDefault(); pause(); go(i-1); }}
  else if(e.key===' ' && e.target.tagName!=='BUTTON'){{ e.preventDefault(); playing?pause():play(); }}
}});

/* --- фильтр таблицы --- */
document.querySelectorAll('.fchip').forEach(ch=>ch.onclick=()=>{{
  document.querySelectorAll('.fchip').forEach(c=>c.classList.toggle('on', c===ch));
  const ph=ch.dataset.ph;
  document.querySelectorAll('#ftable tbody tr').forEach(tr=>{{
    tr.classList.toggle('hide', ph!=='all' && tr.dataset.ph!==ph);
  }});
}});

/* --- взаимодействие с графиком --- */
const box = document.querySelector('.chartbox');
function nearestRow(clientX){{
  const rect = svg.getBoundingClientRect();
  const vx = (clientX-rect.left)/rect.width*CW;
  const t = T0 + (vx-PADL)/(CW-PADL-PADR)*(T1-T0);
  let best=0, bd=1e9;
  ROWS.forEach((r,k)=>{{ if(r.y==null) return; const d=Math.abs(r.t-t); if(d<bd){{bd=d;best=k;}} }});
  return best;
}}
svg.addEventListener('mousemove', e=>{{
  const k=nearestRow(e.clientX), r=ROWS[k];
  const rect=box.getBoundingClientRect(), sx=svg.getBoundingClientRect();
  const x=xOf(r.t)/CW*sx.width + (sx.left-rect.left);
  hov.setAttribute('opacity',1);
  hov.firstChild.setAttribute('x1',xOf(r.t)); hov.firstChild.setAttribute('x2',xOf(r.t));
  tt.style.opacity=1;
  tt.style.left=(xOf(r.t)/CW*100)+'%';
  tt.style.top=(yH(r.h)/CH*100)+'%';
  tt.innerHTML='кадр <b>'+r.f+'</b> · t '+fmt(r.t,2)+' с<br>h '+fmt(r.h)+' см · v '+fmt(r.v,2)+' м/с';
}});
svg.addEventListener('mouseleave', ()=>{{ tt.style.opacity=0; hov.setAttribute('opacity',0); }});
svg.addEventListener('click', e=>{{ pause(); go(nearestRow(e.clientX)); }});

/* --- импульс --- */
const IMP = {{1:[5.86,3.69], 2:[3.69,2.33]}};
let impSel = 1;
const impS = document.getElementById('impSlider');
function impUpd(){{
  const v = IMP[impSel], m = (+impS.value)/1000;
  document.getElementById('impM').textContent = fmt(+impS.value,1) + ' г';
  document.getElementById('impDv').textContent = fmt(v[0]+v[1],2) + ' м/с';
  document.getElementById('impJ').textContent = fmt(m*(v[0]+v[1]),3) + ' Н·с';
}}
document.querySelectorAll('[data-imp]').forEach(b=>b.onclick=()=>{{
  impSel = +b.dataset.imp;
  document.querySelectorAll('[data-imp]').forEach(x=>x.classList.toggle('on', x===b));
  impUpd();
}});
impS.addEventListener('input', impUpd);
impUpd();

/* --- скачивание --- */
const VIDEO = "{VIDEO_B64}";
function saveFile(data, name, type){{
  const blob = (data instanceof Blob) ? data : new Blob([data], {{type:type}});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = name;
  document.body.appendChild(a); a.click(); a.remove();
  setTimeout(()=>URL.revokeObjectURL(a.href), 2000);
}}
function downloadReport(){{
  const clone = document.documentElement.cloneNode(true);
  const ch = clone.querySelector('#chart'); if(ch) ch.innerHTML='';
  const note = clone.querySelector('#dlNote'); if(note) note.textContent='';
  saveFile('<!DOCTYPE html>\\n' + clone.outerHTML, 'drop-ball-analysis.html', 'text/html;charset=utf-8');
  const noteEl = document.getElementById('dlNote'); if(noteEl) noteEl.textContent = 'Файл сохранён';
}}
function downloadCsv(){{
  const head = 'кадр;t_с;y_пикс;Y_см_по_шкале;h_см_над_матом;v_м_с;фаза';
  const num = (x,d) => x==null ? '' : x.toFixed(d).replace('.',',');
  const lines = ROWS.map(r => [r.f, num(r.t,3), num(r.y,1), num(r.Y,1), num(r.h,1), num(r.v,2), r.ph].join(';'));
  saveFile('\\uFEFF' + head + '\\n' + lines.join('\\n'), 'drop-ball-frames.csv', 'text/csv;charset=utf-8');
  const noteEl = document.getElementById('dlNote'); if(noteEl) noteEl.textContent = 'Файл сохранён';
}}
function downloadVideo(){{
  const bin = atob(VIDEO), n = bin.length, arr = new Uint8Array(n);
  for(let i=0;i<n;i++) arr[i] = bin.charCodeAt(i);
  saveFile(new Blob([arr], {{type:'video/mp4'}}), 'drop.mp4');
  const noteEl = document.getElementById('dlNote'); if(noteEl) noteEl.textContent = 'Файл сохранён';
}}
document.getElementById('dlHtml').onclick = downloadReport;
document.getElementById('dlCsv').onclick = downloadCsv;
document.getElementById('dlVideo').onclick = downloadVideo;
document.querySelectorAll('[data-act]').forEach(function(el){{
  const a = el.dataset.act;
  el.onclick = a === 'report' ? downloadReport : a === 'video' ? downloadVideo : downloadCsv;
}});

buildChart();
const m = location.hash.match(/f(\\d+)/);
go(m ? Math.min(109, Math.max(1, +m[1]))-1 : 0, true);
}})();
</script>
</body>
</html>
"""

html = html.replace("@@SIZE@@", f"{len(html.encode()) / 1048576:.1f}")
open(A + r"\report.html", "w", encoding="utf-8").write(html)
print("report.html:", round(len(html.encode()) / 1024 / 1024, 2), "МБ")
