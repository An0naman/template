import unittest
import json
import os
import sys

# Add the project root to the path so we can import the app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.db import init_db, get_db

class StravaSettingsTestCase(unittest.TestCase):
    def setUp(self):
        # Create a test app
        self.app = create_app({'TESTING': True, 'DATABASE_PATH': ':memory:'})
        self.client = self.app.test_client()
        
        # Initialize the database
        with self.app.app_context():
            init_db()

    def test_update_strava_settings(self):
        # Define the settings to update
        settings = {
            'strava_enabled': '1',
            'strava_client_id': '12345',
            'strava_client_secret': 'secret_key',
            'strava_refresh_token': 'refresh_token_value'
        }
        
        # Send PATCH request to update settings
        response = self.client.patch('/api/system_params', 
                                     data=json.dumps(settings),
                                     content_type='application/json')
        
        # Check if the update was successful
        self.assertEqual(response.status_code, 200)
        
        # Verify the settings were saved by fetching them back
        response = self.client.get('/api/system_params')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['strava_enabled'], '1')
        self.assertEqual(data['strava_client_id'], '12345')
        self.assertEqual(data['strava_client_secret'], 'secret_key')
        self.assertEqual(data['strava_refresh_token'], 'refresh_token_value')

if __name__ == '__main__':
    unittest.main()
