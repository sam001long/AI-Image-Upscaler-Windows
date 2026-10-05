from pathlib import Path

p = Path("macos/buildsrc/BigIMG_macOS_v1_0/app_mac.py")
s = p.read_text(encoding="utf-8")

for old, new in [
    ('APP_VERSION = "macOS v1.0.4 攜帶版"', 'APP_VERSION = "macOS v1.0.5 攜帶版"'),
    ('NETWORK_USER_AGENT = "BigIMG-macOS/1.0.4"', 'NETWORK_USER_AGENT = "BigIMG-macOS/1.0.5"'),
    ('self.title("BigIMG JPG+PNG+SVG macOS v1.0.4 攜帶版")',
     'self.title("BigIMG JPG+PNG+SVG macOS v1.0.5 攜帶版")'),
    ('top, text="  JPG+PNG+SVG macOS v1.0.4 攜帶版",',
     'top, text="  JPG+PNG+SVG macOS v1.0.5 攜帶版",'),
]:
    if old not in s:
        raise SystemExit(f"Missing expected version text: {old}")
    s = s.replace(old, new, 1)

if "import platform\n" not in s:
    anchor = "import sys\n"
    if anchor not in s:
        raise SystemExit("Missing import anchor")
    s = s.replace(anchor, anchor + "import platform\n", 1)

old = '''def send_analytics_event_async(endpoint, event, target=""):
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

new = '''ANALYTICS_HARDWARE_CACHE = None

def analytics_hardware_profile():
    """Coarse anonymous hardware only; no device IDs, usernames, or serials."""
    global ANALYTICS_HARDWARE_CACHE
    if isinstance(ANALYTICS_HARDWARE_CACHE, dict):
        return ANALYTICS_HARDWARE_CACHE.copy()

    profile = {
        "arch": str(platform.machine() or "unknown")[:24],
        "cpu_cores": int(os.cpu_count() or 0),
        "ram_gb": 0,
        "gpu": "unknown",
        "vram_gb": 0,
    }

    try:
        p_mem = subprocess.run(
            ["sysctl", "-n", "hw.memsize"],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            text=True, timeout=3
        )
        raw = int((p_mem.stdout or "0").strip() or 0)
        profile["ram_gb"] = int(round(raw / (1024 ** 3)))
    except Exception:
        pass

    try:
        p_gpu = subprocess.run(
            ["system_profiler", "SPDisplaysDataType", "-json"],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            text=True, encoding="utf-8", errors="replace", timeout=8
        )
        data = json.loads(p_gpu.stdout or "{}")
        displays = data.get("SPDisplaysDataType") or []
        if displays:
            first = displays[0] if isinstance(displays[0], dict) else {}
            profile["gpu"] = str(
                first.get("sppci_model")
                or first.get("_name")
                or first.get("spdisplays_chipset-model")
                or "unknown"
            )[:96]
    except Exception:
        pass

    ANALYTICS_HARDWARE_CACHE = profile.copy()
    return profile

def send_analytics_event_async(endpoint, event, target=""):
    """Send a tiny anonymous usage event without blocking the UI."""
    endpoint = str(endpoint or "").strip()
    if not endpoint.startswith(("https://", "http://")):
        return

    def worker():
        try:
            payload = {
                "event": str(event or "")[:32],
                "app": APP_NAME,
                "platform": "macos",
                "version": APP_VERSION.split()[1] if len(APP_VERSION.split()) > 1 else APP_VERSION,
            }
            payload.update(analytics_hardware_profile())
            if target:
                payload["target"] = str(target)[:32]

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

if old not in s:
    raise SystemExit("Missing v1.0.4 analytics function")
s = s.replace(old, new, 1)

p.write_text(s, encoding="utf-8")
print("Applied macOS v1.0.5 detailed anonymous analytics")
