import unittest
from shopkeeperPython.game.g_event import Event, GAME_EVENTS
from shopkeeperPython.game.character import Character # Using actual Character for some Event tests if simple
from shopkeeperPython.game.item import Item # Using actual Item for some Event tests

# If GAME_EVENTS is empty, define a sample one for direct use in Event tests
# This helps if this test file is run before game_manager populates events or if used in isolation.
if not GAME_EVENTS:
    # A fallback minimal event for testing Event class directly
    SAMPLE_EVENT_FOR_TESTING = Event.from_dict({
        "name": "Test Event For Class",
        "description": "A test event description.",
        "min_level": 1,
        "dc_scaling_factor": 0.0,
        "skill_check_options": [
            {
                "choice_text": "Test Choice 1",
                "skill": "Stealth",
                "base_dc": 10,
                "success_outcome_key": "success",
                "failure_outcome_key": "failure"
            }
        ],
        "outcomes": {
            "success": {"message": "Success!"},
            "failure": {"message": "Failure."}
        }
    })
else:
    SAMPLE_EVENT_FOR_TESTING = GAME_EVENTS[0]


class TestEventClass(unittest.TestCase):
    def test_event_creation_defaults(self):
        """Test Event instantiation with minimal data for defaults."""
        event = Event(name="Minimal Event", description="Desc", outcomes={})
        self.assertEqual(event.name, "Minimal Event")
        self.assertEqual(event.description, "Desc")
        self.assertEqual(event.outcomes, {})
        self.assertEqual(event.min_level, 1, "Default min_level should be 1")
        self.assertEqual(event.dc_scaling_factor, 0.0, "Default dc_scaling_factor should be 0.0")
        self.assertEqual(event.skill_check_options, [], "Default skill_check_options should be an empty list")
        self.assertIsInstance(event.effects, dict)
        self.assertEqual(event.duration, 0)
        self.assertEqual(event.event_type, "generic")
        self.assertFalse(event.is_active)

    def test_event_creation_full(self):
        """Test Event instantiation with all parameters."""
        options = [{"choice_text": "Choose", "skill": "TestSkill", "base_dc": 10, "success_outcome_key": "s", "failure_outcome_key": "f"}]
        outcomes_data = {"s": {"message": "Win"}, "f": {"message": "Lose"}}
        effects_data = {"gold_change": 10}

        event = Event(
            name="Full Event",
            description="Full Desc",
            outcomes=outcomes_data,
            skill_check_options=options,
            effects=effects_data,
            duration=5,
            event_type="quest",
            is_active=True,
            min_level=5,
            dc_scaling_factor=1.5
        )
        self.assertEqual(event.name, "Full Event")
        self.assertEqual(event.skill_check_options, options)
        self.assertEqual(event.outcomes, outcomes_data)
        self.assertEqual(event.effects, effects_data)
        self.assertEqual(event.duration, 5)
        self.assertEqual(event.event_type, "quest")
        self.assertTrue(event.is_active)
        self.assertEqual(event.min_level, 5)
        self.assertEqual(event.dc_scaling_factor, 1.5)

    def test_event_from_dict_simple(self):
        """Test Event.from_dict with basic event data."""
        data = {
            "name": "Simple Dict Event",
            "description": "Simple Desc",
            "outcomes": {"success": {"message": "Done"}}
        }
        event = Event.from_dict(data)
        self.assertEqual(event.name, "Simple Dict Event")
        self.assertEqual(event.description, "Simple Desc")
        self.assertEqual(event.outcomes["success"]["message"], "Done")
        self.assertEqual(event.min_level, 1) # Default
        self.assertEqual(event.dc_scaling_factor, 0.0) # Default
        self.assertEqual(event.skill_check_options, []) # Default

    def test_event_from_dict_complex(self):
        """Test Event.from_dict with complex skill check event data."""
        data = {
            "name": "Complex Event",
            "description": "A complex event with choices and scaling.",
            "min_level": 3,
            "dc_scaling_factor": 0.5,
            "skill_check_options": [
                {
                    "choice_text": "Sneak past (STEALTH DC 12).",
                    "skill": "Stealth",
                    "base_dc": 12,
                    "item_requirement": {"name": "Invisibility Potion", "effect": "auto_success"},
                    "success_outcome_key": "sneak_success",
                    "failure_outcome_key": "sneak_failure"
                },
                {
                    "choice_text": "Bribe guard (PERSUASION DC 10).",
                    "skill": "Persuasion",
                    "base_dc": 10,
                    "success_outcome_key": "bribe_success",
                    "failure_outcome_key": "bribe_failure"
                }
            ],
            "outcomes": {
                "sneak_success": {"message": "Succeeded sneaking."},
                "sneak_failure": {"message": "Failed sneaking."},
                "bribe_success": {"message": "Bribe taken."},
                "bribe_failure": {"message": "Bribe rejected."}
            },
            "effects": {"ambient_sound": "tense_music.mp3"},
            "duration": 10,
            "event_type": "encounter",
            "is_active": False
        }
        event = Event.from_dict(data)
        self.assertEqual(event.name, "Complex Event")
        self.assertEqual(event.description, "A complex event with choices and scaling.")
        self.assertEqual(event.min_level, 3)
        self.assertEqual(event.dc_scaling_factor, 0.5)
        self.assertEqual(len(event.skill_check_options), 2)
        self.assertEqual(event.skill_check_options[0]["skill"], "Stealth")
        self.assertIn("item_requirement", event.skill_check_options[0])
        self.assertEqual(event.skill_check_options[0]["item_requirement"]["name"], "Invisibility Potion")
        self.assertEqual(event.outcomes["bribe_success"]["message"], "Bribe taken.")
        self.assertEqual(event.effects, {"ambient_sound": "tense_music.mp3"})
        self.assertEqual(event.duration, 10)
        self.assertEqual(event.event_type, "encounter")
        self.assertFalse(event.is_active)

    def test_event_from_dict_handles_old_skill_check_key(self):
        """Test Event.from_dict can load from 'skill_check' if 'skill_check_options' is missing."""
        data = {
            "name": "Old Format Event",
            "description": "Uses old 'skill_check' key.",
            "skill_check": [ # Old key
                {"choice_text": "Old choice", "skill": "OldSkill", "base_dc": 9, "success_outcome_key": "s", "failure_outcome_key": "f"}
            ],
            "outcomes": {"s": {"message": "ok"}, "f": {"message": "not ok"}}
        }
        event = Event.from_dict(data)
        self.assertEqual(len(event.skill_check_options), 1)
        self.assertEqual(event.skill_check_options[0]["skill"], "OldSkill")

    def test_event_from_dict_prefers_skill_check_options_key(self):
        """Test Event.from_dict prefers 'skill_check_options' if both keys exist."""
        data = {
            "name": "Dual Key Event",
            "skill_check_options": [
                {"choice_text": "New choice", "skill": "NewSkill", "base_dc": 10, "success_outcome_key": "s", "failure_outcome_key": "f"}
            ],
            "skill_check": [ # Old key, should be ignored
                {"choice_text": "Old choice", "skill": "OldSkill", "base_dc": 9, "success_outcome_key": "s", "failure_outcome_key": "f"}
            ],
            "outcomes": {"s": {"message": "ok"}, "f": {"message": "not ok"}}
        }
        event = Event.from_dict(data)
        self.assertEqual(len(event.skill_check_options), 1)
        self.assertEqual(event.skill_check_options[0]["skill"], "NewSkill")


    def test_event_repr(self):
        """Test the string representation of the Event."""
        event = Event(name="Repr Event", description="A test for representation.", outcomes={}, min_level=2)
        representation = repr(event)
        self.assertIn("Event(name='Repr Event'", representation)
        self.assertIn("choices=0", representation) # Assuming skill_check_options is empty by default
        self.assertIn("min_lvl=2", representation)

        options = [{"choice_text": "C1", "skill": "S", "base_dc": 10, "success_outcome_key": "s", "failure_outcome_key": "f"}]
        event_with_options = Event(name="Options Event", description="Desc", outcomes={}, skill_check_options=options)
        repr_with_options = repr(event_with_options)
        self.assertIn("choices=1", repr_with_options)


