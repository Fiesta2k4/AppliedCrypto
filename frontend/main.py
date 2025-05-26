import os
import sys
import tkinter as tk

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

try:
    from frontend.windows.login_window import LoginWindow
    from frontend.services.api_service import ApiService
    print("✅ All modules imported successfully")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running from the correct directory")
    sys.exit(1)

def main():
    """Main entry point for Personal Vault application"""
    print("🔐 Starting Personal Vault Application...")
    print(f"📁 Project root: {project_root}")
    
    # Test API connection
    try:
        api_service = ApiService()
        health = api_service.health_check()
        if health:
            print("✅ Backend connection successful")
            print(f"   Status: {health.get('status')}")
            print(f"   Modules: {health.get('modules_loaded')}")
        else:
            print("⚠️  Backend not responding")
            print("   Make sure backend server is running:")
            print("   python backend/run_server.py")
    except Exception as e:
        print(f"⚠️  Backend connection failed: {e}")
        print("   The app will work in offline mode")
    
    # Create and start GUI
    try:
        app = LoginWindow()
        print("✅ GUI started successfully")
        app.mainloop()
    except Exception as e:
        print(f"❌ GUI error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
