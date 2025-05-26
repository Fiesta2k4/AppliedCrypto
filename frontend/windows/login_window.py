import tkinter as tk
from tkinter import messagebox, font
from concurrent.futures import ThreadPoolExecutor
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, project_root)

try:
    from frontend.services.api_service import ApiService
    from frontend.windows.main_window import MainWindow
except ImportError as e:
    print(f"Import error in login_window: {e}")
    ApiService = None
    MainWindow = None

class LoginWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        
        self.title("Personal Vault - Secure Login")
        self.geometry("450x600")
        self.configure(bg="#f8f9fa")
        self.resizable(False, False)
        
        # Center window
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (450 // 2)
        y = (self.winfo_screenheight() // 2) - (600 // 2)
        self.geometry(f"450x600+{x}+{y}")
        
        # Fonts
        self.title_font = font.Font(family="Segoe UI", size=24, weight="bold")
        self.subtitle_font = font.Font(family="Segoe UI", size=11)
        self.label_font = font.Font(family="Segoe UI", size=11)
        self.button_font = font.Font(family="Segoe UI", size=12, weight="bold")
        
        self.create_ui()
        
    def create_ui(self):
        """Create the login UI"""
        # Main container
        main_frame = tk.Frame(self, bg="#f8f9fa", padx=40, pady=30)
        main_frame.pack(fill="both", expand=True)
        
        # Header with logo
        header_frame = tk.Frame(main_frame, bg="#f8f9fa")
        header_frame.pack(fill="x", pady=(0, 40))
        
        # Logo/Icon
        icon_label = tk.Label(header_frame,
                             text="🔐",
                             font=font.Font(size=48),
                             bg="#f8f9fa")
        icon_label.pack(pady=(0, 10))
        
        tk.Label(header_frame,
                text="Personal Vault",
                font=self.title_font,
                bg="#f8f9fa",
                fg="#2c3e50").pack()
        
        tk.Label(header_frame,
                text="Your passwords, secured with modern cryptography",
                font=self.subtitle_font,
                bg="#f8f9fa",
                fg="#7f8c8d").pack(pady=(5, 0))
        
        # Login form card
        card_frame = tk.Frame(main_frame, bg="white", relief="solid", bd=1)
        card_frame.pack(fill="x", pady=20, padx=20)
        
        # Add shadow effect
        shadow_frame = tk.Frame(main_frame, bg="#e9ecef", height=2)
        shadow_frame.pack(fill="x", padx=22)
        
        # Form content
        form_content = tk.Frame(card_frame, bg="white", padx=40, pady=40)
        form_content.pack(fill="both", expand=True)
        
        tk.Label(form_content,
                text="Welcome Back",
                font=font.Font(family="Segoe UI", size=18, weight="bold"),
                bg="white",
                fg="#2c3e50").pack(pady=(0, 30))
        
        # Email field
        email_frame = tk.Frame(form_content, bg="white")
        email_frame.pack(fill="x", pady=(0, 20))
        
        tk.Label(email_frame,
                text="Email Address",
                font=self.label_font,
                bg="white",
                fg="#495057").pack(anchor="w", pady=(0, 5))
        
        self.email_entry = tk.Entry(email_frame,
                                   font=font.Font(family="Segoe UI", size=12),
                                   relief="solid",
                                   bd=1,
                                   bg="#f8f9fa",
                                   fg="#495057",
                                   insertbackground="#495057")
        self.email_entry.pack(fill="x", ipady=8)
        
        # Password field
        password_frame = tk.Frame(form_content, bg="white")
        password_frame.pack(fill="x", pady=(0, 30))
        
        tk.Label(password_frame,
                text="Master Password",
                font=self.label_font,
                bg="white",
                fg="#495057").pack(anchor="w", pady=(0, 5))
        
        self.password_entry = tk.Entry(password_frame,
                                      font=font.Font(family="Segoe UI", size=12),
                                      relief="solid",
                                      bd=1,
                                      bg="#f8f9fa",
                                      fg="#495057",
                                      insertbackground="#495057",
                                      show="•")
        self.password_entry.pack(fill="x", ipady=8)
        
        # Login button
        self.login_btn = tk.Button(form_content,
                                  text="🔓 Sign In",
                                  font=self.button_font,
                                  bg="#007bff",
                                  fg="white",
                                  relief="flat",
                                  bd=0,
                                  command=self.login,
                                  cursor="hand2",
                                  pady=12)
        self.login_btn.pack(fill="x", pady=(0, 20))
        
        # Or divider
        divider_frame = tk.Frame(form_content, bg="white")
        divider_frame.pack(fill="x", pady=(0, 20))
        
        divider_line1 = tk.Frame(divider_frame, bg="#dee2e6", height=1)
        divider_line1.pack(side="left", fill="x", expand=True, pady=10)
        
        tk.Label(divider_frame,
                text=" or ",
                font=self.label_font,
                bg="white",
                fg="#6c757d").pack(side="left")
        
        divider_line2 = tk.Frame(divider_frame, bg="#dee2e6", height=1)
        divider_line2.pack(side="left", fill="x", expand=True, pady=10)
        
        # Register button
        self.register_btn = tk.Button(form_content,
                                     text="🔐 Create New Account",
                                     font=self.button_font,
                                     bg="white",
                                     fg="#007bff",
                                     relief="solid",
                                     bd=1,
                                     command=self.show_register,
                                     cursor="hand2",
                                     pady=12)
        self.register_btn.pack(fill="x")
        
        # Status and help
        bottom_frame = tk.Frame(main_frame, bg="#f8f9fa")
        bottom_frame.pack(fill="x", pady=(20, 0))
        
        # Status label
        self.status_label = tk.Label(bottom_frame,
                                    text="",
                                    font=self.label_font,
                                    bg="#f8f9fa",
                                    fg="#dc3545")
        self.status_label.pack(pady=(0, 10))
        
        # Help text
        help_frame = tk.Frame(bottom_frame, bg="#f8f9fa")
        help_frame.pack()
        
        tk.Label(help_frame,
                text="🛡️ Your data is encrypted end-to-end",
                font=font.Font(family="Segoe UI", size=9),
                bg="#f8f9fa",
                fg="#6c757d").pack()
        
        tk.Label(help_frame,
                text="🔒 Zero-knowledge architecture",
                font=font.Font(family="Segoe UI", size=9),
                bg="#f8f9fa",
                fg="#6c757d").pack()
        
        # Bind Enter key
        self.bind('<Return>', lambda e: self.login())
        self.bind('<Escape>', lambda e: self.quit())
        
        # Focus on email entry
        self.email_entry.focus_set()
        
        # Add hover effects
        self._add_hover_effects()
    
    def _add_hover_effects(self):
        """Add hover effects to buttons"""
        def on_enter_login(e):
            self.login_btn.config(bg="#0056b3")
        
        def on_leave_login(e):
            self.login_btn.config(bg="#007bff")
        
        def on_enter_register(e):
            self.register_btn.config(bg="#f8f9fa", fg="#0056b3")
        
        def on_leave_register(e):
            self.register_btn.config(bg="white", fg="#007bff")
        
        self.login_btn.bind("<Enter>", on_enter_login)
        self.login_btn.bind("<Leave>", on_leave_login)
        self.register_btn.bind("<Enter>", on_enter_register)
        self.register_btn.bind("<Leave>", on_leave_register)
    
    def show_register(self):
        """Show register window"""
        try:
            from frontend.windows.register_window import RegisterWindow
            
            # Create register window
            register_window = RegisterWindow(self)
            
            # Wait for register window to close
            self.wait_window(register_window)
            
        except ImportError as e:
            messagebox.showerror("Error", f"Cannot load register window: {e}")
    
    def validate_input(self):
        """Validate login input"""
        email = self.email_entry.get().strip()
        password = self.password_entry.get()
        
        if not email:
            self.show_status("Please enter your email address", "#dc3545")
            self.email_entry.focus_set()
            return False
        
        if not password:
            self.show_status("Please enter your password", "#dc3545")
            self.password_entry.focus_set()
            return False
        
        # Basic email validation
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            self.show_status("Please enter a valid email address", "#dc3545")
            self.email_entry.focus_set()
            return False
        
        return True
    
    def login(self):
        """Handle login"""
        if not self.validate_input():
            return
        
        email = self.email_entry.get().strip()
        password = self.password_entry.get()
        
        # Disable UI
        self.login_btn.config(state="disabled", text="🔄 Signing In...")
        self.register_btn.config(state="disabled")
        self.email_entry.config(state="disabled")
        self.password_entry.config(state="disabled")
        
        self.show_status("Authenticating with secure server...", "#17a2b8")
        
        # Use thread to avoid blocking UI
        executor = ThreadPoolExecutor(max_workers=1)
        future = executor.submit(self._do_login, email, password)
        
        def check_result():
            if future.done():
                self._reset_ui()
                try:
                    result = future.result()
                    if result:
                        self._handle_login_result(email, result)
                except Exception as e:
                    self._on_error(f"Login error: {str(e)}")
                finally:
                    executor.shutdown()
            else:
                self.after(100, check_result)
        
        self.after(100, check_result)
    
    def _do_login(self, email, password):
        """Perform login in background thread"""
        if not ApiService:
            raise Exception("API service not available")
        
        api_service = ApiService()
        result = api_service.login(email, password)
        
        if result and 'access_token' in result:
            return {'api_service': api_service, 'result': result}
        else:
            error_msg = result.get('error', 'Invalid credentials') if result else 'Login failed'
            raise Exception(error_msg)
    
    def _handle_login_result(self, email, login_data):
        """Handle successful login"""
        api_service = login_data['api_service']
        result = login_data['result']
        
        self.show_status("✅ Login successful!", "#28a745")
        
        # Show success message
        user_info = result.get('user', {})
        user_id = user_info.get('id', 'Unknown')
        
        self.after(500, lambda: self._open_main_window(email, api_service, user_info))
    
    def _open_main_window(self, email, api_service, user_info):
        """Open main application window"""
        try:
            # Hide login window
            self.withdraw()
            
            if MainWindow:
                main_window = MainWindow(self, user_email=email, api_service=api_service)
                
                # Show welcome message
                messagebox.showinfo("Welcome Back!", 
                                  f"Welcome to Personal Vault!\n\n"
                                  f"Email: {email}\n"
                                  f"User ID: {user_info.get('id', 'Unknown')[:8]}...\n\n"
                                  f"Your encrypted vault is ready to use.")
            else:
                messagebox.showerror("Error", "Main window not available")
                self.deiconify()
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open main window: {str(e)}")
            self.deiconify()
    
    def _on_error(self, error_message):
        """Handle login error"""
        self.show_status(f"❌ {error_message}", "#dc3545")
        messagebox.showerror("Login Failed", 
                           f"Authentication failed:\n\n{error_message}\n\n"
                           f"Please check your credentials and try again.")
    
    def _reset_ui(self):
        """Reset UI to normal state"""
        self.login_btn.config(state="normal", text="🔓 Sign In")
        self.register_btn.config(state="normal")
        self.email_entry.config(state="normal")
        self.password_entry.config(state="normal")
    
    def show_status(self, message, color="#333"):
        """Show status message"""
        self.status_label.config(text=message, fg=color)

if __name__ == "__main__":
    print("🔐 Starting Personal Vault Login...")
    app = LoginWindow()
    app.mainloop()
