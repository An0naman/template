"""
Git Integration Migration
Adds tables for Git repositories, commits, and branches
"""
import sqlite3
import os
import sys
from datetime import datetime

# Add parent directory to path to import db module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def get_db():
    """Get database connection"""
    # Use the same path as app/config.py
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'template.db')
    if not os.path.exists(db_path):
        raise Exception(f"Database not found at {db_path}")
    return sqlite3.connect(db_path)

def migrate():
    """Add Git integration tables"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Git Repositories table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS GitRepository (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                url TEXT NOT NULL,
                local_path TEXT,
                default_branch TEXT DEFAULT 'main',
                credentials_encrypted TEXT,
                last_synced TIMESTAMP,
                entry_type_id INTEGER,
                auto_sync BOOLEAN DEFAULT 0,
                auto_create_entries BOOLEAN DEFAULT 0,
                sync_interval INTEGER DEFAULT 15,
                commit_types TEXT DEFAULT 'feat,fix,docs,refactor',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (entry_type_id) REFERENCES EntryType(id) ON DELETE SET NULL
            )
        ''')
        print("✓ Created GitRepository table")
        
        # Git Commits table (linked to entries)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS GitCommit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                repository_id INTEGER NOT NULL,
                commit_hash TEXT NOT NULL UNIQUE,
                author TEXT,
                author_email TEXT,
                message TEXT,
                message_body TEXT,
                commit_date TIMESTAMP,
                branch TEXT,
                files_changed INTEGER DEFAULT 0,
                insertions INTEGER DEFAULT 0,
                deletions INTEGER DEFAULT 0,
                entry_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (repository_id) REFERENCES GitRepository(id) ON DELETE CASCADE,
                FOREIGN KEY (entry_id) REFERENCES Entry(id) ON DELETE SET NULL
            )
        ''')
        print("✓ Created GitCommit table")
        
        # Git Branches table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS GitBranch (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                repository_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                is_default BOOLEAN DEFAULT 0,
                last_commit_hash TEXT,
                last_commit_date TIMESTAMP,
                entry_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (repository_id) REFERENCES GitRepository(id) ON DELETE CASCADE,
                FOREIGN KEY (entry_id) REFERENCES Entry(id) ON DELETE SET NULL,
                UNIQUE(repository_id, name)
            )
        ''')
        print("✓ Created GitBranch table")
        
        # Create indexes for better performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_git_commit_repo ON GitCommit(repository_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_git_commit_hash ON GitCommit(commit_hash)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_git_commit_entry ON GitCommit(entry_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_git_branch_repo ON GitBranch(repository_id)')
        print("✓ Created indexes")
        
        # Add system parameters for Git integration
        cursor.execute('''
            INSERT OR IGNORE INTO SystemParameters (parameter_name, parameter_value)
            VALUES 
                ('git_integration_enabled', '0'),
                ('git_provider', ''), 
                ('git_token', ''), 
                ('gitlab_url', 'https://gitlab.com')
        ''')
        print("✓ Added Git system parameters")
        
        conn.commit()
        print("\n✅ Git integration migration completed successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Migration failed: {e}")
        raise
    finally:
        conn.close()

def rollback():
    """Remove Git integration tables"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute('DROP TABLE IF EXISTS GitCommit')
        cursor.execute('DROP TABLE IF EXISTS GitBranch')
        cursor.execute('DROP TABLE IF EXISTS GitRepository')
        conn.commit()
        print("✅ Git integration tables removed successfully!")
    except Exception as e:
        conn.rollback()
        print(f"❌ Rollback failed: {e}")
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'rollback':
        rollback()
    else:
        migrate()
