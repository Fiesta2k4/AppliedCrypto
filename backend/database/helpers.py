from datetime import datetime
from .config import db
import json
import sqlite3
import uuid
import os

# ✅ Import DATABASE_PATH from config
DATABASE_PATH = getattr(db, 'db_path', 'vault.db')

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
        """Update user with dynamic fields"""
        try:
            if not kwargs:
                return None
            
            # Build SET clause dynamically
            set_parts = []
            params = []
            
            for key, value in kwargs.items():
                if key in ['email', 'public_key', 'salt', 'password_hash']:
                    set_parts.append(f"{key} = ?")
                    params.append(value)
            
            if not set_parts:
                print("⚠️ No valid fields to update")
                return None
            
            set_clause = ", ".join(set_parts)
            params.append(user_id)  # Add user_id for WHERE clause
            
            query = f"""
            UPDATE users 
            SET {set_clause}, updated_at = CURRENT_TIMESTAMP 
            WHERE id = ?
            """
            
            print(f"🔍 Update query: {query}")
            print(f"🔍 Update params: {params}")
            
            rows_affected = db.execute_query(query, params)
            
            if rows_affected > 0:
                # Return updated user
                return UserDB.get_user_by_id(user_id)
            else:
                print(f"⚠️ No rows affected for user_id: {user_id}")
                return None
                
        except Exception as e:
            print(f"❌ Update user error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    @staticmethod
    def get_all_active_users():
        """Get all active vault users"""
        try:
            query = """
            SELECT id, email, created_at, updated_at, public_key, is_active
            FROM users 
            WHERE is_active = 1 
            ORDER BY created_at ASC
            """
            users = db.execute_query(query, [])
            return users if users else []
        except Exception as e:
            print(f"❌ Get all active users error: {e}")
            return []
    
    @staticmethod
    def get_all_users():
        """Get all active users for sharing"""
        try:
            query = """
            SELECT id, email, created_at, public_key, is_active
            FROM users 
            WHERE is_active = 1 OR is_active IS NULL
            ORDER BY created_at ASC
            """
            users = db.execute_query(query, [])
            return users if users else []
        except Exception as e:
            print(f"❌ Get all users error: {e}")
            return []

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
    """Share database operations for internal users only"""
    
    @staticmethod
    def create_share(sender_id: str, recipient_id: str, encrypted_secret: str, message: str = ""):
        """Create new share record between registered users"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                
                share_id = str(uuid.uuid4())
                created_at = datetime.now().isoformat()
                
                cursor.execute("""
                    INSERT INTO shares (id, sender_id, recipient_id, encrypted_secret, message, created_at, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (share_id, sender_id, recipient_id, encrypted_secret, message, created_at, 'pending'))
                
                conn.commit()
                
                return {
                    'id': share_id,
                    'sender_id': sender_id,
                    'recipient_id': recipient_id,
                    'message': message,
                    'created_at': created_at,
                    'status': 'pending'
                }
                
        except Exception as e:
            print(f"Create share error: {e}")
            return None
    
    @staticmethod
    def get_incoming_shares(user_id: str):
        """Get shares received by user (using recipient_id)"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT s.*, u.email as sender_email 
                    FROM shares s
                    JOIN users u ON s.sender_id = u.id
                    WHERE s.recipient_id = ? 
                    ORDER BY s.created_at DESC
                """, (user_id,))
                
                shares = []
                for row in cursor.fetchall():
                    share = dict(row)
                    shares.append(share)
                
                return shares
                
        except Exception as e:
            print(f"Get incoming shares error: {e}")
            return []
    
    @staticmethod
    def get_outgoing_shares(sender_id: str):
        """Get shares sent by user"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT s.*, u.email as recipient_email 
                    FROM shares s
                    JOIN users u ON s.recipient_id = u.id
                    WHERE s.sender_id = ? 
                    ORDER BY s.created_at DESC
                """, (sender_id,))
                
                shares = []
                for row in cursor.fetchall():
                    share = dict(row)
                    shares.append(share)
                
                return shares
                
        except Exception as e:
            print(f"Get outgoing shares error: {e}")
            return []
    
    @staticmethod
    def get_share_by_id(share_id: str):
        """Get share by ID with sender/recipient info"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT s.*, 
                           sender.email as sender_email,
                           recipient.email as recipient_email
                    FROM shares s
                    JOIN users sender ON s.sender_id = sender.id
                    JOIN users recipient ON s.recipient_id = recipient.id
                    WHERE s.id = ?
                """, (share_id,))
                
                row = cursor.fetchone()
                
                if row:
                    return dict(row)
                
                return None
                
        except Exception as e:
            print(f"Get share by ID error: {e}")
            return None
    
    @staticmethod
    def mark_share_as_read(share_id: str, user_id: str):
        """Mark share as read by recipient"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE shares 
                    SET status = 'read', updated_at = CURRENT_TIMESTAMP
                    WHERE id = ? AND recipient_id = ?
                """, (share_id, user_id))
                
                conn.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            print(f"Mark share as read error: {e}")
            return False

