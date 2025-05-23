import tkinter as tk
import time
import hmac
import hashlib
import base64
import struct
from tkinter import font

class OTPWindow(tk.Toplevel):
    def __init__(self, master, otp_entries):
        super().__init__(master)
        self.title("One-Time Passwords")
        self.geometry("500x400")
        self.configure(bg="white")
        self.resizable(False, False)

        self.title_font = font.Font(family="Segoe UI", size=16, weight="bold")
        self.code_font = font.Font(family="Consolas", size=16, weight="bold")
        self.label_font = font.Font(family="Segoe UI", size=12)

        tk.Label(self, text="Active OTP Codes", font=self.title_font, bg="white", fg="#333").pack(pady=15)

        self.container = tk.Frame(self, bg="white")
        self.container.pack(fill="both", expand=True, padx=20)

        self.otp_entries = otp_entries  # list of dicts: {"label": ..., "secret": ..., "digits":6, "period":30}
        self.code_labels = []

        for entry in self.otp_entries:
            frame = tk.Frame(self.container, bg="white")
            frame.pack(fill="x", pady=10)
            tk.Label(frame, text=entry['label'], font=self.label_font, bg="white", fg="#444").pack(anchor="w")
            code_label = tk.Label(frame, text="----", font=self.code_font, bg="white", fg="#00796b")
            code_label.pack(anchor="w")
            self.code_labels.append((entry, code_label))

        self.update_otp_loop()

    def generate_totp(self, secret_b32, digits=6, period=30):
        try:
            key = base64.b32decode(secret_b32.upper())
        except Exception:
            return "Invalid Secret"
        counter = int(time.time()) // period
        counter_bytes = struct.pack('>Q', counter)
        hmac_digest = hmac.new(key, counter_bytes, hashlib.sha1).digest()
        offset = hmac_digest[-1] & 0x0F
        truncated_hash = hmac_digest[offset:offset+4]
        code_int = struct.unpack('>I', truncated_hash)[0] & 0x7FFFFFFF
        return str(code_int % (10 ** digits)).zfill(digits)

    def update_otp_loop(self):
        for entry, label in self.code_labels:
            otp = self.generate_totp(entry['secret'], entry.get('digits', 6), entry.get('period', 30))
            label.config(text=otp)
        self.after(1000, self.update_otp_loop)


# Example usage (for testing only)
if __name__ == '__main__':
    root = tk.Tk()
    root.withdraw()
    entries = [
        {"label": "Google", "secret": "JBSWY3DPEHPK3PXP", "digits": 6, "period": 30},
        {"label": "GitHub", "secret": "NB2W45DFOIZA====", "digits": 6, "period": 30},
    ]
    OTPWindow(root, entries)
    root.mainloop()
