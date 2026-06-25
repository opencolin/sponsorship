#!/usr/bin/env python3
"""Build the Ethereum 10Y audience-profile page from the Luma guest CSV.

Usage: python3 proposals/build_audience.py /path/to/guests.csv

Reads ONLY approved guests, aggregates the survey columns, and writes a
PII-free static page (proposals/eth-11-audience.html) with inline SVG
donut charts + a top-50 organizations list. The source CSV contains PII
and is NOT committed to the repo — only the aggregated page is.
"""
import sys, csv, re, math
from collections import Counter

CSV = sys.argv[1] if len(sys.argv) > 1 else "guests.csv"
rows = [r for r in csv.DictReader(open(CSV, encoding="utf-8-sig"))
        if r["approval_status"] == "approved"]
N = len(rows)

# ---- palette (harmonized with the site: deep navy -> teal -> lime) ----
PAL = ["#052B42", "#0E3F5C", "#1C6E8C", "#2A9D8F", "#5BA66F",
       "#9BB344", "#E0FF4F", "#C9883E", "#B0493B", "#6E726B"]

def donut(title, pairs, note=""):
    """pairs: list of (label, count). Returns an SVG+legend HTML block."""
    total = sum(c for _, c in pairs) or 1
    cx = cy = 90; r = 78; rin = 46
    segs = []; a0 = -math.pi / 2
    for i, (label, c) in enumerate(pairs):
        frac = c / total
        a1 = a0 + frac * 2 * math.pi
        large = 1 if frac > 0.5 else 0
        x0, y0 = cx + r * math.cos(a0), cy + r * math.sin(a0)
        x1, y1 = cx + r * math.cos(a1), cy + r * math.sin(a1)
        xi1, yi1 = cx + rin * math.cos(a1), cy + rin * math.sin(a1)
        xi0, yi0 = cx + rin * math.cos(a0), cy + rin * math.sin(a0)
        col = PAL[i % len(PAL)]
        segs.append(
            f'<path d="M{x0:.2f},{y0:.2f} A{r},{r} 0 {large} 1 {x1:.2f},{y1:.2f} '
            f'L{xi1:.2f},{yi1:.2f} A{rin},{rin} 0 {large} 0 {xi0:.2f},{yi0:.2f} Z" '
            f'fill="{col}"><title>{label}: {c} ({frac*100:.0f}%)</title></path>')
        a0 = a1
    legend = "".join(
        f'<li><span class="sw" style="background:{PAL[i%len(PAL)]}"></span>'
        f'<span class="lb">{label}</span>'
        f'<span class="vl">{c} &middot; {c/total*100:.0f}%</span></li>'
        for i, (label, c) in enumerate(pairs))
    note = f'<p class="cnote">{note}</p>' if note else ""
    return (f'<figure class="chart"><figcaption>{title}</figcaption>'
            f'<div class="cwrap"><svg viewBox="0 0 180 180" role="img" '
            f'aria-label="{title}">{"".join(segs)}'
            f'<text x="90" y="86" class="ctot">{total}</text>'
            f'<text x="90" y="104" class="clbl">guests</text></svg>'
            f'<ul class="legend">{legend}</ul></div>{note}</figure>')

# ---- 1. Role ----
role_raw = Counter((r["What role describes you best?"].strip() or "Other") for r in rows)
role = [
    ("Founder", role_raw.get("Founder", 0)),
    ("Developer", role_raw.get("Developer", 0)),
    ("Investor", role_raw.get("Investor", 0)),
    ("Community", role_raw.get("Community Leader", 0) + role_raw.get("Community Member", 0)),
    ("Sales & Marketing", role_raw.get("Sales & BD", 0) + role_raw.get("Marketing", 0)),
    ("Student", role_raw.get("Student", 0)),
    ("Other", role_raw.get("Other", 0)),
]

# ---- 2. Tenure in Ethereum (of those who answered) ----
ten_raw = Counter(r["How long have you been in the Ethereum ecosystem?"].strip() for r in rows)
tenure = [(k, ten_raw.get(k, 0)) for k in ["6+ Years", "4-6 Years", "2-4 Years", "1-2 Years", "0-1 Years"]]
tenure_answered = sum(c for _, c in tenure)
exp4 = ten_raw.get("6+ Years", 0) + ten_raw.get("4-6 Years", 0)

