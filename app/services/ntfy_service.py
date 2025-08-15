# ntfy_service.py
import requests
import logging
from flask import current_app

logger = logging.getLogger(__name__)

class NtfyService:
    """Service for sending push notifications via ntfy.sh"""
    
    def __init__(self, server_url="https://ntfy.sh", topic=None, auth_token=None):
        """
        Initialize ntfy service
        
        Args:
            server_url (str): ntfy server URL (default: https://ntfy.sh)
            topic (str): ntfy topic name for your app
            auth_token (str): Optional authentication token for private topics
        """
        self.server_url = server_url.rstrip('/')
        self.topic = topic
        self.auth_token = auth_token
        
    def send_notification(self, title, message, priority=3, tags=None, actions=None, click_url=None):
        """
        Send a notification via ntfy
        
        Args:
            title (str): Notification title
            message (str): Notification message
            priority (int): Priority level (1=min, 2=low, 3=default, 4=high, 5=urgent)
            tags (list): List of emoji tags for the notification
            actions (list): List of action buttons
            click_url (str): URL to open when notification is clicked
            
        Returns:
            tuple: (success: bool, response_text: str)
        """
        if not self.topic:
            logger.error("No ntfy topic configured")
            return False, "No ntfy topic configured"
            
        url = f"{self.server_url}/{self.topic}"
        
        # Ensure title is ASCII-safe for HTTP headers
        try:
            title.encode('ascii')
            safe_title = title
        except UnicodeEncodeError:
            # If title contains Unicode, try to remove problematic characters
            safe_title = title.encode('ascii', errors='ignore').decode('ascii')
            if not safe_title.strip():
                safe_title = "Notification"
        
        headers = {
            "Title": safe_title,
            "Priority": str(priority),
            "Content-Type": "text/plain; charset=utf-8"
        }
        
        # Add optional headers (ensure ASCII encoding for HTTP headers)
        if tags:
            # Filter out any non-ASCII characters from tags for headers
            ascii_tags = []
            for tag in tags:
                try:
                    # Try to encode as ASCII, skip if it fails
                    tag.encode('ascii')
                    ascii_tags.append(tag)
                except UnicodeEncodeError:
                    # For emoji tags, use text alternatives
                    emoji_map = {
                        '📱': 'phone',
                        '📝': 'note', 
                        '📊': 'chart',
                        '⚠️': 'warning',
                        '🎉': 'party',
                        '🚀': 'rocket'
                    }
                    if tag in emoji_map:
                        ascii_tags.append(emoji_map[tag])
            
            if ascii_tags:
                headers["Tags"] = ",".join(ascii_tags)
            
        if click_url:
            headers["Click"] = click_url
            
        if actions:
            # Format actions for ntfy
            # Example: [{"action": "view", "label": "View", "url": "https://..."}]
            action_strings = []
            for action in actions:
                if action.get('action') == 'view' and action.get('url'):
                    action_strings.append(f"view, {action.get('label', 'View')}, {action['url']}")
                elif action.get('action') == 'http':
                    action_strings.append(f"http, {action.get('label', 'Action')}, {action['url']}")
            if action_strings:
                headers["Actions"] = "; ".join(action_strings)
        
        # Add authentication if provided
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        
        try:
            # Ensure message is properly encoded as UTF-8
            if isinstance(message, str):
                message_data = message.encode('utf-8')
            else:
                message_data = message
                
            response = requests.post(
                url,
                data=message_data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"Successfully sent ntfy notification: {title}")
                return True, "Notification sent successfully"
            else:
                error_msg = f"Failed to send notification. Status: {response.status_code}, Response: {response.text}"
                logger.error(error_msg)
                return False, error_msg
                
        except requests.exceptions.RequestException as e:
            error_msg = f"Error sending ntfy notification: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def send_notification_from_app_notification(self, notification_data, app_base_url=None):
        """
        Send an ntfy notification based on app notification data with enhanced context
        
        Args:
            notification_data (dict): Notification data from the app
            app_base_url (str): Base URL of the app for creating action links
            
        Returns:
            tuple: (success: bool, response_text: str)
        """
        from app.db import get_connection
        
        # Start with basic notification data
        enhanced_title = notification_data.get('title', 'Notification')
        enhanced_message = notification_data.get('message', '')
        
        # Get notification type for better context
        notification_type = notification_data.get('type', notification_data.get('notification_type', 'manual'))
        
        # If entry_id is provided, fetch entry details to enhance the notification
        if notification_data.get('entry_id'):
            try:
                conn = get_connection()
                cursor = conn.cursor()
                
                # Fetch entry details including entry type
                cursor.execute('''
                    SELECT e.title as entry_title, e.status, e.intended_end_date, 
                           et.name as entry_type_name
                    FROM Entry e
                    LEFT JOIN EntryType et ON e.entry_type_id = et.id
                    WHERE e.id = ?
                ''', (notification_data['entry_id'],))
                
                entry = cursor.fetchone()
                conn.close()
                
                if entry:
                    # Temporarily disable emojis to avoid encoding issues
                    entry_type_name = entry['entry_type_name'] or 'Entry'
                    # enhanced_title = f"[{entry_type_name}] {enhanced_title}"
                    
                    # Add detailed entry context to message
                    entry_title = entry['entry_title'] or 'Untitled Entry'
                    entry_type_name = entry['entry_type_name'] or 'Entry'
                    entry_status = (entry['status'] or 'Unknown').title()
                    
                    enhanced_message += f"\n\n[Entry] {entry_title}"
                    enhanced_message += f"\n[Type] {entry_type_name}"
                    enhanced_message += f"\n[Status] {entry_status}"
                    
                    if entry['intended_end_date']:
                        from datetime import datetime
                        try:
                            # Parse and format the due date nicely
                            due_date = datetime.fromisoformat(entry['intended_end_date'].replace('Z', '+00:00'))
                            enhanced_message += f"\n[Due] {due_date.strftime('%B %d, %Y')}"
                        except:
                            enhanced_message += f"\n[Due] {entry['intended_end_date'][:10]}"
                            
            except Exception as e:
                logger.error(f"Error fetching entry details for notification: {e}")
                # Continue with basic notification if entry fetch fails
        
        # If note_id is provided, fetch note details
        if notification_data.get('note_id'):
            try:
                conn = get_connection()
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT note_title, entry_id
                    FROM Note 
                    WHERE id = ?
                ''', (notification_data['note_id'],))
                
                note = cursor.fetchone()
                
                if note and note['note_title']:
                    enhanced_message += f"\n[Note] {note['note_title']}"
                    
                conn.close()
                    
            except Exception as e:
                logger.error(f"Error fetching note details for notification: {e}")
        
        # Add notification type context with better formatting
        type_context = {
            'note_based': 'Reminder',
            'sensor_based': 'Sensor Alert', 
            'manual': 'Manual',
            'end_date_overdue': 'Overdue Alert'
        }
        
        type_display = type_context.get(notification_type, 'System')
        enhanced_message += f"\n\n[Type] {type_display}"
        
        # Set priority mapping
        priority_map = {
            'low': 2,
            'medium': 3,
            'high': 4,
            'critical': 5
        }
        priority = priority_map.get(notification_data.get('priority', 'medium'), 3)
        
        # Enhanced emoji tags based on notification type and context
        tag_map = {
            'note_based': ['📝', 'reminder'],
            'sensor_based': ['📊', 'warning', 'sensor'],
            'manual': ['👤', 'manual'],
            'end_date_overdue': ['⚠️', 'calendar', 'overdue']
        }
        tags = tag_map.get(notification_type, ['📱'])
        
        # Create enhanced action buttons
        actions = []
        if notification_data.get('entry_id') and app_base_url:
            entry_url = f"{app_base_url}/entry/{notification_data['entry_id']}"
            actions.append({
                'action': 'view',
                'label': '👁️ View Entry',
                'url': entry_url
            })
            
            # Add mark complete action for entries that aren't completed
            actions.append({
                'action': 'http',
                'label': '✅ Mark Complete',
                'url': f"{app_base_url}/api/entries/{notification_data['entry_id']}/complete",
                'method': 'POST'
            })
        
        # Set click URL
        click_url = None
        if app_base_url:
            if notification_data.get('entry_id'):
                click_url = f"{app_base_url}/entry/{notification_data['entry_id']}"
            else:
                click_url = app_base_url
        
        return self.send_notification(
            title=enhanced_title,
            message=enhanced_message,
            priority=priority,
            tags=tags,
            actions=actions,
            click_url=click_url
        )
    
    @classmethod
    def from_config(cls, config=None):
        """
        Create NtfyService instance from app config
        
        Args:
            config (dict): Flask app config or None to use current_app.config
            
        Returns:
            NtfyService: Configured service instance
        """
        if config is None:
            config = current_app.config
            
        return cls(
            server_url=config.get('NTFY_SERVER_URL', 'https://ntfy.sh'),
            topic=config.get('NTFY_TOPIC'),
            auth_token=config.get('NTFY_AUTH_TOKEN')
        )
    
    @classmethod
    def from_database(cls):
        """
        Create NtfyService instance from database configuration
        
        Returns:
            NtfyService: Configured service instance
        """
        from flask import g
        import sqlite3
        
        # Get database connection
        if 'db' not in g:
            db_path = current_app.config['DATABASE_PATH']
            g.db = sqlite3.connect(db_path)
            g.db.row_factory = sqlite3.Row
        
        cursor = g.db.cursor()
        cursor.execute("SELECT parameter_name, parameter_value FROM SystemParameters WHERE parameter_name IN ('ntfy_server_url', 'ntfy_topic', 'ntfy_auth_token')")
        params = dict(cursor.fetchall())
        
        return cls(
            server_url=params.get('ntfy_server_url', 'https://ntfy.sh'),
            topic=params.get('ntfy_topic'),
            auth_token=params.get('ntfy_auth_token')
        )


def send_app_notification_via_ntfy(notification_data, app_base_url=None):
    """
    Convenience function to send app notifications via ntfy
    
    Args:
        notification_data (dict): Notification data from the app
        app_base_url (str): Base URL of the app for creating action links
        
    Returns:
        tuple: (success: bool, response_text: str)
    """
    try:
        ntfy_service = NtfyService.from_database()
        return ntfy_service.send_notification_from_app_notification(
            notification_data, 
            app_base_url
        )
    except Exception as e:
        error_msg = f"Error initializing ntfy service: {str(e)}"
        logger.error(error_msg)
        return False, error_msg
