#!/usr/bin/env python3
"""
Migration script to add Gemini API key parameter to SystemParameters table
"""

import os
import pymysql

def migrate_gemini_api_key():
    """Add Gemini API key parameter to SystemParameters table"""
    
    # Database paths to check
    db_paths = [
        'template.db',
        'data/template.db',
        'app.db',
        'data/app.db'
    ]
    
    # Find the database file
    db_path = None
    for path in db_paths:
        if os.path.exists(path):
            db_path = path
            break
    
    if not db_path:
        print("❌ No database file found! Please ensure template.db or app.db exists.")
        return False
    
    print(f"📁 Using database: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if SystemParameters table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='SystemParameters'
        """)
        
        if not cursor.fetchone():
            print("❌ SystemParameters table not found! Please ensure the database is properly initialized.")
            return False
        
        # Check if gemini parameters already exist
        cursor.execute("""
            SELECT COUNT(*) FROM SystemParameters 
            WHERE parameter_name IN ('gemini_api_key', 'gemini_model_name', 'gemini_base_prompt')
        """)
        
        existing_count = cursor.fetchone()[0]
        
        if existing_count >= 3:
            print("ℹ️  All Gemini AI parameters already exist")
        else:
            print(f"ℹ️  Found {existing_count}/3 Gemini parameters, adding missing ones...")
        
        # Insert or update gemini parameters with defaults
        gemini_settings = [
            ('gemini_api_key', ''),
            ('gemini_model_name', 'gemini-1.5-flash'),
            ('gemini_base_prompt', 'You are a helpful assistant for a project management application. Please provide clear, concise, and well-structured responses.')
        ]
        
        for param_name, param_value in gemini_settings:
            cursor.execute("""
                INSERT OR IGNORE INTO SystemParameters (parameter_name, parameter_value)
                VALUES (?, ?)
            """, (param_name, param_value))
        
        conn.commit()
        print("✅ Added/verified Gemini AI parameters")
        
        # Show summary
        cursor.execute("""
            SELECT parameter_name, parameter_value FROM SystemParameters 
            WHERE parameter_name IN ('gemini_api_key', 'gemini_model_name', 'gemini_base_prompt')
            ORDER BY parameter_name
        """)
        
        settings = cursor.fetchall()
        
        print("\n✅ Gemini AI parameters migration completed!")
        print("\n📋 AI Configuration Status:")
        
        api_key_value = None
        model_name_value = None
        base_prompt_value = None
        
        for param_name, param_value in settings:
            if param_name == 'gemini_api_key':
                api_key_value = param_value
                if param_value:
                    masked_value = param_value[:8] + "..." + param_value[-4:] if len(param_value) > 12 else "***"
                    print(f"   • API Key: {masked_value}")
                else:
                    print("   • API Key: (not set)")
            elif param_name == 'gemini_model_name':
                model_name_value = param_value
                print(f"   • Model: {param_value}")
            elif param_name == 'gemini_base_prompt':
                base_prompt_value = param_value
                preview = param_value[:50] + "..." if len(param_value) > 50 else param_value
                print(f"   • Base Prompt: {preview}")
        
        if api_key_value:
            print("   • Status: ✅ Configured")
        else:
            print("   • Status: ⚠️  Not configured")
        
        print("\n🔧 Next Steps:")
        if not api_key_value:
            print("   1. Get your API key from https://makersuite.google.com/app/apikey")
            print("   2. Add it through the web interface:")
            print("      - Go to Settings → System Parameters")
            print("      - Find 'Google Gemini API Key' field")
            print("      - Paste your API key and save")
            print("   3. Or update via API:")
            print('      curl -X POST http://localhost:5001/api/system_params \\')
            print('           -H "Content-Type: application/json" \\')
            print('           -d \'{"gemini_api_key": "your-api-key-here"}\'')
        else:
            print("   • AI features are ready to use!")
            print("   • Available in Entry descriptions and SQL IDE")
            print(f"   • Using model: {model_name_value}")
            print("   • You can change settings in Settings → AI Integration")
            print("   • Customize the base prompt to fit your specific use case")
        
        return True
        
    except pymysql.Error as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("🤖 Gemini API Key Migration")
    print("=" * 30)
    migrate_gemini_api_key()
