# template_app/app/scheduler.py
import threading
import time
import logging
from datetime import datetime, timedelta
from flask import current_app
from app.db import get_connection
import sqlite3

logger = logging.getLogger(__name__)

class TaskScheduler:
    def __init__(self, app=None):
        self.app = app
        self.running = False
        self.thread = None
        
    def init_app(self, app):
        self.app = app
        
    def start(self):
        """Start the scheduler in a background thread"""
        if self.running:
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.thread.start()
        logger.info("Task scheduler started")
        
    def stop(self):
        """Stop the scheduler"""
        self.running = False
        if self.thread:
            self.thread.join()
        logger.info("Task scheduler stopped")
        
    def _run_scheduler(self):
        """Main scheduler loop"""
        last_overdue_check = None
        last_scheduled_check = None
        
        while self.running:
            try:
                with self.app.app_context():
                    # Check if overdue checking is enabled
                    if self._should_run_overdue_check(last_overdue_check):
                        logger.info("Running overdue check...")
                        self._check_overdue_entries()
                        last_overdue_check = datetime.now()
                    
                    # Check for scheduled notifications every minute
                    if self._should_run_scheduled_check(last_scheduled_check):
                        logger.info("Running scheduled notifications check...")
                        self._process_scheduled_notifications()
                        last_scheduled_check = datetime.now()
                        
            except Exception as e:
                logger.error(f"Error in scheduler: {e}", exc_info=True)
                
            # Sleep for 1 minute before checking again
            time.sleep(60)
            
    def _should_run_overdue_check(self, last_check):
        """Determine if overdue check should run based on schedule"""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # Get overdue check settings
            cursor.execute("SELECT parameter_value FROM SystemParameters WHERE parameter_name = 'overdue_check_enabled'")
            enabled_row = cursor.fetchone()
            enabled = enabled_row and enabled_row['parameter_value'].lower() == 'true'
            
            if not enabled:
                return False
                
            cursor.execute("SELECT parameter_value FROM SystemParameters WHERE parameter_name = 'overdue_check_schedule'")
            schedule_row = cursor.fetchone()
            schedule = schedule_row['parameter_value'] if schedule_row else '0 9 * * *'
            
            conn.close()
            
            # Parse cron schedule (simplified for common cases)
            # Format: minute hour day month dayofweek
            # For now, we'll support daily schedules like "0 9 * * *" (9 AM daily)
            parts = schedule.split()
            if len(parts) >= 2:
                try:
                    target_hour = int(parts[1])
                    target_minute = int(parts[0])
                    
                    now = datetime.now()
                    
                    # If we haven't checked today at the target time, and it's past that time
                    if last_check is None or last_check.date() < now.date():
                        target_time = now.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
                        if now >= target_time:
                            return True
                            
                except ValueError:
                    # Invalid schedule format, default to once per day
                    if last_check is None or (datetime.now() - last_check).days >= 1:
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking schedule: {e}")
            return False
            
    def _check_overdue_entries(self):
        """Check for overdue entries and create notifications with ntfy integration"""
        try:
            # Import here to avoid circular imports
            from app.api.notifications_api import check_overdue_end_dates
            
            # Use the ntfy-integrated overdue check function
            notifications_created = check_overdue_end_dates()
            
            if notifications_created > 0:
                logger.info(f"Scheduler created {notifications_created} overdue notifications with ntfy integration")
            else:
                logger.info("Scheduler: No overdue entries found")
                
        except Exception as e:
            logger.error(f"Error in scheduler overdue check: {e}", exc_info=True)

    def _should_run_scheduled_check(self, last_check):
        """Check if scheduled notifications should be processed (every minute)"""
        if last_check is None:
            return True
        
        # Run every minute
        return (datetime.now() - last_check).total_seconds() >= 60

    def _process_scheduled_notifications(self):
        """Process notifications that are scheduled for now and send ntfy notifications"""
        try:
            # Import here to avoid circular imports
            from app.services.ntfy_service import send_app_notification_via_ntfy
            from app.db import get_connection
            
            conn = get_connection()
            cursor = conn.cursor()
            
            # Add ntfy_sent column if it doesn't exist
            try:
                cursor.execute("PRAGMA table_info(Notification)")
                columns = [column[1] for column in cursor.fetchall()]
                if 'ntfy_sent' not in columns:
                    logger.info("Adding ntfy_sent column to Notification table...")
                    cursor.execute('ALTER TABLE Notification ADD COLUMN ntfy_sent INTEGER DEFAULT 0')
                    conn.commit()
                    logger.info("Successfully added ntfy_sent column")
            except Exception as e:
                logger.error(f"Error adding ntfy_sent column: {e}")
            
            # Find notifications that are scheduled for now or past and haven't been sent
            current_time = datetime.now().isoformat()
            
            cursor.execute('''
                SELECT n.id, n.title, n.message, n.notification_type, n.priority, 
                       n.entry_id, n.note_id, n.scheduled_for
                FROM Notification n
                WHERE n.scheduled_for IS NOT NULL 
                  AND n.scheduled_for <= ?
                  AND (n.ntfy_sent IS NULL OR n.ntfy_sent = 0)
            ''', (current_time,))
            
            due_notifications = cursor.fetchall()
            
            for notification in due_notifications:
                notification_id = notification['id']
                
                try:
                    # Send ntfy notification
                    notification_data = {
                        'title': notification['title'],
                        'message': notification['message'],
                        'type': notification['notification_type'],
                        'priority': notification['priority'],
                        'entry_id': notification['entry_id'],
                        'notification_id': notification_id
                    }
                    
                    send_app_notification_via_ntfy(notification_data)
                    
                    # Mark as sent in database
                    cursor.execute('''
                        UPDATE Notification 
                        SET ntfy_sent = 1 
                        WHERE id = ?
                    ''', (notification_id,))
                    
                    logger.info(f"Sent scheduled ntfy notification {notification_id}: {notification['title']}")
                    
                except Exception as e:
                    logger.error(f"Failed to send scheduled ntfy notification {notification_id}: {e}")
                    continue
            
            conn.commit()
            conn.close()
            
            if due_notifications:
                logger.info(f"Processed {len(due_notifications)} scheduled notifications")
                
        except Exception as e:
            logger.error(f"Error processing scheduled notifications: {e}", exc_info=True)

# Global scheduler instance
scheduler = TaskScheduler()
