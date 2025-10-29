# Overdue End Date Notifications

This functionality automatically creates notifications when entries have intended end dates that have passed.

## Features

- **Web-Based Configuration**: Configure all settings through the Settings page in the web interface
- **Automatic Detection**: Monitors entries with intended end dates that have passed
- **Smart Filtering**: Only creates notifications for:
  - Entries with entry types that have `show_end_dates` enabled
  - Active entries (not inactive)
  - Entries that don't already have an overdue notification
- **High Priority**: Overdue notifications are created with "high" priority to ensure visibility
- **Detailed Messages**: Notifications include how many days overdue the entry is
- **Flexible Scheduling**: Choose from multiple pre-configured schedules or set custom cron expressions

## Quick Setup

### 1. Configure Settings (Web Interface)
1. Go to **Settings** in your web application
2. Scroll to **"Overdue Notification Settings"** section
3. Check **"Enable automatic overdue notifications"**
4. Select your preferred **check schedule** from the dropdown:
   - Daily at 9:00 AM (recommended)
   - Daily at 8:00 AM
   - Every 6 hours
   - Weekdays only
   - And more options...
5. Click **"Save Overdue Settings"**

### 2. Set Up Cron Job
Copy the cron command shown in the settings and add it to your crontab:

```bash
# Open crontab editor
crontab -e

# Add the line shown in settings (example for daily at 9 AM):
0 9 * * * /home/an0naman/Documents/GitHub/template/cron_check_overdue.sh
```

### 3. Configure Entry Types
1. Go to **Maintenance > Manage Entry Types**
2. Edit entry types that should be monitored
3. Check **"Show End Date fields"**
4. Save the entry type

### 4. Test the Setup
1. In Settings, click **"Test Overdue Check Now"** to verify it works
2. Create test entries with overdue intended end dates
3. Run the manual test again to see notifications created

## Implementation Options

## Available Schedules

The settings page offers these pre-configured options:

| Schedule | Description | Cron Expression |
|----------|-------------|-----------------|
| Daily at 9:00 AM | Recommended for most users | `0 9 * * *` |
| Daily at 8:00 AM | Early morning check | `0 8 * * *` |
| Daily at 10:00 AM | Mid-morning check | `0 10 * * *` |
| Daily at midnight | Midnight daily check | `0 0 * * *` |
| Every 6 hours | Four times per day | `0 */6 * * *` |
| Every 3 hours | Eight times per day | `0 */3 * * *` |
| Every hour | Frequent checking | `0 * * * *` |
| Weekdays at 8:00 AM | Business days only | `0 8 * * 1-5` |

## Advanced Configuration

### Manual Checking Options

You can manually trigger the overdue check in several ways:

#### Settings Page (Recommended)
1. Go to **Settings > Overdue Notification Settings**
2. Click **"Test Overdue Check Now"**
3. View results in the status message

#### Command Line
```bash
# From project directory
/path/to/project/.venv/bin/python check_overdue_dates.py
```

#### API Endpoint
```bash
# POST request to trigger manual check
curl -X POST http://localhost:5000/api/check_overdue_end_dates
```

#### From Python Code
```python
from app.api.notifications_api import check_overdue_end_dates

# Within Flask app context
with app.app_context():
    notifications_created = check_overdue_end_dates()
    print(f"Created {notifications_created} notifications")
```

## System Parameters

The following system parameters control overdue notifications:

- **`overdue_check_enabled`**: `true` or `false` - Whether overdue checking is enabled
- **`overdue_check_schedule`**: Cron expression - When to run the checks (e.g., `0 9 * * *`)

These are configured through the Settings page and automatically applied to the cron script.

## Configuration Details

### Entry Type Setup
1. Go to **Maintenance > Manage Entry Types**
2. Edit an entry type
3. Check the **"Show End Date fields"** checkbox
4. Save the entry type

### Entry Setup
1. Create or edit an entry of a type that has end dates enabled
2. Set the **"Intended End Date"** field
3. The system will monitor this date and create notifications when it passes

## Notification Details

When an intended end date passes, the system creates a notification with:

- **Type**: `end_date_overdue`
- **Priority**: `high` 
- **Title**: "Overdue: [Entry Title]"
- **Message**: Detailed message including:
  - Entry type and title
  - Original intended end date
  - Number of days overdue

## Technical Details

### Database Changes
- Added `end_date_overdue` as a valid notification type
- No additional database schema changes required

### Files Added/Modified
- `check_overdue_dates.py` - Standalone script for checking overdue dates
- `cron_check_overdue.sh` - Cron job wrapper script
- `app/api/notifications_api.py` - Added overdue checking functions and API endpoint

### Logging
- Script logs are written to `logs/overdue_check.log`
- Application logs include overdue check activities
- Each notification creation is logged for audit purposes

## Troubleshooting

### Common Issues

1. **"No such column" error**: Ensure database migrations have been applied by running the app once
2. **Import errors**: Verify Flask and dependencies are installed: `pip install -r requirements.txt`
3. **No notifications created**: Check that:
   - Entries have intended end dates set
   - Entry types have `show_end_dates` enabled
   - Entries are not marked as inactive
   - The intended end date has actually passed

### Debugging
- Run the script manually to see detailed logs: `python check_overdue_dates.py`
- Check the notification table in the database for created notifications
- Review logs in `logs/overdue_check.log` and `logs/app_errors.log`
