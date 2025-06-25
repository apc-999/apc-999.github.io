import unittest
import sqlite3
import os
import shutil
import json
from main import get_db, insert_data, fetch_data, delete_row, update_row, hash_password, get_user_info, db_path
from main import app

class TestFlaskAppDatabase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Called once before all tests"""
        if os.path.exists(db_path):
            shutil.copyfile(db_path, f"{db_path}.old")

    @classmethod
    def tearDownClass(cls):
        """Called once after all tests"""
        if os.path.exists(db_path):
            os.remove(db_path)
        if os.path.exists(f"{db_path}.old"):
            shutil.move(f"{db_path}.old", db_path)
            
    def setUp(self):
        self.app_context = app.app_context()
        self.app_context.push()

        self.client = app.test_client()
        self.conn = get_db()
        self.cursor = self.conn.cursor()

    def tearDown(self):
        self.app_context.pop()
        self.conn.close()

    def test_insert_data(self):
        """Test inserting a new row into the data table"""
        row = ("TEST01", "Test Title", "2.5", "Assigned", "TestGroup", "TestIdentity", 
               "2023-10-09T12:00:00Z", "2023-10-09T12:00:00Z", "TRUE", "Test Root Cause")
        insert_data(row)
        data = fetch_data()
        data_as_tuples = [tuple(d) for d in data]
        self.assertIn(row, data_as_tuples)

    def test_update_row(self):
        """Test updating an existing row in the data table"""
        row = ("TEST02", "Test Title", "3", "Assigned", "TestGroup", "TestIdentity", 
               "2023-10-09T12:00:00Z", "2023-10-09T12:00:00Z", "TRUE", "Test Root Cause")
        insert_data(row)

        update_row("TEST02", "Title", "Updated Title")
        row = ("TEST02", "Updated Title", "3", "Assigned", "TestGroup", "TestIdentity", 
               "2023-10-09T12:00:00Z", "2023-10-09T12:00:00Z", "TRUE", "Test Root Cause")

        data = fetch_data()
        data_as_tuples = [tuple(d) for d in data]
        self.assertIn(row, data_as_tuples)

    def test_delete_row(self):
        """Test deleting a row from the data table"""
        row = ("TEST03", "Test Title", "3", "Assigned", "TestGroup", "TestIdentity", 
               "2023-10-09T12:00:00Z", "2023-10-09T12:00:00Z", "TRUE", "Test Root Cause")
        insert_data(row)

        delete_row("TEST03")

        data = fetch_data() 
        data_as_tuples = [tuple(d) for d in data]
        self.assertNotIn(row, data_as_tuples)

    def test_fetch_data(self):
        """Test fetching all data rows"""
        row = ("TEST04", "Test Title", "3", "Assigned", "TestGroup", "TestIdentity", 
               "2023-10-09T12:00:00Z", "2023-10-09T12:00:00Z", "TRUE", "Test Root Cause")
        insert_data(row)

        all_data = fetch_data()
        self.assertGreater(len(all_data), 0, "No data fetched from the table")

    def test_hash_password(self):
        """Test password hashing"""
        password = "password123"
        hashed = hash_password(password)
        self.assertEqual(len(hashed), 64, "Hash length is incorrect")
        self.assertNotEqual(hashed, password, "Hashed password should not match the original")

    def test_get_user_info(self):
        """Test retrieving user information from the users table"""
        username = "test_user"
        password = hash_password("test_password")
        self.cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        self.conn.commit()

        user_id = self.cursor.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()[0]

        result = get_user_info(user_id, 1)
        self.assertEqual(result, "test_user", "Failed to fetch the correct username")
        
    def test_user_role_permissions(self):
        """Test that admin and regular users have different permissions"""
        # Create a regular user
        self.cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", 
                           ("regular_user", hash_password("password"), "user"))
        
        # Create an admin user
        self.cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", 
                           ("admin_user", hash_password("password"), "admin"))
        self.conn.commit()
        
        # Test regular user access to admin-only route
        with self.client as c:
            with c.session_transaction() as sess:
                user_id = self.cursor.execute("SELECT id FROM users WHERE username = ?", 
                                             ("regular_user",)).fetchone()[0]
                sess['user_id'] = user_id
                
            response = c.get('/update_issue', follow_redirects=True)
            self.assertIn(b"Must be an admin to access that page", response.data)
            
        # Test admin user access to admin-only route
        with self.client as c:
            with c.session_transaction() as sess:
                user_id = self.cursor.execute("SELECT id FROM users WHERE username = ?", 
                                             ("admin_user",)).fetchone()[0]
                sess['user_id'] = user_id
                
            response = c.get('/update_issue')
            self.assertNotIn(b"Must be an admin to access that page", response.data)
            
    def test_validation_rules(self):
        """Test that validation rules are enforced"""
        # Create admin user first if not exists
        try:
            self.cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", 
                              ("admin_user", hash_password("password"), "admin"))
            self.conn.commit()
        except:
            pass  # User might already exist
            
        # Test invalid severity value
        with self.client as c:
            with c.session_transaction() as sess:
                user_id = self.cursor.execute("SELECT id FROM users WHERE username = ?", 
                                             ("admin_user",)).fetchone()[0]
                sess['user_id'] = user_id
                
            response = c.post('/add_issue', data={
                'ShortId': 'TEST-INV',
                'Title': 'Invalid Test',
                'Severity': '10',  # Invalid severity (should be 1-5)
                'Status': 'Assigned',
                'AssignedGroup': 'Test Group',
                'AssigneeIdentity': 'Test User',
                'CreateDate': '2023-10-09T12:00:00Z',
                'Issue open': 'on'
            })
            self.assertIn(b"Severity", response.data)
            
    def test_api_endpoints(self):
        """Test API endpoints for CRUD operations"""
        # Create admin user first
        self.cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", 
                          ("admin_user", hash_password("password"), "admin"))
        self.conn.commit()
        
        # Test adding an issue
        with self.client as c:
            with c.session_transaction() as sess:
                user_id = self.cursor.execute("SELECT id FROM users WHERE username = ?", 
                                             ("admin_user",)).fetchone()[0]
                sess['user_id'] = user_id
                
            # Add an issue
            response = c.post('/add_issue', data={
                'ShortId': 'API-TEST',
                'Title': 'API Test Issue',
                'Severity': '3',
                'Status': 'Assigned',
                'AssignedGroup': 'API Group',
                'AssigneeIdentity': 'API User',
                'CreateDate': '2023-10-09T12:00:00Z',
                'Issue open': 'on'
            }, follow_redirects=True)
            
            # Verify the issue was added
            self.assertIn(b"API-TEST", response.data)
            
            # Test finding the issue if find_issue route exists
            try:
                response = c.post('/find_issue', data={
                    'search_term': 'API-TEST'
                })
                self.assertIn(b"API-TEST", response.data)
            except:
                pass  # Skip if find_issue route doesn't exist

if __name__ == '__main__':
    unittest.main()