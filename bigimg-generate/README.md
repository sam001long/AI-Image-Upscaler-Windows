# BigIMG Generate MVP

Windows 本機 AI 生圖原型。第一階段目標：

- 掃描本機 `.safetensors` / `.ckpt` 模型
- 文字生圖
- SDXL / SD1.5 手動或自動選擇
- 低 VRAM 模式
- 儲存輸出圖片
- 為後續 img2img / inpaint / BigIMG Upscale 串接保留介面

## 快速開始

1. 安裝 Python 3.11 x64。
2. 執行 `setup.bat`。
3. 將模型放進：
   - `models/checkpoints/sdxl/`
   - `models/checkpoints/sd15/`
4. 執行 `run.bat`。
5. 在介面中選模型、輸入 Prompt，按「生成」。

> 第一次安裝 PyTorch / Diffusers 套件會需要網路。模型推論本身可在本機執行。

## 模型格式

MVP 優先支援：

- SDXL checkpoint (`.safetensors`)
- SD1.5 checkpoint (`.safetensors`)
- `.ckpt` 僅列出，不保證所有模型可載入

後續版本再加入 LoRA、VAE、img2img、inpaint、ControlNet。

## 低 VRAM

勾選低 VRAM 時會優先：

- FP16
- CPU offload
- attention slicing
- VAE slicing / tiling（模型支援時）

這是第一個可運作骨架，之後可再加入更細的顯卡偵測與自動配置。
