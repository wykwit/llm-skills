#!/usr/bin/env python3
"""Render a step-by-step PR walkthrough (real diffs + review comments) as one HTML file.

Usage (run from the repo root):
    build_report.py SPEC.json [--out PATH] [--inline]

SPEC.json is described in REPORT-SPEC.md next to SKILL.md. Diffs are taken live from
`git diff <base>...<head> -- <path>`, so re-running after new commits refreshes them.
Exits non-zero if a changed file is neither shown in a step nor listed under "skip".
"""

import argparse
import base64
import fnmatch
import html
import json
import subprocess
import sys
import urllib.request
from datetime import date

D2H = "3.4.48"
D2H_CSS = f"https://cdn.jsdelivr.net/npm/diff2html@{D2H}/bundles/css/diff2html.min.css"
D2H_JS = f"https://cdn.jsdelivr.net/npm/diff2html@{D2H}/bundles/js/diff2html-ui.min.js"
TONES = {"neutral", "attention", "ok"}
FONT_CDN = "https://cdn.jsdelivr.net/fontsource/fonts"
FONTS = [
    ("Plex Sans", "ibm-plex-sans", 400),
    ("Plex Sans", "ibm-plex-sans", 600),
    ("Plex Mono", "ibm-plex-mono", 400),
    ("Plex Mono", "ibm-plex-mono", 500),
]
_SVG = '<svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
ICON_CHECK = _SVG + '<path d="M3.5 8.5l3 3 6-7"/></svg>'
# Two stacked bars (unified) and two columns (side by side): the icon shows the mode the button switches to.
ICON_SPLIT = _SVG + '<rect x="2" y="3" width="5" height="10" rx="1"/><rect x="9" y="3" width="5" height="10" rx="1"/></svg>'
ICON_STACK = _SVG + '<rect x="2" y="2.5" width="12" height="4.5" rx="1"/><rect x="2" y="9" width="12" height="4.5" rx="1"/></svg>'


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout


def file_diff(rng, path, focus):
    raw = git("diff", "--no-color", rng, "--", path)
    if not focus or not raw:
        return raw
    # Keep the file header plus only the hunks that mention a focus needle.
    head, *hunks = raw.split("\n@@")
    kept = [h for h in hunks if any(n in h for n in focus)]
    if not kept:
        sys.exit(f"focus {focus!r} matched no hunk in {path}")
    return head + "".join("\n@@" + h for h in kept)


def stats(raw):
    lines = raw.splitlines()
    add = sum(1 for l in lines if l.startswith("+") and not l.startswith("+++"))
    rem = sum(1 for l in lines if l.startswith("-") and not l.startswith("---"))
    return add, rem


