#!/usr/bin/env python3
"""
Standalone script to check for overdue intended end dates and create notifications.
This script can be run as a cron job or scheduled task to automatically monitor for overdue entries.

Usage:
    python check_overdue_dates.py

This script should be run from the project root directory.
"""

import sys
import os
import logging
from datetime import datetime

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Try to import dependencies
try:
    from app import create_app
    from app.api.notifications_api import check_overdue_end_dates
except ImportError as e:
    print(f"Error importing dependencies: {e}")
    print("Make sure Flask and other dependencies are installed:")
    print("pip install -r requirements.txt")
    sys.exit(1)

def setup_logging():
    """Set up logging for the overdue check script"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/overdue_check.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    """Main function to run the overdue check"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Starting overdue end date check...")
    
    try:
        # Create Flask application context
        app = create_app()
        
        with app.app_context():
            # Run the overdue check
            notifications_created = check_overdue_end_dates()
            
            if notifications_created > 0:
                logger.info(f"Successfully created {notifications_created} overdue notifications.")
            else:
                logger.info("No overdue entries found or no new notifications needed.")
                
    except Exception as e:
        logger.error(f"Error running overdue check: {e}", exc_info=True)
        sys.exit(1)
    
    logger.info("Overdue end date check completed successfully.")

if __name__ == "__main__":
    main()
