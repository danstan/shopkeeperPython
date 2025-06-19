import unittest
from unittest.mock import patch
from shopkeeperPython.game.character import Character
from shopkeeperPython.game.item import Item

class TestCharacter(unittest.TestCase):

    def setUp(self):
        self.character = Character(name="Test Character")
        self.character.inventory = [] # Ensure clean inventory for each test

    def test_add_item_to_inventory_new_item(self):
        item1 = Item(name="Potion", description="Heals", base_value=10, item_type="potion", quality="Common")
        item1.quantity = 1
        self.character.add_item_to_inventory(item1)
        self.assertEqual(len(self.character.inventory), 1)
        self.assertEqual(self.character.inventory[0].name, "Potion")
        self.assertEqual(self.character.inventory[0].quantity, 1)

    def test_add_item_to_inventory_stacking_existing_item(self):
        # This test will likely fail its logic assertions after the TypeError fix,
        # because add_item_to_inventory currently just appends.
        # However, the goal here is to fix the TypeError first.
        item1 = Item(name="Arrow", description="Points", base_value=1, item_type="ammo", quality="Common")
        item1.quantity = 5
        self.character.add_item_to_inventory(item1)

        item2 = Item(name="Arrow", description="Points", base_value=1, item_type="ammo", quality="Common")
        item2.quantity = 10
        self.character.add_item_to_inventory(item2) # This should stack

        # The following assertions will likely fail due to character.add_item_to_inventory's current implementation
        self.assertEqual(len(self.character.inventory), 1, "Items did not stack, found multiple entries.")
        self.assertEqual(self.character.inventory[0].name, "Arrow")
        self.assertEqual(self.character.inventory[0].quantity, 15, "Item quantity did not stack correctly.")

    def test_add_item_to_inventory_different_quality_no_stack(self):
        item1 = Item(name="Sword", description="Sharp", base_value=10, item_type="weapon", quality="Common")
        item1.quantity = 1
        self.character.add_item_to_inventory(item1)

        item2 = Item(name="Sword", description="Sharp", base_value=10, item_type="weapon", quality="Rare")
        item2.quantity = 1
        self.character.add_item_to_inventory(item2) # Should not stack due to different quality

        self.assertEqual(len(self.character.inventory), 2, "Items of different quality stacked but should not have.")
        names = sorted([i.name for i in self.character.inventory])
        qualities = sorted([i.quality for i in self.character.inventory])
        self.assertEqual(names, ["Sword", "Sword"])
        self.assertEqual(qualities, ["Common", "Rare"])


    def test_has_items_sufficient(self):
        item_iron = Item(name="Iron Ore", description="Some iron ore", base_value=5, item_type="component", quality="Common")
        item_iron.quantity = 3
        self.character.add_item_to_inventory(item_iron)

        item_coal = Item(name="Coal", description="Some coal", base_value=2, item_type="component", quality="Common")
        item_coal.quantity = 1
        self.character.add_item_to_inventory(item_coal)

        has_all, missing = self.character.has_items({"Iron Ore": 2, "Coal": 1})
        self.assertTrue(has_all)
        self.assertEqual(missing, {})

        has_all_exact, missing_exact = self.character.has_items({"Iron Ore": 3})
        self.assertTrue(has_all_exact)
        self.assertEqual(missing_exact, {})

    def test_has_items_insufficient_one_item(self):
        item_iron = Item(name="Iron Ore", description="Some iron ore", base_value=5, item_type="component", quality="Common")
        item_iron.quantity = 1
        self.character.add_item_to_inventory(item_iron)
        has_all, missing = self.character.has_items({"Iron Ore": 2})
        self.assertFalse(has_all)
        self.assertEqual(missing, {"Iron Ore": 1})

    def test_has_items_insufficient_multiple_items(self):
        item_iron = Item(name="Iron Ore", description="Some iron ore", base_value=5, item_type="component", quality="Common")
        item_iron.quantity = 1
        self.character.add_item_to_inventory(item_iron)

        item_wood = Item(name="Wood", description="Some wood", base_value=1, item_type="component", quality="Common")
        item_wood.quantity = 5
        self.character.add_item_to_inventory(item_wood)

        has_all, missing = self.character.has_items({"Iron Ore": 2, "Coal": 1, "Wood": 6})
        self.assertFalse(has_all)
        self.assertEqual(missing, {"Iron Ore": 1, "Coal": 1, "Wood": 1})

    def test_has_items_empty_requirement(self):
        has_all, missing = self.character.has_items({})
        self.assertTrue(has_all)
        self.assertEqual(missing, {})

    def test_has_items_item_not_in_inventory_at_all(self):
        has_all, missing = self.character.has_items({"Mythril Ore": 1})
        self.assertFalse(has_all)
        self.assertEqual(missing, {"Mythril Ore": 1})

    def test_consume_items_simple_consumption(self):
        item_iron = Item(name="Iron Ore", description="Some iron ore", base_value=5, item_type="component", quality="Common")
        item_iron.quantity = 3
        self.character.add_item_to_inventory(item_iron)

        item_coal = Item(name="Coal", description="Some coal", base_value=2, item_type="component", quality="Common")
        item_coal.quantity = 2
        self.character.add_item_to_inventory(item_coal)

        consumed = self.character.consume_items({"Iron Ore": 2, "Coal": 1})
        self.assertTrue(consumed)

        self.assertEqual(len(self.character.inventory), 2) # Still two stacks
        iron_stack = next(item for item in self.character.inventory if item.name == "Iron Ore")
        coal_stack = next(item for item in self.character.inventory if item.name == "Coal")
        self.assertEqual(iron_stack.quantity, 1)
        self.assertEqual(coal_stack.quantity, 1)

    def test_consume_items_full_stack_depletion(self):
        item_iron = Item(name="Iron Ore", description="Some iron ore", base_value=5, item_type="component", quality="Common")
        item_iron.quantity = 2
        self.character.add_item_to_inventory(item_iron)

        item_coal = Item(name="Coal", description="Some coal", base_value=2, item_type="component", quality="Common")
        item_coal.quantity = 1
        self.character.add_item_to_inventory(item_coal)

        consumed = self.character.consume_items({"Iron Ore": 2, "Coal": 1})
        self.assertTrue(consumed)

        # Coal stack should be gone
        self.assertEqual(len(self.character.inventory), 0, f"Inventory should be empty. Found: {[i.name for i in self.character.inventory]}")


    def test_consume_items_item_not_fully_consumed_error_case(self):
        # This test assumes consume_items might have its own check or fail gracefully,
        # though the primary guard is has_items.
        # Based on current consume_items, it should return False if not enough.
        item_iron = Item(name="Iron Ore", description="Some iron ore", base_value=5, item_type="component", quality="Common")
        item_iron.quantity = 1
        self.character.add_item_to_inventory(item_iron)
        consumed = self.character.consume_items({"Iron Ore": 2})
        self.assertFalse(consumed, "Consume items should return False if not enough items, even if has_items was skipped/failed.")
        # Check inventory state - should be unchanged if consumption failed early
        iron_stack = next((item for item in self.character.inventory if item.name == "Iron Ore"), None)
        self.assertIsNotNone(iron_stack)
        if iron_stack: # Make linter happy
             self.assertEqual(iron_stack.quantity, 1, "Item quantity should not change if consumption fails.")

    def test_roll_single_stat_range_and_type(self):
        """Tests that roll_single_stat returns an int within the expected range."""
        for _ in range(100):  # Run multiple times to check randomness
            stat_value = Character.roll_single_stat()
            self.assertIsInstance(stat_value, int, "Stat value should be an integer.")
            self.assertTrue(3 <= stat_value <= 18, f"Stat value {stat_value} out of range (3-18).")

    def test_reroll_single_stat_range_and_type(self):
        """Tests that reroll_single_stat returns an int within the expected range."""
        for _ in range(100):  # Run multiple times to check randomness
            stat_value = Character.reroll_single_stat()
            self.assertIsInstance(stat_value, int, "Stat value from reroll should be an integer.")
            self.assertTrue(3 <= stat_value <= 18, f"Stat value {stat_value} from reroll out of range (3-18).")

    def test_attribute_calculation_no_bonuses(self):
        self.character.stats = {"STR": 10, "DEX": 12, "CON": 14, "INT": 16, "WIS": 8, "CHA": 13}
        # _recalculate_all_attributes is called in __init__ and when stats change via methods,
        # but if we are manually setting stats like this, we should call it.
        # However, for a fresh character from setUp, __init__ already called it.
        # If we were to change self.character.stats mid-test AFTER setup, then a manual call is needed.
        # For this test, assuming __init__ has set initial attributes based on default stats (all 0s or from roll_stats if setup did that),
        # then changing self.character.stats requires a manual recalculation.
        self.character._recalculate_all_attributes()

        self.assertEqual(self.character.get_attribute_score("Athletics"), 0)  # STR 10
        self.assertEqual(self.character.get_attribute_score("Acrobatics"), 1) # DEX 12
        self.assertEqual(self.character.get_attribute_score("Stealth"), 1)    # DEX 12
        self.assertEqual(self.character.get_attribute_score("Arcana"), 3)     # INT 16
        self.assertEqual(self.character.get_attribute_score("History"), 3)    # INT 16
        self.assertEqual(self.character.get_attribute_score("Insight"), -1)   # WIS 8
        self.assertEqual(self.character.get_attribute_score("Medicine"), -1)  # WIS 8
        self.assertEqual(self.character.get_attribute_score("Persuasion"), 1) # CHA 13
        self.assertEqual(self.character.get_attribute_score("Deception"), 1)  # CHA 13
        # Spot check a CON based attribute if one existed, for now CON doesn't have default attributes
        # For example, if "Concentration" was CON based:
        # self.assertEqual(self.character.get_attribute_score("Concentration"), 2) # CON 14

    def test_attribute_calculation_with_item_bonuses(self):
        self.character.stats = {"STR": 10, "DEX": 10, "CON": 10, "INT": 10, "WIS": 10, "CHA": 10}
        self.character._recalculate_all_attributes() # Initial calculation with base stats

        self.assertEqual(self.character.get_attribute_score("Acrobatics"), 0) # DEX 10 -> mod 0
        self.assertEqual(self.character.get_attribute_score("Athletics"), 0)  # STR 10 -> mod 0

        # Simulate item bonus
        self.character.stat_bonuses["DEX"] += 2
        self.character._recalculate_all_attributes() # Recalculate with bonus

        self.assertEqual(self.character.get_attribute_score("Acrobatics"), 1) # DEX 10+2=12 -> mod +1
        self.assertEqual(self.character.get_attribute_score("Athletics"), 0)  # STR 10 -> mod 0 (unchanged)

        # Simulate removing item bonus
        self.character.stat_bonuses["DEX"] -= 2
        self.character._recalculate_all_attributes() # Recalculate again

        self.assertEqual(self.character.get_attribute_score("Acrobatics"), 0) # DEX 10 -> mod 0

    @patch('random.randint')
    def test_perform_skill_check_with_attributes(self, mock_randint):
        self.character.stats = {"STR": 10, "DEX": 16, "INT": 12} # DEX 16 -> Acrobatics +3, INT 12 -> Arcana +1
        self.character._recalculate_all_attributes()

        # Test case 1: Roll 5 + Acrobatics 3 = 8. DC 10. Should fail.
        mock_randint.return_value = 5
        self.assertFalse(self.character.perform_skill_check("Acrobatics", dc=10))

        # Test case 2: Roll 10 + Acrobatics 3 = 13. DC 10. Should succeed.
        mock_randint.return_value = 10
        self.assertTrue(self.character.perform_skill_check("Acrobatics", dc=10))

        # Test case 3: Roll 8 + Arcana 1 = 9. DC 10. Should fail.
        mock_randint.return_value = 8
        self.assertFalse(self.character.perform_skill_check("Arcana", dc=10))

        # Test case 4: Roll 9 + Arcana 1 = 10. DC 10. Should succeed.
        mock_randint.return_value = 9
        self.assertTrue(self.character.perform_skill_check("Arcana", dc=10))

        # Test disadvantage from exhaustion
        self.character.exhaustion_level = 1
        # Rolls will be 5 and (e.g.) 15, min is 5. 5 + Arcana 1 = 6. DC 10. Fail.
        mock_randint.side_effect = [5, 15] # First roll, second roll for disadvantage
        self.assertFalse(self.character.perform_skill_check("Arcana", dc=10))

        # Rolls will be 15 and 5, min is 5. 5 + Arcana 1 = 6. DC 10. Fail.
        mock_randint.side_effect = [15, 5]
        self.assertFalse(self.character.perform_skill_check("Arcana", dc=10))

        # Rolls will be 10 and 15, min is 10. 10 + Arcana 1 = 11. DC 10. Succeed.
        mock_randint.side_effect = [10, 15]
        self.assertTrue(self.character.perform_skill_check("Arcana", dc=10))
        self.character.exhaustion_level = 0 # Reset exhaustion


    def test_attributes_recalculated_on_load(self):
        char_data = {
            "name": "Loaded Character",
            "stats": {"STR": 10, "DEX": 10, "CON": 10, "INT": 18, "WIS": 10, "CHA": 10}, # INT 18 -> Arcana +4
            "stat_bonuses": {"INT": 1}, # Effective INT 19 -> Arcana +4
            "ac_bonus": 0, "level": 1, "xp": 0, "pending_xp": 0,
            "base_max_hp": 10, "hp": 10, "hit_dice": 1, "max_hit_dice": 1,
            "attunement_slots": 3, "attuned_items": [], "exhaustion_level": 0,
            "inventory": [], "gold": 100, "skill_points_to_allocate": 0,
            "speed": 30, "is_dead": False, "current_town_name": "Test Town"
        }
        loaded_char = Character.from_dict(char_data)
        # from_dict calls _recalculate_all_attributes at the end

        self.assertEqual(loaded_char.get_attribute_score("Arcana"), 4) # INT 18 (base) + 1 (bonus) = 19 -> mod +4
        self.assertEqual(loaded_char.get_attribute_score("Investigation"), 4) # INT 18 (base) + 1 (bonus) = 19 -> mod +4
        self.assertEqual(loaded_char.get_attribute_score("Acrobatics"), 0) # DEX 10 -> mod 0


