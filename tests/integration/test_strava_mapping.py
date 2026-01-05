import unittest
import json
import os
import sys

# Add the project root to the path so we can import the app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.db import init_db, get_db

class StravaMappingTestCase(unittest.TestCase):
    def setUp(self):
        # Create a test app
        self.app = create_app({'TESTING': True, 'DATABASE_PATH': ':memory:'})
        self.client = self.app.test_client()
        
        # Initialize the database
        with self.app.app_context():
            init_db()
            # Create a dummy entry type
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO EntryType (name, singular_label, plural_label) VALUES ('Run', 'Run', 'Runs')")
            conn.commit()

    def test_save_and_retrieve_mapping(self):
        # Define the mapping to update
        mapping = {"Run": "1", "Ride": "2"}
        settings = {
            'strava_activity_mapping': json.dumps(mapping)
        }
        
        # Send PATCH request to update settings
        response = self.client.patch('/api/system_params', 
                                     data=json.dumps(settings),
                                     content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        
        # Verify the settings were saved by fetching them back
        response = self.client.get('/api/system_params')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        saved_mapping_str = data.get('strava_activity_mapping')
        print(f"Saved mapping string: {saved_mapping_str}")
        
        saved_mapping = json.loads(saved_mapping_str)
        self.assertEqual(saved_mapping['Run'], '1')
        self.assertEqual(saved_mapping['Ride'], '2')

if __name__ == '__main__':
    unittest.main()
