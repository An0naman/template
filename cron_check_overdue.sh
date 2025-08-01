#!/bin/bash
# Cron script to run the overdue end date checker
# This script should be added to your crontab based on the schedule configured in settings

# Set the project directory (change this to your actual project path)
PROJECT_DIR="/home/an0naman/Documents/GitHub/template"

# Change to project directory
cd "$PROJECT_DIR"

# Check if overdue checking is enabled before running
PYTHON_CMD="$PROJECT_DIR/.venv/bin/python"

# Check if overdue check is enabled in system parameters
ENABLED=$($PYTHON_CMD -c "
from app import create_app
from app.db import get_system_parameters
app = create_app()
with app.app_context():
    params = get_system_parameters()
    print(params.get('overdue_check_enabled', 'false'))
" 2>/dev/null)

# Only run if enabled
if [ "$ENABLED" = "true" ]; then
    echo "$(date): Running overdue check (enabled in settings)"
    "$PYTHON_CMD" check_overdue_dates.py
else
    echo "$(date): Overdue check is disabled in settings, skipping"
fi

# Example crontab entries based on your settings:
# Daily at 9:00 AM:     0 9 * * * /path/to/project/cron_check_overdue.sh
# Daily at 8:00 AM:     0 8 * * * /path/to/project/cron_check_overdue.sh  
# Daily at 10:00 AM:    0 10 * * * /path/to/project/cron_check_overdue.sh
# Daily at midnight:    0 0 * * * /path/to/project/cron_check_overdue.sh
# Every 6 hours:        0 */6 * * * /path/to/project/cron_check_overdue.sh
# Every 3 hours:        0 */3 * * * /path/to/project/cron_check_overdue.sh
# Every hour:           0 * * * * /path/to/project/cron_check_overdue.sh
# Weekdays at 8 AM:     0 8 * * 1-5 /path/to/project/cron_check_overdue.sh

# To add to crontab:
# 1. Go to Settings in the web interface and configure your preferred schedule
# 2. Copy the cron command shown in the settings
# 3. Open crontab editor: crontab -e
# 4. Add the copied line
# 5. Save and exit
