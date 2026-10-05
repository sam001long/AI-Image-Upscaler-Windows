from __future__ import annotations

import os
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
import webbrowser

from core.model_manager import CatalogModel, download_model, import_local_file, load_catalog


class ModelCenter(tk.Toplevel):
    def __init__(self, master, on_changed=None):
        super().__init__(master)
        self.title("BigIMG Generate — 模型中心")
        self.geometry("760x500")
        self.minsize(680, 420)
        self.on_changed = on_changed
        self.models = load_catalog()

        root = ttk.Frame(self, padding=14)
        root.pack(fill="both", expand=True)

        ttk.Label(root, text="模型中心", font=("Segoe UI", 17, "bold")).pack(anchor="w")
        ttk.Label(
            root,
            text="官方推薦可用 BigIMG 鏡像或原始來源；第三方模型也可直接加入本機。",
        ).pack(anchor="w", pady=(0, 12))

        self.tree = ttk.Treeview(root, columns=("family", "size", "status"), show="headings", height=12)
        self.tree.heading("family", text="家族")
        self.tree.heading("size", text="大小")
        self.tree.heading("status", text="狀態")
        self.tree.column("family", width=100, anchor="center")
        self.tree.column("size", width=100, anchor="center")
        self.tree.column("status", width=170, anchor="center")
        self.tree.pack(fill="both", expand=True)

        self.name_by_iid = {}
        for i, model in enumerate(self.models):
            iid = str(i)
            self.name_by_iid[iid] = model.name
            size = f"{model.size_gb:.2f} GB" if model.size_gb is not None else "—"
            status = "已安裝" if model.destination.exists() else "未安裝"
            self.tree.insert("", "end", iid=iid, values=(model.family, size, status), text=model.name)

        self.detail_var = tk.StringVar(value="選擇一個模型")
        ttk.Label(root, textvariable=self.detail_var, wraplength=700).pack(anchor="w", pady=(10, 6))
        self.tree.bind("<<TreeviewSelect>>", self._selection_changed)

        actions = ttk.Frame(root)
        actions.pack(fill="x", pady=(4, 0))
        ttk.Button(actions, text="下載（優先 BigIMG 鏡像）", command=lambda: self.start_download(True)).pack(side="left")
        ttk.Button(actions, text="原始來源下載", command=lambda: self.start_download(False)).pack(side="left", padx=(6, 0))
        ttk.Button(actions, text="開啟來源頁", command=self.open_source_page).pack(side="left", padx=(6, 0))
        ttk.Button(actions, text="加入本機模型", command=self.import_local).pack(side="right")

        self.progress = ttk.Progressbar(root, mode="determinate", maximum=100)
        self.progress.pack(fill="x", pady=(10, 0))
        self.status_var = tk.StringVar(value="準備完成")
        ttk.Label(root, textvariable=self.status_var).pack(anchor="w", pady=(4, 0))

    def _selected(self) -> CatalogModel | None:
        selected = self.tree.selection()
        if not selected:
            return None
        idx = int(selected[0])
        return self.models[idx]

    def _selection_changed(self, _event=None):
        model = self._selected()
        if not model:
            return
        source = "BigIMG 鏡像可用" if model.mirror_url else "未設定 BigIMG 鏡像"
        self.detail_var.set(
            f"{model.name}｜{model.kind}｜{model.family}｜{source}｜"
            f"{model.license_note or ''}"
        )

    def open_source_page(self):
        model = self._selected()
        if not model or not model.source_page:
            messagebox.showinfo("沒有來源頁", "這個項目沒有設定來源頁。")
            return
        webbrowser.open(model.source_page)

    def start_download(self, prefer_mirror: bool):
        model = self._selected()
        if not model:
            messagebox.showinfo("尚未選擇", "請先選擇一個模型。")
            return
        self.status_var.set("開始下載…")
        self.progress["value"] = 0
        threading.Thread(target=self._download_worker, args=(model, prefer_mirror), daemon=True).start()

    def _download_worker(self, model: CatalogModel, prefer_mirror: bool):
        try:
            path = download_model(model, prefer_mirror, self._report_progress)
            self.after(0, self._download_done, model, path)
        except Exception as exc:
            self.after(0, lambda: messagebox.showerror("下載失敗", str(exc)))
            self.after(0, lambda: self.status_var.set("下載失敗"))

    def _report_progress(self, done: int, total: int | None):
        if total:
            pct = min(100, done * 100 / total)
            self.after(0, lambda: self.progress.configure(value=pct))
            self.after(0, lambda: self.status_var.set(f"下載中 {pct:.1f}%"))
        else:
            mb = done / (1024 * 1024)
            self.after(0, lambda: self.status_var.set(f"下載中 {mb:.0f} MB"))

    def _download_done(self, model: CatalogModel, path: Path):
        self.progress["value"] = 100
        self.status_var.set(f"已安裝：{path.name}")
        selected = self.tree.selection()
        if selected:
            values = list(self.tree.item(selected[0], "values"))
            values[2] = "已安裝"
            self.tree.item(selected[0], values=values)
        if self.on_changed:
            self.on_changed()

    def import_local(self):
        path = filedialog.askopenfilename(
            filetypes=[
                ("模型檔", "*.safetensors;*.ckpt;*.bin;*.pth"),
                ("所有檔案", "*.*"),
            ]
        )
        if not path:
            return

        kind = tk.StringVar(value="checkpoints/sd15")
        dialog = tk.Toplevel(self)
        dialog.title("選擇模型類型")
        dialog.transient(self)
        dialog.grab_set()
        ttk.Label(dialog, text="要放到哪個模型資料夾？", padding=10).pack()
        combo = ttk.Combobox(
            dialog,
            textvariable=kind,
            state="readonly",
            values=[
                "checkpoints/sd15",
                "checkpoints/sdxl",
                "lora",
                "vae",
                "controlnet/sd15",
                "controlnet/sdxl",
                "ipadapter/sd15",
                "ipadapter/sdxl",
            ],
            width=28,
        )
        combo.pack(padx=10, pady=(0, 10))

        def confirm():
            try:
                dest = import_local_file(path, kind.get())
                dialog.destroy()
                self.status_var.set(f"已加入：{dest.name}")
                if self.on_changed:
                    self.on_changed()
            except Exception as exc:
                messagebox.showerror("匯入失敗", str(exc))

        ttk.Button(dialog, text="加入", command=confirm).pack(pady=(0, 10))
