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
    
    def __init__(self, db_path="vault.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database with schema"""
        try:
            import sqlite3
            from pathlib import Path
            
            # Ensure database directory exists
            db_dir = Path(self.db_path).parent
            db_dir.mkdir(exist_ok=True)
            
            print(f"🔍 Initializing database at: {self.db_path}")
            
            # Read and execute schema file
            schema_path = Path(__file__).parent / "schema.sql"
            if schema_path.exists():
                print(f"🔍 Loading schema from: {schema_path}")
                with open(schema_path, 'r', encoding='utf-8') as f:
                    schema_sql = f.read()
                
                with sqlite3.connect(self.db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.executescript(schema_sql)
                    conn.commit()
                    print("✅ Schema loaded from schema.sql")
            else:
                # Fallback: Create essential tables manually
                print("⚠️ schema.sql not found, creating essential tables...")
                self.create_essential_tables()
                
        except Exception as e:
            print(f"❌ Database initialization error: {e}")
            # Try to create essential tables as fallback
            try:
                self.create_essential_tables()
                print("✅ Essential tables created as fallback")
            except Exception as fallback_error:
                print(f"❌ Fallback table creation failed: {fallback_error}")
                raise
    
    def create_essential_tables(self):
        """Create essential tables if schema.sql is not available"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Users table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
                email TEXT UNIQUE NOT NULL,
                salt TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                public_key TEXT DEFAULT '',
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            # Vault entries table
            cursor.execute("""
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
            )
            """)
            
            # Backups table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS backups (
                id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
                user_id TEXT NOT NULL,
                name TEXT NOT NULL,
                filename TEXT NOT NULL,
                file_path TEXT NOT NULL,
                size_bytes INTEGER DEFAULT 0,
                checksum TEXT DEFAULT '',
                status TEXT DEFAULT 'completed' CHECK (status IN ('pending', 'completed', 'failed', 'corrupted')),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
            """)
            
            # Shares table
            cursor.execute("""
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
            )
            """)
            
            # Session logs table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS session_logs (
                id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
                user_id TEXT,
                action TEXT NOT NULL,
                ip_address TEXT DEFAULT '',
                user_agent TEXT DEFAULT '',
                success BOOLEAN DEFAULT 1,
                details TEXT DEFAULT '',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
            )
            """)
            
            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_vault_user_id ON vault_entries(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_backups_user_id ON backups(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_shares_sender ON shares(sender_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_shares_recipient ON shares(recipient_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_session_logs_user ON session_logs(user_id)")
            
            conn.commit()
    
    def execute_query(self, query, params=None):
        """Execute SQL query and return results"""
        try:
            import sqlite3
            
            print(f"🔍 Executing SQL: {query}")
            print(f"🔍 With params: {params}")
            
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                # For SELECT queries, fetch results
                if query.strip().upper().startswith('SELECT'):
                    results = [dict(row) for row in cursor.fetchall()]
                    print(f"🔍 Query returned {len(results)} rows")
                    return results
                else:
                    # For INSERT/UPDATE/DELETE, return affected row count
                    affected = cursor.rowcount
                    conn.commit()
                    print(f"🔍 Query affected {affected} rows")
                    return affected
                    
        except Exception as e:
            print(f"❌ Database query error: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def get_stats(self):
        """Get database statistics"""
        try:
            stats = {
                'database_path': self.db_path,
                'database_exists': os.path.exists(self.db_path),
                'tables': {}
            }
            
            if not stats['database_exists']:
                stats['error'] = 'Database file does not exist'
                return stats
            
            # Get table information
            tables_query = "SELECT name FROM sqlite_master WHERE type='table'"
            tables = self.execute_query(tables_query)
            
            for table in tables:
                table_name = table['name']
                try:
                    # Get row count for each table
                    count_query = f"SELECT COUNT(*) as count FROM {table_name}"
                    count_result = self.execute_query(count_query)
                    row_count = count_result[0]['count'] if count_result else 0
                    
                    # Get table schema
                    schema_query = f"PRAGMA table_info({table_name})"
                    schema = self.execute_query(schema_query)
                    
                    stats['tables'][table_name] = {
                        'row_count': row_count,
                        'columns': len(schema),
                        'column_names': [col['name'] for col in schema]
                    }
                    
                except Exception as e:
                    stats['tables'][table_name] = {'error': str(e)}
            
            # Database file size
            if os.path.exists(self.db_path):
                stats['file_size_bytes'] = os.path.getsize(self.db_path)
                stats['file_size_mb'] = round(stats['file_size_bytes'] / (1024 * 1024), 2)
            
            return stats
            
        except Exception as e:
            return {
                'database_path': self.db_path,
                'error': f"Failed to get stats: {str(e)}"
            }
    
    def test_connection(self):
        """Test database connection"""
        try:
            test_query = "SELECT 1 as test"
            result = self.execute_query(test_query)
            return result[0]['test'] == 1 if result else False
        except Exception as e:
            print(f"❌ Database connection test failed: {e}")
            return False
    
    def get_table_list(self):
        """Get list of all tables in database"""
        try:
            query = "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            tables = self.execute_query(query)
            return [table['name'] for table in tables]
        except Exception as e:
            print(f"❌ Get table list error: {e}")
            return []
    
    def backup_database(self, backup_path):
        """Create a backup of the database"""
        try:
            import shutil
            shutil.copy2(self.db_path, backup_path)
            return True
        except Exception as e:
            print(f"❌ Database backup error: {e}")
            return False

# Global database instance
db = SQLiteDatabase()