class TestAllGameEventsIntegrity(unittest.TestCase):
    def test_all_events_in_game_events_list_are_valid(self):
        """
        Iterates through all events in GAME_EVENTS and performs structural validation.
        """
        self.assertTrue(len(GAME_EVENTS) > 0, "GAME_EVENTS list should not be empty.")

        for i, event_instance in enumerate(GAME_EVENTS):
            with self.subTest(event_name=getattr(event_instance, 'name', f"Unknown Event at index {i}")):
                self.assertIsInstance(event_instance, Event, f"Item at index {i} is not an Event instance.")

                # Basic attributes
                self.assertTrue(hasattr(event_instance, 'name') and isinstance(event_instance.name, str) and event_instance.name, "Event must have a non-empty name string.")
                self.assertTrue(hasattr(event_instance, 'description') and isinstance(event_instance.description, str) and event_instance.description, "Event must have a non-empty description string.")
                self.assertTrue(hasattr(event_instance, 'min_level') and isinstance(event_instance.min_level, int) and event_instance.min_level >= 0, "Event must have a non-negative min_level integer.")
                self.assertTrue(hasattr(event_instance, 'dc_scaling_factor') and isinstance(event_instance.dc_scaling_factor, float), "Event must have a dc_scaling_factor float.")

                # Outcomes
                self.assertTrue(hasattr(event_instance, 'outcomes') and isinstance(event_instance.outcomes, dict) and event_instance.outcomes, "Event must have a non-empty outcomes dictionary.")
                for outcome_key, outcome_data in event_instance.outcomes.items():
                    self.assertIsInstance(outcome_data, dict, f"Outcome '{outcome_key}' must be a dictionary.")
                    self.assertIn("message", outcome_data, f"Outcome '{outcome_key}' must have a 'message'.")
                    self.assertIsInstance(outcome_data["message"], str, f"Message for outcome '{outcome_key}' must be a string.")
                    self.assertIn("effects", outcome_data, f"Outcome '{outcome_key}' must have an 'effects' dictionary (can be empty).")
                    self.assertIsInstance(outcome_data["effects"], dict, f"Effects for outcome '{outcome_key}' must be a dictionary.")

                # Skill Check Options
                self.assertTrue(hasattr(event_instance, 'skill_check_options') and isinstance(event_instance.skill_check_options, list), "Event must have skill_check_options list (can be empty).")
                for choice_idx, choice_option in enumerate(event_instance.skill_check_options):
                    with self.subTest(choice_index=choice_idx):
                        self.assertIsInstance(choice_option, dict, f"Choice at index {choice_idx} must be a dictionary.")
                        self.assertIn("choice_text", choice_option, f"Choice {choice_idx} must have 'choice_text'.")
                        self.assertIsInstance(choice_option["choice_text"], str, f"choice_text for choice {choice_idx} must be a string.")

                        self.assertIn("success_outcome_key", choice_option, f"Choice {choice_idx} must have 'success_outcome_key'.")
                        self.assertIn(choice_option["success_outcome_key"], event_instance.outcomes, f"success_outcome_key '{choice_option['success_outcome_key']}' for choice {choice_idx} must exist in event outcomes.")

                        self.assertIn("failure_outcome_key", choice_option, f"Choice {choice_idx} must have 'failure_outcome_key'.")
                        self.assertIn(choice_option["failure_outcome_key"], event_instance.outcomes, f"failure_outcome_key '{choice_option['failure_outcome_key']}' for choice {choice_idx} must exist in event outcomes.")

                        if choice_option.get("skill"): # If a skill is specified, a base_dc is expected
                            self.assertIn("base_dc", choice_option, f"Choice {choice_idx} with skill '{choice_option['skill']}' must have 'base_dc'.")
                            self.assertIsInstance(choice_option["base_dc"], int, f"base_dc for choice {choice_idx} must be an integer.")

                        if choice_option.get("item_requirement"):
                            item_req = choice_option["item_requirement"]
                            self.assertIsInstance(item_req, dict, f"item_requirement for choice {choice_idx} must be a dictionary.")
                            self.assertIn("name", item_req, f"item_requirement for choice {choice_idx} must specify item 'name'.")
                            self.assertIn("effect", item_req, f"item_requirement for choice {choice_idx} must specify 'effect'.")
                            if item_req["effect"] == "dc_reduction" or item_req["effect"] == "custom_bonus": # Example, extend as new effects are added
                                self.assertIn("value", item_req, f"item_requirement with effect '{item_req['effect']}' for choice {choice_idx} often has a 'value'.")


