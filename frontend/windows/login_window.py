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

class LoginWindow(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        
        print("🔍 === LOGIN WINDOW INIT ===")
        
        # ✅ Create API service properly
        if ApiService:
            self.api_service = ApiService()
            print(f"✅ API service created in LoginWindow: {self.api_service}")
        else:
            self.api_service = None
            print("❌ ApiService class not available")
        
        # Window settings
        self.title("Personal Vault - Secure Login")
        self.geometry("800x800")
        self.configure(bg="#f8f9fa")
        self.resizable(True, True)
        
        # Center window
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (450 // 2)
        y = (self.winfo_screenheight() // 2) - (600 // 2)
        self.geometry(f"800x800+{x}+{y}")
        
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
        """Handle login attempt"""
        try:
            print("🔍 === LOGIN ATTEMPT ===")
            
            email = self.email_entry.get().strip()
            password = self.password_entry.get()
            
            if not email or not password:
                messagebox.showerror("Error", "Please enter both email and password")
                return
            
            print(f"🔍 Login attempt for: {email}")
            print(f"🔍 API service before login: {self.api_service}")
            print(f"🔍 API service token before: {getattr(self.api_service, 'access_token', 'NOT FOUND')}")
            
            # Disable login button
            self.login_btn.config(state="disabled", text="Logging in...")
            self.update()
            
            # Attempt login
            login_result = self.api_service.login(email, password)
            
            print(f"🔍 Login result: {login_result}")
            print(f"🔍 API service token after: {getattr(self.api_service, 'access_token', 'NOT FOUND')}")
            
            # Re-enable login button
            self.login_btn.config(state="normal", text="🔐 Login")
            
            # ✅ FIX: Check for access_token instead of 'success' field
            if login_result and 'access_token' in login_result:
                print("✅ Login successful!")
                
                # Test API with token immediately
                print("🔍 Testing API with new token...")
                test_result = self.api_service.get_profile()
                print(f"🔍 Profile test result: {test_result}")
                
                # Handle success
                self.handle_login_success(login_result)
            else:
                error_msg = login_result.get('error', 'Login failed') if login_result else 'Network error'
                print(f"❌ Login failed: {error_msg}")
                messagebox.showerror("Login Failed", f"Login failed:\n\n{error_msg}")
                
        except Exception as e:
            print(f"❌ Login error: {e}")
            import traceback
            traceback.print_exc()
            self.login_btn.config(state="normal", text="🔐 Login")
            messagebox.showerror("Error", f"Login error:\n\n{str(e)}")

    def handle_login_success(self, login_response):
        """Handle successful login"""
        try:
            print("🔍 === HANDLE LOGIN SUCCESS ===")
            print(f"🔍 Login response: {login_response}")
            print(f"🔍 API service: {self.api_service}")
            print(f"🔍 API service token: {getattr(self.api_service, 'access_token', 'NOT FOUND')}")
            
            # Hide login window
            self.withdraw()
            
            # Get user data
            user_data = login_response.get('user', {})
            user_email = user_data.get('email', 'Unknown')
            
            print(f"🔍 User email: {user_email}")
            print(f"🔍 Creating MainWindow with API service...")
            
            # CRITICAL: Pass the SAME API service instance that has the token!
            from .main_window import MainWindow
            main_window = MainWindow(
                master=self.master,
                user_email=user_email,
                api_service=self.api_service  # ← This MUST have the access token
            )
            
            print(f"✅ MainWindow created successfully")
            print(f"🔍 MainWindow API service: {getattr(main_window, 'api_service', 'NOT FOUND')}")
            print(f"🔍 MainWindow API token: {getattr(main_window.api_service, 'access_token', 'NOT FOUND') if hasattr(main_window, 'api_service') else 'NO API SERVICE'}")
            
            # Wait for main window to close, then show login again
            self.wait_window(main_window)
            self.deiconify()
            
        except Exception as e:
            print(f"❌ Login success handler error: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Error", f"Failed to open main window:\n\n{str(e)}")
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
