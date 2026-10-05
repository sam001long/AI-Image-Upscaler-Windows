from __future__ import annotations

import gc
from dataclasses import dataclass
from pathlib import Path

import torch
from PIL import Image
from diffusers import (
    AutoencoderKL,
    ControlNetModel,
    StableDiffusionControlNetPipeline,
    StableDiffusionImg2ImgPipeline,
    StableDiffusionInpaintPipeline,
    StableDiffusionPipeline,
    StableDiffusionXLControlNetPipeline,
    StableDiffusionXLImg2ImgPipeline,
    StableDiffusionXLInpaintPipeline,
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
    vae_path: str | None = None
    mode: str = "txt2img"
    input_image: Image.Image | None = None
    mask_image: Image.Image | None = None
    strength: float = 0.45
    controlnet_path: str | None = None
    control_image: Image.Image | None = None
    control_scale: float = 0.8
    ip_adapter_path: str | None = None
    identity_image: Image.Image | None = None
    ip_adapter_scale: float = 0.65


class LocalGenerator:
    def __init__(self) -> None:
        self.pipe = None
        self.loaded_key = None

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

    def hardware_profile(self) -> dict:
        vram = self.vram_gb()
        if vram is None:
            return {"name": "CPU / 相容模式", "width": 512, "height": 512, "steps": 8, "low_vram": True}
        if vram < 6:
            return {"name": "低顯存", "width": 512, "height": 512, "steps": 8, "low_vram": True}
        if vram < 10:
            return {"name": "標準", "width": 768, "height": 768, "steps": 12, "low_vram": True}
        return {"name": "高品質", "width": 1024, "height": 1024, "steps": 20, "low_vram": False}

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

    @staticmethod
    def _load_ip_adapter(pipe, ip_adapter_path: str, scale: float) -> None:
        adapter = Path(ip_adapter_path).resolve()
        pipe.load_ip_adapter(
            str(adapter.parent),
            weight_name=adapter.name,
            image_encoder_folder=None,
        )
        pipe.set_ip_adapter_scale(max(0.0, min(1.5, float(scale))))

    def load(
        self,
        model_path: str,
        family: str,
        low_vram: bool,
        mode: str,
        lora_path: str | None,
        lora_scale: float,
        vae_path: str | None,
        controlnet_path: str | None,
        ip_adapter_path: str | None,
        ip_adapter_scale: float,
    ) -> None:
        resolved = self._resolve_family(family, model_path)
        lora_abs = str(Path(lora_path).resolve()) if lora_path else None
        vae_abs = str(Path(vae_path).resolve()) if vae_path else None
        controlnet_abs = str(Path(controlnet_path).resolve()) if controlnet_path else None
        ip_adapter_abs = str(Path(ip_adapter_path).resolve()) if ip_adapter_path else None

        key = (
            str(Path(model_path).resolve()),
            resolved,
            low_vram,
            mode,
            lora_abs,
            round(lora_scale, 3),
            vae_abs,
            controlnet_abs,
            ip_adapter_abs,
            round(ip_adapter_scale, 3),
        )
        if self.pipe is not None and self.loaded_key == key:
            return

        self.unload()
        dtype = torch.float16 if torch.cuda.is_available() else torch.float32
        common = {
            "torch_dtype": dtype,
            "use_safetensors": str(model_path).lower().endswith(".safetensors"),
        }

        if mode == "pose":
            if not controlnet_abs:
                raise ValueError("姿勢控制模式需要先選擇 ControlNet 模型。")
            controlnet = ControlNetModel.from_single_file(
                controlnet_abs,
                torch_dtype=dtype,
            )
            cls = StableDiffusionXLControlNetPipeline if resolved == "SDXL" else StableDiffusionControlNetPipeline
            pipe = cls.from_single_file(model_path, controlnet=controlnet, **common)
        elif mode == "img2img":
            cls = StableDiffusionXLImg2ImgPipeline if resolved == "SDXL" else StableDiffusionImg2ImgPipeline
            pipe = cls.from_single_file(model_path, **common)
        elif mode == "inpaint":
            cls = StableDiffusionXLInpaintPipeline if resolved == "SDXL" else StableDiffusionInpaintPipeline
            pipe = cls.from_single_file(model_path, **common)
        else:
            cls = StableDiffusionXLPipeline if resolved == "SDXL" else StableDiffusionPipeline
            pipe = cls.from_single_file(model_path, **common)

        if vae_abs:
            pipe.vae = AutoencoderKL.from_single_file(
                vae_abs,
                torch_dtype=dtype,
                use_safetensors=vae_abs.lower().endswith(".safetensors"),
            )

        if lora_abs:
            pipe.load_lora_weights(lora_abs, adapter_name="user_lora")
            try:
                pipe.set_adapters(["user_lora"], adapter_weights=[float(lora_scale)])
            except Exception:
                pass

        if ip_adapter_abs:
            self._load_ip_adapter(pipe, ip_adapter_abs, ip_adapter_scale)

        self.pipe = self._prepare_pipe(pipe, low_vram)
        self.loaded_key = key

    def generate(self, req: GenerateRequest):
        if not req.prompt.strip():
            raise ValueError("Prompt 不可空白。")
        if req.mode in {"img2img", "inpaint"} and req.input_image is None:
            raise ValueError("這個模式需要先選擇參考圖。")
        if req.mode == "inpaint" and req.mask_image is None:
            raise ValueError("局部重繪模式需要遮罩圖。白色區域會被重新生成。")
        if req.mode == "pose":
            if req.control_image is None:
                raise ValueError("姿勢控制模式需要姿勢控制圖。")
            if not req.controlnet_path:
                raise ValueError("姿勢控制模式需要 ControlNet 模型。")
        if req.ip_adapter_path and req.identity_image is None:
            raise ValueError("已選擇 IP-Adapter，但尚未選人物參考圖。")

        self.load(
            req.model_path,
            req.family,
            req.low_vram,
            req.mode,
            req.lora_path,
            req.lora_scale,
            req.vae_path,
            req.controlnet_path,
            req.ip_adapter_path,
            req.ip_adapter_scale,
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

        if req.ip_adapter_path and req.identity_image is not None:
            kwargs["ip_adapter_image"] = req.identity_image.convert("RGB")

        if req.mode == "img2img":
            image = req.input_image.convert("RGB").resize((req.width, req.height), Image.LANCZOS)
            kwargs["image"] = image
            kwargs["strength"] = max(0.05, min(0.95, float(req.strength)))
        elif req.mode == "inpaint":
            image = req.input_image.convert("RGB").resize((req.width, req.height), Image.LANCZOS)
            mask = req.mask_image.convert("L").resize((req.width, req.height), Image.NEAREST)
            kwargs["image"] = image
            kwargs["mask_image"] = mask
            kwargs["strength"] = max(0.05, min(0.95, float(req.strength)))
        elif req.mode == "pose":
            control = req.control_image.convert("RGB").resize((req.width, req.height), Image.LANCZOS)
            kwargs["image"] = control
            kwargs["controlnet_conditioning_scale"] = max(0.0, min(2.0, float(req.control_scale)))

        result = self.pipe(**kwargs)
        return result.images[0], int(seed)
