# template_app/app/api/notes_api.py
from flask import Blueprint, request, jsonify, g, current_app
import sqlite3
from datetime import datetime
import json
import logging
import os
from werkzeug.utils import secure_filename
from ..serializers import serialize_note # Import the serializer
from ..db import get_system_parameters # Import system parameters

def get_allowed_file_types():
    """Get allowed file types from system parameters"""
    try:
        params = get_system_parameters()
        allowed_types_str = params.get('allowed_file_types', 
            'txt,pdf,png,jpg,jpeg,gif,webp,svg,doc,docx,xls,xlsx,ppt,pptx,mp4,avi,mov,wmv,flv,webm,mkv,mp3,wav,flac,aac,ogg,zip,rar,7z,tar,gz')
        return set(ext.strip().lower() for ext in allowed_types_str.split(',') if ext.strip())
    except Exception as e:
        logger.error(f"Error getting allowed file types from system parameters: {e}")
        # Return default set if there's an error
        return {
            'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg',
            'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'mp4', 'avi', 
            'mov', 'wmv', 'flv', 'webm', 'mkv', 'mp3', 'wav', 'flac', 
            'aac', 'ogg', 'zip', 'rar', '7z', 'tar', 'gz'
        }

def serialize_note_with_reminder(note):
    """Helper to serialize note rows with reminder notification info."""
    if note is None:
        return None
    
    base_note = {
        "id": note['id'],
        "entry_id": note['entry_id'],
        "note_title": note['note_title'],
        "note_text": note['note_text'],
        "note_type": note['type'],
        "created_at": note['created_at'],
        "file_paths": note['file_paths'].split(',') if note['file_paths'] else []
    }
    
    # Add reminder information if present
    if note['notification_id']:
        base_note['reminder'] = {
            "notification_id": note['notification_id'],
            "scheduled_for": note['scheduled_for'],
            "is_read": bool(note['is_read']),
            "is_dismissed": bool(note['is_dismissed']),
            "title": note['notification_title']
        }
    else:
        base_note['reminder'] = None
    
    return base_note

def serialize_note_with_reminder_and_entry_info(note):
    """Helper to serialize note rows with reminder notification info and entry relationship details."""
    if note is None:
        return None
    
    # Parse associated_entry_ids as JSON
    try:
        associated_entry_ids = json.loads(note['associated_entry_ids']) if note['associated_entry_ids'] else []
    except (json.JSONDecodeError, TypeError):
        associated_entry_ids = []
    
    base_note = {
        "id": note['id'],
        "entry_id": note['entry_id'],
        "note_title": note['note_title'],
        "note_text": note['note_text'],
        "note_type": note['type'],
        "created_at": note['created_at'],
        "file_paths": note['file_paths'].split(',') if note['file_paths'] else [],
        "associated_entry_ids": associated_entry_ids,
        "relationship_type": note['relationship_type']  # 'primary' or 'associated'
    }
    
    # Add primary entry information (the entry this note belongs to)
    if note['primary_entry_title'] and note['primary_entry_type']:
        base_note['primary_entry_display'] = f"{note['primary_entry_title']} - {note['primary_entry_type']}"
    else:
        base_note['primary_entry_display'] = "Unknown Entry"
    
    # Add reminder information if present
    if note['notification_id']:
        base_note['reminder'] = {
            "notification_id": note['notification_id'],
            "scheduled_for": note['scheduled_for'],
            "is_read": bool(note['is_read']),
            "is_dismissed": bool(note['is_dismissed']),
            "title": note['notification_title']
        }
    else:
        base_note['reminder'] = None
    
    return base_note

# Define a Blueprint for Notes API
notes_api_bp = Blueprint('notes_api', __name__)

# Get a logger for this module
logger = logging.getLogger(__name__)

def get_db():
    if 'db' not in g:
        db_path = current_app.config['DATABASE_PATH']
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row
    return g.db

# Define allowed file extensions from system parameters
def allowed_file(filename):
    """Check if file extension is allowed based on system parameters"""
    if not filename or '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    allowed_extensions = get_allowed_file_types()
    return ext in allowed_extensions

def save_uploaded_file(file, note_id):
    """Save uploaded file and return the saved filename."""
    if file.filename == '':
        return None
    
    if file and allowed_file(file.filename):
        # Create secure filename with note_id prefix
        original_filename = secure_filename(file.filename)
        filename = f"note_{note_id}_{original_filename}"
        
        # Ensure uploads directory exists
        upload_dir = os.path.join(current_app.static_folder, 'uploads')
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)
        
        file_path = os.path.join(upload_dir, filename)
        file.save(file_path)
        
        return filename
    
    return None