class BackupDB:
    """Backup database operations using SQL (not MongoDB)"""
    
    @staticmethod
    def create_backup(user_id, name, filename, file_path, size_bytes=0, checksum=""):
        """Create new backup record"""
        try:
            print(f"🔍 BackupDB.create_backup called with:")
            print(f"   user_id: {user_id}")
            print(f"   name: {name}")
            print(f"   filename: {filename}")
            print(f"   file_path: {file_path}")
            print(f"   size_bytes: {size_bytes}")
            
            query = """
            INSERT INTO backups (user_id, name, filename, file_path, size_bytes, checksum)
            VALUES (?, ?, ?, ?, ?, ?)
            """
            
            print(f"🔍 Executing query: {query}")
            print(f"🔍 With params: [{user_id}, {name}, {filename}, {file_path}, {size_bytes}, {checksum}]")
            
            rows_affected = db.execute_query(query, [user_id, name, filename, file_path, size_bytes, checksum])
            
            print(f"🔍 Rows affected: {rows_affected}")
            
            if rows_affected > 0:
                # Return created backup by getting the latest one
                backups = BackupDB.get_user_backups(user_id, limit=1)
                print(f"🔍 Latest backup after creation: {backups}")
                return backups[0] if backups else None
            
            print("❌ No rows affected")
            return None
            
        except Exception as e:
            print(f"❌ Create backup error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    @staticmethod
    def get_user_backups(user_id, limit=None):
        """Get all backups for user"""
        try:
            print(f"🔍 BackupDB.get_user_backups called with user_id: {user_id}")
            
            query = """
            SELECT * FROM backups 
            WHERE user_id = ? 
            ORDER BY created_at DESC
            """
            if limit:
                query += f" LIMIT {limit}"
            
            print(f"🔍 Executing query: {query}")
            print(f"🔍 With params: [{user_id}]")
            
            result = db.execute_query(query, [user_id])
            
            print(f"🔍 Query result: {result}")
            print(f"🔍 Result type: {type(result)}")
            print(f"🔍 Result length: {len(result) if result else 'None'}")
            
            if result:
                for i, backup in enumerate(result):
                    print(f"🔍 Backup {i}: {dict(backup) if hasattr(backup, 'keys') else backup}")
            
            return result if result else []
        
        except Exception as e:
            print(f"❌ Get user backups error: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    @staticmethod
    def get_backup_by_id(backup_id: str, user_id: str):
        """Get backup by ID with user verification"""
        try:
            query = "SELECT * FROM backups WHERE id = ? AND user_id = ?"
            backups = db.execute_query(query, [backup_id, user_id])
            return backups[0] if backups else None
        except Exception as e:
            print(f"❌ Get backup by ID error: {e}")
            return None
    
    @staticmethod
    def delete_backup(backup_id: str, user_id: str):
        """Delete backup record"""
        try:
            query = "DELETE FROM backups WHERE id = ? AND user_id = ?"
            rows_affected = db.execute_query(query, [backup_id, user_id])
            return rows_affected > 0
        except Exception as e:
            print(f"❌ Delete backup error: {e}")
            return False
    
    # Add debug method to check table existence
    @staticmethod
    def debug_table_info():
        """Debug method to check backup table"""
        try:
            print("🔍 === BACKUP TABLE DEBUG ===")
            
            # Check if table exists
            query = "SELECT name FROM sqlite_master WHERE type='table' AND name='backups'"
            tables = db.execute_query(query, [])
            print(f"🔍 Backup table exists: {len(tables) > 0}")
            
            if tables:
                # Get table schema
                schema_query = "PRAGMA table_info(backups)"
                schema = db.execute_query(schema_query, [])
                print(f"🔍 Backup table schema:")
                for col in schema:
                    print(f"   {col}")
                
                # Count total records
                count_query = "SELECT COUNT(*) as count FROM backups"
                count_result = db.execute_query(count_query, [])
                total_count = count_result[0]['count'] if count_result else 0
                print(f"🔍 Total backup records: {total_count}")
                
                # Get all records for debugging
                all_query = "SELECT * FROM backups ORDER BY created_at DESC LIMIT 10"
                all_records = db.execute_query(all_query, [])
                print(f"🔍 Recent backup records:")
                for i, record in enumerate(all_records):
                    print(f"   {i}: {dict(record)}")
                    
                # Check for specific user_id
                print(f"🔍 Checking for user_ids in backup table...")
                user_query = "SELECT DISTINCT user_id FROM backups"
                user_results = db.execute_query(user_query, [])
                print(f"🔍 Unique user_ids in backups: {[r['user_id'] for r in user_results]}")
        
        except Exception as e:
            print(f"❌ Debug table info error: {e}")
            import traceback
            traceback.print_exc()

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
    
    @staticmethod
    def get_user_logs(user_id, limit=50):
        """Get user session logs"""
        try:
            query = """
            SELECT * FROM session_logs 
            WHERE user_id = ? 
            ORDER BY created_at DESC 
            LIMIT ?
            """
            return db.execute_query(query, [user_id, limit])
        except Exception as e:
            print(f"❌ Get user logs error: {e}")
            return []

# ✅ OTPDB class for completeness
class OTPDB:
    """OTP database operations"""
    
    @staticmethod
    def create_otp_secret(user_id, service_name, encrypted_secret, metadata=None):
        """Create new OTP secret"""
        # This would be implemented when OTP feature is added
        pass
    
    @staticmethod
    def get_user_otp_secrets(user_id):
        """Get user's OTP secrets"""
        # This would be implemented when OTP feature is added
        return []