import sys
import os

def reset_user():
    """Reset specific user for testing"""
    try:
        from database.config import db
        test_email = "testuser@example.com"
        
        print(f"🗑️  Deleting user: {test_email}")
        
        # Delete user and related data
        db.execute_query("DELETE FROM vault_entries WHERE user_id IN (SELECT id FROM users WHERE email = ?)", [test_email])
        rows_deleted = db.execute_query("DELETE FROM users WHERE email = ?", [test_email])
        
        print(f"✅ Deleted {rows_deleted} user(s)")
        
        # Show current users
        users = db.execute_query("SELECT email, created_at FROM users")
        print(f"📋 Remaining users: {len(users)}")
        for user in users:
            print(f"   - {user['email']} (created: {user['created_at']})")
        
    except Exception as e:
        print(f"❌ Reset failed: {e}")

if __name__ == "__main__":
    reset_user()