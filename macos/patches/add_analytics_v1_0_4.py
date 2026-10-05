from pathlib import Path

p = Path("macos/buildsrc/BigIMG_macOS_v1_0/app_mac.py")
s = p.read_text(encoding="utf-8")

replacements = [
    ('APP_VERSION = "macOS v1.0.3 攜帶版"', 'APP_VERSION = "macOS v1.0.4 攜帶版"'),
    ('NETWORK_USER_AGENT = "BigIMG-macOS/1.0.3"', 'NETWORK_USER_AGENT = "BigIMG-macOS/1.0.4"'),
    ('self.title("BigIMG JPG+PNG+SVG macOS v1.0.3 攜帶版")',
     'self.title("BigIMG JPG+PNG+SVG macOS v1.0.4 攜帶版")'),
    ('top, text="  JPG+PNG+SVG macOS v1.0.3 攜帶版",',
     'top, text="  JPG+PNG+SVG macOS v1.0.4 攜帶版",'),
]
for old, new in replacements:
    if old not in s:
        raise SystemExit(f"Missing expected version text: {old}")
    s = s.replace(old, new, 1)

helper_anchor = 'def fetch_latest_youtube_video(channel_id, timeout=4):\n'
helper = '''def send_analytics_event_async(endpoint, event, target=""):
    """Send a tiny anonymous usage event without blocking the UI."""
    endpoint = str(endpoint or "").strip()
    if not endpoint.startswith(("https://", "http://")):
        return

    payload = {
        "event": str(event or "")[:32],
        "app": APP_NAME,
        "platform": "macos",
        "version": APP_VERSION.split()[1] if len(APP_VERSION.split()) > 1 else APP_VERSION,
    }
    if target:
        payload["target"] = str(target)[:32]

    def worker():
        try:
            body = json.dumps(payload, ensure_ascii=True).encode("utf-8")
            req = urllib.request.Request(
                endpoint,
                data=body,
                headers={
                    "User-Agent": NETWORK_USER_AGENT,
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=3) as resp:
                resp.read(64)
        except Exception:
            pass

    threading.Thread(target=worker, daemon=True).start()

'''
if helper_anchor not in s:
    raise SystemExit("Missing analytics helper anchor")
s = s.replace(helper_anchor, helper + helper_anchor, 1)

old_state = '''        self.promo_data = DEFAULT_PROMO.copy()
        self.remote_version = None
        self.youtube_latest = None
        self.youtube_thumb_image = None

        self.build_ui()'''
new_state = '''        self.promo_data = DEFAULT_PROMO.copy()
        self.remote_version = None
        self.youtube_latest = None
        self.youtube_thumb_image = None
        self.analytics_enabled = False
        self.analytics_endpoint = ""
        self.analytics_start_sent = False

        self.build_ui()'''
if old_state not in s:
    raise SystemExit("Missing analytics state anchor")
s = s.replace(old_state, new_state, 1)

apply_anchor = '    def apply_promo(self, promo):\n'
track_method = '''    def track_analytics(self, event, target=""):
        if not self.analytics_enabled or not self.analytics_endpoint:
            return
        send_analytics_event_async(self.analytics_endpoint, event, target)

'''
if apply_anchor not in s:
    raise SystemExit("Missing apply_promo method")
s = s.replace(apply_anchor, track_method + apply_anchor, 1)

old_apply = '''    def apply_promo(self, promo):
        if not isinstance(promo, dict):
            promo = DEFAULT_PROMO

        self.promo_data = promo
        enabled = bool(promo.get("enabled", True))
'''
new_apply = '''    def apply_promo(self, promo):
        if not isinstance(promo, dict):
            promo = DEFAULT_PROMO

        self.promo_data = promo

        analytics = promo.get("analytics") if isinstance(promo.get("analytics"), dict) else {}
        self.analytics_enabled = bool(analytics.get("enabled", False))
        self.analytics_endpoint = str(analytics.get("endpoint") or "").strip()
        if self.analytics_enabled and self.analytics_endpoint and not self.analytics_start_sent:
            self.analytics_start_sent = True
            self.track_analytics("app_start")

        enabled = bool(promo.get("enabled", True))
'''
if old_apply not in s:
    raise SystemExit("Missing apply_promo analytics anchor")
s = s.replace(old_apply, new_apply, 1)

old_video = '''    def open_latest_video(self):
        url = str((self.youtube_latest or {}).get("url") or "")
        if url.startswith(("https://", "http://")):
            try:
                webbrowser.open(url)
'''
new_video = '''    def open_latest_video(self):
        url = str((self.youtube_latest or {}).get("url") or "")
        if url.startswith(("https://", "http://")):
            self.track_analytics("youtube_click", "video")
            try:
                webbrowser.open(url)
'''
if old_video not in s:
    raise SystemExit("Missing video click anchor")
s = s.replace(old_video, new_video, 1)

old_channel = '''    def open_promo_link(self):
        url = str((self.promo_data or {}).get("url") or "")
        if url.startswith(("https://", "http://")):
            try:
                webbrowser.open(url)
'''
new_channel = '''    def open_promo_link(self):
        url = str((self.promo_data or {}).get("url") or "")
        if url.startswith(("https://", "http://")):
            self.track_analytics("youtube_click", "channel")
            try:
                webbrowser.open(url)
'''
if old_channel not in s:
    raise SystemExit("Missing channel click anchor")
s = s.replace(old_channel, new_channel, 1)

p.write_text(s, encoding="utf-8")
print("Applied macOS v1.0.4 anonymous analytics")
