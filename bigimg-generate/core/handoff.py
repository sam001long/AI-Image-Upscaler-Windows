from __future__ import annotations

import json
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path


def handoff_manifest_path() -> Path:
    root = Path(tempfile.gettempdir()) / "BigIMGGenerate"
    root.mkdir(parents=True, exist_ok=True)
    return root / "handoff.json"


def write_handoff_manifest(image_path: str | Path) -> Path:
    image = Path(image_path).resolve()
    manifest = handoff_manifest_path()
    payload = {
        "version": 1,
        "image_path": str(image),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source": "BigIMG Generate",
    }
    manifest.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def launch_bigimg(exe_path: str | Path, image_path: str | Path, mode: str) -> str:
    exe = Path(exe_path)
    image = Path(image_path).resolve()

    if not exe.exists():
        raise FileNotFoundError(f"找不到 BigIMG.exe：{exe}")
    if not image.exists():
        raise FileNotFoundError(f"找不到生成圖片：{image}")

    manifest = write_handoff_manifest(image)

    if mode == "CLI (--input)":
        subprocess.Popen([str(exe), "--input", str(image)])
        return f"已用 --input 啟動 BigIMG｜handoff: {manifest}"

    # Compatibility mode does not assume that the current BigIMG build
    # understands any command-line arguments.
    subprocess.Popen([str(exe)])
    subprocess.Popen(["explorer.exe", f"/select,{image}"])
    return f"已啟動 BigIMG，並在檔案總管選中圖片｜handoff: {manifest}"
