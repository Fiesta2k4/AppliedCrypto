import os
import sqlite3
from pathlib import Path

class DatabaseConfig:
    """Configuration for SQLite database"""
    
    # SQLite database file
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'vault.db')
    DATABASE_URL = f'sqlite:///{DATABASE_PATH}'
    
    # Database settings
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class SQLiteDatabase:
    """SQLite database manager"""
    
    def __init__(self, db_path='vault.db'):
        self.db_path = db_path
        self.schema_path = Path(__file__).parent / "schema.sql"
        # Force initialization to check for tables
        self.init_db()
    
    def init_db(self):
        """Initialize database using schema.sql"""
        try:
            # Always check if tables exist
            needs_init = True
            
            if os.path.exists(self.db_path):
                # Check if tables exist
                conn = sqlite3.connect(self.db_path)
                cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
                tables = cursor.fetchall()
                conn.close()
                
                if tables:
                    print(f"✅ Database and tables exist: {self.db_path}")
                    needs_init = False
                else:
                    print("⚠️  Database exists but no tables found")
            else:
                print(f"🔧 Creating new database: {self.db_path}")
            
            if needs_init:
                self._create_schema_from_file()
                
        except Exception as e:
            print(f"❌ Database initialization failed: {e}")
            # Delete corrupted database and recreate
            if os.path.exists(self.db_path):
                os.remove(self.db_path)
                print("🗑️  Removed corrupted database")
            self._create_schema_from_file()
    
    def _create_schema_from_file(self):
        """Create database schema from schema.sql file"""
        print("🔧 Creating database schema from schema.sql...")
        
        try:
            # Check if schema file exists
            if not self.schema_path.exists():
                print(f"❌ Schema file not found: {self.schema_path}")
                self._create_minimal_schema()
                return
            
            # Read schema file
            with open(self.schema_path, 'r', encoding='utf-8') as f:
                schema_sql = f.read()
            
            print(f"📄 Read schema file: {len(schema_sql)} characters")
            
            # Execute schema
            conn = sqlite3.connect(self.db_path)
            conn.executescript(schema_sql)
            conn.close()
            
            # Verify tables were created
            conn = sqlite3.connect(self.db_path)
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            print(f"✅ Schema created successfully")
            print(f"📋 Tables created: {tables}")
            
            # Insert test data if in development
            self._insert_test_data()
            
        except Exception as e:
            print(f"❌ Schema creation failed: {e}")
            print("🔧 Falling back to minimal schema...")
            self._create_minimal_schema()
    
    def _create_minimal_schema(self):
        """Create minimal schema if schema.sql fails"""
        print("🔧 Creating minimal schema...")
        
        minimal_schema = """
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
            metadata TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        
        -- Session logs table
        CREATE TABLE IF NOT EXISTS session_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            action TEXT NOT NULL,
            ip_address TEXT,
            user_agent TEXT,
            success BOOLEAN DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
        );
        
        -- Indexes
        CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
        CREATE INDEX IF NOT EXISTS idx_vault_user_id ON vault_entries(user_id);
        CREATE INDEX IF NOT EXISTS idx_logs_user_id ON session_logs(user_id);
        """
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.executescript(minimal_schema)
            conn.close()
            
            print("✅ Minimal schema created successfully")
            self._insert_test_data()
            
        except Exception as e:
            print(f"❌ Minimal schema creation failed: {e}")
            raise
    
    def _insert_test_data(self):
        """Insert test data for development"""
        try:
            test_data = """
            -- Test user (only if no users exist)
            INSERT OR IGNORE INTO users (id, email, salt, password_hash, public_key) 
            VALUES (
                'test-user-001',
                'admin@vault.com',
                'test_salt_12345',
                'test_hash_67890',  
                'test_public_key_rsa'
            );
            
            -- Test vault entry
            INSERT OR IGNORE INTO vault_entries (id, user_id, iv, ciphertext, tag, metadata)
            VALUES (
                'test-entry-001',
                'test-user-001',
                'dGVzdF9pdl8xMjM=',
                'dGVzdF9jaXBoZXJfdGV4dA==', 
                'dGVzdF90YWdfaGVyZQ==',
                '{"type": "password", "name": "Test Entry", "username": "testuser", "url": "https://example.com"}'
            );
            """
            
            conn = sqlite3.connect(self.db_path)
            conn.executescript(test_data)
            conn.close()
            
            print("✅ Test data inserted")
            
        except Exception as e:
            print(f"⚠️  Test data insertion failed: {e}")
    
    def execute_query(self, query, params=None):
        """Execute a query and return results"""
        if not os.path.exists(self.db_path):
            print("⚠️  Database doesn't exist, creating...")
            self.init_db()
        
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row
        
        try:
            cursor = conn.execute(query, params or [])
            
            if query.strip().upper().startswith('SELECT'):
                results = [dict(row) for row in cursor.fetchall()]
                return results
            else:
                conn.commit()
                return cursor.rowcount
        except Exception as e:
            print(f"❌ SQL Error: {e}")
            print(f"   Query: {query}")
            print(f"   Params: {params}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def get_stats(self):
        """Get database statistics"""
        if not os.path.exists(self.db_path):
            return {"error": "Database not found"}
        
        try:
            # Get table counts
            stats = {}
            
            # Users count
            user_result = self.execute_query("SELECT COUNT(*) as count FROM users")
            stats['users_count'] = user_result[0]['count'] if user_result else 0
            
            # Vault entries count
            vault_result = self.execute_query("SELECT COUNT(*) as count FROM vault_entries")
            stats['vault_entries_count'] = vault_result[0]['count'] if vault_result else 0
            
            # Session logs count
            try:
                logs_result = self.execute_query("SELECT COUNT(*) as count FROM session_logs")
                stats['session_logs_count'] = logs_result[0]['count'] if logs_result else 0
            except:
                stats['session_logs_count'] = 0
            
            # Database size
            stats['db_size_kb'] = round(os.path.getsize(self.db_path) / 1024, 2)
            
            # List all tables
            tables_result = self.execute_query("SELECT name FROM sqlite_master WHERE type='table'")
            stats['tables'] = [row['name'] for row in tables_result]
            
            return stats
            
        except Exception as e:
            return {"error": str(e)}
    
    def reset_database(self):
        """Reset database (delete and recreate)"""
        try:
            if os.path.exists(self.db_path):
                os.remove(self.db_path)
                print(f"🗑️  Deleted database: {self.db_path}")
            
            self.init_db()
            print("✅ Database reset successfully")
            
        except Exception as e:
            print(f"❌ Database reset failed: {e}")
            raise

# Global database instance
db = SQLiteDatabase()