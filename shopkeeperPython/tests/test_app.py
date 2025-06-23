import unittest
import copy
import html # Import the html module for unescaping
from werkzeug.security import generate_password_hash # Added import
import json # Added for json.dumps
from unittest.mock import patch

from shopkeeperPython.app import app, users, user_characters, graveyard, is_character_name_taken
from shopkeeperPython.game.character import Character

# Helper to initialize a default character dict for tests
def create_default_char_dict(name, level=1, is_dead=False):
    return {
        "name": name,
        "stats": {"STR": 10, "DEX": 10, "CON": 10, "INT": 10, "WIS": 10, "CHA": 10},
        "stat_bonuses": {"STR": 0, "DEX": 0, "CON": 0, "INT": 0, "WIS": 0, "CHA": 0},
        "ac_bonus": 0,
        "level": level,
        "xp": 0,
        "pending_xp": 0,
        "base_max_hp": 10, # Simplified
        "hp": 10,
        "hit_dice": level,
        "max_hit_dice": level,
        "attunement_slots": 3,
        "attuned_items": [], # Corrected key from "attuned_.items"
        "exhaustion_level": 0,
        "inventory": [],
        "gold": 100,
        "skill_points_to_allocate": 0,
        "speed": 30,
        "is_dead": is_dead,
        "current_town_name": "Starting Village"
    }