# Import notification creation function
try:
    from .notifications_api import create_note_notification
except ImportError:
    logger.warning("Could not import create_note_notification function")
    create_note_notification = None

@notes_api_bp.route('/entries/<int:entry_id>/notes', methods=['POST'])
def add_note_to_entry(entry_id):
    # Handle both JSON and form data
    if request.content_type and 'application/json' in request.content_type:
        # Legacy JSON support
        data = request.json
        note_title = data.get('note_title')
        note_text = data.get('note_text')
        note_type = data.get('note_type', 'General')
        reminder_date = data.get('reminder_date')
        associated_entry_ids = data.get('associated_entry_ids', [])
        files = []
    else:
        # Form data with file uploads
        note_title = request.form.get('note_title')
        note_text = request.form.get('note_text')
        note_type = request.form.get('note_type', 'General')
        reminder_date = request.form.get('reminder_date')
        # Handle associated_entry_ids from form data (could be JSON string or comma-separated)
        associated_entry_ids_raw = request.form.get('associated_entry_ids', '[]')
        try:
            if associated_entry_ids_raw.startswith('['):
                # JSON array format
                associated_entry_ids = json.loads(associated_entry_ids_raw)
            else:
                # Comma-separated format
                associated_entry_ids = [int(x.strip()) for x in associated_entry_ids_raw.split(',') if x.strip()]
        except (json.JSONDecodeError, ValueError):
            associated_entry_ids = []
        files = request.files.getlist('files')

    if not note_text:
        return jsonify({'message': 'Note content cannot be empty!'}), 400

    # Validate associated_entry_ids are integers
    if not isinstance(associated_entry_ids, list):
        associated_entry_ids = []
    
    # Convert to JSON string for storage
    associated_entry_ids_json = json.dumps(associated_entry_ids)

    conn = get_db()
    cursor = conn.cursor()
    try:
        # First create the note with associated entry IDs
        cursor.execute(
            "INSERT INTO Note (entry_id, note_title, note_text, type, created_at, file_paths, associated_entry_ids) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (entry_id, note_title, note_text, note_type, datetime.now().isoformat(), '', associated_entry_ids_json)
        )
        conn.commit()
        note_id = cursor.lastrowid
        
        # Handle file uploads
        file_paths = []
        if files:
            for file in files:
                if file and file.filename:
                    saved_filename = save_uploaded_file(file, note_id)
                    if saved_filename:
                        file_paths.append(saved_filename)
                        logger.info(f"Saved file {saved_filename} for note {note_id}")
            
            # Update note with file paths
            if file_paths:
                cursor.execute(
                    "UPDATE Note SET file_paths = ? WHERE id = ?",
                    (','.join(file_paths), note_id)
                )
                conn.commit()
        
        # Create notification if reminder_date is provided
        if reminder_date and create_note_notification:
            try:
                notification_title = f"Reminder: {note_title or 'Note'}"
                notification_message = f"Reminder for note: {note_text[:100]}{'...' if len(note_text) > 100 else ''}"
                
                create_note_notification(
                    note_id=note_id,
                    entry_id=entry_id,
                    scheduled_for=reminder_date,
                    title=notification_title,
                    message=notification_message
                )
                logger.info(f"Created notification for note {note_id} scheduled for {reminder_date}")
            except Exception as e:
                logger.warning(f"Error creating note notification: {e}")
                # Don't fail note creation if notification creation fails
        
        return jsonify({
            'message': 'Note added successfully!', 
            'note_id': note_id,
            'file_paths': file_paths,
            'files_uploaded': len(file_paths)
        }), 201
        
    except sqlite3.IntegrityError:
        conn.rollback()
        return jsonify({'message': 'Entry not found for adding note.'}), 404
    except Exception as e:
        logger.error(f"Error adding note to entry {entry_id}: {e}", exc_info=True)
        conn.rollback()
        return jsonify({'message': 'An internal error occurred.'}), 500

