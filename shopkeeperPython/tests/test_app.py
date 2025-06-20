import unittest
import copy
import html # Import the html module for unescaping
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
        users['testuser'] = {'password': 'password123'} # Simplified for testing login state
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
        self.assertIn("Stats rolled for new character! You can reroll one stat if you wish.", response_data_str)
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
        self.assertIn("Character name 'TakenName' is already taken.", response.data.decode('utf-8'))

    def test_char_creation_max_chars_flash(self):
        """Test flash message when maximum characters are reached."""
        # Fill up character slots for 'testuser' (assuming MAX_CHARS_PER_USER is 2 from app.py)
        from shopkeeperPython.app import MAX_CHARS_PER_USER # Import for clarity
        user_characters['testuser'] = [create_default_char_dict(name=f"Char{i}") for i in range(MAX_CHARS_PER_USER)]

        response = self._login_and_go_to_char_creation() # This attempts to go to creation page
        self.assertEqual(response.status_code, 200)
        self.assertIn(f"You cannot create more than {MAX_CHARS_PER_USER} characters.", response.data.decode('utf-8'))

    # --- Test for Stat Display Order (Character Creation) ---
    def test_char_creation_stat_order(self):
        """Verify stats are displayed in the correct order on character creation."""
        response = self._login_and_go_to_char_creation()
        self.assertEqual(response.status_code, 200)
        response_data_str = response.data.decode('utf-8')

        # Find the stats container (rough check, ideally use a parser)
        stats_section_start = response_data_str.find('<div id="stats_container">')
        stats_section_end = response_data_str.find('</div>', stats_section_start)
        stats_html = response_data_str[stats_section_start:stats_section_end]

        self.assertTrue(stats_section_start != -1 and stats_section_end != -1, "Stats container not found in HTML")

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

        # Crucially, ensure the GameManager is set up for this character.
        # This simulates what happens when display_game_output successfully loads a character.
        # We need to access the global game_manager_instance from the app context.
        from shopkeeperPython.app import game_manager_instance, player_char as app_player_char

        loaded_char_for_gm = Character.from_dict(char_dict)

        # Manually sync app's global player_char and GM's state for testing
        # This is a bit of a hack but necessary because test client doesn't fully replicate browser navigation flow for GM setup
        with app.app_context(): # Ensure we are in app context for modifying globals if needed
            app.player_char = loaded_char_for_gm # Update the global player_char in app.py
            game_manager_instance.setup_for_character(loaded_char_for_gm)
            self.assertTrue(game_manager_instance.is_game_setup, "GameManager failed to setup for action test helper.")
            self.assertEqual(game_manager_instance.character.name, char_name)

        return char_name


    # --- Basic Action Tests ---
    def test_action_talk_to_self(self):
        """Test the 'talk_to_self' action."""
        char_name = self._setup_user_and_character_for_actions()

        response = self.client.post('/action', data={'action_name': 'talk_to_self'}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        # Check the session for 'action_result' which holds the popup content
        with self.client.session_transaction() as sess:
            action_result = sess.get('action_result', '')

        self.assertIn(f"{char_name} mutters something unintelligible.", action_result)

    def test_action_explore_town(self):
        """Test the 'explore_town' action."""
        char_name = self._setup_user_and_character_for_actions()

        response = self.client.post('/action', data={'action_name': 'explore_town'}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        with self.client.session_transaction() as sess:
            action_result = sess.get('action_result', '')

        self.assertIn(f"{char_name} spends an hour exploring", action_result)
        # Further checks could be for "Found ...g!" or "Found a ..." or "Found nothing...",
        # but exact outcome is random. Presence of exploration text is key.

    def test_action_wait(self):
        """Test the 'wait' action."""
        char_name = self._setup_user_and_character_for_actions()

        response = self.client.post('/action', data={'action_name': 'wait'}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        with self.client.session_transaction() as sess:
            action_result = sess.get('action_result', '')

        self.assertIn(f"{char_name} waits for an hour", action_result)


if __name__ == '__main__':
    unittest.main()