class TestApp(unittest.TestCase):
    def setUp(self):
        """Set up test client and backup original data."""
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False # For Flask-WTF forms if used; good practice for testing
        app.config['SECRET_KEY'] = 'test_secret_key_for_session' # Ensure session works
        self.client = app.test_client()

        # Backup original data stores
        self.original_users = copy.deepcopy(users)
        self.original_user_characters = copy.deepcopy(user_characters)
        self.original_graveyard = copy.deepcopy(graveyard)

        # Clear and reset data stores for each test for isolation
        users.clear()
        user_characters.clear()
        graveyard.clear()

        # Add a default test user for routes that require login
        # Password must be hashed for login to succeed
        hashed_password = generate_password_hash('password123')
        users['testuser'] = {
            'password': hashed_password,
            'google_id': None, # Ensure new user structure is matched
            'email_google': None,
            'display_name_google': None
        }
        user_characters['testuser'] = []
        graveyard['testuser'] = []


    def tearDown(self):
        """Restore original data and clear session effects."""
        users.clear()
        users.update(self.original_users)
        user_characters.clear()
        user_characters.update(self.original_user_characters)
        graveyard.clear()
        graveyard.update(self.original_graveyard)
        # Session is typically handled by the test client context,
        # but explicit clearing can be done if issues arise.
        # with self.client.session_transaction() as sess:
        #     sess.clear()

    def test_is_character_name_taken_direct_call(self):
        """Test the is_character_name_taken helper function directly."""
        sample_user_chars = {
            'user1': [create_default_char_dict(name="Hero1"), create_default_char_dict(name="Mage1")],
            'user2': [create_default_char_dict(name="Warrior2")]
        }
        sample_graveyard = {
            'user1': [create_default_char_dict(name="Fallen1", is_dead=True)],
            'user3': [create_default_char_dict(name="Ghost3", is_dead=True)]
        }

        self.assertTrue(is_character_name_taken("Hero1", sample_user_chars, sample_graveyard))
        self.assertTrue(is_character_name_taken("hero1", sample_user_chars, sample_graveyard)) # Case-insensitive
        self.assertTrue(is_character_name_taken("Mage1", sample_user_chars, sample_graveyard))
        self.assertTrue(is_character_name_taken("Fallen1", sample_user_chars, sample_graveyard))
        self.assertTrue(is_character_name_taken("fallen1", sample_user_chars, sample_graveyard)) # Case-insensitive
        self.assertTrue(is_character_name_taken("Ghost3", sample_user_chars, sample_graveyard))
        self.assertFalse(is_character_name_taken("UniqueName", sample_user_chars, sample_graveyard))
        self.assertFalse(is_character_name_taken("Hero2", sample_user_chars, sample_graveyard))

    def test_create_character_name_uniqueness_route(self):
        """Test character name uniqueness via the /create_character route."""
        # Setup: A character "TakenName" already exists for 'testuser'
        user_characters['testuser'] = [create_default_char_dict(name="TakenName")]

        with self.client.session_transaction() as sess:
            sess['username'] = 'testuser'
            # Base stats for creation, actual values don't matter much for name check
            sess['character_creation_stats'] = {'stats': Character.roll_all_stats(), 'reroll_used': False}

        # Attempt to create character with "TakenName"
        # Client makes a POST request to /create_character with data for new character
        response_taken = self.client.post('/create_character', data={'character_name': 'TakenName'}, follow_redirects=True)
        self.assertEqual(response_taken.status_code, 200) # Should redirect then land on a 200 page
        # Decode response data to string and unescape HTML entities
        response_data_str = html.unescape(response_taken.data.decode('utf-8'))
        self.assertIn("Character name 'TakenName' is already taken.", response_data_str) # Check for flash message

        # Verify "TakenName" was not added again (still only 1 character for testuser)
        self.assertEqual(len(user_characters['testuser']), 1)
        self.assertEqual(user_characters['testuser'][0]['name'], 'TakenName')

        # Attempt to create character with "UniqueNewName"
        response_unique = self.client.post('/create_character', data={'character_name': 'UniqueNewName'}, follow_redirects=True)
        self.assertEqual(response_unique.status_code, 200)
        response_unique_data_str = html.unescape(response_unique.data.decode('utf-8'))
        self.assertNotIn("is already taken", response_unique_data_str) # No error flash

        # Verify "UniqueNewName" WAS added
        self.assertEqual(len(user_characters['testuser']), 2)
        # Names can be "TakenName", "UniqueNewName" or vice-versa in list
        created_names = sorted([c['name'] for c in user_characters['testuser']])
        self.assertIn('TakenName', created_names)
        self.assertIn('UniqueNewName', created_names)


    @patch('shopkeeperPython.game.character.Character.reroll_single_stat')
    def test_character_reroll_flow_and_creation(self, mock_reroll_single_stat):
        """Test stat reroll flow and character creation with rerolled stats."""
        with self.client.session_transaction() as sess:
            sess['username'] = 'testuser'
            # Initial stats for character creation
            sess['character_creation_stats'] = {
                'stats': {'STR': 10, 'DEX': 12, 'CON': 11, 'INT': 9, 'WIS': 13, 'CHA': 14},
                'reroll_used': False
            }

        # 1. Successful Reroll (STR)
        mock_reroll_single_stat.return_value = 15 # All rerolls will return 15 for this part
        response_reroll_str = self.client.post('/reroll_stat/STR', follow_redirects=True)
        self.assertEqual(response_reroll_str.status_code, 200)
        self.assertIn(b"STR rerolled to 15!", response_reroll_str.data) # Check flash

        with self.client.session_transaction() as sess:
            self.assertTrue(sess['character_creation_stats']['reroll_used'])
            self.assertEqual(sess['character_creation_stats']['stats']['STR'], 15)
            self.assertEqual(sess['character_creation_stats']['stats']['DEX'], 12) # DEX Unchanged

        # 2. Attempt Second Reroll (DEX) - Should Fail
        mock_reroll_single_stat.return_value = 16 # Change mock for DEX attempt
        response_reroll_dex = self.client.post('/reroll_stat/DEX', follow_redirects=True)
        self.assertEqual(response_reroll_dex.status_code, 200)
        self.assertIn(b"You have already used your reroll", response_reroll_dex.data) # Check flash

        with self.client.session_transaction() as sess:
            self.assertTrue(sess['character_creation_stats']['reroll_used']) # Still true
            self.assertEqual(sess['character_creation_stats']['stats']['STR'], 15) # STR remains rerolled
            self.assertEqual(sess['character_creation_stats']['stats']['DEX'], 12) # DEX still original, not 16

        # 3. Create Character - Should use rerolled STR (15) and original other stats
        char_name_for_creation = "RerolledHero"
        response_create = self.client.post('/create_character', data={'character_name': char_name_for_creation}, follow_redirects=True)
        self.assertEqual(response_create.status_code, 200)
        # Check if character was created successfully

        expected_message = f"Character {char_name_for_creation} (user: testuser) created and game world prepared." # Expected longer message
        self.assertIn(expected_message, response_create.data.decode('utf-8'))


        self.assertTrue(any(c['name'] == char_name_for_creation for c in user_characters['testuser']))
        created_char_data = next((c for c in user_characters['testuser'] if c['name'] == char_name_for_creation), None)
        self.assertIsNotNone(created_char_data)
        self.assertEqual(created_char_data['stats']['STR'], 15) # Rerolled STR
        self.assertEqual(created_char_data['stats']['DEX'], 12) # Original DEX
        self.assertEqual(created_char_data['stats']['CON'], 11) # Original CON

        # Ensure session stats for creation are cleared after successful creation
        with self.client.session_transaction() as sess:
            self.assertNotIn('character_creation_stats', sess)
            self.assertNotIn('character_creation_name', sess) # Also check name is cleared

    # --- Helper function for character creation setup ---
    def _login_and_go_to_char_creation(self, username='testuser'):
        with self.client.session_transaction() as sess:
            sess['username'] = username
        return self.client.get('/?action=create_new_char', follow_redirects=True)

    # --- Tests for Character Creation Flash Messages ---
    def test_char_creation_initial_flash(self):
        """Test initial flash messages on character creation page."""
        response = self._login_and_go_to_char_creation()
        self.assertEqual(response.status_code, 200)
        response_data_str = response.data.decode('utf-8')

        # Check for the informational "Stats rolled..." message
        self.assertIn("Initial stats rolled and saved to session.", response_data_str) # Updated expected message
        # Check that no common error messages are present
        self.assertNotIn("issue with character creator", response_data_str.lower()) # Generic check
        self.assertNotIn("Failed to initialize game", response_data_str)
        self.assertNotIn("name already taken", response_data_str)
        self.assertNotIn("maximum", response_data_str.lower()) # For max characters

    def test_char_creation_name_taken_flash(self):
        """Test flash message when character name is already taken."""
        user_characters['testuser'] = [create_default_char_dict(name="TakenName")]
        self._login_and_go_to_char_creation() # To set up session stats

        with self.client.session_transaction() as sess: # Ensure creation stats are in session
            if 'character_creation_stats' not in sess:
                 sess['character_creation_stats'] = {'stats': Character.roll_all_stats(), 'reroll_used': False}

        response = self.client.post('/create_character', data={'character_name': 'TakenName'}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        # Decode and unescape HTML entities from response data
        response_data_str = html.unescape(response.data.decode('utf-8'))
        self.assertIn("Character name 'TakenName' is already taken.", response_data_str)

    def test_char_creation_max_chars_flash(self):
        """Test flash message when maximum characters are reached."""
        # Fill up character slots for 'testuser' (assuming MAX_CHARS_PER_USER is 2 from app.py)
        from shopkeeperPython.app import MAX_CHARS_PER_USER # Import for clarity
        user_characters['testuser'] = [create_default_char_dict(name=f"Char{i}") for i in range(MAX_CHARS_PER_USER)]

        response = self._login_and_go_to_char_creation() # This attempts to go to creation page
        self.assertEqual(response.status_code, 200)
        self.assertIn(f"You cannot create more than {MAX_CHARS_PER_USER} active characters.", response.data.decode('utf-8'))

    # --- Test for Stat Display Order (Character Creation) ---
    def test_char_creation_stat_order(self):
        """Verify stats are displayed in the correct order on character creation."""
        response = self._login_and_go_to_char_creation()
        self.assertEqual(response.status_code, 200)
        response_data_str = response.data.decode('utf-8')

        # Find the stats container (rough check, ideally use a parser)
        stats_section_start = response_data_str.find('<div id="stats_container">')
        # Find the start of the next major element after the stats container
        stats_section_end = response_data_str.find('<div class="character-creation-submit-container">', stats_section_start)
        stats_html = response_data_str[stats_section_start:stats_section_end]

        self.assertTrue(stats_section_start != -1, "Stats container start not found in HTML")
        self.assertTrue(stats_section_end != -1, "End marker for stats section not found in HTML")

        last_pos = -1
        for stat_name in Character.STAT_NAMES:
            current_pos = stats_html.find(f"<span>{stat_name}:")
            self.assertTrue(current_pos != -1, f"Stat {stat_name} not found in displayed stats.")
            self.assertGreater(current_pos, last_pos, f"Stat {stat_name} is out of order.")
            last_pos = current_pos

    # --- Test for Character Name Persistence (Character Creation) ---
    def test_char_creation_name_persistence_on_reroll(self):
        """Test that character name persists after a stat reroll."""
        self._login_and_go_to_char_creation() # Initial visit to setup session stats

        test_char_name = "MyPersistentHero"
        # Simulate rerolling STR, passing the character_name as the JS would
        response = self.client.post('/reroll_stat/STR',
                                     data={'character_name': test_char_name},
                                     follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        response_data_str = response.data.decode('utf-8')

        # Check if the input field has the correct value
        # Example: <input type="text" id="character_name" name="character_name" value="MyPersistentHero" required>
        self.assertIn(f'id="character_name"', response_data_str)
        self.assertIn(f'name="character_name"', response_data_str)
        self.assertIn(f'value="{test_char_name}"', response_data_str)

    # --- Helper for Action Tests ---
    def _setup_user_and_character_for_actions(self, char_name="ActionHero", username="testuser"):
        # Ensure user is logged in
        with self.client.session_transaction() as sess:
            sess['username'] = username
            # Clear any potential leftover creation session data
            sess.pop('character_creation_stats', None)
            sess.pop('character_creation_name', None)

        # Create and select a character for the user
        char_dict = create_default_char_dict(name=char_name)
        user_characters[username] = [char_dict]

        with self.client.session_transaction() as sess:
            sess['selected_character_slot'] = 0

        # The goal is to ensure that when an action is performed,
        # the app's before_request_setup() correctly initializes g.player_char and g.game_manager.
        # We do this by setting up the session and user_characters data.
        # No direct manipulation of app's g.player_char or g.game_manager from the test.

        # To verify that the setup within the app context works as expected during an action,
        # we can make a preliminary request (e.g., to display_game_output) that would trigger
        # before_request_setup. Then, subsequent action posts will use that context.
        # Alternatively, actions themselves will trigger before_request_setup.

        # The main check will be if the actions themselves behave as expected,
        # implying that g.player_char and g.game_manager were correctly set up by the app.
        return char_name


    # --- Basic Action Tests ---
    def test_action_talk_to_self(self):
        """Test the 'talk_to_self' action."""
        char_name = self._setup_user_and_character_for_actions()

        # Make the action request. The before_request hook in app.py should handle
        # setting up g.player_char and g.game_manager based on the session.
        response = self.client.post('/action', data={'action_name': 'talk_to_self'}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        # The action result is popped from session by display_game_output and rendered in the page.
        # So, we check the response data from the final GET request (due to follow_redirects=True).
        response_html = response.data.decode('utf-8')
        # Assuming the action result is rendered into a div with id "action-result-message"
        # or generally available in the HTML if the popup is to be shown.
        self.assertIn(f"  {char_name} mutters.", response_html)


    def test_action_explore_town(self):
        """Test the 'explore_town' action."""
        char_name = self._setup_user_and_character_for_actions()

        response = self.client.post('/action', data={'action_name': 'explore_town'}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        response_html = response.data.decode('utf-8')
        self.assertIn(f"  {char_name} explores ", response_html) # Made assertion more general


    def test_action_wait(self):
        """Test the 'wait' action."""
        char_name = self._setup_user_and_character_for_actions()

        response = self.client.post('/action', data={'action_name': 'wait'}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        response_html = response.data.decode('utf-8')
        self.assertIn(f"  {char_name} waits.", response_html)

    @patch('shopkeeperPython.game.game_manager.random.random')
    @patch('shopkeeperPython.game.game_manager.random.choice')
    def test_action_explore_town_find_gold(self, mock_game_random_choice, mock_game_random_random):
        """Test explore_town action results in finding gold."""
        char_name = self._setup_user_and_character_for_actions()
        username = 'testuser' # Matches the user in _setup

        # Ensure the 20% chance to find something passes
        mock_game_random_random.return_value = 0.1
        # Configure random.choice to return a gold find
        gold_find_amount = 10
        mock_game_random_choice.return_value = {"type": "gold", "amount": gold_find_amount}

        # Get initial gold from the character's data
        initial_char_data = user_characters[username][0] # Assuming single character at slot 0
        initial_gold = initial_char_data.get('gold', 0)

        response = self.client.post('/action', data={'action_name': 'explore_town'}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        response_html = response.data.decode('utf-8')

        # Check for the "Found X gold!" message
        self.assertIn(f"Found {gold_find_amount} gold!", response_html)

        # Verify character's gold has increased
        updated_char_data = user_characters[username][0] # Reload character data
        self.assertEqual(updated_char_data.get('gold', 0), initial_gold + gold_find_amount)

    @patch('shopkeeperPython.game.game_manager.random.random')
    @patch('shopkeeperPython.game.game_manager.random.choice')
    def test_action_explore_town_find_item(self, mock_game_random_choice, mock_game_random_random):
        """Test explore_town action results in finding a specific item."""
        char_name = self._setup_user_and_character_for_actions()
        username = 'testuser'

        mock_game_random_random.return_value = 0.1 # Ensure find branch is taken
        item_to_find = {
            "type": "item", "name": "Shiny Pebble",
            "description": "A smooth, oddly shiny pebble.",
            "base_value": 1, "item_type": "trinket", "quality": "Common", "quantity": 1
        }
        mock_game_random_choice.return_value = item_to_find

        response = self.client.post('/action', data={'action_name': 'explore_town'}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        response_html = response.data.decode('utf-8')

        self.assertIn(f"Found {item_to_find['quantity']}x {item_to_find['name']}!", response_html)

        updated_char_data = user_characters[username][0]
        found_in_inventory = any(item['name'] == item_to_find['name'] for item in updated_char_data.get('inventory', []))
        self.assertTrue(found_in_inventory, f"{item_to_find['name']} not found in character inventory.")

    def test_action_travel_to_valid_town(self):
        """Test traveling to a valid different town."""
        char_name = self._setup_user_and_character_for_actions(char_name="Traveler", username="testuser")
        username = "testuser"

        initial_char_data = user_characters[username][0]
        self.assertEqual(initial_char_data['current_town_name'], "Starting Village")

        action_details = {'town_name': "Steel Flow City"}
        response = self.client.post('/action', data={'action_name': 'travel_to_town', 'action_details': json.dumps(action_details)}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        response_html = response.data.decode('utf-8')

        self.assertIn("Arrived in Steel Flow City.", response_html)
        updated_char_data = user_characters[username][0]
        self.assertEqual(updated_char_data['current_town_name'], "Steel Flow City")

    def test_action_travel_to_current_town(self):
        """Test attempting to travel to the current town."""
        char_name = self._setup_user_and_character_for_actions(char_name="Homebody", username="testuser")
        username = "testuser"

        initial_char_data = user_characters[username][0]
        self.assertEqual(initial_char_data['current_town_name'], "Starting Village")

        action_details = {'town_name': "Starting Village"}
        response = self.client.post('/action', data={'action_name': 'travel_to_town', 'action_details': json.dumps(action_details)}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        response_html = response.data.decode('utf-8')

        self.assertIn("Already in Starting Village.", response_html)
        updated_char_data = user_characters[username][0]
        self.assertEqual(updated_char_data['current_town_name'], "Starting Village")

    def test_action_travel_to_invalid_town(self):
        """Test attempting to travel to an invalid town."""
        char_name = self._setup_user_and_character_for_actions(char_name="Lost Adventurer", username="testuser")
        username = "testuser"

        initial_char_data = user_characters[username][0]
        self.assertEqual(initial_char_data['current_town_name'], "Starting Village")

        action_details = {'town_name': "Atlantis"} # An invalid town
        response = self.client.post('/action', data={'action_name': 'travel_to_town', 'action_details': json.dumps(action_details)}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        response_html = response.data.decode('utf-8')

        self.assertIn("Cannot travel to unknown town: Atlantis.", response_html)
        updated_char_data = user_characters[username][0]
        self.assertEqual(updated_char_data['current_town_name'], "Starting Village")


if __name__ == '__main__':
    unittest.main()