# ---- 3. Geography ----
BAY = {"oakland", "berkeley", "palo alto", "san jose", "san mateo", "mountain view",
       "redwood city", "menlo park", "sunnyvale", "santa clara", "fremont", "emeryville",
       "south san francisco", "daly city", "alameda", "hayward", "cupertino", "bay area",
       "san francisco bay area", "richmond", "burlingame", "san bruno", "foster city",
       "millbrae", "san carlos", "walnut creek", "san rafael", "novato", "san leandro"}
US_HINT = (" ca", ", ca", "california", "new york", "nyc", "los angeles", "seattle", "austin",
           "boston", "chicago", "miami", "denver", "portland", "washington", "texas", "florida",
           "sacramento", "san diego", "united states", "usa", " us")
def geo(city):
    c = re.sub(r"\s+", " ", city.strip().lower())
    if not c: return "Not specified"
    if c in ("sf", "s.f.") or "san francisco" in c or c == "san fransisco": return "San Francisco"
    base = c.split(",")[0].strip()
    if base in BAY or any(b in c for b in BAY): return "Other Bay Area"
    if any(h in c for h in US_HINT): return "Other US"
    return "International"
geo_raw = Counter(geo(r["Which city are you usually based in?"]) for r in rows)
geography = [(k, geo_raw.get(k, 0)) for k in
             ["San Francisco", "Other Bay Area", "Other US", "International", "Not specified"]
             if geo_raw.get(k, 0) > 0]

# ---- 4. Contributions (free text -> themes, first match by priority) ----
THEMES = [
    ("Core protocol & research", ["eip", "protocol", "core", "ethereumjs", "geth", "client",
        "solidity", "smart contract", "cryptograph", "research", "zk", " zero knowledge",
        "rollup", "l2", "consensus", "evm", "node", "validator", "infrastructure", "infra"]),
    ("Building apps & products", ["built", "build", "founded", "found ", "launch", "startup",
        "product", "dapp", " app", "created", "develop", "engineer", "hack", "ethglobal",
        "shipping", "ship ", "wallet", "tooling"]),
    ("Investing & funding", ["invest", "fund", " vc", "capital", "grant", "backed", "angel",
        "portfolio", "lp ", "financ"]),
    ("Community, education & events", ["communit", "organiz", "meetup", "event", "educat",
        "teach", "content", "writ", "ambassador", "advocate", "podcast", "mentor", "host",
        "speaker", "translate", "moderator", "volunteer"]),
    ("Using & supporting", ["user", "bought", "buy ", "hold", "hodl", "stake", "staking",
        "use ", "using", "supporter", "support", "early", "adopt", "trade", "trading"]),
]
def theme(txt):
    t = " " + txt.strip().lower() + " "
    if len(t.strip()) < 2: return "Other / unspecified"
    for name, kws in THEMES:
        if any(k in t for k in kws): return name
    return "Other / unspecified"
contrib_raw = Counter(theme(r["How have you contributed to the Ethereum ecosystem?"]) for r in rows)
contrib = [(n, contrib_raw.get(n, 0)) for n, _ in THEMES] + \
          [("Other / unspecified", contrib_raw.get("Other / unspecified", 0))]
contrib = [(n, c) for n, c in contrib if c > 0]

# ---- 5. Top organizations (PII-safe: drop personal-name & generic values) ----
BAD = {"", "na", "n/a", "none", "self", "selfemployed", "freelance", "freelancer",
       "independent", "indie", "myself", "student", "stealth", "stealthstartup",
       "unemployed", "retired", "me", "personal", "individual", "solo"}
