# BigIMG Generate MVP

Windows 本機 AI 生圖原型。

目前功能：
- 掃描本機 `.safetensors` / `.ckpt` 主模型
- SDXL / SD1.5
- 文字生圖
- 參考圖生圖（img2img）
- 局部重繪（inpaint，白色遮罩區域重繪）
- LoRA 掃描與單一 LoRA 載入
- 自動硬體 / VRAM 建議設定
- 低 VRAM 模式
- PNG + JSON metadata 輸出

## 快速開始

1. 安裝 Python 3.11 x64。
2. 執行 `setup.bat`。
3. 將主模型放進：
   - `models/checkpoints/sdxl/`
   - `models/checkpoints/sd15/`
4. 可選：將 LoRA 放進 `models/lora/`。
5. 執行 `run.bat`。
6. 選模式、模型並生成。

> 第一次安裝 PyTorch / Diffusers 套件會需要網路。模型推論本身可在本機執行。

## 模型格式

MVP 優先支援：
- SDXL checkpoint (`.safetensors`)
- SD1.5 checkpoint (`.safetensors`)
- LoRA (`.safetensors`)
- `.ckpt` 會列出，但不保證所有模型可載入

## 自動 VRAM profile

啟動後會依 CUDA VRAM 提供建議：
- < 6 GB：512×512、8 steps、低 VRAM
- 6–10 GB：768×768、12 steps、低 VRAM
- >= 10 GB：1024×1024、20 steps
- 無 CUDA：CPU / 相容模式

使用者仍可手動修改尺寸、steps 與低 VRAM 開關。

## 局部重繪

目前 MVP 使用「外部遮罩圖」：
- 先選參考圖
- 再選黑白遮罩圖
- 白色區域 = 重新生成
- 黑色區域 = 儘量保留

後續可再加入直接在圖片上塗遮罩的畫筆介面。

## 待完成
- BigIMG Upscale 串接
- VAE 切換
- ControlNet / pose
- 直接畫遮罩
- 打包 EXE
