#!/usr/bin/env python3
"""Build the static results site from data/figures.json, data/pages.json and data/overview.json.

    python tools/build_site.py --src <path to sim_lag30/analisis>

* every included figure is converted to WebP (max width 1800 px, quality 85) into img/<page>/<id>.webp, and the page
  covers to small thumbnails (img/thumbs/);
* one HTML page per entry of data/pages.json, plus index.html (visual overview) and talk.html (talk figures in slide
  order);
* each figure shows its header and the image; its explanation and source path are folded under "About this figure";
* the skill tables (data/skill_by_site.csv, data/skill_by_run.csv) are rendered on the skill page.
The site is plain HTML + CSS + a small script (click a figure to enlarge); no build step is needed to view it.
"""
import argparse
import csv
import hashlib
import html
import json
import re
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
MAX_W = 1800
THUMB_W = 640
QUALITY = 85
SITE_EN = {"Murcia": "Murcia", "Monaco": "Monaco", "Cerdenia": "Sardinia", "Croacia": "Croatia", "Albania": "Albania",
           "Grecia": "Greece", "Turquia": "Turkey", "Siria": "Syria", "Egipto": "Egypt", "Libia": "Libya",
           "Tunez": "Tunisia", "Argelia": "Algeria"}


def esc(s):
    return html.escape(str(s), quote=True)


def slug(src):
    s = re.sub(r"\.png$", "", src)
    return re.sub(r"[^A-Za-z0-9]+", "-", s).strip("-").lower()


def convert(src_path, out_path, max_w=MAX_W):
    """PNG -> WebP (RGB on white). Skips the work when the output exists and the source hash is unchanged."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    digest = f"{hashlib.sha256(src_path.read_bytes()).hexdigest()[:16]}-{max_w}"
    stamp = out_path.with_suffix(".src")
    if out_path.exists() and stamp.exists() and stamp.read_text() == digest:
        with Image.open(out_path) as im:
            return im.size
    with Image.open(src_path) as im:
        im = im.convert("RGBA")
        bg = Image.new("RGB", im.size, "white")
        bg.paste(im, mask=im.split()[3])
        if bg.width > max_w:
            bg = bg.resize((max_w, round(bg.height * max_w / bg.width)), Image.LANCZOS)
        bg.save(out_path, "WEBP", quality=QUALITY, method=6)
        stamp.write_text(digest)
        return bg.size


def nav(pages, current):
    """Top menu: Overview and Talk, then the topic pages grouped (Method / Results / More) with a small group label."""
    def link(h, t, k):
        return f'<a href="{h}"{" class=\"on\"" if k == current else ""}>{esc(t)}</a>'
    parts = [f'<div class="grp">{link("index.html", "Overview", "index")}{link("talk.html", "Talk", "talk")}</div>']
    groups = []
    for p in pages:
        if not groups or groups[-1][0] != p["group"]:
            groups.append((p["group"], []))
        groups[-1][1].append(link(f"{p['id']}.html", p["nav"], p["id"]))
    for g, links in groups:
        parts.append(f'<div class="grp"><span class="glab">{esc(g)}</span>{"".join(links)}</div>')
    return f'<nav class="top">{"".join(parts)}</nav>'


def shell(title, body, pages, current):
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} · Plinius 19 · Mediterranean heatwave drivers</title>
<link rel="stylesheet" href="assets/style.css">
</head>
<body>
<header class="site">
  <div class="wrap">
    <a class="brand" href="index.html">Plinius 19 · Drivers of Mediterranean heatwaves</a>
    {nav(pages, current)}
  </div>
</header>
<main class="wrap">
{body}
</main>
<footer class="wrap">STCO-FS results · train 1950–2010 · test 2011–2021</footer>
<div id="lightbox" hidden><img alt=""><p></p></div>
<script src="assets/site.js"></script>
</body>
</html>
"""


def figure_card(f, label="", msg=""):
    w, h = f["size"]
    lab = f'<span class="slide">{esc(label)}</span>' if label else ""
    return f"""<figure class="card" id="{esc(f['id'])}">
  {lab}<h3><a class="anchor" href="#{esc(f['id'])}">{esc(f['title'])}</a></h3>
  <a class="zoom" href="{esc(f['img'])}"><img src="{esc(f['img'])}" alt="{esc(f['title'])}" width="{w}" height="{h}" loading="lazy"></a>{msg}
  <details><summary>About this figure</summary><p>{esc(f['caption'])}</p><p class="src">{esc(f['src'])}</p></details>
</figure>"""


def sections_of(figs):
    out = {}
    for f in sorted(figs, key=lambda f: (f["order"], f["title"])):
        out.setdefault(f["section"], []).append(f)
    return out


