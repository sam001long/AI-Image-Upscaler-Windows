# AI Image Upscaler Windows

Windows 可攜式 AI 圖片放大工具。

## 目前目標

- Portable：解壓縮後直接執行，不需要安裝
- 自動偵測 GPU / VRAM
- 依硬體選擇較安全的放大方式
- 支援 2× / 4× / 8× / 18×
- 支援自動判斷、照片、動漫 / 插畫、照片＋文字
- Real-ESRGAN NCNN Vulkan
- 圖片處理可離線執行

## 線上設定

程式之後會讀取兩個公開設定檔：

- `promo.json`：YouTube 推廣文字、按鈕、連結、橫幅
- `version.json`：最新版版本號、下載位置、更新說明

如果沒有網路，或 GitHub 暫時無法連線，程式會使用內建預設值，不影響圖片放大功能。

### promo.json

這個檔案可以直接在 GitHub 上修改，不需要重新打包 EXE。

```json
{
  "enabled": true,
  "title": "最新影片",
  "message": "歡迎到我的 YouTube 頻道看看",
  "button_text": "前往 YouTube",
  "url": "https://www.youtube.com/...",
  "banner_image_url": ""
}
```

### version.json

```json
{
  "latest_version": "1.6",
  "download_url": "",
  "release_notes": "Portable 版本準備中",
  "force_update": false
}
```

## 隱私

圖片放大在使用者自己的電腦上執行。線上設定只讀取公開的推廣與版本資訊，不會上傳圖片。
