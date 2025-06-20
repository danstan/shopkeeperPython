import unittest
from unittest.mock import patch, MagicMock
import random

# Ensure correct import paths for Shop, Item, Town, Character based on project structure
# Assuming shopkeeperPython is the root package for these modules
from shopkeeperPython.game.shop import Shop
from shopkeeperPython.game.item import Item, QUALITY_TIERS
from shopkeeperPython.game.town import Town
# from shopkeeperPython.game.character import Character # Using MockCharacter instead for shop tests

# A simple mock character for Shop interactions
class MockCharacter:
    def __init__(self, name="Test Character", gold=1000):
        self.name = name
        self.inventory = []
        self.gold = gold
        self.skills = {} # For potential future skill check tests

    def add_item_to_inventory(self, item: Item):
        # Simplified: assumes item is an object with name and quantity
        for existing_item in self.inventory:
            if existing_item.name == item.name and existing_item.quality == item.quality and hasattr(existing_item, 'quantity'):
                existing_item.quantity += item.quantity
                return
        self.inventory.append(item)

    def has_items(self, items_to_check: dict) -> tuple[bool, dict]:
        missing_items = {}
        for item_name, required_qty in items_to_check.items():
            current_qty = sum(item.quantity for item in self.inventory if item.name == item_name)
            if current_qty < required_qty:
                missing_items[item_name] = required_qty - current_qty
        return not missing_items, missing_items

    def consume_items(self, items_to_consume: dict) -> bool:
        if not self.has_items(items_to_consume)[0]:
            return False
        for item_name, qty_to_consume in items_to_consume.items():
            consumed_count = 0
            new_inventory = []
            # Consume from stacks correctly
            for item_in_inv in reversed(self.inventory):
                if item_in_inv.name == item_name and consumed_count < qty_to_consume:
                    if item_in_inv.quantity > (qty_to_consume - consumed_count):
                        item_in_inv.quantity -= (qty_to_consume - consumed_count)
                        consumed_count = qty_to_consume
                        new_inventory.append(item_in_inv) # Add back with reduced quantity
                    else: # Consume entire stack
                        consumed_count += item_in_inv.quantity
                        # Don't add back to new_inventory
                else:
                    new_inventory.append(item_in_inv)
            self.inventory = list(reversed(new_inventory))
            if consumed_count < qty_to_consume:
                 # This indicates an issue if has_items passed
                return False
        return True

