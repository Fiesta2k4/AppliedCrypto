import tkinter as tk
from tkinter import ttk, messagebox, font, simpledialog
import threading
import time
from datetime import datetime

class OTPWindow(tk.Toplevel):
    """Clean and beautiful OTP management window"""
    
    def __init__(self, master=None, api_service=None):
        super().__init__(master)
        
        self.api_service = api_service
        self.otp_accounts = []
        self.otp_codes = {}
        self.countdown_active = False
        
        self.title("🔑 Two-Factor Authentication (2FA/OTP)")
        self.geometry("1000x700")
        self.configure(bg="#f8f9fa")
        self.resizable(True, True)
        self.minsize(800, 600)
        
        # Center window
        self.center_window()
        
        # Fonts
        self.title_font = font.Font(family="Segoe UI", size=24, weight="bold")
        self.header_font = font.Font(family="Segoe UI", size=16, weight="bold")
        self.body_font = font.Font(family="Segoe UI", size=11)
        self.code_font = font.Font(family="Consolas", size=18, weight="bold")
        self.small_font = font.Font(family="Segoe UI", size=9)
        
        # Colors
        self.colors = {
            'primary': '#007bff',
            'success': '#28a745',
            'danger': '#dc3545',
            'warning': '#ffc107',
            'info': '#17a2b8',
            'light': '#f8f9fa',
            'dark': '#343a40',
            'white': '#ffffff',
            'gray': '#6c757d',
            'border': '#dee2e6'
        }
        
        self.setup_ui()
        self.load_otp_accounts()
        
        # Auto-refresh OTP codes
        self.start_auto_refresh()
        
        # Handle window close
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def center_window(self):
        """Center window on screen"""
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (self.winfo_width() // 2)
        y = (self.winfo_screenheight() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")
    
    def setup_ui(self):
        """Setup the UI layout"""
        
        # Main container
        main_frame = tk.Frame(self, bg=self.colors['light'])
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header
        self.create_header(main_frame)
        
        # Action buttons
        self.create_action_buttons(main_frame)
        
        # OTP accounts display
        self.create_otp_display(main_frame)
        
        # Status bar
        self.create_status_bar(main_frame)
    
    def create_header(self, parent):
        """Create header section"""
        header_frame = tk.Frame(parent, bg=self.colors['white'], relief="solid", bd=1)
        header_frame.pack(fill="x", pady=(0, 20))
        
        # Title with icon
        title_frame = tk.Frame(header_frame, bg=self.colors['white'])
        title_frame.pack(fill="x", padx=20, pady=15)
        
        tk.Label(title_frame,
                text="🔑 Two-Factor Authentication",
                font=self.title_font,
                bg=self.colors['white'],
                fg=self.colors['dark']).pack(side="left")
        
        # Info label
        info_text = "Secure your accounts with time-based one-time passwords (TOTP)"
        tk.Label(header_frame,
                text=info_text,
                font=self.body_font,
                bg=self.colors['white'],
                fg=self.colors['gray']).pack(padx=20, pady=(0, 15))
    
    def create_action_buttons(self, parent):
        """Create action buttons"""
        btn_frame = tk.Frame(parent, bg=self.colors['light'])
        btn_frame.pack(fill="x", pady=(0, 20))
        
        # Left side buttons
        left_frame = tk.Frame(btn_frame, bg=self.colors['light'])
        left_frame.pack(side="left")
        
        # Add Account button
        add_btn = tk.Button(left_frame,
                           text="➕ Add Account",
                           font=self.body_font,
                           bg=self.colors['success'],
                           fg=self.colors['white'],
                           relief="flat",
                           padx=20,
                           pady=8,
                           cursor="hand2",
                           command=self.show_add_account_dialog)
        add_btn.pack(side="left", padx=(0, 10))
        
        # Scan QR button
        qr_btn = tk.Button(left_frame,
                          text="📷 Scan QR Code",
                          font=self.body_font,
                          bg=self.colors['info'],
                          fg=self.colors['white'],
                          relief="flat",
                          padx=20,
                          pady=8,
                          cursor="hand2",
                          command=self.show_qr_dialog)
        qr_btn.pack(side="left", padx=(0, 10))
        
        # Right side buttons
        right_frame = tk.Frame(btn_frame, bg=self.colors['light'])
        right_frame.pack(side="right")
        
        # Refresh button
        refresh_btn = tk.Button(right_frame,
                               text="🔄 Refresh",
                               font=self.body_font,
                               bg=self.colors['primary'],
                               fg=self.colors['white'],
                               relief="flat",
                               padx=15,
                               pady=8,
                               cursor="hand2",
                               command=self.refresh_otp_codes)
        refresh_btn.pack(side="right")
    
    def create_otp_display(self, parent):
        """Create OTP codes display area"""
        
        # Container with border
        display_frame = tk.Frame(parent, bg=self.colors['white'], relief="solid", bd=1)
        display_frame.pack(fill="both", expand=True)
        
        # Header
        header = tk.Frame(display_frame, bg=self.colors['primary'], height=50)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        tk.Label(header,
                text="📱 Your 2FA Accounts",
                font=self.header_font,
                bg=self.colors['primary'],
                fg=self.colors['white']).pack(side="left", padx=20, pady=12)
        
        # Countdown timer display
        self.countdown_label = tk.Label(header,
                                       text="⏱️ Next refresh in: 30s",
                                       font=self.body_font,
                                       bg=self.colors['primary'],
                                       fg=self.colors['white'])
        self.countdown_label.pack(side="right", padx=20, pady=12)
        
        # Scrollable content area
        self.create_scrollable_content(display_frame)
    
    def create_scrollable_content(self, parent):
        """Create scrollable content area for OTP accounts"""
        
        # Create canvas and scrollbar
        canvas_frame = tk.Frame(parent, bg=self.colors['white'])
        canvas_frame.pack(fill="both", expand=True, padx=2, pady=2)
        
        self.canvas = tk.Canvas(canvas_frame, bg=self.colors['white'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)
        
        self.scrollable_frame = tk.Frame(self.canvas, bg=self.colors['white'])
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Bind mousewheel
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.scrollable_frame.bind("<MouseWheel>", self._on_mousewheel)
    
    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling"""
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def create_status_bar(self, parent):
        """Create status bar"""
        self.status_frame = tk.Frame(parent, bg=self.colors['border'], height=30)
        self.status_frame.pack(fill="x", pady=(10, 0))
        self.status_frame.pack_propagate(False)
        
        self.status_label = tk.Label(self.status_frame,
                                    text="Ready",
                                    font=self.small_font,
                                    bg=self.colors['border'],
                                    fg=self.colors['gray'])
        self.status_label.pack(side="left", padx=10, pady=5)
    
    def show_add_account_dialog(self):
        """Show add account dialog"""
        AddAccountDialog(self, self.api_service, self.on_account_added)
    
    def show_qr_dialog(self):
        """Show QR code scanner dialog"""
        QRScanDialog(self, self.api_service, self.on_account_added)
    
    def on_account_added(self):
        """Callback when account is added"""
        self.load_otp_accounts()
        self.set_status("Account added successfully", "success")
    
    def load_otp_accounts(self):
        """Load OTP accounts from API"""
        try:
            self.set_status("Loading accounts...", "info")
            
            if not self.api_service:
                self.set_status("API service not available", "danger")
                return
            
            result = self.api_service.get_otp_accounts()
            
            if result and result.get('success'):
                self.otp_accounts = result.get('accounts', [])
                self.refresh_otp_codes()
                self.set_status(f"Loaded {len(self.otp_accounts)} accounts", "success")
            else:
                error_msg = result.get('error', 'Unknown error') if result else 'Failed to load accounts'
                self.set_status(f"Error: {error_msg}", "danger")
                self.otp_accounts = []
                
        except Exception as e:
            print(f"❌ Load OTP accounts error: {e}")
            self.set_status(f"Error loading accounts: {str(e)}", "danger")
            self.otp_accounts = []
        
        # Always update display
        self.update_otp_display()
    
    def refresh_otp_codes(self):
        """Refresh all OTP codes"""
        try:
            self.set_status("Generating OTP codes...", "info")
            
            if not self.api_service:
                return
            
            result = self.api_service.generate_all_otps()
            
            if result and result.get('success'):
                otp_data = result.get('otp_accounts', [])
                
                # Update otp_codes dictionary
                self.otp_codes = {}
                for otp in otp_data:
                    self.otp_codes[otp['id']] = {
                        'code': otp['otp_code'],
                        'time_remaining': otp['time_remaining'],
                        'period': otp['period']
                    }
                
                self.update_otp_display()
                self.set_status("OTP codes updated", "success")
            else:
                error_msg = result.get('error', 'Unknown error') if result else 'Failed to generate codes'
                self.set_status(f"Error: {error_msg}", "danger")
                
        except Exception as e:
            print(f"❌ Refresh OTP codes error: {e}")
            self.set_status(f"Error: {str(e)}", "danger")
    
    def update_otp_display(self):
        """Update the OTP display"""
        
        # Clear existing content
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        if not self.otp_accounts:
            # Show empty state
            self.show_empty_state()
            return
        
        # Display each account
        for i, account in enumerate(self.otp_accounts):
            self.create_account_card(account, i)
        
        # Update scroll region
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def show_empty_state(self):
        """Show empty state when no accounts"""
        empty_frame = tk.Frame(self.scrollable_frame, bg=self.colors['white'])
        empty_frame.pack(fill="both", expand=True, padx=40, pady=60)
        
        # Icon
        tk.Label(empty_frame,
                text="🔐",
                font=font.Font(size=48),
                bg=self.colors['white'],
                fg=self.colors['gray']).pack(pady=(0, 20))
        
        # Title
        tk.Label(empty_frame,
                text="No 2FA Accounts",
                font=self.header_font,
                bg=self.colors['white'],
                fg=self.colors['dark']).pack(pady=(0, 10))
        
        # Description
        description = ("Add your first 2FA account to get started.\n"
                      "You can add accounts manually or scan QR codes.")
        tk.Label(empty_frame,
                text=description,
                font=self.body_font,
                bg=self.colors['white'],
                fg=self.colors['gray'],
                justify="center").pack(pady=(0, 30))
        
        # Add button
        tk.Button(empty_frame,
                 text="➕ Add Your First Account",
                 font=self.body_font,
                 bg=self.colors['primary'],
                 fg=self.colors['white'],
                 relief="flat",
                 padx=30,
                 pady=12,
                 cursor="hand2",
                 command=self.show_add_account_dialog).pack()
    
    def create_account_card(self, account, index):
        """Create account card"""
        
        # Card container
        card_frame = tk.Frame(self.scrollable_frame, 
                             bg=self.colors['white'], 
                             relief="solid", 
                             bd=1)
        card_frame.pack(fill="x", padx=20, pady=10)
        
        # Hover effects
        self.add_hover_effect(card_frame)
        
        # Main content frame
        content_frame = tk.Frame(card_frame, bg=self.colors['white'])
        content_frame.pack(fill="x", padx=20, pady=15)
        
        # Left side - Account info
        left_frame = tk.Frame(content_frame, bg=self.colors['white'])
        left_frame.pack(side="left", fill="x", expand=True)
        
        # Account name
        account_name = f"{account.get('issuer', 'Unknown')} ({account.get('account', 'Unknown')})"
        tk.Label(left_frame,
                text=account_name,
                font=self.header_font,
                bg=self.colors['white'],
                fg=self.colors['dark'],
                anchor="w").pack(fill="x", pady=(0, 5))
        
        # Account details
        details = f"Digits: {account.get('digits', 6)} • Period: {account.get('period', 30)}s • Algorithm: {account.get('algorithm', 'SHA1')}"
        tk.Label(left_frame,
                text=details,
                font=self.small_font,
                bg=self.colors['white'],
                fg=self.colors['gray'],
                anchor="w").pack(fill="x")
        
        # Right side - OTP code and actions
        right_frame = tk.Frame(content_frame, bg=self.colors['white'])
        right_frame.pack(side="right", padx=(20, 0))
        
        # OTP code display
        code_frame = tk.Frame(right_frame, bg=self.colors['light'], relief="solid", bd=1)
        code_frame.pack(pady=(0, 10))
        
        account_id = account['id']
        otp_data = self.otp_codes.get(account_id, {})
        otp_code = otp_data.get('code', '------')
        time_remaining = otp_data.get('time_remaining', 0)
        
        # Format OTP code for better readability
        formatted_code = self.format_otp_code(otp_code)
        
        code_label = tk.Label(code_frame,
                             text=formatted_code,
                             font=self.code_font,
                             bg=self.colors['light'],
                             fg=self.colors['dark'],
                             padx=15,
                             pady=8)
        code_label.pack()
        
        # Time remaining
        time_color = self.colors['danger'] if time_remaining < 10 else self.colors['success']
        time_label = tk.Label(right_frame,
                             text=f"⏱️ {time_remaining}s",
                             font=self.small_font,
                             bg=self.colors['white'],
                             fg=time_color)
        time_label.pack(pady=(0, 5))
        
        # Action buttons
        actions_frame = tk.Frame(right_frame, bg=self.colors['white'])
        actions_frame.pack()
        
        # Copy button
        copy_btn = tk.Button(actions_frame,
                            text="📋",
                            font=self.body_font,
                            bg=self.colors['info'],
                            fg=self.colors['white'],
                            relief="flat",
                            width=3,
                            cursor="hand2",
                            command=lambda: self.copy_otp_code(otp_code))
        copy_btn.pack(side="left", padx=(0, 5))
        
        # Delete button
        delete_btn = tk.Button(actions_frame,
                              text="🗑️",
                              font=self.body_font,
                              bg=self.colors['danger'],
                              fg=self.colors['white'],
                              relief="flat",
                              width=3,
                              cursor="hand2",
                              command=lambda: self.delete_account(account))
        delete_btn.pack(side="left")
        
        # Store references for updates
        setattr(code_label, 'account_id', account_id)
        setattr(time_label, 'account_id', account_id)
    
    def format_otp_code(self, code):
        """Format OTP code for better readability"""
        if len(code) == 6:
            return f"{code[:3]} {code[3:]}"
        elif len(code) == 8:
            return f"{code[:4]} {code[4:]}"
        else:
            return code
    
    def add_hover_effect(self, widget):
        """Add hover effect to widget"""
        def on_enter(event):
            widget.configure(bg="#f0f0f0")
        
        def on_leave(event):
            widget.configure(bg=self.colors['white'])
        
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)
    
    def copy_otp_code(self, code):
        """Copy OTP code to clipboard"""
        try:
            self.clipboard_clear()
            self.clipboard_append(code)
            self.set_status(f"Copied {code} to clipboard", "success")
        except Exception as e:
            self.set_status(f"Failed to copy: {str(e)}", "danger")
    
    def delete_account(self, account):
        """Delete OTP account"""
        account_name = f"{account.get('issuer', 'Unknown')} ({account.get('account', 'Unknown')})"
        
        if messagebox.askyesno("Confirm Delete", 
                              f"Are you sure you want to delete this account?\n\n{account_name}\n\nThis action cannot be undone."):
            try:
                result = self.api_service.delete_otp_account(account['id'])
                
                if result and result.get('success'):
                    self.load_otp_accounts()
                    self.set_status("Account deleted successfully", "success")
                else:
                    error_msg = result.get('error', 'Unknown error') if result else 'Delete failed'
                    self.set_status(f"Delete failed: {error_msg}", "danger")
                    
            except Exception as e:
                self.set_status(f"Delete error: {str(e)}", "danger")
    
    def start_auto_refresh(self):
        """Start auto-refresh timer"""
        self.countdown_active = True
        self.update_countdown()
        
        # Refresh codes every 30 seconds
        def auto_refresh():
            while self.countdown_active:
                time.sleep(30)
                if self.countdown_active:
                    self.after(0, self.refresh_otp_codes)
        
        threading.Thread(target=auto_refresh, daemon=True).start()
    
    def update_countdown(self):
        """Update countdown timer"""
        if not self.countdown_active:
            return
        
        try:
            current_time = int(time.time())
            seconds_remaining = 30 - (current_time % 30)
            
            self.countdown_label.configure(text=f"⏱️ Next refresh in: {seconds_remaining}s")
            
            # Update time remaining for each account
            for widget in self.scrollable_frame.winfo_children():
                for child in widget.winfo_children():
                    for grandchild in child.winfo_children():
                        if hasattr(grandchild, 'winfo_children'):
                            for ggchild in grandchild.winfo_children():
                                if hasattr(ggchild, 'account_id') and 'account_id' in dir(ggchild):
                                    account_id = ggchild.account_id
                                    if account_id in self.otp_codes:
                                        otp_data = self.otp_codes[account_id]
                                        period = otp_data.get('period', 30)
                                        time_remaining = period - (current_time % period)
                                        
                                        if isinstance(ggchild, tk.Label) and ggchild.cget('text').startswith('⏱️'):
                                            time_color = self.colors['danger'] if time_remaining < 10 else self.colors['success']
                                            ggchild.configure(text=f"⏱️ {time_remaining}s", fg=time_color)
            
            # Schedule next update
            self.after(1000, self.update_countdown)
            
        except Exception as e:
            print(f"Countdown update error: {e}")
            self.after(1000, self.update_countdown)
    
    def set_status(self, message, status_type="info"):
        """Set status message"""
        colors = {
            'info': self.colors['info'],
            'success': self.colors['success'],
            'danger': self.colors['danger'],
            'warning': self.colors['warning']
        }
        
        color = colors.get(status_type, self.colors['gray'])
        self.status_label.configure(text=message, fg=color)
        
        # Auto-clear status after 5 seconds
        self.after(5000, lambda: self.status_label.configure(text="Ready", fg=self.colors['gray']))
    
    def on_closing(self):
        """Handle window closing"""
        self.countdown_active = False
        self.destroy()


class AddAccountDialog(tk.Toplevel):
    """Dialog for adding OTP account manually"""
    
    def __init__(self, parent, api_service, callback):
        super().__init__(parent)
        
        self.api_service = api_service
        self.callback = callback
        
        self.title("➕ Add 2FA Account")
        self.geometry("500x600")
        self.configure(bg="#ffffff")
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()
        
        # Center on parent
        self.center_on_parent(parent)
        
        # Fonts
        self.title_font = font.Font(family="Segoe UI", size=18, weight="bold")
        self.label_font = font.Font(family="Segoe UI", size=11, weight="bold")
        self.body_font = font.Font(family="Segoe UI", size=11)
        
        self.setup_ui()
    
    def center_on_parent(self, parent):
        """Center dialog on parent window"""
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")
    
    def setup_ui(self):
        """Setup dialog UI"""
        
        # Main frame
        main_frame = tk.Frame(self, bg="#ffffff")
        main_frame.pack(fill="both", expand=True, padx=30, pady=30)
        
        # Title
        tk.Label(main_frame,
                text="➕ Add 2FA Account",
                font=self.title_font,
                bg="#ffffff",
                fg="#343a40").pack(pady=(0, 30))
        
        # Form fields
        self.create_form_fields(main_frame)
        
        # Buttons
        self.create_buttons(main_frame)
    
    def create_form_fields(self, parent):
        """Create form fields"""
        
        # Service Provider
        tk.Label(parent,
                text="Service Provider *",
                font=self.label_font,
                bg="#ffffff",
                fg="#343a40").pack(anchor="w", pady=(0, 5))
        
        self.issuer_entry = tk.Entry(parent,
                                    font=self.body_font,
                                    relief="solid",
                                    bd=1,
                                    bg="#f8f9fa")
        self.issuer_entry.pack(fill="x", pady=(0, 20), ipady=8)
        self.issuer_entry.insert(0, "Google")
        
        # Account Name
        tk.Label(parent,
                text="Account Name *",
                font=self.label_font,
                bg="#ffffff",
                fg="#343a40").pack(anchor="w", pady=(0, 5))
        
        self.account_entry = tk.Entry(parent,
                                     font=self.body_font,
                                     relief="solid",
                                     bd=1,
                                     bg="#f8f9fa")
        self.account_entry.pack(fill="x", pady=(0, 20), ipady=8)
        self.account_entry.insert(0, "user@example.com")
        
        # Secret Key
        tk.Label(parent,
                text="Secret Key *",
                font=self.label_font,
                bg="#ffffff",
                fg="#343a40").pack(anchor="w", pady=(0, 5))
        
        self.secret_entry = tk.Entry(parent,
                                    font=font.Font(family="Consolas", size=11),
                                    relief="solid",
                                    bd=1,
                                    bg="#f8f9fa",
                                    show="*")
        self.secret_entry.pack(fill="x", pady=(0, 10), ipady=8)
        
        # Show/Hide secret button
        show_frame = tk.Frame(parent, bg="#ffffff")
        show_frame.pack(fill="x", pady=(0, 20))
        
        self.show_secret_var = tk.BooleanVar()
        show_cb = tk.Checkbutton(show_frame,
                                text="Show secret key",
                                variable=self.show_secret_var,
                                command=self.toggle_secret_visibility,
                                font=self.body_font,
                                bg="#ffffff",
                                fg="#6c757d")
        show_cb.pack(anchor="w")
        
        # Advanced options
        advanced_frame = tk.LabelFrame(parent,
                                      text="Advanced Options",
                                      font=self.label_font,
                                      bg="#ffffff",
                                      fg="#343a40",
                                      relief="solid",
                                      bd=1)
        advanced_frame.pack(fill="x", pady=(0, 20), padx=5)
        
        # Digits
        digits_frame = tk.Frame(advanced_frame, bg="#ffffff")
        digits_frame.pack(fill="x", padx=15, pady=10)
        
        tk.Label(digits_frame,
                text="Code Length:",
                font=self.body_font,
                bg="#ffffff",
                fg="#343a40").pack(side="left")
        
        self.digits_var = tk.StringVar(value="6")
        digits_combo = ttk.Combobox(digits_frame,
                                   textvariable=self.digits_var,
                                   values=["6", "7", "8"],
                                   state="readonly",
                                   width=5)
        digits_combo.pack(side="right")
        
        # Period
        period_frame = tk.Frame(advanced_frame, bg="#ffffff")
        period_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        tk.Label(period_frame,
                text="Time Period (seconds):",
                font=self.body_font,
                bg="#ffffff",
                fg="#343a40").pack(side="left")
        
        self.period_var = tk.StringVar(value="30")
        period_combo = ttk.Combobox(period_frame,
                                   textvariable=self.period_var,
                                   values=["15", "30", "60"],
                                   state="readonly",
                                   width=5)
        period_combo.pack(side="right")
        
        # Algorithm
        algo_frame = tk.Frame(advanced_frame, bg="#ffffff")
        algo_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        tk.Label(algo_frame,
                text="Algorithm:",
                font=self.body_font,
                bg="#ffffff",
                fg="#343a40").pack(side="left")
        
        self.algorithm_var = tk.StringVar(value="SHA1")
        algo_combo = ttk.Combobox(algo_frame,
                                 textvariable=self.algorithm_var,
                                 values=["SHA1", "SHA256", "SHA512"],
                                 state="readonly",
                                 width=8)
        algo_combo.pack(side="right")
    
    def create_buttons(self, parent):
        """Create dialog buttons"""
        btn_frame = tk.Frame(parent, bg="#ffffff")
        btn_frame.pack(fill="x", pady=(20, 0))
        
        # Cancel button
        cancel_btn = tk.Button(btn_frame,
                              text="Cancel",
                              font=self.body_font,
                              bg="#6c757d",
                              fg="#ffffff",
                              relief="flat",
                              padx=20,
                              pady=8,
                              cursor="hand2",
                              command=self.destroy)
        cancel_btn.pack(side="right", padx=(10, 0))
        
        # Add button
        add_btn = tk.Button(btn_frame,
                           text="➕ Add Account",
                           font=self.body_font,
                           bg="#28a745",
                           fg="#ffffff",
                           relief="flat",
                           padx=20,
                           pady=8,
                           cursor="hand2",
                           command=self.add_account)
        add_btn.pack(side="right")
    
    def toggle_secret_visibility(self):
        """Toggle secret key visibility"""
        if self.show_secret_var.get():
            self.secret_entry.configure(show="")
        else:
            self.secret_entry.configure(show="*")
    
    def add_account(self):
        """Add the OTP account"""
        try:
            # Validate input
            issuer = self.issuer_entry.get().strip()
            account = self.account_entry.get().strip()
            secret = self.secret_entry.get().strip()
            
            if not issuer or not account or not secret:
                messagebox.showerror("Validation Error", "Please fill in all required fields.")
                return
            
            # Prepare data
            data = {
                'issuer': issuer,
                'account': account,
                'secret': secret,
                'digits': int(self.digits_var.get()),
                'period': int(self.period_var.get()),
                'algorithm': self.algorithm_var.get()
            }
            
            # Add via API
            result = self.api_service.add_otp_account(**data)
            
            if result and result.get('success'):
                messagebox.showinfo("Success", "Account added successfully!")
                if self.callback:
                    self.callback()
                self.destroy()
            else:
                error_msg = result.get('error', 'Unknown error') if result else 'Failed to add account'
                messagebox.showerror("Error", f"Failed to add account:\n\n{error_msg}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error adding account:\n\n{str(e)}")


class QRScanDialog(tk.Toplevel):
    """Dialog for scanning QR codes"""
    
    def __init__(self, parent, api_service, callback):
        super().__init__(parent)
        
        self.api_service = api_service
        self.callback = callback
        
        self.title("📷 Scan QR Code")
        self.geometry("450x300")
        self.configure(bg="#ffffff")
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()
        
        # Center on parent
        self.center_on_parent(parent)
        
        # Fonts
        self.title_font = font.Font(family="Segoe UI", size=18, weight="bold")
        self.body_font = font.Font(family="Segoe UI", size=11)
        
        self.setup_ui()
    
    def center_on_parent(self, parent):
        """Center dialog on parent window"""
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")
    
    def setup_ui(self):
        """Setup dialog UI"""
        
        # Main frame
        main_frame = tk.Frame(self, bg="#ffffff")
        main_frame.pack(fill="both", expand=True, padx=30, pady=30)
        
        # Title
        tk.Label(main_frame,
                text="📷 Scan QR Code",
                font=self.title_font,
                bg="#ffffff",
                fg="#343a40").pack(pady=(0, 20))
        
        # Instructions
        instructions = ("Paste the otpauth:// URL from the QR code below.\n"
                       "This URL contains your secret key and account details.")
        
        tk.Label(main_frame,
                text=instructions,
                font=self.body_font,
                bg="#ffffff",
                fg="#6c757d",
                justify="center",
                wraplength=380).pack(pady=(0, 20))
        
        # URL input
        tk.Label(main_frame,
                text="QR Code URL:",
                font=font.Font(family="Segoe UI", size=11, weight="bold"),
                bg="#ffffff",
                fg="#343a40").pack(anchor="w", pady=(0, 5))
        
        self.url_text = tk.Text(main_frame,
                               height=4,
                               font=font.Font(family="Consolas", size=10),
                               relief="solid",
                               bd=1,
                               bg="#f8f9fa",
                               wrap="word")
        self.url_text.pack(fill="x", pady=(0, 20))
        
        # Buttons
        btn_frame = tk.Frame(main_frame, bg="#ffffff")
        btn_frame.pack(fill="x")
        
        # Cancel button
        cancel_btn = tk.Button(btn_frame,
                              text="Cancel",
                              font=self.body_font,
                              bg="#6c757d",
                              fg="#ffffff",
                              relief="flat",
                              padx=20,
                              pady=8,
                              cursor="hand2",
                              command=self.destroy)
        cancel_btn.pack(side="right", padx=(10, 0))
        
        # Parse button
        parse_btn = tk.Button(btn_frame,
                             text="📷 Parse QR Code",
                             font=self.body_font,
                             bg="#17a2b8",
                             fg="#ffffff",
                             relief="flat",
                             padx=20,
                             pady=8,
                             cursor="hand2",
                             command=self.parse_qr_code)
        parse_btn.pack(side="right")
    
    def parse_qr_code(self):
        """Parse QR code URL"""
        try:
            url = self.url_text.get("1.0", "end-1c").strip()
            
            if not url:
                messagebox.showerror("Validation Error", "Please paste the QR code URL.")
                return
            
            if not url.startswith('otpauth://'):
                messagebox.showerror("Invalid URL", "Please enter a valid otpauth:// URL.")
                return
            
            # Parse via API
            result = self.api_service.parse_qr_code(url)
            
            if result and result.get('success'):
                messagebox.showinfo("Success", "QR code parsed and account added successfully!")
                if self.callback:
                    self.callback()
                self.destroy()
            else:
                error_msg = result.get('error', 'Unknown error') if result else 'Failed to parse QR code'
                messagebox.showerror("Parse Error", f"Failed to parse QR code:\n\n{error_msg}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error parsing QR code:\n\n{str(e)}")


if __name__ == "__main__":
    # Test the OTP window
    root = tk.Tk()
    root.withdraw()  # Hide root window
    
    # Mock API service for testing
    class MockAPIService:
        def get_otp_accounts(self):
            return {
                'success': True,
                'accounts': [
                    {
                        'id': '1',
                        'issuer': 'Google',
                        'account': 'user@gmail.com',
                        'digits': 6,
                        'period': 30,
                        'algorithm': 'SHA1'
                    },
                    {
                        'id': '2',
                        'issuer': 'GitHub',
                        'account': 'developer',
                        'digits': 6,
                        'period': 30,
                        'algorithm': 'SHA1'
                    }
                ]
            }
        
        def generate_all_otps(self):
            return {
                'success': True,
                'otp_accounts': [
                    {
                        'id': '1',
                        'issuer': 'Google',
                        'account': 'user@gmail.com',
                        'otp_code': '123456',
                        'time_remaining': 25,
                        'period': 30,
                        'digits': 6
                    },
                    {
                        'id': '2',
                        'issuer': 'GitHub',
                        'account': 'developer',
                        'otp_code': '789012',
                        'time_remaining': 15,
                        'period': 30,
                        'digits': 6
                    }
                ]
            }
    
    # Show OTP window
    otp_window = OTPWindow(root, MockAPIService())
    root.mainloop()