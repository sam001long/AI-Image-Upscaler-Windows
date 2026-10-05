from __future__ import annotations

import argparse
import sys
import traceback
from datetime import datetime
from pathlib import Path

import torch

from core.generator import GenerateRequest, LocalGenerator
from core.model_scanner import scan_models


APP_DIR = Path(__file__).resolve().parent
MODEL_DIR = APP_DIR / "models" / "checkpoints"
OUTPUT_DIR = APP_DIR / "outputs" / "validation"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def classify_error(exc: BaseException) -> str:
    text = str(exc).lower()
    if "out of memory" in text or "cuda oom" in text:
        return (
            "GPU 顯存不足。先改用 512x512、較少 steps，並開啟低 VRAM 模式。"
        )
    if "cuda" in text and ("not available" in text or "driver" in text):
        return "CUDA / NVIDIA 驅動異常。請先執行 smoke_test.bat 檢查環境。"
    if "config" in text and ("hub" in text or "local" in text or "repository" in text):
        return (
            "模型缺少 Diffusers 所需設定。單檔 checkpoint 第一次載入可能需要網路取得設定快取，"
            "或之後提供本機 config。"
        )
    if "safetensor" in text or "checkpoint" in text:
        return "模型檔可能不相容或損壞。請先換一個已知可用的 SD1.5 / SDXL checkpoint 測試。"
    return "未分類錯誤。請保留下方完整 traceback。"


def main() -> int:
    parser = argparse.ArgumentParser(description="BigIMG Generate first image validation")
    parser.add_argument("--model", help="checkpoint path; omitted = first scanned model")
    parser.add_argument("--family", choices=["Auto", "SD1.5", "SDXL"], default="Auto")
    parser.add_argument("--width", type=int, default=512)
    parser.add_argument("--height", type=int, default=512)
    parser.add_argument("--steps", type=int, default=6)
    parser.add_argument("--seed", type=int, default=12345)
    parser.add_argument(
        "--prompt",
        default="a clean studio photograph of a red ceramic teapot on a wooden table, soft light, detailed",
    )
    args = parser.parse_args()

    print("BigIMG Generate - First Image Test")
    print("==================================")

    models = scan_models(MODEL_DIR)
    if args.model:
        model_path = Path(args.model).resolve()
        if not model_path.exists():
            print("[ERROR] Model not found:", model_path)
            return 2
        family = args.family
    else:
        if not models:
            print("[ERROR] No checkpoint found.")
            print("Put one .safetensors model under:")
            print("  models/checkpoints/sd15/")
            print("or")
            print("  models/checkpoints/sdxl/")
            return 2
        model_path = models[0].path
        family = args.family if args.family != "Auto" else models[0].family

    if family == "Unknown":
        family = "Auto"

    print("Model:", model_path)
    print("Family:", family)
    print("CUDA:", torch.cuda.is_available())
    if torch.cuda.is_available():
        print("GPU:", torch.cuda.get_device_name(0))
        print("VRAM GB:", round(torch.cuda.get_device_properties(0).total_memory / (1024 ** 3), 2))
    print("Size:", f"{args.width}x{args.height}")
    print("Steps:", args.steps)
    print("Seed:", args.seed)
    print()

    engine = LocalGenerator()
    req = GenerateRequest(
        model_path=str(model_path),
        family=family,
        prompt=args.prompt,
        negative_prompt="blurry, low quality, distorted",
        width=args.width,
        height=args.height,
        steps=args.steps,
        guidance_scale=6.0,
        seed=args.seed,
        low_vram=True,
        mode="txt2img",
    )

    started = datetime.now()
    try:
        image, seed = engine.generate(req)
    except Exception as exc:
        print()
        print("[FAILED]", type(exc).__name__ + ":", exc)
        print("[HINT]", classify_error(exc))
        print()
        traceback.print_exc()
        return 1

    elapsed = (datetime.now() - started).total_seconds()
    output = OUTPUT_DIR / f"first_image_seed{seed}.png"
    image.save(output)

    print()
    print("[SUCCESS] First image generated.")
    print("Output:", output)
    print("Seconds:", round(elapsed, 1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
