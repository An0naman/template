#!/usr/bin/env python3
"""
Test script to verify automatic dark mode functionality
"""

from datetime import datetime, time

def is_dark_mode_time(start_time_str, end_time_str):
    """
    Determine if current time falls within dark mode hours
    
    Args:
        start_time_str: Dark mode start time in HH:MM format (e.g., "18:00")
        end_time_str: Dark mode end time in HH:MM format (e.g., "06:00")
    
    Returns:
        bool: True if current time is within dark mode hours
    """
    try:
        current_time = datetime.now().time()
        
        # Parse start and end times
        start_hour, start_min = map(int, start_time_str.split(':'))
        end_hour, end_min = map(int, end_time_str.split(':'))
        
        start_time = time(start_hour, start_min)
        end_time = time(end_hour, end_min)
        
        # Handle overnight periods (e.g., 18:00 to 06:00)
        if start_time > end_time:
            # Dark mode spans midnight
            return current_time >= start_time or current_time < end_time
        else:
            # Dark mode within same day
            return start_time <= current_time < end_time
            
    except (ValueError, AttributeError):
        # Default to light mode if time parsing fails
        return False

def test_auto_dark_mode():
    """Test the automatic dark mode time checking function"""
    
    print("🌙 Testing Automatic Dark Mode Time Function")
    print("=" * 50)
    
    # Test cases
    test_cases = [
        # (start_time, end_time, expected_description)
        ("18:00", "06:00", "Evening to morning (overnight)"),
        ("22:00", "07:00", "Late night to morning"),
        ("09:00", "17:00", "Morning to afternoon (same day)"),
        ("06:00", "18:00", "Morning to evening (same day)"),
        ("00:00", "23:59", "Midnight to midnight (all day)"),
    ]
    
    current_time = datetime.now().time()
    print(f"Current time: {current_time.strftime('%H:%M')}")
    print()
    
    for start_time, end_time, description in test_cases:
        result = is_dark_mode_time(start_time, end_time)
        status = "🌙 DARK" if result else "☀️ LIGHT"
        print(f"{description}:")
        print(f"  Dark mode: {start_time} - {end_time}")
        print(f"  Current result: {status}")
        print()
    
    print("🔍 Testing Current Settings")
    print("-" * 30)
    
    # Test with common settings
    common_settings = [
        ("18:00", "06:00"),  # 6 PM to 6 AM
        ("20:00", "08:00"),  # 8 PM to 8 AM
        ("22:00", "07:00"),  # 10 PM to 7 AM
    ]
    
    for start, end in common_settings:
        result = is_dark_mode_time(start, end)
        status = "🌙 DARK MODE" if result else "☀️ LIGHT MODE"
        print(f"Settings {start}-{end}: {status}")
    
    print()
    print("✅ Test completed!")

if __name__ == "__main__":
    test_auto_dark_mode()