@notes_api_bp.route('/entries/<int:entry_id>/notes', methods=['GET'])
def get_notes_for_entry(entry_id):
    conn = get_db()
    cursor = conn.cursor()
    
    logger.info(f"Getting notes for entry_id: {entry_id}")
    
    # Get notes where this entry is either the primary entry_id OR appears in associated_entry_ids
    # Include entry information for proper display of associated notes
    cursor.execute("""
        SELECT DISTINCT n.id, n.entry_id, n.note_title, n.note_text, n.type, n.created_at, n.file_paths, n.associated_entry_ids,
               nt.id as notification_id, nt.scheduled_for, nt.is_read, nt.is_dismissed, nt.title as notification_title,
               e.title as primary_entry_title, et.singular_label as primary_entry_type,
               CASE 
                   WHEN n.entry_id = ? THEN 'primary'
                   ELSE 'associated'
               END as relationship_type
        FROM Note n
        LEFT JOIN Notification nt ON n.id = nt.note_id AND nt.notification_type = 'note_based'
        LEFT JOIN Entry e ON n.entry_id = e.id
        LEFT JOIN EntryType et ON e.entry_type_id = et.id
        WHERE n.entry_id = ? 
           OR (n.associated_entry_ids != '[]' AND (
               n.associated_entry_ids LIKE '[' || ? || ']' OR              -- Single entry: [123]
               n.associated_entry_ids LIKE '[' || ? || ',%' OR             -- First in list: [123,...]
               n.associated_entry_ids LIKE '%,' || ? || ',%' OR            -- Middle of list: [...,123,...]
               n.associated_entry_ids LIKE '%,' || ? || ']' OR             -- Last in list: [...,123]
               n.associated_entry_ids LIKE '[' || ? || ' %' OR             -- First with space: [123 ...]
               n.associated_entry_ids LIKE '%, ' || ? || ',%' OR           -- Middle with space: [..., 123,...]
               n.associated_entry_ids LIKE '%, ' || ? || ']'               -- Last with space: [..., 123]
           ))
        ORDER BY n.created_at DESC
    """, (entry_id, entry_id, entry_id, entry_id, entry_id, entry_id, entry_id, entry_id, entry_id))
    
    notes = cursor.fetchall()
    logger.info(f"Found {len(notes)} raw notes from database")
    
    # Log first note details for debugging
    if notes:
        logger.info(f"First note raw data: {dict(notes[0])}")
    
    serialized_notes = [serialize_note_with_reminder_and_entry_info(note) for note in notes]
    logger.info(f"Serialized {len(serialized_notes)} notes")
    
    if serialized_notes:
        logger.info(f"First serialized note: {serialized_notes[0]}")
    
    return jsonify(serialized_notes)

@notes_api_bp.route('/notes/<int:note_id>', methods=['DELETE'])
def delete_note(note_id):
    conn = get_db()
    cursor = conn.cursor()
    try:
        # Get note and its file paths before deletion
        cursor.execute("SELECT file_paths FROM Note WHERE id = ?", (note_id,))
        note = cursor.fetchone()
        
        if not note:
            return jsonify({'error': 'Note not found.'}), 404
        
        # Delete associated files from filesystem
        if note['file_paths']:
            file_paths = note['file_paths'].split(',')
            for file_path in file_paths:
                full_path = os.path.join(current_app.static_folder, file_path)
                if os.path.exists(full_path):
                    os.remove(full_path)
                    logger.info(f"Deleted file: {full_path}")
        
        # Delete the note from database
        cursor.execute("DELETE FROM Note WHERE id = ?", (note_id,))
        conn.commit()
        
        return jsonify({'message': 'Note and associated files deleted successfully!'}), 200
        
    except Exception as e:
        logger.error(f"Error deleting note {note_id}: {e}", exc_info=True)
        conn.rollback()
        return jsonify({'error': 'An internal error occurred.'}), 500

