import tkinter as tk
from tkinter import ttk, messagebox, font, scrolledtext
import json

class ShareWindow(tk.Toplevel):
    def __init__(self, master, api_service=None):
        super().__init__(master)
        
        self.api_service = api_service
        self.user_private_key = None
        
        self.title("🔗 Secure Sharing")
        self.geometry("800x600")
        self.configure(bg="#f5f5f5")
        self.resizable(True, True)
        
        # Fonts
        self.header_font = font.Font(family="Segoe UI", size=16, weight="bold")
        self.content_font = font.Font(family="Segoe UI", size=11)
        
        self.create_ui()
        self.load_data()
    
    def create_ui(self):
        # Header
        header_frame = tk.Frame(self, bg="#2c3e50", height=60)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        tk.Label(header_frame,
                text="🔗 Secure Password Sharing",
                font=self.header_font,
                bg="#2c3e50", fg="white").pack(side="left", padx=20, pady=15)
        
        # Main content
        main_frame = tk.Frame(self, bg="#f5f5f5")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill="both", expand=True)
        
        # Send Share tab
        self.send_frame = tk.Frame(self.notebook, bg="white")
        self.notebook.add(self.send_frame, text="📤 Send Share")
        self.create_send_tab()
        
        # Received Shares tab
        self.received_frame = tk.Frame(self.notebook, bg="white")
        self.notebook.add(self.received_frame, text="📥 Received")
        self.create_received_tab()
        
        # Sent Shares tab
        self.sent_frame = tk.Frame(self.notebook, bg="white")
        self.notebook.add(self.sent_frame, text="📤 Sent")
        self.create_sent_tab()
        
        # Keys tab
        self.keys_frame = tk.Frame(self.notebook, bg="white")
        self.notebook.add(self.keys_frame, text="🔑 Keys")
        self.create_keys_tab()
    
    def create_send_tab(self):
        # Title
        tk.Label(self.send_frame,
                text="Send Encrypted Secret",
                font=self.header_font,
                bg="white").pack(pady=20)
        
        # Form
        form_frame = tk.Frame(self.send_frame, bg="white")
        form_frame.pack(fill="x", padx=40, pady=20)
        
        # Recipient email
        tk.Label(form_frame, text="Recipient Email:", bg="white").pack(anchor="w")
        self.recipient_var = tk.StringVar()
        recipient_entry = tk.Entry(form_frame, textvariable=self.recipient_var, width=50)
        recipient_entry.pack(fill="x", pady=(5, 15))
        
        # Secret data
        tk.Label(form_frame, text="Secret to Share:", bg="white").pack(anchor="w")
        self.secret_text = scrolledtext.ScrolledText(form_frame, height=6, width=50)
        self.secret_text.pack(fill="x", pady=(5, 15))
        
        # Message
        tk.Label(form_frame, text="Message (optional):", bg="white").pack(anchor="w")
        self.message_text = scrolledtext.ScrolledText(form_frame, height=3, width=50)
        self.message_text.pack(fill="x", pady=(5, 15))
        
        # Send button
        tk.Button(form_frame,
                 text="🔗 Send Encrypted Share",
                 command=self.send_share,
                 bg="#007bff", fg="white",
                 font=self.content_font,
                 pady=10).pack(pady=20)
    
    def create_received_tab(self):
        # Title and refresh
        top_frame = tk.Frame(self.received_frame, bg="white")
        top_frame.pack(fill="x", padx=20, pady=20)
        
        tk.Label(top_frame,
                text="Received Shares",
                font=self.header_font,
                bg="white").pack(side="left")
        
        tk.Button(top_frame,
                 text="🔄 Refresh",
                 command=self.load_received_shares).pack(side="right")
        
        # Received shares tree
        tree_frame = tk.Frame(self.received_frame, bg="white")
        tree_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.received_tree = ttk.Treeview(tree_frame, 
                                         columns=("Sender", "Message", "Date", "Status"), 
                                         show="tree headings")
        self.received_tree.heading("#0", text="ID")
        self.received_tree.heading("Sender", text="From")
        self.received_tree.heading("Message", text="Message")
        self.received_tree.heading("Date", text="Date")
        self.received_tree.heading("Status", text="Status")
        
        received_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.received_tree.yview)
        self.received_tree.configure(yscrollcommand=received_scrollbar.set)
        
        self.received_tree.pack(side="left", fill="both", expand=True)
        received_scrollbar.pack(side="right", fill="y")
        
        # Decrypt button
        tk.Button(self.received_frame,
                 text="🔓 Decrypt Selected",
                 command=self.decrypt_selected_share,
                 bg="#28a745", fg="white").pack(pady=10)
    
    def create_sent_tab(self):
        # Title and refresh
        top_frame = tk.Frame(self.sent_frame, bg="white")
        top_frame.pack(fill="x", padx=20, pady=20)
        
        tk.Label(top_frame,
                text="Sent Shares",
                font=self.header_font,
                bg="white").pack(side="left")
        
        tk.Button(top_frame,
                 text="🔄 Refresh",
                 command=self.load_sent_shares).pack(side="right")
        
        # Sent shares tree
        tree_frame = tk.Frame(self.sent_frame, bg="white")
        tree_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.sent_tree = ttk.Treeview(tree_frame, 
                                     columns=("Recipient", "Message", "Date", "Status"), 
                                     show="tree headings")
        self.sent_tree.heading("#0", text="ID")
        self.sent_tree.heading("Recipient", text="To")
        self.sent_tree.heading("Message", text="Message")
        self.sent_tree.heading("Date", text="Date")
        self.sent_tree.heading("Status", text="Status")
        
        sent_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.sent_tree.yview)
        self.sent_tree.configure(yscrollcommand=sent_scrollbar.set)
        
        self.sent_tree.pack(side="left", fill="both", expand=True)
        sent_scrollbar.pack(side="right", fill="y")
    
    def create_keys_tab(self):
        # Title
        tk.Label(self.keys_frame,
                text="Key Management",
                font=self.header_font,
                bg="white").pack(pady=20)
        
        # Generate keys button
        tk.Button(self.keys_frame,
                 text="🔑 Generate New Key Pair",
                 command=self.generate_keys,
                 bg="#17a2b8", fg="white",
                 font=self.content_font,
                 pady=10).pack(pady=20)
        
        # Private key input
        tk.Label(self.keys_frame,
                text="Your Private Key (keep this secure!):",
                bg="white").pack(pady=(20, 5))
        
        self.private_key_text = scrolledtext.ScrolledText(self.keys_frame, height=8, width=80)
        self.private_key_text.pack(padx=20, pady=10)
        
        # Save private key button
        tk.Button(self.keys_frame,
                 text="💾 Save Private Key",
                 command=self.save_private_key,
                 bg="#6c757d", fg="white").pack(pady=10)
    
    def load_data(self):
        """Load all sharing data"""
        self.load_received_shares()
        self.load_sent_shares()
    
    def load_received_shares(self):
        """Load received shares"""
        try:
            if not self.api_service:
                return
            
            result = self.api_service.get_received_shares()
            
            # Clear tree
            for item in self.received_tree.get_children():
                self.received_tree.delete(item)
            
            if result and 'shares' in result:
                for share in result['shares']:
                    self.received_tree.insert('', 'end',
                                            text=share.get('id', '')[:8],
                                            values=(
                                                share.get('sender_email', ''),
                                share.get('message', '')[:50],
                                                share.get('created_at', '')[:10],
                                                share.get('status', 'pending')
                                            ),
                                            tags=(share.get('id', ''),))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load received shares: {str(e)}")
    
    def load_sent_shares(self):
        """Load sent shares"""
        try:
            if not self.api_service:
                return
            
            result = self.api_service.get_sent_shares()
            
            # Clear tree
            for item in self.sent_tree.get_children():
                self.sent_tree.delete(item)
            
            if result and 'shares' in result:
                for share in result['shares']:
                    self.sent_tree.insert('', 'end',
                                        text=share.get('id', '')[:8],
                                        values=(
                                            share.get('recipient_email', ''),
                                            share.get('message', '')[:50],
                                            share.get('created_at', '')[:10],
                                            share.get('status', 'pending')
                                        ),
                                        tags=(share.get('id', ''),))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load sent shares: {str(e)}")
    
    def send_share(self):
        """Send encrypted share"""
        try:
            recipient_email = self.recipient_var.get().strip()
            secret_data = self.secret_text.get("1.0", tk.END).strip()
            message = self.message_text.get("1.0", tk.END).strip()
            
            if not recipient_email or not secret_data:
                messagebox.showerror("Error", "Recipient email and secret are required")
                return
            
            if not self.api_service:
                messagebox.showerror("Error", "API service not available")
                return
            
            result = self.api_service.send_share(recipient_email, secret_data, message)
            
            if result and result.get('success'):
                messagebox.showinfo("Success", "Secret shared successfully!")
                
                # Clear form
                self.recipient_var.set("")
                self.secret_text.delete("1.0", tk.END)
                self.message_text.delete("1.0", tk.END)
                
                # Refresh sent shares
                self.load_sent_shares()
            else:
                error_msg = result.get('error', 'Unknown error') if result else 'Share failed'
                messagebox.showerror("Error", f"Failed to send share: {error_msg}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Send share failed: {str(e)}")
    
    def decrypt_selected_share(self):
        """Decrypt selected received share"""
        try:
            selection = self.received_tree.selection()
            if not selection:
                messagebox.showwarning("Warning", "Please select a share to decrypt")
                return
            
            # Get private key
            private_key = self.private_key_text.get("1.0", tk.END).strip()
            if not private_key:
                messagebox.showerror("Error", "Please enter your private key in the Keys tab")
                return
            
            item = selection[0]
            share_id = self.received_tree.item(item, 'tags')[0]
            
            if not self.api_service:
                messagebox.showerror("Error", "API service not available")
                return
            
            result = self.api_service.decrypt_share(share_id, private_key)
            
            if result and result.get('success'):
                # Show decrypted secret in new window
                self.show_decrypted_secret(result)
            else:
                error_msg = result.get('error', 'Unknown error') if result else 'Decryption failed'
                messagebox.showerror("Error", f"Failed to decrypt: {error_msg}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Decryption failed: {str(e)}")
    
    def show_decrypted_secret(self, decrypted_data):
        """Show decrypted secret in popup window"""
        popup = tk.Toplevel(self)
        popup.title("🔓 Decrypted Secret")
        popup.geometry("500x400")
        popup.configure(bg="white")
        
        # Header
        tk.Label(popup,
                text="🔓 Decrypted Secret",
                font=self.header_font,
                bg="white").pack(pady=20)
        
        # Info
        info_frame = tk.Frame(popup, bg="white")
        info_frame.pack(fill="x", padx=20, pady=10)
        
        tk.Label(info_frame,
                text=f"From: {decrypted_data.get('sender_email', 'Unknown')}",
                bg="white").pack(anchor="w")
        tk.Label(info_frame,
                text=f"Date: {decrypted_data.get('created_at', '')[:10]}",
                bg="white").pack(anchor="w")
        
        if decrypted_data.get('message'):
            tk.Label(info_frame,
                    text=f"Message: {decrypted_data.get('message')}",
                    bg="white").pack(anchor="w", pady=(10, 0))
        
        # Secret
        tk.Label(popup, text="Secret:", bg="white").pack(anchor="w", padx=20, pady=(20, 5))
        
        secret_text = scrolledtext.ScrolledText(popup, height=8, width=60)
        secret_text.pack(fill="both", expand=True, padx=20, pady=10)
        secret_text.insert("1.0", decrypted_data.get('decrypted_secret', ''))
        secret_text.config(state='disabled')
        
        # Copy button
        def copy_secret():
            popup.clipboard_clear()
            popup.clipboard_append(decrypted_data.get('decrypted_secret', ''))
            messagebox.showinfo("Copied", "Secret copied to clipboard!")
        
        tk.Button(popup,
                 text="📋 Copy to Clipboard",
                 command=copy_secret,
                 bg="#007bff", fg="white").pack(pady=10)
    
    def generate_keys(self):
        """Generate new RSA key pair"""
        try:
            if not self.api_service:
                messagebox.showerror("Error", "API service not available")
                return
            
            if messagebox.askyesno("Confirm", 
                                  "This will generate new keys. "
                                  "Make sure to save your private key! Continue?"):
                
                result = self.api_service.generate_user_keys()
                
                if result and result.get('success'):
                    # Show private key
                    self.private_key_text.delete("1.0", tk.END)
                    self.private_key_text.insert("1.0", result.get('private_key', ''))
                    
                    messagebox.showinfo("Success", 
                                      "Keys generated successfully!\n\n"
                                      "⚠️ IMPORTANT: Save your private key securely. "
                                      "You'll need it to decrypt received shares.")
                else:
                    error_msg = result.get('error', 'Unknown error') if result else 'Key generation failed'
                    messagebox.showerror("Error", f"Failed to generate keys: {error_msg}")
                    
        except Exception as e:
            messagebox.showerror("Error", f"Key generation failed: {str(e)}")
    
    def save_private_key(self):
        """Save private key to file"""
        try:
            from tkinter import filedialog
            
            private_key = self.private_key_text.get("1.0", tk.END).strip()
            if not private_key:
                messagebox.showerror("Error", "No private key to save")
                return
            
            filename = filedialog.asksaveasfilename(
                title="Save Private Key",
                defaultextension=".pem",
                filetypes=[("PEM files", "*.pem"), ("All files", "*.*")]
            )
            
            if filename:
                with open(filename, 'w') as f:
                    f.write(private_key)
                messagebox.showinfo("Success", f"Private key saved to {filename}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save private key: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    app = ShareWindow(root)
    app.mainloop()