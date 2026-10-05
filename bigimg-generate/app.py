from __future__ import annotations

import json
import threading
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageTk

from core.generator import GenerateRequest, LocalGenerator
from core.model_scanner import ModelInfo, scan_models


APP_DIR = Path(__file__).resolve().parent
MODELS_DIR = APP_DIR / "models" / "checkpoints"
OUTPUT_DIR = APP_DIR / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

for folder in [
    MODELS_DIR / "sdxl",
    MODELS_DIR / "sd15",
    APP_DIR / "models" / "lora",
    APP_DIR / "models" / "vae",
    APP_DIR / "models" / "inpaint",
    APP_DIR / "models" / "upscalers",
]:
    folder.mkdir(parents=True, exist_ok=True)


class BigIMGGenerateApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("BigIMG Generate — MVP")
        self.geometry("1180x760")
        self.minsize(980, 650)

        self.generator_engine = LocalGenerator()
        self.models: list[ModelInfo] = []
        self.preview_photo = None
        self.last_image: Image.Image | None = None
        self.last_seed: int | None = None

        self._build_ui()
        self.refresh_models()
        self._refresh_hardware_status()

    def _build_ui(self) -> None:
        outer = ttk.Frame(self, padding=14)
        outer.pack(fill="both", expand=True)

        left = ttk.Frame(outer)
        left.pack(side="left", fill="y", padx=(0, 14))

        center = ttk.Frame(outer)
        center.pack(side="left", fill="both", expand=True)

        ttk.Label(left, text="BigIMG Generate", font=("Segoe UI", 18, "bold")).pack(anchor="w")
        ttk.Label(left, text="Windows 本機 AI 生圖 MVP").pack(anchor="w", pady=(0, 14))

        ttk.Label(left, text="模型").pack(anchor="w")
        self.model_var = tk.StringVar()
        self.model_combo = ttk.Combobox(left, textvariable=self.model_var, width=42, state="readonly")
        self.model_combo.pack(fill="x", pady=(4, 6))

        ttk.Button(left, text="重新掃描模型", command=self.refresh_models).pack(fill="x")
        ttk.Button(left, text="開啟模型資料夾", command=self.open_models_folder).pack(fill="x", pady=(5, 12))

        ttk.Label(left, text="模型家族").pack(anchor="w")
        self.family_var = tk.StringVar(value="Auto")
        ttk.Combobox(
            left,
            textvariable=self.family_var,
            state="readonly",
            values=["Auto", "SDXL", "SD1.5"],
            width=18,
        ).pack(fill="x", pady=(4, 12))

        ttk.Label(left, text="尺寸").pack(anchor="w")
        size_row = ttk.Frame(left)
        size_row.pack(fill="x", pady=(4, 8))
        self.width_var = tk.IntVar(value=512)
        self.height_var = tk.IntVar(value=512)
        ttk.Entry(size_row, textvariable=self.width_var, width=8).pack(side="left")
        ttk.Label(size_row, text=" × ").pack(side="left")
        ttk.Entry(size_row, textvariable=self.height_var, width=8).pack(side="left")

        ttk.Label(left, text="Steps").pack(anchor="w")
        self.steps_var = tk.IntVar(value=12)
        ttk.Spinbox(left, from_=1, to=60, textvariable=self.steps_var, width=10).pack(anchor="w", pady=(4, 8))

        ttk.Label(left, text="CFG").pack(anchor="w")
        self.cfg_var = tk.DoubleVar(value=6.0)
        ttk.Spinbox(left, from_=1.0, to=20.0, increment=0.5, textvariable=self.cfg_var, width=10).pack(anchor="w", pady=(4, 8))

        ttk.Label(left, text="Seed（-1 = 隨機）").pack(anchor="w")
        self.seed_var = tk.IntVar(value=-1)
        ttk.Entry(left, textvariable=self.seed_var, width=14).pack(anchor="w", pady=(4, 8))

        self.low_vram_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(left, text="低 VRAM 模式", variable=self.low_vram_var).pack(anchor="w", pady=(4, 10))

        self.hardware_var = tk.StringVar(value="偵測硬體中…")
        ttk.Label(left, textvariable=self.hardware_var, wraplength=300).pack(anchor="w", pady=(6, 12))

        ttk.Label(center, text="Prompt").pack(anchor="w")
        self.prompt = tk.Text(center, height=6, wrap="word")
        self.prompt.pack(fill="x", pady=(4, 10))

        ttk.Label(center, text="Negative Prompt").pack(anchor="w")
        self.negative = tk.Text(center, height=3, wrap="word")
        self.negative.pack(fill="x", pady=(4, 10))

        actions = ttk.Frame(center)
        actions.pack(fill="x", pady=(0, 10))
        self.generate_button = ttk.Button(actions, text="生成圖片", command=self.start_generate)
        self.generate_button.pack(side="left")
        ttk.Button(actions, text="儲存副本", command=self.save_copy).pack(side="left", padx=(8, 0))

        self.status_var = tk.StringVar(value="準備完成")
        ttk.Label(actions, textvariable=self.status_var).pack(side="right")

        preview_box = ttk.LabelFrame(center, text="預覽")
        preview_box.pack(fill="both", expand=True)
        self.preview = ttk.Label(preview_box, anchor="center")
        self.preview.pack(fill="both", expand=True, padx=10, pady=10)

        ttk.Label(
            center,
            text="下一階段：img2img / inpaint / LoRA / 自動 VRAM profile / 送到 BigIMG 放大",
        ).pack(anchor="w", pady=(10, 0))

    def _refresh_hardware_status(self) -> None:
        name = self.generator_engine.device_name()
        vram = self.generator_engine.vram_gb()
        if vram is None:
            self.hardware_var.set(f"運算裝置：{name}｜未偵測到 CUDA VRAM")
        else:
            self.hardware_var.set(f"運算裝置：{name}｜VRAM 約 {vram:.1f} GB")
            if vram <= 6:
                self.low_vram_var.set(True)

    def refresh_models(self) -> None:
        self.models = scan_models(MODELS_DIR)
        self.model_combo["values"] = [m.label for m in self.models]
        if self.models:
            self.model_combo.current(0)
            self.status_var.set(f"找到 {len(self.models)} 個模型")
        else:
            self.model_var.set("")
            self.status_var.set("尚未找到模型，請放入 models/checkpoints")

    def open_models_folder(self) -> None:
        import os
        os.startfile(MODELS_DIR)

    def _selected_model(self) -> ModelInfo:
        idx = self.model_combo.current()
        if idx < 0 or idx >= len(self.models):
            raise ValueError("請先加入並選擇模型。")
        return self.models[idx]

    def start_generate(self) -> None:
        try:
            model = self._selected_model()
            req = GenerateRequest(
                model_path=str(model.path),
                family=self.family_var.get(),
                prompt=self.prompt.get("1.0", "end").strip(),
                negative_prompt=self.negative.get("1.0", "end").strip(),
                width=int(self.width_var.get()),
                height=int(self.height_var.get()),
                steps=int(self.steps_var.get()),
                guidance_scale=float(self.cfg_var.get()),
                seed=int(self.seed_var.get()),
                low_vram=bool(self.low_vram_var.get()),
            )
        except Exception as exc:
            messagebox.showerror("無法開始", str(exc))
            return

        self.generate_button.config(state="disabled")
        self.status_var.set("正在載入模型 / 生成…")
        threading.Thread(target=self._worker_generate, args=(req,), daemon=True).start()

    def _worker_generate(self, req: GenerateRequest) -> None:
        try:
            image, seed = self.generator_engine.generate(req)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            out = OUTPUT_DIR / f"{timestamp}_seed{seed}.png"
            image.save(out)

            meta = {
                "prompt": req.prompt,
                "negative_prompt": req.negative_prompt,
                "model": req.model_path,
                "family": req.family,
                "width": req.width,
                "height": req.height,
                "steps": req.steps,
                "guidance_scale": req.guidance_scale,
                "seed": seed,
                "low_vram": req.low_vram,
            }
            out.with_suffix(".json").write_text(
                json.dumps(meta, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            self.after(0, self._show_result, image, seed, out)
        except Exception as exc:
            self.after(0, self._show_error, str(exc))

    def _show_result(self, image: Image.Image, seed: int, out: Path) -> None:
        self.last_image = image.copy()
        self.last_seed = seed

        preview = image.copy()
        preview.thumbnail((760, 470))
        self.preview_photo = ImageTk.PhotoImage(preview)
        self.preview.configure(image=self.preview_photo)
        self.seed_var.set(seed)
        self.status_var.set(f"完成：{out.name}")
        self.generate_button.config(state="normal")

    def _show_error(self, message: str) -> None:
        self.generate_button.config(state="normal")
        self.status_var.set("生成失敗")
        messagebox.showerror("生成失敗", message)

    def save_copy(self) -> None:
        if self.last_image is None:
            messagebox.showinfo("尚無圖片", "請先生成一張圖片。")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg;*.jpeg")],
        )
        if path:
            self.last_image.save(path)
            self.status_var.set(f"已儲存：{Path(path).name}")


if __name__ == "__main__":
    BigIMGGenerateApp().mainloop()
