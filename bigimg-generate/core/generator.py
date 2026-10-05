from __future__ import annotations

import gc
from dataclasses import dataclass
from pathlib import Path

import torch
from PIL import Image
from diffusers import (
    StableDiffusionImg2ImgPipeline,
    StableDiffusionPipeline,
    StableDiffusionXLImg2ImgPipeline,
    StableDiffusionXLPipeline,
)


@dataclass
class GenerateRequest:
    model_path: str
    family: str
    prompt: str
    negative_prompt: str = ""
    width: int = 512
    height: int = 512
    steps: int = 12
    guidance_scale: float = 6.0
    seed: int = -1
    low_vram: bool = True
    lora_path: str | None = None
    lora_scale: float = 1.0
    mode: str = "txt2img"
    input_image: Image.Image | None = None
    strength: float = 0.45


class LocalGenerator:
    def __init__(self) -> None:
        self.pipe = None
        self.loaded_key: tuple[str, str, bool, str, str | None, float] | None = None

    @staticmethod
    def device_name() -> str:
        if torch.cuda.is_available():
            try:
                return torch.cuda.get_device_name(0)
            except Exception:
                return "CUDA GPU"
        return "CPU"

    @staticmethod
    def vram_gb() -> float | None:
        if not torch.cuda.is_available():
            return None
        try:
            return torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
        except Exception:
            return None

    def unload(self) -> None:
        self.pipe = None
        self.loaded_key = None
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    def _resolve_family(self, family: str, path: str) -> str:
        if family in {"SDXL", "SD1.5"}:
            return family
        lower = path.lower()
        if "sdxl" in lower or "xl" in Path(path).name.lower():
            return "SDXL"
        return "SD1.5"

    def _prepare_pipe(self, pipe, low_vram: bool):
        if torch.cuda.is_available():
            if low_vram:
                pipe.enable_model_cpu_offload()
                for method in ("enable_attention_slicing", "enable_vae_slicing", "enable_vae_tiling"):
                    try:
                        getattr(pipe, method)()
                    except Exception:
                        pass
            else:
                pipe = pipe.to("cuda")
        else:
            pipe = pipe.to("cpu")
        return pipe

    def load(
        self,
        model_path: str,
        family: str,
        low_vram: bool,
        mode: str,
        lora_path: str | None,
        lora_scale: float,
    ) -> None:
        resolved = self._resolve_family(family, model_path)
        lora_abs = str(Path(lora_path).resolve()) if lora_path else None
        key = (str(Path(model_path).resolve()), resolved, low_vram, mode, lora_abs, round(lora_scale, 3))
        if self.pipe is not None and self.loaded_key == key:
            return

        self.unload()
        dtype = torch.float16 if torch.cuda.is_available() else torch.float32
        common = {
            "torch_dtype": dtype,
            "use_safetensors": str(model_path).lower().endswith(".safetensors"),
        }

        if mode == "img2img":
            cls = StableDiffusionXLImg2ImgPipeline if resolved == "SDXL" else StableDiffusionImg2ImgPipeline
        else:
            cls = StableDiffusionXLPipeline if resolved == "SDXL" else StableDiffusionPipeline

        pipe = cls.from_single_file(model_path, **common)

        if lora_abs:
            pipe.load_lora_weights(lora_abs, adapter_name="user_lora")
            try:
                pipe.set_adapters(["user_lora"], adapter_weights=[float(lora_scale)])
            except Exception:
                pass

        self.pipe = self._prepare_pipe(pipe, low_vram)
        self.loaded_key = key

    def generate(self, req: GenerateRequest):
        if not req.prompt.strip():
            raise ValueError("Prompt 不可空白。")
        if req.mode == "img2img" and req.input_image is None:
            raise ValueError("參考圖生圖模式需要先選擇一張參考圖。")

        self.load(
            req.model_path,
            req.family,
            req.low_vram,
            req.mode,
            req.lora_path,
            req.lora_scale,
        )

        seed = torch.seed() % (2**31 - 1) if req.seed < 0 else req.seed
        device = "cuda" if torch.cuda.is_available() else "cpu"
        generator = torch.Generator(device=device).manual_seed(seed)

        kwargs = dict(
            prompt=req.prompt,
            negative_prompt=req.negative_prompt or None,
            width=req.width,
            height=req.height,
            num_inference_steps=req.steps,
            guidance_scale=req.guidance_scale,
            generator=generator,
        )

        if req.mode == "img2img":
            image = req.input_image.convert("RGB").resize((req.width, req.height), Image.LANCZOS)
            kwargs["image"] = image
            kwargs["strength"] = max(0.05, min(0.95, float(req.strength)))

        result = self.pipe(**kwargs)
        return result.images[0], int(seed)
