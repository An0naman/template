#!/bin/bash
# Cron script to run the overdue end date checker
# This script should be added to your crontab to run daily

# Set the project directory (change this to your actual project path)
PROJECT_DIR="/home/an0naman/Documents/GitHub/template"

# Change to project directory
cd "$PROJECT_DIR"

# Run the overdue checker with the virtual environment Python
"$PROJECT_DIR/.venv/bin/python" check_overdue_dates.py

# Example crontab entry (run daily at 9:00 AM):
# 0 9 * * * /path/to/your/project/cron_check_overdue.sh

# Example crontab entry (run every hour):
# 0 * * * * /path/to/your/project/cron_check_overdue.sh

# To add to crontab:
# 1. Open crontab editor: crontab -e
# 2. Add the line above (uncommented and with correct path)
# 3. Save and exit