if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)

# TestEventManager will be added below in subsequent steps.

from unittest.mock import MagicMock # Removed patch

# Using actual EventManager, but Character and GameManager will be mocked for EventManager tests
from shopkeeperPython.game.g_event import EventManager


# --- Mocks for Testing EventManager ---
class MockCharacter:
    def __init__(self, name="Test Mock Character", level=1):
        self.name = name
        self.level = level
        self.inventory = []
        self.gold = 100
        self.xp = 0
        self.pending_xp = 0
        # Ensure all skills referenced in new events are mockable by Character.ATTRIBUTE_DEFINITIONS
        # This might require adding them if they are not standard D&D 5e skills mapped in Character.py
        # For testing, we can expand the mock's known skills.
        _mock_attr_defs = Character.ATTRIBUTE_DEFINITIONS.copy()
        _mock_attr_defs.update({
            "Animal Handling": "WIS",
            "Medicine": "WIS",
            "History": "INT",
            "Perception": "WIS",
            "Survival": "WIS",
            "Alchemy": "INT", # Conceptual skill
            "Acrobatics": "DEX",
            "Nature": "INT",
            "Performance": "CHA",
            "Religion": "INT",
            "Sleight of Hand": "DEX",
            "Stealth": "DEX"
        })
        self.ATTRIBUTE_DEFINITIONS = _mock_attr_defs
        self.stats = {"STR": 10, "DEX": 10, "CON": 10, "INT": 10, "WIS": 10, "CHA": 10} # Base for attribute calculation
        self.exhaustion_level = 0 # Important for skill checks

        # Mock necessary methods
        self.perform_skill_check = MagicMock()
        self.add_item_to_inventory = MagicMock()
        self.remove_item_from_inventory = MagicMock() # General removal
        self.remove_specific_item_from_inventory = MagicMock() # Specific instance removal
        self.award_xp = MagicMock()

    def get_attribute_score(self, skill_name): # Simplified for placeholder
            # Ensure skill_name is treated case-insensitively for lookups if necessary, or ensure definitions match event skill strings.
            # For this mock, assume exact match from ATTRIBUTE_DEFINITIONS.
            base_stat_name = self.ATTRIBUTE_DEFINITIONS.get(skill_name)
            if base_stat_name:
                return (self.stats.get(base_stat_name, 10) -10) // 2
            # print(f"Warning: MockCharacter.get_attribute_score: Skill '{skill_name}' not found in ATTRIBUTE_DEFINITIONS. Returning 0 modifier.")
            return 0

