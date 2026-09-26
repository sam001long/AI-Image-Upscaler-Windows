import json
import os
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

CHANNEL_ID = "UCkePBCiTrqwbYoUx7ahynSQ"
FEED_URL = f"https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL_ID}"
OUT_JSON = "latest_video.json"
OUT_IMAGE = os.path.join("assets", "latest_youtube.jpg")
RAW_IMAGE_URL = "https://raw.githubusercontent.com/sam001long/AI-Image-Upscaler-Windows/main/assets/latest_youtube.jpg"

NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "yt": "http://www.youtube.com/xml/schemas/2015",
    "media": "http://search.yahoo.com/mrss/",
}

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()

raw = fetch(FEED_URL)
root = ET.fromstring(raw)
entry = root.find("atom:entry", NS)
if entry is None:
    raise SystemExit("No videos found in channel RSS feed")

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

os.makedirs("assets", exist_ok=True)
if thumb_url:
    image = fetch(thumb_url)
    with open(OUT_IMAGE, "wb") as f:
        f.write(image)

payload = {
    "ok": True,
    "channel_id": CHANNEL_ID,
    "video_id": video_id,
    "title": title,
    "url": video_url,
    "published": published,
    "thumbnail_url": RAW_IMAGE_URL if os.path.exists(OUT_IMAGE) else "",
    "updated_at": datetime.now(timezone.utc).isoformat(),
}

with open(OUT_JSON, "w", encoding="utf-8") as f:
    json.dump(payload, f, ensure_ascii=False, indent=2)
    f.write("\n")

print(json.dumps(payload, ensure_ascii=False))
