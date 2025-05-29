import tkinter as tk
from tkinter import ttk, messagebox, font
from datetime import datetime

class BackupSelectionDialog(tk.Toplevel):
    def __init__(self, parent, api_service):
        print("🔍 === BACKUP SELECTION DIALOG INIT ===")
        print(f"🔍 parent: {parent}")
        print(f"🔍 parent type: {type(parent)}")
        print(f"🔍 parent class: {parent.__class__.__name__ if parent else 'None'}")
        print(f"🔍 api_service: {api_service}")
        print(f"🔍 api_service type: {type(api_service)}")
        
        # Check if parent is valid window
        try:
            parent_name = str(parent)
            print(f"🔍 parent window path: {parent_name}")
        except Exception as e:
            print(f"❌ Error getting parent info: {e}")
    
        super().__init__(parent)
        self.parent = parent
        self.api_service = api_service  # This should not be None!
        self.import_successful = False
        
        # Additional debug
        print(f"🔍 After assignment - self.api_service: {self.api_service}")
        print(f"🔍 self.api_service is None: {self.api_service is None}")
        
        if self.api_service is None:
            print("❌ CRITICAL: api_service is None!")
            messagebox.showerror("Error", "API service is not available. Please restart the application.")
            self.destroy()
            return
        
        self.title("Select Backup to Import")
        self.geometry("600x400")
        self.configure(bg="#f8f9fa")
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()
        
        # Center window
        self.center_window()
        
        # Fonts
        self.title_font = font.Font(family="Segoe UI", size=14, weight="bold")
        self.label_font = font.Font(family="Segoe UI", size=10)
        self.button_font = font.Font(family="Segoe UI", size=10, weight="bold")
        
        self.create_ui()
        self.load_backups()  # This will call the correct method now
        
        print("✅ BackupSelectionDialog initialized successfully")
        
    def center_window(self):
        """Center window on parent"""
        self.update_idletasks()
        x = self.parent.winfo_x() + (self.parent.winfo_width() // 2) - (600 // 2)
        y = self.parent.winfo_y() + (self.parent.winfo_height() // 2) - (400 // 2)
        self.geometry(f"600x400+{x}+{y}")
    
    def create_ui(self):
        """Create backup selection UI"""
        # Main frame
        main_frame = tk.Frame(self, bg="#f8f9fa", padx=20, pady=20)
        main_frame.pack(fill="both", expand=True)
        
        # Header
        tk.Label(main_frame,
                text="📁 Select Backup to Import",
                font=self.title_font,
                bg="#f8f9fa",
                fg="#2c3e50").pack(pady=(0, 20))
        
        # Backup list frame
        list_frame = tk.Frame(main_frame, bg="white", relief="solid", bd=1)
        list_frame.pack(fill="both", expand=True, pady=(0, 20))
        
        # Treeview for backups
        columns = ('Name', 'Created', 'Size', 'Status')
        self.backup_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=10)
        
        # Configure columns
        self.backup_tree.heading('Name', text='Backup Name')
        self.backup_tree.heading('Created', text='Created At')
        self.backup_tree.heading('Size', text='Size')
        self.backup_tree.heading('Status', text='Status')
        
        self.backup_tree.column('Name', width=200)
        self.backup_tree.column('Created', width=150)
        self.backup_tree.column('Size', width=100)
        self.backup_tree.column('Status', width=100)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.backup_tree.yview)
        self.backup_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack treeview and scrollbar
        self.backup_tree.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        scrollbar.pack(side="right", fill="y", pady=10)
        
        # Button frame
        button_frame = tk.Frame(main_frame, bg="#f8f9fa")
        button_frame.pack(fill="x", pady=(0, 10))
        
        # Buttons
        tk.Button(button_frame,
                 text="📥 Import Selected",
                 font=self.button_font,
                 bg="#28a745",
                 fg="white",
                 relief="flat",
                 command=self.import_selected,
                 cursor="hand2",
                 padx=20,
                 pady=8).pack(side="left", padx=(0, 10))
        
        tk.Button(button_frame,
                 text="🔄 Refresh",
                 font=self.button_font,
                 bg="#17a2b8",
                 fg="white",
                 relief="flat",
                 command=self.load_backups,
                 cursor="hand2",
                 padx=20,
                 pady=8).pack(side="left", padx=(0, 10))
        
        tk.Button(button_frame,
                 text="❌ Cancel",
                 font=self.button_font,
                 bg="#6c757d",
                 fg="white",
                 relief="flat",
                 command=self.destroy,
                 cursor="hand2",
                 padx=20,
                 pady=8).pack(side="right")
        
        # Status label
        self.status_label = tk.Label(main_frame,
                                    text="Loading backups...",
                                    font=self.label_font,
                                    bg="#f8f9fa",
                                    fg="#666")
        self.status_label.pack(pady=(10, 0))

    def debug_backup_api(self):
        """Debug backup API calls"""
        print("🔍 === DEBUG BACKUP API ===")
        
        # Test direct API call
        try:
            print("🔍 Testing direct API call...")
            result = self.api_service._make_request('GET', '/backup/list')
            print(f"🔍 Direct API result: {result}")
            
            if result:
                print(f"🔍 Result type: {type(result)}")
                print(f"🔍 Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
                
                if 'backups' in result:
                    backups = result['backups']
                    print(f"🔍 Backups count: {len(backups)}")
                    for i, backup in enumerate(backups):
                        print(f"🔍 Backup {i}: {backup}")
                else:
                    print("🔍 No 'backups' key in result")
            else:
                print("🔍 API returned None or empty result")
                
        except Exception as e:
            print(f"❌ Debug API error: {e}")
            import traceback
            traceback.print_exc()

    def load_backups(self):
        """Load available backups with detailed debugging"""
        try:
            print("🔍 === LOADING BACKUPS ===")
            self.status_label.config(text="Loading backups...", fg="#007bff")
            
            # Clear existing items
            for item in self.backup_tree.get_children():
                self.backup_tree.delete(item)
            
            # Debug API service
            print(f"🔍 API service exists: {self.api_service is not None}")
            if self.api_service:
                print(f"🔍 API service type: {type(self.api_service)}")
                print(f"🔍 API base URL: {self.api_service.base_url}")
                print(f"🔍 Has access token: {self.api_service.access_token is not None}")
                
            # Run debug
            self.debug_backup_api()
            
            # Get backups from API
            print("🔍 Calling api_service.get_backups()...")
            result = self.api_service.get_backups()
            
            print(f"🔍 get_backups() returned: {result}")
            print(f"🔍 Result type: {type(result)}")
            
            if result and isinstance(result, dict):
                print(f"🔍 Result keys: {list(result.keys())}")
                
                if 'error' in result:
                    print(f"❌ API Error: {result['error']}")
                    self.status_label.config(text=f"Error: {result['error']}", fg="#dc3545")
                    return
                
                if 'backups' in result:
                    backups = result['backups']
                    print(f"🔍 Found {len(backups)} backups")
                    
                    if backups:
                        for i, backup in enumerate(backups):
                            print(f"🔍 Processing backup {i}: {backup}")
                            
                            # Format date
                            created_date = backup.get('created_at', '')
                            if created_date:
                                try:
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
                        
                            # Insert into tree
                            tree_id = self.backup_tree.insert('', 'end', values=(
                                backup.get('name', 'Unnamed'),
                                formatted_date,
                                size_str,
                                backup.get('status', 'Unknown')
                            ), tags=(backup['id'],))
                            
                            print(f"✅ Added backup to tree: {tree_id}")
                        
                        self.status_label.config(text=f"Found {len(backups)} backups", fg="#28a745")
                        print(f"✅ Successfully loaded {len(backups)} backups")
                    else:
                        print("⚠️ Backups list is empty")
                        self.status_label.config(text="No backups found", fg="#6c757d")
                else:
                    print("❌ No 'backups' key in API response")
                    self.status_label.config(text="Invalid API response", fg="#dc3545")
            else:
                print(f"❌ Invalid API response: {result}")
                error_msg = result.get('error', 'Failed to load backups') if isinstance(result, dict) else 'Invalid response format'
                self.status_label.config(text=f"Error: {error_msg}", fg="#dc3545")
                
        except Exception as e:
            print(f"❌ Load backups error: {e}")
            import traceback
            traceback.print_exc()
            self.status_label.config(text=f"Load error: {str(e)}", fg="#dc3545")
    
    def import_selected(self):
        """Import selected backup"""
        try:
            # Get selected item
            selection = self.backup_tree.selection()
            if not selection:
                messagebox.showwarning("No Selection", "Please select a backup to import")
                return
            
            # Get backup ID from tags
            item = selection[0]
            backup_id = self.backup_tree.item(item, 'tags')[0]
            backup_name = self.backup_tree.item(item, 'values')[0]
            
            # Show import options dialog
            import_options = self.show_import_options_dialog(backup_name)
            if not import_options:
                return  # User cancelled
            
            merge_strategy = import_options['merge_strategy']
            
            self.status_label.config(text="Importing backup...", fg="#007bff")
            self.update()  # Force UI update
            
            # Import backup
            result = self.api_service.restore_backup(backup_id, merge_strategy)
            
            if result and result.get('success'):
                # Show detailed import results
                self.show_import_results(result)
                self.import_successful = True
                
                # Close dialog after showing results
                self.after(3000, self.destroy)
            else:
                error_msg = result.get('error', 'Import failed') if result else 'Unknown error'
                self.status_label.config(text=f"❌ {error_msg}", fg="#dc3545")
                messagebox.showerror("Import Failed", f"Failed to import backup:\n\n{error_msg}")
                
        except Exception as e:
            self.status_label.config(text=f"❌ Import error: {str(e)}", fg="#dc3545")
            messagebox.showerror("Import Error", f"Import failed:\n\n{str(e)}")

    def show_import_options_dialog(self, backup_name):
        """Show dialog to select import options"""
        # Create custom dialog for import options
        options_dialog = tk.Toplevel(self)
        options_dialog.title("Import Options")
        options_dialog.geometry("400x300")
        options_dialog.configure(bg="#f8f9fa")
        options_dialog.transient(self)
        options_dialog.grab_set()
        
        # Center dialog
        options_dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - (400 // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (300 // 2)
        options_dialog.geometry(f"400x300+{x}+{y}")
        
        result = {'merge_strategy': None}
        
        # Main frame
        main_frame = tk.Frame(options_dialog, bg="#f8f9fa", padx=20, pady=20)
        main_frame.pack(fill="both", expand=True)
        
        # Header
        tk.Label(main_frame,
                text=f"Import Backup: {backup_name}",
                font=self.title_font,
                bg="#f8f9fa",
                fg="#2c3e50").pack(pady=(0, 20))
        
        tk.Label(main_frame,
                text="Choose how to handle duplicate entries:",
                font=self.label_font,
                bg="#f8f9fa",
                fg="#495057").pack(pady=(0, 15))
        
        # Radio button variable
        strategy_var = tk.StringVar(value="merge")
        
        # Option frames
        option_frame1 = tk.Frame(main_frame, bg="#f8f9fa")
        option_frame1.pack(fill="x", pady=5)
        
        tk.Radiobutton(option_frame1,
                      text="Merge (Keep both, rename imported)",
                      variable=strategy_var,
                      value="merge",
                      bg="#f8f9fa",
                      font=self.label_font).pack(anchor="w")
        
        tk.Label(option_frame1,
                text="  • Imported entries will be renamed to avoid conflicts",
                font=("Segoe UI", 9),
                bg="#f8f9fa",
                fg="#6c757d").pack(anchor="w", padx=20)
        
        option_frame2 = tk.Frame(main_frame, bg="#f8f9fa")
        option_frame2.pack(fill="x", pady=5)
        
        tk.Radiobutton(option_frame2,
                      text="Skip duplicates (Keep existing only)",
                      variable=strategy_var,
                      value="skip_duplicates",
                      bg="#f8f9fa",
                      font=self.label_font).pack(anchor="w")
        
        tk.Label(option_frame2,
                text="  • Duplicate entries will be skipped",
                font=("Segoe UI", 9),
                bg="#f8f9fa",
                fg="#6c757d").pack(anchor="w", padx=20)
        
        # Button frame
        button_frame = tk.Frame(main_frame, bg="#f8f9fa")
        button_frame.pack(fill="x", pady=(30, 0))
        
        def confirm_import():
            result['merge_strategy'] = strategy_var.get()
            options_dialog.destroy()
        
        def cancel_import():
            options_dialog.destroy()
        
        tk.Button(button_frame,
                 text="📥 Import",
                 font=self.button_font,
                 bg="#28a745",
                 fg="white",
                 relief="flat",
                 command=confirm_import,
                 cursor="hand2",
                 padx=20,
                 pady=8).pack(side="left", padx=(0, 10))
        
        tk.Button(button_frame,
                 text="❌ Cancel",
                 font=self.button_font,
                 bg="#6c757d",
                 fg="white",
                 relief="flat",
                 command=cancel_import,
                 cursor="hand2",
                 padx=20,
                 pady=8).pack(side="right")
        
        # Wait for dialog to close
        self.wait_window(options_dialog)
        
        return result if result['merge_strategy'] else None

    def show_import_results(self, result):
        """Show detailed import results"""
        imported = result.get('imported_count', 0)
        failed = result.get('failed_count', 0)
        skipped = result.get('skipped_count', 0)
        total = result.get('total_count', 0)
        
        backup_info = result.get('backup_info', {})
        backup_version = backup_info.get('version', 'Unknown')
        backup_date = backup_info.get('created_at', 'Unknown')
        
        # Format backup date
        if backup_date != 'Unknown':
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(backup_date.replace('Z', '+00:00'))
                backup_date = dt.strftime('%Y-%m-%d %H:%M:%S')
            except:
                pass
        
        # Create results message
        results_text = f"""Import Completed Successfully!

📊 Import Summary:
✅ Imported: {imported} entries
❌ Failed: {failed} entries
⏭️ Skipped: {skipped} entries
📋 Total: {total} entries

📦 Backup Information:
Version: {backup_version}
Created: {backup_date}

{imported} entries have been added to your vault!"""
        
        # Update status
        if imported > 0:
            self.status_label.config(text=f"✅ Imported {imported}/{total} entries", fg="#28a745")
        else:
            self.status_label.config(text="⚠️ No entries imported", fg="#ffc107")
        
        # Show results dialog
        messagebox.showinfo("Import Complete", results_text)