def page_html(p, figs, extra=""):
    secs = sections_of(figs)
    parts = [f"<h1>{esc(p['title'])}</h1>", f'<p class="lede">{esc(p["blurb"])}</p>']
    if len(secs) > 1:
        toc = "".join(f'<a href="#sec-{slug(s)}">{esc(s)} <span class="n">{len(v)}</span></a>' for s, v in secs.items())
        parts.append(f'<nav class="toc">{toc}</nav>')
    if extra:
        parts.append(extra)
    for s, v in secs.items():
        parts.append(f'<section><h2 id="sec-{slug(s)}">{esc(s)}</h2>')
        parts += [figure_card(f) for f in v]
        parts.append("</section>")
    return "\n".join(parts)


def fmt(x, nd=2):
    try:
        return f"{float(x):.{nd}f}"
    except (TypeError, ValueError):
        return esc(x)


def skill_tables():
    site_csv, run_csv = ROOT / "data" / "skill_by_site.csv", ROOT / "data" / "skill_by_run.csv"
    rows = sorted(csv.DictReader(site_csv.open()), key=lambda r: -float(r["test_auc_mean"]))
    head = ("<tr><th>Site</th><th>Test AUC<br><small>mean (min–max)</small></th><th>Test F1</th>"
            "<th>Always-yes F1</th><th>F1 gain</th><th>Seeds with gain CI &gt; 0</th><th>Train AUC</th><th>CV F1</th></tr>")
    body = "".join(
        f"<tr><td>{esc(SITE_EN.get(r['site'], r['site']))}</td><td>{fmt(r['test_auc_mean'])} ({fmt(r['test_auc_min'])}–"
        f"{fmt(r['test_auc_max'])})</td><td>{fmt(r['test_f1_mean'])}</td><td>{fmt(r['always_yes_test_f1'])}</td>"
        f"<td>{fmt(r['f1_gain_mean'])}</td><td>{esc(r['n_seeds_gain_ci_excludes_0'])}/{esc(r['n_seeds'])}</td>"
        f"<td>{fmt(r['train_auc_mean'])}</td><td>{fmt(r['cv_f1_mean'])}</td></tr>" for r in rows)
    out = [f'<section><h2 id="sec-tables">Skill tables</h2><figure class="card"><h3>Skill by site (mean of 3 seeds, test '
           f'2011–2021)</h3><div class="tw"><table>{head}{body}</table></div><details><summary>About this table</summary>'
           f'<p>F1 gain = test F1 minus the F1 of always predicting a heatwave day; its CI is a year-block bootstrap over the 11 '
           f'test years. Train AUC is 0.95–0.99 (site means): the models overfit, so only test scores measure skill.</p>'
           f'<p class="src">general/resultados/skill_by_site.csv · <a href="data/skill_by_site.csv">download</a></p>'
           f'</details></figure>']
    runs = list(csv.DictReader(run_csv.open()))
    head = ("<tr><th>Site</th><th>Seed</th><th>Test AUC (95% CI)</th><th>Test F1</th><th>F1 gain (95% CI)</th>"
            "<th>CV F1</th><th>Train F1</th><th>Train AUC</th><th>Drivers</th><th>Columns</th></tr>")
    body = "".join(
        f"<tr><td>{esc(SITE_EN.get(r['site'], r['site']))}</td><td>{esc(r['seed'])}</td><td>{fmt(r['test_auc'])} "
        f"({fmt(r['test_auc_ci_lo'])}–{fmt(r['test_auc_ci_hi'])})</td><td>{fmt(r['test_f1'])}</td><td>{fmt(r['f1_gain'])} "
        f"({fmt(r['f1_gain_ci_lo'])}–{fmt(r['f1_gain_ci_hi'])})</td><td>{fmt(r['cv_f1'])}</td><td>{fmt(r['train_f1'])}</td>"
        f"<td>{fmt(r['train_auc'])}</td><td>{esc(r['n_drivers'])}</td><td>{esc(r['n_columns'])}</td></tr>" for r in runs)
    out.append(f'<figure class="card"><h3>Skill by run (12 sites × seeds 42, 43, 44)</h3><div class="tw"><table>{head}{body}'
               f'</table></div><details><summary>About this table</summary><p>One row per CRO run. Drivers = selected '
               f'drivers; columns = lagged inputs of the logistic regression.</p><p class="src">general/resultados/'
               f'skill_by_run.csv · <a href="data/skill_by_run.csv">download</a></p></details></figure></section>')
    return "\n".join(out)


def thumb(src_root, src):
    out = ROOT / "img" / "thumbs" / f"{slug(src)}.webp"
    convert(src_root / src, out, THUMB_W)
    return out.relative_to(ROOT).as_posix()


