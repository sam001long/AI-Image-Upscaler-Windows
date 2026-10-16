from pathlib import Path

p = Path("macos/buildsrc/BigIMG_macOS_v1_0/app_mac.py")
s = p.read_text(encoding="utf-8")

replacements = [
    ('APP_VERSION = "macOS v1.0 攜帶版"', 'APP_VERSION = "macOS v1.0.1 攜帶版"'),
    ('NETWORK_USER_AGENT = "BigIMG-macOS/1.0"', 'NETWORK_USER_AGENT = "BigIMG-macOS/1.0.1"'),
    ('self.title("BigIMG JPG+PNG+SVG macOS v1.0 攜帶版")',
     'self.title("BigIMG JPG+PNG+SVG macOS v1.0.1 攜帶版")'),
    ('top, text="  JPG+PNG+SVG macOS v1.0 攜帶版",',
     'top, text="  JPG+PNG+SVG macOS v1.0.1 攜帶版",'),
]

for old, new in replacements:
    if old not in s:
        raise SystemExit(f"Missing expected text: {old}")
    s = s.replace(old, new, 1)

old_body = '''        body = ttk.Frame(self, padding=(12, 0, 12, 6))
        body.pack(fill="both", expand=True)

        self.notebook = ttk.Notebook(body)'''
new_body = '''        # macOS fix: keep progress/status directly under the header so
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

p.write_text(s, encoding="utf-8")
print("Applied macOS v1.0.1 progress visibility fix")
