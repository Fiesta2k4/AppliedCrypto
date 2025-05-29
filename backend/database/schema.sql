-- Personal Vault Database Schema
-- SQLite Database for Personal Password Manager
-- Created: 2025

-- Enable foreign key constraints
PRAGMA foreign_keys = ON;
PRAGMA user_version = 1; -- Database schema version

-- ============================================
-- USERS TABLE
-- ============================================
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

-- ============================================
-- VAULT ENTRIES TABLE
-- ============================================
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

-- ============================================
-- BACKUPS TABLE
-- ============================================
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
);

-- ============================================
-- SHARES TABLE  
-- ============================================
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

-- ============================================
-- SESSION LOGS TABLE
-- ============================================
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
);

-- ============================================
-- INDEXES FOR PERFORMANCE
-- ============================================

-- Users indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active);
CREATE INDEX IF NOT EXISTS idx_users_created ON users(created_at);

-- Vault entries indexes
CREATE INDEX IF NOT EXISTS idx_vault_user_id ON vault_entries(user_id);
CREATE INDEX IF NOT EXISTS idx_vault_created ON vault_entries(created_at);
CREATE INDEX IF NOT EXISTS idx_vault_metadata ON vault_entries(json_extract(metadata, '$.type'));

-- Backups indexes
CREATE INDEX IF NOT EXISTS idx_backups_user_id ON backups(user_id);
CREATE INDEX IF NOT EXISTS idx_backups_status ON backups(status);
CREATE INDEX IF NOT EXISTS idx_backups_created ON backups(created_at);

-- Shares indexes
CREATE INDEX IF NOT EXISTS idx_shares_sender ON shares(sender_id);
CREATE INDEX IF NOT EXISTS idx_shares_recipient ON shares(recipient_id);
CREATE INDEX IF NOT EXISTS idx_shares_status ON shares(status);
CREATE INDEX IF NOT EXISTS idx_shares_created ON shares(created_at);

-- Session logs indexes
CREATE INDEX IF NOT EXISTS idx_session_logs_user ON session_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_session_logs_action ON session_logs(action);
CREATE INDEX IF NOT EXISTS idx_session_logs_created ON session_logs(created_at);

-- ============================================
-- TRIGGERS FOR AUTO-UPDATE TIMESTAMPS
-- ============================================

-- Users update trigger
CREATE TRIGGER IF NOT EXISTS update_users_timestamp 
    AFTER UPDATE ON users
    FOR EACH ROW
BEGIN
    UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Vault entries update trigger
CREATE TRIGGER IF NOT EXISTS update_vault_entries_timestamp 
    AFTER UPDATE ON vault_entries
    FOR EACH ROW
BEGIN
    UPDATE vault_entries SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Backups update trigger
CREATE TRIGGER IF NOT EXISTS update_backups_timestamp 
    AFTER UPDATE ON backups
    FOR EACH ROW
BEGIN
    UPDATE backups SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Shares update trigger
CREATE TRIGGER IF NOT EXISTS update_shares_timestamp 
    AFTER UPDATE ON shares
    FOR EACH ROW
BEGIN
    UPDATE shares SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;