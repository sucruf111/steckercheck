# steckercheck.de

Static site for https://steckercheck.de/ — Steckersolar 800 VA / 2000 Wp, sourced from EEG, BNetzA, MaStR.

No analytics, no Awin JS, no Google Fonts CDN. IBM Plex Sans and Source Serif 4 are self-hosted (SIL OFL) in `/fonts`. Illustrations are hand-built SVGs in `/img` (only `og.jpg` and `apple-touch-icon.png` are raster). Partner links are plain `<a href>` to the Awin deep link, never a script, and every one of them sits in a block labelled **Werbung**. They currently run on `index.html`, `800-watt-2000-wp.html` and `balkonkraftwerk-kaufen.html`.

Public pages: `index.html`, `800-watt-2000-wp.html`, `schuko-oder-wieland.html`, `balkonkraftwerk-kaufen.html`. Legal: `impressum.html`, `datenschutz.html` (noindex). Crawlers: `robots.txt`, `sitemap.xml`. Agents: `llms.txt`, `llms-full.txt`, `openapi.json`. Cloudflare: `_headers`, `_redirects`, `404.html`.

Deploy: zip the public files and replace-deploy the existing Cloudflare Pages project `steckercheck`. There is no build step.

## URLs

Public URLs are extensionless and carry no trailing slash: `/800-watt-2000-wp`, not `/800-watt-2000-wp.html`. `rel=canonical`, `og:url`, the hreflang links, `sitemap.xml`, `llms.txt` and `openapi.json` all use that form, and so does every internal link. `_redirects` answers 301 for the `.html` paths.

## Open item: www must be redirected in the Cloudflare dashboard

`https://www.steckercheck.de/` answers 200 with the same HTML as the apex host. Every page is therefore reachable under two hostnames, and only `rel=canonical` tells search engines which one counts.

This cannot be fixed from the repository. Cloudflare Pages matches `_redirects` rules on the path alone and [lists domain-level redirects as unsupported](https://developers.cloudflare.com/pages/configuration/redirects/#advanced-redirects), and `_headers` cannot redirect at all. One Single Redirect rule closes it:

1. Cloudflare dashboard → the `steckercheck.de` zone → **Rules** → **Redirect Rules** → **Create rule**
2. If: `http.host eq "www.steckercheck.de"`
3. Then: **Dynamic** redirect, URL expression `concat("https://steckercheck.de", http.request.uri.path)`
4. Status **301**, **Preserve query string** on

Verify with `curl -sI https://www.steckercheck.de/schuko-oder-wieland`, which should answer `301` with `location: https://steckercheck.de/schuko-oder-wieland`.