def esc(s):
    return html.escape(s or "")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--out")
    ap.add_argument("--inline", action="store_true", help="embed diff2html for offline viewing")
    a = ap.parse_args()

    spec = json.load(open(a.spec))
    base, head = spec["base"], spec.get("head", "HEAD")
    rng = f"{base}...{head}"
    out = a.out or spec.get("out") or f"/tmp/{spec.get('slug', 'pr')}-walkthrough.html"

    changed = [p for p in git("diff", "--name-only", rng).splitlines() if p]
    commits = len(git("log", "--oneline", f"{base}..{head}").splitlines())
    shown, payloads, sections, nav = set(), {}, [], []

    for i, step in enumerate(spec["steps"], 1):
        num = f"{i:02d}"
        tone = step.get("tone", "neutral")
        if tone not in TONES:
            sys.exit(f"step {num}: tone must be one of {sorted(TONES)}")
        files_html = ""
        for f in step.get("files", []):
            f = {"path": f} if isinstance(f, str) else f
            path = f["path"]
            if path not in changed:
                sys.exit(f"step {num}: {path} is not in {rng}")
            shown.add(path)
            raw = file_diff(rng, path, f.get("focus"))
            key = f"d{len(payloads)}"
            payloads[key] = raw
            add, rem = stats(raw)
            part = " · excerpt" if f.get("focus") else ""
            files_html += (
                f'<div class="fileblock"><div class="filehead"><span class="fpath">{esc(path)}</span>'
                f'<span class="fstat"><span class="add">+{add}</span> <span class="del">&minus;{rem}</span>'
                f'<span class="fnote">{esc(f.get("note", ""))}{part}</span></span></div>'
                f'<div class="difftarget" id="{key}"></div></div>'
            )
        bullets = "".join(f"<li>{b}</li>" for b in step.get("bullets", []))
        comment = step.get("comment")
        sections.append(
            f'<section class="step {tone}" id="s{num}"><header class="stephead"><span class="num">{num}</span>'
            f'<div class="titles"><h2>{esc(step["title"])}</h2>'
            + (f'<p class="subtitle">{esc(step["subtitle"])}</p>' if step.get("subtitle") else "")
            + f'</div><span class="badge">{esc(step.get("badge", ""))}</span></header>'
            f'<p class="explain">{step.get("explain", "")}</p>'
            + (f'<ul class="points">{bullets}</ul>' if bullets else "")
            + files_html
            + (f'<div class="cr"><span class="crlabel">Review</span><div>{comment}</div></div>' if comment else "")
            + "</section>"
        )
        nav.append(f'<a href="#s{num}" class="{tone}"><span class="num">{num}</span><span>{esc(step["title"])}</span></a>')

    skipped = []
    for s in spec.get("skip", []):
        hits = [p for p in changed if fnmatch.fnmatch(p, s["glob"])]
        shown.update(hits)
        n = f"{len(hits)} file" + ("" if len(hits) == 1 else "s")
        skipped.append(f'<li><code>{esc(s["glob"])}</code> · {n} · {esc(s["reason"])}</li>')
    missing = [p for p in changed if p not in shown]
    if missing:
        sys.exit("changed files not covered by any step or skip:\n  " + "\n  ".join(missing))

    ck = spec.get("checklist", {})

    def ck_list(key, label, cls):
        items = ck.get(key) or []
        if not items:
            return ""
        return f'<h3 class="{cls}">{label}</h3><ul>' + "".join(f"<li>{x}</li>" for x in items) + "</ul>"

    checklist = (
        ck_list("blockers", "Blocking: fix before approving", "blocker")
        + ck_list("confirm", "Confirm with the author or product", "attention")
        + ck_list("not_blocking", "Not blocking: follow-ups", "ok")
    ) or "<p>No blockers, confirmations or follow-ups found.</p>"
    nav.append(f'<a href="#checklist" class="ok"><span class="num">{ICON_CHECK}</span><span>Before you approve</span></a>')

    if a.inline:
        fetch = lambda u: urllib.request.urlopen(u).read()
        css = f"<style>{fetch(D2H_CSS).decode()}</style>"
        js = "<script>" + fetch(D2H_JS).decode().replace("</script", "<\\/script") + "</script>"
        font_src = lambda u: "data:font/woff2;base64," + base64.b64encode(fetch(u)).decode()
    else:
        css = f'<link rel="stylesheet" href="{D2H_CSS}">'
        js = f'<script src="{D2H_JS}"></script>'
        font_src = lambda u: u
    fonts = "".join(
        f"@font-face{{font-family:'{fam}';font-weight:{w};font-style:normal;font-display:swap;"
        f"src:url({font_src(f'{FONT_CDN}/{slug}@latest/latin-{w}-normal.woff2')}) format('woff2')}}"
        for fam, slug, w in FONTS
    )

    payload = json.dumps(payloads).replace("</", "<\\/")
    pills = "".join(f'<span class="pill">{esc(p)}</span>' for p in spec.get("pills", []))
    page = TEMPLATE.format(
        title=esc(spec["title"]),
        slug=esc(spec.get("slug", "")),
        summary=spec.get("summary", ""),
        verification=spec.get("verification", "Not stated."),
        rng=esc(rng),
        commits=f"{commits} commit" + ("" if commits == 1 else "s"),
        nfiles=f"{len(changed)} file" + ("" if len(changed) == 1 else "s"),
        today=date.today().isoformat(),
        pills=pills,
        nav="".join(nav),
        steps="".join(sections),
        skipped=('<h3 class="skipped">Not shown</h3><ul>' + "".join(skipped) + "</ul>") if skipped else "",
        checklist=checklist,
        css=css,
        js=js,
        fonts=fonts,
        icon_check=ICON_CHECK,
        icon_split=ICON_SPLIT,
        icon_split_js=json.dumps(ICON_SPLIT),
        icon_stack_js=json.dumps(ICON_STACK),
        payload=payload,
    )
    with open(out, "w") as fh:
        fh.write(page)
    print(f"wrote {out}: {len(spec['steps'])} steps, {len(payloads)} diffs, {len(changed)} changed files covered")


