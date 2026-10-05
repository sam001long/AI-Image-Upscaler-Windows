# BigIMG Generate MVP

Windows 本機 AI 生圖工具。BigIMG Generate 與 BigIMG 圖片放大工具維持獨立，只保留輕量 handoff。

目前功能：
- 掃描本機 `.safetensors` / `.ckpt` 主模型
- SDXL / SD1.5
- 文字生圖
- 參考圖生圖（img2img）
- 局部重繪（inpaint，白色遮罩區域重繪）
- LoRA 掃描、載入與強度調整
- VAE 掃描與切換
- ControlNet 姿勢控制
- OpenPose 自動抽人物骨架
- 可直接載入現成 OpenPose 骨架圖
- 自動硬體 / VRAM 建議設定
- 低 VRAM 模式
- PNG + JSON metadata 輸出
- BigIMG 輕量 handoff

## 快速開始

1. 安裝 Python 3.11 x64。
2. 執行 `setup.bat`。
3. 將主模型放進：
   - `models/checkpoints/sdxl/`
   - `models/checkpoints/sd15/`
4. 可選：將 LoRA 放進 `models/lora/`。
5. 可選：將 VAE 放進 `models/vae/`。
6. 姿勢控制用 ControlNet 放進：
   - `models/controlnet/sd15/`
   - `models/controlnet/sdxl/`
7. 執行 `run.bat`。

> 第一次安裝 Python 套件需要網路。OpenPose 自動抽骨架第一次使用時，還需要下載 OpenPose 偵測權重；下載後會使用本機快取。若要完全離線，也可以直接載入已經準備好的 OpenPose 骨架圖。

## 模型格式

MVP 優先支援：
- SDXL checkpoint (`.safetensors`)
- SD1.5 checkpoint (`.safetensors`)
- LoRA (`.safetensors`)
- VAE (`.safetensors`)
- ControlNet (`.safetensors` / `.ckpt` / `.pth`)
- 主模型 `.ckpt` 會列出，但不保證所有第三方模型都可載入

第三方主模型、LoRA、VAE、ControlNet 必須彼此架構相容，例如 SD1.5 ControlNet 不應搭配 SDXL 主模型。

## 姿勢控制：ControlNet + OpenPose

「姿勢控制」模式有兩種輸入方式。

### 從人物照片自動抽姿勢
1. 選主模型。
2. 選對應的 OpenPose ControlNet。
3. 選「姿勢來源圖」。
4. 按「自動抽 OpenPose 骨架」。
5. 確認預覽中的骨架。
6. 輸入 Prompt。
7. 調整「控制強度」。
8. 生成。

OpenPose 在這裡只負責把人物姿勢轉成骨架控制圖；真正控制生成的是 ControlNet。

### 直接使用骨架圖
若已有 OpenPose 骨架 PNG/JPG，可直接按「直接選骨架圖」，不需要再次跑 OpenPose 偵測器，也較適合完全離線使用。

### 控制強度
`controlnet_conditioning_scale` 預設為 0.8：
- 較低：生成較自由
- 較高：更強制遵循姿勢骨架

## 自動 VRAM profile

啟動後會依 CUDA VRAM 提供建議：
- < 6 GB：512×512、8 steps、低 VRAM
- 6–10 GB：768×768、12 steps、低 VRAM
- >= 10 GB：1024×1024、20 steps
- 無 CUDA：CPU / 相容模式

使用者仍可手動修改尺寸、steps 與低 VRAM 開關。

ControlNet 會再增加顯存需求，因此低 VRAM 電腦建議先從 512×512 測試。

## 局部重繪

目前 MVP 使用外部遮罩圖：
- 先選參考圖
- 再選黑白遮罩圖
- 白色區域 = 重新生成
- 黑色區域 = 儘量保留

後續可再加入直接在圖片上塗遮罩的畫筆介面。

## BigIMG handoff

BigIMG Generate 與 BigIMG 維持兩個獨立工具。

### 相容模式（預設）
- 指定本機 BigIMG.exe
- 啟動 BigIMG
- 自動打開檔案總管並選中最新生成圖
- 寫入 `%TEMP%\\BigIMGGenerate\\handoff.json`

### CLI (--input)
- 預留 `BigIMG.exe --input <image path>`
- 等 BigIMG Windows 本體原始碼可修改後，再補真正自動載入圖片的接收端

## 待完成
- BigIMG 主程式 handoff 接收端
- 直接畫遮罩
- 多 ControlNet
- IP-Adapter / 人物一致性
- Windows EXE 打包與本機 GPU 實測
