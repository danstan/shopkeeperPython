import unittest
from shopkeeperPython.game.character import Character
from shopkeeperPython.game.item import Item

class TestCharacter(unittest.TestCase):

    def setUp(self):
        self.character = Character(name="Test Character")
        self.character.inventory = [] # Ensure clean inventory for each test

    def test_add_item_to_inventory_new_item(self):
        item1 = Item(name="Potion", description="Heals", base_value=10, item_type="potion", quality="Common", quantity=1)
        self.character.add_item_to_inventory(item1)
        self.assertEqual(len(self.character.inventory), 1)
        self.assertEqual(self.character.inventory[0].name, "Potion")
        self.assertEqual(self.character.inventory[0].quantity, 1)

    def test_add_item_to_inventory_stacking_existing_item(self):
        item1 = Item(name="Arrow", description="Points", base_value=1, item_type="ammo", quality="Common", quantity=5)
        self.character.add_item_to_inventory(item1)

        item2 = Item(name="Arrow", description="Points", base_value=1, item_type="ammo", quality="Common", quantity=10)
        self.character.add_item_to_inventory(item2) # This should stack

        self.assertEqual(len(self.character.inventory), 1, "Items did not stack, found multiple entries.")
        self.assertEqual(self.character.inventory[0].name, "Arrow")
        self.assertEqual(self.character.inventory[0].quantity, 15, "Item quantity did not stack correctly.")

    def test_add_item_to_inventory_different_quality_no_stack(self):
        item1 = Item(name="Sword", description="Sharp", base_value=10, item_type="weapon", quality="Common", quantity=1)
        self.character.add_item_to_inventory(item1)

        item2 = Item(name="Sword", description="Sharp", base_value=10, item_type="weapon", quality="Rare", quantity=1)
        self.character.add_item_to_inventory(item2) # Should not stack due to different quality

        self.assertEqual(len(self.character.inventory), 2, "Items of different quality stacked but should not have.")
        names = sorted([i.name for i in self.character.inventory])
        qualities = sorted([i.quality for i in self.character.inventory])
        self.assertEqual(names, ["Sword", "Sword"])
        self.assertEqual(qualities, ["Common", "Rare"])


    def test_has_items_sufficient(self):
        self.character.add_item_to_inventory(Item(name="Iron Ore", base_value=5, item_type="component", quantity=3))
        self.character.add_item_to_inventory(Item(name="Coal", base_value=2, item_type="component", quantity=1))

        has_all, missing = self.character.has_items({"Iron Ore": 2, "Coal": 1})
        self.assertTrue(has_all)
        self.assertEqual(missing, {})

        has_all_exact, missing_exact = self.character.has_items({"Iron Ore": 3})
        self.assertTrue(has_all_exact)
        self.assertEqual(missing_exact, {})

    def test_has_items_insufficient_one_item(self):
        self.character.add_item_to_inventory(Item(name="Iron Ore", base_value=5, item_type="component", quantity=1))
        has_all, missing = self.character.has_items({"Iron Ore": 2})
        self.assertFalse(has_all)
        self.assertEqual(missing, {"Iron Ore": 1})

    def test_has_items_insufficient_multiple_items(self):
        self.character.add_item_to_inventory(Item(name="Iron Ore", base_value=5, item_type="component", quantity=1))
        self.character.add_item_to_inventory(Item(name="Wood", base_value=1, item_type="component", quantity=5))

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
        self.character.add_item_to_inventory(Item(name="Iron Ore", base_value=5, item_type="component", quantity=3))
        self.character.add_item_to_inventory(Item(name="Coal", base_value=2, item_type="component", quantity=2))

        consumed = self.character.consume_items({"Iron Ore": 2, "Coal": 1})
        self.assertTrue(consumed)

        self.assertEqual(len(self.character.inventory), 2) # Still two stacks
        iron_stack = next(item for item in self.character.inventory if item.name == "Iron Ore")
        coal_stack = next(item for item in self.character.inventory if item.name == "Coal")
        self.assertEqual(iron_stack.quantity, 1)
        self.assertEqual(coal_stack.quantity, 1)

    def test_consume_items_full_stack_depletion(self):
        self.character.add_item_to_inventory(Item(name="Iron Ore", base_value=5, item_type="component", quantity=2))
        self.character.add_item_to_inventory(Item(name="Coal", base_value=2, item_type="component", quantity=1))

        consumed = self.character.consume_items({"Iron Ore": 2, "Coal": 1})
        self.assertTrue(consumed)

        # Coal stack should be gone
        self.assertEqual(len(self.character.inventory), 0, f"Inventory should be empty. Found: {[i.name for i in self.character.inventory]}")


    def test_consume_items_item_not_fully_consumed_error_case(self):
        # This test assumes consume_items might have its own check or fail gracefully,
        # though the primary guard is has_items.
        # Based on current consume_items, it should return False if not enough.
        self.character.add_item_to_inventory(Item(name="Iron Ore", base_value=5, item_type="component", quantity=1))
        consumed = self.character.consume_items({"Iron Ore": 2})
        self.assertFalse(consumed, "Consume items should return False if not enough items, even if has_items was skipped/failed.")
        # Check inventory state - should be unchanged if consumption failed early
        iron_stack = next((item for item in self.character.inventory if item.name == "Iron Ore"), None)
        self.assertIsNotNone(iron_stack)
        if iron_stack: # Make linter happy
             self.assertEqual(iron_stack.quantity, 1, "Item quantity should not change if consumption fails.")


if __name__ == '__main__':
    unittest.main()
