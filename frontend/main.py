# main.py
from frontend.windows.main_window import MainWindow
from windows.login_window import LoginWindow
from frontend.windows.backup_window import BackupWindow


if __name__ == "__main__":
    LoginWindow().mainloop()
