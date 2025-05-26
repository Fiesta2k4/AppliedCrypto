import tkinter as tk
from tkinter import font, ttk, messagebox
import sys
import os

# Add parent directories to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

try:
    from frontend.windows.backup_window import BackupWindow
    from frontend.windows.otp_window import OTPWindow
    from frontend.services.api_service import ApiService
except ImportError as e:
    print(f"Warning: Could not import modules: {e}")
    BackupWindow = None
    OTPWindow = None
    ApiService = None

class MainWindow(tk.Toplevel):
    def __init__(self, master, user_email=None, api_service=None):
        super().__init__(master)
        self.master = master
        self.user_email = user_email
        self.api_service = api_service or (ApiService() if ApiService else None)
        
        self.title("Personal Vault")
        self.geometry("900x700")
        self.configure(bg="#f5f5f5")
        self.resizable(True, True)
        self.protocol("WM_DELETE_WINDOW", self.logout)
        self.minsize(800, 600)

        # --- Fonts ---
        self.header_font = font.Font(family="Segoe UI", size=20, weight="bold")
        self.sidebar_font = font.Font(family="Segoe UI", size=11)
        self.content_h1 = font.Font(family="Segoe UI", size=18, weight="bold")
        self.content_h2 = font.Font(family="Segoe UI", size=14, weight="bold")
        self.content_txt = font.Font(family="Segoe UI", size=11)

        # --- Layout grid ---
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Load initial data
        self.vault_entries = []
        self.load_vault_data()

        self.create_header()
        self.create_sidebar()
        self.create_content_area()
        self.show_dashboard()

    def load_vault_data(self):
        """Load and decrypt vault data from API"""
        if self.api_service:
            result = self.api_service.get_vault_entries_decrypted()
            if result and 'entries' in result:
                self.vault_entries = result['entries']
            else:
                self.vault_entries = []

    def create_header(self):
        """Tạo header với thiết kế cải tiến"""
        header = tk.Frame(self, bg="#00695c", height=70)
        header.grid(row=0, column=0, columnspan=2, sticky="nsew")
        header.grid_propagate(False)
        
        # Title
        title_label = tk.Label(header,
                              text="🔐 Personal Vault",
                              fg="white", bg="#00695c",
                              font=self.header_font)
        title_label.place(x=20, y=20)
        
        # User info
        if self.user_email:
            user_frame = tk.Frame(header, bg="#00695c")
            user_frame.place(x=600, y=15)
            
            tk.Label(user_frame,
                    text="Welcome,",
                    fg="#bbdfc8", bg="#00695c",
                    font=font.Font(family="Segoe UI", size=10)).pack()
            
            tk.Label(user_frame,
                    text=self.user_email,
                    fg="white", bg="#00695c",
                    font=font.Font(family="Segoe UI", size=12, weight="bold")).pack()

    def create_sidebar(self):
        """Tạo sidebar với thiết kế cải tiến"""
        sidebar = tk.Frame(self, bg="#e8f5e8", width=200)
        sidebar.grid(row=1, column=0, sticky="nsew")
        sidebar.grid_propagate(False)

        # Sidebar title
        title_frame = tk.Frame(sidebar, bg="#d4edda", height=40)
        title_frame.pack(fill="x", pady=(0, 10))
        title_frame.pack_propagate(False)
        
        tk.Label(title_frame,
                text="Navigation",
                font=font.Font(family="Segoe UI", size=12, weight="bold"),
                bg="#d4edda", fg="#155724").pack(pady=10)

        # Navigation buttons
        self.nav_buttons = {}
        nav_items = [
            ("🏠 Dashboard", self.show_dashboard),
            ("🔒 Vault", self.show_vault),
            ("🔑 OTP", self.open_otp),
            ("📤 Share", self.show_share),
            ("💾 Recovery", self.open_recovery),
            ("⚙️ Settings", self.show_settings),
            ("🚪 Logout", self.logout),
        ]
        
        for text, cmd in nav_items:
            btn = tk.Button(sidebar, 
                          text=text, 
                          command=cmd,
                          font=self.sidebar_font,
                          bg="white", 
                          fg="#333",
                          bd=1, 
                          relief="solid",
                          anchor="w", 
                          padx=15, 
                          pady=10,
                          cursor="hand2")
            btn.pack(fill="x", pady=2, padx=8)
            
            # Hover effects
            btn.bind("<Enter>", lambda e, b=btn: self.on_button_hover(b, True))
            btn.bind("<Leave>", lambda e, b=btn: self.on_button_hover(b, False))
            
            self.nav_buttons[text] = btn

    def create_content_area(self):
        """Tạo content area"""
        self.content = tk.Frame(self, bg="white", bd=2, relief="groove")
        self.content.grid(row=1, column=1, sticky="nsew", padx=15, pady=15)

    def on_button_hover(self, button, is_enter):
        """Xử lý hover effect cho buttons"""
        if is_enter:
            button.config(bg="#00695c", fg="white")
        else:
            button.config(bg="white", fg="#333")

    def clear_content(self):
        """Xóa nội dung content area"""
        for widget in self.content.winfo_children():
            widget.destroy()

    def show_dashboard(self):
        """Hiển thị dashboard với dữ liệu thực"""
        self.clear_content()
        
        # Title
        tk.Label(self.content,
                text="🏠 Dashboard",
                font=self.content_h1,
                bg="white", fg="#333").pack(anchor="w", pady=(20, 10), padx=20)
        
        # Welcome message
        welcome_text = f"Welcome back, {self.user_email}!" if self.user_email else "Welcome to Personal Vault!"
        tk.Label(self.content,
                text=welcome_text,
                font=self.content_h2,
                bg="white", fg="#666").pack(anchor="w", pady=(0, 20), padx=20)
        
        # Quick stats frame
        stats_frame = tk.Frame(self.content, bg="white")
        stats_frame.pack(fill="x", padx=20, pady=10)
        
        # Real stats from API
        vault_count = len(self.vault_entries)
        otp_count = len([e for e in self.vault_entries if e.get('metadata', {}).get('type') == 'otp'])
        shared_count = 0  # Will be implemented with share module
        
        self.create_stat_card(stats_frame, "🔒", "Vault Entries", str(vault_count), 0)
        self.create_stat_card(stats_frame, "🔑", "OTP Codes", str(otp_count), 1)
        self.create_stat_card(stats_frame, "📤", "Shared Items", str(shared_count), 2)

    def create_stat_card(self, parent, icon, title, value, column):
        """Tạo thẻ thống kê"""
        card = tk.Frame(parent, bg="#f8f9fa", bd=1, relief="solid")
        card.grid(row=0, column=column, padx=10, pady=5, sticky="ew")
        parent.grid_columnconfigure(column, weight=1)
        
        tk.Label(card, text=icon, font=font.Font(size=24), bg="#f8f9fa").pack(pady=(10, 5))
        tk.Label(card, text=title, font=self.sidebar_font, bg="#f8f9fa", fg="#666").pack()
        tk.Label(card, text=value, font=self.content_h1, bg="#f8f9fa", fg="#00695c").pack(pady=(0, 10))

    def show_vault(self):
        """Hiển thị vault entries với dữ liệu đã giải mã"""
        self.clear_content()
        tk.Label(self.content,
                text="🔒 Vault Entries",
                font=self.content_h1,
                bg="white", fg="#333").pack(anchor="w", pady=(20, 10), padx=20)
        
        # Refresh data
        self.load_vault_data()
        
        # Create treeview for entries
        tree_frame = tk.Frame(self.content, bg="white")
        tree_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Treeview with more columns
        columns = ("Name", "Type", "Username", "URL", "Created")
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings")
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120)
        
        # Add decrypted entries to tree
        for entry in self.vault_entries:
            metadata = entry.get('metadata', {})
            decrypted_data = entry.get('decrypted_data', {})
            
            tree.insert("", "end", values=(
                decrypted_data.get('name', metadata.get('name', 'Unnamed')),
                metadata.get('type', 'Unknown'),
                decrypted_data.get('username', 'N/A'),
                decrypted_data.get('url', 'N/A'),
                entry.get('created_at', 'N/A')[:10]
            ))
        
        tree.pack(fill="both", expand=True)
        
        # Action buttons
        btn_frame = tk.Frame(self.content, bg="white")
        btn_frame.pack(fill="x", padx=20, pady=10)
        
        tk.Button(btn_frame, text="Add Entry", 
                 command=self.add_vault_entry).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Refresh", 
                 command=self.show_vault).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Export Backup", 
                 command=self.export_backup).pack(side="left", padx=5)

    def add_vault_entry(self):
        """Add new encrypted vault entry"""
        dialog = VaultEntryDialog(self, self.api_service)
        self.wait_window(dialog)
        
        # Refresh after adding
        if dialog.result:
            self.show_vault()

    def open_otp(self):
        """Mở OTP window"""
        otp_entries = [
            {"label": "Google", "secret": "JBSWY3DPEHPK3PXP", "digits": 6, "period": 30},
            {"label": "GitHub", "secret": "NB2W45DFOIZA====", "digits": 6, "period": 30},
            {"label": "Microsoft", "secret": "GEZDGNBVGY3TQOJQ", "digits": 6, "period": 30},
        ]
        OTPWindow(self, otp_entries)

    def show_share(self):
        """Hiển thị share interface"""
        self.clear_content()
        tk.Label(self.content,
                text="📤 Share a Secret",
                font=self.content_h1,
                bg="white", fg="#333").pack(anchor="w", pady=(20, 10), padx=20)
        
        tk.Label(self.content,
                text="Securely share encrypted data with others.",
                font=self.content_txt,
                bg="white", fg="#666").pack(anchor="w", padx=20)

    def show_settings(self):
        """Hiển thị settings"""
        self.clear_content()
        tk.Label(self.content,
                text="⚙️ Settings",
                font=self.content_h1,
                bg="white", fg="#333").pack(anchor="w", pady=(20, 10), padx=20)
        
        tk.Label(self.content,
                text="Configure your vault settings here.",
                font=self.content_txt,
                bg="white", fg="#666").pack(anchor="w", padx=20)

    def open_recovery(self):
        """Mở recovery window"""
        if BackupWindow:
            BackupWindow(self)

    def logout(self):
        """Đăng xuất"""
        self.destroy()
        if self.master:
            self.master.deiconify()

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    
    # Create API service
    api_service = ApiService() if ApiService else None
    
    main_window = MainWindow(root, user_email="user@example.com", api_service=api_service)
    root.mainloop()
