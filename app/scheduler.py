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
        
        while self.running:
            try:
                with self.app.app_context():
                    # Check if overdue checking is enabled
                    if self._should_run_overdue_check(last_overdue_check):
                        logger.info("Running overdue check...")
                        self._check_overdue_entries()
                        last_overdue_check = datetime.now()
                        
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
        """Check for overdue entries and create notifications"""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # Find entries that are overdue (intended_end_date is past and status is not completed)
            cursor.execute("""
                SELECT e.id, e.title, e.intended_end_date, et.name as entry_type_name
                FROM Entry e
                JOIN EntryType et ON e.entry_type_id = et.id
                WHERE e.intended_end_date IS NOT NULL 
                  AND e.intended_end_date != ''
                  AND e.status != 'completed'
                  AND date(e.intended_end_date) < date('now')
                  AND et.show_end_dates = 1
            """)
            
            overdue_entries = cursor.fetchall()
            
            for entry in overdue_entries:
                # Check if we already have a recent notification for this entry
                cursor.execute("""
                    SELECT id FROM Notification 
                    WHERE entry_id = ? 
                      AND notification_type = 'overdue'
                      AND created_at > datetime('now', '-7 days')
                """, (entry['id'],))
                
                recent_notification = cursor.fetchone()
                
                if not recent_notification:
                    # Create notification
                    title = f"Overdue: {entry['title']}"
                    message = f"The {entry['entry_type_name'].lower()} '{entry['title']}' was due on {entry['intended_end_date']} and is now overdue."
                    
                    cursor.execute("""
                        INSERT INTO Notification 
                        (title, message, notification_type, priority, entry_id, scheduled_for)
                        VALUES (?, ?, 'overdue', 'high', ?, datetime('now'))
                    """, (title, message, entry['id']))
                    
                    logger.info(f"Created overdue notification for entry {entry['id']}: {entry['title']}")
            
            conn.commit()
            conn.close()
            
            if overdue_entries:
                logger.info(f"Processed {len(overdue_entries)} overdue entries")
            else:
                logger.info("No overdue entries found")
                
        except Exception as e:
            logger.error(f"Error checking overdue entries: {e}", exc_info=True)

# Global scheduler instance
scheduler = TaskScheduler()
