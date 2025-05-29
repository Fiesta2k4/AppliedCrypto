import tkinter as tk
from tkinter import font, ttk, messagebox
import sys
import os

# Add parent directories to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from frontend.windows.backup_window import BackupWindow
from frontend.windows.otp_window import OTPWindow  
from frontend.windows.vault_entry_dialog import VaultEntryDialog
from frontend.windows.backup_selection_dialog import BackupSelectionDialog
from frontend.windows.vault_entry_view_dialog import VaultEntryViewDialog
from frontend.windows.share_window import ShareWindow

class MainWindow(tk.Toplevel):
    def __init__(self, master, user_email=None, api_service=None):
        super().__init__(master)
        
        self.api_service = api_service
        self.current_view = "dashboard"
        self.user_email = user_email
        self.vault_entries = []
        
        self.title("Personal Vault")
        self.geometry("900x700")
        self.configure(bg="#f5f5f5")
        self.resizable(True, True)
        self.protocol("WM_DELETE_WINDOW", self.logout)
        self.minsize(800, 600)

        # Fonts
        self.header_font = font.Font(family="Segoe UI", size=20, weight="bold")
        self.sidebar_font = font.Font(family="Segoe UI", size=11)
        self.content_h1 = font.Font(family="Segoe UI", size=18, weight="bold")
        self.content_h2 = font.Font(family="Segoe UI", size=14, weight="bold")
        self.content_txt = font.Font(family="Segoe UI", size=11)

        # Layout
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.create_header()
        self.create_sidebar()
        self.create_content_area()

        self.load_vault_data()
        self.show_dashboard()

    def load_vault_data(self):
        try:
            if self.api_service:
                result = self.api_service.get_vault_entries_decrypted()
                if result and 'entries' in result:
                    self.vault_entries = result['entries']
                else:
                    self.vault_entries = []
            else:
                self.vault_entries = []
        except Exception as e:
            print(f"Failed to load vault data: {e}")
            self.vault_entries = []

    def create_header(self):
        header = tk.Frame(self, bg="#2c3e50", height=60)
        header.grid(row=0, column=0, columnspan=2, sticky="ew")
        header.grid_propagate(False)
        
        tk.Label(header,
                text="🔐 Personal Vault",
                font=self.header_font,
                bg="#2c3e50", fg="white").pack(side="left", padx=20, pady=15)
        
        if self.user_email:
            tk.Label(header,
                    text=f"👤 {self.user_email}",
                    font=self.sidebar_font,
                    bg="#2c3e50", fg="white").pack(side="right", padx=20, pady=15)

    def create_sidebar(self):
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
        nav_items = [
            ("🏠 Dashboard", self.show_dashboard),
            ("🔒 Vault", self.show_vault),
            ("🔗 Share", self.open_share),
            ("📥 Import Backup", self.import_backup),
            ("📤 Export Backup", self.export_backup),
            ("🔑 OTP", self.open_otp),
            ("💾 Recovery", self.open_recovery),
            ("🚪 Logout", self.logout),
        ]
        
        for text, cmd in nav_items:
            btn = tk.Button(sidebar,
                           text=text,
                           font=self.sidebar_font,
                           bg="#e8f5e8",
                           fg="#155724",
                           relief="flat",
                           anchor="w",
                           padx=20,
                           pady=10,
                           command=cmd,
                           cursor="hand2")
            btn.pack(fill="x", padx=5, pady=2)

    def create_content_area(self):
        self.content = tk.Frame(self, bg="white")
        self.content.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)

    def clear_content(self):
        for widget in self.content.winfo_children():
            widget.destroy()

    def show_dashboard(self):
        self.clear_content()
        self.current_view = "dashboard"
        
        tk.Label(self.content,
                text="🏠 Dashboard",
                font=self.content_h1,
                bg="white", fg="#333").pack(anchor="w", pady=(20, 10), padx=20)
        
        # Stats
        stats_frame = tk.Frame(self.content, bg="#f8f9fa", relief="solid", bd=1)
        stats_frame.pack(fill="x", padx=20, pady=20)
        
        tk.Label(stats_frame,
                text="📊 Vault Statistics",
                font=self.content_h2,
                bg="#f8f9fa", fg="#333").pack(anchor="w", padx=15, pady=(15, 5))
        
        entry_count = len(self.vault_entries)
        tk.Label(stats_frame,
                text=f"🔒 Total Entries: {entry_count}",
                font=self.content_txt,
                bg="#f8f9fa", fg="#666").pack(anchor="w", padx=30, pady=5)
        
        tk.Label(stats_frame,
                text=f"👤 User: {self.user_email or 'Unknown'}",
                font=self.content_txt,
                bg="#f8f9fa", fg="#666").pack(anchor="w", padx=30, pady=5)

    def show_vault(self):
        self.clear_content()
        self.current_view = "vault"
        
        tk.Label(self.content,
                text="🔒 Your Vault",
                font=self.content_h1,
                bg="white", fg="#333").pack(anchor="w", pady=(20, 10), padx=20)
        
        # Buttons
        btn_frame = tk.Frame(self.content, bg="white")
        btn_frame.pack(fill="x", padx=20, pady=10)
        
        tk.Button(btn_frame, text="Add Entry", 
                 command=self.add_vault_entry).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Refresh", 
                 command=self.refresh_vault).pack(side="left", padx=5)

        # Vault tree
        tree_frame = tk.Frame(self.content, bg="white")
        tree_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.vault_tree = ttk.Treeview(tree_frame, columns=("Type", "Created"), show="tree headings")
        self.vault_tree.heading("#0", text="Name")
        self.vault_tree.heading("Type", text="Type")
        self.vault_tree.heading("Created", text="Created")
        
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.vault_tree.yview)
        self.vault_tree.configure(yscrollcommand=scrollbar.set)
        
        self.vault_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Populate tree
        for entry in self.vault_entries:
            name = entry.get('metadata', {}).get('name', 'Unnamed')
            entry_type = entry.get('metadata', {}).get('type', 'unknown')
            created = entry.get('created_at', '')[:10]  # Date only
            
            self.vault_tree.insert('', 'end', text=name, values=(entry_type, created), 
                                  tags=(entry['id'],))
        
        # Double-click to view
        self.vault_tree.bind('<Double-1>', lambda e: self.view_selected_entry())

    def refresh_vault(self):
        self.load_vault_data()
        self.show_vault()

    def view_selected_entry(self):
        try:
            selection = self.vault_tree.selection()
            if not selection:
                return
            
            item = selection[0]
            entry_id = self.vault_tree.item(item, 'tags')[0]
            
            # Find entry
            entry = next((e for e in self.vault_entries if e['id'] == entry_id), None)
            if entry:
                VaultEntryViewDialog(self, entry, self.api_service)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to view entry: {str(e)}")

    def add_vault_entry(self):
        dialog = VaultEntryDialog(self, self.api_service)
        self.wait_window(dialog)
        
        if hasattr(dialog, 'result') and dialog.result:
            self.refresh_vault()

    def export_backup(self):
        try:
            if not self.api_service:
                messagebox.showerror("Error", "API service not available")
                return
            
            # Get vault data
            vault_data = self.api_service.get_vault_entries()
            
            if not vault_data or 'entries' not in vault_data:
                messagebox.showerror("Error", "No vault data to backup")
                return
            
            # Create backup
            backup_data = {
                "version": "1.0",
                "backup_type": "full_vault",
                "created_at": self.api_service.crypto_service.__class__.__name__,  # Timestamp
                "entry_count": vault_data['count'],
                "encrypted_entries": vault_data['entries']
            }
            
            from datetime import datetime
            backup_data["created_at"] = datetime.now().isoformat()
            
            result = self.api_service.create_backup(backup_data)
            
            if result and 'backup_id' in result:
                messagebox.showinfo("Success", 
                                  f"Backup created successfully!\n\n"
                                  f"Name: {result.get('name', 'Unnamed')}")
            else:
                error_msg = result.get('error', 'Unknown error') if result else 'Backup failed'
                messagebox.showerror("Error", f"Backup failed: {error_msg}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Backup creation failed: {str(e)}")

    def import_backup(self):
        try:
            BackupSelectionDialog(self, self.api_service)
        except Exception as e:
            messagebox.showerror("Error", f"Import backup failed: {str(e)}")

    def open_otp(self):
        try:
            print("🔍 Opening OTP window...")
            from frontend.windows.otp_window import OTPWindow
            OTPWindow(self, self.api_service)
        except Exception as e:
            print(f"❌ Failed to open OTP window: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Error", f"Failed to open OTP window:\n\n{str(e)}")

    def open_recovery(self):
        try:
            BackupWindow(self, self.api_service)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open backup window: {str(e)}")

    def open_share(self):
        try:
            ShareWindow(self, self.api_service)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open sharing: {str(e)}")

    def logout(self):
        try:
            if self.api_service:
                self.api_service.logout()
            
            self.destroy()
            
            # Show login window again
            from frontend.windows.login_window import LoginWindow
            LoginWindow(self.master)
            
        except Exception as e:
            print(f"Logout error: {e}")
            self.destroy()
