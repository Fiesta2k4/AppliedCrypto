-- Personal Vault Database Schema
-- SQLite Database for Personal Password Manager
-- Created: 2025

-- Enable foreign key constraints
PRAGMA foreign_keys = ON;

-- ============================================
-- USERS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))), -- UUID as hex string
    email TEXT UNIQUE NOT NULL,
    salt TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    public_key TEXT,
    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Create index for faster email lookups
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active);

-- ============================================
-- VAULT ENTRIES TABLE  
-- ============================================
CREATE TABLE IF NOT EXISTS vault_entries (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    user_id TEXT NOT NULL,
    iv TEXT NOT NULL,               -- Initialization Vector (base64)
    ciphertext TEXT NOT NULL,       -- Encrypted data (base64)
    tag TEXT NOT NULL,              -- Authentication tag (base64)
    metadata TEXT,                  -- JSON metadata (type, name, url, etc)
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_vault_user_id ON vault_entries(user_id);
CREATE INDEX IF NOT EXISTS idx_vault_created ON vault_entries(created_at);

-- ============================================
-- SHARES TABLE (for sharing secrets)
-- ============================================
CREATE TABLE IF NOT EXISTS shares (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    sender_id TEXT NOT NULL,
    recipient_id TEXT NOT NULL,
    encrypted_secret TEXT NOT NULL, -- Secret encrypted with recipient's public key
    message TEXT,                   -- Optional message
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'rejected', 'expired')),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    processed_at DATETIME,
    expires_at DATETIME DEFAULT (datetime('now', '+7 days')), -- Auto expire in 7 days
    FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (recipient_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_shares_sender ON shares(sender_id);
CREATE INDEX IF NOT EXISTS idx_shares_recipient ON shares(recipient_id);
CREATE INDEX IF NOT EXISTS idx_shares_status ON shares(status);

-- ============================================
-- BACKUPS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS backups (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    user_id TEXT NOT NULL,
    name TEXT NOT NULL,
    filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    size_bytes INTEGER,
    checksum TEXT,                  -- SHA256 checksum for integrity
    status TEXT DEFAULT 'completed' CHECK (status IN ('pending', 'completed', 'failed', 'corrupted')),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_backups_user_id ON backups(user_id);
CREATE INDEX IF NOT EXISTS idx_backups_status ON backups(status);

-- ============================================
-- OTP SECRETS TABLE (for 2FA codes)
-- ============================================
CREATE TABLE IF NOT EXISTS otp_secrets (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    user_id TEXT NOT NULL,
    service_name TEXT NOT NULL,
    account_name TEXT,
    secret_key TEXT NOT NULL,       -- Base32 encoded secret
    algorithm TEXT DEFAULT 'SHA1' CHECK (algorithm IN ('SHA1', 'SHA256', 'SHA512')),
    digits INTEGER DEFAULT 6 CHECK (digits IN (6, 8)),
    period INTEGER DEFAULT 30,     -- Time period in seconds
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_otp_user_id ON otp_secrets(user_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_otp_user_service ON otp_secrets(user_id, service_name);

-- ============================================
-- SESSION LOGS TABLE (for security monitoring)
-- ============================================
CREATE TABLE IF NOT EXISTS session_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    action TEXT NOT NULL,           -- login, logout, vault_access, etc
    ip_address TEXT,
    user_agent TEXT,
    success BOOLEAN DEFAULT 1,
    details TEXT,                   -- JSON with additional info
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_logs_user_id ON session_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_logs_action ON session_logs(action);
CREATE INDEX IF NOT EXISTS idx_logs_created ON session_logs(created_at);

-- ============================================
-- TRIGGERS (for automatic updated_at)
-- ============================================

-- Update users.updated_at automatically
CREATE TRIGGER IF NOT EXISTS update_users_timestamp 
    AFTER UPDATE ON users
BEGIN
    UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Update vault_entries.updated_at automatically
CREATE TRIGGER IF NOT EXISTS update_vault_entries_timestamp 
    AFTER UPDATE ON vault_entries
BEGIN
    UPDATE vault_entries SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Update otp_secrets.updated_at automatically
CREATE TRIGGER IF NOT EXISTS update_otp_secrets_timestamp 
    AFTER UPDATE ON otp_secrets
BEGIN
    UPDATE otp_secrets SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- ============================================
-- VIEWS (for easier querying)
-- ============================================

-- User stats view
CREATE VIEW IF NOT EXISTS user_stats AS
SELECT 
    u.id,
    u.email,
    u.created_at,
    COUNT(DISTINCT ve.id) as vault_entries_count,
    COUNT(DISTINCT s1.id) as sent_shares_count,
    COUNT(DISTINCT s2.id) as received_shares_count,
    COUNT(DISTINCT b.id) as backups_count,
    COUNT(DISTINCT otp.id) as otp_secrets_count
FROM users u
LEFT JOIN vault_entries ve ON u.id = ve.user_id
LEFT JOIN shares s1 ON u.id = s1.sender_id
LEFT JOIN shares s2 ON u.id = s2.recipient_id  
LEFT JOIN backups b ON u.id = b.user_id
LEFT JOIN otp_secrets otp ON u.id = otp.user_id
GROUP BY u.id, u.email, u.created_at;

-- Recent activity view
CREATE VIEW IF NOT EXISTS recent_activity AS
SELECT 
    'vault_entry' as type,
    ve.id as item_id,
    ve.user_id,
    json_extract(ve.metadata, '$.name') as item_name,
    ve.created_at as activity_time
FROM vault_entries ve
UNION ALL
SELECT 
    'share' as type,
    s.id as item_id,
    s.sender_id as user_id,
    'Share to ' || (SELECT email FROM users WHERE id = s.recipient_id) as item_name,
    s.created_at as activity_time
FROM shares s
UNION ALL
SELECT 
    'backup' as type,
    b.id as item_id,
    b.user_id,
    b.name as item_name,
    b.created_at as activity_time
FROM backups b
ORDER BY activity_time DESC;

-- ============================================
-- SAMPLE DATA (for testing)
-- ============================================

-- Note: This will only insert if tables are empty
-- Uncomment the following lines for test data:

/*
-- Test user
INSERT OR IGNORE INTO users (id, email, salt, password_hash, public_key) 
VALUES (
    'test-user-001',
    'test@example.com',
    'random_salt_here',
    'hashed_password_here',
    'public_key_here'
);

-- Test vault entry
INSERT OR IGNORE INTO vault_entries (user_id, iv, ciphertext, tag, metadata)
VALUES (
    'test-user-001',
    'base64_iv_here',
    'base64_ciphertext_here', 
    'base64_tag_here',
    '{"type": "password", "name": "Gmail", "username": "test@gmail.com", "url": "https://gmail.com"}'
);
*/

-- ============================================
-- DATABASE INFO
-- ============================================
-- Query to check database info:
-- SELECT name, sql FROM sqlite_master WHERE type='table';
-- SELECT * FROM user_stats;
-- SELECT * FROM recent_activity LIMIT 10;

PRAGMA user_version = 1; -- Database schema version