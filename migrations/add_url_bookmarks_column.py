#!/usr/bin/env python3
"""
Migration script to add url_bookmarks column to Note table
"""

import sqlite3
import json
import logging
from urllib.parse import urlparse

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_database(db_path):
    """Add url_bookmarks column and migrate existing urls data"""
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check if url_bookmarks column exists
        cursor.execute("PRAGMA table_info(Note)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'url_bookmarks' in columns:
            logger.info("url_bookmarks column already exists")
            return
        
        # Add url_bookmarks column
        cursor.execute("ALTER TABLE Note ADD COLUMN url_bookmarks TEXT DEFAULT '[]'")
        logger.info("Added url_bookmarks column to Note table")
        
        # Migrate existing urls data if urls column exists
        if 'urls' in columns:
            cursor.execute("SELECT id, urls FROM Note WHERE urls IS NOT NULL AND urls != '[]'")
            notes_with_urls = cursor.fetchall()
            
            migrated_count = 0
            for note in notes_with_urls:
                try:
                    old_urls = json.loads(note['urls']) if note['urls'] else []
                    # Convert simple URL strings to the new format with friendly names
                    new_bookmarks = []
                    for url in old_urls:
                        if isinstance(url, str):
                            # Extract domain name as friendly name
                            parsed = urlparse(url)
                            friendly_name = parsed.netloc or url
                            new_bookmarks.append({
                                'url': url,
                                'friendly_name': friendly_name
                            })
                        elif isinstance(url, dict) and 'url' in url:
                            # Already in the correct format
                            new_bookmarks.append({
                                'url': url['url'],
                                'friendly_name': url.get('friendly_name', url['url'])
                            })
                    
                    # Update the note with the new format
                    cursor.execute(
                        "UPDATE Note SET url_bookmarks = ? WHERE id = ?",
                        (json.dumps(new_bookmarks), note['id'])
                    )
                    migrated_count += 1
                except (json.JSONDecodeError, Exception) as e:
                    logger.warning(f"Error migrating URLs for note {note['id']}: {e}")
            
            conn.commit()
            logger.info(f"Migrated URLs to url_bookmarks format for {migrated_count} notes")
        
        conn.close()
        logger.info("Migration completed successfully")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise

if __name__ == "__main__":
    # Migrate both databases
    databases = [
        "data/app.db",
        "data/template.db"
    ]
    
    for db_path in databases:
        try:
            logger.info(f"Migrating database: {db_path}")
            migrate_database(db_path)
        except Exception as e:
            logger.error(f"Failed to migrate {db_path}: {e}")
