from __future__ import annotations

import gc
from dataclasses import dataclass
from pathlib import Path

import torch
from diffusers import StableDiffusionPipeline, StableDiffusionXLPipeline


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


class LocalGenerator:
    def __init__(self) -> None:
        self.pipe = None
        self.loaded_key: tuple[str, str, bool] | None = None

    @staticmethod
    def cuda_available() -> bool:
        return torch.cuda.is_available()

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
            props = torch.cuda.get_device_properties(0)
            return props.total_memory / (1024 ** 3)
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

    def load(self, model_path: str, family: str, low_vram: bool) -> None:
        resolved = self._resolve_family(family, model_path)
        key = (str(Path(model_path).resolve()), resolved, low_vram)
        if self.pipe is not None and self.loaded_key == key:
            return

        self.unload()

        dtype = torch.float16 if torch.cuda.is_available() else torch.float32
        common = {
            "torch_dtype": dtype,
            "use_safetensors": str(model_path).lower().endswith(".safetensors"),
        }

        if resolved == "SDXL":
            pipe = StableDiffusionXLPipeline.from_single_file(model_path, **common)
        else:
            pipe = StableDiffusionPipeline.from_single_file(model_path, **common)

        if torch.cuda.is_available():
            if low_vram:
                pipe.enable_model_cpu_offload()
                try:
                    pipe.enable_attention_slicing()
                except Exception:
                    pass
                try:
                    pipe.enable_vae_slicing()
                except Exception:
                    pass
                try:
                    pipe.enable_vae_tiling()
                except Exception:
                    pass
            else:
                pipe = pipe.to("cuda")
        else:
            pipe = pipe.to("cpu")

        self.pipe = pipe
        self.loaded_key = key

    def generate(self, req: GenerateRequest):
        if not req.prompt.strip():
            raise ValueError("Prompt 不可空白。")

        self.load(req.model_path, req.family, req.low_vram)

        if req.seed < 0:
            seed = torch.seed() % (2**31 - 1)
        else:
            seed = req.seed

        device = "cuda" if torch.cuda.is_available() else "cpu"
        generator = torch.Generator(device=device).manual_seed(seed)

        result = self.pipe(
            prompt=req.prompt,
            negative_prompt=req.negative_prompt or None,
            width=req.width,
            height=req.height,
            num_inference_steps=req.steps,
            guidance_scale=req.guidance_scale,
            generator=generator,
        )

        return result.images[0], int(seed)
