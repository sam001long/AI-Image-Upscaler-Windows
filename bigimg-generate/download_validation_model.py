from __future__ import annotations

import shutil
import sys
from pathlib import Path

from huggingface_hub import hf_hub_download, snapshot_download


REPO_ID = "stable-diffusion-v1-5/stable-diffusion-v1-5"
MODEL_FILE = "v1-5-pruned-emaonly.safetensors"
APP_DIR = Path(__file__).resolve().parent
MODEL_DIR = APP_DIR / "models" / "checkpoints" / "sd15"
CONFIG_DIR = APP_DIR / "models" / "configs" / "sd15-v1-5"


def main() -> int:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    target = MODEL_DIR / MODEL_FILE
    if target.exists() and target.stat().st_size > 4_000_000_000:
        print("[OK] Validation model already exists:")
        print(target)
    else:
        print("Downloading official Stable Diffusion v1.5 validation checkpoint...")
        print("This file is about 4.27 GB.")
        cached = hf_hub_download(
            repo_id=REPO_ID,
            filename=MODEL_FILE,
        )
        print("Copying checkpoint into BigIMG Generate model folder...")
        shutil.copy2(cached, target)
        print("[OK] Saved:")
        print(target)

    print()
    print("Preparing lightweight Diffusers config/tokenizer cache...")
    snapshot_download(
        repo_id=REPO_ID,
        local_dir=str(CONFIG_DIR),
        allow_patterns=[
            "*.json",
            "*.txt",
            "*.yaml",
            "*.md",
            "tokenizer/*",
            "scheduler/*",
            "feature_extractor/*",
        ],
        ignore_patterns=[
            "*.safetensors",
            "*.bin",
            "*.ckpt",
        ],
    )

    print()
    print("[READY] Validation model and config assets are prepared.")
    print("Next: run first_image_test.bat")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nCancelled.")
        raise SystemExit(130)
    except Exception as exc:
        print("\n[ERROR]", type(exc).__name__ + ":", exc)
        print("Check internet access and free disk space, then try again.")
        raise SystemExit(1)
