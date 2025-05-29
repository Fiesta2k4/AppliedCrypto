import tkinter as tk
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.api_service import ApiService
from windows.main_window import MainWindow

def test_main_window():
    print("🔍 === TESTING MAIN WINDOW CREATION ===")
    
    # Create root
    root = tk.Tk()
    root.withdraw()
    
    # Create API service
    api_service = ApiService()
    print(f"✅ Created API service: {api_service}")
    
    # Create main window
    main_window = MainWindow(
        master=root,
        user_email="test@example.com", 
        api_service=api_service
    )
    
    print(f"✅ Main window created: {main_window}")
    print(f"🔍 Main window API service: {main_window.api_service}")
    
    # Test import backup
    print("🔍 Testing import_backup...")
    main_window.import_backup()
    
    root.mainloop()

if __name__ == "__main__":
    test_main_window()