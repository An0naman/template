#!/usr/bin/env python3
"""
Test script for ntfy push notifications
Run this to test your ntfy setup without starting the full app
"""

import requests
import sys
import json

def test_ntfy_notification(topic, server_url="https://ntfy.sh", auth_token=None):
    """Test sending a notification via ntfy"""
    
    if not topic:
        print("Error: Topic name is required")
        return False
    
    url = f"{server_url.rstrip('/')}/{topic}"
    
    headers = {
        "Title": "Test from Your App 🎉",
        "Priority": "3",
        "Tags": "📱,test",
        "Content-Type": "text/plain"
    }
    
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    
    message = "Hello! This is a test notification from your app. If you received this, ntfy is working correctly! 🚀"
    
    try:
        print(f"Sending test notification to topic '{topic}' on server '{server_url}'...")
        
        response = requests.post(
            url,
            data=message,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Success! Test notification sent successfully.")
            print(f"Check your ntfy app for the notification on topic '{topic}'")
            return True
        else:
            print(f"❌ Failed to send notification.")
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error sending notification: {e}")
        return False

def main():
    print("🔔 ntfy Test Script")
    print("==================")
    
    # Get topic from command line or prompt user
    if len(sys.argv) > 1:
        topic = sys.argv[1]
    else:
        topic = input("Enter your ntfy topic name: ").strip()
    
    if not topic:
        print("No topic provided. Exiting.")
        sys.exit(1)
    
    # Optional server URL
    server_url = "https://ntfy.sh"
    if len(sys.argv) > 2:
        server_url = sys.argv[2]
    
    # Optional auth token
    auth_token = None
    if len(sys.argv) > 3:
        auth_token = sys.argv[3]
    
    success = test_ntfy_notification(topic, server_url, auth_token)
    
    if success:
        print("\n🎉 ntfy is working! You can now configure it in your app.")
        print("\nNext steps:")
        print("1. Go to your app's settings")
        print("2. Navigate to Push Notifications")
        print(f"3. Enter '{topic}' as your topic name")
        print("4. Save the configuration")
        print("5. Test from within the app")
    else:
        print("\n❌ There was an issue with the test.")
        print("\nTroubleshooting:")
        print("1. Check your internet connection")
        print("2. Verify the topic name is correct")
        print("3. If using a custom server, check the URL")
        print("4. If using authentication, verify the token")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
