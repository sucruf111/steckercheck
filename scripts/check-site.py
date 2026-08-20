#!/usr/bin/env python3
"""Invariants for the four public steckercheck.de URLs. Not a public page."""

from __future__ import annotations

import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AWIN = "https://www.awin1.com/cread.php?s=4866441&v=68786&q=568335&r=3038929"
BANNED = (
    "Link folgt",
    "Entwurf",
    "Platzhalter",
    "Als Nächstes",
    "keine Tracking-Links",
)
BANNED_BRANDS = ("heimwallbox", "Solakon", "HD24")
PUBLIC = (
    "index.html",
    "800-watt-2000-wp.html",
    "schuko-oder-wieland.html",
    "balkonkraftwerk-kaufen.html",
)
LEGAL = ("impressum.html", "datenschutz.html")
KNOWN_HTML = PUBLIC + LEGAL + ("404.html", "google8fd2b20152f4b794.html")
TITLE_800 = "Steckersolargerät 800 VA und 2000 Wp laut Bundesnetzagentur — steckercheck.de"
H1_800 = "Steckersolargerät: 800 VA und 2000 Wp"
CANONICALS = {
    "index.html": "https://steckercheck.de/",
    "800-watt-2000-wp.html": "https://steckercheck.de/800-watt-2000-wp",
    "schuko-oder-wieland.html": "https://steckercheck.de/schuko-oder-wieland",
    "balkonkraftwerk-kaufen.html": "https://steckercheck.de/balkonkraftwerk-kaufen",
    "impressum.html": "https://steckercheck.de/impressum",
    "datenschutz.html": "https://steckercheck.de/datenschutz",
}

errors: list[str] = []


def fail(msg: str) -> None:
    errors.append(msg)


def read(name: str) -> str:
    return (ROOT / name).read_text(encoding="utf-8")


def one(pattern: str, text: str, flags: int = 0) -> str | None:
    matches = re.findall(pattern, text, flags)
    if len(matches) != 1:
        return None
    return matches[0]


def strip_tags(html: str) -> str:
    return re.sub(r"<[^>]+>", "", html).strip()


def inline_css(html: str) -> str:
    match = re.search(r"<style>\n(.*)\n  </style>", html, re.S)
    if not match:
        fail("missing inline <style> block")
        return ""
    return match.group(1).rstrip("\n") + "\n"


html_files = sorted(p.name for p in ROOT.glob("*.html"))
if tuple(html_files) != tuple(sorted(KNOWN_HTML)):
    fail(f"unexpected HTML set: {html_files}")

css = (ROOT / "site.css").read_text(encoding="utf-8")
for name in PUBLIC:
    text = read(name)
    if inline_css(text) != css:
        fail(f"{name}: inline CSS does not match site.css")

    title = one(r"<title>(.*?)</title>", text, re.S)
    h1 = one(r"<h1[^>]*>(.*?)</h1>", text, re.S)
    if not title:
        fail(f"{name}: expected exactly one <title>")
    if not h1:
        fail(f"{name}: expected exactly one <h1>")
    if name == "800-watt-2000-wp.html":
        if title != TITLE_800:
            fail(f"800 page title drifted: {title!r}")
        if h1 and strip_tags(h1) != H1_800:
            fail(f"800 page H1 drifted: {strip_tags(h1)!r}")
        lede = one(
            r'<header class="page-hero">.*?<p class="lede">(.*?)</p>',
            text,
            re.S,
        )
        if not lede or "Bundesnetzagentur" not in lede or "EEG" not in lede:
            fail("800 page lede must name Bundesnetzagentur and EEG")
        if lede and lede.count("Bundesnetzagentur") != 1:
            fail("800 page lede should name Bundesnetzagentur once")
        kurz = re.search(r"<strong>Die Kurzantwort:</strong>(.{0,280})", text, re.S)
        if kurz and "Bundesnetzagentur" in kurz.group(1):
            fail("800 page Kurzantwort repeats Bundesnetzagentur (stuffing)")
        if 'href="/schuko-oder-wieland"' not in text.split("<footer", 1)[0]:
            fail("800 page body must link to /schuko-oder-wieland")

    canonical = one(r'<link rel="canonical" href="([^"]+)">', text)
    expected = CANONICALS[name]
    if canonical != expected:
        fail(f"{name}: canonical {canonical!r} != {expected!r}")
    if canonical and (canonical.endswith(".html") or (canonical.endswith("/") and canonical != "https://steckercheck.de/")):
        fail(f"{name}: canonical is not the extensionless apex URL")

    og = one(r'<meta property="og:url" content="([^"]+)">', text)
    if og and og != expected:
        fail(f"{name}: og:url {og!r} != {expected!r}")

    if re.search(r'href="/[^"]+\.html"', text):
        fail(f"{name}: internal .html href")

    for phrase in BANNED:
        if phrase in text:
            fail(f"{name}: banned phrase {phrase!r}")
    for brand in BANNED_BRANDS:
        if brand.lower() in text.lower():
            fail(f"{name}: banned brand {brand!r}")

    awin_count = text.count(AWIN.replace("&", "&amp;"))
    if name in ("index.html", "balkonkraftwerk-kaufen.html"):
        if awin_count != 1:
            fail(f"{name}: expected one Zendure Awin URL, found {awin_count}")
        if 'rel="sponsored nofollow"' not in text:
            fail(f"{name}: Awin link must stay rel=sponsored nofollow")
    elif awin_count:
        fail(f"{name}: unexpected Awin URL")

    for block in re.findall(
        r'<script type="application/ld\+json">\s*(.*?)\s*</script>', text, re.S
    ):
        try:
            data = json.loads(block)
        except json.JSONDecodeError as exc:
            fail(f"{name}: JSON-LD {exc}")
            continue
        dumped = json.dumps(data)
        if ".html" in dumped and "gesetze-im-internet" not in dumped:
            if re.search(r"steckercheck\.de/[^\"\\]+\.html", dumped):
                fail(f"{name}: JSON-LD points at a .html site URL")

