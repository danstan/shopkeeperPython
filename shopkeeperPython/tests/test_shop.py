import unittest
from shopkeeperPython.game.shop import Shop
from shopkeeperPython.game.character import Character
from shopkeeperPython.game.item import Item
from shopkeeperPython.game.town import Town # Shop requires a Town

class TestShop(unittest.TestCase):

    def setUp(self):
        # Create a dummy town for the shop
        self.town = Town(name="Testville")
        self.shop = Shop(name="Test Shop", owner_name="Test Owner", town=self.town)
        self.character = Character(name="Test Crafter")
        self.character.inventory = [] # Clear inventory

        # Define recipes for the shop to use (mirroring BASIC_RECIPES structure)
        # Items used as ingredients should also be definable as Item objects if needed.
        self.shop.BASIC_RECIPES = {
            "Traveler's Bread": {
                "base_value": 2, "type": "food", "description": "A dense loaf.",
                "crafting_difficulty": 2, "effects": {"stamina_recovery": 2, "healing": 1},
                "is_consumable": True,
                "ingredients": {"Grain": 2, "Clean Water": 1}
            },
            "Basic Arrow": {
                "type": "ammunition", "base_value": 1,
                "description": "Recipe makes 5.", "crafting_difficulty": 4,
                "effects": {"damage": "1d6"}, "quantity_produced": 5,
                "ingredients": {"Small Twig": 5, "Stone Fragment": 5, "Bird Feather": 5}
            },
            "Simple Dagger": { # An existing recipe type for broader test
                "base_value": 5, "type": "weapon", "description": "A crude dagger.",
                "crafting_difficulty": 5, "effects": {"damage": "1d4"},
                "ingredients": {"Leather Scraps": 1, "Scrap Metal": 2}
            }
        }
        # Make sure some base components for crafting are defined for tests if needed.
        # For this test, we add ingredients directly to character inventory.

    def test_craft_item_successful_travelers_bread(self):
        # Add ingredients to character
        self.character.add_item_to_inventory(Item(name="Grain", base_value=1, item_type="component", quantity=2))
        self.character.add_item_to_inventory(Item(name="Clean Water", base_value=1, item_type="component", quantity=1))

        crafted_item = self.shop.craft_item("Traveler's Bread", self.character)

        self.assertIsNotNone(crafted_item)
        self.assertEqual(crafted_item.name, "Traveler's Bread")
        self.assertEqual(crafted_item.quantity, 1) # Default quantity_produced is 1
        self.assertIn(crafted_item, self.shop.inventory)

        # Verify ingredients consumed
        # Grain should be 0, Clean Water should be 0
        has_grain, _ = self.character.has_items({"Grain": 1})
        self.assertFalse(has_grain, "Grain should have been consumed.")
        has_water, _ = self.character.has_items({"Clean Water": 1})
        self.assertFalse(has_water, "Clean Water should have been consumed.")

        # Check if any stacks remain with 0 quantity (they should be removed by consume_items)
        self.assertEqual(len(self.character.inventory), 0,
                         f"Character inventory should be empty after consuming all ingredients. Found: {[i.name for i in self.character.inventory]}")


    def test_craft_item_successful_basic_arrow_batch(self):
        # Add ingredients
        self.character.add_item_to_inventory(Item(name="Small Twig", base_value=0, item_type="component", quantity=5))
        self.character.add_item_to_inventory(Item(name="Stone Fragment", base_value=0, item_type="component", quantity=5))
        self.character.add_item_to_inventory(Item(name="Bird Feather", base_value=1, item_type="component", quantity=5))

        crafted_item = self.shop.craft_item("Basic Arrow", self.character)

        self.assertIsNotNone(crafted_item)
        self.assertEqual(crafted_item.name, "Basic Arrow")
        self.assertEqual(crafted_item.quantity, 5, "Basic Arrow recipe should produce 5.") # quantity_produced
        self.assertIn(crafted_item, self.shop.inventory)

        # Verify ingredients consumed
        self.assertEqual(len(self.character.inventory), 0,
                         f"Character inventory should be empty after consuming all arrow ingredients. Found: {[i.name for i in self.character.inventory]}")


    def test_craft_item_missing_ingredients_simple_dagger(self):
        # Character has some, but not all ingredients
        self.character.add_item_to_inventory(Item(name="Leather Scraps", base_value=2, item_type="component", quantity=1))
        # Missing Scrap Metal

        initial_char_inv_count = len(self.character.inventory)
        initial_shop_inv_count = len(self.shop.inventory)

        crafted_item = self.shop.craft_item("Simple Dagger", self.character)

        self.assertIsNone(crafted_item, "Item should not be crafted due to missing ingredients.")
        self.assertEqual(len(self.shop.inventory), initial_shop_inv_count, "Shop inventory should not change on failed craft.")

        # Verify ingredients NOT consumed
        leather_stack = next((item for item in self.character.inventory if item.name == "Leather Scraps"), None)
        self.assertIsNotNone(leather_stack)
        if leather_stack: # Linter satisfaction
            self.assertEqual(leather_stack.quantity, 1, "Leather Scraps quantity should not change.")
        self.assertEqual(len(self.character.inventory), initial_char_inv_count, "Character inventory should not change overall on failed craft if only partial ingredients existed.")

    def test_craft_item_recipe_unknown(self):
        crafted_item = self.shop.craft_item("Mythical Sword", self.character)
        self.assertIsNone(crafted_item)

if __name__ == '__main__':
    unittest.main()
