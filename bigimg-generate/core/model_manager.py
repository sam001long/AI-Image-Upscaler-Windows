from __future__ import annotations

import json
import shutil
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


APP_DIR = Path(__file__).resolve().parents[1]
CATALOG_PATH = APP_DIR / "config" / "model_catalog.json"
MODEL_ROOT = APP_DIR / "models"


@dataclass(frozen=True)
class CatalogModel:
    id: str
    name: str
    kind: str
    family: str
    filename: str
    relative_dir: str
    size_gb: float | None
    mirror_url: str | None
    source_url: str | None
    source_page: str | None
    license_note: str | None

    @property
    def destination(self) -> Path:
        return MODEL_ROOT / self.relative_dir / self.filename


def load_catalog() -> list[CatalogModel]:
    if not CATALOG_PATH.exists():
        return []
    data = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    items: list[CatalogModel] = []
    for raw in data.get("models", []):
        items.append(
            CatalogModel(
                id=str(raw["id"]),
                name=str(raw["name"]),
                kind=str(raw["kind"]),
                family=str(raw.get("family", "Unknown")),
                filename=str(raw["filename"]),
                relative_dir=str(raw["relative_dir"]),
                size_gb=float(raw["size_gb"]) if raw.get("size_gb") is not None else None,
                mirror_url=raw.get("mirror_url"),
                source_url=raw.get("source_url"),
                source_page=raw.get("source_page"),
                license_note=raw.get("license_note"),
            )
        )
    return items


def import_local_file(source: str | Path, relative_dir: str) -> Path:
    src = Path(source).resolve()
    if not src.is_file():
        raise FileNotFoundError(src)
    dest_dir = MODEL_ROOT / relative_dir
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / src.name
    if src != dest.resolve():
        shutil.copy2(src, dest)
    return dest


def download_model(
    model: CatalogModel,
    prefer_mirror: bool = True,
    progress: Callable[[int, int | None], None] | None = None,
) -> Path:
    url = None
    if prefer_mirror and model.mirror_url:
        url = model.mirror_url
    elif model.source_url:
        url = model.source_url
    elif model.mirror_url:
        url = model.mirror_url

    if not url:
        raise ValueError("這個模型尚未設定可直接下載的網址。")

    dest = model.destination
    dest.parent.mkdir(parents=True, exist_ok=True)
    partial = dest.with_suffix(dest.suffix + ".part")

    req = urllib.request.Request(url, headers={"User-Agent": "BigIMG-Generate/1.0"})
    with urllib.request.urlopen(req, timeout=60) as response, partial.open("wb") as out:
        total = response.headers.get("Content-Length")
        total_bytes = int(total) if total and total.isdigit() else None
        done = 0
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            out.write(chunk)
            done += len(chunk)
            if progress:
                progress(done, total_bytes)

    partial.replace(dest)
    return dest