for name in LEGAL:
    text = read(name)
    canonical = one(r'<link rel="canonical" href="([^"]+)">', text)
    if canonical != CANONICALS[name]:
        fail(f"{name}: canonical {canonical!r} != {CANONICALS[name]!r}")
    if "noindex" not in text:
        fail(f"{name}: must stay noindex")
    if "AC Beauty to Customer UG (haftungsbeschränkt)" not in text:
        fail(f"{name}: company name drifted")
    for phrase in BANNED:
        if phrase in text:
            fail(f"{name}: banned phrase {phrase!r}")
    for brand in BANNED_BRANDS:
        if brand.lower() in text.lower():
            fail(f"{name}: banned brand {brand!r}")

sitemap = ET.parse(ROOT / "sitemap.xml")
ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
locs = [el.text for el in sitemap.findall(".//sm:loc", ns)]
expected_locs = [
    "https://steckercheck.de/",
    "https://steckercheck.de/800-watt-2000-wp",
    "https://steckercheck.de/balkonkraftwerk-kaufen",
    "https://steckercheck.de/schuko-oder-wieland",
]
if locs != expected_locs:
    fail(f"sitemap locs drifted: {locs}")

openapi = json.loads(read("openapi.json"))
if openapi["info"]["version"] != "2026-08-20":
    fail("openapi.json version should match the 800-page edit day")
if openapi["paths"]["/800-watt-2000-wp"]["get"]["summary"] != "Steckersolargerät 800 VA und 2000 Wp laut Bundesnetzagentur":
    fail("openapi.json 800-page summary drifted")

llms = read("llms.txt")
if "Steckersolargerät 800 VA und 2000 Wp laut Bundesnetzagentur" not in llms:
    fail("llms.txt must use the live 800-page title")
if ".html" in llms:
    fail("llms.txt must not list .html URLs")

redirects = read("_redirects")
for path, dest in (
    ("/800-watt-2000-wp.html", "https://steckercheck.de/800-watt-2000-wp"),
    ("/schuko-oder-wieland.html", "https://steckercheck.de/schuko-oder-wieland"),
    ("/balkonkraftwerk-kaufen.html", "https://steckercheck.de/balkonkraftwerk-kaufen"),
    ("/index.html", "https://steckercheck.de/"),
    ("/impressum.html", "https://steckercheck.de/impressum"),
    ("/datenschutz.html", "https://steckercheck.de/datenschutz"),
):
    if f"{path} " not in redirects or dest not in redirects:
        fail(f"_redirects missing 301 {path} → {dest}")

if errors:
    print("check-site: FAIL")
    for item in errors:
        print(f" - {item}")
    sys.exit(1)

print("check-site: OK")
print(" - 4 public pages, no fifth content HTML")
print(" - 800 title/H1 kept; lede names BNetzA + EEG once")
print(" - extensionless canonicals; leftover .html 301s declared")
print(" - Zendure Awin only on / and /balkonkraftwerk-kaufen")
print(" - no banned process phrases or other-brand links")