TEMPLATE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="dark">
<title>{slug} · {title}</title>
{css}
<style>
{fonts}
:root{{
  --bg:oklch(0.16 0.012 255);--panel:oklch(0.2 0.013 255);--inset:oklch(0.177 0.012 255);--code:oklch(0.145 0.012 255);
  --line:oklch(0.3 0.014 255);--line-soft:oklch(0.245 0.012 255);
  --ink:oklch(0.94 0.006 255);--muted:oklch(0.74 0.014 255);
  --accent:oklch(0.79 0.105 225);--warn:oklch(0.84 0.135 78);--ok:oklch(0.8 0.13 158);
  --tone:var(--accent);
  --sans:'Plex Sans',ui-sans-serif,system-ui,sans-serif;--mono:'Plex Mono',ui-monospace,SFMono-Regular,Menlo,monospace;
}}
.attention{{--tone:var(--warn)}}.ok{{--tone:var(--ok)}}.blocker{{--tone:oklch(0.76 0.14 25)}}
*{{box-sizing:border-box}}
html{{scroll-behavior:smooth;scrollbar-color:var(--line) var(--bg)}}
body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.6 var(--sans);-webkit-font-smoothing:antialiased}}
::selection{{background:color-mix(in oklch,var(--accent) 32%,transparent);color:var(--ink)}}
:focus-visible{{outline:2px solid var(--accent);outline-offset:2px;border-radius:6px}}
a{{color:var(--accent);text-underline-offset:3px}}
b,strong{{font-weight:600}}
code{{font:500 .86em var(--mono);background:var(--inset);border:1px solid var(--line-soft);border-radius:5px;padding:.05em .38em;color:var(--ink);overflow-wrap:anywhere}}
.layout{{display:flex;max-width:1480px;margin:0 auto}}
nav{{width:264px;flex-shrink:0;position:sticky;top:0;align-self:flex-start;height:100vh;overflow:auto;padding:32px 14px 32px 20px;border-right:1px solid var(--line-soft)}}
nav .brand{{font:500 12px var(--mono);color:var(--muted);padding:0 10px 14px}}
nav a{{display:flex;gap:10px;align-items:flex-start;padding:7px 10px;border-radius:8px;color:var(--muted);text-decoration:none;font-size:13.5px;line-height:1.4;transition:background .2s,color .2s}}
nav a:hover{{color:var(--ink);background:var(--inset)}}
nav a[aria-current]{{color:var(--ink);background:var(--panel)}}
.num{{display:inline-flex;flex-shrink:0;align-items:center;justify-content:center;width:24px;height:24px;border-radius:50%;
  font:600 11px var(--mono);font-variant-numeric:tabular-nums;color:var(--tone);background:color-mix(in oklch,var(--tone) 15%,transparent)}}
