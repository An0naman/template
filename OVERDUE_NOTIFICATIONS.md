# Overdue End Date Notifications

This functionality automatically creates notifications when entries have intended end dates that have passed.

## Features

- **Automatic Detection**: Monitors entries with intended end dates that have passed
- **Smart Filtering**: Only creates notifications for:
  - Entries with entry types that have `show_end_dates` enabled
  - Active entries (not inactive)
  - Entries that don't already have an overdue notification for the current day
- **High Priority**: Overdue notifications are created with "high" priority to ensure visibility
- **Detailed Messages**: Notifications include how many days overdue the entry is

## Implementation

### 1. Automated Checking (Recommended)

Set up a daily cron job to automatically check for overdue entries:

```bash
# Edit your crontab
crontab -e

# Add this line to run daily at 9:00 AM
0 9 * * * /path/to/your/project/cron_check_overdue.sh

# Or run hourly (if you need more frequent checks)
0 * * * * /path/to/your/project/cron_check_overdue.sh
```

### 2. Manual Checking

You can manually trigger the overdue check in several ways:

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

## Configuration

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
