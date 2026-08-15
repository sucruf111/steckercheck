# steckercheck.de

Static site for https://steckercheck.de/ — Steckersolar 800 VA / 2000 Wp, sourced from EEG, BNetzA, MaStR.

No analytics, no Awin JS, no Google Fonts CDN. IBM Plex Sans and Source Serif 4 are self-hosted (SIL OFL) in `/fonts`. Illustrations are hand-built SVGs in `/img` (only `og.jpg` and `apple-touch-icon.png` are raster). Partner links only when a program has accepted; they belong on `balkonkraftwerk-kaufen.html` and must be labelled **Werbung**.

Public pages: `index.html`, `800-watt-2000-wp.html`, `balkonkraftwerk-kaufen.html`. Legal: `impressum.html`, `datenschutz.html` (noindex). Agents: `llms.txt`, `llms-full.txt`. Cloudflare: `_headers`, `404.html`.

Deploy: zip the public files and replace-deploy the existing Cloudflare Pages project `steckercheck`.
