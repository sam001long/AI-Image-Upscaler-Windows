import base64
import json
import re
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

PROMO_JSON = Path("promo.json")
OUT_JSON = Path("latest_video.json")


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def load_selected_video():
    promo = json.loads(PROMO_JSON.read_text(encoding="utf-8"))
    youtube = promo.get("youtube") or {}

    video_id = str(youtube.get("video_id") or "").strip()
    title = str(youtube.get("title") or "").strip()
    url = str(youtube.get("url") or "").strip()

    if youtube.get("source") != "manual":
        raise SystemExit('promo.json youtube.source must be "manual"')
    if not re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id):
        raise SystemExit("Invalid YouTube video_id")
    if not title:
        raise SystemExit("Missing YouTube title")

    expected = f"https://www.youtube.com/watch?v={video_id}"
    if not url:
        url = expected
    if url != expected:
        raise SystemExit(f"YouTube url must be {expected}")

    return video_id, title, url


def fetch_thumbnail(video_id):
    for thumb_url in (
        f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg",
        f"https://i.ytimg.com/vi/{video_id}/mqdefault.jpg",
    ):
        for delay in (0, 3, 8):
            if delay:
                time.sleep(delay)
            try:
                image = fetch(thumb_url)
                if image:
                    return base64.b64encode(image).decode("ascii")
            except (urllib.error.URLError, OSError) as exc:
                print(f"Thumbnail fetch failed: {exc}")
    return ""


video_id, title, video_url = load_selected_video()
now = datetime.now(timezone.utc).isoformat()

payload = {
    "ok": True,
    "source": "manual",
    "channel_id": "UCkePBCiTrqwbYoUx7ahynSQ",
    "video_id": video_id,
    "title": title,
    "url": video_url,
    "published": now,
    "thumbnail_base64": fetch_thumbnail(video_id),
    "updated_at": now,
}

OUT_JSON.write_text(
    json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)

print(json.dumps({
    "ok": True,
    "source": "manual",
    "video_id": video_id,
    "title": title,
    "updated_at": now,
}, ensure_ascii=False))
