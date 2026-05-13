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
        self.sent_notifications = set()  # Track sent notification IDs
        
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
        last_strava_sync = None
        last_scheduled_check = None
        
        while self.running:
            try:
                with self.app.app_context():
                    # Check if overdue checking is enabled
                    if self._should_run_overdue_check(last_overdue_check):
                        logger.info("Running overdue check...")
                        self._check_overdue_entries()
                        last_overdue_check = datetime.now()

                    if self._should_run_strava_sync(last_strava_sync):
                        logger.info("Running scheduled Strava sync...")
                        self._run_strava_sync()
                        last_strava_sync = datetime.now()
                    
                    # Check for scheduled notifications every minute
                    if self._should_run_scheduled_check(last_scheduled_check):
                        logger.info("Running scheduled notifications check...")
                        self._process_scheduled_notifications()
                        last_scheduled_check = datetime.now()
                        
            except Exception as e:
                logger.error(f"Error in scheduler: {e}", exc_info=True)
                
            # Sleep for 1 minute before checking again
            time.sleep(60)

    def _should_run_job(self, last_check, enabled_param, schedule_param, default_schedule):
        """Determine if a scheduled job should run for common cron-style schedules."""
        try:
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT parameter_value FROM SystemParameters WHERE parameter_name = ?", (enabled_param,))
            enabled_row = cursor.fetchone()
            enabled_val = (enabled_row or {}).get('parameter_value', 'false')
            enabled = str(enabled_val).lower() in ('true', '1', 'yes', 'on')
            if not enabled:
                conn.close()
                return False

            cursor.execute("SELECT parameter_value FROM SystemParameters WHERE parameter_name = ?", (schedule_param,))
            schedule_row = cursor.fetchone()
            schedule = (schedule_row or {}).get('parameter_value') or default_schedule
            conn.close()

            parts = schedule.split()
            if len(parts) < 2:
                return False

            minute_part = parts[0]
            hour_part = parts[1]
            day_of_week_part = parts[4] if len(parts) > 4 else '*'

            try:
                target_minute = int(minute_part)
            except ValueError:
                return False

            now = datetime.now()

            # Respect weekday ranges like 1-5 (Mon-Fri).
            if day_of_week_part != '*':
                allowed_days = set()
                for token in day_of_week_part.split(','):
                    token = token.strip()
                    if not token:
                        continue
                    if '-' in token:
                        try:
                            start, end = token.split('-', 1)
                            start_i = int(start)
                            end_i = int(end)
                            allowed_days.update(range(start_i, end_i + 1))
                        except ValueError:
                            continue
                    else:
                        try:
                            allowed_days.add(int(token))
                        except ValueError:
                            continue
                if allowed_days:
                    # Python weekday: Mon=0..Sun=6, Cron weekday: Sun=0/7, Mon=1..Sat=6
                    cron_weekday = (now.weekday() + 1) % 7
                    if cron_weekday not in allowed_days:
                        return False

            if hour_part == '*':
                slot = now.replace(minute=target_minute, second=0, microsecond=0)
                if now < slot:
                    return False
                return last_check is None or last_check < slot

            if hour_part.startswith('*/'):
                try:
                    interval_hours = int(hour_part[2:])
                except ValueError:
                    return False
                if interval_hours <= 0 or now.hour % interval_hours != 0:
                    return False
                slot = now.replace(minute=target_minute, second=0, microsecond=0)
                if now < slot:
                    return False
                return last_check is None or last_check < slot

            target_hour = int(hour_part)
            target_time = now.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
            if now < target_time:
                return False
            return last_check is None or last_check < target_time

        except Exception as e:
            logger.error(f"Error checking scheduled job ({enabled_param}): {e}")
            return False
            
    def _should_run_overdue_check(self, last_check):
        """Determine if overdue check should run based on schedule"""
        return self._should_run_job(
            last_check,
            'overdue_check_enabled',
            'overdue_check_schedule',
            '0 9 * * *',
        )

    def _should_run_strava_sync(self, last_check):
        """Determine if scheduled Strava sync should run based on schedule."""
        return self._should_run_job(
            last_check,
            'strava_sync_enabled',
            'strava_sync_schedule',
            '0 */6 * * *',
        )
            
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

    def _run_strava_sync(self):
        """Run Strava sync as a scheduled job."""
        try:
            from app.services.strava_service import sync_strava_activities

            result = sync_strava_activities()
            logger.info(f"Scheduled Strava sync result: {result}")
        except Exception as e:
            logger.error(f"Error in scheduled Strava sync: {e}", exc_info=True)

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
            
            # Find notifications that are scheduled for now or past
            current_time = datetime.now().isoformat()
            
            cursor.execute('''
                SELECT n.id, n.title, n.message, n.notification_type, n.priority, 
                       n.entry_id, n.note_id, n.scheduled_for
                FROM Notification n
                WHERE n.scheduled_for IS NOT NULL 
                  AND n.scheduled_for <= ?
            ''', (current_time,))
            
            due_notifications = cursor.fetchall()
            
            for notification in due_notifications:
                notification_id = notification['id']
                
                # Skip if we've already sent this notification
                if notification_id in self.sent_notifications:
                    continue
                
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
                    
                    # Mark as sent in memory
                    self.sent_notifications.add(notification_id)
                    
                    logger.info(f"Sent scheduled ntfy notification {notification_id}: {notification['title']}")
                    
                except Exception as e:
                    logger.error(f"Failed to send scheduled ntfy notification {notification_id}: {e}")
                    continue
            
            conn.close()
            
            if due_notifications:
                logger.info(f"Processed {len(due_notifications)} scheduled notifications ({len([n for n in due_notifications if n['id'] not in self.sent_notifications])} new)")
                
        except Exception as e:
            logger.error(f"Error processing scheduled notifications: {e}", exc_info=True)

# Global scheduler instance
scheduler = TaskScheduler()
