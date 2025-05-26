import sqlite3
import os
from pathlib import Path

class DatabaseInitializer:
    def __init__(self, db_path="vault.db"):
        self.db_path = db_path
        self.schema_path = Path(__file__).parent / "schema.sql"
    
    def initialize_database(self):
        """Initialize database from SQL schema file"""
        print(f"🔧 Initializing database: {self.db_path}")
        
        if not self.schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {self.schema_path}")
        
        # Read SQL schema
        with open(self.schema_path, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
        # Execute schema
        conn = sqlite3.connect(self.db_path)
        try:
            # Enable foreign keys
            conn.execute("PRAGMA foreign_keys = ON")
            
            # Execute schema (split by semicolon and execute individually)
            statements = [stmt.strip() for stmt in schema_sql.split(';') if stmt.strip()]
            
            for statement in statements:
                if statement.startswith('--') or not statement:
                    continue
                try:
                    conn.execute(statement)
                except sqlite3.Error as e:
                    print(f"⚠️  SQL Error in statement: {statement[:50]}...")
                    print(f"   Error: {e}")
            
            conn.commit()
            print("✅ Database schema created successfully")
            
            # Verify tables
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            print(f"📊 Created tables: {', '.join(tables)}")
            
            return True
            
        except Exception as e:
            print(f"❌ Database initialization failed: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def get_stats(self):
        """Get database statistics"""
        if not os.path.exists(self.db_path):
            return {"error": "Database not found"}
        
        conn = sqlite3.connect(self.db_path)
        try:
            stats = {}
            
            # Get table counts
            tables = ['users', 'vault_entries', 'shares', 'backups', 'otp_secrets', 'session_logs']
            for table in tables:
                cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
                stats[f"{table}_count"] = cursor.fetchone()[0]
            
            # Database size
            stats['db_size_bytes'] = os.path.getsize(self.db_path)
            stats['db_size_mb'] = round(stats['db_size_bytes'] / (1024 * 1024), 2)
            
            return stats
            
        except Exception as e:
            return {"error": str(e)}
        finally:
            conn.close()
    
    def reset_database(self):
        """Reset database (delete and recreate)"""
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
            print(f"🗑️  Deleted existing database: {self.db_path}")
        
        return self.initialize_database()

# For direct usage
if __name__ == "__main__":
    db_init = DatabaseInitializer()
    
    print("🔐 Personal Vault Database Initializer")
    print("=" * 50)
    
    # Initialize database
    success = db_init.initialize_database()
    
    if success:
        # Show stats
        stats = db_init.get_stats()
        print(f"📊 Database Stats: {stats}")
        
        print("\n✅ Database ready for use!")
        print("🔧 To reset database: python backend/database/init_db.py --reset")
    else:
        print("❌ Database initialization failed!")