class TestShop(unittest.TestCase):

    def setUp(self):
        self.town = Town(name="Test Town", properties=[], nearby_resources=[], unique_npc_crafters=[])
        self.owner = MockCharacter(name="Test Owner", gold=10000)
        self.shop = Shop(name="The Test Shop", owner_name=self.owner.name, town=self.town, initial_gold=5000)

        # Add some basic ingredients to owner's inventory for crafting tests
        iron_ingot = Item(name="Iron Ingot", description="Desc", base_value=10, item_type="component", quality="Common"); iron_ingot.quantity = 20; self.owner.add_item_to_inventory(iron_ingot)
        leather_straps = Item(name="Leather Straps", description="Desc", base_value=5, item_type="component", quality="Common"); leather_straps.quantity = 10; self.owner.add_item_to_inventory(leather_straps)
        steel_ingot = Item(name="Steel Ingot", description="Desc", base_value=25, item_type="component", quality="Common"); steel_ingot.quantity = 10; self.owner.add_item_to_inventory(steel_ingot)
        oak_wood = Item(name="Oak Wood", description="Desc", base_value=8, item_type="component", quality="Common"); oak_wood.quantity = 5; self.owner.add_item_to_inventory(oak_wood)
        concentrated_herbs = Item(name="Concentrated Herbs", description="Desc", base_value=15, item_type="component", quality="Common"); concentrated_herbs.quantity = 10; self.owner.add_item_to_inventory(concentrated_herbs)
        purified_water = Item(name="Purified Water", description="Desc", base_value=5, item_type="component", quality="Common"); purified_water.quantity = 5; self.owner.add_item_to_inventory(purified_water)
        crystal_vial = Item(name="Crystal Vial", description="Desc", base_value=10, item_type="component", quality="Common"); crystal_vial.quantity = 5; self.owner.add_item_to_inventory(crystal_vial)
        herb_bundle = Item(name="Herb Bundle", description="Desc", base_value=5, item_type="component", quality="Common"); herb_bundle.quantity = 10; self.owner.add_item_to_inventory(herb_bundle)
        clean_water = Item(name="Clean Water", description="Desc", base_value=1, item_type="component", quality="Common"); clean_water.quantity = 10; self.owner.add_item_to_inventory(clean_water)


    def test_shop_initialization(self):
        self.assertEqual(self.shop.shop_level, 1)
        self.assertEqual(self.shop.specialization, "General Store")
        self.assertEqual(self.shop.reputation, 0)
        self.assertEqual(self.shop.max_inventory_slots, Shop.SHOP_LEVEL_CONFIG[1]["max_inventory_slots"])
        self.assertEqual(Shop.SHOP_LEVEL_CONFIG[1]["crafting_quality_bonus"], 0) # indirect check

    def test_set_specialization(self):
        self.shop.set_specialization("Blacksmith")
        self.assertEqual(self.shop.specialization, "Blacksmith")
        # Test invalid specialization
        initial_specialization = self.shop.specialization
        self.shop.set_specialization("InvalidSpec")
        self.assertEqual(self.shop.specialization, initial_specialization) # Should not change

    def test_can_craft_specialized_items(self):
        self.shop.set_specialization("Blacksmith")
        self.assertTrue(self.shop.can_craft("Iron Armor")) # Blacksmith recipe
        self.assertFalse(self.shop.can_craft("Greater Healing Potion")) # Alchemist recipe

        self.shop.set_specialization("Alchemist")
        self.assertTrue(self.shop.can_craft("Greater Healing Potion"))
        self.assertFalse(self.shop.can_craft("Iron Armor"))

        self.shop.set_specialization("General Store")
        self.assertFalse(self.shop.can_craft("Iron Armor"))
        self.assertTrue(self.shop.can_craft("Minor Healing Potion")) # Basic recipe

    def test_craft_specialized_item(self):
        self.shop.set_specialization("Blacksmith")
        # Ensure owner has ingredients for Iron Armor
        self.owner.inventory = [] # Clear and add specific
        iron_ingot_craft = Item(name="Iron Ingot", description="Desc", base_value=10, item_type="component", quality="Common"); iron_ingot_craft.quantity = 5; self.owner.add_item_to_inventory(iron_ingot_craft)
        leather_straps_craft = Item(name="Leather Straps", description="Desc", base_value=5, item_type="component", quality="Common"); leather_straps_craft.quantity = 2; self.owner.add_item_to_inventory(leather_straps_craft)

        item = self.shop.craft_item("Iron Armor", self.owner)
        self.assertIsNotNone(item)
        self.assertEqual(item.name, "Iron Armor")
        self.assertIn(item, self.shop.inventory)

        # Test crafting with wrong specialization
        self.shop.set_specialization("Alchemist")
        item_wrong_spec = self.shop.craft_item("Iron Armor", self.owner)
        self.assertIsNone(item_wrong_spec)

    def test_upgrade_shop(self):
        initial_level = self.shop.shop_level
        initial_slots = self.shop.max_inventory_slots

        upgraded = self.shop.upgrade_shop()
        self.assertTrue(upgraded)
        self.assertEqual(self.shop.shop_level, initial_level + 1)
        self.assertEqual(self.shop.max_inventory_slots, Shop.SHOP_LEVEL_CONFIG[initial_level + 1]["max_inventory_slots"])
        # Check quality bonus (indirectly, as it's used in _determine_quality)
        self.assertEqual(Shop.SHOP_LEVEL_CONFIG[self.shop.shop_level]["crafting_quality_bonus"], 1)


    def test_upgrade_shop_max_level(self):
        # Upgrade to max level first
        for _ in range(Shop.MAX_SHOP_LEVEL - self.shop.shop_level):
            self.shop.upgrade_shop()

        self.assertEqual(self.shop.shop_level, Shop.MAX_SHOP_LEVEL)
        upgraded_at_max = self.shop.upgrade_shop()
        self.assertFalse(upgraded_at_max)
        self.assertEqual(self.shop.shop_level, Shop.MAX_SHOP_LEVEL) # Still at max

    def test_inventory_limit(self):
        # Fill inventory to current max_slots -1
        for i in range(self.shop.max_inventory_slots -1):
            self.shop.add_item_to_inventory(Item(name=f"TestItem{i}", description="Desc", base_value=1, item_type="misc", quality="Common"))
        self.assertEqual(len(self.shop.inventory), self.shop.max_inventory_slots -1)

        # Add one more, should be fine
        self.shop.add_item_to_inventory(Item(name="LastNewItem", description="Desc", base_value=1, item_type="misc", quality="Common"))
        self.assertEqual(len(self.shop.inventory), self.shop.max_inventory_slots)

        # Try to add another new item, should fail
        self.shop.add_item_to_inventory(Item(name="OverflowItem", description="Desc", base_value=1, item_type="misc", quality="Common"))
        self.assertEqual(len(self.shop.inventory), self.shop.max_inventory_slots) # Should not have increased

        # Test stacking an existing item when full (e.g. LastNewItem now has quantity 1)
        # Add it again, it should stack
        last_new_item_stack = Item(name="LastNewItem", description="Desc", base_value=1, item_type="misc", quality="Common"); last_new_item_stack.quantity = 5; self.shop.add_item_to_inventory(last_new_item_stack)
        self.assertEqual(len(self.shop.inventory), self.shop.max_inventory_slots) # Still same number of slots
        found_item = next(item for item in self.shop.inventory if item.name == "LastNewItem")
        self.assertEqual(found_item.quantity, 1 + 5) # Original 1 + new 5


    @patch('random.random') # Add patch decorator
    def test_crafting_quality_bonus_on_level_up(self, mock_random): # Add mock_random argument
        item_name = "Minor Healing Potion"
        # Ensure character has ingredients
        herb_bundle_craft = Item(name="Herb Bundle", description="Desc", base_value=1,item_type="component", quality="Common"); herb_bundle_craft.quantity = 10; self.owner.add_item_to_inventory(herb_bundle_craft)
        clean_water_craft = Item(name="Clean Water", description="Desc", base_value=1,item_type="component", quality="Common"); clean_water_craft.quantity = 10; self.owner.add_item_to_inventory(clean_water_craft)

        # Craft at level 1 (no quality bonus)
        mock_random.return_value = 0.5 # Ensure no critical success/failure for this craft
        self.shop.crafting_experience[item_name] = 4 # Set to 4, so it becomes 5 before quality check -> Common
        item_lvl1 = self.shop.craft_item(item_name, self.owner) # crafting_experience is now 5
        quality_lvl1 = item_lvl1.quality
        # Remove item from inventory for next craft to be clean
        self.shop.remove_item_from_inventory(item_name, specific_item_to_remove=item_lvl1)


        # Upgrade shop to level 2 (quality bonus +1)
        self.shop.upgrade_shop()
        mock_random.return_value = 0.5 # Ensure no critical success/failure for this craft either
        # crafting_experience is already 5 from the previous craft.
        # It will be incremented to 6 before quality check for item_lvl2.
        # Effective count will be 6 (base from experience) + 1 (shop bonus) = 7 -> Uncommon.
        item_lvl2 = self.shop.craft_item(item_name, self.owner) # crafting_experience is now 6
        quality_lvl2 = item_lvl2.quality

        # Assuming QUALITY_THRESHOLDS = [(0, "Common"), (6, "Uncommon"), ...]
        self.assertEqual(quality_lvl1, "Common")
        self.assertEqual(quality_lvl2, "Uncommon")


    @patch('random.random')
    def test_craft_item_critical_success(self, mock_random):
        mock_random.return_value = Shop.CRITICAL_SUCCESS_CHANCE - 0.01 # Ensure critical success
        item_name = "Minor Healing Potion"
        self.shop.crafting_experience[item_name] = 0 # Base "Common"

        item = self.shop.craft_item(item_name, self.owner)
        self.assertIsNotNone(item)
        # Assuming QUALITY_THRESHOLDS = ["Common", "Uncommon", ...]
        # Common (index 0) + 1 (bonus) = Uncommon (index 1)
        self.assertEqual(item.quality, Shop.QUALITY_THRESHOLDS[1][1]) # Should be Uncommon

    @patch('random.random')
    def test_craft_item_critical_failure(self, mock_random):
        mock_random.return_value = Shop.CRITICAL_SUCCESS_CHANCE + (Shop.CRITICAL_FAILURE_CHANCE - 0.01) # Ensure critical failure
        item_name = "Minor Healing Potion"
        # Set experience high enough for "Uncommon" to test going down
        self.shop.crafting_experience[item_name] = 6 # Base "Uncommon"

        item = self.shop.craft_item(item_name, self.owner)
        self.assertIsNotNone(item)
        # Uncommon (index 1) - 1 (penalty) = Common (index 0)
        self.assertEqual(item.quality, Shop.QUALITY_THRESHOLDS[0][1]) # Should be Common

    @patch('random.random')
    def test_craft_item_normal_success(self, mock_random):
        mock_random.return_value = Shop.CRITICAL_SUCCESS_CHANCE + Shop.CRITICAL_FAILURE_CHANCE + 0.1 # Ensure normal success
        item_name = "Minor Healing Potion"
        self.shop.crafting_experience[item_name] = 0 # Base "Common"

        item = self.shop.craft_item(item_name, self.owner)
        self.assertIsNotNone(item)
        self.assertEqual(item.quality, Shop.QUALITY_THRESHOLDS[0][1]) # Should be Common

    def test_reputation_gain_on_hq_sale(self):
        item_to_sell = Item(name="Exquisite Sword", description="Desc", base_value=100, item_type="weapon", quality="Legendary")
        self.shop.add_item_to_inventory(item_to_sell)

        initial_reputation = self.shop.reputation
        self.shop.complete_sale_to_npc(item_to_sell.name, quality_to_sell=item_to_sell.quality)
        self.assertTrue(self.shop.reputation > initial_reputation)
        # Expected: Legendary = +4 rep
        self.assertEqual(self.shop.reputation, initial_reputation + 4)


    def test_reputation_gain_on_specialized_sale(self):
        self.shop.set_specialization("Blacksmith")
        # Craft Iron Armor - specialized, assume it becomes "Common"
        self.owner.inventory = []
        iron_ingot_spec = Item(name="Iron Ingot", description="Desc", base_value=10, item_type="component", quality="Common"); iron_ingot_spec.quantity = 5; self.owner.add_item_to_inventory(iron_ingot_spec)
        leather_straps_spec = Item(name="Leather Straps", description="Desc", base_value=5, item_type="component", quality="Common"); leather_straps_spec.quantity = 2; self.owner.add_item_to_inventory(leather_straps_spec)

        # Set crit chances to 0 for predictable quality
        _orig_crit_s, _orig_crit_f = Shop.CRITICAL_SUCCESS_CHANCE, Shop.CRITICAL_FAILURE_CHANCE
        Shop.CRITICAL_SUCCESS_CHANCE = 0.0
        Shop.CRITICAL_FAILURE_CHANCE = 0.0

        item_to_sell = self.shop.craft_item("Iron Armor", self.owner) # Should be Common
        Shop.CRITICAL_SUCCESS_CHANCE, Shop.CRITICAL_FAILURE_CHANCE = _orig_crit_s, _orig_crit_f

        self.assertIsNotNone(item_to_sell)
        self.assertEqual(item_to_sell.quality, "Common") # Common gives 0 quality rep bonus

        initial_reputation = self.shop.reputation
        self.shop.complete_sale_to_npc(item_to_sell.name, quality_to_sell=item_to_sell.quality)
        # Expected: Specialized item = +1 rep
        self.assertEqual(self.shop.reputation, initial_reputation + 1)

    def test_reputation_effect_on_npc_price(self):
        item_to_sell = Item(name="Test Gem", description="Desc", base_value=1000, item_type="gem", quality="Common")
        self.shop.add_item_to_inventory(item_to_sell)

        # Sale with 0 reputation
        self.shop.reputation = 0
        price_low_rep = self.shop.complete_sale_to_npc(item_to_sell.name, npc_offer_percentage=0.8)
        # Re-add item for next sale test
        self.shop.add_item_to_inventory(Item(name="Test Gem", description="Desc", base_value=1000, item_type="gem", quality="Common"))


        # Sale with high reputation
        self.shop.reputation = 50 # 50 * 0.001 = 0.05 bonus to multiplier
        price_high_rep = self.shop.complete_sale_to_npc(item_to_sell.name, npc_offer_percentage=0.8)

        self.assertTrue(price_high_rep > price_low_rep)

        # Expected math:
        # base_price for NPC = item_value * town_mod (1.0) * shop_markup (1.2) = 1000 * 1.2 = 1200
        # price_low_rep = 1200 * 0.8 = 960
        # price_high_rep = 1200 * (0.8 + 50 * 0.001) = 1200 * (0.8 + 0.05) = 1200 * 0.85 = 1020
        # (The cap is npc_offer_percentage * 1.1 = 0.8 * 1.1 = 0.88. 0.85 is within this)
        self.assertEqual(price_low_rep, int( (1000 * 1.2) * 0.8) )
        self.assertEqual(price_high_rep, int( (1000 * 1.2) * (0.8 + 0.05) ))


    def test_reputation_cap(self):
        self.shop.reputation = Shop.MAX_REPUTATION -1
        item_to_sell = Item(name="Legendary Helm", description="Desc", base_value=100, item_type="armor", quality="Legendary") # +4 rep
        self.shop.add_item_to_inventory(item_to_sell)
        self.shop.complete_sale_to_npc(item_to_sell.name)
        self.assertEqual(self.shop.reputation, Shop.MAX_REPUTATION)

    def test_shop_serialization(self):
        self.shop.shop_level = 2
        self.shop.max_inventory_slots = Shop.SHOP_LEVEL_CONFIG[2]["max_inventory_slots"]
        self.shop.specialization = "Alchemist"
        self.shop.reputation = 25
        self.shop.crafting_experience["Potion of Strength"] = 10
        self.shop.add_item_to_inventory(Item(name="Potion of Strength", description="Desc", base_value=60, item_type="potion", quality="Common"))

        shop_dict = self.shop.to_dict()

        # Create a new town object for from_dict, as it's required
        new_town = Town(name=self.town.name, properties=[], nearby_resources=[], unique_npc_crafters=[]) # Assuming town name is what's used for linkage
        loaded_shop = Shop.from_dict(shop_dict, new_town)

        self.assertEqual(loaded_shop.name, self.shop.name)
        self.assertEqual(loaded_shop.owner_name, self.shop.owner_name)
        self.assertEqual(loaded_shop.shop_level, 2)
        self.assertEqual(loaded_shop.specialization, "Alchemist")
        self.assertEqual(loaded_shop.reputation, 25)
        self.assertEqual(loaded_shop.max_inventory_slots, Shop.SHOP_LEVEL_CONFIG[2]["max_inventory_slots"])
        self.assertEqual(loaded_shop.crafting_experience["Potion of Strength"], 10)
        self.assertEqual(len(loaded_shop.inventory), 1)
        self.assertEqual(loaded_shop.inventory[0].name, "Potion of Strength")
        # Check that quality bonus would be correct (indirectly via config)
        self.assertEqual(Shop.SHOP_LEVEL_CONFIG[loaded_shop.shop_level]["crafting_quality_bonus"], Shop.SHOP_LEVEL_CONFIG[2]["crafting_quality_bonus"])


if __name__ == '__main__':
    unittest.main()
