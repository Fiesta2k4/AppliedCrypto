class VaultEntryDialog(tk.Toplevel):
    def __init__(self, parent, api_service):
        super().__init__(parent)
        self.api_service = api_service
        self.result = None
        
        self.title("Add Vault Entry")
        self.geometry("400x500")
        self.transient(parent)
        self.grab_set()
        
        self.create_form()
    
    def create_form(self):
        main_frame = tk.Frame(self, padx=20, pady=20)
        main_frame.pack(fill="both", expand=True)
        
        # Entry type
        tk.Label(main_frame, text="Type:").pack(anchor="w")
        self.type_var = tk.StringVar(value="password")
        type_combo = ttk.Combobox(main_frame, textvariable=self.type_var,
                                 values=["password", "note", "card", "identity"])
        type_combo.pack(fill="x", pady=(0, 10))
        
        # Name
        tk.Label(main_frame, text="Name:").pack(anchor="w")
        self.name_entry = tk.Entry(main_frame)
        self.name_entry.pack(fill="x", pady=(0, 10))
        
        # Username
        tk.Label(main_frame, text="Username:").pack(anchor="w")
        self.username_entry = tk.Entry(main_frame)
        self.username_entry.pack(fill="x", pady=(0, 10))
        
        # Password/Secret
        tk.Label(main_frame, text="Password/Secret:").pack(anchor="w")
        self.password_entry = tk.Entry(main_frame, show="*")
        self.password_entry.pack(fill="x", pady=(0, 10))
        
        # URL
        tk.Label(main_frame, text="URL:").pack(anchor="w")
        self.url_entry = tk.Entry(main_frame)
        self.url_entry.pack(fill="x", pady=(0, 10))
        
        # Notes
        tk.Label(main_frame, text="Notes:").pack(anchor="w")
        self.notes_text = tk.Text(main_frame, height=4)
        self.notes_text.pack(fill="x", pady=(0, 20))
        
        # Buttons
        btn_frame = tk.Frame(main_frame)
        btn_frame.pack(fill="x")
        
        tk.Button(btn_frame, text="Save", command=self.save_entry).pack(side="right", padx=5)
        tk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side="right")
    
    def save_entry(self):
        # Collect form data
        entry_data = {
            'type': self.type_var.get(),
            'name': self.name_entry.get(),
            'username': self.username_entry.get(),
            'password': self.password_entry.get(),
            'url': self.url_entry.get(),
            'notes': self.notes_text.get(1.0, tk.END).strip()
        }
        
        if not entry_data['name']:
            messagebox.showerror("Error", "Name is required")
            return
        
        # Create encrypted entry
        result = self.api_service.create_vault_entry(entry_data)
        
        if result and 'id' in result:
            messagebox.showinfo("Success", "Entry saved successfully!")
            self.result = result
            self.destroy()
        else:
            error_msg = result.get('error', 'Unknown error') if result else 'Save failed'
            messagebox.showerror("Error", f"Failed to save entry: {error_msg}")