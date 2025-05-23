import tkinter as tk
from tkinter import font
from frontend.windows.backup_window import BackupWindow
from frontend.windows.otp_window import OTPWindow

class MainWindow(tk.Toplevel):
    def __init__(self, master, user_email=None):
        super().__init__(master)
        self.master = master
        self.title("Personal Vault")
        self.geometry("800x600")
        self.configure(bg="#f5f5f5")
        self.resizable(True, True)
        self.protocol("WM_DELETE_WINDOW", self.logout)

        # --- Fonts ---
        self.header_font  = font.Font(family="Segoe UI", size=18, weight="bold")
        self.sidebar_font = font.Font(family="Segoe UI", size=12)
        self.content_h1   = font.Font(family="Segoe UI", size=16, weight="bold")
        self.content_txt  = font.Font(family="Segoe UI", size=12)

        # --- Layout grid ---
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # --- Header ---
        header = tk.Frame(self, bg="#00695c", height=60)
        header.grid(row=0, column=0, columnspan=2, sticky="nsew")
        header.grid_propagate(False)
        tk.Label(header,
                 text="🔐 Personal Vault",
                 fg="white", bg="#00695c",
                 font=self.header_font).place(x=20, y=15)
        if user_email:
            tk.Label(header,
                     text=user_email,
                     fg="#bbdfc8", bg="#00695c",
                     font=self.sidebar_font).place(x=650, y=20)

        # --- Sidebar ---
        sidebar = tk.Frame(self, bg="#eeeeee", width=180)
        sidebar.grid(row=1, column=0, sticky="nsew")
        sidebar.grid_propagate(False)

        # Sidebar buttons
        btn_cfg = dict(font=self.sidebar_font,
                       bg="white", fg="#333",
                       bd=0, relief="flat",
                       anchor="w", padx=12, pady=8,
                       cursor="hand2")
        nav_items = [
            ("Vault",    self.show_vault),
            ("OTP",      self.open_otp),
            ("Share",    self.show_share),
            ("Recovery", self.open_recovery),
            ("Settings", self.show_settings),
            ("Logout",   self.logout),
        ]
        for text, cmd in nav_items:
            btn = tk.Button(sidebar, text=text, command=cmd, **btn_cfg)
            btn.pack(fill="x", pady=2, padx=5)
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg="#ddd"))
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg="white"))

        # --- Content Area ---
        self.content = tk.Frame(self, bg="white", bd=1, relief="solid")
        self.content.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)
        self.clear_content()
        self.default_label = tk.Label(
            self.content,
            text="Select an option from the sidebar",
            font=self.content_txt,
            bg="white", fg="#666"
        )
        self.default_label.pack(expand=True)

    def clear_content(self):
        for w in self.content.winfo_children():
            w.destroy()

    def show_vault(self):
        self.clear_content()
        tk.Label(self.content,
                 text="🔒 Vault Entries",
                 font=self.content_h1,
                 bg="white", fg="#333").pack(anchor="w", pady=(10,5), padx=10)

    def open_otp(self):
        # Simulate real OTP entries (replace with actual decrypted user secrets)
        otp_entries = [
            {"label": "Google", "secret": "JBSWY3DPEHPK3PXP", "digits": 6, "period": 30},
            {"label": "GitHub", "secret": "NB2W45DFOIZA====", "digits": 6, "period": 30},
        ]
        OTPWindow(self, otp_entries)

    def show_share(self):
        self.clear_content()
        tk.Label(self.content,
                 text="📤 Share a Secret",
                 font=self.content_h1,
                 bg="white", fg="#333").pack(anchor="w", pady=(10,5), padx=10)

    def show_settings(self):
        self.clear_content()
        tk.Label(self.content,
                 text="⚙️ Settings",
                 font=self.content_h1,
                 bg="white", fg="#333").pack(anchor="w", pady=(10,5), padx=10)

    def open_recovery(self):
        BackupWindow(self)

    def logout(self):
        self.destroy()
        self.master.deiconify()

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    MainWindow(root, user_email="you@example.com")
    root.mainloop()