class TestCharacterPerformSkillCheck(unittest.TestCase):
    def setUp(self):
        self.character = Character(name="Test Player")
        # Initialize stats for consistent modifiers; e.g., a +1 modifier for relevant skills
        # For skill 'Stealth' (DEX) and 'Insight' (WIS), let's set DEX and WIS to 12 (+1 mod)
        self.character.stats = {"STR": 10, "DEX": 12, "CON": 10, "INT": 10, "WIS": 12, "CHA": 10}
        self.character._recalculate_all_attributes() # Ensure attributes are based on these stats
        self.character.inventory = []
        self.character.exhaustion_level = 0

    def test_perform_skill_check_returns_detailed_dict(self):
        """Test that perform_skill_check returns the new detailed dictionary."""
        # Mock random.randint to control the d20 roll
        with patch('random.randint', return_value=10):
            result = self.character.perform_skill_check(skill_name="Stealth", dc=10)

        expected_keys = [
            "success", "d20_roll", "modifier", "total_value", "dc",
            "is_critical_hit", "is_critical_failure",
            "disadvantage_details", "reroll_details"
        ]
        for key in expected_keys:
            self.assertIn(key, result, f"Key '{key}' missing from result dictionary.")

        self.assertEqual(result["d20_roll"], 10)
        self.assertEqual(result["modifier"], self.character.get_attribute_score("Stealth")) # DEX mod (+1)
        self.assertEqual(result["total_value"], 10 + self.character.get_attribute_score("Stealth"))
        self.assertEqual(result["dc"], 10)
        self.assertIsNone(result["reroll_details"]) # No reroll in this basic test

    @patch('random.randint') # Patch at the class or method level
    def test_perform_skill_check_disadvantage(self, mock_randint):
        """Test skill check with disadvantage due to exhaustion."""
        self.character.exhaustion_level = 1 # Apply disadvantage

        # Configure mock_randint to return two different values for the disadvantage roll
        mock_randint.side_effect = [5, 15] # Rolls 5 then 15, disadvantage takes 5

        result = self.character.perform_skill_check(skill_name="Insight", dc=10)

        self.assertEqual(result["d20_roll"], 5, "d20_roll should be the lower of the two rolls.")
        self.assertIn("(rolled 5,15 dis, took 5)", result["disadvantage_details"], "Disadvantage details not correctly recorded.")
        # Modifier for Insight (WIS 12) should be +1
        self.assertEqual(result["total_value"], 5 + 1)
        self.assertFalse(result["success"])

    @patch('random.randint')
    def test_perform_skill_check_lucky_charm_reroll_success(self, mock_randint):
        """Test reroll with Lucky Charm leading to success."""
        lucky_charm = Item(name="Lucky Charm of the Gods", effects={"allow_reroll": True}, is_consumable=True)
        self.character.add_item_to_inventory(lucky_charm)

        # Initial roll fails (e.g., 5), reroll succeeds (e.g., 15)
        # random.randint will be called for: initial_roll1, reroll1
        mock_randint.side_effect = [5, 15]

        result = self.character.perform_skill_check(skill_name="Stealth", dc=15) # DC 15, Stealth mod is +1

        self.assertTrue(result["success"], "Check should succeed after reroll.")
        self.assertEqual(result["d20_roll"], 15, "d20_roll should reflect the reroll.")
        self.assertEqual(result["total_value"], 15 + 1)
        self.assertIsNotNone(result["reroll_details"], "reroll_details should be populated.")
        self.assertTrue(result["reroll_details"]["success"])
        self.assertEqual(result["reroll_details"]["d20_roll"], 15)
        self.assertNotIn(lucky_charm, self.character.inventory, "Consumable Lucky Charm should be removed.")

    @patch('random.randint')
    def test_perform_skill_check_lucky_charm_reroll_still_fails(self, mock_randint):
        lucky_charm = Item(name="Lucky Charm (Weak)", effects={"allow_reroll": True}, is_consumable=False) # Non-consumable
        self.character.add_item_to_inventory(lucky_charm)

        mock_randint.side_effect = [3, 7] # Initial roll 3, reroll 7. Stealth mod +1. DC 15.

        result = self.character.perform_skill_check(skill_name="Stealth", dc=15)

        self.assertFalse(result["success"])
        self.assertEqual(result["d20_roll"], 7) # Reflects reroll
        self.assertIsNotNone(result["reroll_details"])
        self.assertFalse(result["reroll_details"]["success"])
        self.assertEqual(result["reroll_details"]["d20_roll"], 7)
        self.assertIn(lucky_charm, self.character.inventory, "Non-consumable Lucky Charm should remain.")

    @patch('random.randint', return_value=8) # Always rolls 8
    def test_perform_skill_check_no_lucky_charm_fail(self, mock_randint):
        # Ensure no lucky charm
        self.character.inventory = [item for item in self.character.inventory if "Lucky Charm" not in item.name]

        result = self.character.perform_skill_check(skill_name="Stealth", dc=15) # DC 15, Mod +1, Roll 8 -> Total 9 (Fail)

        self.assertFalse(result["success"])
        self.assertEqual(result["d20_roll"], 8)
        self.assertIsNone(result["reroll_details"], "No reroll should be attempted.")

    @patch('random.randint', return_value=20)
    def test_perform_skill_check_critical_hit(self, mock_randint):
        result = self.character.perform_skill_check(skill_name="Stealth", dc=25) # DC very high
        self.assertTrue(result["is_critical_hit"])
        # Default 5e skill check rules: Nat 20 doesn't guarantee success if DC is too high, but it's a "crit".
        # Current implementation: success is total_value >= dc.
        # For Stealth +1, roll 20 -> total 21. So it fails against DC 25.
        self.assertFalse(result["success"], "Nat 20 is a critical hit, but not auto-success if total < DC for skill checks.")

    @patch('random.randint', return_value=1)
    def test_perform_skill_check_critical_failure(self, mock_randint):
        result = self.character.perform_skill_check(skill_name="Stealth", dc=5) # DC very low
        self.assertTrue(result["is_critical_failure"])
        # Default 5e skill check rules: Nat 1 doesn't guarantee failure if total >= DC, but it's a "crit fail".
        # Current implementation: success is total_value >= dc.
        # For Stealth +1, roll 1 -> total 2. So it fails against DC 5.
        self.assertFalse(result["success"])


if __name__ == '__main__':
    unittest.main()
