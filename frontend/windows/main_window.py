import tkinter as tk
from tkinter import font, ttk, messagebox
import sys
import os
from datetime import datetime

# Add parent directories to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

try:
    from frontend.windows.backup_window import BackupWindow
    from frontend.windows.otp_window import OTPWindow
    from frontend.services.api_service import ApiService
    from frontend.windows.vault_entry_dialog import VaultEntryDialog
    from frontend.windows.backup_selection_dialog import BackupSelectionDialog
    from frontend.windows.vault_entry_view_dialog import VaultEntryViewDialog
except ImportError as e:
    print(f"Warning: Could not import modules: {e}")
    BackupWindow = None
    OTPWindow = None
    ApiService = None
    VaultEntryDialog = None
    BackupSelectionDialog = None
    VaultEntryViewDialog = None

class MainWindow(tk.Toplevel):
    def __init__(self, master, user_email=None, api_service=None):
        super().__init__(master)
        
        print("🔍 === MAIN WINDOW INIT ===")
        print(f"🔍 Passed api_service: {api_service}")
        print(f"🔍 Passed api_service token: {getattr(api_service, 'access_token', 'NOT FOUND') if api_service else 'NO API SERVICE'}")
        
        # ✅ CRITICAL: Always use the passed API service - NEVER create new one!
        if api_service is not None:
            # Use passed api_service (from login flow)
            self.api_service = api_service
            print(f"✅ Using passed API service: {self.api_service}")
            print(f"✅ API service token: {self.api_service.access_token}")
        else:
            # ❌ ERROR: If no API service passed, this is an error!
            print("❌ CRITICAL ERROR: No API service passed to MainWindow!")
            messagebox.showerror("Error", "No API service available. Please restart application.")
            self.destroy()
            return
        
        print(f"🔍 Final API service: {self.api_service}")
        print(f"🔍 Final API service token: {getattr(self.api_service, 'access_token', 'NOT FOUND')}")
        
        # Test API immediately
        print("🔍 Testing API in MainWindow...")
        test_result = self.api_service.get_profile()
        print(f"🔍 Profile test in MainWindow: {test_result}")
        
        # Initialize other attributes
        self.current_view = "dashboard"
        self.user_email = user_email
        self.vault_entries = []
        
        # Rest of initialization...
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

        self.create_header()
        self.create_sidebar()
        self.create_content_area()

        # Load initial data AFTER UI is created
        self.load_vault_data()
        self.show_dashboard()
        
        print("✅ Main window initialized successfully")

    def load_vault_data(self):
        """Load vault data from API"""
        try:
            print("🔍 === LOAD VAULT DATA ===")
            print(f"🔍 API service: {self.api_service}")
            print(f"🔍 API service token: {getattr(self.api_service, 'access_token', 'NOT FOUND')}")
            
            if not self.api_service:
                print("❌ No API service available!")
                return
            
            if not getattr(self.api_service, 'access_token', None):
                print("❌ No access token available!")
                return
            
            print("🔍 Calling get_vault_entries_decrypted...")
            
            # Get decrypted vault entries
            vault_response = self.api_service.get_vault_entries_decrypted()
            
            print(f"🔍 Vault response: {vault_response}")
            
            if vault_response and 'entries' in vault_response:
                self.vault_entries = vault_response['entries']
                print(f"✅ Loaded {len(self.vault_entries)} decrypted entries")
            else:
                print("❌ Failed to load vault entries")
                self.vault_entries = []
        
        except Exception as e:
            print(f"❌ Load vault data error: {e}")
            import traceback
            traceback.print_exc()
            self.vault_entries = []

    def create_header(self):
        """Create header"""
        header = tk.Frame(self, bg="#2c3e50", height=60)
        header.grid(row=0, column=0, columnspan=2, sticky="ew")
        header.grid_propagate(False)
        
        # App title
        tk.Label(header,
                text="🔐 Personal Vault",
                font=self.header_font,
                bg="#2c3e50", fg="white").pack(side="left", padx=20, pady=15)
        
        # User info
        if self.user_email:
            tk.Label(header,
                    text=f"👤 {self.user_email}",
                    font=self.sidebar_font,
                    bg="#2c3e50", fg="#ecf0f1").pack(side="right", padx=20, pady=15)

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

        # Navigation buttons - ADD IMPORT BACKUP HERE
        self.nav_buttons = {}
        nav_items = [
            ("🏠 Dashboard", self.show_dashboard),
            ("🔒 Vault", self.show_vault),
            ("📥 Import Backup", self.import_backup),  # ✅ Add this
            ("📤 Export Backup", self.export_backup),   # ✅ Add this
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
        """Create main content area"""
        self.content = tk.Frame(self, bg="white")
        self.content.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)

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
        """Show dashboard"""
        self.clear_content()
        self.current_view = "dashboard"
        
        # Title
        tk.Label(self.content,
                text="🏠 Dashboard",
                font=self.content_h1,
                bg="white", fg="#333").pack(anchor="w", pady=(20, 10), padx=20)
        
        # Vault stats
        stats_frame = tk.Frame(self.content, bg="#f8f9fa", relief="solid", bd=1)
        stats_frame.pack(fill="x", padx=20, pady=20)
        
        tk.Label(stats_frame,
                text="📊 Vault Statistics",
                font=self.content_h2,
                bg="#f8f9fa", fg="#333").pack(anchor="w", padx=15, pady=(15, 5))
        
        # Entry count
        entry_count = len(self.vault_entries) if self.vault_entries else 0
        tk.Label(stats_frame,
                text=f"🔒 Total Entries: {entry_count}",
                font=self.content_txt,
                bg="#f8f9fa", fg="#666").pack(anchor="w", padx=30, pady=5)
        
        tk.Label(stats_frame,
                text=f"👤 User: {self.user_email or 'Unknown'}",
                font=self.content_txt,
                bg="#f8f9fa", fg="#666").pack(anchor="w", padx=30, pady=5)
        
        tk.Label(stats_frame, text="", bg="#f8f9fa").pack(pady=10)

    def show_vault(self):
        """Show vault entries"""
        self.clear_content()
        self.current_view = "vault"
        
        # Title
        tk.Label(self.content,
                text="🔒 Your Vault",
                font=self.content_h1,
                bg="white", fg="#333").pack(anchor="w", pady=(20, 10), padx=20)
        
        # Vault entries list
        if self.vault_entries:
            for i, entry in enumerate(self.vault_entries):
                entry_frame = tk.Frame(self.content, bg="#f9f9f9", relief="solid", bd=1)
                entry_frame.pack(fill="x", padx=20, pady=5)
                
                decrypted = entry.get('decrypted_data', {})
                entry_name = decrypted.get('name', 'Unnamed Entry')
                entry_type = decrypted.get('type', 'Unknown')
                
                tk.Label(entry_frame,
                        text=f"🔑 {entry_name} ({entry_type})",
                        font=self.content_txt,
                        bg="#f9f9f9", fg="#333").pack(anchor="w", padx=15, pady=10)
        else:
            tk.Label(self.content,
                    text="No entries found. Create your first entry!",
                    font=self.content_txt,
                    bg="white", fg="#666").pack(anchor="w", padx=20, pady=20)

        # Action buttons
        btn_frame = tk.Frame(self.content, bg="white")
        btn_frame.pack(fill="x", padx=20, pady=10)
        
        tk.Button(btn_frame, text="Add Entry", 
                 command=self.add_vault_entry).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Refresh", 
                 command=self.show_vault).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Export Backup", 
                 command=self.export_backup).pack(side="left", padx=5)

        # Create tree frame and tree widget
        tree_frame = tk.Frame(self.content, bg="white")
        tree_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Create tree widget
        self.vault_tree = ttk.Treeview(tree_frame, columns=("Type", "Created", "Modified"), show="tree headings")
        self.vault_tree.heading("#0", text="Name")
        self.vault_tree.heading("Type", text="Type")
        self.vault_tree.heading("Created", text="Created")
        self.vault_tree.heading("Modified", text="Modified")
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.vault_tree.yview)
        self.vault_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack tree and scrollbar
        self.vault_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Populate tree with vault entries
        for entry in self.vault_entries:
            decrypted = entry.get('decrypted_data', {})
            entry_name = decrypted.get('name', 'Unnamed Entry')
            entry_type = decrypted.get('type', 'Unknown')
            entry_id = entry.get('id', '')
            
            self.vault_tree.insert("", "end", text=entry_name, 
                                 values=(entry_type, "N/A", "N/A"),
                                 tags=(entry_id,))
        
        # Create vault tree with view functionality
        self.create_vault_tree(tree_frame)

    def create_vault_tree(self, parent):
        """Create vault entries tree with view functionality"""
        # Add double-click binding
        self.vault_tree.bind('<Double-1>', lambda e: self.view_selected_entry())
        
        # Add right-click context menu
        def show_context_menu(event):
            try:
                # Select item under cursor
                item = self.vault_tree.identify_row(event.y)
                if item:
                    self.vault_tree.selection_set(item)
                    
                    # Create context menu
                    context_menu = tk.Menu(self, tearoff=0)
                    context_menu.add_command(label="👁️ View Details", command=self.view_selected_entry)
                    context_menu.add_command(label="✏️ Edit Entry", command=self.edit_selected_entry)
                    context_menu.add_separator()
                    context_menu.add_command(label="🗑️ Delete Entry", command=self.delete_selected_entry)
                    
                    # Show menu
                    context_menu.tk_popup(event.x_root, event.y_root)
            except Exception as e:
                print(f"Context menu error: {e}")
        
        self.vault_tree.bind('<Button-3>', show_context_menu)  # Right-click

    def view_selected_entry(self):
        """View selected vault entry details"""
        try:
            # Get selected item from vault tree
            selection = self.vault_tree.selection()
            if not selection:
                messagebox.showwarning("No Selection", "Please select an entry to view")
                return
            
            # Get entry ID from selection tags
            item = selection[0]
            item_tags = self.vault_tree.item(item, 'tags')
            
            print(f"🔍 Debug - Item tags: {item_tags}")  # Debug info
            
            if not item_tags or len(item_tags) == 0:
                messagebox.showerror("Error", "Could not determine entry ID - no tags found")
                return
            
            entry_id = item_tags[0]  # Get first tag (which is entry ID)
            
            print(f"🔍 Debug - Entry ID: {entry_id}")  # Debug info
            
            if not entry_id:
                messagebox.showerror("Error", "Entry ID is empty")
                return
            
            # Find the entry in our loaded data
            selected_entry = None
            for entry in self.vault_entries:
                if entry.get('id') == entry_id:
                    selected_entry = entry
                    break
            
            print(f"🔍 Debug - Found entry: {selected_entry is not None}")  # Debug info
            
            if not selected_entry:
                # Try to get the raw entry (without decrypted data)
                selected_entry = self.find_raw_entry_by_id(entry_id)
                
                if not selected_entry:
                    messagebox.showerror("Error", f"Entry not found in loaded data (ID: {entry_id})")
                    return
            
            print(f"🔍 Opening view dialog for entry: {selected_entry.get('metadata', {}).get('name', 'unknown')}")
            
            # Open view dialog
            from .vault_entry_view_dialog import VaultEntryViewDialog
            view_dialog = VaultEntryViewDialog(self, selected_entry, self.api_service)
            
            print(f"✅ View dialog created successfully")
            
        except Exception as e:
            print(f"❌ View entry error: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Error", f"Failed to view entry:\n\n{str(e)}")

    def find_raw_entry_by_id(self, entry_id):
        """Find raw entry by ID from API"""
        try:
            if not self.api_service:
                return None
            
            # Get raw entries from API
            result = self.api_service.get_vault_entries()
            if result and 'entries' in result:
                for entry in result['entries']:
                    if entry.get('id') == entry_id:
                        return entry
            return None
            
        except Exception as e:
            print(f"❌ Find raw entry error: {e}")
            return None

    def add_vault_entry(self):
        """Add new encrypted vault entry"""
        dialog = VaultEntryDialog(self, self.api_service)
        self.wait_window(dialog)
        
        # Refresh after adding
        if dialog.result:
            self.show_vault()

    def logout(self):
        """Logout user and return to login window"""
        try:
            print("🔍 === LOGOUT ===")
            
            # Clear API service tokens
            if self.api_service:
                print("🔍 Clearing API service tokens...")
                self.api_service.logout()
            
            # Clear sensitive data
            self.vault_entries = []
            self.user_email = None
            
            print("✅ Logout completed successfully")
            
            # Close main window
            self.destroy()
            
        except Exception as e:
            print(f"❌ Logout error: {e}")
            import traceback
            traceback.print_exc()
            # Force close even if error
            self.destroy()

    def export_backup(self):
        """Export/Create backup"""
        try:
            print("🔍 === EXPORT BACKUP ===")
            
            if not self.api_service:
                messagebox.showerror("Error", "API service not available")
                return
            
            if not self.vault_entries:
                messagebox.showinfo("No Data", "Your vault is empty. Add some entries first.")
                return
            
            # Get vault data for backup
            vault_data = self.api_service.get_vault_entries()
            
            if not vault_data or 'entries' not in vault_data:
                messagebox.showerror("Error", "Failed to get vault data for backup")
                return
            
            # Create backup
            backup_name = f"Backup {datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            backup_data = {
                'version': '1.0',
                'backup_type': 'vault_export',
                'created_at': datetime.now().isoformat(),
                'entry_count': len(vault_data['entries']),
                'encrypted_entries': vault_data['entries']
            }
            
            result = self.api_service.create_backup(backup_data, backup_name)
            
            if result and result.get('backup_id'):
                messagebox.showinfo("Backup Created", 
                                  f"Backup created successfully!\n\n"
                                  f"Name: {backup_name}\n"
                                  f"Entries: {len(vault_data['entries'])}\n"
                                  f"Backup ID: {result['backup_id']}")
            else:
                error_msg = result.get('error', 'Unknown error') if result else 'Failed to create backup'
                messagebox.showerror("Backup Failed", f"Failed to create backup:\n\n{error_msg}")
        
        except Exception as e:
            print(f"❌ Export backup error: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Error", f"Export backup failed:\n\n{str(e)}")

    def import_backup(self):
        """Import backup dialog with detailed debugging"""
        try:
            print("🔍 === IMPORT BACKUP CALLED ===")
            print(f"🔍 self.api_service: {self.api_service}")
            print(f"🔍 self.api_service type: {type(self.api_service)}")
            print(f"🔍 self.api_service is None: {self.api_service is None}")
            
            if not self.api_service:
                print("❌ API service is None in import_backup!")
                messagebox.showerror("Error", "API service not available. Please restart the application.")
                return
            
            # Check if user is logged in
            if not getattr(self.api_service, 'access_token', None):
                print("❌ User not logged in!")
                messagebox.showerror("Error", "Please login first before importing backups.")
                return
            
            print("🔍 Importing BackupSelectionDialog...")
            from .backup_selection_dialog import BackupSelectionDialog
            
            print("🔍 Creating BackupSelectionDialog...")
            print(f"🔍 Passing parent: {self}")
            print(f"🔍 Passing api_service: {self.api_service}")
            
            dialog = BackupSelectionDialog(self, self.api_service)
            
            print("🔍 Waiting for dialog...")
            self.wait_window(dialog)
            
            # Refresh vault data if import was successful
            if hasattr(dialog, 'import_successful') and dialog.import_successful:
                print("🔄 Refreshing vault after import...")
                self.load_vault_data()
                
                # If currently showing vault, refresh the display
                if hasattr(self, 'vault_tree'):
                    self.show_vault()
                
                messagebox.showinfo("Import Complete", 
                                  "Backup imported successfully!\n\n"
                                  "Your vault has been updated with the imported entries.")
        
        except Exception as e:
            print(f"❌ Import backup error: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Error", f"Import failed:\n\n{str(e)}")

    def open_otp(self):
        """Open OTP management"""
        try:
            messagebox.showinfo("OTP", "OTP feature coming soon!")
        except Exception as e:
            print(f"❌ OTP error: {e}")
            messagebox.showerror("Error", f"OTP error:\n\n{str(e)}")

    def show_share(self):
        """Show share management interface"""
        self.clear_content()
        self.current_view = "share"
        
        # Title
        tk.Label(self.content,
                text="📤 Secret Sharing",
                font=self.content_h1,
                bg="white", fg="#333").pack(anchor="w", pady=(20, 10), padx=20)
        
        # Description
        tk.Label(self.content,
                text="Share encrypted secrets with other vault users securely.",
                font=self.content_txt,
                bg="white", fg="#666").pack(anchor="w", padx=20, pady=(0, 20))
        
        # Create tabbed interface
        notebook = ttk.Notebook(self.content)
        notebook.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Tab 1: Send Share
        send_frame = tk.Frame(notebook, bg="white")
        notebook.add(send_frame, text="📤 Send Secret")
        self.create_send_share_tab(send_frame)
        
        # Tab 2: Incoming Shares
        incoming_frame = tk.Frame(notebook, bg="white")
        notebook.add(incoming_frame, text="📥 Incoming")
        self.create_incoming_shares_tab(incoming_frame)
        
        # Tab 3: Outgoing Shares
        outgoing_frame = tk.Frame(notebook, bg="white")
        notebook.add(outgoing_frame, text="📤 Sent")
        self.create_outgoing_shares_tab(outgoing_frame)

    def create_send_share_tab(self, parent):
        """Create send share interface for internal users"""
        # Form frame
        form_frame = tk.Frame(parent, bg="white")
        form_frame.pack(fill="x", padx=20, pady=20)
        
        # Recipient selection
        tk.Label(form_frame,
                text="Select Recipient:",
                font=self.content_h2,
                bg="white", fg="#333").pack(anchor="w", pady=(0, 5))
        
        # Dropdown for registered users
        self.recipient_var = tk.StringVar()
        self.recipient_combo = ttk.Combobox(form_frame,
                                           textvariable=self.recipient_var,
                                           font=self.content_txt,
                                           width=48,
                                           state="readonly")
        self.recipient_combo.pack(anchor="w", pady=(0, 15))
        
        # Load users button
        tk.Button(form_frame,
                 text="🔄 Load Users",
                 command=self.load_vault_users,
                 bg="#6c757d", fg="white", relief="flat",
                 padx=10, pady=5).pack(anchor="w", pady=(0, 15))
        
        # Secret data
        tk.Label(form_frame,
                text="Secret to Share:",
                font=self.content_h2,
                bg="white", fg="#333").pack(anchor="w", pady=(0, 5))
        
        self.secret_text = tk.Text(form_frame,
                              font=self.content_txt,
                              height=6, width=60,
                              wrap=tk.WORD)
        self.secret_text.pack(anchor="w", pady=(0, 15))
        
        # Message (optional)
        tk.Label(form_frame,
                text="Message (Optional):",
                font=self.content_h2,
                bg="white", fg="#333").pack(anchor="w", pady=(0, 5))
        
        self.message_entry = tk.Entry(form_frame,
                                     font=self.content_txt,
                                     width=50)
        self.message_entry.pack(anchor="w", pady=(0, 15))
        
        # Send button
        tk.Button(form_frame,
                 text="🔒 Send to Vault User",
                 font=font.Font(family="Segoe UI", size=12, weight="bold"),
                 bg="#28a745",
                 fg="white",
                 relief="flat",
                 command=self.send_internal_secret,
                 cursor="hand2",
                 padx=20,
                 pady=10).pack(anchor="w", pady=10)
        
        # Status frame
        status_frame = tk.Frame(parent, bg="#f8f9fa", relief="solid", bd=1)
        status_frame.pack(fill="x", padx=20, pady=20)
        
        tk.Label(status_frame,
                text="🔐 Internal Sharing:",
                font=font.Font(family="Segoe UI", size=12, weight="bold"),
                bg="#f8f9fa", fg="#333").pack(anchor="w", padx=15, pady=(15, 5))
        
        tips = [
            "• Share secrets only with registered vault users",
            "• Recipients must be logged in to decrypt secrets",
            "• All sharing is end-to-end encrypted within vault",
            "• Secrets are deleted after successful decryption"
        ]
        
        for tip in tips:
            tk.Label(status_frame,
                    text=tip,
                    font=self.content_txt,
                    bg="#f8f9fa", fg="#666").pack(anchor="w", padx=30, pady=2)
        
        tk.Label(status_frame, text="", bg="#f8f9fa").pack(pady=10)
        
        # Load users initially
        self.load_vault_users()

    def load_vault_users(self):
        """Load registered vault users for sharing"""
        try:
            print("🔍 Loading vault users...")
            
            if not self.api_service:
                messagebox.showerror("Error", "API service not available")
                return
            
            # ✅ Use existing auth endpoint
            result = self.api_service.get_vault_users()
            
            if result and 'users' in result:
                users = result['users']
                
                # Filter out current user
                available_users = []
                for user in users:
                    if user.get('email') != self.user_email:
                        display_name = f"{user['email']} (ID: {user['id'][:8]}...)"
                        available_users.append((display_name, user['id'], user['email']))
                
                # Update combobox
                if available_users:
                    display_names = [user[0] for user in available_users]
                    self.recipient_combo['values'] = display_names
                    
                    # Store user mapping for later use
                    self.user_mapping = {user[0]: {'id': user[1], 'email': user[2]} for user in available_users}
                    
                    print(f"✅ Loaded {len(available_users)} users for sharing")
                else:
                    self.recipient_combo['values'] = ["No other users available"]
                    self.user_mapping = {}
                    print("⚠️ No other users found")
            else:
                error_msg = result.get('error', 'Failed to load users') if result else 'No response'
                messagebox.showerror("Error", f"Could not load users:\n\n{error_msg}")
    
        except Exception as e:
            print(f"❌ Load vault users error: {e}")
            messagebox.showerror("Error", f"Failed to load users:\n\n{str(e)}")

    def send_internal_secret(self):
        """Send secret to selected vault user"""
        try:
            selected_display = self.recipient_var.get()
            secret_data = self.secret_text.get("1.0", tk.END).strip()
            message = self.message_entry.get().strip()
            
            if not selected_display or selected_display == "No other users available":
                messagebox.showerror("Error", "Please select a recipient")
                return
            
            if not secret_data:
                messagebox.showerror("Error", "Please enter secret data to share")
                return
            
            if not hasattr(self, 'user_mapping') or selected_display not in self.user_mapping:
                messagebox.showerror("Error", "Invalid recipient selection")
                return
            
            recipient_info = self.user_mapping[selected_display]
            recipient_id = recipient_info['id']
            recipient_email = recipient_info['email']
            
            # Confirm sharing
            if not messagebox.askyesno("Confirm Share", 
                                     f"Share secret with {recipient_email}?\n\n"
                                     f"Secret length: {len(secret_data)} characters\n"
                                     f"Message: {message or 'None'}"):
                return
            
            # Send via API
            result = self.api_service.send_internal_share(recipient_id, secret_data, message)
            
            if result and result.get('share_id'):
                messagebox.showinfo("Success", 
                                  f"Secret shared successfully!\n\n"
                                  f"Recipient: {recipient_email}\n"
                                  f"Share ID: {result['share_id']}")
                
                # Clear form
                self.recipient_var.set('')
                self.secret_text.delete("1.0", tk.END)
                self.message_entry.delete(0, tk.END)
                
                # Refresh outgoing shares
                self.load_outgoing_shares()
            else:
                error_msg = result.get('error', 'Unknown error') if result else 'Send failed'
                messagebox.showerror("Send Failed", f"Failed to send secret:\n\n{error_msg}")
    
        except Exception as e:
            print(f"❌ Send internal secret error: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Error", f"Failed to send secret:\n\n{str(e)}")

    def open_recovery(self):
        """Open backup management interface"""
        self.clear_content()
        
        # Title
        tk.Label(self.content,
                text="💾 Backup & Recovery",
                font=self.content_h1,
                bg="white", fg="#333").pack(anchor="w", pady=(20, 10), padx=20)
        
        # Description
        tk.Label(self.content,
                text="Manage your vault backups and recovery options.",
                font=self.content_txt,
                bg="white", fg="#666").pack(anchor="w", padx=20, pady=(0, 20))
        
        # Button frame
        button_frame = tk.Frame(self.content, bg="white")
        button_frame.pack(fill="x", padx=20, pady=20)
        
        # Action buttons
        tk.Button(button_frame,
                 text="📤 Create Backup",
                 font=font.Font(family="Segoe UI", size=12, weight="bold"),
                 bg="#28a745",
                 fg="white",
                 relief="flat",
                 command=self.export_backup,
                 cursor="hand2",
                 padx=20,
                 pady=10).pack(side="left", padx=(0, 10))
        
        tk.Button(button_frame,
                 text="📥 Import Backup",
                 font=font.Font(family="Segoe UI", size=12, weight="bold"),
                 bg="#17a2b8",
                 fg="white",
                 relief="flat",
                 command=self.import_backup,
                 cursor="hand2",
                 padx=20,
                 pady=10).pack(side="left", padx=(0, 10))
        
        tk.Button(button_frame,
                 text="📋 View Backups",
                 font=font.Font(family="Segoe UI", size=12, weight="bold"),
                 bg="#6f42c1",
                 fg="white",
                 relief="flat",
                 command=self.view_backups,
                 cursor="hand2",
                 padx=20,
                 pady=10).pack(side="left", padx=(0, 10))
        
        # Status frame
        status_frame = tk.Frame(self.content, bg="#f8f9fa", relief="solid", bd=1)
        status_frame.pack(fill="x", padx=20, pady=20)
        
        tk.Label(status_frame,
                text="💡 Backup Tips:",
                font=font.Font(family="Segoe UI", size=12, weight="bold"),
                bg="#f8f9fa", fg="#333").pack(anchor="w", padx=15, pady=(15, 5))
        
        tips = [
            "• Regular backups protect against data loss",
            "• Backups are encrypted with your master password",
            "• Store backups in multiple secure locations",
            "• Test backup restoration periodically"
        ]
        
        for tip in tips:
            tk.Label(status_frame,
                    text=tip,
                    font=self.content_txt,
                    bg="#f8f9fa", fg="#666").pack(anchor="w", padx=30, pady=2)
        
        tk.Label(status_frame, text="", bg="#f8f9fa").pack(pady=10)

    def view_backups(self):
        """View available backups"""
        try:
            print("🔍 === VIEW BACKUPS ===")
            
            if not self.api_service:
                messagebox.showerror("Error", "API service not available")
                return
            
            # Get backups list
            result = self.api_service.get_backups()
            
            if result and 'backups' in result:
                backups = result['backups']
                
                # Create view dialog
                view_dialog = tk.Toplevel(self)
                view_dialog.title("Available Backups")
                view_dialog.geometry("600x400")
                view_dialog.configure(bg="#f8f9fa")
                view_dialog.transient(self)
                view_dialog.grab_set()
                
                # Center dialog
                view_dialog.update_idletasks()
                x = self.winfo_x() + (self.winfo_width() // 2) - (300)
                y = self.winfo_y() + (self.winfo_height() // 2) - (200)
                view_dialog.geometry(f"600x400+{x}+{y}")
                
                # Header
                tk.Label(view_dialog,
                        text="📋 Your Backups",
                        font=font.Font(family="Segoe UI", size=16, weight="bold"),
                        bg="#f8f9fa", fg="#333").pack(pady=20)
                
                # Backup list
                list_frame = tk.Frame(view_dialog, bg="white", relief="solid", bd=1)
                list_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
                
                # Treeview
                columns = ('Name', 'Created', 'Size', 'Status')
                tree = ttk.Treeview(list_frame, columns=columns, show='headings')
                
                for col in columns:
                    tree.heading(col, text=col)
                    tree.column(col, width=140)
                
                # Add backups
                for backup in backups:
                    # Format date
                    created_date = backup.get('created_at', '')
                    if created_date:
                        try:
                            from datetime import datetime
                            dt = datetime.fromisoformat(created_date.replace('Z', '+00:00'))
                            formatted_date = dt.strftime('%Y-%m-%d %H:%M')
                        except:
                            formatted_date = created_date[:16]
                    else:
                        formatted_date = 'Unknown'
                    
                    # Format size
                    size_bytes = backup.get('size_bytes', 0)
                    if size_bytes > 1024 * 1024:
                        size_str = f"{size_bytes / (1024 * 1024):.1f} MB"
                    elif size_bytes > 1024:
                        size_str = f"{size_bytes / 1024:.1f} KB"
                    else:
                        size_str = f"{size_bytes} B"
                    
                    tree.insert('', 'end', values=(
                        backup.get('name', 'Unnamed'),
                        formatted_date,
                        size_str,
                        backup.get('status', 'Unknown')
                    ))
                
                tree.pack(fill="both", expand=True, padx=10, pady=10)
                
                # Button frame
                btn_frame = tk.Frame(view_dialog, bg="#f8f9fa")
                btn_frame.pack(fill="x", padx=20, pady=(0, 20))
                
                tk.Button(btn_frame,
                         text="🔄 Refresh",
                         command=lambda: view_dialog.destroy() or self.view_backups(),
                         bg="#17a2b8", fg="white", relief="flat",
                         padx=15, pady=8).pack(side="left", padx=(0, 10))
                
                tk.Button(btn_frame,
                         text="❌ Close",
                         command=view_dialog.destroy,
                         bg="#6c757d", fg="white", relief="flat",
                         padx=15, pady=8).pack(side="right")
                
            else:
                error_msg = result.get('error', 'Failed to load backups') if result else 'No response'
                messagebox.showerror("Error", f"Could not load backups:\n\n{error_msg}")
        
        except Exception as e:
            print(f"❌ View backups error: {e}")
            messagebox.showerror("Error", f"Failed to view backups:\n\n{str(e)}")

    def edit_selected_entry(self):
        """Edit selected vault entry"""
        try:
            messagebox.showinfo("Edit Entry", "Edit feature coming soon!")
        except Exception as e:
            print(f"❌ Edit entry error: {e}")
            messagebox.showerror("Error", f"Edit error:\n\n{str(e)}")

    def delete_selected_entry(self):
        """Delete selected vault entry"""
        try:
            # Get selected item from vault tree
            selection = self.vault_tree.selection()
            if not selection:
                messagebox.showwarning("No Selection", "Please select an entry to delete")
                return
            
            # Get entry ID from selection tags
            item = selection[0]
            item_tags = self.vault_tree.item(item, 'tags')
            
            if not item_tags or len(item_tags) == 0:
                messagebox.showerror("Error", "Could not determine entry ID")
                return
            
            entry_id = item_tags[0]
            entry_name = self.vault_tree.item(item, 'text')
            
            # Confirm deletion
            if messagebox.askyesno("Confirm Delete", 
                                  f"Are you sure you want to delete '{entry_name}'?\n\n"
                                  f"This action cannot be undone!"):
                
                # Delete entry
                result = self.api_service.delete_vault_entry(entry_id)
                
                if result and result.get('success'):
                    messagebox.showinfo("Deleted", f"Entry '{entry_name}' has been deleted.")
                    
                    # Refresh vault display
                    self.load_vault_data()
                    self.show_vault()
                else:
                    error_msg = result.get('error', 'Delete failed') if result else 'Unknown error'
                    messagebox.showerror("Delete Failed", f"Failed to delete entry:\n\n{error_msg}")
        
        except Exception as e:
            print(f"❌ Delete entry error: {e}")
            messagebox.showerror("Error", f"Failed to delete entry:\n\n{str(e)}")

    def create_incoming_shares_tab(self, parent):
        """Create incoming shares interface"""
        # Header
        header_frame = tk.Frame(parent, bg="white")
        header_frame.pack(fill="x", padx=20, pady=20)
        
        tk.Label(header_frame,
                text="📥 Secrets Shared With You",
                font=self.content_h2,
                bg="white", fg="#333").pack(side="left")
        
        tk.Button(header_frame,
                 text="🔄 Refresh",
                 command=self.load_incoming_shares,
                 bg="#17a2b8", fg="white", relief="flat",
                 padx=15, pady=8).pack(side="right")
        
        # Shares list frame
        list_frame = tk.Frame(parent, bg="white", relief="solid", bd=1)
        list_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Treeview for incoming shares
        columns = ('From', 'Message', 'Received', 'Status')
        self.incoming_tree = ttk.Treeview(list_frame, columns=columns, show='headings')
        
        for col in columns:
            self.incoming_tree.heading(col, text=col)
            if col == 'Message':
                self.incoming_tree.column(col, width=200)
            else:
                self.incoming_tree.column(col, width=120)
        
        # Scrollbar
        incoming_scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.incoming_tree.yview)
        self.incoming_tree.configure(yscrollcommand=incoming_scrollbar.set)
        
        self.incoming_tree.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        incoming_scrollbar.pack(side="right", fill="y", pady=10)
        
        # Double-click to decrypt
        self.incoming_tree.bind('<Double-1>', lambda e: self.decrypt_selected_share())
        
        # Load initial data
        self.load_incoming_shares()

    def create_outgoing_shares_tab(self, parent):
        """Create outgoing shares interface"""
        # Header
        header_frame = tk.Frame(parent, bg="white")
        header_frame.pack(fill="x", padx=20, pady=20)
        
        tk.Label(header_frame,
                text="📤 Secrets You've Shared",
                font=self.content_h2,
                bg="white", fg="#333").pack(side="left")
        
        tk.Button(header_frame,
                 text="🔄 Refresh",
                 command=self.load_outgoing_shares,
                 bg="#17a2b8", fg="white", relief="flat",
                 padx=15, pady=8).pack(side="right")
        
        # Shares list frame
        list_frame = tk.Frame(parent, bg="white", relief="solid", bd=1)
        list_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Treeview for outgoing shares
        columns = ('To', 'Message', 'Sent', 'Status')
        self.outgoing_tree = ttk.Treeview(list_frame, columns=columns, show='headings')
        
        for col in columns:
            self.outgoing_tree.heading(col, text=col)
            if col == 'Message':
                self.outgoing_tree.column(col, width=200)
            else:
                self.outgoing_tree.column(col, width=120)
        
        # Scrollbar
        outgoing_scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.outgoing_tree.yview)
        self.outgoing_tree.configure(yscrollcommand=outgoing_scrollbar.set)
        
        self.outgoing_tree.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        outgoing_scrollbar.pack(side="right", fill="y", pady=10)
        
        # Load initial data
        self.load_outgoing_shares()

    def load_incoming_shares(self):
        """Load incoming shares"""
        try:
            # Clear existing items
            if hasattr(self, 'incoming_tree'):
                for item in self.incoming_tree.get_children():
                    self.incoming_tree.delete(item)
            
            # Get shares from API
            result = self.api_service.get_incoming_shares()
            
            if result and 'shares' in result:
                shares = result['shares']
                
                for share in shares:
                    from_user = share.get('sender_email', 'Unknown')
                    message = share.get('message', '') or 'No message'
                    received_date = share.get('created_at', '')
                    status = share.get('status', 'Pending')
                    
                    # Format date
                    if received_date:
                        try:
                            from datetime import datetime
                            dt = datetime.fromisoformat(received_date.replace('Z', '+00:00'))
                            formatted_date = dt.strftime('%Y-%m-%d %H:%M')
                        except:
                            formatted_date = received_date[:16]
                    else:
                        formatted_date = 'Unknown'
                    
                    if hasattr(self, 'incoming_tree'):
                        self.incoming_tree.insert('', 'end', 
                                                values=(from_user, message, formatted_date, status),
                                                tags=(share.get('id', ''),))
            else:
                print(f"Failed to load incoming shares: {result}")
        
        except Exception as e:
            print(f"❌ Load incoming shares error: {e}")

    def load_outgoing_shares(self):
        """Load outgoing shares"""
        try:
            # Clear existing items
            if hasattr(self, 'outgoing_tree'):
                for item in self.outgoing_tree.get_children():
                    self.outgoing_tree.delete(item)
            
            # Get shares from API
            result = self.api_service.get_outgoing_shares()
            
            if result and 'shares' in result:
                shares = result['shares']
                
                for share in shares:
                    to_user = share.get('recipient_email', 'Unknown')
                    message = share.get('message', '') or 'No message'
                    sent_date = share.get('created_at', '')
                    status = share.get('status', 'Sent')
                    
                    # Format date
                    if sent_date:
                        try:
                            from datetime import datetime
                            dt = datetime.fromisoformat(sent_date.replace('Z', '+00:00'))
                            formatted_date = dt.strftime('%Y-%m-%d %H:%M')
                        except:
                            formatted_date = sent_date[:16]
                    else:
                        formatted_date = 'Unknown'
                    
                    if hasattr(self, 'outgoing_tree'):
                        self.outgoing_tree.insert('', 'end', 
                                                values=(to_user, message, formatted_date, status),
                                                tags=(share.get('id', ''),))
            else:
                print(f"Failed to load outgoing shares: {result}")
        
        except Exception as e:
            print(f"❌ Load outgoing shares error: {e}")

    def decrypt_selected_share(self):
        """Decrypt and view selected incoming share"""
        try:
            selection = self.incoming_tree.selection()
            if not selection:
                messagebox.showwarning("No Selection", "Please select a share to decrypt")
                return
            
            # Get share ID from selection tags
            item = selection[0]
            item_tags = self.incoming_tree.item(item, 'tags')
            
            if not item_tags or len(item_tags) == 0:
                messagebox.showerror("Error", "Could not determine share ID")
                return
            
            share_id = item_tags[0]
            
            # Get share details and decrypt
            result = self.api_service.decrypt_internal_share(share_id)
            
            if result and 'decrypted_secret' in result:
                # Show decrypted secret in dialog
                self.show_decrypted_secret(result)
            else:
                error_msg = result.get('error', 'Decryption failed') if result else 'Unknown error'
                messagebox.showerror("Decryption Failed", f"Failed to decrypt secret:\n\n{error_msg}")
        
        except Exception as e:
            print(f"❌ Decrypt share error: {e}")
            messagebox.showerror("Error", f"Failed to decrypt share:\n\n{str(e)}")

    def show_decrypted_secret(self, share_data):
        """Show decrypted secret in dialog"""
        dialog = tk.Toplevel(self)
        dialog.title("🔓 Decrypted Secret")
        dialog.geometry("500x400")
        dialog.configure(bg="#f8f9fa")
        dialog.transient(self)
        dialog.grab_set()
        
        # Center dialog
        dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - (250)
        y = self.winfo_y() + (self.winfo_height() // 2) - (200)
        dialog.geometry(f"500x400+{x}+{y}")
        
        # Header
        tk.Label(dialog,
                text="🔓 Secret Successfully Decrypted",
                font=font.Font(family="Segoe UI", size=16, weight="bold"),
                bg="#f8f9fa", fg="#333").pack(pady=20)
        
        # From info
        from_user = share_data.get('sender_email', 'Unknown')
        tk.Label(dialog,
                text=f"From: {from_user}",
                font=font.Font(family="Segoe UI", size=12),
                bg="#f8f9fa", fg="#666").pack(pady=5)
        
        # Message
        message = share_data.get('message', '')
        if message:
            tk.Label(dialog,
                    text=f"Message: {message}",
                    font=font.Font(family="Segoe UI", size=12),
                    bg="#f8f9fa", fg="#666").pack(pady=5)
        
        # Secret content
        content_frame = tk.Frame(dialog, bg="white", relief="solid", bd=1)
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        tk.Label(content_frame,
                text="Secret Content:",
                font=font.Font(family="Segoe UI", size=12, weight="bold"),
                bg="white", fg="#333").pack(anchor="w", padx=10, pady=(10, 5))
        
        secret_text = tk.Text(content_frame,
                         font=font.Font(family="Consolas", size=10),
                         wrap=tk.WORD,
                         state=tk.NORMAL)
        secret_text.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Insert secret content
        decrypted_secret = share_data.get('decrypted_secret', '')
        secret_text.insert("1.0", decrypted_secret)
        secret_text.config(state=tk.DISABLED)  # Read-only
        
        # Button frame
        btn_frame = tk.Frame(dialog, bg="#f8f9fa")
        btn_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        tk.Button(btn_frame,
                 text="📋 Copy to Clipboard",
                 command=lambda: self.copy_to_clipboard(decrypted_secret),
                 bg="#17a2b8", fg="white", relief="flat",
                 padx=15, pady=8).pack(side="left", padx=(0, 10))
        
        tk.Button(btn_frame,
                 text="❌ Close",
                 command=dialog.destroy,
                 bg="#6c757d", fg="white", relief="flat",
                 padx=15, pady=8).pack(side="right")

    def copy_to_clipboard(self, text):
        """Copy text to clipboard"""
        try:
            self.clipboard_clear()
            self.clipboard_append(text)
            messagebox.showinfo("Copied", "Text copied to clipboard!")
        except Exception as e:
            print(f"❌ Copy to clipboard error: {e}")
            messagebox.showerror("Error", f"Failed to copy to clipboard:\n\n{str(e)}")

    def show_settings(self):
        """Show settings interface"""
        try:
            messagebox.showinfo("Settings", "Settings feature coming soon!")
        except Exception as e:
            print(f"❌ Settings error: {e}")
            messagebox.showerror("Error", f"Settings error:\n\n{str(e)}")
