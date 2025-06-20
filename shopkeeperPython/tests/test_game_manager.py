import unittest
from unittest.mock import patch
from io import StringIO # Import StringIO

from shopkeeperPython.game.game_manager import GameManager
from shopkeeperPython.game.character import Character
from shopkeeperPython.game.shop import Shop
from shopkeeperPython.game.item import Item
# from shopkeeperPython.game.town import Town # Removed
# Assuming GameTime is also needed if perform_hourly_action directly uses it beyond just advancing hours
# from shopkeeperPython.game.time_system import GameTime # Removed


class TestGameManager(unittest.TestCase):

    def setUp(self):
        # Suppress print output during tests by redirecting stdout
        # self.patcher = patch('sys.stdout', new_callable=MagicMock)
        # self.mock_stdout = self.patcher.start()

        self.player = Character(name="Test Player") # Start with plenty of gold
        self.player.gold = 20000
        # GameManager init can be basic, setup_for_character does the heavy lifting
        self.test_output_stream = StringIO() # Create a StringIO instance
        self.gm = GameManager(player_character=self.player, output_stream=self.test_output_stream) # Pass it to GameManager
        self.gm.setup_for_character(self.player)

        # Ensure the shop has some basic ingredients for player/shop crafting tests
        # Player inventory for actions that require player to have items
        item1 = Item(name="Iron Ingot", description="An ingot of iron", base_value=10, item_type="component", quality="Common"); item1.quantity = 20; self.player.add_item_to_inventory(item1)
        item2 = Item(name="Leather Straps", description="Some leather straps", base_value=5, item_type="component", quality="Common"); item2.quantity = 10; self.player.add_item_to_inventory(item2)
        item3 = Item(name="Steel Ingot", description="An ingot of steel", base_value=25, item_type="component", quality="Common"); item3.quantity = 10; self.player.add_item_to_inventory(item3)
        item4 = Item(name="Oak Wood", description="A piece of oak wood", base_value=8, item_type="component", quality="Common"); item4.quantity = 5; self.player.add_item_to_inventory(item4)

    # def tearDown(self):
        # self.patcher.stop() # Stop redirecting stdout

    def test_initial_setup_for_character(self):
        self.assertIsNotNone(self.gm.shop)
        self.assertEqual(self.gm.shop.owner_name, self.player.name)
        self.assertEqual(self.gm.shop.specialization, "General Store")
        self.assertEqual(self.gm.shop.shop_level, 1)
        self.assertEqual(self.gm.shop.reputation, 0)
        self.assertTrue(self.gm.is_game_setup)

    def test_action_set_shop_specialization(self):
        self.gm.perform_hourly_action("set_shop_specialization", {"specialization_name": "Blacksmith"})
        self.assertEqual(self.gm.shop.specialization, "Blacksmith")

        # Test setting an invalid specialization
        self.gm.perform_hourly_action("set_shop_specialization", {"specialization_name": "InvalidSpec"})
        self.assertEqual(self.gm.shop.specialization, "Blacksmith") # Should remain Blacksmith

    def test_action_upgrade_shop_successful(self):
        initial_gold = self.player.gold
        initial_shop_level = self.gm.shop.shop_level
        cost_to_upgrade = Shop.SHOP_LEVEL_CONFIG[initial_shop_level]["cost_to_upgrade"]

        self.gm.perform_hourly_action("upgrade_shop")

        self.assertEqual(self.player.gold, initial_gold - cost_to_upgrade)
        self.assertEqual(self.gm.shop.shop_level, initial_shop_level + 1)
        self.assertEqual(self.gm.shop.max_inventory_slots, Shop.SHOP_LEVEL_CONFIG[initial_shop_level + 1]["max_inventory_slots"])

    def test_action_upgrade_shop_insufficient_gold(self):
        self.player.gold = 100 # Not enough for first upgrade (500g)
        initial_shop_level = self.gm.shop.shop_level

        self.gm.perform_hourly_action("upgrade_shop")

        self.assertEqual(self.player.gold, 100) # Gold should not change
        self.assertEqual(self.gm.shop.shop_level, initial_shop_level) # Level should not change

    @patch('random.random', return_value=0.99) # Prevent random events
    def test_action_upgrade_shop_max_level(self, mock_random_main): # mock_random_main to avoid conflict if other patches are added
        # Manually set shop to max level for testing this action
        self.gm.shop.shop_level = Shop.MAX_SHOP_LEVEL
        initial_gold = self.player.gold

        self.gm.perform_hourly_action("upgrade_shop")

        self.assertEqual(self.player.gold, initial_gold) # Gold should not change
        self.assertEqual(self.gm.shop.shop_level, Shop.MAX_SHOP_LEVEL) # Level should remain max

    @patch('random.random') # Patch to control NPC sale chance
    def test_action_craft_advanced_item_correct_specialization(self, mock_random):
        mock_random.return_value = 0.99 # Ensure NPC sale doesn't happen during specialization set or craft
        self.gm.perform_hourly_action("set_shop_specialization", {"specialization_name": "Blacksmith"})
        # Player already has ingredients from setUp for Iron Armor (5 Iron Ingot, 2 Leather Straps)

        initial_inventory_count = len(self.gm.shop.inventory)
        self.gm.perform_hourly_action("craft", {"item_name": "Iron Armor"})

        self.assertEqual(len(self.gm.shop.inventory), initial_inventory_count + 1)
        crafted_item = next((item for item in self.gm.shop.inventory if item.name == "Iron Armor"), None)
        self.assertIsNotNone(crafted_item)

    @patch('random.random') # Patch to control NPC sale chance
    def test_action_craft_advanced_item_wrong_specialization(self, mock_random):
        mock_random.return_value = 0.99 # Ensure NPC sale doesn't happen
        self.gm.perform_hourly_action("set_shop_specialization", {"specialization_name": "Alchemist"})
        # Player has ingredients, but shop has wrong specialization for Iron Armor

        initial_inventory_count = len(self.gm.shop.inventory)
        self.gm.perform_hourly_action("craft", {"item_name": "Iron Armor"})

        self.assertEqual(len(self.gm.shop.inventory), initial_inventory_count) # Item should not be crafted

    @patch('random.random') # To control the NPC buy chance roll
    @patch('random.uniform') # To control the NPC offer percentage roll

    def test_npc_purchase_chance_with_reputation(self, mock_uniform, mock_random_roll): # Removed mock_choice

        # This test focuses on the chance calculation and if a sale is attempted.
        # It doesn't deeply verify the sale itself, which is Shop's responsibility.
        mock_uniform.return_value = 0.9 # Ensure NPC offers a decent percentage (e.g., 90%)

        # Add an item to shop inventory for NPC to buy
        item_for_npc = Item(name="NPC Bait", description="Bait for NPCs", base_value=10, item_type="misc", quality="Common")

        # Ensure shop inventory is clear before adding the specific item for this test case
        self.gm.shop.inventory = []

        self.gm.shop.add_item_to_inventory(item_for_npc)
        # random.choice will now pick item_for_npc if the shop inventory only has this item for relevant cases.

        # Case 1: Low reputation (0), high random roll (no sale)
        self.gm.shop.reputation = 0
        mock_random_roll.return_value = 0.25 # Higher than 0.1 + (0 * 0.001) = 0.1
        initial_shop_gold = self.gm.shop.gold
        with patch.object(self.gm.shop, 'complete_sale_to_npc', wraps=self.gm.shop.complete_sale_to_npc) as spy_complete_sale:
            self.gm.perform_hourly_action("wait") # Any non-shop interfering action
            spy_complete_sale.assert_not_called()
        self.assertEqual(self.gm.shop.gold, initial_shop_gold)


        # Case 2: Low reputation (0), low random roll (sale attempt)
        mock_random_roll.return_value = 0.05 # Lower than 0.1
        initial_shop_gold = self.gm.shop.gold
        initial_shop_inventory_count = len(self.gm.shop.inventory)
        with patch.object(self.gm.shop, 'complete_sale_to_npc', wraps=self.gm.shop.complete_sale_to_npc) as spy_complete_sale:
            self.gm.perform_hourly_action("wait")
            spy_complete_sale.assert_called_once() # Assert that a sale was processed
        # We expect the item to be sold, gold increases, inventory decreases
        self.assertTrue(self.gm.shop.gold > initial_shop_gold)
        self.assertEqual(len(self.gm.shop.inventory), initial_shop_inventory_count -1)


        # Re-add item for next test

        self.gm.shop.inventory = [] # Clear for next case
        item_for_npc_2 = Item(name="NPC Bait", description="Bait for NPCs", base_value=10, item_type="misc", quality="Common"); self.gm.shop.add_item_to_inventory(item_for_npc_2)
        # mock_choice.return_value = item_for_npc_2 # Ensure "NPC Bait" is chosen for this part too


        # Case 3: High reputation (100), roll that would fail for low rep but pass for high rep
        self.gm.shop.reputation = 100 # npc_buy_chance = min(0.1 + (100 * 0.001), 0.3) = min(0.1 + 0.1, 0.3) = 0.2
        mock_random_roll.return_value = 0.15 # Higher than 0.1 (low rep chance), lower than 0.2 (high rep chance)
        initial_shop_gold = self.gm.shop.gold
        initial_shop_inventory_count = len(self.gm.shop.inventory)
        with patch.object(self.gm.shop, 'complete_sale_to_npc', wraps=self.gm.shop.complete_sale_to_npc) as spy_complete_sale:
            self.gm.perform_hourly_action("wait")
            spy_complete_sale.assert_called_once()
        self.assertTrue(self.gm.shop.gold > initial_shop_gold)
        self.assertEqual(len(self.gm.shop.inventory), initial_shop_inventory_count -1)

        # Case 4: High reputation (100), roll that would fail even for high rep (above cap or calculated chance)

        self.gm.shop.inventory = [] # Clear for next case
        item_for_npc_3 = Item(name="NPC Bait", description="Bait for NPCs", base_value=10, item_type="misc", quality="Common"); self.gm.shop.add_item_to_inventory(item_for_npc_3)
        # mock_choice.return_value = item_for_npc_3 # Ensure "NPC Bait" is chosen

        self.gm.shop.reputation = 100
        mock_random_roll.return_value = 0.28 # Higher than 0.2
        initial_shop_gold = self.gm.shop.gold
        with patch.object(self.gm.shop, 'complete_sale_to_npc', wraps=self.gm.shop.complete_sale_to_npc) as spy_complete_sale:
            self.gm.perform_hourly_action("wait")
            spy_complete_sale.assert_not_called()
        self.assertEqual(self.gm.shop.gold, initial_shop_gold)


if __name__ == '__main__':
    unittest.main()
