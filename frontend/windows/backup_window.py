import tkinter as tk
from tkinter import messagebox, font

class BackupWindow(tk.Toplevel):
    """
    Backup and Recovery dialog as a separate window.
    """
    def __init__(self, master=None):
        super().__init__(master)
        self.title("Backup & Recovery")
        self.geometry("400x300")
        self.configure(bg="white")
        self.resizable(True, True)

        # Fonts
        header_font = font.Font(family="Helvetica", size=16, weight="bold")
        btn_font    = font.Font(family="Helvetica", size=12)

        # Header
        tk.Label(
            self,
            text="Backup & Recovery",
            font=header_font,
            bg="white"
        ).pack(pady=20)

        # Create Backup button
        tk.Button(
            self,
            text="Create Backup",
            font=btn_font,
            bg="#81d4fa",
            fg="#01579b",
            bd=0,
            padx=10,
            pady=8,
            cursor="hand2",
            command=self.create_backup
        ).pack(pady=10)



    def create_backup(self):
        # TODO: call APIService to create backup
        # Example placeholder:
        messagebox.showinfo("Backup", "Backup created successfully!")

    def restore_backup(self):
        # TODO: call APIService to restore backup
        # Example placeholder:
        messagebox.showinfo("Recovery", "Recovery completed successfully!")

if __name__ == '__main__':
    # 1) Create a real root
    root = tk.Tk()
    # 2) Hide it so only your Toplevel shows
    root.withdraw()
    # 3) Create your BackupWindow as a child of that root
    bw = BackupWindow(root)
    # 4) Run the event loop on the root (not on bw)
    root.mainloop()