#!/usr/bin/env python3
"""
Migration script to add Hugging Face parameters to existing database
Run this if you already have a database and want to add Hugging Face support
"""
import pymysql
import os
import sys

# Get database path from environment or use default
db_path = os.getenv('DATABASE_PATH', 'data/template.db')

if not os.path.exists(db_path):
    print(f"❌ Database not found at: {db_path}")
    sys.exit(1)

print(f"📦 Migrating database: {db_path}")

# Parameters to add
parameters = {
    'huggingface_api_key': '',
    'huggingface_model': 'stabilityai/stable-diffusion-xl-base-1.0',
    'huggingface_image_size': '1024x576',
    'groq_api_key': ''  # Also add this if missing
}

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    added_count = 0
    
    for param_name, param_value in parameters.items():
        # Check if parameter exists
        cursor.execute(
            "SELECT parameter_value FROM SystemParameters WHERE parameter_name = ?",
            (param_name,)
        )
        result = cursor.fetchone()
        
        if result is None:
            # Parameter doesn't exist, add it
            cursor.execute(
                "INSERT INTO SystemParameters (parameter_name, parameter_value) VALUES (?, ?)",
                (param_name, param_value)
            )
            print(f"✅ Added parameter: {param_name} = '{param_value}'")
            added_count += 1
        else:
            print(f"ℹ️  Parameter already exists: {param_name} = '{result[0]}'")
    
    conn.commit()
    conn.close()
    
    if added_count > 0:
        print(f"\n🎉 Migration complete! Added {added_count} parameter(s)")
        print("📝 You can now save Hugging Face settings in the Settings page")
    else:
        print("\n✨ All parameters already exist - no migration needed")
        
except pymysql.Error as e:
    print(f"❌ Database error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    sys.exit(1)
