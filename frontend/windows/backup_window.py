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
        """Create new backup"""
        try:
            if not self.api_service:
                messagebox.showerror("Error", "API service not available")
                return
            
            self.status_label.config(text="Creating backup...", fg="#007bff")
            
            # Get vault data
            vault_data = self.api_service.get_vault_entries()
            
            if not vault_data or 'entries' not in vault_data:
                messagebox.showerror("Error", "No vault data to backup")
                self.status_label.config(text="No data to backup", fg="#dc3545")
                return
            
            # Create backup
            backup_data = {
                "version": "1.0",
                "backup_type": "full_vault",
                "created_at": datetime.now().isoformat(),
                "entry_count": vault_data['count'],
                "encrypted_entries": vault_data['entries']
            }
            
            result = self.api_service.create_backup(backup_data)
            
            if result and 'backup_id' in result:
                self.status_label.config(text="✅ Backup created!", fg="#28a745")
                messagebox.showinfo("Success", 
                                  f"Backup created successfully!\n\n"
                                  f"Name: {result.get('name', 'Unnamed')}\n"
                                  f"ID: {result['backup_id']}")
            else:
                error_msg = result.get('error', 'Unknown error') if result else 'Backup failed'
                self.status_label.config(text=f"❌ {error_msg}", fg="#dc3545")
                messagebox.showerror("Error", f"Backup failed:\n\n{error_msg}")
                
        except Exception as e:
            self.status_label.config(text=f"❌ Error: {str(e)}", fg="#dc3545")
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