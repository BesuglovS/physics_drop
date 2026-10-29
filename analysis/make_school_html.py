# -*- coding: utf-8 -*-
"""Собирает автономную веб-страницу school_physics.html из school_physics.md.

Запуск: python analysis/make_school_html.py
"""
import html
import re
from pathlib import Path

from markdown_it import MarkdownIt

A = Path(__file__).resolve().parent
SRC = A / "school_physics.md"
OUT = A / "school_physics.html"


def strip_tags(s: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", s)).strip()


def build_toc(body: str):
    """Добавляет id к h2/h3 и собирает вложенное содержание."""
    counter = 0
    toc = []
    current_h2 = None

    def repl(m):
        nonlocal counter, current_h2
        level = int(m.group(1))
        inner = m.group(2)
        counter += 1
        hid = f"s{counter}"
        label = strip_tags(inner)
        if level == 2:
            current_h2 = {"id": hid, "label": label, "children": []}
            toc.append(current_h2)
        elif level == 3 and current_h2 is not None:
            current_h2["children"].append({"id": hid, "label": label})
        return f'<h{level} id="{hid}">{inner}<a class="hlink" href="#{hid}" aria-label="Ссылка на раздел">#</a></h{level}>'

    body = re.sub(r"<h([23])>(.*?)</h\1>", repl, body, flags=re.S)
    return body, toc


def render_toc(toc) -> str:
    items = []
    for sec in toc:
        items.append(
            f'<li><a href="#{sec["id"]}">{html.escape(sec["label"])}</a>'
        )
        if sec["children"]:
            items.append("<ul>")
            for ch in sec["children"]:
                items.append(f'<li><a href="#{ch["id"]}">{html.escape(ch["label"])}</a></li>')
            items.append("</ul>")
        items.append("</li>")
    return '<ol class="toc-list">' + "".join(items) + "</ol>"


def main():
    text = SRC.read_text(encoding="utf-8")
    # Первый H1 — заголовок страницы; в тело он не попадает.
    title = "Школьная физика на одном видео"
    if text.startswith("# "):
        first, _, text = text.partition("\n")
        title = first[2:].strip()

    md = MarkdownIt("commonmark").enable("table")
    body = md.render(text)
    body, toc = build_toc(body)
    body = re.sub(
        r"<table>(.*?)</table>",
        r'<div class="table-wrap"><table>\1</table></div>',
        body,
        flags=re.S,
    )
    # Ссылки на интерактивы ведут в интерактивный отчёт, а не в пустые якоря.
    for anchor in ("sim-free", "sim-bounce", "sim-energy", "sim-drag", "sim-blur",
                   "sim-parallax", "sim-fit", "sim-sound", "imp"):
        body = body.replace(
            f"<code>#{anchor}</code>",
            f'<a href="report.html#{anchor}"><code>#{anchor}</code></a>',
        )
    toc_html = render_toc(toc)

    page = f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="Методический конспект: темы школьной физики 7–11 классов на одном видео падения мяча — свободное падение, g, отскок, импульс, энергия, звук, оптика.">
<meta name="theme-color" content="#1d2740">
<link rel="icon" href="favicon.svg" type="image/svg+xml">
<link rel="icon" href="favicon.ico" sizes="any">
<link rel="icon" type="image/png" sizes="192x192" href="favicon-192.png">
<link rel="apple-touch-icon" href="apple-touch-icon.png">
<title>{html.escape(title)} — методический конспект</title>
<style>
:root{{
  --bg:#eef1f6; --card:#ffffff; --ink:#141a25; --muted:#5b6678; --line:#dfe4ec;
  --blue:#2563eb; --red:#e11d48; --green:#0f9d58; --amber:#c2761a; --violet:#7c3aed;
  --shadow:0 1px 2px rgba(16,24,40,.06),0 8px 24px -12px rgba(16,24,40,.25);
}}
*{{box-sizing:border-box}}
html{{scroll-behavior:smooth}}
body{{margin:0;background:var(--bg);color:var(--ink);
  font:16px/1.65 "Inter","Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;
  -webkit-font-smoothing:antialiased}}
a{{color:var(--blue)}}
a:hover{{color:#1d4ed8}}
.wrap{{max-width:1180px;margin:0 auto;padding:0 22px 80px}}

header.hero{{background:radial-gradient(900px 320px at 88% -20%,#3b5bdb55,transparent),
  linear-gradient(160deg,#111826,#1d2740 55%,#22304d);color:#fff;padding:44px 0 38px}}
header.hero .wrap{{padding-bottom:0}}
.eyebrow{{font-size:12.5px;letter-spacing:.14em;text-transform:uppercase;color:#8fb0ff;font-weight:800}}
h1{{font-size:clamp(26px,4.2vw,42px);line-height:1.12;margin:10px 0 12px;letter-spacing:-.02em;font-weight:800}}
.hero p{{max-width:820px;color:#c8d2e6;margin:0 0 18px}}
.chips{{display:flex;flex-wrap:wrap;gap:8px;margin-top:18px}}
.chip{{background:#ffffff17;border:1px solid #ffffff2e;border-radius:999px;padding:5px 12px;
  font-size:12.5px;color:#dfe7f7;text-decoration:none}}
.chip b{{color:#fff}}
.hero-actions{{display:flex;flex-wrap:wrap;gap:9px;margin-top:20px}}
.btn{{display:inline-flex;align-items:center;gap:6px;border:1px solid #ffffff3a;border-radius:10px;
  padding:8px 13px;font-size:14px;font-weight:700;color:#fff;text-decoration:none;background:#ffffff12}}
.btn:hover{{background:#ffffff22;color:#fff}}
.btn.primary{{background:#2563eb;border-color:#2563eb}}
.btn.primary:hover{{background:#1d4ed8}}

.doc-layout{{display:grid;grid-template-columns:270px minmax(0,1fr);gap:30px;align-items:start;
  margin-top:-18px;position:relative;z-index:2}}
.toc{{position:sticky;top:18px;background:var(--card);border:1px solid var(--line);border-radius:16px;
  padding:16px 16px 12px;box-shadow:var(--shadow);max-height:calc(100vh - 36px);overflow:auto}}
.toc summary{{cursor:pointer;font-size:13px;letter-spacing:.08em;text-transform:uppercase;
  color:var(--muted);font-weight:800;list-style:none;display:flex;align-items:center;
  justify-content:space-between;gap:10px;margin:0 0 8px}}
.toc summary::-webkit-details-marker{{display:none}}
.toc summary::after{{content:"⌄";color:#8a94a6;font-size:16px;line-height:1}}
.toc[open] summary::after{{content:"⌃"}}
.toc-list,.toc-list ul{{list-style:none;margin:0;padding:0}}
.toc-list li{{margin:1px 0}}
.toc-list a{{display:block;padding:4px 8px;border-radius:7px;text-decoration:none;color:#445063;
  font-size:13px;line-height:1.35}}
.toc-list a:hover{{background:#f2f6ff;color:#1d4ed8}}
.toc-list a.on{{background:#e8efff;color:#1d4ed8;font-weight:700}}
.toc-list ul{{margin:1px 0 5px 9px;border-left:1px solid var(--line);padding-left:7px}}
.toc-list ul a{{font-size:12.4px;color:#667386}}

article{{min-width:0}}
article>h2{{font-size:22px;line-height:1.3;margin:34px 0 14px;padding-top:8px;letter-spacing:-.01em}}
article>h2:first-child{{margin-top:0}}
article>h3{{font-size:17px;margin:26px 0 10px;color:#1d2740}}
article p{{margin:0 0 13px}}
article ul,article ol{{margin:0 0 15px;padding-left:24px}}
article li{{margin-bottom:7px}}
article strong{{color:#0f172a}}
article code{{background:#f1f4f9;border:1px solid var(--line);border-radius:6px;padding:1px 6px;
  font-size:13.5px;font-family:"JetBrains Mono",Consolas,monospace;overflow-wrap:anywhere}}
article pre{{background:#0f172a;color:#e2e8f0;border-radius:12px;padding:14px 16px;overflow:auto;
  font-size:13px;line-height:1.5}}
article pre code{{background:none;border:0;padding:0;color:inherit}}
article blockquote{{margin:0 0 20px;background:#f8fafd;border:1px solid var(--line);
  border-left:4px solid var(--blue);border-radius:12px;padding:14px 17px;color:#4b5769}}
article blockquote p:last-child{{margin-bottom:0}}
article hr{{border:0;border-top:1px solid var(--line);margin:26px 0}}
.table-wrap{{overflow-x:auto;-webkit-overflow-scrolling:touch;margin:14px 0 20px;
  border:1px solid var(--line);border-radius:12px;background:#fff}}
.table-wrap::before{{content:"↔ таблицу можно прокрутить";display:none;font-size:11.5px;
  color:var(--muted);padding:7px 11px 0;background:#fff}}
table{{width:100%;border-collapse:collapse;font-size:14px;min-width:560px}}
th,td{{padding:9px 12px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}}
th{{background:#f6f8fb;font-size:11.5px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);
  font-weight:800;position:sticky;top:0}}
tbody tr:nth-child(even){{background:#fafbfe}}
tbody tr:last-child td{{border-bottom:0}}
tbody tr:hover{{background:#f5f9ff}}
.lead{{font-size:17px;color:#3c485b;max-width:900px}}
.cta{{display:flex;flex-wrap:wrap;gap:14px;align-items:center;justify-content:space-between;
  background:linear-gradient(135deg,#eef4ff,#f8fafd);border:1px solid #d7e2f7;border-radius:14px;
  padding:15px 18px;margin:0 0 24px}}
.cta p{{margin:0;max-width:720px;font-size:14px;color:#445063}}
.cta a{{white-space:nowrap}}
.hlink{{margin-left:6px;color:#b6c0d0;text-decoration:none;font-weight:400;opacity:0;transition:.15s}}
h2:hover .hlink,h3:hover .hlink{{opacity:1}}
.hlink:hover{{color:var(--blue)}}
footer{{text-align:center;color:var(--muted);font-size:12.5px;padding:28px 0 0}}
#toTop{{position:fixed;right:18px;bottom:18px;width:42px;height:42px;border-radius:50%;
  border:1px solid var(--line);background:#fff;color:var(--blue);font-size:19px;font-weight:800;
  box-shadow:var(--shadow);cursor:pointer;display:none;z-index:20}}
#toTop.show{{display:block}}

@media(max-width:960px){{
  .doc-layout{{grid-template-columns:1fr;margin-top:0}}
  .toc{{position:static;max-height:none}}
  .toc-list{{columns:2;column-gap:18px}}
  .toc-list ul{{columns:1}}
}}
@media(max-width:620px){{
  .wrap{{padding:0 15px 60px}}
  header.hero{{padding:34px 0 30px}}
  .toc-list{{columns:1}}
  article>h2{{font-size:19px}}
  .table-wrap{{margin-left:-2px;margin-right:-2px}}
  .table-wrap::before{{display:block}}
}}
@media print{{
  body{{background:#fff}} header.hero{{background:#1d2740 !important;-webkit-print-color-adjust:exact}}
  .toc,#toTop,.hlink{{display:none}} .doc-layout{{display:block}}
  article{{max-width:none}} .table-wrap{{overflow:visible}} table{{min-width:0}}
}}
</style>
</head>
<body>
<header class="hero">
  <div class="wrap">
    <div class="eyebrow">Методический конспект · физика 7–11</div>
    <h1>{html.escape(title)}</h1>
    <p>Один опыт — падение и отскок мяча — как универсальный стенд для измерения, кинематики,
      динамики, энергии, импульса, звука и оптики. С вопросами, планами уроков и типичными ошибками.</p>
    <div class="chips">
      <span class="chip"><b>7–11</b> классы</span>
      <span class="chip"><b>20+</b> тем</span>
      <span class="chip"><b>9</b> интерактивов</span>
      <span class="chip"><b>109</b> кадров · 30 к/с</span>
      <span class="chip">прямо и косвенно</span>
    </div>
    <div class="hero-actions">
      <a class="btn primary" href="report.html#school">Открыть интерактивы →</a>
      <a class="btn" href="school_physics.md" download>Скачать Markdown</a>
      <a class="btn" href="report.html">Весь отчёт</a>
    </div>
  </div>
</header>

<div class="wrap">
  <div class="doc-layout">
    <details class="toc" open>
      <summary>Содержание</summary>
      {toc_html}
    </details>
    <article>
      <div class="cta">
        <p><b>Нужны модели к этим темам?</b> В интерактивном отчёте — свободное падение на планетах,
          отскок и коэффициент восстановления, энергия, сопротивление воздуха, размытие, параллакс,
          подгонка параболы, звук и импульс.</p>
        <a class="btn primary" style="background:#2563eb;border-color:#2563eb;color:#fff"
           href="report.html#school">К интерактивам →</a>
      </div>
      {body}
    </article>
  </div>
  <footer>Собрано из <code>school_physics.md</code> · видео <code>drop.mp4</code> · 30 к/с ·
    интерактивная версия — <a href="report.html#school">report.html#school</a></footer>
</div>
<button id="toTop" type="button" aria-label="Наверх">↑</button>
<script>
(function(){{
  "use strict";
  const toc = document.querySelector('.toc');
  if (toc && window.matchMedia('(max-width: 960px)').matches) toc.removeAttribute('open');
  const links = Array.from(document.querySelectorAll('.toc a[href^="#"]'));
  const map = new Map(links.map(a => [a.getAttribute('href').slice(1), a]));
  const heads = Array.from(document.querySelectorAll('article h2[id], article h3[id]'));
  if ('IntersectionObserver' in window) {{
    const obs = new IntersectionObserver(entries => {{
      entries.forEach(en => {{
        if (!en.isIntersecting) return;
        links.forEach(a => a.classList.remove('on'));
        const a = map.get(en.target.id);
        if (a) a.classList.add('on');
      }});
    }}, {{rootMargin: '-10% 0px -75% 0px', threshold: 0}});
    heads.forEach(h => obs.observe(h));
  }}
  const top = document.getElementById('toTop');
  const onScroll = () => top.classList.toggle('show', window.scrollY > 700);
  window.addEventListener('scroll', onScroll, {{passive:true}});
  onScroll();
  top.addEventListener('click', () => window.scrollTo({{top:0, behavior:'smooth'}}));
  // На мобильных TOC не должен занимать полэкрана: сворачиваем после перехода.
  links.forEach(a => a.addEventListener('click', () => {{
    if (window.matchMedia('(max-width: 960px)').matches) {{
      setTimeout(() => window.scrollBy(0, -8), 60);
    }}
  }}));
}})();
</script>
</body>
</html>
"""
    OUT.write_text(page, encoding="utf-8")
    print(f"{OUT.name}: {len(page.encode()) / 1024:.1f} КБ, разделов в TOC: {len(toc)}")


if __name__ == "__main__":
    main()
