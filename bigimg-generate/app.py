from __future__ import annotations

import json
import os
import subprocess
import threading
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageTk

from core.generator import GenerateRequest, LocalGenerator
from core.model_scanner import LoraInfo, ModelInfo, VaeInfo, scan_loras, scan_models, scan_vaes


APP_DIR = Path(__file__).resolve().parent
MODELS_DIR = APP_DIR / "models" / "checkpoints"
LORA_DIR = APP_DIR / "models" / "lora"
VAE_DIR = APP_DIR / "models" / "vae"
OUTPUT_DIR = APP_DIR / "outputs"
SETTINGS_PATH = APP_DIR / "settings.json"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

for folder in [
    MODELS_DIR / "sdxl",
    MODELS_DIR / "sd15",
    LORA_DIR,
    VAE_DIR,
    APP_DIR / "models" / "inpaint",
    APP_DIR / "models" / "upscalers",
]:
    folder.mkdir(parents=True, exist_ok=True)


class BigIMGGenerateApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("BigIMG Generate — MVP")
        self.geometry("1320x860")
        self.minsize(1120, 740)

        self.generator_engine = LocalGenerator()
        self.models: list[ModelInfo] = []
        self.loras: list[LoraInfo] = []
        self.vaes: list[VaeInfo] = []
        self.input_image: Image.Image | None = None
        self.input_image_path: str | None = None
        self.mask_image: Image.Image | None = None
        self.mask_image_path: str | None = None
        self.preview_photo = None
        self.last_image: Image.Image | None = None
        self.last_output_path: Path | None = None
        self.settings = self._load_settings()

        self._build_ui()
        self.refresh_models()
        self._apply_hardware_profile()

    def _load_settings(self) -> dict:
        try:
            return json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _save_settings(self) -> None:
        SETTINGS_PATH.write_text(json.dumps(self.settings, ensure_ascii=False, indent=2), encoding="utf-8")

    def _build_ui(self) -> None:
        outer = ttk.Frame(self, padding=14)
        outer.pack(fill="both", expand=True)
        left = ttk.Frame(outer)
        left.pack(side="left", fill="y", padx=(0, 14))
        center = ttk.Frame(outer)
        center.pack(side="left", fill="both", expand=True)

        ttk.Label(left, text="BigIMG Generate", font=("Segoe UI", 18, "bold")).pack(anchor="w")
        ttk.Label(left, text="Windows 本機 AI 生圖 MVP").pack(anchor="w", pady=(0, 12))

        ttk.Label(left, text="模式").pack(anchor="w")
        self.mode_var = tk.StringVar(value="文字生圖")
        ttk.Combobox(left, textvariable=self.mode_var, state="readonly",
                     values=["文字生圖", "參考圖生圖", "局部重繪"], width=24).pack(fill="x", pady=(4, 10))

        ttk.Label(left, text="主模型").pack(anchor="w")
        self.model_var = tk.StringVar()
        self.model_combo = ttk.Combobox(left, textvariable=self.model_var, width=44, state="readonly")
        self.model_combo.pack(fill="x", pady=(4, 6))
        ttk.Button(left, text="重新掃描模型 / LoRA / VAE", command=self.refresh_models).pack(fill="x")
        ttk.Button(left, text="開啟模型資料夾", command=lambda: os.startfile(MODELS_DIR)).pack(fill="x", pady=(5, 10))

        ttk.Label(left, text="LoRA（可不選）").pack(anchor="w")
        self.lora_var = tk.StringVar(value="不使用")
        self.lora_combo = ttk.Combobox(left, textvariable=self.lora_var, width=44, state="readonly")
        self.lora_combo.pack(fill="x", pady=(4, 3))
        self.lora_scale_var = tk.DoubleVar(value=1.0)
        lora_row = ttk.Frame(left)
        lora_row.pack(fill="x", pady=(0, 7))
        ttk.Label(lora_row, text="強度").pack(side="left")
        ttk.Spinbox(lora_row, from_=0.1, to=2.0, increment=0.1, textvariable=self.lora_scale_var, width=8).pack(side="left", padx=(6, 8))
        ttk.Button(lora_row, text="資料夾", command=lambda: os.startfile(LORA_DIR)).pack(side="left")

        ttk.Label(left, text="VAE（可不選）").pack(anchor="w")
        self.vae_var = tk.StringVar(value="使用模型內建 VAE")
        self.vae_combo = ttk.Combobox(left, textvariable=self.vae_var, width=44, state="readonly")
        self.vae_combo.pack(fill="x", pady=(4, 3))
        ttk.Button(left, text="開啟 VAE 資料夾", command=lambda: os.startfile(VAE_DIR)).pack(fill="x", pady=(0, 8))

        ttk.Label(left, text="參考圖").pack(anchor="w")
        ttk.Button(left, text="選擇參考圖", command=self.select_input_image).pack(fill="x", pady=(4, 3))
        self.input_label_var = tk.StringVar(value="尚未選擇")
        ttk.Label(left, textvariable=self.input_label_var, wraplength=300).pack(anchor="w", pady=(0, 5))

        ttk.Label(left, text="遮罩圖（局部重繪）").pack(anchor="w")
        ttk.Button(left, text="選擇遮罩圖", command=self.select_mask_image).pack(fill="x", pady=(4, 3))
        self.mask_label_var = tk.StringVar(value="尚未選擇｜白色區域會重繪")
        ttk.Label(left, textvariable=self.mask_label_var, wraplength=300).pack(anchor="w", pady=(0, 6))

        ttk.Label(left, text="保留原圖程度").pack(anchor="w")
        self.preserve_var = tk.DoubleVar(value=0.55)
        ttk.Scale(left, from_=0.10, to=0.90, variable=self.preserve_var, orient="horizontal").pack(fill="x")
        self.preserve_value = ttk.Label(left, text="55%")
        self.preserve_value.pack(anchor="w", pady=(0, 8))
        self.preserve_var.trace_add("write", lambda *_: self.preserve_value.config(text=f"{int(self.preserve_var.get()*100)}%"))

        ttk.Label(left, text="模型家族").pack(anchor="w")
        self.family_var = tk.StringVar(value="Auto")
        ttk.Combobox(left, textvariable=self.family_var, state="readonly",
                     values=["Auto", "SDXL", "SD1.5"], width=18).pack(fill="x", pady=(4, 8))

        size_row = ttk.Frame(left)
        size_row.pack(fill="x", pady=(0, 6))
        ttk.Label(size_row, text="尺寸").pack(side="left")
        self.width_var = tk.IntVar(value=512)
        self.height_var = tk.IntVar(value=512)
        ttk.Entry(size_row, textvariable=self.width_var, width=7).pack(side="left", padx=(8, 0))
        ttk.Label(size_row, text="×").pack(side="left", padx=3)
        ttk.Entry(size_row, textvariable=self.height_var, width=7).pack(side="left")

        param_row = ttk.Frame(left)
        param_row.pack(fill="x", pady=(0, 6))
        ttk.Label(param_row, text="Steps").pack(side="left")
        self.steps_var = tk.IntVar(value=12)
        ttk.Spinbox(param_row, from_=1, to=60, textvariable=self.steps_var, width=7).pack(side="left", padx=(6, 12))
        ttk.Label(param_row, text="CFG").pack(side="left")
        self.cfg_var = tk.DoubleVar(value=6.0)
        ttk.Spinbox(param_row, from_=1.0, to=20.0, increment=0.5, textvariable=self.cfg_var, width=7).pack(side="left", padx=(6, 0))

        ttk.Label(left, text="Seed（-1 = 隨機）").pack(anchor="w")
        self.seed_var = tk.IntVar(value=-1)
        ttk.Entry(left, textvariable=self.seed_var, width=14).pack(anchor="w", pady=(4, 6))

        self.auto_profile_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(left, text="自動硬體最佳化", variable=self.auto_profile_var,
                        command=self._apply_hardware_profile).pack(anchor="w", pady=(2, 2))
        self.low_vram_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(left, text="低 VRAM 模式", variable=self.low_vram_var).pack(anchor="w", pady=(2, 6))
        self.hardware_var = tk.StringVar(value="偵測硬體中…")
        ttk.Label(left, textvariable=self.hardware_var, wraplength=310).pack(anchor="w")

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
        ttk.Button(actions, text="送到 BigIMG", command=self.send_to_bigimg).pack(side="left", padx=(8, 0))
        self.status_var = tk.StringVar(value="準備完成")
        ttk.Label(actions, textvariable=self.status_var).pack(side="right")

        bigimg_row = ttk.Frame(center)
        bigimg_row.pack(fill="x", pady=(0, 8))
        self.bigimg_path_var = tk.StringVar(value=self.settings.get("bigimg_exe", "尚未指定 BigIMG.exe"))
        ttk.Label(bigimg_row, textvariable=self.bigimg_path_var).pack(side="left", fill="x", expand=True)
        ttk.Button(bigimg_row, text="指定 BigIMG.exe", command=self.choose_bigimg_exe).pack(side="right")

        preview_box = ttk.LabelFrame(center, text="預覽")
        preview_box.pack(fill="both", expand=True)
        self.preview = ttk.Label(preview_box, anchor="center")
        self.preview.pack(fill="both", expand=True, padx=10, pady=10)

        ttk.Label(center, text="已加入：LoRA / VAE / img2img / inpaint / 自動 VRAM｜BigIMG handoff 需 BigIMG 端支援 --input").pack(anchor="w", pady=(10, 0))

    def _apply_hardware_profile(self) -> None:
        profile = self.generator_engine.hardware_profile()
        name = self.generator_engine.device_name()
        vram = self.generator_engine.vram_gb()
        vram_text = "無 CUDA VRAM" if vram is None else f"{vram:.1f} GB VRAM"
        self.hardware_var.set(f"{name}｜{vram_text}｜建議：{profile['name']}")
        if self.auto_profile_var.get():
            self.width_var.set(profile["width"])
            self.height_var.set(profile["height"])
            self.steps_var.set(profile["steps"])
            self.low_vram_var.set(profile["low_vram"])

    def refresh_models(self) -> None:
        self.models = scan_models(MODELS_DIR)
        self.loras = scan_loras(LORA_DIR)
        self.vaes = scan_vaes(VAE_DIR)
        self.model_combo["values"] = [m.label for m in self.models]
        self.lora_combo["values"] = ["不使用"] + [x.label for x in self.loras]
        self.vae_combo["values"] = ["使用模型內建 VAE"] + [x.label for x in self.vaes]
        if self.models:
            self.model_combo.current(0)
        else:
            self.model_var.set("")
        self.lora_combo.current(0)
        self.vae_combo.current(0)
        self.status_var.set(f"找到 {len(self.models)} 個模型、{len(self.loras)} 個 LoRA、{len(self.vaes)} 個 VAE")

    def select_input_image(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("圖片", "*.png;*.jpg;*.jpeg;*.webp;*.bmp")])
        if not path:
            return
        try:
            self.input_image = Image.open(path).convert("RGB")
            self.input_image_path = path
            self.input_label_var.set(Path(path).name)
            preview = self.input_image.copy()
            preview.thumbnail((760, 470))
            self.preview_photo = ImageTk.PhotoImage(preview)
            self.preview.configure(image=self.preview_photo)
        except Exception as exc:
            messagebox.showerror("無法讀取圖片", str(exc))

    def select_mask_image(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("遮罩圖片", "*.png;*.jpg;*.jpeg;*.webp;*.bmp")])
        if not path:
            return
        try:
            self.mask_image = Image.open(path).convert("L")
            self.mask_image_path = path
            self.mask_label_var.set(Path(path).name + "｜白色區域會重繪")
        except Exception as exc:
            messagebox.showerror("無法讀取遮罩", str(exc))

    def _selected_model(self) -> ModelInfo:
        idx = self.model_combo.current()
        if idx < 0 or idx >= len(self.models):
            raise ValueError("請先加入並選擇主模型。")
        return self.models[idx]

    def _selected_lora_path(self) -> str | None:
        idx = self.lora_combo.current()
        return None if idx <= 0 else str(self.loras[idx - 1].path)

    def _selected_vae_path(self) -> str | None:
        idx = self.vae_combo.current()
        return None if idx <= 0 else str(self.vaes[idx - 1].path)

    def start_generate(self) -> None:
        try:
            model = self._selected_model()
            mode_map = {"文字生圖": "txt2img", "參考圖生圖": "img2img", "局部重繪": "inpaint"}
            mode = mode_map[self.mode_var.get()]
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
                lora_path=self._selected_lora_path(),
                lora_scale=float(self.lora_scale_var.get()),
                vae_path=self._selected_vae_path(),
                mode=mode,
                input_image=self.input_image,
                mask_image=self.mask_image,
                strength=1.0 - float(self.preserve_var.get()),
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
            out = OUTPUT_DIR / f"{timestamp}_{req.mode}_seed{seed}.png"
            image.save(out)
            meta = {
                "mode": req.mode,
                "prompt": req.prompt,
                "negative_prompt": req.negative_prompt,
                "model": req.model_path,
                "family": req.family,
                "lora": req.lora_path,
                "lora_scale": req.lora_scale,
                "vae": req.vae_path,
                "input_image": self.input_image_path if req.mode in {"img2img", "inpaint"} else None,
                "mask_image": self.mask_image_path if req.mode == "inpaint" else None,
                "preserve": 1.0 - req.strength if req.mode in {"img2img", "inpaint"} else None,
                "width": req.width,
                "height": req.height,
                "steps": req.steps,
                "guidance_scale": req.guidance_scale,
                "seed": seed,
                "low_vram": req.low_vram,
            }
            out.with_suffix(".json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
            self.after(0, self._show_result, image, seed, out)
        except Exception as exc:
            self.after(0, self._show_error, str(exc))

    def _show_result(self, image: Image.Image, seed: int, out: Path) -> None:
        self.last_image = image.copy()
        self.last_output_path = out
        preview = image.copy()
        preview.thumbnail((760, 470))
        self.preview_photo = ImageTk.PhotoImage(preview)
        self.preview.configure(image=self.preview_photo)
        self.seed_var.set(seed)
        self.status_var.set(f"完成：{out.name}")
        self.generate_button.config(state="normal")

    def choose_bigimg_exe(self) -> None:
        path = filedialog.askopenfilename(title="選擇 BigIMG.exe", filetypes=[("Windows 程式", "*.exe"), ("所有檔案", "*.*")])
        if not path:
            return
        self.settings["bigimg_exe"] = path
        self._save_settings()
        self.bigimg_path_var.set(path)

    def send_to_bigimg(self) -> None:
        if self.last_output_path is None or not self.last_output_path.exists():
            messagebox.showinfo("尚無圖片", "請先生成一張圖片。")
            return

        exe = self.settings.get("bigimg_exe")
        if not exe or not Path(exe).exists():
            self.choose_bigimg_exe()
            exe = self.settings.get("bigimg_exe")
        if not exe or not Path(exe).exists():
            return

        try:
            subprocess.Popen([exe, "--input", str(self.last_output_path)])
            self.status_var.set("已啟動 BigIMG 並傳入圖片路徑")
        except Exception as exc:
            messagebox.showerror("無法啟動 BigIMG", str(exc))

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
