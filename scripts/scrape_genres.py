"""Scrape everynoise.com genre list into data/genres.json.

Run again whenever the snapshot should be refreshed:
    python scripts/scrape_genres.py
"""

import html
import json
import re
import urllib.request
from pathlib import Path

SOURCE = "https://everynoise.com/"
OUT = Path(__file__).resolve().parent.parent / "data" / "genres.json"

ENTRY = re.compile(
    r'preview_url="https://p\.scdn\.co/mp3-preview/([0-9a-f]{40})"'
    r'\s+class="genre scanme"[^>]*?'
    r'style="color: (#[0-9a-f]{6}); top: \d+px; left: \d+px; font-size: \d+%"'
    r'[^>]*?onclick="playx\(&quot;(\w+)&quot;,[^>]*?'
    r'title="e\.g\. (.*?)"'
    r'>(.*?)<a class=navlink'
)


def parse(page):
    """Rows are compact arrays, not objects: 6k+ entries, key names would cost ~200KB.

    Layout: [name, color, spotify_track_id, preview_hash, example_track]
    Two fields on the page are dropped because they are recoverable:
    the genre-page slug is the name stripped to [a-z0-9], and popularity is the row
    order itself, everynoise emits genres most-popular first.
    """
    rows = []
    for prev, color, track, example, name in ENTRY.findall(page):
        rows.append([
            html.unescape(name),
            color,
            track,
            prev,
            html.unescape(example),
        ])
    return rows


def main():
    req = urllib.request.Request(SOURCE, headers={"User-Agent": "Mozilla/5.0"})
    page = urllib.request.urlopen(req).read().decode("utf-8")
    rows = parse(page)
    if len(rows) < 5000:
        raise SystemExit(f"only parsed {len(rows)} genres, page layout probably changed")
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(rows, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"{len(rows)} genres -> {OUT} ({OUT.stat().st_size // 1024} KB)")


def demo():
    sample = (
        '<div preview_url="https://p.scdn.co/mp3-preview/' + 'a' * 40 + '" '
        'class="genre scanme" scan=true style="color: #ad8907; top: 4997px; left: 783px; '
        'font-size: 160%" role=button tabindex=0 onKeyDown="kb(event);" '
        'onclick="playx(&quot;1V6gIisPpYqgFeWbMLI0bA&quot;, &quot;pop&quot;, this);" '
        'title="e.g. Demi Lovato &quot;Heart Attack&quot;">pop'
        '<a class=navlink href="engenremap-pop.html" >&raquo;</a> </div>'
    )
    assert parse(sample) == [[
        "pop", "#ad8907", "1V6gIisPpYqgFeWbMLI0bA", "a" * 40,
        'Demi Lovato "Heart Attack"',
    ]], parse(sample)
    print("ok")


if __name__ == "__main__":
    import sys
    demo() if "--demo" in sys.argv else main()
