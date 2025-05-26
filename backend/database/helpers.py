from datetime import datetime
from .config import db
import json
import sqlite3

class UserDB:
    @staticmethod
    def create_user(email, salt, password_hash, public_key=""):
        """Create new user with detailed error handling"""
        try:
            print(f"🔧 Creating user: {email}")
            
            # Check if user exists first
            existing = UserDB.get_user_by_email(email)
            if existing:
                print(f"⚠️  User already exists: {email}")
                return None
            
            query = """
            INSERT INTO users (email, salt, password_hash, public_key)
            VALUES (?, ?, ?, ?)
            """
            
            print(f"📝 Executing query with params: [{email}, {salt[:10]}..., {password_hash[:20]}..., {public_key[:20]}...]")
            
            rows_affected = db.execute_query(query, [email, salt, password_hash, public_key])
            print(f"📊 Rows affected: {rows_affected}")
            
            if rows_affected > 0:
                created_user = UserDB.get_user_by_email(email)
                print(f"✅ User created successfully: {created_user['id'] if created_user else 'None'}")
                return created_user
            else:
                print("❌ No rows affected")
                return None
                
        except sqlite3.IntegrityError as e:
            print(f"❌ Integrity error (duplicate email?): {e}")
            return None
        except Exception as e:
            print(f"❌ Create user error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    @staticmethod
    def get_user_by_email(email):
        """Get user by email"""
        try:
            query = "SELECT * FROM users WHERE email = ?"
            users = db.execute_query(query, [email])
            return users[0] if users else None
        except Exception as e:
            print(f"❌ Get user by email error: {e}")
            return None
    
    @staticmethod
    def get_user_by_id(user_id):
        """Get user by ID"""
        try:
            query = "SELECT * FROM users WHERE id = ?"
            users = db.execute_query(query, [user_id])
            return users[0] if users else None
        except Exception as e:
            print(f"❌ Get user by ID error: {e}")
            return None
    
    @staticmethod
    def update_user(user_id, **kwargs):
        """Update user fields"""
        if not kwargs:
            return False
        
        set_clause = ", ".join([f"{key} = ?" for key in kwargs.keys()])
        query = f"UPDATE users SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
        
        params = list(kwargs.values()) + [user_id]
        rows_affected = db.execute_query(query, params)
        return rows_affected > 0

class VaultDB:
    """Vault database operations using SQL"""
    
    @staticmethod
    def create_entry(user_id, iv, ciphertext, tag, metadata=None):
        """Create new vault entry"""
        query = """
        INSERT INTO vault_entries (user_id, iv, ciphertext, tag, metadata)
        VALUES (?, ?, ?, ?, ?)
        """
        metadata_json = json.dumps(metadata) if metadata else None
        
        db.execute_query(query, [user_id, iv, ciphertext, tag, metadata_json])
        
        # Get the created entry
        return VaultDB.get_user_entries(user_id, limit=1)[0]
    
    @staticmethod
    def get_user_entries(user_id, limit=None):
        """Get all vault entries for user"""
        query = """
        SELECT id, iv, ciphertext, tag, metadata, created_at, updated_at
        FROM vault_entries 
        WHERE user_id = ? 
        ORDER BY created_at DESC
        """
        if limit:
            query += f" LIMIT {limit}"
        
        entries = db.execute_query(query, [user_id])
        
        # Parse JSON metadata
        for entry in entries:
            if entry['metadata']:
                try:
                    entry['metadata'] = json.loads(entry['metadata'])
                except:
                    entry['metadata'] = {}
            else:
                entry['metadata'] = {}
        
        return entries
    
    @staticmethod
    def get_entry_by_id(entry_id, user_id):
        """Get specific entry by ID (with user verification)"""
        query = """
        SELECT * FROM vault_entries 
        WHERE id = ? AND user_id = ?
        """
        entries = db.execute_query(query, [entry_id, user_id])
        
        if entries:
            entry = entries[0]
            if entry['metadata']:
                try:
                    entry['metadata'] = json.loads(entry['metadata'])
                except:
                    entry['metadata'] = {}
            return entry
        return None
    
    @staticmethod
    def update_entry(entry_id, user_id, **kwargs):
        """Update vault entry"""
        if not kwargs:
            return False
        
        # Handle metadata separately
        if 'metadata' in kwargs:
            kwargs['metadata'] = json.dumps(kwargs['metadata'])
        
        set_clause = ", ".join([f"{key} = ?" for key in kwargs.keys()])
        query = f"""
        UPDATE vault_entries 
        SET {set_clause}, updated_at = CURRENT_TIMESTAMP 
        WHERE id = ? AND user_id = ?
        """
        
        params = list(kwargs.values()) + [entry_id, user_id]
        rows_affected = db.execute_query(query, params)
        return rows_affected > 0
    
    @staticmethod
    def delete_entry(entry_id, user_id):
        """Delete vault entry"""
        query = "DELETE FROM vault_entries WHERE id = ? AND user_id = ?"
        rows_affected = db.execute_query(query, [entry_id, user_id])
        return rows_affected > 0
    
    @staticmethod
    def get_stats(user_id):
        """Get vault statistics for user"""
        query = """
        SELECT 
            COUNT(*) as total_entries,
            json_extract(metadata, '$.type') as entry_type,
            COUNT(*) as type_count
        FROM vault_entries 
        WHERE user_id = ?
        GROUP BY json_extract(metadata, '$.type')
        """
        type_stats = db.execute_query(query, [user_id])
        
        # Get total count
        total_query = "SELECT COUNT(*) as total FROM vault_entries WHERE user_id = ?"
        total_result = db.execute_query(total_query, [user_id])
        total_entries = total_result[0]['total'] if total_result else 0
        
        # Format type counts
        type_counts = {}
        for stat in type_stats:
            entry_type = stat['entry_type'] or 'unknown'
            type_counts[entry_type] = stat['type_count']
        
        return {
            'total_entries': total_entries,
            'type_counts': type_counts
        }

class ShareDB:
    """Share database operations using SQL"""
    
    @staticmethod
    def create_share(sender_id, recipient_email, encrypted_secret, message=""):
        """Create new share"""
        # Get recipient ID
        recipient = UserDB.get_user_by_email(recipient_email)
        if not recipient:
            return None
        
        query = """
        INSERT INTO shares (sender_id, recipient_id, encrypted_secret, message)
        VALUES (?, ?, ?, ?)
        """
        
        db.execute_query(query, [sender_id, recipient['id'], encrypted_secret, message])
        
        # Return created share
        return ShareDB.get_user_shares(sender_id, sent=True, limit=1)[0]
    
    @staticmethod
    def get_user_shares(user_id, sent=True, received=True, limit=None):
        """Get shares for user"""
        conditions = []
        params = []
        
        if sent and received:
            conditions.append("(sender_id = ? OR recipient_id = ?)")
            params.extend([user_id, user_id])
        elif sent:
            conditions.append("sender_id = ?")
            params.append(user_id)
        elif received:
            conditions.append("recipient_id = ?")
            params.append(user_id)
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        query = f"""
        SELECT s.*, 
               sender.email as sender_email,
               recipient.email as recipient_email
        FROM shares s
        JOIN users sender ON s.sender_id = sender.id
        JOIN users recipient ON s.recipient_id = recipient.id
        WHERE {where_clause}
        ORDER BY s.created_at DESC
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        return db.execute_query(query, params)

class BackupDB:
    """Backup database operations using SQL"""
    
    @staticmethod
    def create_backup(user_id, name, filename, file_path, size_bytes=0, checksum=""):
        """Create new backup record"""
        query = """
        INSERT INTO backups (user_id, name, filename, file_path, size_bytes, checksum)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        
        db.execute_query(query, [user_id, name, filename, file_path, size_bytes, checksum])
        
        # Return created backup
        return BackupDB.get_user_backups(user_id, limit=1)[0]
    
    @staticmethod
    def get_user_backups(user_id, limit=None):
        """Get all backups for user"""
        query = """
        SELECT * FROM backups 
        WHERE user_id = ? 
        ORDER BY created_at DESC
        """
        if limit:
            query += f" LIMIT {limit}"
        
        return db.execute_query(query, [user_id])

class SessionLogDB:
    """Session logging using SQL"""
    
    @staticmethod
    def log_action(user_id, action, ip_address="", user_agent="", success=True, details=None):
        """Log user action"""
        query = """
        INSERT INTO session_logs (user_id, action, ip_address, user_agent, success, details)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        
        details_json = json.dumps(details) if details else None
        db.execute_query(query, [user_id, action, ip_address, user_agent, success, details_json])