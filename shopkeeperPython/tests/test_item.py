import unittest
from shopkeeperPython.game.item import Item, QUALITY_TIERS, QUALITY_VALUE_MULTIPLIERS

class TestItem(unittest.TestCase):

    def test_item_creation_with_quantity(self):
        """Test item creation with an explicit quantity."""
        item = Item(name="Test Item", description="Desc", base_value=10, item_type="misc", quality="Common", quantity=5)
        self.assertEqual(item.quantity, 5)

    def test_item_creation_default_quantity(self):
        """Test item creation with default quantity."""
        item = Item(name="Test Item Default Quantity", description="Desc", base_value=10, item_type="misc", quality="Common")
        self.assertEqual(item.quantity, 1)

    def test_item_to_dict(self):
        """Test that to_dict includes quantity."""
        item = Item(name="Test Item", description="Desc", base_value=10, item_type="misc", quality="Common", quantity=7)
        item_dict = item.to_dict()
        self.assertIn("quantity", item_dict)
        self.assertEqual(item_dict["quantity"], 7)

    def test_item_from_dict_with_quantity(self):
        """Test item creation from dict with quantity."""
        item_data = {
            "name": "Test Item from Dict",
            "description": "Desc",
            "base_value": 10,
            "item_type": "misc",
            "quality": "Common",
            "quantity": 3,
            "effects": {"stat_boost": 1},
            "is_magical": True,
            "is_attunement": False,
            "is_consumable": True
        }
        item = Item.from_dict(item_data)
        self.assertEqual(item.quantity, 3)
        self.assertEqual(item.name, "Test Item from Dict")
        self.assertTrue(item.is_magical)
        self.assertTrue(item.is_consumable)
        self.assertFalse(item.is_attunement)
        self.assertIn("stat_boost", item.effects)

    def test_item_from_dict_default_quantity(self):
        """Test item creation from dict without quantity (should default to 1)."""
        item_data = {
            "name": "Test Item No Quantity",
            "description": "Desc",
            "base_value": 10,
            "item_type": "misc",
            "quality": "Uncommon",
            # No quantity specified
            "effects": {},
            "is_magical": False,
            "is_attunement": False,
            "is_consumable": False
        }
        item = Item.from_dict(item_data)
        self.assertEqual(item.quantity, 1)
        self.assertEqual(item.name, "Test Item No Quantity")
        self.assertEqual(item.quality, "Uncommon")

    def test_item_repr(self):
        """Test the __repr__ method includes quantity."""
        item = Item(name="Test Repr", description="Desc", base_value=10, item_type="misc", quality="Rare", quantity=15)
        self.assertIn("quantity=15", repr(item))

    def test_item_value_calculation(self):
        """Test that item value is calculated correctly based on quality."""
        base_value = 100
        quality = "Rare"
        expected_multiplier = QUALITY_VALUE_MULTIPLIERS[quality]
        item = Item(name="Value Test", description="Desc", base_value=base_value, item_type="gear", quality=quality)
        self.assertEqual(item.value, int(base_value * expected_multiplier))

    def test_invalid_quality_tier(self):
        """Test that creating an item with an invalid quality tier raises ValueError."""
        with self.assertRaises(ValueError):
            Item(name="Invalid Quality Item", description="Desc", base_value=10, item_type="misc", quality="Super Mythical")

if __name__ == '__main__':
    unittest.main()