main{{flex:1;min-width:0;padding:40px 40px 120px}}
.page-head{{margin:0 0 28px}}
.page-head h1{{font-size:30px;line-height:1.2;font-weight:600;letter-spacing:-.02em;margin:0 0 10px;text-wrap:balance;max-width:28ch}}
.meta{{font:13px var(--mono);color:var(--muted);font-variant-numeric:tabular-nums}}
.meta code{{background:none;border:none;padding:0;color:var(--ink)}}
.pills{{display:flex;flex-wrap:wrap;gap:6px;margin-top:14px}}
.pill{{border:1px solid var(--line);border-radius:999px;padding:2px 10px;font-size:12.5px;color:var(--muted)}}
.lede{{font-size:16px;max-width:75ch;margin:0 0 16px}}
.verify{{display:flex;gap:14px;max-width:75ch;padding:12px 16px;border-radius:12px;background:var(--inset);border:1px solid var(--line-soft);font-size:14px;margin:0 0 40px}}
.verify .label{{flex-shrink:0;font-weight:600;color:var(--muted)}}
.step{{background:var(--panel);border:1px solid var(--line-soft);border-radius:14px;padding:24px 26px 26px;margin:0 0 28px;scroll-margin-top:24px}}
.step.attention{{border-color:color-mix(in oklch,var(--warn) 38%,var(--line-soft))}}
.stephead{{display:flex;gap:14px;align-items:flex-start}}
.stephead .num{{width:32px;height:32px;font-size:12.5px;margin-top:1px}}
.titles{{flex:1;min-width:0}}
.stephead h2{{margin:0;font-size:20px;line-height:1.35;font-weight:600;letter-spacing:-.01em;text-wrap:balance}}
.subtitle{{margin:2px 0 0;color:var(--muted);font-size:14px}}
.badge{{flex-shrink:0;border-radius:999px;padding:3px 11px;font-size:12.5px;font-weight:600;white-space:nowrap;color:var(--tone);background:color-mix(in oklch,var(--tone) 13%,transparent)}}
.explain{{margin:18px 0 8px;max-width:75ch}}
ul.points{{margin:8px 0 4px;padding-left:20px;max-width:75ch}}ul.points li{{margin:5px 0}}
ul.points li::marker{{color:var(--muted)}}
.cr{{display:flex;gap:14px;align-items:flex-start;margin-top:20px;padding:14px 16px;border-radius:12px;max-width:none;
  background:color-mix(in oklch,var(--tone) 8%,var(--panel));border:1px solid color-mix(in oklch,var(--tone) 26%,transparent)}}
.crlabel{{flex-shrink:0;font:600 11.5px var(--mono);color:var(--tone);padding:2px 8px;border-radius:6px;background:color-mix(in oklch,var(--tone) 16%,transparent);margin-top:2px}}
.cr > div{{max-width:80ch}}
.fileblock{{margin-top:18px;border:1px solid var(--line-soft);border-radius:10px;overflow:hidden;background:var(--code)}}
.filehead{{display:flex;justify-content:space-between;gap:12px;align-items:baseline;background:var(--inset);border-bottom:1px solid var(--line-soft);padding:8px 14px;font:12.5px var(--mono)}}
.fpath{{font-weight:500;word-break:break-all}}
.fstat{{white-space:nowrap;font-variant-numeric:tabular-nums}}
.fstat .add{{color:var(--ok)}}.fstat .del{{color:oklch(0.76 0.13 25)}}.fnote{{color:var(--muted);margin-left:10px}}
/* diff2html, dark and compact. Only colours and fonts are overridden. Each rule answers a bug users hit:
   isolation+relative: side-by-side panes painted over later steps;
   d2h positions line numbers absolutely and reserves room with code-line left padding
   (8em unified, 4.5em side-by-side): overriding that padding hides the start of every line;
   d2h code lines are nowrap; white-space:pre turns markup newlines into blank rows. */
.difftarget{{max-height:560px;overflow:auto;position:relative;isolation:isolate;scrollbar-color:var(--line) var(--code);
  --d2h-dark-bg-color:var(--code);--d2h-dark-color:var(--ink);--d2h-dark-dim-color:var(--muted);
  --d2h-dark-line-border-color:var(--line-soft);--d2h-dark-border-color:var(--line-soft);
  --d2h-dark-info-bg-color:color-mix(in oklch,var(--accent) 7%,var(--code));--d2h-dark-info-border-color:var(--line-soft);
  --d2h-dark-empty-placeholder-bg-color:var(--inset);--d2h-dark-empty-placeholder-border-color:var(--line-soft);
  /* d2h tints modified lines amber; amber means "needs attention" in this report, so keep red/green */
  --d2h-dark-change-del-color:oklch(0.62 0.17 25 / .16);--d2h-dark-change-ins-color:oklch(0.7 0.15 150 / .16);
  --d2h-dark-del-bg-color:oklch(0.62 0.17 25 / .13);--d2h-dark-ins-bg-color:oklch(0.7 0.15 150 / .13);
  --d2h-dark-del-highlight-bg-color:oklch(0.62 0.17 25 / .42);--d2h-dark-ins-highlight-bg-color:oklch(0.7 0.15 150 / .38)}}