@notes_api_bp.route('/notes/<int:note_id>/reminder', methods=['PUT'])
def update_note_reminder(note_id):
    data = request.json
    scheduled_for = data.get('scheduled_for')
    
    if not scheduled_for:
        return jsonify({'error': 'scheduled_for is required'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    try:
        # First verify the note exists
        cursor.execute("SELECT entry_id, note_title, note_text FROM Note WHERE id = ?", (note_id,))
        note = cursor.fetchone()
        if not note:
            return jsonify({'error': 'Note not found'}), 404
        
        # Check if a notification already exists for this note
        cursor.execute("SELECT id FROM Notification WHERE note_id = ? AND notification_type = 'note_based'", (note_id,))
        existing_notification = cursor.fetchone()
        
        if existing_notification:
            # Update existing notification
            cursor.execute("""
                UPDATE Notification 
                SET scheduled_for = ?, is_read = 0, is_dismissed = 0, updated_at = ?
                WHERE id = ?
            """, (scheduled_for, datetime.now().isoformat(), existing_notification['id']))
            logger.info(f"Updated reminder for note {note_id} to {scheduled_for}")
        else:
            # Create new notification
            notification_title = f"Reminder: {note['note_title'] or 'Note'}"
            notification_message = f"Reminder for note: {note['note_text'][:100]}{'...' if len(note['note_text']) > 100 else ''}"
            
            cursor.execute("""
                INSERT INTO Notification (notification_type, entry_id, note_id, scheduled_for, title, message, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, ('note_based', note['entry_id'], note_id, scheduled_for, notification_title, notification_message, datetime.now().isoformat()))
            
            notification_id = cursor.lastrowid
            logger.info(f"Created new reminder for note {note_id} scheduled for {scheduled_for}")
            
            # Send ntfy notification if scheduled for now or past
            try:
                from app.services.ntfy_service import send_app_notification_via_ntfy
                from datetime import datetime
                scheduled_datetime = datetime.fromisoformat(scheduled_for.replace('Z', '+00:00'))
                current_datetime = datetime.now()
                
                # If scheduled for now or in the past, send immediately
                if scheduled_datetime <= current_datetime:
                    notification_data = {
                        'title': notification_title,
                        'message': notification_message,
                        'type': 'note_based',
                        'priority': 'medium',
                        'entry_id': note['entry_id'],
                        'notification_id': notification_id
                    }
                    send_app_notification_via_ntfy(notification_data)
            except Exception as e:
                logger.error(f"Failed to send ntfy notification for note {note_id}: {e}")
        
        conn.commit()
        return jsonify({'message': 'Reminder updated successfully'}), 200
        
    except Exception as e:
        logger.error(f"Error updating reminder for note {note_id}: {e}", exc_info=True)
        conn.rollback()
        return jsonify({'error': 'An internal error occurred'}), 500

@notes_api_bp.route('/notes/<int:note_id>/reminder', methods=['DELETE'])
def delete_note_reminder(note_id):
    conn = get_db()
    cursor = conn.cursor()
    try:
        # Delete the notification for this note
        cursor.execute("DELETE FROM Notification WHERE note_id = ? AND notification_type = 'note_based'", (note_id,))
        conn.commit()
        
        if cursor.rowcount == 0:
            return jsonify({'error': 'No reminder found for this note'}), 404
        
        logger.info(f"Deleted reminder for note {note_id}")
        return jsonify({'message': 'Reminder deleted successfully'}), 200
        
    except Exception as e:
        logger.error(f"Error deleting reminder for note {note_id}: {e}", exc_info=True)
        conn.rollback()
        return jsonify({'error': 'An internal error occurred'}), 500

@notes_api_bp.route('/notes/<int:note_id>', methods=['PUT'])
def update_note_content(note_id):
    """Update note title and content"""
    conn = get_db()
    cursor = conn.cursor()
    try:
        note_title = request.form.get('note_title', '').strip()
        note_text = request.form.get('note_text', '').strip()
        
        # Handle associated_entry_ids from form data (could be JSON string or comma-separated)
        associated_entry_ids_raw = request.form.get('associated_entry_ids', None)
        associated_entry_ids_json = None
        
        if associated_entry_ids_raw is not None:
            try:
                if associated_entry_ids_raw.startswith('['):
                    # JSON array format
                    associated_entry_ids = json.loads(associated_entry_ids_raw)
                else:
                    # Comma-separated format
                    associated_entry_ids = [int(x.strip()) for x in associated_entry_ids_raw.split(',') if x.strip()]
                # Convert to JSON string for storage
                associated_entry_ids_json = json.dumps(associated_entry_ids)
            except (json.JSONDecodeError, ValueError):
                associated_entry_ids_json = '[]'
        
        if not note_text:
            return jsonify({'error': 'Note text is required'}), 400
        
        # Build the update query based on what fields are provided
        if associated_entry_ids_json is not None:
            cursor.execute("""
                UPDATE Note 
                SET note_title = ?, note_text = ?, associated_entry_ids = ?
                WHERE id = ?
            """, (note_title, note_text, associated_entry_ids_json, note_id))
        else:
            cursor.execute("""
                UPDATE Note 
                SET note_title = ?, note_text = ? 
                WHERE id = ?
            """, (note_title, note_text, note_id))
        
        conn.commit()
        
        if cursor.rowcount == 0:
            return jsonify({'error': 'Note not found'}), 404
        
        response_data = {
            'message': 'Note updated successfully',
            'note_title': note_title,
            'note_text': note_text
        }
        
        if associated_entry_ids_json is not None:
            response_data['associated_entry_ids'] = json.loads(associated_entry_ids_json)
            
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"Error updating note {note_id}: {e}", exc_info=True)
        conn.rollback()
        return jsonify({'error': 'An internal error occurred'}), 500

@notes_api_bp.route('/notes/<int:note_id>/attachments', methods=['POST'])
def add_note_attachments(note_id):
    """Add additional attachments to an existing note"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Check if note exists
        cursor.execute("SELECT file_paths FROM Note WHERE id = ?", (note_id,))
        note = cursor.fetchone()
        
        if not note:
            return jsonify({'error': 'Note not found'}), 404
            
        # Get current file paths
        current_files = note['file_paths'].split(',') if note['file_paths'] else []
        
        # Handle file uploads
        uploaded_files = request.files.getlist('files')
        if not uploaded_files or uploaded_files[0].filename == '':
            return jsonify({'error': 'No files selected'}), 400
        
        # Process uploaded files
        new_file_paths = []
        upload_folder = os.path.join(current_app.static_folder, 'uploads')
        os.makedirs(upload_folder, exist_ok=True)
        
        for file in uploaded_files:
            if file and file.filename and allowed_file(file.filename):
                # Check file size (50MB limit)
                file.seek(0, os.SEEK_END)
                file_size = file.tell()
                file.seek(0)
                
                if file_size > 50 * 1024 * 1024:  # 50MB
                    return jsonify({'error': f'File {file.filename} is too large (max 50MB)'}), 400
                
                filename = secure_filename(file.filename)
                
                # Ensure unique filename
                base_filename = filename
                counter = 1
                while os.path.exists(os.path.join(upload_folder, filename)):
                    name, ext = os.path.splitext(base_filename)
                    filename = f"{name}_{counter}{ext}"
                    counter += 1
                
                file_path = os.path.join(upload_folder, filename)
                file.save(file_path)
                new_file_paths.append(f'uploads/{filename}')
            else:
                return jsonify({'error': f'File type not allowed for {file.filename}'}), 400
        
        # Combine current and new file paths
        all_file_paths = current_files + new_file_paths
        file_paths_str = ','.join(all_file_paths)
        
        # Update note with new file paths
        cursor.execute("UPDATE Note SET file_paths = ? WHERE id = ?", (file_paths_str, note_id))
        conn.commit()
        
        return jsonify({
            'message': f'{len(new_file_paths)} files uploaded successfully',
            'file_paths': all_file_paths,
            'new_files': new_file_paths
        }), 200
        
    except Exception as e:
        logger.error(f"Error adding attachments to note {note_id}: {e}", exc_info=True)
        conn.rollback()
        return jsonify({'error': 'An internal error occurred'}), 500

@notes_api_bp.route('/notes/<int:note_id>/attachments/<int:file_index>', methods=['DELETE'])
def delete_note_attachment(note_id, file_index):
    """Delete a specific attachment from a note"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Get current note and file paths
        cursor.execute("SELECT file_paths FROM Note WHERE id = ?", (note_id,))
        note = cursor.fetchone()
        
        if not note:
            return jsonify({'error': 'Note not found'}), 404
            
        current_files = note['file_paths'].split(',') if note['file_paths'] else []
        
        if file_index < 0 or file_index >= len(current_files):
            return jsonify({'error': 'Invalid file index'}), 400
            
        # Get the file to delete
        file_to_delete = current_files[file_index]
        
        # Remove the file from filesystem
        file_path = os.path.join(current_app.static_folder, file_to_delete)
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Deleted file: {file_path}")
        
        # Remove from file list
        current_files.pop(file_index)
        new_file_paths_str = ','.join(current_files) if current_files else ''
        
        # Update note
        cursor.execute("UPDATE Note SET file_paths = ? WHERE id = ?", (new_file_paths_str, note_id))
        conn.commit()
        
        return jsonify({
            'message': 'File deleted successfully',
            'file_paths': current_files,
            'deleted_file': file_to_delete
        }), 200
        
    except Exception as e:
        logger.error(f"Error deleting attachment from note {note_id}: {e}", exc_info=True)
        conn.rollback()
        return jsonify({'error': 'An internal error occurred'}), 500