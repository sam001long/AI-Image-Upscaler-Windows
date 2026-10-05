from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


SUPPORTED_EXTENSIONS = {".safetensors", ".ckpt"}


@dataclass(frozen=True)
class ModelInfo:
    path: Path
    family: str
    size_gb: float

    @property
    def label(self) -> str:
        return f"{self.path.name}  [{self.family}]  {self.size_gb:.2f} GB"


def _guess_family(path: Path) -> str:
    text = str(path).lower()
    name = path.name.lower()

    if "sdxl" in text or "xl" in name:
        return "SDXL"
    if "sd15" in text or "sd1.5" in text or "1-5" in name or "v15" in name:
        return "SD1.5"
    return "Unknown"


def scan_models(root: str | Path) -> list[ModelInfo]:
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)

    results: list[ModelInfo] = []
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        try:
            size_gb = path.stat().st_size / (1024 ** 3)
        except OSError:
            size_gb = 0.0
        results.append(
            ModelInfo(
                path=path.resolve(),
                family=_guess_family(path),
                size_gb=size_gb,
            )
        )

    return sorted(results, key=lambda x: x.path.name.lower())
