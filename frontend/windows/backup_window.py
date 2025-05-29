import tkinter as tk
from tkinter import messagebox, font
from datetime import datetime

class BackupWindow(tk.Toplevel):
    """
    Backup and Recovery dialog as a separate window.
    """
    def __init__(self, master=None, api_service=None):
        super().__init__(master)
        self.api_service = api_service
        
        self.title("Backup & Recovery")
        self.geometry("500x400")
        self.configure(bg="white")
        self.resizable(True, True)
        self.transient(master)
        self.grab_set()

        # Fonts
        header_font = font.Font(family="Helvetica", size=16, weight="bold")
        btn_font = font.Font(family="Helvetica", size=12)

        # Header
        tk.Label(
            self,
            text="🔄 Backup & Recovery",
            font=header_font,
            bg="white",
            fg="#2c3e50"
        ).pack(pady=20)

        # Button frame
        button_frame = tk.Frame(self, bg="white")
        button_frame.pack(pady=20)

        # Create Backup button
        tk.Button(
            button_frame,
            text="📤 Create Backup",
            font=btn_font,
            bg="#28a745",
            fg="white",
            bd=0,
            padx=20,
            pady=10,
            cursor="hand2",
            command=self.create_backup
        ).pack(pady=10, fill="x")

        # Import Backup button
        tk.Button(
            button_frame,
            text="📥 Import Backup",
            font=btn_font,
            bg="#17a2b8",
            fg="white",
            bd=0,
            padx=20,
            pady=10,
            cursor="hand2",
            command=self.import_backup
        ).pack(pady=10, fill="x")

        # Manage Backups button
        tk.Button(
            button_frame,
            text="📋 Manage Backups",
            font=btn_font,
            bg="#6f42c1",
            fg="white",
            bd=0,
            padx=20,
            pady=10,
            cursor="hand2",
            command=self.manage_backups
        ).pack(pady=10, fill="x")

        # Status label
        self.status_label = tk.Label(
            self,
            text="Ready",
            font=font.Font(family="Helvetica", size=10),
            bg="white",
            fg="#666"
        )
        self.status_label.pack(pady=10)

    def create_backup(self):
        """Create backup of vault data"""
        try:
            print("🔍 === CREATE BACKUP ===")
            
            if not self.api_service:
                messagebox.showerror("Error", "API service not available")
                return
            
            # Get backup name from user
            from tkinter import simpledialog
            from datetime import datetime
            
            default_name = f"Backup {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            backup_name = simpledialog.askstring(
                "Backup Name", 
                "Enter backup name:",
                initialvalue=default_name
            )
            
            if not backup_name:
                print("🔍 Backup creation cancelled by user")
                return
            
            print(f"🔍 Creating backup with name: '{backup_name}'")
            
            # Get all vault entries
            print("🔍 Getting vault entries...")
            vault_response = self.api_service.get_vault_entries()
            
            if not vault_response or 'entries' not in vault_response:
                print("❌ Failed to get vault entries")
                messagebox.showerror("Error", "Failed to get vault entries for backup")
                return
            
            entries = vault_response['entries']
            print(f"🔍 Found {len(entries)} vault entries")
            
            # Create backup data structure
            backup_data = {
                "version": "1.0",
                "backup_type": "full_vault",
                "created_at": datetime.now().isoformat(),
                "entry_count": len(entries),
                "encrypted_entries": entries
            }
            
            print(f"🔍 Backup data structure created")
            print(f"   Version: {backup_data['version']}")
            print(f"   Type: {backup_data['backup_type']}")
            print(f"   Entries: {backup_data['entry_count']}")
            
            # Disable create button
            if hasattr(self, 'create_btn'):
                self.create_btn.config(state="disabled", text="Creating...")
                self.update()
            
            # Create backup via API
            result = self.api_service.create_backup(backup_data, backup_name)
            
            # Re-enable create button
            if hasattr(self, 'create_btn'):
                self.create_btn.config(state="normal", text="📦 Create Backup")
            
            print(f"🔍 Backup creation result: {result}")
            
            if result and result.get('success'):
                backup_id = result.get('backup_id', 'unknown')
                size_bytes = result.get('size_bytes', 0)
                size_mb = round(size_bytes / (1024 * 1024), 2) if size_bytes > 0 else 0
                
                message = (
                    f"Backup created successfully!\n\n"
                    f"Name: {backup_name}\n"
                    f"ID: {backup_id}\n"
                    f"Entries: {len(entries)}\n"
                    f"Size: {size_mb} MB"
                )
                
                messagebox.showinfo("Backup Created", message)
                print(f"✅ Backup created successfully: {backup_id}")
                
                # Refresh backup list
                self.load_backups()
                
            else:
                error_msg = result.get('error', 'Unknown error') if result else 'Network error'
                print(f"❌ Backup creation failed: {error_msg}")
                messagebox.showerror("Backup Failed", f"Failed to create backup:\n\n{error_msg}")
        
        except Exception as e:
            print(f"❌ Create backup error: {e}")
            import traceback
            traceback.print_exc()
            
            # Re-enable create button
            if hasattr(self, 'create_btn'):
                self.create_btn.config(state="normal", text="📦 Create Backup")
            
            messagebox.showerror("Error", f"Backup creation failed:\n\n{str(e)}")

    def import_backup(self):
        """Import backup - redirect to main window"""
        try:
            # Close this window and let main window handle it
            messagebox.showinfo("Import Backup", 
                              "Please use the 'Import Backup' option in the main window sidebar for better experience.")
            self.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Import failed:\n\n{str(e)}")

    def manage_backups(self):
        """Manage existing backups"""
        try:
            # This could open a backup management window
            messagebox.showinfo("Manage Backups", "Backup management feature coming soon!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open backup manager:\n\n{str(e)}")

if __name__ == '__main__':
    # 1) Create a real root
    root = tk.Tk()
    # 2) Hide it so only your Toplevel shows
    root.withdraw()
    # 3) Create your BackupWindow as a child of that root
    bw = BackupWindow(root)
    # 4) Run the event loop on the root (not on bw)
    root.mainloop()