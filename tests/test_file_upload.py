#!/usr/bin/env python3
"""
Test script for file upload functionality
Tests the new file upload system that replaced Immich integration
"""

import os
import sqlite3
import requests
import tempfile
from pathlib import Path

def test_file_upload():
    """Test file upload functionality through the API"""
    
    # Test configuration
    base_url = "http://localhost:5002"
    entry_id = 1  # Test with existing entry
    
    # Create test files of different types
    test_files = {}
    
    # Create a temporary directory for test files
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create a test image file
        image_file = temp_path / "test_image.png"
        with open(image_file, 'wb') as f:
            # Create a minimal PNG header for testing
            f.write(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x00\x00\x00\x01\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00IEND\xaeB`\x82')
        test_files['image'] = image_file
        
        # Create a test PDF file
        pdf_file = temp_path / "test_document.pdf"
        with open(pdf_file, 'wb') as f:
            # Create a minimal PDF for testing
            f.write(b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000010 00000 n \n0000000053 00000 n \n0000000125 00000 n \ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n174\n%%EOF')
        test_files['pdf'] = pdf_file
        
        # Create a test text file
        txt_file = temp_path / "test_notes.txt"
        with open(txt_file, 'w') as f:
            f.write("This is a test text file for the file upload functionality.")
        test_files['text'] = txt_file
        
        print("Testing file upload functionality...")
        print("=" * 50)
        
        # Test 1: Single file upload with note
        print("\n1. Testing single file upload with note...")
        try:
            with open(test_files['image'], 'rb') as f:
                files = {'files': (image_file.name, f, 'image/png')}
                data = {
                    'note_text': 'Test note with image attachment',
                    'reminder_date': '',
                    'reminder_time': ''
                }
                response = requests.post(f"{base_url}/api/entries/{entry_id}/notes", files=files, data=data)
                
            if response.status_code == 201:
                print("✅ Single file upload successful")
                result = response.json()
                print(f"   Note ID: {result.get('note_id')}")
                if 'file_paths' in result and result['file_paths']:
                    print(f"   File saved: {result['file_paths'][0]}")
                else:
                    print("   Warning: No file paths returned")
            else:
                print(f"❌ Single file upload failed: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Error during single file upload: {e}")
        
        # Test 2: Multiple file upload
        print("\n2. Testing multiple file upload...")
        try:
            files = []
            with open(test_files['pdf'], 'rb') as f1, open(test_files['text'], 'rb') as f2:
                files = [
                    ('files', (pdf_file.name, f1, 'application/pdf')),
                    ('files', (txt_file.name, f2, 'text/plain'))
                ]
                data = {
                    'note_text': 'Test note with multiple attachments',
                    'reminder_date': '',
                    'reminder_time': ''
                }
                response = requests.post(f"{base_url}/api/entries/{entry_id}/notes", files=files, data=data)
                
            if response.status_code == 201:
                print("✅ Multiple file upload successful")
                result = response.json()
                print(f"   Note ID: {result.get('note_id')}")
                if 'file_paths' in result and result['file_paths']:
                    print(f"   Files saved: {len(result['file_paths'])} files")
                    for path in result['file_paths']:
                        print(f"     - {path}")
                else:
                    print("   Warning: No file paths returned")
            else:
                print(f"❌ Multiple file upload failed: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Error during multiple file upload: {e}")
        
    # Test 3: Check database schema
    print("\n3. Checking database schema...")
    try:
        db_path = "/home/an0naman/Documents/GitHub/template/template.db"
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check if file_paths column exists
            cursor.execute("PRAGMA table_info(Note)")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]
            
            if 'file_paths' in column_names:
                print("✅ Database schema updated correctly")
                print(f"   Available columns: {', '.join(column_names)}")
                
                # Check for any notes with file attachments
                cursor.execute("SELECT id, note_text, file_paths FROM Note WHERE file_paths IS NOT NULL AND file_paths != ''")
                notes_with_files = cursor.fetchall()
                
                if notes_with_files:
                    print(f"   Found {len(notes_with_files)} notes with file attachments:")
                    for note_id, text, files in notes_with_files:
                        print(f"     - Note {note_id}: '{text[:50]}...' ({len(files.split(',') if files else [])} files)")
                else:
                    print("   No notes with file attachments found yet")
                    
            else:
                print("❌ Database schema not updated - file_paths column missing")
                
            conn.close()
        else:
            print(f"❌ Database not found at {db_path}")
            
    except Exception as e:
        print(f"❌ Error checking database: {e}")
    
    # Test 4: Check file storage directory
    print("\n4. Checking file storage...")
    try:
        upload_dir = "/home/an0naman/Documents/GitHub/template/app/static/uploads"
        if os.path.exists(upload_dir):
            files = list(Path(upload_dir).glob("*"))
            print(f"✅ Upload directory exists: {upload_dir}")
            print(f"   Files in directory: {len(files)}")
            for file_path in files[:5]:  # Show first 5 files
                print(f"     - {file_path.name} ({file_path.stat().st_size} bytes)")
            if len(files) > 5:
                print(f"     ... and {len(files) - 5} more files")
        else:
            print(f"❌ Upload directory not found: {upload_dir}")
            
    except Exception as e:
        print(f"❌ Error checking upload directory: {e}")
    
    print("\n" + "=" * 50)
    print("File upload functionality test completed!")
    
    # Test 5: Get notes to verify files are associated
    print("\n5. Verifying notes retrieval with files...")
    try:
        response = requests.get(f"{base_url}/api/entries/{entry_id}/notes")
        if response.status_code == 200:
            notes = response.json()
            print(f"✅ Retrieved {len(notes)} notes for entry {entry_id}")
            
            notes_with_files = [note for note in notes if note.get('file_paths')]
            if notes_with_files:
                print(f"   {len(notes_with_files)} notes have file attachments:")
                for note in notes_with_files:
                    file_paths = note['file_paths']
                    if isinstance(file_paths, str):
                        files = file_paths.split(',') if file_paths else []
                    else:
                        files = file_paths if file_paths else []
                    print(f"     - Note {note['id']}: {len(files)} files")
                    for file_path in files:
                        print(f"       * {file_path}")
            else:
                print("   No notes with file attachments found")
        else:
            print(f"❌ Failed to retrieve notes: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error retrieving notes: {e}")

if __name__ == "__main__":
    test_file_upload()
