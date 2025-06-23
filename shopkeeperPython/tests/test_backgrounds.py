import unittest
from shopkeeperPython.game.character import Character
from shopkeeperPython.game.item import Item # Needed to check item instances
from shopkeeperPython.game.backgrounds import BACKGROUND_DEFINITIONS

def find_item_in_inventory(inventory, item_name):
    for item in inventory:
        if item.name == item_name:
            return item
    return None

class TestCharacterBackgrounds(unittest.TestCase):

    def test_apply_acolyte_background(self):
        char = Character(name="Acolyte Test", background_id="acolyte")
        # Set known stats for predictable modifiers (all 10s -> +0 mod)
        for stat_name in Character.STAT_NAMES:
            char.stats[stat_name] = 10
        char._recalculate_all_attributes()

        self.assertEqual(char.attribute_bonuses_from_background.get("Insight", 0), 1)
        self.assertEqual(char.attribute_bonuses_from_background.get("Religion", 0), 1)

        acolyte_bg_def = next((bg for bg in BACKGROUND_DEFINITIONS if bg["id"] == "acolyte"), None)
        self.assertIsNotNone(acolyte_bg_def, "Acolyte background definition not found.")
        expected_gold = 100 + acolyte_bg_def.get("starting_gold_bonus", 0)
        self.assertEqual(char.gold, expected_gold)

        sacred_text_item = find_item_in_inventory(char.inventory, "Sacred Text Scrap")
        self.assertIsNotNone(sacred_text_item, "Sacred Text Scrap not found in inventory.")
        if sacred_text_item:
            self.assertEqual(sacred_text_item.quantity, 1)

        # Insight is WIS-based. WIS 10 = +0 mod. Acolyte gives +1.
        self.assertEqual(char.get_attribute_score("Insight"), 1)
        # Religion is INT-based. INT 10 = +0 mod. Acolyte gives +1.
        self.assertEqual(char.get_attribute_score("Religion"), 1)

    def test_apply_urchin_background(self):
        char = Character(name="Urchin Test", background_id="urchin")
        # Set known stats for predictable modifiers (all 10s -> +0 mod)
        for stat_name in Character.STAT_NAMES:
            char.stats[stat_name] = 10
        char._recalculate_all_attributes()

        self.assertEqual(char.attribute_bonuses_from_background.get("Sleight of Hand", 0), 1)
        self.assertEqual(char.attribute_bonuses_from_background.get("Stealth", 0), 1)

        urchin_bg_def = next((bg for bg in BACKGROUND_DEFINITIONS if bg["id"] == "urchin"), None)
        self.assertIsNotNone(urchin_bg_def, "Urchin background definition not found.")
        expected_gold = 100 + urchin_bg_def.get("starting_gold_bonus", 0)
        self.assertEqual(char.gold, expected_gold)

        small_token_item = find_item_in_inventory(char.inventory, "Small Token")
        self.assertIsNotNone(small_token_item, "Small Token not found in inventory.")
        if small_token_item:
            self.assertEqual(small_token_item.quantity, 1)

        # Sleight of Hand is DEX-based. DEX 10 = +0 mod. Urchin gives +1.
        self.assertEqual(char.get_attribute_score("Sleight of Hand"), 1)
        # Stealth is DEX-based. DEX 10 = +0 mod. Urchin gives +1.
        self.assertEqual(char.get_attribute_score("Stealth"), 1)

    def test_invalid_background_id(self):
        char = Character(name="Invalid BG Test", background_id="non_existent_bg")
        # Set known stats for predictable modifiers
        for stat_name in Character.STAT_NAMES:
            char.stats[stat_name] = 10
        char._recalculate_all_attributes()

        self.assertEqual(char.attribute_bonuses_from_background, {})
        # Check if default items are added (assuming none for this test based on current understanding)
        self.assertEqual(len(char.inventory), 0, f"Inventory should be empty for invalid BG. Found: {[item.name for item in char.inventory]}")
        self.assertEqual(char.gold, 100) # Default starting gold

    def test_no_background_id(self):
        char = Character(name="No BG Test") # No background_id provided
        # Set known stats
        for stat_name in Character.STAT_NAMES:
            char.stats[stat_name] = 10
        char._recalculate_all_attributes()

        self.assertEqual(char.attribute_bonuses_from_background, {})
        self.assertEqual(len(char.inventory), 0, f"Inventory should be empty for no BG. Found: {[item.name for item in char.inventory]}")
        self.assertEqual(char.gold, 100) # Default starting gold

if __name__ == '__main__':
    unittest.main()
