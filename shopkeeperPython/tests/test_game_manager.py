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

    @patch('random.uniform')
    @patch('random.random')
    def test_npc_purchase_chance_with_reputation(self, mock_random_roll, mock_uniform):
        mock_uniform.return_value = 0.9 # for npc_offer_percentage if a sale occurs

        # Common item for sale
        item_to_sell_info = {"name": "NPC Bait", "description": "Bait for NPCs", "base_value": 10, "item_type": "misc", "quality": "Common"}

        # Case 1: Low reputation (0), high random roll (no sale)
        self.gm.shop.reputation = 0
        self.gm.shop.inventory = [] # Clear inventory
        self.gm.shop.add_item_to_inventory(Item(**item_to_sell_info))
        # For "wait" action: 1. base_event_chance, 2. npc_buy_chance, 3. customer_interaction_chance
        mock_random_roll.side_effect = [0.99, 0.25, 0.99] # Generic event(no), NPC buy(no), Customer interaction(no)
        initial_shop_gold = self.gm.shop.gold
        with patch.object(self.gm.shop, 'complete_sale_to_npc', wraps=self.gm.shop.complete_sale_to_npc) as spy_sale1, \
             patch('shopkeeperPython.game.game_manager.EventManager.trigger_random_event', return_value=None), \
             patch('shopkeeperPython.game.game_manager.GameManager._handle_customer_interaction'):
            self.gm.perform_hourly_action("wait")
            spy_sale1.assert_not_called()
        self.assertEqual(self.gm.shop.gold, initial_shop_gold)

        # Case 2: Low reputation (0), low random roll (sale attempt)
        self.gm.shop.reputation = 0
        self.gm.shop.inventory = [] # Clear inventory
        self.gm.shop.add_item_to_inventory(Item(**item_to_sell_info))
        initial_shop_gold = self.gm.shop.gold
        initial_inv_count = len(self.gm.shop.inventory) # Should be 1
        # For "wait" action: 1. base_event_chance, 2. npc_buy_chance, 3. customer_interaction_chance
        mock_random_roll.side_effect = [0.99, 0.05, 0.99] # Generic event(no), NPC buy(yes), Customer interaction(no)
        with patch.object(self.gm.shop, 'complete_sale_to_npc', wraps=self.gm.shop.complete_sale_to_npc) as spy_sale2, \
             patch('shopkeeperPython.game.game_manager.EventManager.trigger_random_event', return_value=None), \
             patch('shopkeeperPython.game.game_manager.GameManager._handle_customer_interaction'):
            self.gm.perform_hourly_action("wait")
            spy_sale2.assert_called_once()
        self.assertTrue(self.gm.shop.gold > initial_shop_gold)
        self.assertEqual(len(self.gm.shop.inventory), initial_inv_count - 1)

        # Case 3: High reputation (100), roll that would fail for low rep but pass for high rep
        self.gm.shop.reputation = 100
        self.gm.shop.inventory = []
        self.gm.shop.add_item_to_inventory(Item(**item_to_sell_info))
        initial_shop_gold = self.gm.shop.gold
        initial_inv_count = len(self.gm.shop.inventory) # Should be 1
        # For "wait" action: 1. base_event_chance, 2. npc_buy_chance, 3. customer_interaction_chance
        mock_random_roll.side_effect = [0.99, 0.15, 0.99] # Generic event(no), NPC buy(yes, 0.15 < 0.2), Customer interaction(no)
        with patch.object(self.gm.shop, 'complete_sale_to_npc', wraps=self.gm.shop.complete_sale_to_npc) as spy_sale3, \
             patch('shopkeeperPython.game.game_manager.EventManager.trigger_random_event', return_value=None), \
             patch('shopkeeperPython.game.game_manager.GameManager._handle_customer_interaction'):
            self.gm.perform_hourly_action("wait")
            spy_sale3.assert_called_once()
        self.assertTrue(self.gm.shop.gold > initial_shop_gold)
        self.assertEqual(len(self.gm.shop.inventory), initial_inv_count - 1)

        # Case 4: High reputation (100), roll that would fail even for high rep
        self.gm.shop.reputation = 100
        self.gm.shop.inventory = []
        self.gm.shop.add_item_to_inventory(Item(**item_to_sell_info))
        initial_shop_gold = self.gm.shop.gold
        # For "wait" action: 1. base_event_chance, 2. npc_buy_chance, 3. customer_interaction_chance
        mock_random_roll.side_effect = [0.99, 0.28, 0.99] # Generic event(no), NPC buy(no, 0.28 > 0.2), Customer interaction(no)
        with patch.object(self.gm.shop, 'complete_sale_to_npc', wraps=self.gm.shop.complete_sale_to_npc) as spy_sale4, \
             patch('shopkeeperPython.game.game_manager.EventManager.trigger_random_event', return_value=None), \
             patch('shopkeeperPython.game.game_manager.GameManager._handle_customer_interaction'):
            self.gm.perform_hourly_action("wait")
            spy_sale4.assert_not_called()
        self.assertEqual(self.gm.shop.gold, initial_shop_gold)

    def test_perform_action_rest_short_success(self):
        self.player.stats["CON"] = 12 # Corrected: Use self.stats
        # Recalculate base_max_hp and hp after changing CON if necessary, or ensure it's set.
        # For this test, setting hp directly after CON might be simplest.
        # Default con_mod is -5. With CON 12, con_mod is +1.
        # If base_max_hp was 5 (10 + -5*1), now it should be 10 + 1*1 = 11 if level 1.
        # Let's ensure base_max_hp is explicitly set for clarity or roll_stats is called.
        # For simplicity in test, let's ensure hp is set to a known value for the test logic.
        self.player.base_max_hp = 15 # Example: ensure max_hp is sufficient for the test
        self.player.hp = 5           # Corrected: Use self.hp
        initial_hp = self.player.hp
        initial_hit_dice = self.player.hit_dice = 3
        # self.player.hit_die_type = 8 # d8 - This attribute doesn't exist on Character, HD is d8 by default in rest logic

        with patch('random.randint', return_value=5): # Mock HD roll
            self.gm.perform_hourly_action("rest_short")

        self.assertEqual(self.player.hit_dice, initial_hit_dice - 1)
        # Expected HP: initial_hp (5) + roll (5) + CON_mod (1 based on CON 12) = 11
        self.assertEqual(self.player.hp, initial_hp + 5 + 1) # Corrected: Use self.hp
        self.assertIn("Spent 1 Hit Die, recovered 6 HP", self.test_output_stream.getvalue())
        # Check journal entry
        last_entry = self.player.journal[-1]
        self.assertEqual(last_entry.action_type, "Short Rest")
        self.assertEqual(last_entry.details.get("hp_recovered"), 6)

    def test_perform_action_rest_short_no_hit_dice(self):
        initial_hp = self.player.current_hp = 5
        self.player.hit_dice = 0

        self.gm.perform_hourly_action("rest_short")

        self.assertEqual(self.player.current_hp, initial_hp) # HP should not change
        self.assertIn("has no Hit Dice remaining", self.test_output_stream.getvalue())
        last_entry = self.player.journal[-1]
        self.assertEqual(last_entry.action_type, "Short Rest")
        self.assertEqual(last_entry.outcome, "No Hit Dice remaining.")

    def test_perform_action_rest_long_success(self):
        self.player.level = 3 # Set level first as it might influence max_hp calculation if not overridden
        self.player.base_max_hp = 20 # Set base_max_hp directly
        self.player.hp = 1     # Corrected from current_hp and set after base_max_hp
        self.player.hit_dice = 0
        self.player.exhaustion_level = 2
        self.player.add_item_to_inventory(Item(name="Food", description="Some food", base_value=1, item_type="consumable", quality="Common", quantity=1))
        self.player.add_item_to_inventory(Item(name="Drink", description="Some drink", base_value=1, item_type="consumable", quality="Common", quantity=1))

        initial_time = self.gm.time.current_hour

        self.gm.perform_hourly_action("rest_long")

        self.assertEqual(self.player.hp, self.player.get_effective_max_hp()) # Compare hp to effective_max_hp
        self.assertEqual(self.player.hit_dice, self.player.level)
        self.assertEqual(self.player.exhaustion_level, 1) # Reduced by 1
        self.assertIsNone(next((item for item in self.player.inventory if item.name == "Food"), None)) # Consumed
        self.assertIsNone(next((item for item in self.player.inventory if item.name == "Drink"), None)) # Consumed
        self.assertIn("HP fully restored. All Hit Dice recovered.", self.test_output_stream.getvalue())

        # Check time advanced by 8 hours
        expected_hour = (initial_time + 8) % 24
        self.assertEqual(self.gm.time.current_hour, expected_hour)

        last_entry = self.player.journal[-1]
        self.assertEqual(last_entry.action_type, "Long Rest")
        self.assertTrue(last_entry.outcome.startswith("HP fully restored."))

    def test_perform_action_rest_long_no_food(self):
        self.player.current_hp = 1
        self.player.exhaustion_level = 0
        # No food, but has drink
        self.player.add_item_to_inventory(Item(name="Drink", description="Some drink", base_value=1, item_type="consumable", quality="Common", quantity=1))
        initial_exhaustion = self.player.exhaustion_level

        self.gm.perform_hourly_action("rest_long")

        self.assertNotEqual(self.player.current_hp, self.player.max_hp) # HP should not be fully restored
        self.assertEqual(self.player.exhaustion_level, initial_exhaustion + 1) # Gained exhaustion
        self.assertIn("Failed to complete long rest. Missing: Food", self.test_output_stream.getvalue())
        last_entry = self.player.journal[-1]
        self.assertEqual(last_entry.action_type, "Long Rest")
        self.assertTrue(last_entry.outcome.startswith("Failed to complete long rest."))

    def test_perform_action_gather_rumors_tavern(self):
        # Ensure the current town has a tavern with the action
        # Default setup has Starting Village, which we modified to have "The Sleeping Dragon Inn"
        # Or switch to Steel Flow City
        self.gm.current_town = self.gm.towns_map["Steel Flow City"] # Has "The Rusty Pickaxe Tavern"

        initial_journal_len = len(self.player.journal)
        with patch('random.choice', return_value="Test rumor") as mock_choice:
            self.gm.perform_hourly_action("gather_rumors_tavern")

        self.assertIn("Test rumor", self.test_output_stream.getvalue())
        self.assertEqual(len(self.player.journal), initial_journal_len + 1)
        last_entry = self.player.journal[-1]
        self.assertEqual(last_entry.action_type, "Gather Rumors")
        self.assertEqual(last_entry.details.get("rumor"), "Test rumor")
        # Check if XP was awarded (player's XP should increase)
        # Assuming base XP is 0 or tracking XP gain specifically
        # For simplicity, we'll just check if the output indicates XP gain if applicable.
        # The action itself awards XP, so self.player.xp should have increased.

    def test_action_study_local_history(self):
        initial_xp = self.player.xp
        initial_journal_len = len(self.player.journal)

        with patch('random.random', return_value=0.5) as mock_random: # Not triggering the 10% discovery
            self.gm.perform_hourly_action("study_local_history")

        self.assertIn(f"{self.player.name} spends an hour studying local history", self.test_output_stream.getvalue())
        self.assertIn("Learned some interesting historical facts", self.test_output_stream.getvalue())
        self.assertEqual(self.player.pending_xp, initial_xp + 10) # Check pending_xp
        self.assertEqual(len(self.player.journal), initial_journal_len + 1)
        last_entry = self.player.journal[-1]
        self.assertEqual(last_entry.action_type, "Study History")
        self.assertEqual(last_entry.outcome, "Learned some interesting historical facts about the area.")

        # Test the discovery case
        # initial_xp here refers to self.player.xp which is 0.
        # pending_xp from the previous action was 10.
        previous_pending_xp = self.player.pending_xp
        # Clear the output stream for the second action part of the test for clearer assertion
        self.test_output_stream.truncate(0)
        self.test_output_stream.seek(0)

        with patch('random.random', return_value=0.05) as mock_random: # Triggering the 10% discovery
            self.gm.perform_hourly_action("study_local_history")
        self.assertIn("Uncovered a minor local secret", self.test_output_stream.getvalue())
        # XP from this action (10 base + 5 discovery) is added to previous pending_xp
        self.assertEqual(self.player.pending_xp, previous_pending_xp + 10 + 5)
        last_entry_discovery = self.player.journal[-1] # This will be the journal entry from the second action
        self.assertEqual(last_entry_discovery.outcome, "Uncovered a minor local secret or a piece of forgotten lore!")


    def test_action_organize_inventory(self):
        initial_xp = self.player.xp
        initial_journal_len = len(self.player.journal)

        self.gm.perform_hourly_action("organize_inventory")

        self.assertIn(f"{self.player.name} meticulously organizes their personal inventory", self.test_output_stream.getvalue())
        self.assertEqual(self.player.pending_xp, initial_xp + 3) # Check pending_xp
        self.assertEqual(len(self.player.journal), initial_journal_len + 1)
        last_entry = self.player.journal[-1]
        self.assertEqual(last_entry.action_type, "Organize Inventory")
        self.assertEqual(last_entry.outcome, "Everything is neat and tidy.")

    def test_action_post_advertisements(self):
        initial_xp = self.player.xp
        initial_journal_len = len(self.player.journal)
        initial_boost = self.gm.shop.temporary_customer_boost

        self.gm.perform_hourly_action("post_advertisements")

        self.assertIn(f"{self.player.name} posts advertisements for '{self.gm.shop.name}'", self.test_output_stream.getvalue())
        # The specific phrase "Hopefully, this will attract more customers!" is part of the journal outcome,
        # and might be appended with more details. The _print statement is more about the boost.
        self.assertIn("Applied a small temporary boost to customer attraction", self.test_output_stream.getvalue())
        self.assertEqual(self.player.pending_xp, initial_xp + 7) # Check pending_xp
        self.assertEqual(len(self.player.journal), initial_journal_len + 1)
        last_entry = self.player.journal[-1]
        self.assertEqual(last_entry.action_type, "Post Advertisements")
        self.assertTrue(last_entry.outcome.startswith("Hopefully, this will attract more customers!")) # Journal outcome check is good
        self.assertAlmostEqual(self.gm.shop.temporary_customer_boost, initial_boost + 0.05)


if __name__ == '__main__':
    unittest.main()
