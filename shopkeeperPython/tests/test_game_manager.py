import unittest
import unittest
from unittest.mock import patch, MagicMock
from io import StringIO # Import StringIO

from shopkeeperPython.game.game_manager import GameManager, EXPLORATION_FINDS, RESOURCE_ITEM_DEFINITIONS, HEMLOCK_HERBS
from shopkeeperPython.game.character import Character
from shopkeeperPython.game.shop import Shop
from shopkeeperPython.game.item import Item
from shopkeeperPython.game.town import Town
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

    # --- Tests for item quantity ---

    @patch('random.choice')
    def test_explore_town_action_item_with_quantity(self, mock_random_choice):
        """Test explore_town action finds an item with specified quantity."""
        # Ensure EXPLORATION_FINDS is globally available or mock game_manager.EXPLORATION_FINDS
        # For this test, let's assume EXPLORATION_FINDS is accessible for mocking its choice
        item_to_find = {"type": "item", "name": "Test Rock", "description": "A rock.", "base_value": 1, "item_type": "trinket", "quality": "Common", "quantity": 2}
        mock_random_choice.return_value = item_to_find

        # Mock random.random to prevent other random events from interfering
        with patch('random.random', return_value=0.99): # Make sure not to trigger other random events
             # Also ensure the 20% chance to find *something* passes
            with patch('shopkeeperPython.game.game_manager.random.random', return_value=0.10): # This random is for the 20% chance
                self.gm.perform_hourly_action("explore_town")

        found_item = next((item for item in self.player.inventory if item.name == "Test Rock"), None)
        self.assertIsNotNone(found_item)
        self.assertEqual(found_item.quantity, 2)

    @patch('random.choice')
    def test_explore_town_action_item_default_quantity(self, mock_random_choice):
        """Test explore_town action finds an item that defaults to quantity 1."""
        item_to_find = {"type": "item", "name": "Test Stick", "description": "A stick.", "base_value": 0, "item_type": "component", "quality": "Common"} # No quantity specified
        mock_random_choice.return_value = item_to_find

        with patch('random.random', return_value=0.99): # Prevent other random events
            with patch('shopkeeperPython.game.game_manager.random.random', return_value=0.10): # Pass 20% chance
                self.gm.perform_hourly_action("explore_town")

        found_item = next((item for item in self.player.inventory if item.name == "Test Stick"), None)
        self.assertIsNotNone(found_item)
        self.assertEqual(found_item.quantity, 1)

    def test_craft_action_shop_crafting_success(self):
        """Test successful shop crafting of an item with quantity_produced."""
        # Ensure Minor Healing Potion recipe exists and character has ingredients
        # Shop.BASIC_RECIPES is a class variable, so we can check/modify it for test setup if needed,
        # but ideally, it's pre-configured correctly.
        # For this test, assume "Minor Healing Potion" recipe exists and produces 1.
        # Ingredients are "Herb Bundle" and "Clean Water".

        self.player.inventory = [] # Clear inventory for specific test
        self.player.add_item_to_inventory(Item(name="Herb Bundle", description="Desc", base_value=1, item_type="component", quality="Common", quantity=1))
        self.player.add_item_to_inventory(Item(name="Clean Water", description="Desc", base_value=1, item_type="component", quality="Common", quantity=1))

        self.gm.shop.inventory = [] # Clear shop inventory

        with patch('random.random', return_value=0.99): # Prevent random events
            self.gm.perform_hourly_action("craft", {"item_name": "Minor Healing Potion"})

        # Check shop inventory for crafted item
        crafted_potion = next((item for item in self.gm.shop.inventory if item.name == "Minor Healing Potion"), None)
        self.assertIsNotNone(crafted_potion)
        # Assuming recipe quantity_produced is 1, or test needs to know the recipe's output quantity
        recipe_output_quantity = Shop.BASIC_RECIPES.get("Minor Healing Potion", {}).get("quantity_produced", 1)
        self.assertEqual(crafted_potion.quantity, recipe_output_quantity)

        # Check player inventory for consumed ingredients
        herb_bundle = next((item for item in self.player.inventory if item.name == "Herb Bundle"), None)
        clean_water = next((item for item in self.player.inventory if item.name == "Clean Water"), None)
        self.assertIsNone(herb_bundle) # Assuming full consumption
        self.assertIsNone(clean_water) # Assuming full consumption

    def test_craft_action_shop_crafting_insufficient_ingredients(self):
        """Test shop crafting failure due to insufficient ingredients."""
        self.player.inventory = [] # Ensure player has no ingredients
        self.gm.shop.inventory = []

        with patch('random.random', return_value=0.99): # Prevent random events
            self.gm.perform_hourly_action("craft", {"item_name": "Minor Healing Potion"})

        crafted_potion = next((item for item in self.gm.shop.inventory if item.name == "Minor Healing Potion"), None)
        self.assertIsNone(crafted_potion)
        # Player inventory should remain empty (or unchanged if they had other items)
        self.assertEqual(len(self.player.inventory), 0)


    @patch('random.randint')
    @patch('random.choice')
    def test_gather_resources_action(self, mock_random_choice, mock_random_randint):
        """Test gather_resources action gives item with correct quantity."""
        # Setup GM's current town and its resources
        self.gm.current_town.nearby_resources = ["Wild Herb"]
        # Ensure RESOURCE_ITEM_DEFINITIONS has "Wild Herb"
        if "Wild Herb" not in RESOURCE_ITEM_DEFINITIONS:
             RESOURCE_ITEM_DEFINITIONS["Wild Herb"] = {"description": "A wild herb.", "base_value": 2, "item_type": "component"}


        mock_random_choice.return_value = "Wild Herb"
        mock_random_randint.return_value = 3 # Mock the quantity gathered

        self.player.inventory = [] # Clear inventory for test

        with patch('random.random', return_value=0.99): # Prevent other random events
            self.gm.perform_hourly_action("gather_resources")

        gathered_herb = next((item for item in self.player.inventory if item.name == "Wild Herb"), None)
        self.assertIsNotNone(gathered_herb)
        self.assertEqual(gathered_herb.quantity, 3)

    def test_buy_from_npc_action(self):
        """Test buying an item from an NPC, checking quantity and gold."""
        # Ensure HEMLOCK_HERBS has "Sunpetal"
        if "Sunpetal" not in HEMLOCK_HERBS:
            HEMLOCK_HERBS["Sunpetal"] = {"description": "A sunny flower.", "base_value": 5, "item_type": "herb", "quality": "Common", "price": 8}

        sunpetal_price = HEMLOCK_HERBS["Sunpetal"]["price"]
        quantity_to_buy = 2
        expected_cost = sunpetal_price * quantity_to_buy

        initial_gold = 100
        self.player.gold = initial_gold
        self.player.inventory = [] # Clear inventory

        # Ensure the NPC exists in the current town (default is Starting Village)
        # Add Hemlock if not present for some reason (though default setup should have him)
        if not any(npc['name'] == "Old Man Hemlock" for npc in self.gm.current_town.unique_npc_crafters):
            self.gm.current_town.unique_npc_crafters.append({
                "name": "Old Man Hemlock", "specialty": "Herbalism", "services": [], "dialogue": []
            })


        with patch('random.random', return_value=0.99): # Prevent other random events
            self.gm.perform_hourly_action("buy_from_npc", {"npc_name": "Old Man Hemlock", "item_name": "Sunpetal", "quantity": quantity_to_buy})

        self.assertEqual(self.player.gold, initial_gold - expected_cost)
        bought_sunpetal = next((item for item in self.player.inventory if item.name == "Sunpetal"), None)
        self.assertIsNotNone(bought_sunpetal)
        self.assertEqual(bought_sunpetal.quantity, quantity_to_buy)

    # --- End of tests for item quantity ---

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

    @patch('random.uniform') # Outer patch, mock_uniform should be the second mock argument
    @patch('random.random')  # Inner patch, mock_random_roll should be the first mock argument
    def test_npc_purchase_chance_with_reputation(self, mock_random_roll, mock_uniform):

        # This test focuses on the chance calculation and if a sale is attempted.
        # It doesn't deeply verify the sale itself, which is Shop's responsibility.
        # This mock is for random.uniform, used in shop.complete_sale_to_npc
        mock_uniform.return_value = 0.9

        # Add an item to shop inventory for NPC to buy
        item_for_npc = Item(name="NPC Bait", description="Bait for NPCs", base_value=10, item_type="misc", quality="Common")

        # Ensure shop inventory is clear before adding the specific item for this test case
        self.gm.shop.inventory = []

        self.gm.shop.add_item_to_inventory(item_for_npc)
        # random.choice will now pick item_for_npc if the shop inventory only has this item for relevant cases.

        # Case 1: Low reputation (0), high random roll (no sale)
        self.gm.shop.reputation = 0
        # random.random() calls in perform_hourly_action: 1. skill_event_chance, 2. base_event_chance (if applicable), 3. npc_buy_chance
        mock_random_roll.side_effect = [0.99, 0.99, 0.25] # Skill event (no), Base event (no), NPC sale (no, 0.25 > 0.1)
        initial_shop_gold = self.gm.shop.gold
        # Use a non-interfering action that still allows NPC sales to occur
        with patch.object(self.gm.shop, 'complete_sale_to_npc', wraps=self.gm.shop.complete_sale_to_npc) as spy_complete_sale, \
             patch('shopkeeperPython.game.game_manager.EventManager.trigger_random_event', return_value=None), \
             patch('shopkeeperPython.game.game_manager.GameManager._handle_customer_interaction') as mock_interaction:
            self.gm.perform_hourly_action("wait")
            spy_complete_sale.assert_not_called()
        self.assertEqual(self.gm.shop.gold, initial_shop_gold)


        # Case 2: Low reputation (0), low random roll (sale attempt)
        mock_random_roll.side_effect = [0.99, 0.99, 0.05] # Skill event (no), Base event (no), NPC sale (yes, 0.05 < 0.1)
        initial_shop_gold = self.gm.shop.gold
        initial_shop_inventory_count = len(self.gm.shop.inventory)
        with patch.object(self.gm.shop, 'complete_sale_to_npc', wraps=self.gm.shop.complete_sale_to_npc) as spy_complete_sale, \
             patch('shopkeeperPython.game.game_manager.EventManager.trigger_random_event', return_value=None), \
             patch('shopkeeperPython.game.game_manager.GameManager._handle_customer_interaction') as mock_interaction:
            self.gm.perform_hourly_action("wait")
            if self.gm.shop.inventory : # Sale can only happen if item is in inventory
                 spy_complete_sale.assert_called_once() # Assert that a sale was processed
                 # We expect the item to be sold, gold increases, inventory decreases
                 self.assertTrue(self.gm.shop.gold > initial_shop_gold)
                 self.assertEqual(len(self.gm.shop.inventory), initial_shop_inventory_count -1)
            else: # Item was already sold or not added correctly
                 spy_complete_sale.assert_not_called()
                 self.assertEqual(self.gm.shop.gold, initial_shop_gold)


        # Re-add item for next test

        self.gm.shop.inventory = [] # Clear for next case
        item_for_npc_2 = Item(name="NPC Bait", description="Bait for NPCs", base_value=10, item_type="misc", quality="Common"); self.gm.shop.add_item_to_inventory(item_for_npc_2)
        # mock_choice.return_value = item_for_npc_2 # Ensure "NPC Bait" is chosen for this part too


        # Case 3: High reputation (100), roll that would fail for low rep but pass for high rep
        self.gm.shop.reputation = 100 # npc_buy_chance = min(0.1 + (100 * 0.001), 0.3) = min(0.1 + 0.1, 0.3) = 0.2
        mock_random_roll.side_effect = [0.99, 0.99, 0.15] # Skill event (no), Base event (no), NPC sale (yes, 0.15 < 0.2)
        initial_shop_gold = self.gm.shop.gold
        initial_shop_inventory_count = len(self.gm.shop.inventory)
        with patch.object(self.gm.shop, 'complete_sale_to_npc', wraps=self.gm.shop.complete_sale_to_npc) as spy_complete_sale, \
             patch('shopkeeperPython.game.game_manager.EventManager.trigger_random_event', return_value=None), \
             patch('shopkeeperPython.game.game_manager.GameManager._handle_customer_interaction') as mock_interaction:
            self.gm.perform_hourly_action("wait")
            if self.gm.shop.inventory:
                spy_complete_sale.assert_called_once()
                self.assertTrue(self.gm.shop.gold > initial_shop_gold)
                self.assertEqual(len(self.gm.shop.inventory), initial_shop_inventory_count -1)
            else:
                spy_complete_sale.assert_not_called()
                self.assertEqual(self.gm.shop.gold, initial_shop_gold)


        # Case 4: High reputation (100), roll that would fail even for high rep (above cap or calculated chance)
        self.gm.shop.inventory = [] # Clear for next case
        item_for_npc_3 = Item(name="NPC Bait", description="Bait for NPCs", base_value=10, item_type="misc", quality="Common"); self.gm.shop.add_item_to_inventory(item_for_npc_3)

        self.gm.shop.reputation = 100
        # Skill event (no), Base event (no), NPC sale (no, 0.28 > 0.2)
        mock_random_roll.side_effect = [0.99, 0.99, 0.28]
        initial_shop_gold = self.gm.shop.gold
        # Restore nested patches
        with patch.object(self.gm.shop, 'complete_sale_to_npc', wraps=self.gm.shop.complete_sale_to_npc) as spy_complete_sale, \
             patch('shopkeeperPython.game.game_manager.EventManager.trigger_random_event', return_value=None) as mock_trigger_event, \
             patch('shopkeeperPython.game.game_manager.GameManager._handle_customer_interaction') as mock_interaction:
            self.gm.perform_hourly_action("wait")
            spy_complete_sale.assert_not_called()
        self.assertEqual(self.gm.shop.gold, initial_shop_gold)


if __name__ == '__main__':
    unittest.main()
