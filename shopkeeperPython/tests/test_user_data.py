import unittest
import os
import json
import sys

# Adjust the path to import from the shopkeeperPython directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Now import from app
from shopkeeperPython.app import load_data, save_users, users as app_users_global, USERS_FILE as APP_USERS_FILE_CONSTANT, generate_password_hash, check_password_hash

class TestUserDataMigration(unittest.TestCase):

    def setUp(self):
        # Define a name for a temporary test users file
        self.test_users_file = os.path.join(os.path.dirname(__file__), 'test_users_temp.json')
        # Store the original USERS_FILE path from app.py
        self.original_users_file_path = APP_USERS_FILE_CONSTANT
        # Temporarily override the USERS_FILE in the app module to use our test file
        # This requires the app module to allow this variable to be changed.
        # Assuming app.USERS_FILE can be patched or is accessible for modification.
        # For this test, we'll assume direct patching for simplicity of test setup.
        # A more robust way might involve dependency injection for USERS_FILE in load_data/save_users
        # or using unittest.mock.patch if app.USERS_FILE is accessed like app.config.USERS_FILE.

        # Since app.USERS_FILE is a global constant string, we can't directly patch its usage inside
        # functions like load_data unless those functions are refactored to receive it as an argument
        # or access it via a mutable config object.
        # For this subtask, we will proceed with the assumption that test_users_file will be used
        # by directly preparing and cleaning it up, and that load_data/save_users in app.py
        # will need to be modified to accept USERS_FILE as an argument for proper testing.
        #
        # **Correction for subtask**: The test will have to manually manage the file that app.load_data()
        # implicitly uses (APP_USERS_FILE_CONSTANT). So, we backup and replace this file.

        self.app_users_file_backup_path = APP_USERS_FILE_CONSTANT + ".bak"

        # Ensure no old backup exists
        if os.path.exists(self.app_users_file_backup_path):
            os.remove(self.app_users_file_backup_path)
        # Backup current USERS_FILE if it exists
        if os.path.exists(APP_USERS_FILE_CONSTANT):
            os.rename(APP_USERS_FILE_CONSTANT, self.app_users_file_backup_path)


    def tearDown(self):
        # Delete the temporary test users file if it was created by a test
        if os.path.exists(self.test_users_file):
            os.remove(self.test_users_file)

        # Restore the original USERS_FILE from backup
        if os.path.exists(self.app_users_file_backup_path):
            os.rename(self.app_users_file_backup_path, APP_USERS_FILE_CONSTANT)
        elif os.path.exists(APP_USERS_FILE_CONSTANT) and not os.path.exists(self.app_users_file_backup_path):
            # If backup was not created (e.g. original users.json didn't exist)
            # but a users.json was created by the test, remove it.
            os.remove(APP_USERS_FILE_CONSTANT)


    def test_load_data_migrates_old_format_and_saves(self):
        # 1. Prepare the temporary USERS_FILE with old and new format data
        # Ensure generate_password_hash returns string (or decode if bytes) for JSON
        hashed_new_pass_obj = generate_password_hash("newpass")
        hashed_new_pass_str = hashed_new_pass_obj # Werkzeug generate_password_hash returns str by default

        test_data = {
            "olduser1": "password123",
            "newuser1": {
                "password": hashed_new_pass_str,
                "google_id": None,
                "email_google": "new@example.com",
                "display_name_google": "New User"
            },
            "olduser2": "anotherpassword"
        }
        with open(APP_USERS_FILE_CONSTANT, 'w') as f:
            json.dump(test_data, f, indent=4)

        # 2. Reset global users dict in app.py before calling load_data
        # This is important because app_users_global is loaded at app import time.
        # For the test, we need load_data to populate it freshly.
        app_users_global.clear()

        # 3. Call load_data() from the app module
        load_data() # This will use APP_USERS_FILE_CONSTANT

        # 4. Assertions for app_users_global (the dictionary in app.py)
        self.assertIn("olduser1", app_users_global)
        self.assertIsInstance(app_users_global["olduser1"], dict)
        self.assertTrue(check_password_hash(app_users_global["olduser1"]["password"], "password123"))
        self.assertIsNone(app_users_global["olduser1"]["google_id"])
        self.assertIsNone(app_users_global["olduser1"]["email_google"])
        self.assertIsNone(app_users_global["olduser1"]["display_name_google"])

        self.assertIn("olduser2", app_users_global)
        self.assertIsInstance(app_users_global["olduser2"], dict)
        self.assertTrue(check_password_hash(app_users_global["olduser2"]["password"], "anotherpassword"))
        self.assertIsNone(app_users_global["olduser2"]["google_id"])

        self.assertIn("newuser1", app_users_global)
        self.assertIsInstance(app_users_global["newuser1"], dict)
        self.assertTrue(check_password_hash(app_users_global["newuser1"]["password"], "newpass"))
        self.assertEqual(app_users_global["newuser1"]["email_google"], "new@example.com")
        self.assertEqual(app_users_global["newuser1"]["display_name_google"], "New User")

        # 5. Assert that the USERS_FILE (APP_USERS_FILE_CONSTANT) has been updated
        with open(APP_USERS_FILE_CONSTANT, 'r') as f:
            saved_data = json.load(f)

        self.assertIn("olduser1", saved_data)
        self.assertIsInstance(saved_data["olduser1"], dict)
        self.assertTrue(check_password_hash(saved_data["olduser1"]["password"], "password123"))
        self.assertIsNone(saved_data["olduser1"]["google_id"])

        self.assertIn("olduser2", saved_data)
        self.assertIsInstance(saved_data["olduser2"], dict)
        self.assertTrue(check_password_hash(saved_data["olduser2"]["password"], "anotherpassword"))

        self.assertIn("newuser1", saved_data) # Check new user data is preserved
        self.assertTrue(check_password_hash(saved_data["newuser1"]["password"], "newpass"))
        self.assertEqual(saved_data["newuser1"]["email_google"], "new@example.com")

if __name__ == '__main__':
    unittest.main()
