import tkinter as tk
from tkinter import messagebox, font
import re
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, project_root)

try:
    from frontend.services.api_service import ApiService
except ImportError as e:
    print(f"Import error in register_window: {e}")
    ApiService = None

class RegisterWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        
        self.title("Personal Vault - Create Account")
        self.geometry("500x750")
        self.configure(bg="#f8f9fa")
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()
        
        # Center window
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (500 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (750 // 2)
        self.geometry(f"500x750+{x}+{y}")
        
        # Fonts
        self.title_font = font.Font(family="Segoe UI", size=20, weight="bold")
        self.subtitle_font = font.Font(family="Segoe UI", size=11)
        self.label_font = font.Font(family="Segoe UI", size=11)
        self.button_font = font.Font(family="Segoe UI", size=12, weight="bold")
        
        self.create_ui()
        
    def create_ui(self):
        """Create the register UI"""
        # Main container
        main_frame = tk.Frame(self, bg="#f8f9fa", padx=40, pady=30)
        main_frame.pack(fill="both", expand=True)
        
        # Header
        header_frame = tk.Frame(main_frame, bg="#f8f9fa")
        header_frame.pack(fill="x", pady=(0, 30))
        
        # Logo
        tk.Label(header_frame,
                text="🔐",
                font=font.Font(size=36),
                bg="#f8f9fa").pack()
        
        tk.Label(header_frame,
                text="Join Personal Vault",
                font=self.title_font,
                bg="#f8f9fa",
                fg="#2c3e50").pack(pady=(10, 5))
        
        tk.Label(header_frame,
                text="Create your secure, encrypted password vault",
                font=self.subtitle_font,
                bg="#f8f9fa",
                fg="#7f8c8d").pack()
        
        # Register form card
        card_frame = tk.Frame(main_frame, bg="white", relief="solid", bd=1)
        card_frame.pack(fill="x", pady=20, padx=20)
        
        # Form content
        form_content = tk.Frame(card_frame, bg="white", padx=40, pady=40)
        form_content.pack(fill="both", expand=True)
        
        tk.Label(form_content,
                text="Create Your Account",
                font=font.Font(family="Segoe UI", size=16, weight="bold"),
                bg="white",
                fg="#2c3e50").pack(pady=(0, 25))
        
        # Email field
        email_frame = tk.Frame(form_content, bg="white")
        email_frame.pack(fill="x", pady=(0, 15))
        
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
        password_frame.pack(fill="x", pady=(0, 10))
        
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
        
        # Password strength indicator
        self.strength_frame = tk.Frame(form_content, bg="white")
        self.strength_frame.pack(fill="x", pady=(5, 15))
        
        self.strength_label = tk.Label(self.strength_frame,
                                      text="Enter a password to see strength",
                                      font=font.Font(family="Segoe UI", size=9),
                                      bg="white",
                                      fg="#6c757d")
        self.strength_label.pack(anchor="w")
        
        # Strength bar
        self.strength_bar_frame = tk.Frame(self.strength_frame, bg="white")
        self.strength_bar_frame.pack(fill="x", pady=(2, 0))
        
        self.strength_bars = []
        for i in range(4):
            bar = tk.Frame(self.strength_bar_frame, bg="#e9ecef", height=4, width=70)
            bar.pack(side="left", padx=(0, 5))
            self.strength_bars.append(bar)
        
        # Bind password entry
        self.password_entry.bind('<KeyRelease>', self.check_password_strength)
        
        # Confirm Password field
        confirm_frame = tk.Frame(form_content, bg="white")
        confirm_frame.pack(fill="x", pady=(0, 20))
        
        tk.Label(confirm_frame,
                text="Confirm Master Password",
                font=self.label_font,
                bg="white",
                fg="#495057").pack(anchor="w", pady=(0, 5))
        
        self.confirm_password_entry = tk.Entry(confirm_frame,
                                              font=font.Font(family="Segoe UI", size=12),
                                              relief="solid",
                                              bd=1,
                                              bg="#f8f9fa",
                                              fg="#495057",
                                              insertbackground="#495057",
                                              show="•")
        self.confirm_password_entry.pack(fill="x", ipady=8)
        
        # Terms checkbox
        terms_frame = tk.Frame(form_content, bg="white")
        terms_frame.pack(fill="x", pady=(0, 25))
        
        self.terms_var = tk.BooleanVar()
        terms_check = tk.Checkbutton(terms_frame,
                                    variable=self.terms_var,
                                    bg="white",
                                    activebackground="white",
                                    text="I agree to the Terms of Service and Privacy Policy",
                                    font=font.Font(family="Segoe UI", size=10))
        terms_check.pack(anchor="w")
        
        # Register button
        self.register_btn = tk.Button(form_content,
                                     text="🔐 Create Account",
                                     font=self.button_font,
                                     bg="#28a745",
                                     fg="white",
                                     relief="flat",
                                     bd=0,
                                     command=self.register,
                                     cursor="hand2",
                                     pady=12)
        self.register_btn.pack(fill="x", pady=(0, 15))
        
        # Back to login
        back_frame = tk.Frame(form_content, bg="white")
        back_frame.pack(fill="x")
        
        tk.Label(back_frame,
                text="Already have an account?",
                font=self.label_font,
                bg="white",
                fg="#6c757d").pack(side="left")
        
        back_link = tk.Label(back_frame,
                             text="Sign in here",
                             font=self.label_font,
                             bg="white",
                             fg="#007bff",
                             cursor="hand2")
        back_link.pack(side="left", padx=(5, 0))
        back_link.bind("<Button-1>", self.go_back)
        
        # Status label
        self.status_label = tk.Label(main_frame,
                                    text="",
                                    font=self.label_font,
                                    bg="#f8f9fa",
                                    fg="#dc3545")
        self.status_label.pack(pady=10)
        
        # Security info
        security_frame = tk.Frame(main_frame, bg="#f8f9fa")
        security_frame.pack(fill="x", pady=(10, 0))
        
        tk.Label(security_frame,
                text="🔒 Your master password is never stored on our servers",
                font=font.Font(family="Segoe UI", size=9),
                bg="#f8f9fa",
                fg="#6c757d").pack()
        
        tk.Label(security_frame,
                text="🛡️ All data is encrypted locally before upload",
                font=font.Font(family="Segoe UI", size=9),
                bg="#f8f9fa",
                fg="#6c757d").pack()
        
        # Bind keys
        self.bind('<Return>', lambda e: self.register())
        self.bind('<Escape>', lambda e: self.destroy())
        
        # Focus on email
        self.email_entry.focus_set()
        
        # Add hover effects
        self._add_hover_effects()
    
    def _add_hover_effects(self):
        """Add hover effects to buttons"""
        def on_enter(e):
            self.register_btn.config(bg="#218838")
        
        def on_leave(e):
            self.register_btn.config(bg="#28a745")
        
        self.register_btn.bind("<Enter>", on_enter)
        self.register_btn.bind("<Leave>", on_leave)
    
    def check_password_strength(self, event=None):
        """Check and display password strength"""
        password = self.password_entry.get()
        
        if not password:
            self.strength_label.config(text="Enter a password to see strength", fg="#6c757d")
            self._update_strength_bars(0)
            return
        
        # Check criteria
        criteria = {
            'length': len(password) >= 8,
            'uppercase': re.search(r'[A-Z]', password) is not None,
            'lowercase': re.search(r'[a-z]', password) is not None,
            'number': re.search(r'\d', password) is not None,
            'special': re.search(r'[!@#$%^&*(),.?":{}|<>]', password) is not None
        }
        
        score = sum(criteria.values())
        
        if score <= 2:
            strength = "Weak"
            color = "#dc3545"
            bars = 1
        elif score == 3:
            strength = "Fair"
            color = "#ffc107"
            bars = 2
        elif score == 4:
            strength = "Good"
            color = "#fd7e14"
            bars = 3
        else:
            strength = "Strong"
            color = "#28a745"
            bars = 4
        
        # Show requirements
        missing = []
        if not criteria['length']:
            missing.append("8+ characters")
        if not criteria['uppercase']:
            missing.append("uppercase")
        if not criteria['lowercase']:
            missing.append("lowercase")
        if not criteria['number']:
            missing.append("number")
        if not criteria['special']:
            missing.append("special char")
        
        if missing:
            message = f"Password strength: {strength}. Need: {', '.join(missing)}"
        else:
            message = f"Password strength: {strength} ✓"
        
        self.strength_label.config(text=message, fg=color)
        self._update_strength_bars(bars, color)
    
    def _update_strength_bars(self, active_bars, color="#28a745"):
        """Update password strength bars"""
        for i, bar in enumerate(self.strength_bars):
            if i < active_bars:
                bar.config(bg=color)
            else:
                bar.config(bg="#e9ecef")
    
    def validate_form(self):
        """Validate registration form"""
        email = self.email_entry.get().strip()
        password = self.password_entry.get()
        confirm_password = self.confirm_password_entry.get()
        
        # Email validation
        if not email:
            self.show_status("Email is required", "#dc3545")
            self.email_entry.focus_set()
            return False
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            self.show_status("Please enter a valid email address", "#dc3545")
            self.email_entry.focus_set()
            return False
        
        # Password validation
        if not password:
            self.show_status("Password is required", "#dc3545")
            self.password_entry.focus_set()
            return False
        
        if len(password) < 8:
            self.show_status("Password must be at least 8 characters long", "#dc3545")
            self.password_entry.focus_set()
            return False
        
        if password != confirm_password:
            self.show_status("Passwords do not match", "#dc3545")
            self.confirm_password_entry.focus_set()
            return False
        
        # Terms acceptance
        if not self.terms_var.get():
            self.show_status("Please accept the Terms of Service", "#dc3545")
            return False
        
        return True
    
    def register(self):
        """Handle registration"""
        if not self.validate_form():
            return
        
        email = self.email_entry.get().strip()
        password = self.password_entry.get()
        
        # Disable UI
        self.register_btn.config(state="disabled", text="🔄 Creating Account...")
        self.email_entry.config(state="disabled")
        self.password_entry.config(state="disabled")
        self.confirm_password_entry.config(state="disabled")
        
        self.show_status("Creating your secure vault...", "#17a2b8")
        
        try:
            if not ApiService:
                self.show_status("Service not available", "#dc3545")
                return
            
            api_service = ApiService()
            result = api_service.register(email, password)
            
            if result and 'user' in result:
                # Registration successful
                self.show_status("✅ Account created successfully!", "#28a745")
                
                messagebox.showinfo("Welcome to Personal Vault!", 
                                   f"🎉 Your account has been created!\n\n"
                                   f"Email: {email}\n"
                                   f"User ID: {result['user']['id'][:8]}...\n\n"
                                   f"You can now access your encrypted vault.\n"
                                   f"Remember: Your master password cannot be recovered!")
                
                # Close and return to login
                self.destroy()
                
            else:
                # Registration failed
                error_msg = result.get('error', 'Registration failed') if result else 'Unknown error'
                self.show_status(f"❌ {error_msg}", "#dc3545")
                messagebox.showerror("Registration Failed", 
                                   f"Account creation failed:\n\n{error_msg}\n\n"
                                   f"Please try again or contact support.")
        
        except Exception as e:
            self.show_status(f"❌ Error: {str(e)}", "#dc3545")
            messagebox.showerror("Error", f"Registration failed:\n\n{str(e)}")
        
        finally:
            # Re-enable UI
            self._reset_ui()
    
    def _reset_ui(self):
        """Reset UI to normal state"""
        self.register_btn.config(state="normal", text="🔐 Create Account")
        self.email_entry.config(state="normal")
        self.password_entry.config(state="normal")
        self.confirm_password_entry.config(state="normal")
    
    def go_back(self, event=None):
        """Return to login window"""
        self.destroy()
    
    def show_status(self, message, color="#333"):
        """Show status message"""
        self.status_label.config(text=message, fg=color)

if __name__ == "__main__":
    # Test the register window
    root = tk.Tk()
    root.withdraw()
    
    register_window = RegisterWindow(root)
    root.mainloop()