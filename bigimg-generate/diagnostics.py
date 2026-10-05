from __future__ import annotations

import argparse
import platform
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true")
    args = parser.parse_args()

    print("BigIMG Generate diagnostics")
    print("--------------------------")
    print("Python:", sys.version.split()[0])
    print("Platform:", platform.platform())

    try:
        import torch
        print("PyTorch:", torch.__version__)
        print("CUDA available:", torch.cuda.is_available())
        if torch.cuda.is_available():
            print("CUDA runtime:", torch.version.cuda)
            print("GPU:", torch.cuda.get_device_name(0))
            props = torch.cuda.get_device_properties(0)
            print("VRAM GB:", round(props.total_memory / (1024 ** 3), 2))
        else:
            print("GPU mode: CPU fallback")
    except Exception as exc:
        print("[ERROR] PyTorch import failed:", exc)
        return 1

    if args.quick:
        return 0

    checks = {
        "diffusers": "diffusers",
        "transformers": "transformers",
        "accelerate": "accelerate",
        "safetensors": "safetensors",
        "Pillow": "PIL",
        "controlnet_aux": "controlnet_aux",
    }

    for label, module in checks.items():
        try:
            imported = __import__(module)
            version = getattr(imported, "__version__", "OK")
            print(f"{label}: {version}")
        except Exception as exc:
            print(f"[ERROR] {label} import failed: {exc}")
            return 1

    model_root = Path(__file__).resolve().parent / "models" / "checkpoints"
    models = [
        p for p in model_root.rglob("*")
        if p.is_file() and p.suffix.lower() in {".safetensors", ".ckpt"}
    ]
    print("Local checkpoints:", len(models))
    if not models:
        print("[INFO] No local checkpoint yet. Put one under models/checkpoints/sd15 or sdxl.")

    print("Environment check: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
