"""Save only a valid stats card, keeping the last good SVG on upstream failure."""

from pathlib import Path
import re
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET


URL = (
    "https://github-readme-stats-snf0866s-projects.vercel.app/api"
    "?username=shuhei0866&show_icons=true&count_private=true"
    "&hide_border=true&theme=tokyonight&card_width=495"
)
DESTINATION = Path(__file__).resolve().parents[1] / "profile/stats.svg"
SVG = "{http://www.w3.org/2000/svg}"


def validate_card(data):
    root = ET.fromstring(data)
    if root.tag != SVG + "svg":
        raise ValueError("Response is not an SVG")
    # Upstream returns HTTP 200 even for error cards. Check actual stats fields.
    fields = {node.get("data-testid"): node for node in root.iter()}
    if "message" in fields:
        raise ValueError("Upstream returned an error card")
    for name in ("stars", "commits", "prs", "issues", "contribs"):
        node = fields.get(name)
        value = "" if node is None else "".join(node.itertext()).strip()
        if not re.fullmatch(r"\d[\d,]*(?:\.\d+)?[kmb]?", value, re.IGNORECASE):
            raise ValueError(f"Missing or invalid stats field: {name}")


def update_card(destination=DESTINATION):
    for attempt in range(3):
        try:
            with urllib.request.urlopen(URL, timeout=30) as response:
                data = response.read(128 * 1024 + 1)
            if len(data) > 128 * 1024:
                raise ValueError("Stats card is unexpectedly large")
            validate_card(data)
            data = b"\n".join(line.rstrip() for line in data.strip().splitlines()) + b"\n"
            break
        except (urllib.error.URLError, TimeoutError, ValueError, ET.ParseError):
            if attempt == 2:
                raise
            time.sleep(2)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(".svg.tmp")
    temporary.write_bytes(data)
    temporary.replace(destination)


if __name__ == "__main__":
    update_card()
    print("Saved validated stats card to profile/stats.svg")