ALIAS = {  # merge obvious variants -> canonical key
    "stanforduniversity": "stanford", "storyprotocol": "story",
    "coinbasecom": "coinbase", "googlecom": "google",
}
DISPLAY = {  # canonical key -> clean display name
    "ethereumfoundation": "Ethereum Foundation", "stanford": "Stanford", "meta": "Meta",
    "dablclub": "Dabl", "manifoldmarkets": "Manifold Markets", "piggywallet": "Piggy Wallet",
    "alchemy": "Alchemy", "para": "Para", "sfsu": "SFSU", "metamask": "MetaMask",
    "litprotocol": "Lit Protocol", "zkm": "ZKM", "0x": "0x", "ey": "EY", "sfluv": "SFLuv",
    "etherealize": "Etherealize", "avaprotocol": "Ava Protocol",
    "fundingthecommons": "Funding the Commons", "sui": "Sui", "google": "Google",
    "phalanetwork": "Phala Network", "blockchainatberkeley": "Blockchain at Berkeley",
    "base": "Base", "coinbase": "Coinbase", "frontiertower": "Frontier Tower",
    "story": "Story Protocol", "polychaincapital": "Polychain Capital",
    "tensorblock": "TensorBlock", "standardcrypto": "Standard Crypto",
}
names = set()
for r in rows:
    fn = (r["first_name"] or "").strip().lower(); ln = (r["last_name"] or "").strip().lower()
    if fn and ln: names.add(re.sub(r"[^a-z0-9]", "", fn + ln))
org_cnt = Counter(); org_disp = {}
for r in rows:
    s = r["Current Organization"].strip()
    key = re.sub(r"[^a-z0-9]", "", s.lower())
    key = ALIAS.get(key, key)
    if not key or key in BAD or key in names:
        continue
    org_cnt[key] += 1
    org_disp.setdefault(key, Counter())[s] += 1
def disp_name(key):
    if key in DISPLAY: return DISPLAY[key]
    best = org_disp[key].most_common(1)[0][0]
    return best if best[:1].isupper() else best.title()
top = org_cnt.most_common(50)
top_items = "".join(
    f'<li><span class="rank">{i+1}</span><span class="co">{disp_name(k)}</span>'
    f'{"<span class=cc>"+str(v)+"</span>" if v>=2 else ""}</li>'
    for i, (k, v) in enumerate(top))

charts = (donut("By role", role) +
          donut("Time in the Ethereum ecosystem", tenure,
                f"Of the {tenure_answered} who answered &middot; "
                f"{exp4/tenure_answered*100:.0f}% have 4+ years.") +
          donut("Where they're based", geography) +
          donut("How they've contributed (self-described, categorized)", contrib))

CSS = """
*{box-sizing:border-box}body{margin:0;background:#FAFAF7;color:#0B0E0C;
font-family:"Hanken Grotesk",system-ui,sans-serif;line-height:1.6;-webkit-font-smoothing:antialiased}
.topbar{position:sticky;top:0;z-index:10;display:flex;align-items:center;justify-content:space-between;
gap:1rem;padding:.8rem clamp(1rem,4vw,2rem);background:rgba(5,43,66,.97);color:#fff;border-bottom:2px solid #E0FF4F}
.topbar .brand{display:flex;align-items:center;gap:.55rem;font-weight:800}
.topbar .dot{width:.55rem;height:.55rem;border-radius:50%;background:#E0FF4F;box-shadow:0 0 10px #E0FF4F}
.topbar a{color:#E0FF4F;font-family:"JetBrains Mono",monospace;font-size:.74rem;text-decoration:none;
border:1px solid rgba(224,255,79,.4);padding:.4rem .7rem;border-radius:3px}
.wrap{max-width:920px;margin:0 auto;padding:clamp(2rem,5vw,3.5rem) clamp(1.1rem,4vw,1.5rem) 4rem}
.kicker{font-family:"JetBrains Mono",monospace;font-size:.72rem;letter-spacing:.22em;text-transform:uppercase;color:#6E726B;margin:0 0 1rem}
h1{font-size:clamp(2rem,5vw,2.8rem);font-weight:800;color:#052B42;line-height:1.1;margin:.2rem 0 .5rem}
.lead{font-size:1.12rem;color:#0E3F5C;max-width:60ch}
h2{font-size:1.4rem;color:#052B42;margin:2.6rem 0 1rem;padding-top:1rem;border-top:2px solid #E0FF4F}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:1rem;margin:1.6rem 0}
.stat{background:#fff;border:1px solid #E7E8E4;border-radius:10px;padding:1rem 1.1rem}
.stat b{display:block;font-size:1.9rem;color:#052B42;line-height:1}
.stat span{font-size:.85rem;color:#6E726B}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(330px,1fr));gap:1.3rem}
.chart{margin:0;background:#fff;border:1px solid #E7E8E4;border-radius:12px;padding:1.2rem 1.3rem}
.chart figcaption{font-weight:700;color:#052B42;margin-bottom:.6rem}
.cwrap{display:flex;align-items:center;gap:1rem;flex-wrap:wrap}
.cwrap svg{width:150px;height:150px;flex:0 0 auto}
.ctot{text-anchor:middle;font-weight:800;font-size:24px;fill:#052B42}
.clbl{text-anchor:middle;font-size:9px;fill:#6E726B;letter-spacing:.1em;text-transform:uppercase}
.legend{list-style:none;margin:0;padding:0;flex:1 1 160px;font-size:.88rem}
.legend li{display:flex;align-items:center;gap:.5rem;padding:.18rem 0}
.legend .sw{width:.8rem;height:.8rem;border-radius:3px;flex:0 0 auto}
.legend .lb{flex:1}
.legend .vl{color:#6E726B;font-variant-numeric:tabular-nums;white-space:nowrap}
.cnote{font-size:.85rem;color:#6E726B;margin:.8rem 0 0;font-style:italic}
.colist{columns:2;column-gap:2rem;list-style:none;padding:0;margin:1rem 0}
@media(max-width:560px){.colist{columns:1}}
.colist li{display:flex;align-items:baseline;gap:.55rem;padding:.28rem 0;break-inside:avoid;border-bottom:1px solid #F0F1ED}
.colist .rank{font-family:"JetBrains Mono",monospace;font-size:.78rem;color:#9BA09A;min-width:1.6rem}
.colist .co{flex:1;color:#0B0E0C}
.colist .cc{font-family:"JetBrains Mono",monospace;font-size:.78rem;color:#fff;background:#1C6E8C;border-radius:10px;padding:.05rem .5rem}
.foot{color:#6E726B;font-size:.85rem;border-top:1px solid #E7E8E4;margin-top:2.5rem;padding-top:1.2rem}
a{color:#0E3F5C}
"""