def index_html(ov, pages, figs, talk, src_root, by_src):
    hero = by_src[ov["hero"]]
    stats = "".join(f'<div class="stat"><b>{esc(s["value"])}</b><span>{esc(s["label"])}</span></div>' for s in ov["stats"])
    steps = "".join(f'<figure class="step"><a class="zoom" href="{esc(s["img"])}"><img src="{esc(s["img"])}" alt="{esc(s["label"])}" '
                    f'loading="lazy"></a><figcaption>{esc(s["label"])}</figcaption></figure>' for s in ov["steps"])
    concl = "".join(f'<li><span class="num">{i:02d}</span>{esc(c)}</li>' for i, c in enumerate(ov["conclusions"], 1))
    cards = [("talk.html", "Talk figures", f"{len(talk)} figures", thumb(src_root, ov["talk_cover"]))]
    cards += [(f"{p['id']}.html", p["title"], f"{sum(f['page'] == p['id'] for f in figs)} figures",
               thumb(src_root, p["cover"])) for p in pages]
    grid = "".join(f'<a class="pcard" href="{h}"><img src="{im}" alt="" loading="lazy"><h3>{esc(t)}</h3>'
                   f'<span class="n">{esc(n)}</span></a>' for h, t, n, im in cards)
    return f"""<section class="hero">
  <p class="kicker">{esc(ov['kicker'])}</p>
  <h1>{esc(ov['title'])}</h1>
  <p class="authors">{esc(ov['authors'])}</p>
  <a class="zoom" href="{esc(hero['img'])}"><img src="{esc(hero['img'])}" alt="{esc(hero['title'])}"></a>
</section>
<div class="stats">{stats}</div>
<h2>Framework</h2>
<div class="steps">{steps}</div>
<h2>Conclusions</h2>
<ol class="concl">{concl}</ol>
<h2>Explore the results</h2>
<div class="pages">{grid}</div>
<p class="credits">{esc(ov['credits'])}</p>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="path to sim_lag30/analisis")
    src_root = Path(ap.parse_args().src).resolve()
    pages = json.loads((ROOT / "data" / "pages.json").read_text())
    ov = json.loads((ROOT / "data" / "overview.json").read_text())
    figs = [f for f in json.loads((ROOT / "data" / "figures.json").read_text()) if f.get("include", True)]
    ids = set()
    for f in figs:
        f["id"] = slug(f["src"])
        if f["id"] in ids:
            raise ValueError(f"duplicate figure id {f['id']}")
        ids.add(f["id"])
        out = ROOT / "img" / f["page"] / f"{f['id']}.webp"
        f["size"] = convert(src_root / f["src"], out)
        f["img"] = out.relative_to(ROOT).as_posix()
    by_src = {f["src"]: f for f in figs}
    page_ids = {p["id"] for p in pages}
    bad = [f["src"] for f in figs if f["page"] not in page_ids]
    if bad:
        raise ValueError(f"figures with unknown page: {bad}")
    for p in pages:
        pf = [f for f in figs if f["page"] == p["id"]]
        extra = skill_tables() if p["id"] == "skill" else ""
        (ROOT / f"{p['id']}.html").write_text(shell(p["title"], page_html(p, pf, extra), pages, p["id"]), encoding="utf-8")
    talk = sorted([f for f in figs if f.get("talk")], key=lambda f: f["talk_order"])
    body = ["<h1>Talk</h1>", '<p class="lede">The figures of the Plinius 19 talk, by slide, with the key messages shown on each '
            'results slide.</p>']
    slides = {t["src"]: t for t in json.loads((ROOT / "data" / "talk.json").read_text())}
    for f in talk:
        t = slides.get(f["src"], {})
        msg = ""
        if t.get("headline"):
            items = "".join(f"<li>{esc(b)}</li>" for b in t.get("bullets", []))
            msg = f'<div class="msg"><p>{esc(t["headline"])}</p><ul>{items}</ul></div>'
        body.append(figure_card(dict(f, id=f"talk-{f['id']}"), f"Slide {f['slide']}", msg))
    (ROOT / "talk.html").write_text(shell("Talk", "\n".join(body), pages, "talk"), encoding="utf-8")
    (ROOT / "index.html").write_text(shell("Overview", index_html(ov, pages, figs, talk, src_root, by_src), pages, "index"),
                                     encoding="utf-8")
    # remove images no longer referenced
    keep = {ROOT / f["img"] for f in figs} | set((ROOT / "img" / "thumbs").glob("*.webp"))
    thumbs_used = {ROOT / "img" / "thumbs" / f"{slug(s)}.webp" for s in [ov["talk_cover"]] + [p["cover"] for p in pages]}
    for old in (ROOT / "img").rglob("*.webp"):
        if old not in keep or (old.parent.name == "thumbs" and old not in thumbs_used):
            old.unlink()
            old.with_suffix(".src").unlink(missing_ok=True)
    print(f"{len(figs)} figures, {len(pages)} pages, {len(talk)} talk figures")


if __name__ == "__main__":
    main()
