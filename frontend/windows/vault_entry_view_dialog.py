import tkinter as tk
from tkinter import ttk, messagebox, font
import json

class VaultEntryViewDialog(tk.Toplevel):
    """Dialog to view vault entry details with decrypted passwords"""
    
    def __init__(self, parent, entry_data, api_service=None):
        super().__init__(parent)
        self.parent = parent
        self.entry_data = entry_data
        self.api_service = api_service
        self.password_visible = False
        
        print(f"🔍 VaultEntryViewDialog init - Entry: {entry_data.get('id', 'unknown')}")
        print(f"🔍 Entry data keys: {list(entry_data.keys())}")
        
        entry_name = entry_data.get('metadata', {}).get('name', 'Unnamed')
        print(f"🔍 Entry name: {entry_name}")
        
        self.title(f"View Entry: {entry_name}")
        self.geometry("600x700")  # ✅ Larger window
        self.configure(bg="#f8f9fa")
        self.transient(parent)
        self.grab_set()
        
        # Center window
        self.center_window()
        
        # Fonts
        self.title_font = font.Font(family="Segoe UI", size=14, weight="bold")
        self.label_font = font.Font(family="Segoe UI", size=10, weight="bold")
        self.value_font = font.Font(family="Segoe UI", size=10)
        self.button_font = font.Font(family="Segoe UI", size=10, weight="bold")
        
        print(f"🔍 Creating UI...")
        self.create_simple_ui()  # ✅ Use simple UI
    
        print(f"🔍 Loading entry details...")
        self.load_entry_details()
        
        print(f"✅ VaultEntryViewDialog created successfully")
    
    def center_window(self):
        """Center window on parent"""
        self.update_idletasks()
        x = self.parent.winfo_x() + (self.parent.winfo_width() // 2) - (600 // 2)
        y = self.parent.winfo_y() + (self.parent.winfo_height() // 2) - (700 // 2)
        self.geometry(f"600x700+{x}+{y}")
    
    def create_simple_ui(self):
        """Create simple UI without canvas complications"""
        # Main frame
        main_frame = tk.Frame(self, bg="#f8f9fa", padx=20, pady=20)
        main_frame.pack(fill="both", expand=True)
        
        # Header
        header_frame = tk.Frame(main_frame, bg="#f8f9fa")
        header_frame.pack(fill="x", pady=(0, 20))
        
        entry_name = self.entry_data.get('metadata', {}).get('name', 'Unnamed Entry')
        entry_type = self.entry_data.get('metadata', {}).get('type', 'unknown')
        
        tk.Label(header_frame,
                text=f"🔑 {entry_name}",
                font=self.title_font,
                bg="#f8f9fa",
                fg="#2c3e50").pack(anchor="w")
        
        tk.Label(header_frame,
                text=f"Type: {entry_type.title()}",
                font=self.label_font,
                bg="#f8f9fa",
                fg="#6c757d").pack(anchor="w")
        
        # Separator
        tk.Frame(main_frame, height=2, bg="#dee2e6").pack(fill="x", pady=(0, 20))
        
        # Scrollable content frame
        canvas = tk.Canvas(main_frame, bg="#f8f9fa", highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        
        # Create scrollable frame
        self.content_frame = tk.Frame(canvas, bg="#f8f9fa")
        self.content_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.content_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Status label
        self.loading_label = tk.Label(self.content_frame,
                                     text="🔄 Decrypting entry...",
                                     font=self.value_font,
                                     bg="#f8f9fa",
                                     fg="#007bff")
        self.loading_label.pack(pady=50)
        
        # Button frame at bottom
        button_frame = tk.Frame(main_frame, bg="#f8f9fa")
        button_frame.pack(fill="x", pady=(20, 0))
        
        tk.Button(button_frame,
                 text="❌ Close",
                 font=self.button_font,
                 bg="#6c757d",
                 fg="white",
                 relief="flat",
                 command=self.destroy,
                 cursor="hand2",
                 padx=15,
                 pady=8).pack(side="right")
    
    def load_entry_details(self):
        """Load and decrypt entry details"""
        try:
            print(f"🔍 Loading entry details...")
            
            if not self.api_service:
                self.show_error("API service not available")
                return
            
            # Decrypt the entry data
            decrypted_data = self.decrypt_entry()
            
            if decrypted_data:
                print(f"✅ Decryption successful, displaying data...")
                self.display_decrypted_data(decrypted_data)
            else:
                self.show_error("Failed to decrypt entry data")
                
        except Exception as e:
            print(f"❌ Load entry details error: {e}")
            import traceback
            traceback.print_exc()
            self.show_error(f"Error loading entry: {str(e)}")
    
    def decrypt_entry(self):
        """Decrypt the vault entry"""
        try:
            print(f"🔍 Decrypting entry: {self.entry_data.get('id', 'unknown')}")
            
            # Check if we already have decrypted data
            if 'decrypted_data' in self.entry_data:
                print("✅ Using pre-decrypted data")
                decrypted_data = self.entry_data['decrypted_data']
                print(f"🔍 Pre-decrypted data: {decrypted_data}")
                return decrypted_data
            
            # Otherwise decrypt manually
            print("🔍 Decrypting manually...")
            
            if not self.api_service:
                print("❌ No API service")
                return None
            
            # Use API service to decrypt
            master_key = self.api_service.crypto_service.derive_master_key(
                self.api_service.user_password,
                self.api_service.user_salt
            )
            
            print(f"🔍 Master key derived: {len(master_key)} bytes")
            
            # Decrypt the entry
            decrypted_text = self.api_service.crypto_service.decrypt_data(
                iv=self.entry_data['iv'],
                ciphertext=self.entry_data['ciphertext'],
                tag=self.entry_data['tag'],
                key=master_key
            )
            
            print(f"🔍 Decrypted text: {decrypted_text[:100]}...")
            
            # Parse JSON
            decrypted_data = json.loads(decrypted_text)
            print(f"✅ Parsed data: {decrypted_data}")
            
            return decrypted_data
            
        except Exception as e:
            print(f"❌ Decryption error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def display_decrypted_data(self, data):
        """Display the decrypted entry data"""
        try:
            print(f"🔍 Displaying decrypted data: {data}")
            
            # Clear loading label
            self.loading_label.destroy()
            
            # Create scrollable frame
            canvas = tk.Canvas(self.content_frame, bg="#f8f9fa", highlightthickness=0)
            scrollbar = ttk.Scrollbar(self.content_frame, orient="vertical", command=canvas.yview)
            scrollable_frame = tk.Frame(canvas, bg="#f8f9fa")
            
            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            
            # Display fields based on entry type
            entry_type = data.get('type', 'password')
            print(f"🔍 Entry type: {entry_type}")
            
            if entry_type == 'password':
                self.display_password_fields(scrollable_frame, data)
            else:
                self.display_generic_fields(scrollable_frame, data)
            
            # Pack canvas and scrollbar
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
            print(f"✅ Data displayed successfully")
            
        except Exception as e:
            print(f"❌ Display data error: {e}")
            import traceback
            traceback.print_exc()
            self.show_error(f"Error displaying data: {str(e)}")
    
    def display_password_fields(self, parent, data):
        """Display password entry fields with simple layout"""
        print(f"🔍 Displaying password fields: {list(data.keys())}")
        
        # Create each field with spacing
        self.create_simple_field(parent, "Name", data.get('name', ''))
        self.create_simple_field(parent, "Username", data.get('username', ''))
        
        # Password field with LARGE buttons
        self.create_large_password_field(parent, "Password", data.get('password', ''))
        
        self.create_simple_field(parent, "URL", data.get('url', ''))
        self.create_simple_field(parent, "Notes", data.get('notes', ''))
        
        # Metadata
        tk.Frame(parent, height=2, bg="#dee2e6").pack(fill="x", pady=(20, 15))
        self.create_simple_field(parent, "Created", self.entry_data.get('created_at', ''))
        self.create_simple_field(parent, "Entry ID", self.entry_data.get('id', ''))
    
    def display_generic_fields(self, parent, data):
        """Display unknown entry type fields"""
        print(f"🔍 Displaying generic fields: {list(data.keys())}")
        
        for key, value in data.items():
            if key not in ['type']:
                if key.lower() == 'password':
                    self.create_password_field(parent, key.title(), str(value))
                else:
                    self.create_field(parent, key.title(), str(value))
        
        # Metadata
        self.create_separator(parent)
        self.create_field(parent, "Created", self.entry_data.get('created_at', ''))
        self.create_field(parent, "Entry ID", self.entry_data.get('id', ''))
    
    def create_simple_field(self, parent, label, value):
        """Create simple field without complications"""
        field_frame = tk.Frame(parent, bg="#f8f9fa")
        field_frame.pack(fill="x", pady=(0, 15))
        
        tk.Label(field_frame,
                text=f"{label}:",
                font=self.label_font,
                bg="#f8f9fa",
                fg="#495057").pack(anchor="w")
        
        entry = tk.Entry(field_frame,
                        font=self.value_font,
                        bg="white",
                        fg="#212529",
                        relief="solid",
                        bd=1,
                        state="normal")
        entry.insert(0, value)
        entry.config(state="readonly")
        entry.pack(fill="x", pady=(2, 0))
    
    def create_large_password_field(self, parent, label, value):
        """Create password field with LARGE visible buttons"""
        print(f"🔍 Creating LARGE password field: {label} = {value}")
        
        field_frame = tk.Frame(parent, bg="#f8f9fa")
        field_frame.pack(fill="x", pady=(0, 20))  # Extra spacing
        
        # Label
        tk.Label(field_frame,
                text=f"{label}:",
                font=self.label_font,
                bg="#f8f9fa",
                fg="#495057").pack(anchor="w")
        
        # Frame for entry and buttons
        input_frame = tk.Frame(field_frame, bg="#f8f9fa")
        input_frame.pack(fill="x", pady=(5, 0))
        
        # Password entry
        password_entry = tk.Entry(input_frame,
                                 font=self.value_font,
                                 bg="white",
                                 fg="#212529",
                                 relief="solid",
                                 bd=2,  # Thicker border
                                 state="normal",
                                 show="*")
        password_entry.insert(0, value)
        password_entry.config(state="readonly")
        password_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        # Button frame
        btn_frame = tk.Frame(input_frame, bg="#f8f9fa")
        btn_frame.pack(side="right")
        
        # Toggle button - LARGE
        def toggle_password():
            current_show = password_entry.cget('show')
            print(f"🔍 TOGGLE CLICKED! Current show: '{current_show}'")
            
            password_entry.config(state="normal")
            if current_show == '*':
                password_entry.config(show='')
                toggle_btn.config(text="🙈 HIDE", bg="#dc3545")
                print("👁️ Password is now VISIBLE!")
            else:
                password_entry.config(show='*')
                toggle_btn.config(text="👁️ SHOW", bg="#28a745")
                print("🙈 Password is now HIDDEN!")
            password_entry.config(state="readonly")
        
        # Large toggle button
        toggle_btn = tk.Button(btn_frame,
                              text="👁️ SHOW",
                              font=("Segoe UI", 12, "bold"),
                              bg="#28a745",
                              fg="white",
                              relief="raised",
                              bd=2,
                              command=toggle_password,
                              cursor="hand2",
                              width=8,
                              height=2)
        toggle_btn.pack(side="left", padx=(0, 5))
        
        # Large copy button
        copy_btn = tk.Button(btn_frame,
                            text="📋 COPY",
                            font=("Segoe UI", 12, "bold"),
                            bg="#007bff",
                            fg="white",
                            relief="raised",
                            bd=2,
                            command=lambda: self.copy_to_clipboard(value),
                            cursor="hand2",
                            width=8,
                            height=2)
        copy_btn.pack(side="left")
        
        print(f"✅ LARGE password field created with buttons!")
    
    def create_field(self, parent, label, value, is_url=False, is_multiline=False):
        """Create a field display"""
        print(f"🔍 Creating field: {label} = {value}")
        
        field_frame = tk.Frame(parent, bg="#f8f9fa")
        field_frame.pack(fill="x", pady=(0, 15))
        
        # Label
        tk.Label(field_frame,
                text=f"{label}:",
                font=self.label_font,
                bg="#f8f9fa",
                fg="#495057").pack(anchor="w")
        
        if is_multiline:
            # Text widget for multiline content
            text_widget = tk.Text(field_frame,
                                 height=4,
                                 wrap="word",
                                 font=self.value_font,
                                 bg="white",
                                 fg="#212529",
                                 relief="solid",
                                 bd=1,
                                 state="normal")
            text_widget.insert(1.0, value)
            text_widget.config(state="disabled")
            text_widget.pack(fill="x", pady=(2, 0))
        else:
            # Frame for value and copy button
            value_frame = tk.Frame(field_frame, bg="#f8f9fa")
            value_frame.pack(fill="x", pady=(2, 0))
            
            # Value entry (read-only)
            value_entry = tk.Entry(value_frame,
                                  font=self.value_font,
                                  bg="white",
                                  fg="#212529",
                                  relief="solid",
                                  bd=1,
                                  state="readonly")
            value_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
            
            # Insert value
            value_entry.config(state="normal")
            value_entry.delete(0, tk.END)
            value_entry.insert(0, value)
            value_entry.config(state="readonly")
            
            # Copy button
            tk.Button(value_frame,
                     text="📋",
                     font=self.button_font,
                     bg="#e9ecef",
                     fg="#495057",
                     relief="flat",
                     command=lambda v=value: self.copy_to_clipboard(v),
                     cursor="hand2",
                     padx=8,
                     pady=4).pack(side="right")
    
    def create_password_field(self, parent, label, value):
        """Create a password field with show/hide toggle"""
        print(f"🔍 Creating password field: {label} = {value}")
        
        field_frame = tk.Frame(parent, bg="#f8f9fa")
        field_frame.pack(fill="x", pady=(0, 15))
        
        # Label
        tk.Label(field_frame,
                text=f"{label}:",
                font=self.label_font,
                bg="#f8f9fa",
                fg="#495057").pack(anchor="w")
        
        # Frame for password field and buttons
        password_frame = tk.Frame(field_frame, bg="#f8f9fa")
        password_frame.pack(fill="x", pady=(2, 0))
        
        # Password entry
        password_var = tk.StringVar(value=value)
        password_entry = tk.Entry(password_frame,
                                 textvariable=password_var,
                                 font=self.value_font,
                                 bg="white",
                                 fg="#212529",
                                 relief="solid",
                                 bd=1,
                                 state="readonly",
                                 show="*")  # Hide by default
        password_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        # Toggle visibility button
        def toggle_password():
            try:
                current_show = password_entry.cget('show')
                print(f"🔍 Toggle password - current show: '{current_show}'")
                
                # Change entry state to normal for modification
                password_entry.config(state="normal")
                
                if current_show == '*':
                    password_entry.config(show='')
                    toggle_btn.config(text="🙈", bg="#dc3545")
                    print("👁️ Password now visible")
                else:
                    password_entry.config(show='*')
                    toggle_btn.config(text="👁️", bg="#6c757d")
                    print("🙈 Password now hidden")
                
                # Set back to readonly
                password_entry.config(state="readonly")
                
            except Exception as e:
                print(f"❌ Toggle password error: {e}")
                import traceback
                traceback.print_exc()
        
        toggle_btn = tk.Button(password_frame,
                              text="👁️",
                              font=self.button_font,
                              bg="#6c757d",
                              fg="white",
                              relief="flat",
                              command=toggle_password,
                              cursor="hand2",
                              padx=8,
                              pady=4)
        toggle_btn.pack(side="right", padx=(0, 5))
        
        # Copy button
        tk.Button(password_frame,
                 text="📋",
                 font=self.button_font,
                 bg="#e9ecef",
                 fg="#495057",
                 relief="flat",
                 command=lambda: self.copy_to_clipboard(value),
                 cursor="hand2",
                 padx=8,
                 pady=4).pack(side="right")
        
        print(f"✅ Password field created successfully")
    
    def create_separator(self, parent):
        """Create a visual separator"""
        separator = tk.Frame(parent, height=2, bg="#dee2e6")
        separator.pack(fill="x", pady=(20, 15))
    
    def copy_to_clipboard(self, text):
        """Copy text to clipboard"""
        try:
            self.clipboard_clear()
            self.clipboard_append(text)
            print(f"✅ Copied to clipboard: {text[:10]}...")
            messagebox.showinfo("Copied", "Text copied to clipboard!")
        except Exception as e:
            print(f"❌ Copy error: {e}")
            messagebox.showerror("Error", f"Failed to copy: {str(e)}")
    
    def show_error(self, message):
        """Show error message"""
        print(f"❌ Error: {message}")
        self.loading_label.config(text=f"❌ {message}", fg="#dc3545")

# Test if module is run directly
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    
    # Mock entry data with decrypted_data
    mock_entry = {
        'id': 'test-123',
        'iv': 'mock_iv',
        'ciphertext': 'mock_cipher',
        'tag': 'mock_tag',
        'metadata': {
            'name': 'Test Gmail',
            'type': 'password'
        },
        'created_at': '2024-01-15T10:30:45',
        'decrypted_data': {
            'type': 'password',
            'name': 'Test Gmail',
            'username': 'test@gmail.com',
            'password': 'mypassword123',
            'url': 'https://gmail.com',
            'notes': 'Test account'
        }
    }
    
    dialog = VaultEntryViewDialog(root, mock_entry)
    root.mainloop()