HTML = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Ethereum Turns 11 — Last Year's Audience</title>
<meta name="description" content="Who attended the 2025 Ethereum 10th-birthday celebration in San Francisco: a data profile of {N} approved guests. Founder-heavy, deeply experienced, SF-based.">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Hanken+Grotesk:wght@400;500;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>{CSS}</style></head><body>
<div class="topbar"><span class="brand"><span class="dot"></span>Ethereum Turns 11</span>
<a href="eth-11-celebration.html">&larr; Back to the partner brief</a></div>
<main class="wrap">
<p class="kicker">Audience profile &middot; last year's event</p>
<h1>Who was in the room last year</h1>
<p class="lead">A profile of the <strong>{N} approved guests</strong> at the 2025 Ethereum
10th-birthday celebration in San Francisco. This is the audience a partner reaches at the 11th.
No personal data is shown — every figure below is an aggregate.</p>
<div class="stats">
<div class="stat"><b>{N}</b><span>approved guests</span></div>
<div class="stat"><b>{role[0][1]}</b><span>founders</span></div>
<div class="stat"><b>{exp4/tenure_answered*100:.0f}%</b><span>4+ years in Ethereum</span></div>
<div class="stat"><b>{(geo_raw.get('San Francisco',0)+geo_raw.get('Other Bay Area',0))/N*100:.0f}%</b><span>SF Bay Area</span></div>
</div>
<h2>The audience, by the numbers</h2>
<div class="grid">{charts}</div>
<h2>Top {len(top)} organizations represented</h2>
<p class="lead">Companies and institutions with the most approved guests. A badge shows where
more than one person attended from the same organization.</p>
<ol class="colist">{top_items}</ol>
<p class="foot">Source: approved guest list from the 2025 Ethereum 10th-birthday celebration
(Luma). {N} approved guests of {N} shown; invited / pending / declined registrations excluded.
Organization names are aggregated; personal names, emails, and contact details are never displayed.
Contribution categories are derived from free-text responses and are approximate.</p>
</main></body></html>"""

import pathlib
pathlib.Path("proposals/eth-11-audience.html").write_text(HTML, encoding="utf-8")
print(f"wrote proposals/eth-11-audience.html ({len(HTML)} bytes) from {N} approved guests")
print("role:", role)
print("tenure answered:", tenure_answered, "4+yr%:", round(exp4/tenure_answered*100))
print("geo:", dict(geo_raw))
print("contrib:", contrib)
print("orgs>=2:", sum(1 for _,v in top if v>=2), "top5:", [(disp_name(k),v) for k,v in top[:5]])
