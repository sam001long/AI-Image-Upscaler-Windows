import base64
import json
import binascii
import re
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

CHANNEL_ID = "UCkePBCiTrqwbYoUx7ahynSQ"
FEED_URL = f"https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL_ID}"
OUT_JSON = "latest_video.json"

NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "yt": "http://www.youtube.com/xml/schemas/2015",
    "media": "http://search.yahoo.com/mrss/",
}

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()

def has_valid_cache():
    try:
        cached = json.loads(Path(OUT_JSON).read_text(encoding="utf-8"))
        if not isinstance(cached, dict):
            return False
        required = ("video_id", "title", "url", "published",
                    "thumbnail_base64", "updated_at")
        if cached.get("ok") is not True or cached.get("channel_id") != CHANNEL_ID:
            return False
        if any(not isinstance(cached.get(key), str) or not cached[key].strip()
               for key in required):
            return False
        if not re.fullmatch(r"[A-Za-z0-9_-]{11}", cached["video_id"]):
            return False
        if cached["url"] != f'https://www.youtube.com/watch?v={cached["video_id"]}':
            return False
        for key in ("published", "updated_at"):
            if datetime.fromisoformat(cached[key]).tzinfo is None:
                return False
        return bool(base64.b64decode(cached["thumbnail_base64"], validate=True))
    except (OSError, ValueError, TypeError, binascii.Error):
        return False


def fetch_latest_entry():
    last_error = ""
    for attempt, delay in enumerate((0, 5, 15), start=1):
        if delay:
            time.sleep(delay)
        try:
            root = ET.fromstring(fetch(FEED_URL))
            entry = root.find("atom:entry", NS)
            if entry is None:
                raise ValueError("No videos found in channel RSS feed")
            video_id = entry.findtext("yt:videoId", default="", namespaces=NS).strip()
            published = entry.findtext("atom:published", default="", namespaces=NS).strip()
            if not re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id):
                raise ValueError("Invalid RSS video ID")
            if not published or datetime.fromisoformat(published).tzinfo is None:
                raise ValueError("Invalid RSS publication timestamp")
            return entry
        except (urllib.error.URLError, OSError, ET.ParseError, ValueError) as exc:
            last_error = str(exc).replace("\n", " ").replace("\r", " ")
            print(f"RSS attempt {attempt}/3 failed: {last_error}")

    if has_valid_cache():
        print("::warning::YouTube RSS failed after 3 attempts; keeping existing cache")
        raise SystemExit(0)
    raise SystemExit(f"YouTube RSS failed and no valid cache is available: {last_error}")


entry = fetch_latest_entry()

title = entry.findtext("atom:title", default="最新影片", namespaces=NS).strip()
video_id = entry.findtext("yt:videoId", default="", namespaces=NS).strip()
published = entry.findtext("atom:published", default="", namespaces=NS).strip()

link = entry.find("atom:link[@rel='alternate']", NS)
video_url = link.attrib.get("href", "") if link is not None else ""
if not video_url and video_id:
    video_url = f"https://www.youtube.com/watch?v={video_id}"

thumb_url = ""
group = entry.find("media:group", NS)
if group is not None:
    thumb = group.find("media:thumbnail", NS)
    if thumb is not None:
        thumb_url = thumb.attrib.get("url", "")
if not thumb_url and video_id:
    thumb_url = f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"

thumbnail_base64 = ""
if thumb_url:
    image = fetch(thumb_url)
    thumbnail_base64 = base64.b64encode(image).decode("ascii")

payload = {
    "ok": True,
    "channel_id": CHANNEL_ID,
    "video_id": video_id,
    "title": title,
    "url": video_url,
    "published": published,
    "thumbnail_base64": thumbnail_base64,
    "updated_at": datetime.now(timezone.utc).isoformat(),
}

with open(OUT_JSON, "w", encoding="utf-8") as f:
    json.dump(payload, f, ensure_ascii=False, indent=2)
    f.write("\n")

print(json.dumps({
    "ok": payload["ok"],
    "video_id": payload["video_id"],
    "title": payload["title"],
    "updated_at": payload["updated_at"],
}, ensure_ascii=False))