class MockGameManager:
    def __init__(self):
        self.add_journal_entry = MagicMock()
        # Add any other attributes EventManager might access from GameManager
        self.character = None # Will be set by EventManager's __init__ via self.character


class TestEventManager(unittest.TestCase):
    def setUp(self):
        self.mock_character = MockCharacter(name="Test Hero", level=5)
        self.mock_game_manager = MockGameManager()

        # EventManager takes character and game_manager.
        # The EventManager's self.character will be our mock_character.
        # The EventManager's self.game_manager will be our mock_game_manager.
        self.event_manager = EventManager(character=self.mock_character, game_manager=self.mock_game_manager)

        # Define a sample complex event for use in multiple tests
        self.sample_event_data = {
            "name": "Ancient Tomb",
            "description": "A dusty tomb entrance.",
            "min_level": 3,
            "dc_scaling_factor": 1.0, # DC increases by 1 for each level above min_level
            "skill_check_options": [
                {
                    "choice_text": "Search for traps (INVESTIGATION).",
                    "skill": "Investigation",
                    "base_dc": 15,
                    "success_outcome_key": "traps_disabled",
                    "failure_outcome_key": "trap_triggered"
                },
                {
                    "choice_text": "Try to decipher runes (ARCANA).",
                    "skill": "Arcana",
                    "base_dc": 18,
                    "item_requirement": {"name": "Scroll of Comprehension", "effect": "auto_success"},
                    "success_outcome_key": "runes_deciphered",
                    "failure_outcome_key": "runes_confuse"
                },
                {
                    "choice_text": "Force open the stone door (ATHLETICS).",
                    "skill": "Athletics",
                    "base_dc": 20,
                    "item_requirement": {"name": "Crowbar", "effect": "dc_reduction", "value": 3},
                    "success_outcome_key": "door_opened",
                    "failure_outcome_key": "door_stuck"
                }
            ],
            "outcomes": {
                "traps_disabled": {"message": "You found and disabled a trap!", "effects": {"character_xp_gain": 50}},
                "trap_triggered": {"message": "A trap springs!", "effects": {"hp_loss": 10}},
                "runes_deciphered": {"message": "The runes reveal a secret.", "effects": {"character_xp_gain": 75, "item_reward": {"name": "Ancient Scroll", "quantity": 1, "description":"A very old scroll.", "base_value":100, "item_type":"scroll", "quality":"Rare"}}},
                "runes_confuse": {"message": "The runes are baffling.", "effects": {"character_xp_gain": 10}},
                "door_opened": {"message": "The door creaks open.", "effects": {"character_xp_gain": 40}},
                "door_stuck": {"message": "The door remains sealed.", "effects": {"character_xp_gain": 5}}
            }
        }
        self.sample_event = Event.from_dict(self.sample_event_data)

    def test_resolve_event_calculates_choices_and_dcs(self):
        """Test resolve_event returns structured choices with correctly scaled DCs."""
        self.mock_character.level = 5 # Event min_level=3, dc_scaling_factor=1.0
        # Expected DC for first choice (base 15): 15 + (5-3)*1.0 = 17
        # Expected DC for second choice (base 18): 18 + (5-3)*1.0 = 20
        # Expected DC for third choice (base 20): 20 + (5-3)*1.0 = 22

        choices = self.event_manager.resolve_event(self.sample_event)

        self.assertEqual(len(choices), 3)

        # Choice 0 (Investigation)
        self.assertEqual(choices[0]["skill"], "Investigation")
        self.assertEqual(choices[0]["dc"], 17) # Scaled DC
        self.assertEqual(choices[0]["text"], self.sample_event.skill_check_options[0]["choice_text"])

        # Choice 1 (Arcana) - with item requirement description
        self.assertEqual(choices[1]["skill"], "Arcana")
        self.assertEqual(choices[1]["dc"], 20) # Scaled DC
        self.assertIn("item_requirement_desc", choices[1])
        self.assertIn("Scroll of Comprehension", choices[1]["item_requirement_desc"])

        # Choice 2 (Athletics) - with item requirement description
        self.assertEqual(choices[2]["skill"], "Athletics")
        self.assertEqual(choices[2]["dc"], 22) # Scaled DC
        self.assertIn("item_requirement_desc", choices[2])
        self.assertIn("Crowbar", choices[2]["item_requirement_desc"])

        # Test with a different character level to ensure scaling works
        self.mock_character.level = 3 # DC should be base_dc
        choices_level_3 = self.event_manager.resolve_event(self.sample_event)
        self.assertEqual(choices_level_3[0]["dc"], 15) # Base DC for Investigation
        self.assertEqual(choices_level_3[1]["dc"], 18) # Base DC for Arcana
        self.assertEqual(choices_level_3[2]["dc"], 20) # Base DC for Athletics

    def test_execute_skill_choice_basic_success(self):
        # Configure mock perform_skill_check to return success
        self.mock_character.perform_skill_check.return_value = {
            "success": True, "d20_roll": 18, "modifier": 2, "total_value": 20, "dc": 17,
            "is_critical_hit": False, "is_critical_failure": False,
            "disadvantage_details": "", "reroll_details": None
        }

        # Character level 5, event min_level 3, scaling 1.0. Base DC 15 -> Scaled DC 17
        result = self.event_manager.execute_skill_choice(self.sample_event, choice_index=0) # Investigation choice

        self.assertTrue(result["rolled_successfully"])
        self.assertEqual(result["message"], self.sample_event.outcomes["traps_disabled"]["message"])
        self.mock_character.award_xp.assert_called_with(50) # XP from "traps_disabled" outcome
        self.assertIsNotNone(result.get("roll_data"))
        self.assertTrue(result.get("roll_data").get("success"))
        self.mock_game_manager.add_journal_entry.assert_called_once()

    def test_execute_skill_choice_basic_failure(self):
        self.mock_character.perform_skill_check.return_value = {
            "success": False, "d20_roll": 5, "modifier": 2, "total_value": 7, "dc": 17,
            "is_critical_hit": False, "is_critical_failure": False,
            "disadvantage_details": "", "reroll_details": None
        }

        result = self.event_manager.execute_skill_choice(self.sample_event, choice_index=0) # Investigation choice

        self.assertFalse(result["rolled_successfully"])
        self.assertEqual(result["message"], self.sample_event.outcomes["trap_triggered"]["message"])
        # Assuming hp_loss is handled by character or another system, check if effect was passed
        self.assertEqual(result["outcome_details"].get("hp_loss"), 10)
        self.assertIsNotNone(result.get("roll_data"))
        self.assertFalse(result.get("roll_data").get("success"))
        self.mock_game_manager.add_journal_entry.assert_called_once()

    def test_execute_skill_choice_item_auto_success(self):
        # Give character the "Scroll of Comprehension"
        scroll = Item(name="Scroll of Comprehension", description="A readable scroll.", base_value=50, item_type="scroll", quality="Common")
        self.mock_character.inventory = [scroll]

        # Choice 1 is Arcana check with Scroll of Comprehension for auto_success
        result = self.event_manager.execute_skill_choice(self.sample_event, choice_index=1)

        self.assertTrue(result["rolled_successfully"])
        self.assertEqual(result["message"], self.sample_event.outcomes["runes_deciphered"]["message"])
        self.mock_character.award_xp.assert_called_with(75)
        self.mock_character.add_item_to_inventory.assert_called() # For the "Ancient Scroll" reward
        self.assertEqual(result["roll_data"]["status"], "auto_success")
        self.assertEqual(result["roll_data"]["item_used"], "Scroll of Comprehension")
        self.mock_character.perform_skill_check.assert_not_called() # Skill check should be bypassed
        self.mock_game_manager.add_journal_entry.assert_called_once()

    def test_execute_skill_choice_item_dc_reduction(self):
        crowbar = Item(name="Crowbar", description="A sturdy crowbar.", base_value=10, item_type="tool", quality="Common")
        self.mock_character.inventory = [crowbar]
        self.mock_character.level = 5 # Scaled DC for Athletics (choice 2) is 20 + (5-3)*1 = 22
                                      # With crowbar (-3 DC), effective DC is 19.

        # Make perform_skill_check succeed only with the reduction
        # Original DC would be 22. Reduced DC is 19.
        # We'll make the roll succeed against 19 but fail against 22.
        self.mock_character.perform_skill_check.return_value = {
            "success": True, "d20_roll": 18, "modifier": 1, "total_value": 19, "dc": 19, # Simulating check against reduced DC
            "is_critical_hit": False, "is_critical_failure": False,
            "disadvantage_details": "", "reroll_details": None
        }

        result = self.event_manager.execute_skill_choice(self.sample_event, choice_index=2) # Athletics choice

        self.assertTrue(result["rolled_successfully"])
        self.assertEqual(result["message"], self.sample_event.outcomes["door_opened"]["message"])
        self.mock_character.award_xp.assert_called_with(40)
        self.mock_character.perform_skill_check.assert_called_once_with(skill_name="Athletics", dc=19) # Check called with reduced DC
        self.assertIsNotNone(result.get("roll_data"))
        self.assertTrue(result.get("roll_data").get("success"))
        self.mock_game_manager.add_journal_entry.assert_called_once()

    def test_execute_skill_choice_item_required_not_present(self):
        self.mock_character.inventory = [] # Ensure no crowbar
        self.mock_character.level = 5
        # Scaled DC for Athletics (choice 2) is 22.

        self.mock_character.perform_skill_check.return_value = {
            "success": False, "d20_roll": 10, "modifier": 1, "total_value": 11, "dc": 22, # Failed against original DC
            "is_critical_hit": False, "is_critical_failure": False,
            "disadvantage_details": "", "reroll_details": None
        }

        result = self.event_manager.execute_skill_choice(self.sample_event, choice_index=2) # Athletics choice

        self.assertFalse(result["rolled_successfully"])
        self.assertEqual(result["message"], self.sample_event.outcomes["door_stuck"]["message"])
        self.mock_character.perform_skill_check.assert_called_once_with(skill_name="Athletics", dc=22) # Called with original scaled DC
        self.mock_game_manager.add_journal_entry.assert_called_once()

    def test_execute_skill_choice_dc_scaling(self):
        self.mock_character.level = 6 # min_level=3, scaling=1.0. Base DC 15 for choice 0.
        # Expected scaled DC = 15 + (6-3)*1.0 = 18

        self.mock_character.perform_skill_check.return_value = {"success": True, "d20_roll": 20, "modifier": 0, "total_value": 20, "dc": 18} # Assume success

        self.event_manager.execute_skill_choice(self.sample_event, choice_index=0)

        # Check that perform_skill_check was called with the correctly scaled DC
        self.mock_character.perform_skill_check.assert_called_with(skill_name="Investigation", dc=18)

    def test_execute_skill_choice_invalid_choice_index(self):
        result = self.event_manager.execute_skill_choice(self.sample_event, choice_index=99)
        self.assertFalse(result["rolled_successfully"])
        self.assertIn("Error: Invalid choice", result["message"])
        self.mock_game_manager.add_journal_entry.assert_not_called() # Or called with error

    def test_execute_skill_choice_event_with_no_options(self):
        no_options_event_data = {
            "name": "Direct Outcome Event", "description": "This just happens.",
            "outcomes": {"success": {"message": "It happened!", "effects": {"character_xp_gain": 5}}}
        }
        no_options_event = Event.from_dict(no_options_event_data)

        result = self.event_manager.execute_skill_choice(no_options_event, choice_index=0) # Index 0 for direct

        self.assertTrue(result["rolled_successfully"]) # Default success for direct outcome
        self.assertEqual(result["message"], "It happened!")
        self.mock_character.award_xp.assert_called_with(5)
        self.assertEqual(result["roll_data"]["status"], "direct_outcome")
        self.mock_game_manager.add_journal_entry.assert_called_once()

# End of TestEventManager, continue with TestCharacterPerformSkillCheck in the next step if needed.
