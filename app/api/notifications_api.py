# template_app/app/api/notifications_api.py
from flask import Blueprint, request, jsonify, g, current_app
import sqlite3
from datetime import datetime, timedelta
import logging
from ..utils.sensor_type_manager import ensure_sensor_type_exists
from ..services.ntfy_service import send_app_notification_via_ntfy

# Define a Blueprint for Notifications API
notifications_api_bp = Blueprint('notifications_api', __name__)

# Get a logger for this module
logger = logging.getLogger(__name__)

def get_db():
    if 'db' not in g:
        db_path = current_app.config['DATABASE_PATH']
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row
    return g.db

@notifications_api_bp.route('/notifications', methods=['GET'])
def get_notifications():
    """Get all active notifications"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Get current datetime
    now = datetime.now().isoformat()
    
    # Get optional entry_id filter
    entry_id = request.args.get('entry_id', type=int)
    
    try:
        # Build WHERE clause dynamically based on filters
        where_conditions = ["n.is_dismissed = 0"]
        params = []
        
        # Filter by entry_id if provided
        if entry_id:
            where_conditions.append("n.entry_id = ?")
            params.append(entry_id)
            
        # Show notifications that are due with improved date/time handling
        # If scheduled_for ends with T00:00, treat it as "any time on that date"
        where_conditions.append("""(n.scheduled_for IS NULL OR 
                                   n.scheduled_for <= ? OR 
                                   (n.scheduled_for LIKE '%T00:00' AND date(n.scheduled_for) = date(?)))""")
        params.append(now)
        params.append(now)  # Second parameter for the date comparison
        
        where_clause = " AND ".join(where_conditions)
        
        # Get notifications that should be shown
        cursor.execute(f'''
            SELECT 
                n.*,
                e.title as entry_title,
                note.note_title,
                et.singular_label as entry_type_label
            FROM Notification n
            LEFT JOIN Entry e ON n.entry_id = e.id
            LEFT JOIN Note note ON n.note_id = note.id
            LEFT JOIN EntryType et ON e.entry_type_id = et.id
            WHERE {where_clause}
            ORDER BY 
                CASE n.priority 
                    WHEN 'critical' THEN 1 
                    WHEN 'high' THEN 2 
                    WHEN 'medium' THEN 3 
                    WHEN 'low' THEN 4 
                    ELSE 5 
                END,
                n.created_at DESC
        ''', params)
        
        notifications = [dict(row) for row in cursor.fetchall()]
        
        # Debug logging
        logger.info(f"Fetched {len(notifications)} notifications for entry_id={entry_id}, current time={now}")
        for notif in notifications:
            scheduled = notif.get('scheduled_for')
            logger.info(f"Notification ID {notif['id']}: '{notif['title']}' - scheduled_for: {scheduled} (now: {now}, comparison: {scheduled} <= {now} = {scheduled is None or (scheduled and scheduled <= now)})")
        
        return jsonify(notifications), 200
        
    except Exception as e:
        logger.error(f"Error fetching notifications: {e}", exc_info=True)
        return jsonify({'error': 'An internal error occurred.'}), 500

@notifications_api_bp.route('/notifications/<int:notification_id>/read', methods=['PATCH', 'PUT'])
def mark_notification_read(notification_id):
    """Mark a notification as read"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            UPDATE Notification 
            SET is_read = 1, read_at = ? 
            WHERE id = ?
        ''', (datetime.now().isoformat(), notification_id))
        
        conn.commit()
        
        if cursor.rowcount == 0:
            return jsonify({'error': 'Notification not found.'}), 404
            
        return jsonify({'message': 'Notification marked as read.'}), 200
        
    except Exception as e:
        logger.error(f"Error marking notification {notification_id} as read: {e}", exc_info=True)
        conn.rollback()
        return jsonify({'error': 'An internal error occurred.'}), 500

@notifications_api_bp.route('/notifications/<int:notification_id>', methods=['DELETE'])
def delete_notification(notification_id):
    """Delete a notification"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute('DELETE FROM Notification WHERE id = ?', (notification_id,))
        conn.commit()
        
        if cursor.rowcount == 0:
            return jsonify({'error': 'Notification not found.'}), 404
            
        return jsonify({'message': 'Notification deleted successfully.'}), 200
        
    except Exception as e:
        logger.error(f"Error deleting notification {notification_id}: {e}", exc_info=True)
        conn.rollback()
        return jsonify({'error': 'An internal error occurred.'}), 500

@notifications_api_bp.route('/notifications/<int:notification_id>/dismiss', methods=['PATCH'])
def dismiss_notification(notification_id):
    """Dismiss a notification"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            UPDATE Notification 
            SET is_dismissed = 1, dismissed_at = ? 
            WHERE id = ?
        ''', (datetime.now().isoformat(), notification_id))
        
        conn.commit()
        
        if cursor.rowcount == 0:
            return jsonify({'error': 'Notification not found.'}), 404
            
        return jsonify({'message': 'Notification dismissed.'}), 200
        
    except Exception as e:
        logger.error(f"Error dismissing notification {notification_id}: {e}", exc_info=True)
        conn.rollback()
        return jsonify({'error': 'An internal error occurred.'}), 500

