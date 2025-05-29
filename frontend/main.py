import tkinter as tk
import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print("✅ All modules imported successfully")

def main():
    """Main application entry point"""
    print("🔐 Starting Personal Vault Application...")
    print(f"📁 Project root: {project_root}")
    
    try:
        # Test backend connection first
        from frontend.services.api_service import ApiService
        
        api_service = ApiService()
        health = api_service.health_check()
        
        if health and health.get('status') == 'healthy':
            print("✅ Backend connection successful")
            print(f"   Status: {health.get('status')}")
            print(f"   Modules: {health.get('modules_loaded', [])}")
        else:
            print("⚠️ Backend connection warning")
            print(f"   Response: {health}")
        
        # Create main tkinter root
        root = tk.Tk()
        root.title("Personal Vault")
        root.geometry("400x300")
        root.withdraw()  # Hide root window initially
        
        # ✅ Import and create LoginWindow with master parameter
        from frontend.windows.login_window import LoginWindow
        
        print("🔍 Creating LoginWindow with master...")
        login_window = LoginWindow(master=root)  # ← Add master=root
        
        print("✅ LoginWindow created successfully")
        
        # Start the main event loop
        root.mainloop()
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure all required modules are available.")
        
    except Exception as e:
        print(f"❌ GUI error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
