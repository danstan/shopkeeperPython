import unittest
import sys
import os
import json # Not strictly needed for tests, but good for context

# Adjust the path to import from the parent directory (shopkeeperPython)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# This import will initialize app.py's global game_manager_instance,
# whose _print output will go to its own output_stream (a StringIO).
# We are only testing the return value of parse_action_details here.
from shopkeeperPython.app import parse_action_details

class TestAppUtils(unittest.TestCase):

    def test_parse_valid_json_details(self):
        """Test parsing a valid JSON string with multiple details."""
        details_str = '{"item_name": "Potion of Healing", "quantity": 2, "target": "Player"}'
        expected_dict = {"item_name": "Potion of Healing", "quantity": 2, "target": "Player"}
        self.assertEqual(parse_action_details(details_str), expected_dict)

    def test_parse_empty_json_object(self):
        """Test parsing an empty JSON object string: '{}'."""
        details_str = '{}'
        expected_dict = {}
        self.assertEqual(parse_action_details(details_str), expected_dict)

    def test_parse_empty_string(self):
        """Test parsing an empty string: ''."""
        details_str = ''
        expected_dict = {}
        self.assertEqual(parse_action_details(details_str), expected_dict)

    def test_parse_none_input(self):
        """Test parsing a None input."""
        details_str = None
        expected_dict = {}
        # The function has `if not details_str:` which handles None.
        self.assertEqual(parse_action_details(details_str), expected_dict)

    def test_parse_string_null(self):
        """Test parsing the string 'null'."""
        details_str = 'null'
        # json.loads('null') results in None. The function should then return {}.
        expected_dict = {}
        self.assertEqual(parse_action_details(details_str), expected_dict)

    def test_parse_malformed_json_incomplete(self):
        """Test parsing an incomplete (malformed) JSON string."""
        details_str = '{"item_name": "Potion"' # Missing closing brace and quotes
        expected_dict = {}
        self.assertEqual(parse_action_details(details_str), expected_dict)

    def test_parse_malformed_json_syntax_error(self):
        """Test parsing JSON with a syntax error (e.g., trailing comma)."""
        details_str = '{"item_name": "Potion", "quantity": 2,}' # Trailing comma can be an issue for some parsers
        # Python's json.loads is generally tolerant of trailing commas in objects/arrays.
        # However, if it were strict, this would be an error. Let's test for strictness.
        # If json.loads is tolerant, this should pass:
        # expected_dict = {"item_name": "Potion", "quantity": 2}
        # If json.loads is strict (which it is by default for trailing commas in standard JSON), it's an error.
        # The implementation prints to log and returns {}.
        expected_dict = {}
        self.assertEqual(parse_action_details(details_str), expected_dict)


    def test_parse_json_array_not_dict(self):
        """Test parsing a valid JSON array, which is not a dictionary."""
        details_str = '[1, 2, 3]'
        # The function checks `isinstance(details_dict, dict)`
        expected_dict = {}
        self.assertEqual(parse_action_details(details_str), expected_dict)

    def test_parse_json_primitive_string_not_dict(self):
        """Test parsing a valid JSON string primitive, which is not a dictionary."""
        details_str = '"just_a_string"'
        # json.loads('"just_a_string"') -> "just_a_string"
        # The function checks `isinstance(details_dict, dict)`
        expected_dict = {}
        self.assertEqual(parse_action_details(details_str), expected_dict)

    def test_parse_non_string_input_integer(self):
        """Test parsing a non-string input like an integer."""
        details_input = 12345
        expected_dict = {}
        # This should trigger the TypeError exception handling in parse_action_details
        self.assertEqual(parse_action_details(details_input), expected_dict)

if __name__ == '__main__':
    unittest.main()
