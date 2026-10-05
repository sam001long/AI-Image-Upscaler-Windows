# BigIMG Generate｜現在就可以測

這是目前的 Windows 開發測試版，不是最後的 Portable 正式版。

## 最簡單測法

1. 下載 `feature/bigimg-generate-mvp` branch 的 ZIP。
2. 解壓縮。
3. 進入 `bigimg-generate` 資料夾。
4. 確認電腦已安裝 Python 3.11 x64。
5. 雙擊：

`START_TEST.bat`

接下來不用自己依序點其他檔案。

START_TEST 會自動：

- 建立 / 修復 Python 環境
- 安裝 PyTorch 與必要套件
- 檢查 NVIDIA / CUDA
- 若沒有驗收模型，自動下載 SD1.5 驗收模型
- 執行第一張 512×512 真實生圖
- 成功後詢問是否直接開啟 BigIMG Generate

## 成功標準

看到：

`[PASS] BigIMG Generate basic test passed.`

並且出現：

`outputs/validation/first_image_seed12345.png`

就代表最基本的本機生圖鏈已經真的跑通。

## 如果失敗

不要重裝整台電腦。

直接把黑色視窗最後一段錯誤訊息截圖或複製回來即可。測試程式目前會盡量區分：

- Python / 套件問題
- NVIDIA / CUDA 問題
- VRAM 不足
- 模型下載問題
- checkpoint / config 問題

## 目前與正式 Portable 的差別

目前測試版仍需要 Python 3.11。

正式目標仍是：

`BigIMG_Generate_Portable.zip`
→ 解壓縮
→ 雙擊 `BigIMG Generate.exe`
→ 不需要另外安裝 Python

等第一張真實生圖通過後，再進 Portable 打包階段。
