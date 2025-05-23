import tkinter as tk
from tkinter import messagebox, font
from concurrent.futures import ThreadPoolExecutor

#from api_service import ApiService      # your HTTP wrapper
from frontend.windows.main_window import MainWindow     # the Toplevel main app

class LoginWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Personal Vault – Đăng nhập")
        self.geometry("420x320")
        self.configure(bg="#e0f7fa")
        self.resizable(True, True)

        # Thread pool for background tasks
        self.executor = ThreadPoolExecutor(max_workers=1)

        # Fonts
        self.header_font = font.Font(family="Arial Rounded MT Bold", size=18)
        self.label_font  = font.Font(family="Helvetica", size=11)
        self.entry_font  = font.Font(family="Helvetica", size=11)
        self.btn_font    = font.Font(family="Helvetica", size=12, weight="bold")
        self.error_font  = font.Font(family="Helvetica", size=10, slant="italic")

        # Container
        container = tk.Frame(self, bg="white")
        container.place(relx=0.5, rely=0.5, anchor="c", width=360, height=260)

        # Header
        tk.Label(container,
                 text="Welcome to your Vault",
                 font=self.header_font,
                 bg="white", fg="#00695c") \
          .pack(pady=(20,10))

        # Email
        tk.Label(container, text="Email:",
                 font=self.label_font, bg="white", fg="#00796b") \
          .pack(anchor="w", padx=30)
        self.email_entry = tk.Entry(container,
                                    font=self.entry_font,
                                    bd=2, relief="groove")
        self.email_entry.pack(fill="x", padx=30, pady=(0,10))

        # Password
        tk.Label(container, text="Password:",
                 font=self.label_font, bg="white", fg="#00796b") \
          .pack(anchor="w", padx=30)
        self.password_entry = tk.Entry(container,
                                       font=self.entry_font,
                                       bd=2, relief="groove",
                                       show="*")
        self.password_entry.pack(fill="x", padx=30, pady=(0,15))

        # Login button
        self.login_btn = tk.Button(container,
                                   text="Login",
                                   font=self.btn_font,
                                   bg="#26a69a", fg="white",
                                   activebackground="#00796b",
                                   bd=0, padx=10, pady=5,
                                   cursor="hand2",
                                   command=self.login)
        self.login_btn.pack(pady=(0,10))

        # Error label
        self.error_label = tk.Label(container, text="",
                                    font=self.error_font,
                                    bg="white", fg="red")
        self.error_label.pack()

        # Bindings
        self.email_entry.focus()
        self.bind("<Return>", lambda e: self.login())
        # Clear errors on edit
        for widget in (self.email_entry, self.password_entry):
            widget.bind("<Key>", lambda e: self.error_label.config(text=""))

    def login(self):
        email = self.email_entry.get().strip()
        pwd   = self.password_entry.get().strip()

        # Basic validation
        if not email or not pwd:
            self.error_label.config(text="Both email and password are required.")
            return

        # Disable the button & clear old error
        self.login_btn.config(state="disabled", text="Logging in…")
        self.error_label.config(text="")

        # Do the API call in the background
        self.executor.submit(self._do_login, email, pwd)

    def _do_login(self, email, pwd):
        try:
            resp = ApiService.login(email, pwd)
            if resp.ok:
                # success! switch to MainWindow on the main thread
                self.after(0, self._on_success, email)
            else:
                # failure: show error message
                msg = resp.error or "Invalid email or password."
                self.after(0, self._on_error, msg)
        except Exception as e:
            # network or unexpected error
            self.after(0, self._on_error, str(e))

    def _on_success(self, email):
        messagebox.showinfo("Success", "Logged in successfully!")
        self.withdraw()                     # hide login root
        MainWindow(self, user_email=email)  # open main as Toplevel

    def _on_error(self, msg):
        self.error_label.config(text=msg)
        self.login_btn.config(state="normal", text="Login")

if __name__ == "__main__":
    LoginWindow().mainloop()
