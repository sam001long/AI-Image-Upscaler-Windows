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
- IP-Adapter 人物參考一致性
- OpenPose 自動抽人物骨架
- 可直接載入現成 OpenPose 骨架圖
- 自動硬體 / VRAM 建議設定
- 低 VRAM 模式
- PNG + JSON metadata 輸出
- BigIMG 輕量 handoff

## 快速開始

1. 安裝 Python 3.11 x64。
2. 執行 `setup.bat`。
   - 有 NVIDIA 顯卡：優先安裝官方 PyTorch CUDA 12.6 build。
   - 沒有 NVIDIA：安裝 CPU build。
   - 安裝完會自動執行 `diagnostics.py` 檢查 PyTorch、CUDA 與必要套件。
3. 將主模型放進：
   - `models/checkpoints/sdxl/`
   - `models/checkpoints/sd15/`
4. 可選：將 LoRA 放進 `models/lora/`。
5. 可選：將 VAE 放進 `models/vae/`。
6. 姿勢控制用 ControlNet 放進：
   - `models/controlnet/sd15/`
   - `models/controlnet/sdxl/`
7. IP-Adapter 權重放進 `models/ipadapter/sd15/` 或 `models/ipadapter/sdxl/`。
8. 可先執行 `smoke_test.bat` 看完整環境報告。
9. 執行 `run.bat`。啟動前會先做快速環境檢查。

> 第一次安裝 Python 套件需要網路。PyTorch 目前固定使用 2.13.0；Windows NVIDIA 路徑使用官方 CUDA 12.6 wheel。OpenPose 自動抽骨架第一次使用時，還需要下載 OpenPose 偵測權重；下載後會使用本機快取。若要完全離線，也可以直接載入已經準備好的 OpenPose 骨架圖。

## 模型格式

MVP 優先支援：
- SDXL checkpoint (`.safetensors`)
- SD1.5 checkpoint (`.safetensors`)
- LoRA (`.safetensors`)
- VAE (`.safetensors`)
- ControlNet (`.safetensors` / `.ckpt` / `.pth`)
- IP-Adapter (`.safetensors` / `.bin`)
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

## 人物參考一致性：IP-Adapter

可選擇一張人物參考圖，搭配本機 IP-Adapter 權重，讓生成角色外觀更接近參考人物。

使用方式：
1. 選擇與主模型家族相容的 IP-Adapter。
2. 選「人物參考圖」。
3. 調整「一致性」強度，預設 0.65。
4. 可單獨使用，也可和「姿勢控制」一起使用。

搭配姿勢控制時：
- OpenPose / ControlNet 控制姿勢
- IP-Adapter 約束人物外觀

目前第一版以單張人物參考圖為主，第三方 IP-Adapter 權重是否可直接載入，仍需用實際模型在 Windows GPU 驗證。

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
- 更進階的人物參考一致性
- Windows EXE 打包與本機 GPU 實測


## Windows 驗證流程

目前 Draft PR 已能做「環境層」驗證，但真正生圖仍需要本機模型。

建議實機順序：
1. 執行 `setup.bat`。
2. 確認 diagnostics 顯示 `CUDA available: True`（NVIDIA 使用者）。
3. 執行 `smoke_test.bat`。
4. 先只放一個 SD1.5 或 SDXL checkpoint。
5. 第一輪只測文字生圖，不開 LoRA / VAE / ControlNet / IP-Adapter。
6. 基本生圖成功後，再逐項打開附加功能。

若 diagnostics 顯示 `CUDA available: False`，程式仍可走 CPU，但速度會非常慢；這時先處理 PyTorch / NVIDIA driver，不應直接測大型模型。


## 第一張實際生圖驗收

環境檢查通過後：

1. 放入一個 SD1.5 或 SDXL checkpoint。
2. 雙擊 `first_image_test.bat`。
3. 測試只跑最基本文字生圖：
   - 512x512
   - 6 steps
   - 固定 seed
   - 不使用 LoRA
   - 不使用額外 VAE
   - 不使用 ControlNet
   - 不使用 IP-Adapter
4. 成功時會輸出到：
   `outputs/validation/first_image_seed12345.png`

若失敗，腳本會盡量分類：
- GPU 顯存不足
- CUDA / NVIDIA driver 問題
- checkpoint / safetensors 問題
- Diffusers config / Hub cache 問題

### 單檔模型的注意事項

Diffusers 的 `from_single_file()` 可以直接讀本機 `.ckpt` / `.safetensors`，但某些單檔模型第一次載入時仍可能需要從 Hugging Face 取得對應設定並寫入快取。若未來要做到完全離線 Portable，會再把必要 config/cache 一併打包。
