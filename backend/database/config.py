import os
import sqlite3
import json
from pathlib import Path

class SQLiteDatabase:
    def __init__(self, db_path="vault.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        try:
            db_dir = Path(self.db_path).parent
            db_dir.mkdir(exist_ok=True)
            
            schema_path = Path(__file__).parent / "schema.sql"
            if schema_path.exists():
                with open(schema_path, 'r', encoding='utf-8') as f:
                    schema_sql = f.read()
                
                with sqlite3.connect(self.db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    conn.executescript(schema_sql)
                    conn.commit()
                print(f"✅ Database initialized: {self.db_path}")
                
                # Verify all tables
                self.verify_all_tables()
            else:
                print("❌ Schema file not found")
                self.create_fallback_tables()
                
        except Exception as e:
            print(f"❌ Database init error: {e}")
            print("🔧 Attempting to fix database...")
            self.fix_database()
    
    def verify_all_tables(self):
        """Verify all required tables exist"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check required tables
                required_tables = ['users', 'vault_entries', 'otp_secrets', 'backups', 'shares']
                
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                existing_tables = [row[0] for row in cursor.fetchall()]
                
                missing_tables = set(required_tables) - set(existing_tables)
                
                if missing_tables:
                    print(f"🔧 Missing tables: {missing_tables}")
                    self.fix_database()
                else:
                    print("✅ All required tables exist")
                    
                # Verify OTP table structure specifically
                self.verify_otp_table()
                
        except Exception as e:
            print(f"❌ Table verification error: {e}")
            self.fix_database()
    
    def verify_otp_table(self):
        """Verify OTP table has all required columns"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if otp_secrets table exists
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='otp_secrets'")
                if not cursor.fetchone():
                    print("🔧 Creating missing otp_secrets table...")
                    self.create_otp_table(conn)
                    return
                
                # Check table structure
                cursor.execute("PRAGMA table_info(otp_secrets)")
                columns = {row[1]: row[2] for row in cursor.fetchall()}
                
                required_columns = {
                    'id': 'TEXT',
                    'user_id': 'TEXT', 
                    'issuer': 'TEXT',
                    'account': 'TEXT',
                    'encrypted_secret': 'TEXT',
                    'digits': 'INTEGER',
                    'period': 'INTEGER',
                    'algorithm': 'TEXT',
                    'is_active': 'BOOLEAN',
                    'created_at': 'DATETIME',
                    'updated_at': 'DATETIME'
                }
                
                missing_columns = []
                for col_name, col_type in required_columns.items():
                    if col_name not in columns:
                        missing_columns.append((col_name, col_type))
                
                if missing_columns:
                    print(f"🔧 Adding missing columns to otp_secrets: {[col[0] for col in missing_columns]}")
                    for col_name, col_type in missing_columns:
                        try:
                            default_value = self.get_default_value(col_name)
                            cursor.execute(f"ALTER TABLE otp_secrets ADD COLUMN {col_name} {col_type} {default_value}")
                        except sqlite3.Error as e:
                            print(f"❌ Failed to add column {col_name}: {e}")
                    
                    conn.commit()
                    print("✅ OTP table structure fixed")
                else:
                    print("✅ OTP table structure verified")
                    
        except Exception as e:
            print(f"❌ OTP table verification error: {e}")
            self.fix_database()
    
    def get_default_value(self, col_name):
        """Get default value for column"""
        defaults = {
            'id': "DEFAULT (lower(hex(randomblob(16))))",
            'issuer': "DEFAULT ''",
            'account': "DEFAULT ''", 
            'encrypted_secret': "DEFAULT ''",
            'digits': "DEFAULT 6",
            'period': "DEFAULT 30",
            'algorithm': "DEFAULT 'SHA1'",
            'is_active': "DEFAULT 1",
            'created_at': "DEFAULT CURRENT_TIMESTAMP",
            'updated_at': "DEFAULT CURRENT_TIMESTAMP"
        }
        return defaults.get(col_name, "")
    
    def create_otp_table(self, conn):
        """Create OTP table with all required columns"""
        otp_sql = """
        CREATE TABLE IF NOT EXISTS otp_secrets (
            id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
            user_id TEXT NOT NULL,
            issuer TEXT NOT NULL DEFAULT '',
            account TEXT NOT NULL DEFAULT '',
            encrypted_secret TEXT NOT NULL DEFAULT '',
            digits INTEGER DEFAULT 6 CHECK (digits IN (6, 7, 8)),
            period INTEGER DEFAULT 30 CHECK (period IN (15, 30, 60)),
            algorithm TEXT DEFAULT 'SHA1' CHECK (algorithm IN ('SHA1', 'SHA256', 'SHA512')),
            is_active BOOLEAN DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        
        CREATE INDEX IF NOT EXISTS idx_otp_user_id ON otp_secrets(user_id);
        CREATE INDEX IF NOT EXISTS idx_otp_active ON otp_secrets(is_active);
        CREATE INDEX IF NOT EXISTS idx_otp_issuer ON otp_secrets(issuer);
        
        CREATE TRIGGER IF NOT EXISTS update_otp_secrets_timestamp 
            AFTER UPDATE ON otp_secrets FOR EACH ROW
        BEGIN
            UPDATE otp_secrets SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
        END;
        """
        
        conn.executescript(otp_sql)
        conn.commit()
        print("✅ OTP table created successfully")
    
    def fix_database(self):
        """Fix database by recreating with correct schema"""
        try:
            print("🔧 Fixing database schema...")
            
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # Create all essential tables
                essential_sql = """
                PRAGMA foreign_keys = ON;
                
                -- Users table
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
                    email TEXT UNIQUE NOT NULL,
                    salt TEXT NOT NULL,
                    password_hash TEXT NOT NULL,
                    public_key TEXT DEFAULT '',
                    is_active BOOLEAN DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
                
                -- Vault entries table
                CREATE TABLE IF NOT EXISTS vault_entries (
                    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
                    user_id TEXT NOT NULL,
                    iv TEXT NOT NULL,
                    ciphertext TEXT NOT NULL,
                    tag TEXT NOT NULL,
                    metadata TEXT DEFAULT '{}',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                );
                
                -- Shares table
                CREATE TABLE IF NOT EXISTS shares (
                    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
                    sender_id TEXT NOT NULL,
                    recipient_id TEXT NOT NULL,
                    encrypted_secret TEXT NOT NULL,
                    message TEXT DEFAULT '',
                    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'declined', 'expired')),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (recipient_id) REFERENCES users(id) ON DELETE CASCADE
                );
                
                -- Backups table
                CREATE TABLE IF NOT EXISTS backups (
                    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
                    user_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    size_bytes INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'completed',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                );
                
                -- Essential indexes
                CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
                CREATE INDEX IF NOT EXISTS idx_vault_user_id ON vault_entries(user_id);
                CREATE INDEX IF NOT EXISTS idx_backups_user_id ON backups(user_id);
                CREATE INDEX IF NOT EXISTS idx_shares_sender ON shares(sender_id);
                CREATE INDEX IF NOT EXISTS idx_shares_recipient ON shares(recipient_id);
                CREATE INDEX IF NOT EXISTS idx_shares_status ON shares(status);
                
                -- Essential triggers
                CREATE TRIGGER IF NOT EXISTS update_users_timestamp 
                    AFTER UPDATE ON users FOR EACH ROW
                BEGIN
                    UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
                END;
                
                CREATE TRIGGER IF NOT EXISTS update_vault_entries_timestamp 
                    AFTER UPDATE ON vault_entries FOR EACH ROW
                BEGIN
                    UPDATE vault_entries SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
                END;
                
                CREATE TRIGGER IF NOT EXISTS update_shares_timestamp 
                    AFTER UPDATE ON shares FOR EACH ROW
                BEGIN
                    UPDATE shares SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
                END;
                """
                
                conn.executescript(essential_sql)
                
                # Create OTP table with all columns
                self.create_otp_table(conn)
                
                print("✅ Database schema fixed")
                
        except Exception as e:
            print(f"❌ Database fix failed: {e}")
            raise
    
    def create_fallback_tables(self):
        """Create fallback tables if schema.sql not found"""
        print("🔧 Creating fallback database tables...")
        self.fix_database()
    
    def execute_query(self, query, params=None):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                if query.strip().upper().startswith('SELECT'):
                    return [dict(row) for row in cursor.fetchall()]
                else:
                    conn.commit()
                    return cursor.rowcount
        except Exception as e:
            print(f"❌ Query error: {e}")
            print(f"🔍 Query: {query}")
            print(f"🔍 Params: {params}")
            raise

# Global database instance
db = SQLiteDatabase()

# Database Operations Classes
class UserDB:
    @staticmethod
    def create_user(email, salt, password_hash, public_key=""):
        query = "INSERT INTO users (email, salt, password_hash, public_key) VALUES (?, ?, ?, ?)"
        try:
            db.execute_query(query, [email, salt, password_hash, public_key])
            return UserDB.get_user_by_email(email)
        except Exception as e:
            print(f"❌ Create user error: {e}")
            return None
    
    @staticmethod
    def get_user_by_email(email):
        query = "SELECT * FROM users WHERE email = ?"
        users = db.execute_query(query, [email])
        return users[0] if users else None
    
    @staticmethod
    def get_user_by_id(user_id):
        query = "SELECT * FROM users WHERE id = ?"
        users = db.execute_query(query, [user_id])
        return users[0] if users else None
    
    @staticmethod
    def get_all_users():
        query = "SELECT id, email, public_key, created_at FROM users WHERE is_active = 1"
        return db.execute_query(query, [])
    
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
            params.append(user_id)
            
            query = f"""
            UPDATE users 
            SET {set_clause}, updated_at = CURRENT_TIMESTAMP 
            WHERE id = ?
            """
            
            rows_affected = db.execute_query(query, params)
            
            if rows_affected > 0:
                return UserDB.get_user_by_id(user_id)
            else:
                print(f"⚠️ No rows affected for user_id: {user_id}")
                return None
                
        except Exception as e:
            print(f"❌ Update user error: {e}")
            return None

class VaultDB:
    @staticmethod
    def create_entry(user_id, iv, ciphertext, tag, metadata=None):
        query = "INSERT INTO vault_entries (user_id, iv, ciphertext, tag, metadata) VALUES (?, ?, ?, ?, ?)"
        metadata_json = json.dumps(metadata) if metadata else '{}'
        db.execute_query(query, [user_id, iv, ciphertext, tag, metadata_json])
        return VaultDB.get_user_entries(user_id, limit=1)[0]
    
    @staticmethod
    def get_user_entries(user_id, limit=None):
        query = "SELECT * FROM vault_entries WHERE user_id = ? ORDER BY created_at DESC"
        if limit:
            query += f" LIMIT {limit}"
        
        entries = db.execute_query(query, [user_id])
        for entry in entries:
            try:
                entry['metadata'] = json.loads(entry['metadata']) if entry['metadata'] else {}
            except:
                entry['metadata'] = {}
        return entries
    
    @staticmethod
    def delete_entry(entry_id, user_id):
        query = "DELETE FROM vault_entries WHERE id = ? AND user_id = ?"
        return db.execute_query(query, [entry_id, user_id]) > 0

class OTPDB:
    @staticmethod
    def create_otp_secret(user_id, issuer, account, encrypted_secret, digits=6, period=30, algorithm='SHA1'):
        query = """
        INSERT INTO otp_secrets (user_id, issuer, account, encrypted_secret, digits, period, algorithm)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        try:
            print(f"🔍 Creating OTP secret: {issuer} - {account}")
            db.execute_query(query, [user_id, issuer, account, encrypted_secret, digits, period, algorithm])
            return OTPDB.get_user_otp_secrets(user_id, limit=1)[0]
        except Exception as e:
            print(f"❌ Create OTP secret error: {e}")
            return None
    
    @staticmethod
    def get_user_otp_secrets(user_id, limit=None):
        # First check if table exists with all columns
        try:
            # Test query to check columns exist
            test_query = "SELECT issuer, account FROM otp_secrets LIMIT 1"
            db.execute_query(test_query, [])
        except Exception as e:
            print(f"🔧 OTP table issue detected: {e}")
            # Force table verification
            db.verify_otp_table()
        
        query = """
        SELECT id, issuer, account, digits, period, algorithm, created_at
        FROM otp_secrets WHERE user_id = ? AND is_active = 1 ORDER BY created_at DESC
        """
        if limit:
            query += f" LIMIT {limit}"
        
        try:
            return db.execute_query(query, [user_id])
        except Exception as e:
            print(f"❌ Get OTP secrets error: {e}")
            return []
    
    @staticmethod
    def get_otp_secret_by_id(otp_id, user_id):
        query = "SELECT * FROM otp_secrets WHERE id = ? AND user_id = ? AND is_active = 1"
        try:
            results = db.execute_query(query, [otp_id, user_id])
            return results[0] if results else None
        except Exception as e:
            print(f"❌ Get OTP secret by ID error: {e}")
            return None
    
    @staticmethod
    def delete_otp_secret(otp_id, user_id):
        query = "UPDATE otp_secrets SET is_active = 0 WHERE id = ? AND user_id = ?"
        try:
            return db.execute_query(query, [otp_id, user_id]) > 0
        except Exception as e:
            print(f"❌ Delete OTP secret error: {e}")
            return False

class BackupDB:
    @staticmethod
    def create_backup(user_id, name, filename, file_path, size_bytes=0):
        """Create backup record"""
        query = """
        INSERT INTO backups (user_id, name, filename, file_path, size_bytes)
        VALUES (?, ?, ?, ?, ?)
        """
        try:
            print(f"🔍 BackupDB.create_backup called with:")
            print(f"   user_id: {user_id}")
            print(f"   name: {name}")
            print(f"   filename: {filename}")
            print(f"   file_path: {file_path}")
            print(f"   size_bytes: {size_bytes}")
            
            # Execute insert
            rows_affected = db.execute_query(query, [user_id, name, filename, file_path, size_bytes])
            print(f"🔍 Insert query affected {rows_affected} rows")
            
            # Get the created backup
            if rows_affected > 0:
                # Get latest backup for this user
                created_backup = BackupDB.get_user_backups(user_id, limit=1)
                if created_backup:
                    print(f"✅ Backup record created: {created_backup[0]['id']}")
                    return created_backup[0]
                else:
                    print("❌ Failed to retrieve created backup")
                    return None
            else:
                print("❌ No rows affected by insert")
                return None
                
        except Exception as e:
            print(f"❌ Create backup error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    @staticmethod
    def get_user_backups(user_id, limit=None):
        """Get backups for user"""
        query = "SELECT * FROM backups WHERE user_id = ? ORDER BY created_at DESC"
        if limit:
            query += f" LIMIT {limit}"
        
        try:
            print(f"🔍 BackupDB.get_user_backups called for user: {user_id}")
            
            # Check if table exists first
            check_query = "SELECT name FROM sqlite_master WHERE type='table' AND name='backups'"
            table_check = db.execute_query(check_query)
            
            if not table_check:
                print("❌ Backups table does not exist!")
                # Create table
                BackupDB._create_backups_table()
                return []
            
            print("✅ Backups table exists")
            
            # Get backups
            backups = db.execute_query(query, [user_id])
            print(f"🔍 Found {len(backups)} backups for user {user_id}")
            
            for backup in backups:
                print(f"   - {backup['name']} (ID: {backup['id']})")
            
            return backups
            
        except Exception as e:
            print(f"❌ Get user backups error: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    @staticmethod
    def get_backup_by_id(backup_id, user_id):
        """Get specific backup"""
        query = "SELECT * FROM backups WHERE id = ? AND user_id = ?"
        try:
            backups = db.execute_query(query, [backup_id, user_id])
            return backups[0] if backups else None
        except Exception as e:
            print(f"❌ Get backup by ID error: {e}")
            return None
    
    @staticmethod
    def delete_backup(backup_id, user_id):
        """Delete backup"""
        query = "DELETE FROM backups WHERE id = ? AND user_id = ?"
        try:
            rows_affected = db.execute_query(query, [backup_id, user_id])
            return rows_affected > 0
        except Exception as e:
            print(f"❌ Delete backup error: {e}")
            return False
    
    @staticmethod
    def _create_backups_table():
        """Create backups table if missing"""
        try:
            create_sql = """
            CREATE TABLE IF NOT EXISTS backups (
                id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
                user_id TEXT NOT NULL,
                name TEXT NOT NULL,
                filename TEXT NOT NULL,
                file_path TEXT NOT NULL,
                size_bytes INTEGER DEFAULT 0,
                status TEXT DEFAULT 'completed',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
            
            CREATE INDEX IF NOT EXISTS idx_backups_user_id ON backups(user_id);
            """
            
            db.execute_query(create_sql)
            print("✅ Backups table created")
            
        except Exception as e:
            print(f"❌ Failed to create backups table: {e}")

class ShareDB:
    """Share operations"""
    
    @staticmethod
    def create_share(sender_id, recipient_id, encrypted_secret, message=""):
        """Create share record"""
        query = """
        INSERT INTO shares (sender_id, recipient_id, encrypted_secret, message)
        VALUES (?, ?, ?, ?)
        """
        try:
            print(f"🔍 ShareDB.create_share called:")
            print(f"   sender_id: {sender_id}")
            print(f"   recipient_id: {recipient_id}")
            print(f"   message: {message}")
            
            rows_affected = db.execute_query(query, [sender_id, recipient_id, encrypted_secret, message])
            print(f"🔍 Insert affected {rows_affected} rows")
            
            if rows_affected > 0:
                # Get the created share
                created_shares = ShareDB.get_outgoing_shares(sender_id, limit=1)
                if created_shares:
                    print(f"✅ Share created: {created_shares[0]['id']}")
                    return created_shares[0]
                else:
                    print("❌ Failed to retrieve created share")
                    return None
            else:
                print("❌ No rows affected by insert")
                return None
                
        except Exception as e:
            print(f"❌ Create share error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    @staticmethod
    def get_incoming_shares(user_id, limit=None):
        """Get shares received by user"""
        query = """
        SELECT s.*, u.email as sender_email 
        FROM shares s JOIN users u ON s.sender_id = u.id
        WHERE s.recipient_id = ? ORDER BY s.created_at DESC
        """
        if limit:
            query += f" LIMIT {limit}"
        
        try:
            print(f"🔍 ShareDB.get_incoming_shares for user: {user_id}")
            
            # Check if shares table exists
            check_query = "SELECT name FROM sqlite_master WHERE type='table' AND name='shares'"
            table_check = db.execute_query(check_query)
            
            if not table_check:
                print("❌ Shares table does not exist!")
                ShareDB._create_shares_table()
                return []
            
            shares = db.execute_query(query, [user_id])
            print(f"🔍 Found {len(shares)} incoming shares")
            
            return shares
            
        except Exception as e:
            print(f"❌ Get incoming shares error: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    @staticmethod
    def get_outgoing_shares(sender_id, limit=None):
        """Get shares sent by user"""
        query = """
        SELECT s.*, u.email as recipient_email 
        FROM shares s JOIN users u ON s.recipient_id = u.id
        WHERE s.sender_id = ? ORDER BY s.created_at DESC
        """
        if limit:
            query += f" LIMIT {limit}"
        
        try:
            print(f"🔍 ShareDB.get_outgoing_shares for user: {sender_id}")
            
            # Check if shares table exists
            check_query = "SELECT name FROM sqlite_master WHERE type='table' AND name='shares'"
            table_check = db.execute_query(check_query)
            
            if not table_check:
                print("❌ Shares table does not exist!")
                ShareDB._create_shares_table()
                return []
            
            shares = db.execute_query(query, [sender_id])
            print(f"🔍 Found {len(shares)} outgoing shares")
            
            return shares
            
        except Exception as e:
            print(f"❌ Get outgoing shares error: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    @staticmethod
    def get_share_by_id(share_id, user_id):
        """Get specific share (for recipient only)"""
        query = """
        SELECT s.*, u.email as sender_email 
        FROM shares s JOIN users u ON s.sender_id = u.id
        WHERE s.id = ? AND s.recipient_id = ?
        """
        try:
            shares = db.execute_query(query, [share_id, user_id])
            return shares[0] if shares else None
        except Exception as e:
            print(f"❌ Get share by ID error: {e}")
            return None
    
    @staticmethod
    def update_share_status(share_id, recipient_id, status):
        """Update share status"""
        query = """
        UPDATE shares 
        SET status = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ? AND recipient_id = ?
        """
        try:
            print(f"🔍 Updating share {share_id} status to: {status}")
            rows_affected = db.execute_query(query, [status, share_id, recipient_id])
            return rows_affected > 0
        except Exception as e:
            print(f"❌ Update share status error: {e}")
            return False
    
    @staticmethod
    def delete_share(share_id, user_id):
        """Delete share (sender or recipient can delete)"""
        query = """
        DELETE FROM shares 
        WHERE id = ? AND (sender_id = ? OR recipient_id = ?)
        """
        try:
            rows_affected = db.execute_query(query, [share_id, user_id, user_id])
            return rows_affected > 0
        except Exception as e:
            print(f"❌ Delete share error: {e}")
            return False
    
    @staticmethod
    def _create_shares_table():
        """Create shares table if missing"""
        try:
            create_sql = """
            CREATE TABLE IF NOT EXISTS shares (
                id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
                sender_id TEXT NOT NULL,
                recipient_id TEXT NOT NULL,
                encrypted_secret TEXT NOT NULL,
                message TEXT DEFAULT '',
                status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'declined', 'expired')),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (recipient_id) REFERENCES users(id) ON DELETE CASCADE
            );
            
            CREATE INDEX IF NOT EXISTS idx_shares_sender ON shares(sender_id);
            CREATE INDEX IF NOT EXISTS idx_shares_recipient ON shares(recipient_id);
            CREATE INDEX IF NOT EXISTS idx_shares_status ON shares(status);
            
            CREATE TRIGGER IF NOT EXISTS update_shares_timestamp 
                AFTER UPDATE ON shares FOR EACH ROW
            BEGIN
                UPDATE shares SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
            END;
            """
            
            db.execute_query(create_sql)
            print("✅ Shares table created")
            
        except Exception as e:
            print(f"❌ Failed to create shares table: {e}")