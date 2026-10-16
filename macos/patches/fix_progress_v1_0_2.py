from pathlib import Path

p = Path("macos/buildsrc/BigIMG_macOS_v1_0/app_mac.py")
s = p.read_text(encoding="utf-8")

replacements = [
    ('APP_VERSION = "macOS v1.0 攜帶版"', 'APP_VERSION = "macOS v1.0.2 攜帶版"'),
    ('NETWORK_USER_AGENT = "BigIMG-macOS/1.0"', 'NETWORK_USER_AGENT = "BigIMG-macOS/1.0.2"'),
    ('self.title("BigIMG JPG+PNG+SVG macOS v1.0 攜帶版")',
     'self.title("BigIMG JPG+PNG+SVG macOS v1.0.2 攜帶版")'),
    ('top, text="  JPG+PNG+SVG macOS v1.0 攜帶版",',
     'top, text="  JPG+PNG+SVG macOS v1.0.2 攜帶版",'),
]

for old, new in replacements:
    if old not in s:
        raise SystemExit(f"Missing expected text: {old}")
    s = s.replace(old, new, 1)

old_body = '''        body = ttk.Frame(self, padding=(12, 0, 12, 6))
        body.pack(fill="both", expand=True)

        self.notebook = ttk.Notebook(body)'''
new_body = '''        # macOS: keep progress/status directly under the header so
        # Aqua/Tk layout cannot push it below the visible window.
        progress_panel = ttk.Frame(self, padding=(12, 0, 12, 6))
        progress_panel.pack(fill="x")
        self.progress_bar = ttk.Progressbar(
            progress_panel, orient="horizontal", mode="determinate",
            maximum=100, variable=self.progress_var, length=520
        )
        self.progress_bar.pack(fill="x", ipady=3)
        ttk.Label(progress_panel, textvariable=self.status_var).pack(anchor="w", pady=(4, 0))
        ttk.Label(
            progress_panel,
            text="處理中會持續更新進度與運算時間。",
            font=("Arial", 8)
        ).pack(anchor="w", pady=(1, 0))

        body = ttk.Frame(self, padding=(12, 0, 12, 6))
        body.pack(fill="both", expand=True)

        self.notebook = ttk.Notebook(body)'''
if old_body not in s:
    raise SystemExit("Missing body layout anchor")
s = s.replace(old_body, new_body, 1)

old_bottom = '''        bottom = ttk.Frame(self, padding=(12, 0, 12, 8))
        self.bottom_frame = bottom
        bottom.pack(fill="x")
        ttk.Progressbar(bottom, maximum=100, variable=self.progress_var).pack(fill="x")
        ttk.Label(bottom, textvariable=self.status_var).pack(anchor="w", pady=(4, 0))
        ttk.Label(
            bottom,
            text="處理中會持續更新進度與運算時間。",
            font=("Microsoft JhengHei UI", 8)
        ).pack(anchor="w", pady=(1, 0))

        action_row = ttk.Frame(bottom)'''
new_bottom = '''        bottom = ttk.Frame(self, padding=(12, 0, 12, 8))
        self.bottom_frame = bottom
        bottom.pack(fill="x")

        action_row = ttk.Frame(bottom)'''
if old_bottom not in s:
    raise SystemExit("Missing bottom layout anchor")
s = s.replace(old_bottom, new_bottom, 1)

old_done = '''                elif kind == "done":
                    self.progress_var.set(100)
                    self.status_var.set(f"完成：{payload}")
                    self.start_btn.config(state="normal")
                    self.cancel_btn.config(state="disabled")
                    self.open_output_btn.config(state="normal")
                    messagebox.showinfo("完成", "圖片放大完成。")'''
new_done = '''                elif kind == "done":
                    self.progress_var.set(100)
                    self.status_var.set(f"完成：{payload}")
                    self.start_btn.config(state="normal")
                    self.cancel_btn.config(state="disabled")
                    self.open_output_btn.config(state="normal")
                    # macOS Aqua may not repaint widgets before a modal messagebox.
                    # Force the 100% state to paint first, then show the dialog.
                    self.update_idletasks()
                    self.after(120, lambda: messagebox.showinfo("完成", "圖片放大完成。"))'''
if old_done not in s:
    raise SystemExit("Missing done handler anchor")
s = s.replace(old_done, new_done, 1)

old_svg_call = '                    messagebox.showinfo("完成", msg)'
new_svg_call = '''                    self.update_idletasks()
                    self.after(120, lambda m=msg: messagebox.showinfo("完成", m))'''
if old_svg_call not in s:
    raise SystemExit("Missing SVG completion call")
s = s.replace(old_svg_call, new_svg_call, 1)

p.write_text(s, encoding="utf-8")
print("Applied macOS v1.0.2 progress repaint fix")