.difftarget .d2h-file-wrapper{{border:none;border-radius:0;margin:0}}
.difftarget .d2h-file-header{{display:none}}
.difftarget .d2h-diff-table{{font:12px/1.45 var(--mono);font-variant-numeric:tabular-nums}}
.checklist h3{{margin:22px 0 6px;font-size:15px;font-weight:600;color:var(--tone)}}
.checklist h3:first-child{{margin-top:18px}}
.checklist ul{{margin:0;padding-left:20px;max-width:80ch}}.checklist li{{margin:6px 0}}
.checklist .skipped{{--tone:var(--muted)}}
#viewToggle{{position:fixed;right:22px;bottom:22px;z-index:50;display:inline-flex;align-items:center;gap:8px;
  background:oklch(0.26 0.014 255);color:var(--ink);border:none;border-radius:999px;padding:9px 16px;
  font:600 13px var(--sans);cursor:pointer;box-shadow:0 8px 24px -6px oklch(0 0 0 / .6);transition:background .2s}}
#viewToggle:hover{{background:oklch(0.3 0.016 255)}}
#viewToggle svg{{color:var(--accent)}}
@media (max-width:900px){{
  nav{{display:none}}main{{padding:22px 16px 100px}}
  .page-head h1{{font-size:24px}}
  .step{{padding:18px 16px 20px}}
  .stephead{{flex-wrap:wrap}}.titles{{flex-basis:calc(100% - 46px)}}.badge{{margin-left:46px}}
  .cr{{flex-direction:column;gap:8px}}
  .filehead{{flex-direction:column;gap:2px}}
}}
@media (prefers-reduced-motion:reduce){{html{{scroll-behavior:auto}}*{{transition:none!important}}}}
</style></head>
<body><div class="layout">
<nav aria-label="Reading order"><div class="brand">{slug} · reading order</div>{nav}</nav>
<main>
<header class="page-head"><h1>{title}</h1>
<div class="meta"><code>{rng}</code> · {commits} · {nfiles} · built {today}</div>
<div class="pills">{pills}</div></header>
<p class="lede">{summary}</p>
<div class="verify"><span class="label">Verification</span><span>{verification}</span></div>
{steps}
<section class="step ok" id="checklist"><header class="stephead"><span class="num">{icon_check}</span><div class="titles"><h2>Before you approve</h2></div></header>
<div class="checklist">{checklist}{skipped}</div></section>
</main></div>
<button id="viewToggle" type="button">{icon_split}<span>Side by side</span></button>
<script type="application/json" id="diffs">{payload}</script>
{js}
<script>
(function(){{
  var diffs=JSON.parse(document.getElementById('diffs').textContent),mode='line-by-line',btn=document.getElementById('viewToggle');
  var icons={{split:{icon_split_js},stack:{icon_stack_js}}};
  function drawAll(){{Object.keys(diffs).forEach(function(k){{
    var t=document.getElementById(k);t.innerHTML='';
    try{{var ui=new Diff2HtmlUI(t,diffs[k],{{outputFormat:mode,drawFileList:false,matching:'words',matchWordsThreshold:0.4,highlight:true,colorScheme:'dark'}});ui.draw();ui.highlightCode();}}
    catch(e){{t.innerHTML='<pre style="padding:12px;color:var(--warn)">diff2html failed: '+e.message+'</pre>';}}
  }});}}
  btn.addEventListener('click',function(){{
    mode=mode==='line-by-line'?'side-by-side':'line-by-line';
    btn.innerHTML=mode==='side-by-side'?icons.stack+'<span>Unified</span>':icons.split+'<span>Side by side</span>';
    drawAll();
  }});
  drawAll();
  var links={{}};document.querySelectorAll('nav a').forEach(function(a){{links[a.hash.slice(1)]=a;}});
  var spy=new IntersectionObserver(function(entries){{entries.forEach(function(e){{
    if(!e.isIntersecting)return;
    Object.values(links).forEach(function(a){{a.removeAttribute('aria-current');}});
    if(links[e.target.id])links[e.target.id].setAttribute('aria-current','step');
  }});}},{{rootMargin:'-20% 0px -70% 0px'}});
  document.querySelectorAll('main section[id]').forEach(function(s){{spy.observe(s);}});
}})();
</script></body></html>
"""

if __name__ == "__main__":
    main()
