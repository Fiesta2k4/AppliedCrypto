import secrets
import hashlib
from datetime import datetime, timedelta

class SecureSessionManager:
    """Quản lý session bảo mật cho master password"""
    
    def __init__(self):
        self.active_sessions = {}  # {user_id: {master_key, expires_at}}
        self.session_timeout = 800  # 5 phút
    
    def create_session(self, user_id, master_password, user_salt):
        """Tạo session và derive master key"""
        master_key = hashlib.pbkdf2_hmac(
            'sha256',
            master_password.encode('utf-8'),
            user_salt.encode('utf-8'),
            200000
        )
        
        expires_at = datetime.now() + timedelta(seconds=self.session_timeout)
        
        self.active_sessions[user_id] = {
            'master_key': master_key,
            'expires_at': expires_at
        }
        
        return True
    
    def get_master_key(self, user_id):
        """Lấy master key từ session"""
        if user_id not in self.active_sessions:
            return None
            
        session = self.active_sessions[user_id]
        if datetime.now() > session['expires_at']:
            del self.active_sessions[user_id]
            return None
            
        return session['master_key']
    
    def clear_session(self, user_id):
        """Xóa session"""
        self.active_sessions.pop(user_id, None)

# Global instance
session_manager = SecureSessionManager()