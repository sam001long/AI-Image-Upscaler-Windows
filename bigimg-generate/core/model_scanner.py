from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


SUPPORTED_EXTENSIONS = {".safetensors", ".ckpt"}


@dataclass(frozen=True)
class ModelInfo:
    path: Path
    family: str
    size_gb: float

    @property
    def label(self) -> str:
        return f"{self.path.name}  [{self.family}]  {self.size_gb:.2f} GB"


@dataclass(frozen=True)
class LoraInfo:
    path: Path
    size_mb: float

    @property
    def label(self) -> str:
        return f"{self.path.name}  {self.size_mb:.0f} MB"


@dataclass(frozen=True)
class VaeInfo:
    path: Path
    size_mb: float

    @property
    def label(self) -> str:
        return f"{self.path.name}  {self.size_mb:.0f} MB"


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
        results.append(ModelInfo(path.resolve(), _guess_family(path), size_gb))
    return sorted(results, key=lambda x: x.path.name.lower())


def scan_loras(root: str | Path) -> list[LoraInfo]:
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    results: list[LoraInfo] = []
    for path in root.rglob("*.safetensors"):
        if not path.is_file():
            continue
        try:
            size_mb = path.stat().st_size / (1024 ** 2)
        except OSError:
            size_mb = 0.0
        results.append(LoraInfo(path.resolve(), size_mb))
    return sorted(results, key=lambda x: x.path.name.lower())


def scan_vaes(root: str | Path) -> list[VaeInfo]:
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    results: list[VaeInfo] = []
    for path in root.rglob("*.safetensors"):
        if not path.is_file():
            continue
        try:
            size_mb = path.stat().st_size / (1024 ** 2)
        except OSError:
            size_mb = 0.0
        results.append(VaeInfo(path.resolve(), size_mb))
    return sorted(results, key=lambda x: x.path.name.lower())
