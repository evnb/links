#!/usr/bin/env python3
"""
generate.py — reads links.yaml, fetches OG metadata for each URL,
and generates a dist/ folder of redirect pages with proper OG tags.
"""

import os
import shutil
import yaml
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; LinkShortener/1.0)"
}

TIMEOUT = 10


def fetch_og(url: str) -> dict:
    """Fetch a URL and extract OG/meta tags. Returns a dict with title, description, image."""
    og = {"title": None, "description": None, "image": None}
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "lxml")

        def get_meta(prop):
            # Try og: property first, then name= fallback
            tag = soup.find("meta", property=f"og:{prop}") or \
                  soup.find("meta", attrs={"name": f"og:{prop}"}) or \
                  soup.find("meta", attrs={"name": prop})
            return tag["content"].strip() if tag and tag.get("content") else None

        og["title"] = get_meta("title") or (soup.title.string.strip() if soup.title else None)
        og["description"] = get_meta("description")
        og["image"] = get_meta("image")

        print(f"  title:       {og['title']}")
        print(f"  description: {og['description']}")
        print(f"  image:       {og['image']}")
    except Exception as e:
        print(f"  ⚠️  Could not fetch OG data: {e}")
    return og


def escape(s: str) -> str:
    if not s:
        return ""
    return s.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;")


def make_redirect_page(url: str, og: dict) -> str:
    title = escape(og["title"]) or "Redirecting…"
    description = escape(og["description"]) or ""
    image = escape(og["image"]) or ""

    og_tags = f'  <meta property="og:title" content="{title}">\n' if title else ""
    og_tags += f'  <meta property="og:description" content="{description}">\n' if description else ""
    og_tags += f'  <meta property="og:image" content="{image}">\n' if image else ""
    og_tags += f'  <meta property="og:url" content="{escape(url)}">\n'
    og_tags += f'  <meta name="twitter:card" content="summary_large_image">\n' if image else \
               f'  <meta name="twitter:card" content="summary">\n'
    og_tags += f'  <meta name="twitter:title" content="{title}">\n' if title else ""
    og_tags += f'  <meta name="twitter:description" content="{description}">\n' if description else ""
    og_tags += f'  <meta name="twitter:image" content="{image}">\n' if image else ""

    return f"""<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8">
    <title>{title}</title>
    <meta http-equiv="refresh" content="0; url={escape(url)}">
    <link rel="canonical" href="{escape(url)}">
{og_tags}  </head>
  <body>
    <p>Redirecting to <a href="{escape(url)}">{escape(url)}</a>…</p>
    <script>window.location.replace("{escape(url)}");</script>
  </body>
</html>
"""


def main():
    with open("links.yaml") as f:
        links = yaml.safe_load(f)

    if os.path.exists("dist"):
        shutil.rmtree("dist")
    os.makedirs("dist")

    # Copy root index if present
    if os.path.exists("index.html"):
        shutil.copy("index.html", "dist/index.html")
    else:
        with open("dist/index.html", "w") as f:
            f.write("<html><body>Nothing here.</body></html>")

    for key, url in links.items():
        print(f"\n🔗 /{key} → {url}")
        og = fetch_og(url)
        html = make_redirect_page(url, og)
        os.makedirs(f"dist/{key}", exist_ok=True)
        with open(f"dist/{key}/index.html", "w") as f:
            f.write(html)
        print(f"  ✓ wrote dist/{key}/index.html")

    print(f"\n✅ Done! Generated {len(links)} shortlink(s).")


if __name__ == "__main__":
    main()