@notifications_api_bp.route('/notifications', methods=['POST'])
def create_notification():
    """Create a new notification"""
    data = request.json
    title = data.get('title')
    message = data.get('message')
    notification_type = data.get('notification_type', 'manual')
    priority = data.get('priority', 'medium')
    entry_id = data.get('entry_id')
    note_id = data.get('note_id')
    scheduled_for = data.get('scheduled_for')
    
    if not all([title, message]):
        return jsonify({'error': 'Title and message are required.'}), 400
    
    if priority not in ['low', 'medium', 'high', 'critical']:
        return jsonify({'error': 'Invalid priority level.'}), 400
    
    if notification_type not in ['note_based', 'sensor_based', 'manual', 'end_date_overdue']:
        return jsonify({'error': 'Invalid notification type.'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO Notification 
            (title, message, notification_type, priority, entry_id, note_id, scheduled_for)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (title, message, notification_type, priority, entry_id, note_id, scheduled_for))
        
        conn.commit()
        notification_id = cursor.lastrowid
        
        # Send push notification via ntfy if configured
        try:
            # Check if ntfy is configured in the database
            from app.services.ntfy_service import NtfyService
            ntfy_service = NtfyService.from_database()
            
            if ntfy_service and ntfy_service.server_url and ntfy_service.topic:
                # Get app base URL for creating action links
                app_base_url = request.host_url.rstrip('/')
                
                # Prepare notification data for ntfy
                notification_data = {
                    'title': title,
                    'message': message,
                    'type': notification_type,
                    'priority': priority,
                    'entry_id': entry_id,
                    'notification_id': notification_id
                }
                
                send_app_notification_via_ntfy(notification_data)
                logger.info(f"Successfully sent ntfy push notification for notification {notification_id}")
                    
        except Exception as e:
            logger.error(f"Error sending ntfy push notification: {e}", exc_info=True)
            # Don't fail the notification creation if push notification fails
        
        return jsonify({
            'message': 'Notification created successfully!',
            'notification_id': notification_id
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating notification: {e}", exc_info=True)
        conn.rollback()
        return jsonify({'error': 'An internal error occurred.'}), 500

@notifications_api_bp.route('/notification_rules', methods=['GET'])
def get_notification_rules():
    """Get all notification rules"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT 
                nr.*,
                et.singular_label as entry_type_label,
                e.title as entry_title
            FROM NotificationRule nr
            LEFT JOIN EntryType et ON nr.entry_type_id = et.id
            LEFT JOIN Entry e ON nr.entry_id = e.id
            ORDER BY nr.name
        ''')
        
        rules = [dict(row) for row in cursor.fetchall()]
        return jsonify(rules), 200
        
    except Exception as e:
        logger.error(f"Error fetching notification rules: {e}", exc_info=True)
        return jsonify({'error': 'An internal error occurred.'}), 500

@notifications_api_bp.route('/notification_rules', methods=['POST'])
def create_notification_rule():
    """Create a new notification rule"""
    data = request.json
    name = data.get('name')
    description = data.get('description')
    entry_type_id = data.get('entry_type_id')
    entry_id = data.get('entry_id')
    sensor_type = data.get('sensor_type')
    condition_type = data.get('condition_type')
    threshold_value = data.get('threshold_value')
    threshold_value_secondary = data.get('threshold_value_secondary')
    threshold_unit = data.get('threshold_unit')
    notification_title = data.get('notification_title')
    notification_message = data.get('notification_message')
    priority = data.get('priority', 'medium')
    cooldown_minutes = data.get('cooldown_minutes', 60)
    
    # Validate required fields
    required_fields = [name, sensor_type, condition_type, threshold_value, notification_title, notification_message]
    if not all(required_fields):
        return jsonify({'error': 'Missing required fields.'}), 400
    
    if condition_type not in ['greater_than', 'less_than', 'equals', 'between', 'change_rate']:
        return jsonify({'error': 'Invalid condition type.'}), 400
    
    if priority not in ['low', 'medium', 'high', 'critical']:
        return jsonify({'error': 'Invalid priority level.'}), 400
    
    # Ensure the sensor type exists in the system
    if not ensure_sensor_type_exists(sensor_type):
        logger.warning(f"Failed to ensure sensor type '{sensor_type}' exists, but continuing with rule creation")
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO NotificationRule 
            (name, description, entry_type_id, entry_id, sensor_type, condition_type, 
             threshold_value, threshold_value_secondary, threshold_unit, notification_title, 
             notification_message, priority, cooldown_minutes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, description, entry_type_id, entry_id, sensor_type, condition_type,
              threshold_value, threshold_value_secondary, threshold_unit, notification_title,
              notification_message, priority, cooldown_minutes))
        
        conn.commit()
        rule_id = cursor.lastrowid
        
        return jsonify({
            'message': 'Notification rule created successfully!',
            'rule_id': rule_id
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating notification rule: {e}", exc_info=True)
        conn.rollback()
        return jsonify({'error': 'An internal error occurred.'}), 500

@notifications_api_bp.route('/notification_rules/<int:rule_id>', methods=['DELETE'])
def delete_notification_rule(rule_id):
    """Delete a notification rule"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute('DELETE FROM NotificationRule WHERE id = ?', (rule_id,))
        conn.commit()
        
        if cursor.rowcount == 0:
            return jsonify({'error': 'Notification rule not found.'}), 404
            
        return jsonify({'message': 'Notification rule deleted successfully!'}), 200
        
    except Exception as e:
        logger.error(f"Error deleting notification rule {rule_id}: {e}", exc_info=True)
        conn.rollback()
        return jsonify({'error': 'An internal error occurred.'}), 500

@notifications_api_bp.route('/notification_rules/<int:rule_id>', methods=['PATCH'])
def patch_notification_rule(rule_id):
    """Partially update a notification rule (e.g., toggle active status)"""
    data = request.json
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Check if rule exists
        cursor.execute('SELECT id FROM NotificationRule WHERE id = ?', (rule_id,))
        if not cursor.fetchone():
            return jsonify({'error': 'Notification rule not found.'}), 404
        
        # Build dynamic UPDATE query based on provided fields
        update_fields = []
        update_values = []
        
        allowed_fields = ['is_active', 'name', 'description', 'priority', 'cooldown_minutes']
        
        for field in allowed_fields:
            if field in data:
                update_fields.append(f"{field} = ?")
                update_values.append(data[field])
        
        if not update_fields:
            return jsonify({'error': 'No valid fields to update'}), 400
        
        # Add rule_id to values
        update_values.append(rule_id)
        
        # Execute update
        query = f"UPDATE NotificationRule SET {', '.join(update_fields)} WHERE id = ?"
        cursor.execute(query, update_values)
        
        conn.commit()
        
        return jsonify({'message': 'Notification rule updated successfully!', 'id': rule_id}), 200
        
    except Exception as e:
        logger.error(f"Error patching notification rule {rule_id}: {e}", exc_info=True)
        conn.rollback()
        return jsonify({'error': 'An internal error occurred.'}), 500

@notifications_api_bp.route('/notification_rules/<int:rule_id>', methods=['PUT'])
def update_notification_rule(rule_id):
    """Update a notification rule"""
    data = request.json
    name = data.get('name')
    description = data.get('description')
    entry_type_id = data.get('entry_type_id')
    entry_id = data.get('entry_id')
    sensor_type = data.get('sensor_type')
    condition_type = data.get('condition_type')
    threshold_value = data.get('threshold_value')
    threshold_value_secondary = data.get('threshold_value_secondary')
    threshold_unit = data.get('threshold_unit')
    notification_title = data.get('notification_title')
    notification_message = data.get('notification_message')
    priority = data.get('priority', 'medium')
    cooldown_minutes = data.get('cooldown_minutes', 60)
    
    # Validate required fields
    required_fields = [name, sensor_type, condition_type, threshold_value, notification_title, notification_message]
    if not all(required_fields):
        return jsonify({'error': 'Missing required fields.'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Check if rule exists
        cursor.execute('SELECT id FROM NotificationRule WHERE id = ?', (rule_id,))
        if not cursor.fetchone():
            return jsonify({'error': 'Notification rule not found.'}), 404
        
        # Update the notification rule
        cursor.execute('''
            UPDATE NotificationRule SET
                name = ?,
                description = ?,
                entry_type_id = ?,
                entry_id = ?,
                sensor_type = ?,
                condition_type = ?,
                threshold_value = ?,
                threshold_value_secondary = ?,
                threshold_unit = ?,
                notification_title = ?,
                notification_message = ?,
                priority = ?,
                cooldown_minutes = ?
            WHERE id = ?
        ''', (name, description, entry_type_id, entry_id, sensor_type, condition_type,
              threshold_value, threshold_value_secondary, threshold_unit,
              notification_title, notification_message, priority, cooldown_minutes, rule_id))
        
        conn.commit()
        
        return jsonify({'message': 'Notification rule updated successfully!', 'id': rule_id}), 200
        
    except Exception as e:
        logger.error(f"Error updating notification rule {rule_id}: {e}", exc_info=True)
        conn.rollback()
        return jsonify({'error': 'An internal error occurred.'}), 500

def check_sensor_rules(entry_id, sensor_type, value, recorded_at):
    """Check if sensor data triggers any notification rules"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # First check if the entry is active - don't create notifications for inactive entries
        cursor.execute('SELECT status FROM Entry WHERE id = ?', (entry_id,))
        entry_result = cursor.fetchone()
        if not entry_result or entry_result['status'] == 'inactive':
            logger.debug(f"Skipping sensor rule check for inactive entry {entry_id}")
            return
        
        # Get applicable rules for this sensor data
        cursor.execute('''
            SELECT * FROM NotificationRule 
            WHERE is_active = 1 
            AND sensor_type = ?
            AND (entry_id = ? OR entry_id IS NULL)
            AND (entry_type_id IS NULL OR entry_type_id IN (
                SELECT entry_type_id FROM Entry WHERE id = ?
            ))
        ''', (sensor_type, entry_id, entry_id))
        
        rules = cursor.fetchall()
        
        for rule in rules:
            # Check if cooldown period has passed
            cursor.execute('''
                SELECT created_at FROM Notification 
                WHERE notification_type = 'sensor_based'
                AND entry_id = ?
                ORDER BY created_at DESC
                LIMIT 1
            ''', (entry_id,))
            
            last_notification = cursor.fetchone()
            if last_notification:
                last_time = datetime.fromisoformat(last_notification['created_at'])
                cooldown_end = last_time + timedelta(minutes=rule['cooldown_minutes'])
                if datetime.now() < cooldown_end:
                    continue  # Still in cooldown period
            
            # Check if condition is met
            try:
                # Extract numeric value from potentially formatted string (e.g., "232724 bytes" -> 232724)
                # This handles sensor values that include units from device data formatting
                import re
                numeric_match = re.match(r'^(-?\d+(?:\.\d+)?)', str(value).strip())
                if numeric_match:
                    sensor_value = float(numeric_match.group(1))
                else:
                    sensor_value = float(value)
                threshold = rule['threshold_value']
                
                condition_met = False
                if rule['condition_type'] == 'greater_than':
                    condition_met = sensor_value > threshold
                elif rule['condition_type'] == 'less_than':
                    condition_met = sensor_value < threshold
                elif rule['condition_type'] == 'equals':
                    condition_met = abs(sensor_value - threshold) < 0.01  # Allow small floating point differences
                elif rule['condition_type'] == 'between':
                    threshold_secondary = rule['threshold_value_secondary']
                    condition_met = min(threshold, threshold_secondary) <= sensor_value <= max(threshold, threshold_secondary)
                
                if condition_met:
                    # Create notification - sensor notifications should show immediately
                    cursor.execute('''
                        INSERT INTO Notification 
                        (title, message, notification_type, priority, entry_id, scheduled_for)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (rule['notification_title'], rule['notification_message'], 
                          'sensor_based', rule['priority'], entry_id, datetime.now().isoformat()))
                    
                    notification_id = cursor.lastrowid
                    conn.commit()
                    logger.info(f"Created sensor-based notification for rule {rule['id']}")
                    
                    # Send ntfy notification immediately for sensor-based notifications
                    try:
                        notification_data = {
                            'title': rule['notification_title'],
                            'message': rule['notification_message'],
                            'type': 'sensor_based',
                            'priority': rule['priority'],
                            'entry_id': entry_id,
                            'notification_id': notification_id
                        }
                        send_app_notification_via_ntfy(notification_data)
                    except Exception as e:
                        logger.error(f"Failed to send ntfy notification for sensor rule {rule['id']}: {e}")
                    
            except (ValueError, TypeError):
                # Skip non-numeric sensor values for numeric comparisons
                continue
                
    except Exception as e:
        logger.error(f"Error checking sensor rules: {e}", exc_info=True)

def check_sensor_rules_with_connection(cursor, entry_id, sensor_type, value, recorded_at):
    """Check if sensor data triggers any notification rules - version that accepts external cursor"""
    try:
        # First check if the entry is active - don't create notifications for inactive entries
        cursor.execute('SELECT status FROM Entry WHERE id = ?', (entry_id,))
        entry_result = cursor.fetchone()
        if not entry_result or entry_result['status'] == 'inactive':
            logger.debug(f"Skipping sensor rule check for inactive entry {entry_id}")
            return
        
        # Get applicable rules for this sensor data
        cursor.execute('''
            SELECT * FROM NotificationRule 
            WHERE is_active = 1 
            AND sensor_type = ?
            AND (entry_id = ? OR entry_id IS NULL)
            AND (entry_type_id IS NULL OR entry_type_id IN (
                SELECT entry_type_id FROM Entry WHERE id = ?
            ))
        ''', (sensor_type, entry_id, entry_id))
        
        rules = cursor.fetchall()
        
        for rule in rules:
            # Check if cooldown period has passed
            cursor.execute('''
                SELECT created_at FROM Notification 
                WHERE notification_type = 'sensor_based'
                AND entry_id = ?
                ORDER BY created_at DESC
                LIMIT 1
            ''', (entry_id,))
            
            last_notification = cursor.fetchone()
            if last_notification:
                last_time = datetime.fromisoformat(last_notification['created_at'])
                cooldown_end = last_time + timedelta(minutes=rule['cooldown_minutes'])
                if datetime.now() < cooldown_end:
                    continue  # Still in cooldown period
            
            # Check if condition is met
            try:
                # Extract numeric value from potentially formatted string (e.g., "232724 bytes" -> 232724)
                # This handles sensor values that include units from device data formatting
                import re
                numeric_match = re.match(r'^(-?\d+(?:\.\d+)?)', str(value).strip())
                if numeric_match:
                    sensor_value = float(numeric_match.group(1))
                else:
                    sensor_value = float(value)
                threshold = rule['threshold_value']
                
                condition_met = False
                if rule['condition_type'] == 'greater_than':
                    condition_met = sensor_value > threshold
                elif rule['condition_type'] == 'less_than':
                    condition_met = sensor_value < threshold
                elif rule['condition_type'] == 'equals':
                    condition_met = abs(sensor_value - threshold) < 0.01  # Allow small floating point differences
                elif rule['condition_type'] == 'between':
                    threshold_secondary = rule['threshold_value_secondary']
                    condition_met = min(threshold, threshold_secondary) <= sensor_value <= max(threshold, threshold_secondary)
                
                if condition_met:
                    # Create notification - sensor notifications should show immediately
                    cursor.execute('''
                        INSERT INTO Notification 
                        (title, message, notification_type, priority, entry_id, scheduled_for)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (rule['notification_title'], rule['notification_message'], 
                          'sensor_based', rule['priority'], entry_id, datetime.now().isoformat()))
                    
                    notification_id = cursor.lastrowid
                    # Note: Don't commit here - let the calling function handle the transaction
                    logger.info(f"Created sensor-based notification for rule {rule['id']}")
                    
                    # Send ntfy notification immediately for sensor-based notifications
                    try:
                        notification_data = {
                            'title': rule['notification_title'],
                            'message': rule['notification_message'],
                            'type': 'sensor_based',
                            'priority': rule['priority'],
                            'entry_id': entry_id,
                            'notification_id': notification_id
                        }
                        send_app_notification_via_ntfy(notification_data)
                    except Exception as e:
                        logger.error(f"Failed to send ntfy notification for sensor rule {rule['id']}: {e}")
                    
            except (ValueError, TypeError):
                # Skip non-numeric sensor values for numeric comparisons
                continue
                
    except Exception as e:
        logger.error(f"Error checking sensor rules with connection: {e}", exc_info=True)

def create_note_notification(note_id, entry_id, scheduled_for, title, message):
    """Create a notification from a note with future date"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO Notification 
            (title, message, notification_type, priority, entry_id, note_id, scheduled_for)
            VALUES (?, ?, 'note_based', 'medium', ?, ?, ?)
        ''', (title, message, entry_id, note_id, scheduled_for))
        
        notification_id = cursor.lastrowid
        conn.commit()
        
        # Send ntfy notification for note-based notifications that are scheduled for now or past
        try:
            from datetime import datetime
            scheduled_datetime = datetime.fromisoformat(scheduled_for.replace('Z', '+00:00'))
            current_datetime = datetime.now()
            
            # If scheduled for now or in the past, send immediately
            if scheduled_datetime <= current_datetime:
                notification_data = {
                    'title': title,
                    'message': message,
                    'type': 'note_based',
                    'priority': 'medium',
                    'entry_id': entry_id,
                    'notification_id': notification_id
                }
                send_app_notification_via_ntfy(notification_data)
        except Exception as e:
            logger.error(f"Failed to send ntfy notification for note {note_id}: {e}")
        
        return notification_id
        
    except Exception as e:
        logger.error(f"Error creating note notification: {e}", exc_info=True)
        raise

def check_overdue_end_dates():
    """
    Check for entries with overdue intended end dates and create notifications.
    This function should be called periodically (e.g., daily) to monitor overdue entries.
    """
    conn = None
    try:
        # Get a new connection since this might be called from a background task
        from ..db import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        
        # Get current date (YYYY-MM-DD format)
        current_date = datetime.now().strftime('%Y-%m-%d')
        
        # Find entries with intended_end_date that has passed and don't already have an overdue notification
        # Only check entries with ACTIVE state category (not completed/inactive entries)
        query = '''
            SELECT DISTINCT 
                e.id as entry_id,
                e.title,
                e.intended_end_date,
                et.singular_label as entry_type
            FROM Entry e
            JOIN EntryType et ON e.entry_type_id = et.id
            LEFT JOIN EntryState es ON es.entry_type_id = e.entry_type_id AND es.name = e.status
            WHERE 
                e.intended_end_date IS NOT NULL 
                AND e.intended_end_date != ''
                AND date(e.intended_end_date) < date(?)
                AND COALESCE(es.category, 'active') = 'active'
                AND et.show_end_dates = 1
                AND NOT EXISTS (
                    SELECT 1 FROM Notification n 
                    WHERE n.entry_id = e.id 
                    AND n.notification_type = 'end_date_overdue'
                    AND n.is_dismissed = 0
                )
        '''
        
        cursor.execute(query, (current_date,))
        overdue_entries = cursor.fetchall()
        
        notifications_created = 0
        
        for entry in overdue_entries:
            try:
                # Calculate how many days overdue
                intended_end = datetime.strptime(entry['intended_end_date'][:10], '%Y-%m-%d')
                current = datetime.now()
                days_overdue = (current - intended_end).days
                
                # Create notification
                title = f"Overdue: {entry['title']}"
                message = f"The {entry['entry_type'].lower()} '{entry['title']}' has an intended end date of {entry['intended_end_date'][:10]} and is {days_overdue} day{'s' if days_overdue != 1 else ''} overdue."
                
                cursor.execute('''
                    INSERT INTO Notification 
                    (title, message, notification_type, priority, entry_id, scheduled_for)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (title, message, 'end_date_overdue', 'high', entry['entry_id'], current_date))
                
                notifications_created += 1
                logger.info(f"Created overdue notification for entry {entry['entry_id']}: {entry['title']}")
                
            except Exception as e:
                logger.error(f"Error creating overdue notification for entry {entry['entry_id']}: {e}")
                continue
        
        conn.commit()
        logger.info(f"Overdue end date check completed. Created {notifications_created} notifications.")
        return notifications_created
        
    except Exception as e:
        logger.error(f"Error in check_overdue_end_dates: {e}", exc_info=True)
        if conn:
            conn.rollback()
        return 0
    finally:
        if conn:
            conn.close()

@notifications_api_bp.route('/check_overdue_end_dates', methods=['POST'])
def manual_check_overdue_end_dates():
    """Manually trigger the overdue end date check (for testing or manual execution)"""
    try:
        notifications_created = check_overdue_end_dates()
        return jsonify({
            'message': f'Overdue check completed. Created {notifications_created} notifications.',
            'notifications_created': notifications_created
        }), 200
    except Exception as e:
        logger.error(f"Error in manual overdue check: {e}", exc_info=True)
        return jsonify({'error': 'An error occurred while checking for overdue entries.'}), 500
