#!/usr/bin/env python3
"""Render the playbook and proposal Markdown into styled static HTML pages."""
import markdown, pathlib

def render_md(path):
    return markdown.markdown(
        pathlib.Path(path).read_text(encoding="utf-8"),
        extensions=["tables", "fenced_code", "sane_lists", "toc", "attr_list", "md_in_html"],
    )

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<meta name="description" content="__DESC__">
<meta property="og:title" content="__TITLE__">
<meta property="og:description" content="__DESC__">
<meta property="og:type" content="article">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Hanken+Grotesk:wght@400;500;600;700;800&family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;1,6..72,400&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
:root{
  --paper:#FAFAF7; --ink:#0B0E0C; --navy:#052B42; --navy2:#0E3F5C;
  --lime:#E0FF4F; --mist:#6E726B; --line:#E7E8E4; --soft:#F4F5F2;
  --serif:"Newsreader",Georgia,serif; --sans:"Hanken Grotesk",system-ui,sans-serif; --mono:"JetBrains Mono",monospace;
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--serif);font-size:19px;line-height:1.72;-webkit-font-smoothing:antialiased}
::selection{background:var(--lime);color:var(--navy)}
.topbar{position:sticky;top:0;z-index:10;display:flex;align-items:center;justify-content:space-between;gap:1rem;
  padding:.8rem clamp(1rem,4vw,2rem);background:rgba(5,43,66,.97);backdrop-filter:blur(8px);color:#fff;border-bottom:2px solid var(--lime)}
.topbar .brand{display:flex;align-items:center;gap:.55rem;font-family:var(--sans);font-weight:800;font-size:1rem;letter-spacing:.01em}
.topbar .dot{width:.55rem;height:.55rem;border-radius:50%;background:var(--lime);box-shadow:0 0 10px var(--lime)}
.topbar a{color:var(--lime);font-family:var(--mono);font-size:.74rem;text-decoration:none;letter-spacing:.04em;border:1px solid rgba(224,255,79,.4);padding:.4rem .7rem;border-radius:3px;white-space:nowrap}
.topbar a:hover{background:var(--lime);color:var(--navy)}
.wrap{max-width:760px;margin:0 auto;padding:clamp(2rem,5vw,4rem) clamp(1.1rem,4vw,1.5rem) 5rem}
.kicker{font-family:var(--mono);font-size:.72rem;letter-spacing:.22em;text-transform:uppercase;color:var(--mist);margin:0 0 1.2rem}
h1,h2,h3,h4{font-family:var(--sans);color:var(--navy);line-height:1.15;letter-spacing:-.01em}
h1{font-size:clamp(2.2rem,6vw,3.1rem);font-weight:800;margin:.2rem 0 .6rem}
h2{font-size:clamp(1.5rem,4vw,2rem);font-weight:700;margin:3rem 0 .9rem;padding-top:1.2rem;border-top:2px solid var(--lime)}
h3{font-size:1.25rem;font-weight:700;margin:2rem 0 .5rem}
h4{font-size:1.02rem;font-weight:700;margin:1.4rem 0 .4rem;font-family:var(--sans)}
p{margin:0 0 1.15rem}
a{color:var(--navy2);text-decoration:underline;text-underline-offset:2px;text-decoration-color:rgba(14,63,92,.35)}
a:hover{text-decoration-color:var(--lime);background:linear-gradient(transparent 60%, rgba(224,255,79,.5) 0)}
strong{color:var(--navy);font-weight:600}
em{font-style:italic}
ul,ol{margin:0 0 1.15rem;padding-left:1.3rem}
li{margin:.3rem 0}
hr{border:0;height:2px;background:linear-gradient(90deg,var(--lime),transparent);margin:2.5rem 0}
blockquote{margin:1.4rem 0;padding:.4rem 0 .4rem 1.2rem;border-left:3px solid var(--lime);color:var(--navy2);font-style:italic;background:linear-gradient(90deg,var(--soft),transparent)}
blockquote p{margin:.3rem 0}
code{font-family:var(--mono);font-size:.84em;background:var(--soft);padding:.12em .4em;border-radius:4px;color:var(--navy)}
pre{background:var(--navy);color:#E8EEF3;padding:1rem 1.2rem;border-radius:8px;overflow:auto;font-size:.82rem}
pre code{background:none;color:inherit;padding:0}
table{width:100%;border-collapse:collapse;margin:1.4rem 0;font-family:var(--sans);font-size:.92rem}
th,td{text-align:left;padding:.6rem .8rem;border-bottom:1px solid var(--line);vertical-align:top}
thead th{background:var(--navy);color:#fff;font-weight:600;border-bottom:none}
tbody tr:nth-child(even){background:var(--soft)}
.lead{font-size:1.18rem}
.sitefoot{max-width:760px;margin:0 auto;padding:2rem clamp(1.1rem,4vw,1.5rem) 4rem;border-top:1px solid var(--line);font-family:var(--sans);font-size:.85rem;color:var(--mist)}
.sitefoot a{color:var(--navy2)}
</style>
</head>
<body>
<div class="topbar">
  <span class="brand"><span class="dot"></span>__BRAND__</span>
  <a href="__NAVHREF__" target="_blank" rel="noopener">__NAVTEXT__ &rarr;</a>
</div>
<main class="wrap">
<p class="kicker">__KICKER__</p>
__BODY__
</main>
<footer class="sitefoot">
__FOOTER__
</footer>
</body>
</html>
"""

def write_page(out_path, *, body, title, desc, brand, navhref, navtext, kicker, footer):
    html = (PAGE
            .replace("__BODY__", body)
            .replace("__TITLE__", title)
            .replace("__DESC__", desc)
            .replace("__BRAND__", brand)
            .replace("__NAVHREF__", navhref)
            .replace("__NAVTEXT__", navtext)
            .replace("__KICKER__", kicker)
            .replace("__FOOTER__", footer))
    pathlib.Path(out_path).write_text(html, encoding="utf-8")
    print(f"{out_path} written: {len(html)} bytes")

# The playbook (home page).
write_page(
    "index.html",
    body=render_md("00_MASTER_PLAYBOOK.md"),
    title="Sponsorship Playbook — How to Get Sponsorships",
    desc="The complete operating system for getting corporate sponsorships, synthesized from modern sponsorship-sales best practices. A research archive + reusable playbook.",
    brand="Sponsorship Playbook",
    navhref="https://github.com/opencolin/sponsorship",
    navtext="Full archive on GitHub",
    kicker="Research archive &middot; how to get sponsorships",
    footer=('A synthesis of modern sponsorship-sales best practices, compiled for BuilderShip sponsor outreach. '
            'The full archive &mdash; 21 digests and a reusable Claude skill &mdash; is '
            '<a href="https://github.com/opencolin/sponsorship">on GitHub</a>.'),
)

# The Ethereum 11th-birthday partner proposal (public, partner-facing).
write_page(
    "proposals/eth-11-celebration.html",
    body=render_md("proposals/eth-11-celebration.public.md"),
    title="Ethereum Turns 11 — A Builder-First Celebration",
    desc="A builder-first celebration of 11 years of Ethereum mainnet. San Francisco, July 30, 2026. Hosted by Dabl. Partner with the room that decides what gets built.",
    brand="Ethereum Turns 11",
    navhref="https://dablclub.com",
    navtext="dablclub.com",
    kicker="Partner invitation &middot; hosted by Dabl",
    footer=('Hosted by <a href="https://dablclub.com">Dabl</a> &middot; Frontier Tower, San Francisco &middot; July 30, 2026. '
            'Questions? <a href="mailto:collin@dabl.club">collin@dabl.club</a>.'),
)
