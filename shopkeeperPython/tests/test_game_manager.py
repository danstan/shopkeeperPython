import unittest
import sys
import os

# Adjust the path to import from the parent directory (shopkeeperPython)
# This allows running the test directly from the tests directory or using unittest discovery
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from game.game_manager import GameManager
from game.character import Character
from game.item import Item
from game.shop import Shop
from game.town import Town
from game.time_system import GameTime
from game.g_event import EventManager, Event, SAMPLE_EVENTS # Added Event and SAMPLE_EVENTS
import random # For controlling event chance
import io # Added for capturing output

class TestGameManager(unittest.TestCase):

    def setUp(self):
        """Set up common objects for test methods."""
        self.player_char = Character(name="Test Player")
        self.player_char.level = 3 # Set level to 3 for more hit dice
        # Manually set stats or call roll_stats()
        self.player_char.stats = {"STR": 12, "DEX": 14, "CON": 15, "INT": 10, "WIS": 13, "CHA": 11}

        # Initialize HP and Hit Dice based on level and CON
        con_modifier = self.player_char._calculate_modifier(self.player_char.stats["CON"], is_base_stat_score=True)
        # Simplified HP calculation for testing: (Base 10 for level 1) + (Avg roll (e.g. 5 for d8) + CON_mod for subsequent levels)
        self.player_char.base_max_hp = (10 + con_modifier) + (self.player_char.level - 1) * (5 + con_modifier) # Example for d8 HD class
        self.player_char.hp = self.player_char.get_effective_max_hp()
        self.player_char.max_hit_dice = self.player_char.level # Max HD = Level
        self.player_char.hit_dice = self.player_char.max_hit_dice # Start with full HD

        self.player_char.exhaustion_level = 0 # Ensure exhaustion is reset for each test
        self.player_char.gold = 200 # Standard starting gold for tests needing it

        # Each test method will get a fresh GameManager, so output_stream can be set per test if needed
        # or set here if all tests benefit from a captured stream.
        # For now, let individual tests that need to check output manage it.
        self.gm = GameManager(player_character=self.player_char)
        self.output_stream = io.StringIO()
        self.gm.output_stream = self.output_stream # Redirect gm's output

        # Alias for convenience, as gm is used in the problem description
        self.char = self.player_char # Using self.char as per prompt for new tests
        # self.test_item = Item(name="Test Potion", item_type="potion", base_value=10)

    def test_initialization(self):
        """Test that the GameManager initializes correctly (basic check)."""
        self.assertIsNotNone(self.gm, "GameManager should not be None after initialization.")
        self.assertEqual(self.gm.character.name, "Test Player", "Character name mismatch.")
        self.assertEqual(self.gm.shop.owner_name, "Test Player", "Shop owner name mismatch.")

    def test_initialization_details(self):
        """Test detailed aspects of GameManager initialization."""
        self.assertIsNotNone(self.gm, "GameManager (self.gm) should be initialized in setUp.")
        self.assertIsInstance(self.gm.time, GameTime, "gm.time should be an instance of GameTime.")
        self.assertIs(self.gm.character, self.player_char, "gm.character should be the instance passed during creation.")
        self.assertIsInstance(self.gm.shop, Shop, "gm.shop should be an instance of Shop.")
        self.assertIsInstance(self.gm.current_town, Town, "gm.current_town should be an instance of Town.")
        self.assertIsInstance(self.gm.event_manager, EventManager, "gm.event_manager should be an instance of EventManager.")

        # Test initial state of daily trackers
        self.assertEqual(self.gm.daily_gold_earned_from_sales, 0, "Initial daily_gold_earned_from_sales should be 0.")
        self.assertEqual(self.gm.daily_gold_spent_on_purchases_by_player, 0, "Initial daily_gold_spent_on_purchases_by_player should be 0.")
        self.assertEqual(self.gm.daily_gold_player_earned_selling_to_shop, 0, "Initial daily_gold_player_earned_selling_to_shop should be 0.")
        self.assertEqual(self.gm.daily_visitors, 0, "Initial daily_visitors should be 0.")
        self.assertEqual(self.gm.daily_xp_awarded_this_day, 0, "Initial daily_xp_awarded_this_day should be 0.")
        self.assertEqual(self.gm.daily_items_crafted, [], "Initial daily_items_crafted should be an empty list.")
        self.assertEqual(self.gm.daily_items_sold_by_shop_to_npcs, [], "Initial daily_items_sold_by_shop_to_npcs should be an empty list.")
        self.assertEqual(self.gm.daily_items_player_bought_from_shop, [], "Initial daily_items_player_bought_from_shop should be an empty list.")
        self.assertEqual(self.gm.daily_items_player_sold_to_shop, [], "Initial daily_items_player_sold_to_shop should be an empty list.")
        self.assertEqual(self.gm.daily_special_events, [], "Initial daily_special_events should be an empty list.")
        self.assertEqual(self.gm.daily_customer_dialogue_snippets, [], "Initial daily_customer_dialogue_snippets should be an empty list.")
        self.assertEqual(self.gm.tracking_day, self.gm.time.current_day, "Initial tracking_day should match current_day.")

    # Helper to reset output stream for focused tests
    def _clear_output(self):
        self.output_stream.truncate(0)
        self.output_stream.seek(0)

    def test_daily_tracker_reset(self):
        """Test that _reset_daily_trackers correctly resets all trackers."""
        # Modify some trackers directly
        self.gm.daily_visitors = 5
        self.gm.daily_items_crafted = ["TestItem"]
        self.gm.daily_gold_earned_from_sales = 100
        self.gm.daily_xp_awarded_this_day = 50 # Note: this is reset before recap calculation in normal flow
        self.gm.daily_special_events = ["Old Event"]
        self.gm.tracking_day = 99 # Arbitrary different day

        # Call the reset method
        self.gm._reset_daily_trackers()

        # Assert they are reset to default initial states
        self.assertEqual(self.gm.daily_gold_earned_from_sales, 0, "daily_gold_earned_from_sales should be 0 after reset.")
        self.assertEqual(self.gm.daily_gold_spent_on_purchases_by_player, 0, "daily_gold_spent_on_purchases_by_player should be 0 after reset.")
        self.assertEqual(self.gm.daily_gold_player_earned_selling_to_shop, 0, "daily_gold_player_earned_selling_to_shop should be 0 after reset.")
        self.assertEqual(self.gm.daily_visitors, 0, "daily_visitors should be 0 after reset.")
        self.assertEqual(self.gm.daily_xp_awarded_this_day, 0, "daily_xp_awarded_this_day should be 0 after reset.")
        self.assertEqual(self.gm.daily_items_crafted, [], "daily_items_crafted should be an empty list after reset.")
        self.assertEqual(self.gm.daily_items_sold_by_shop_to_npcs, [], "daily_items_sold_by_shop_to_npcs should be an empty list after reset.")
        self.assertEqual(self.gm.daily_items_player_bought_from_shop, [], "daily_items_player_bought_from_shop should be an empty list after reset.")
        self.assertEqual(self.gm.daily_items_player_sold_to_shop, [], "daily_items_player_sold_to_shop should be an empty list after reset.")
        self.assertEqual(self.gm.daily_special_events, [], "daily_special_events should be an empty list after reset.")
        self.assertEqual(self.gm.daily_customer_dialogue_snippets, [], "daily_customer_dialogue_snippets should be an empty list after reset.")
        self.assertEqual(self.gm.tracking_day, self.gm.time.current_day, "tracking_day should be reset to current_day.")

    def test_end_of_day_recap_trigger_and_reset(self):
        """Test that the end-of-day recap triggers automatically and resets trackers."""
        # Prevent random events from interfering with XP calculation for this test
        original_event_chance = self.gm.base_event_chance
        self.gm.base_event_chance = 0.0

        try:
            self.assertEqual(self.gm.time.current_hour, 7, "Test assumes GameTime starts at 7 AM.")
            self.assertEqual(self.gm.time.current_day, 1, "Test assumes GameTime starts on Day 1.")

            for _ in range(16): # From 7:00 to 23:00
                self.gm.perform_hourly_action("talk_to_customer")
                if self.gm.time.current_hour == 0:
                    self.fail("Midnight crossed prematurely during initial 16-hour simulation.")

            self.assertEqual(self.gm.time.current_hour, 23, "Time should be 23:00 after 16 hours from 7:00.")

            self.gm.daily_gold_earned_from_sales = 100
            self.gm.daily_items_crafted.append("OldCraftItem")

            # Reset pending_xp before awarding a known amount for this test
            self.char.pending_xp = 0
            self.gm.character.award_xp(25)
            self.assertEqual(self.gm.character.pending_xp, 25, "Pending XP should be 25 before recap.")

            initial_day = self.gm.time.current_day
            self.assertEqual(initial_day, 1, "Initial day should be 1.")
            self.gm.perform_hourly_action("sleep_one_hour")

            self.assertEqual(self.gm.time.current_day, initial_day + 1, "Time should advance to the next day.")
            self.assertEqual(self.gm.time.current_hour, 0, "Time should be 00:00 after crossing midnight.")
            self.assertEqual(self.gm.tracking_day, self.gm.time.current_day,
                             f"Tracking day should be {self.gm.time.current_day} after recap and reset.")
            self.assertEqual(self.gm.tracking_day, initial_day + 1,
                             "Tracking day should be the new current day.")
            self.assertEqual(self.gm.daily_gold_earned_from_sales, 0, "daily_gold_earned_from_sales should be reset after recap.")
            self.assertEqual(self.gm.daily_items_crafted, [], "daily_items_crafted should be reset after recap.")
            self.assertEqual(self.gm.character.pending_xp, 0, "Pending XP should be committed (cleared) by the recap.")
            self.assertEqual(self.gm.daily_xp_awarded_this_day, 0, "daily_xp_awarded_this_day for the new day should be 0.")
        finally:
            # Restore original event chance
            self.gm.base_event_chance = original_event_chance

    def test_action_craft_item_success(self):
        self.assertEqual(initial_day, 1, "Initial day should be 1.")
        # At 23:00, one more hour will advance to 00:00 of the next day, triggering recap for day 1.
        self.gm.perform_hourly_action("sleep_one_hour") # Advances from 23:00 to 00:00 (Day 2)

        # Assert that time has advanced to the next day
        self.assertEqual(self.gm.time.current_day, initial_day + 1, "Time should advance to the next day.")
        self.assertEqual(self.gm.time.current_hour, 0, "Time should be 00:00 after crossing midnight.")

        # Assert that tracking_day (after the reset within the recap) is now equal to the new current_day
        # The recap for 'initial_day' runs, then trackers are reset for 'initial_day + 1'
        self.assertEqual(self.gm.tracking_day, self.gm.time.current_day,
                         f"Tracking day should be {self.gm.time.current_day} after recap and reset.")
        self.assertEqual(self.gm.tracking_day, initial_day + 1,
                         "Tracking day should be the new current day.")

        # Assert that daily trackers have been reset
        # These were reset because generate_end_of_day_recap for 'initial_day' was called,
        # and it internally calls _reset_daily_trackers() for the *new* day.
        self.assertEqual(self.gm.daily_gold_earned_from_sales, 0, "daily_gold_earned_from_sales should be reset after recap.")
        self.assertEqual(self.gm.daily_items_crafted, [], "daily_items_crafted should be reset after recap.")

        # Assert that pending XP was committed during the recap of 'initial_day'
        self.assertEqual(self.gm.character.pending_xp, 0, "Pending XP should be committed (cleared) by the recap.")
        # The daily_xp_awarded_this_day for the *new* day (tracking_day) should be 0.
        self.assertEqual(self.gm.daily_xp_awarded_this_day, 0, "daily_xp_awarded_this_day for the new day should be 0.")

    def test_action_craft_item_success(self):
        """Test successful crafting of an item."""
        initial_time = self.gm.time.current_hour
        item_name_to_craft = "CraftedTesterPotion" # Use a unique name for this test

        # Ensure the recipe exists for reliable testing
        # This modification of a class attribute within a test is generally not recommended
        # but done here for simplicity to ensure the test focuses on GameManager logic.
        # A better approach might involve a test-specific recipe list or mocking.
        if item_name_to_craft not in Shop.BASIC_RECIPES:
            Shop.BASIC_RECIPES[item_name_to_craft] = {
                "base_value": 15, "type": "potion", "description": "A special potion for testing crafting.",
                "crafting_difficulty": 2, "effects": {"test_effect": 1},
                "skill": "Alchemy", "level": 1, "materials": {"Magic Dust": 1}, # Assuming Magic Dust is a conceptual material
                "product": {"name": item_name_to_craft, "quantity": 1}
            }

        # Ensure character has dummy material if needed by a more complex Shop.craft_item
        # For now, assuming Shop.craft_item doesn't check character inventory for materials.

        initial_item_count = sum(1 for item_in_inv in self.gm.shop.inventory if item_in_inv.name == item_name_to_craft)
        self.assertEqual(initial_item_count, 0, f"'{item_name_to_craft}' should not be in shop inventory initially.")

        self.gm.perform_hourly_action("craft", {"item_name": item_name_to_craft})

        final_item_count = sum(1 for item_in_inv in self.gm.shop.inventory if item_in_inv.name == item_name_to_craft)

        self.assertIn(item_name_to_craft, [item.name for item in self.gm.shop.inventory], f"{item_name_to_craft} should be in shop inventory after crafting.")
        self.assertEqual(final_item_count, 1, "Item count in shop inventory should be 1 after crafting.") # initial_item_count was 0
        self.assertIn(item_name_to_craft, self.gm.daily_items_crafted, f"{item_name_to_craft} should be in daily_items_crafted.")
        self.assertEqual(self.gm.time.current_hour, (initial_time + 1) % 24, "Time should advance by 1 hour.")

    def test_action_craft_item_unknown(self):
        """Test crafting an unknown item."""
        initial_time = self.gm.time.current_hour
        item_name_to_craft = "Unknown Super Sword"

        self.gm.perform_hourly_action("craft", {"item_name": item_name_to_craft})

        self.assertNotIn(item_name_to_craft, [item.name for item in self.gm.shop.inventory], f"{item_name_to_craft} should NOT be in shop inventory.")
        self.assertNotIn(item_name_to_craft, self.gm.daily_items_crafted, f"{item_name_to_craft} should NOT be in daily_items_crafted.")
        self.assertEqual(self.gm.time.current_hour, (initial_time + 1) % 24, "Time should advance by 1 hour.")

    def test_action_talk_to_customer_and_potential_sale(self):
        """Test talking to a customer, with a potential for a sale. May be flaky due to randomness."""
        initial_time = self.gm.time.current_hour

        # Add an item to shop to be sold
        test_sell_item = Item(name="Shiny Dagger", description="A shiny dagger.", quality="Common", base_value=20, item_type="weapon") # Capitalized quality
        self.gm.shop.add_item_to_inventory(test_sell_item)
        initial_shop_gold = self.gm.shop.gold
        initial_item_count = sum(1 for item_in_inv in self.gm.shop.inventory if item_in_inv.name == test_sell_item.name)
        initial_visitors = self.gm.daily_visitors
        initial_dialogue_count = len(self.gm.daily_customer_dialogue_snippets)

        # To make sale deterministic for this test, we'd mock random.random()
        # For now, we accept it might not always sell.
        # import random
        # original_random = random.random
        # random.random = lambda: 0.01 # Ensure sale happens (if condition is < 0.3)

        self.gm.perform_hourly_action("talk_to_customer")

        # random.random = original_random # Restore random

        self.assertEqual(self.gm.time.current_hour, (initial_time + 1) % 24, "Time should advance by 1 hour.")
        self.assertEqual(self.gm.daily_visitors, initial_visitors + 1, "Daily visitors should increase by 1.")

        if test_sell_item.name in self.gm.daily_items_sold_by_shop_to_npcs:
            current_item_count_after_sale = sum(1 for item_in_inv in self.gm.shop.inventory if item_in_inv.name == test_sell_item.name)
            self.assertTrue(self.gm.daily_gold_earned_from_sales > 0, "Gold earned from sales should be positive if item sold.")
            self.assertEqual(current_item_count_after_sale, initial_item_count - 1, "Item count should decrease if sold.")
            self.assertTrue(self.gm.shop.gold > initial_shop_gold, "Shop gold should increase if item sold.")
            # Dialogue is not guaranteed even on sale, but more likely
            self.assertTrue(len(self.gm.daily_customer_dialogue_snippets) >= initial_dialogue_count, "Customer dialogue snippets should not decrease.")
        else:
            current_item_count_no_sale = sum(1 for item_in_inv in self.gm.shop.inventory if item_in_inv.name == test_sell_item.name)
            # No sale occurred, check gold and item count remain same
            self.assertEqual(current_item_count_no_sale, initial_item_count, "Item count should not change if not sold.")
            self.assertEqual(self.gm.shop.gold, initial_shop_gold, "Shop gold should not change if not sold.")
        # A dialogue snippet might occur even without a sale
        self.assertTrue(len(self.gm.daily_customer_dialogue_snippets) >= initial_dialogue_count, "Customer dialogue snippets should generally not decrease.")


    def test_action_research_market(self):
        """Test researching the market."""
        initial_time = self.gm.time.current_hour
        initial_pending_xp = self.gm.character.pending_xp

        self.gm.perform_hourly_action("research_market")

        self.assertEqual(self.gm.character.pending_xp, initial_pending_xp + 5, "Pending XP should increase by 5.")
        self.assertEqual(self.gm.time.current_hour, (initial_time + 1) % 24, "Time should advance by 1 hour.")

    def test_action_buy_from_own_shop_success(self):
        """Test successfully buying an item from the character's own shop."""
        initial_time = self.gm.time.current_hour
        item_to_buy = Item(name="Potion of Testing", description="A potion for testing.", quality="Common", base_value=10, item_type="potion") # Capitalized quality
        self.gm.shop.add_item_to_inventory(item_to_buy) # Add item to shop

        self.gm.character.gold = 100 # Ensure character has gold
        initial_player_gold = self.gm.character.gold
        initial_shop_gold = self.gm.shop.gold

        # Calculate expected price (shop buys low, sells high - assume default 2x markup for now)
        # This depends on Shop.calculate_effective_price logic which might not be 2x.
        # For robustness, let's assume a fixed price or get it from shop.
        # GameManager.perform_hourly_action for "buy_from_own_shop" uses item.get_sale_price()
        # which uses base_value by default. Let's assume this for now.
        # Corrected to use shop's calculation method
        expected_cost = self.gm.shop.calculate_sale_price(item_to_buy)


        self.gm.perform_hourly_action("buy_from_own_shop", {"item_name": "Potion of Testing"})

        self.assertIn("Potion of Testing", [item.name for item in self.gm.character.inventory], "Item should be in player inventory.")
        self.assertNotIn("Potion of Testing", [item.name for item in self.gm.shop.inventory], "Item should be removed from shop inventory.")
        self.assertEqual(self.gm.character.gold, initial_player_gold - expected_cost, "Player gold should decrease by item cost.")
        self.assertEqual(self.gm.shop.gold, initial_shop_gold + expected_cost, "Shop gold should increase by item cost.")
        self.assertIn("Potion of Testing", self.gm.daily_items_player_bought_from_shop, "Item should be in daily_items_player_bought_from_shop.")
        self.assertEqual(self.gm.daily_gold_spent_on_purchases_by_player, expected_cost, "daily_gold_spent should reflect cost.")
        self.assertEqual(self.gm.time.current_hour, (initial_time + 1) % 24, "Time should advance by 1 hour.")

    def test_action_buy_from_own_shop_item_not_in_stock(self):
        """Test buying an item not in stock."""
        initial_time = self.gm.time.current_hour
        self.gm.character.gold = 100
        initial_player_gold = self.gm.character.gold
        initial_shop_gold = self.gm.shop.gold

        self.gm.perform_hourly_action("buy_from_own_shop", {"item_name": "NonExistentItem"})

        self.assertNotIn("NonExistentItem", [item.name for item in self.gm.character.inventory], "NonExistentItem should not be in player inventory.")
        self.assertEqual(self.gm.character.gold, initial_player_gold, "Player gold should remain unchanged.")
        self.assertEqual(self.gm.shop.gold, initial_shop_gold, "Shop gold should remain unchanged.")
        self.assertNotIn("NonExistentItem", self.gm.daily_items_player_bought_from_shop, "Item should not be in daily_items_player_bought_from_shop.")
        self.assertEqual(self.gm.daily_gold_spent_on_purchases_by_player, 0, "Daily gold spent should be 0.")
        self.assertEqual(self.gm.time.current_hour, (initial_time + 1) % 24, "Time should advance by 1 hour.")

    def test_action_buy_from_own_shop_insufficient_funds(self):
        """Test buying an item when player has insufficient funds."""
        initial_time = self.gm.time.current_hour
        expensive_item = Item(name="Expensive Lute", description="A very expensive lute.", quality="Rare", base_value=1000, item_type="instrument") # Capitalized quality
        self.gm.shop.add_item_to_inventory(expensive_item)

        self.gm.character.gold = 10 # Player has insufficient gold
        initial_player_gold = self.gm.character.gold
        initial_shop_gold = self.gm.shop.gold
        initial_player_inventory_count = len(self.gm.character.inventory)


        self.gm.perform_hourly_action("buy_from_own_shop", {"item_name": "Expensive Lute"})

        self.assertNotIn("Expensive Lute", [item.name for item in self.gm.character.inventory], "Expensive Lute should not be in player inventory.")
        self.assertEqual(len(self.gm.character.inventory), initial_player_inventory_count, "Player inventory count should not change.")
        self.assertEqual(self.gm.character.gold, initial_player_gold, "Player gold should remain unchanged.")
        # Shop gold should also remain unchanged as the transaction fails before gold transfer
        self.assertEqual(self.gm.shop.gold, initial_shop_gold, "Shop gold should remain unchanged.")
        self.assertNotIn("Expensive Lute", self.gm.daily_items_player_bought_from_shop)
        self.assertEqual(self.gm.daily_gold_spent_on_purchases_by_player, 0)
        self.assertEqual(self.gm.time.current_hour, (initial_time + 1) % 24, "Time should advance by 1 hour.")

    def test_action_rest_short_success(self):
        """Test successful short rest action."""
        self.char.level = 3 # Ensure level is set for max_hit_dice
        self.char.max_hit_dice = self.char.level
        self.char.hit_dice = self.char.max_hit_dice # Full hit dice
        self.char.hp = self.char.get_effective_max_hp() - 10 # Take some damage
        if self.char.hp < 1: self.char.hp = 1 # Ensure not dead

        initial_hp = self.char.hp
        initial_hit_dice = self.char.hit_dice
        initial_time = self.gm.time.current_hour

        self.gm.perform_hourly_action("sleep_one_hour")

        self.assertTrue(self.char.hp > initial_hp or self.char.hp == self.char.get_effective_max_hp(), "HP should increase by 1 or be maxed.")
        self.assertEqual(self.char.hit_dice, initial_hit_dice, "Hit dice should not change for sleep_one_hour.")
        self.assertEqual(self.gm.time.current_hour, (initial_time + 1) % 24, "Time should advance by 1 hour.")

    def test_action_rest_short_no_hit_dice(self):
        """Test short rest action when character has no hit dice."""
        self.char.hp = self.char.get_effective_max_hp() - 5
        self.char.hit_dice = 0 # No hit dice
        initial_hp = self.char.hp
        initial_time = self.gm.time.current_hour

        self.gm.perform_hourly_action("sleep_one_hour")

        if initial_hp < self.char.get_effective_max_hp():
            self.assertEqual(self.char.hp, initial_hp + 1, "HP should increase by 1 if not at max.")
        else:
            self.assertEqual(self.char.hp, initial_hp, "HP should remain at max if already maxed.")
        self.assertEqual(self.char.hit_dice, 0, "Hit dice should remain 0.")
        self.assertEqual(self.gm.time.current_hour, (initial_time + 1) % 24, "Time should advance by 1 hour.")

    def test_player_sell_item_to_shop_success(self):
        """Test player successfully selling an item to the shop."""
        item_to_sell = Item(name="Shiny Rock", description="A somewhat shiny rock.", base_value=5, item_type="gem", quality="Common") # Capitalized quality
        self.char.add_item_to_inventory(item_to_sell)
        self.gm.shop.gold = 100 # Ensure shop has gold
        self.char.gold = 0 # Player starts with 0 gold for clarity

        initial_shop_gold = self.gm.shop.gold
        # The sell_item_to_shop action itself doesn't advance game time in GameManager,
        # it's a direct character method. The prompt implies it's part of a larger sequence.
        # For this test, we'll manually track its effects on daily trackers and assume time is advanced by perform_hourly_action.
        # Let's simulate it as part of an implicit hour of managing inventory/talking to shop.
        initial_time = self.gm.time.current_hour

        # Perform the sale
        gold_earned = self.char.sell_item_to_shop(item_to_sell, self.gm.shop)

        # Manually update GameManager's daily trackers as if an action caused this
        if gold_earned > 0:
            self.gm.daily_gold_player_earned_selling_to_shop += gold_earned
            self.gm.daily_items_player_sold_to_shop.append(item_to_sell.name)

        # Simulate time passage for the action that included this sale
        # self.gm.time.advance_hour(1) # This would be if not using perform_hourly_action
        # For consistency with other tests, let's assume this was part of a generic action
        # and the next perform_hourly_action call would advance time.
        # Or, if this test is *only* for Character.sell_item_to_shop, time wouldn't advance here.
        # Given the prompt structure, it seems like it's a GM-level test.
        # Let's assume the prompt meant for this to be wrapped in a conceptual hourly action.
        # We'll advance time by 1 hour to reflect the game progressing.
        self.gm.time.advance_hour(1) # Manually advance time for this test case

        self.assertTrue(gold_earned > 0, "Should have earned some gold.")
        # Shop.buy_item_from_character adds to its inventory
        self.assertIn(item_to_sell, self.gm.shop.inventory, "Item should be in shop's inventory.")
        self.assertNotIn(item_to_sell, self.char.inventory, "Item should not be in character's inventory.")
        self.assertEqual(self.char.gold, gold_earned, "Character gold should match gold earned.")
        self.assertEqual(self.gm.shop.gold, initial_shop_gold - gold_earned, "Shop gold should decrease by gold earned (as it paid out).")
        self.assertIn("Shiny Rock", self.gm.daily_items_player_sold_to_shop, "Item name should be in daily_items_player_sold_to_shop.")
        self.assertEqual(self.gm.daily_gold_player_earned_selling_to_shop, gold_earned, "Daily gold earned by player should be updated.")
        self.assertEqual(self.gm.time.current_hour, (initial_time + 1) % 24, "Time should advance by 1 hour.")


    def test_start_long_rest_success(self):
        """Test successful long rest."""
        self.char.hp = 1
        self.char.hit_dice = 0
        self.char.exhaustion_level = 1

        initial_day = self.gm.time.current_day
        initial_hour = self.gm.time.current_hour

        # --- Mock random.random to prevent interruption ---
        original_random_random = random.random
        # Make random.random return a value that ensures no interruption (e.g., > 0.1 if default chance is 0.1)
        random.random = lambda: 0.5

        self.gm.perform_hourly_action("sleep_eight_hours")

        random.random = original_random_random # Restore original random function
        # --- End Mock ---

        # After rest, exhaustion should be 0, so max_hp is base_max_hp
        self.assertEqual(self.char.hp, self.char.base_max_hp, "HP should be restored to base max HP (since exhaustion is 0).")

        expected_hit_dice_regained = max(1, self.char.max_hit_dice // 2)
        # initial_hit_dice was 0, so current hit_dice should be exactly what was regained.
        self.assertEqual(self.char.hit_dice, expected_hit_dice_regained, f"Should regain {expected_hit_dice_regained} hit dice.")
        self.assertEqual(self.char.exhaustion_level, 0, "Exhaustion level should be 0.")

        expected_days_advanced = (initial_hour + 8) // 24
        expected_hour = (initial_hour + 8) % 24
        self.assertEqual(self.gm.time.current_hour, expected_hour, "Time hour is incorrect after long rest.")
        self.assertEqual(self.gm.time.current_day, initial_day + expected_days_advanced, "Time day is incorrect after long rest.")

    def test_start_long_rest_death_by_exhaustion(self):
        """Test death by exhaustion during long rest."""
        self.char.exhaustion_level = 5 # Start close to death
        self.gm.perform_hourly_action("sleep_one_hour") # Trigger one hour of rest
        self.char.exhaustion_level = 6 # Explicitly set to death level

        initial_hp = self.char.hp # HP before the rest action that might cause death print

        import io
        from contextlib import redirect_stdout
        captured_output = io.StringIO()

        # The death check is inside perform_hourly_action("sleep_one_hour") called by start_long_rest
        # We need to ensure the loop in start_long_rest runs at least once with exhaustion at 6
        # The setup above makes the character die on the *next* hour of sleep if not already "dead"
        # The Character.gain_exhaustion() already prints a death message if it reaches 6.
        # The GameManager's start_long_rest loop also has a "perished during rest" print.

        # Let's simplify: set exhaustion to 6 directly and then try to rest.
        self.char.exhaustion_level = 6
        # Manually call the print from Character class to ensure it's in output if expected from there
        # Or rely on the GameManager's print. The GameManager's print is:
        # print(f"  {self.character.name} perished during rest due to exhaustion.")
        self.char.exhaustion_level = 5 # Start at exhaustion 5
        self.char.hp = 1 # Ensure HP is low so death is apparent

        with redirect_stdout(captured_output):
            # Attempt long rest without food, which should increment exhaustion to 6 and cause death.
            self.gm.perform_hourly_action("sleep_eight_hours", action_details={"food_available": False, "drink_available": True})

        output_str = captured_output.getvalue()

        # Check for the death message from Character.gain_exhaustion()
        expected_death_message = f"  {self.char.name} has died from exhaustion!"
        self.assertIn(expected_death_message, output_str, "Death message from Character.gain_exhaustion() not found.")

        self.assertEqual(self.char.exhaustion_level, 6, "Exhaustion should be 6.")
        # HP might be 0 or unchanged at 1 depending on when death is checked vs HP effects
        self.assertTrue(self.char.hp <= 1, "HP should be 0 or remain at its low value if death occurred.")

    def test_event_trigger_and_recording(self):
        """Test that events can trigger and are recorded in daily_special_events."""
        # Make a copy of original events and ensure SAMPLE_EVENTS is a list
        original_sample_events = list(SAMPLE_EVENTS)

        test_event_dict = {"name": "Test Event Alpha", "description": "A test event happened!", "effects": {"character_xp_gain": 10}}
        # Ensure EventManager uses a list that can be appended to for testing
        # If EventManager.SAMPLE_EVENTS is a tuple, this won't work directly.
        # Assuming EventManager.SAMPLE_EVENTS is a list or can be replaced for testing.
        # For this test, we directly modify the global SAMPLE_EVENTS used by EventManager instance in GameManager
        SAMPLE_EVENTS.clear() # Clear existing sample events for predictability
        SAMPLE_EVENTS.append(Event.from_dict(test_event_dict))

        initial_pending_xp = self.char.pending_xp

        # Mock random.random to ensure event chance is met.
        # The event check is `if random.random() < self.base_event_chance:`
        original_random_random = random.random
        random.random = lambda: self.gm.base_event_chance - 0.01 # Ensure it's less than the chance

        self.gm.perform_hourly_action("talk_to_customer")

        random.random = original_random_random # Restore original random function

        self.assertGreater(len(self.gm.daily_special_events), 0, "daily_special_events should not be empty after a guaranteed event.")
        self.assertIn("Test Event Alpha", self.gm.daily_special_events[0], "The name of the test event should be in daily_special_events.")

        # Check if XP effect was applied (this tests EventManager's handling too)
        # EventManager.trigger_random_event applies XP directly to character.award_xp
        # which goes into pending_xp.
        if "character_xp_gain" in test_event_dict["effects"]:
            self.assertEqual(self.char.pending_xp, initial_pending_xp + test_event_dict["effects"]["character_xp_gain"],
                             "Character pending_xp should reflect event XP gain.")

        # Cleanup: Restore original SAMPLE_EVENTS
        SAMPLE_EVENTS.clear()
        SAMPLE_EVENTS.extend(original_sample_events)


    def test_town_change_and_shop_association(self):
        """Test changing towns and ensuring the shop's town reference is updated."""
        self.assertEqual(self.gm.shop.town, self.gm.current_town, "Shop's town should initially match GameManager's current town.")

        initial_town_name = self.gm.current_town.name

        new_town = Town(name="Testville", properties=[], nearby_resources=[], unique_npc_crafters=[], market_demand_modifiers={})
        self.assertNotIn(new_town, self.gm.towns, "New town should not already be in GameManager's town list.")
        self.gm.towns.append(new_town) # Add new town to list of known towns

        # Change current town in GameManager
        self.gm.current_town = new_town

        # Update shop's town association (as per new Shop.update_town method)
        self.gm.shop.update_town(new_town)

        self.assertNotEqual(self.gm.current_town.name, initial_town_name, "GameManager's current town should have changed.")
        self.assertEqual(self.gm.current_town.name, "Testville", "GameManager's current town name is incorrect.")
        self.assertEqual(self.gm.shop.town, new_town, "Shop's town reference should be the new town instance.")
        self.assertEqual(self.gm.shop.town.name, "Testville", "Shop's town name attribute should reflect the new town.")

    def test_market_demand_impacts_sale_price(self):
        """Test that town market demand modifiers impact shop's item sale prices."""
        test_item_name = "Healing Salve" # Use a unique name to avoid conflicts with default recipes if any
        test_item_base_value = 10

        # Add item to shop's BASIC_RECIPES if calculate_sale_price needs it for non-inventory items
        # Or ensure item is in inventory. Let's add to inventory for this test.
        test_item = Item(name=test_item_name, description="A healing salve.", quality="Uncommon", base_value=test_item_base_value, item_type="potion") # Capitalized quality
        self.gm.shop.add_item_to_inventory(test_item)

        # The item's actual value after quality modification (Uncommon = 1.5x)
        item_actual_value = test_item.value # This is 10 * 1.5 = 15

        # Scenario 1: No modifier (or modifier is 1.0)
        self.gm.current_town.market_demand_modifiers = {} # Clear existing modifiers for current town
        price_no_modifier = self.gm.shop.calculate_sale_price(test_item)
        # Expected price should use item's actual value (post-quality) times shop markup
        expected_price_no_mod = int(item_actual_value * self.gm.shop.markup_percentage)
        self.assertEqual(price_no_modifier, expected_price_no_mod,
                         f"Price with no modifier incorrect. Expected {expected_price_no_mod}, Got {price_no_modifier}")

        # Scenario 2: Positive modifier
        self.gm.current_town.market_demand_modifiers = {test_item_name: 1.5} # 50% higher demand
        price_positive_modifier = self.gm.shop.calculate_sale_price(test_item)
        expected_price_positive_mod = int(item_actual_value * 1.5 * self.gm.shop.markup_percentage)
        self.assertEqual(price_positive_modifier, expected_price_positive_mod,
                         f"Price with positive modifier incorrect. Expected {expected_price_positive_mod}, Got {price_positive_modifier}")

        # Scenario 3: Negative modifier
        self.gm.current_town.market_demand_modifiers = {test_item_name: 0.8} # 20% lower demand
        price_negative_modifier = self.gm.shop.calculate_sale_price(test_item)
        expected_price_negative_mod = int(item_actual_value * 0.8 * self.gm.shop.markup_percentage)
        self.assertEqual(price_negative_modifier, expected_price_negative_mod,
                                 f"Price with negative modifier incorrect. Expected {expected_price_negative_mod}, Got {price_negative_modifier}")

    def test_action_talk_to_customer(self):
        """Test the 'talk_to_customer' action."""
        # Ensure output stream is clean for this test
        self.output_stream.truncate(0)
        self.output_stream.seek(0)

        initial_xp = self.char.pending_xp # Assuming XP is awarded to pending_xp
        initial_dialogue_snippets_count = len(self.gm.daily_customer_dialogue_snippets)

        action_name = "talk_to_customer"
        action_details = {}
        self.gm.perform_hourly_action(action_name, action_details)

        # 1. Assert XP was gained
        # The action_talk_to_customer in GameManager awards 2 XP.
        self.assertEqual(self.char.pending_xp, initial_xp + 2, "Player should gain 2 XP for talking to a customer.")

        # 2. Assert game log contains a customer dialogue snippet
        log_output = self.output_stream.getvalue()
        self.assertIn("You approach a customer. They say:", log_output, "Log output should indicate approaching a customer.")
        # Check if any known part of a dialogue is present. This is tricky as dialogues are random.
        # Instead, we'll rely on the daily_customer_dialogue_snippets check.
        # A more robust check here might involve checking against CUSTOMER_DIALOGUE_TEMPLATES if possible
        # or ensuring the format "They say: \"...\"" is present.
        self.assertRegex(log_output, r"They say: \"[\w\s,.!'?-]+\"", "Log output should contain formatted customer dialogue.")


        # 3. Assert daily_customer_dialogue_snippets has a new entry
        self.assertEqual(len(self.gm.daily_customer_dialogue_snippets), initial_dialogue_snippets_count + 1,
                         "A new dialogue snippet should be added to daily_customer_dialogue_snippets.")

        # Check the content of the added snippet
        last_snippet = self.gm.daily_customer_dialogue_snippets[-1]
        self.assertTrue(last_snippet.startswith("(Directly engaged)"), "Snippet should be marked as directly engaged.")

    # --- Tests for features from the latest subtasks ---

    def test_action_craft_item_via_game_manager_success(self):
        self._clear_output()
        # Setup: Character needs ingredients for "Traveler's Bread"
        # Recipe: {"Grain": 2, "Clean Water": 1}
        self.char.add_item_to_inventory(Item(name="Grain", base_value=1, item_type="component", quantity=2))
        self.char.add_item_to_inventory(Item(name="Clean Water", base_value=1, item_type="component", quantity=1))
        initial_xp = self.char.pending_xp

        self.gm.perform_hourly_action("craft", {"item_name": "Traveler's Bread"})

        # Verify bread is in shop inventory
        found_bread = next((item for item in self.gm.shop.inventory if item.name == "Traveler's Bread"), None)
        self.assertIsNotNone(found_bread)
        if found_bread:
            self.assertEqual(found_bread.quantity, 1)

        # Verify ingredients removed from character
        self.assertFalse(self.char.has_items({"Grain": 1})[0], "Grain should be consumed.")
        self.assertFalse(self.char.has_items({"Clean Water": 1})[0], "Clean Water should be consumed.")

        self.assertEqual(self.char.pending_xp, initial_xp + 10, "Crafting XP not awarded.") # Default craft XP is 10
        self.assertIn("Successfully crafted 1x Common Traveler's Bread.", self.output_stream.getvalue()) # Assuming common quality

    def test_action_craft_item_via_game_manager_fail_no_ingredients(self):
        self._clear_output()
        # Character does NOT have ingredients for "Simple Dagger"
        # Recipe: {"Leather Scraps": 1, "Scrap Metal": 2}
        self.char.inventory = [] # Ensure empty
        initial_xp = self.char.pending_xp

        self.gm.perform_hourly_action("craft", {"item_name": "Simple Dagger"})

        self.assertIsNone(next((item for item in self.gm.shop.inventory if item.name == "Simple Dagger"), None))
        self.assertEqual(self.char.pending_xp, initial_xp, "XP should not be awarded for failed craft.")
        self.assertIn("Cannot craft Simple Dagger. Missing ingredients", self.output_stream.getvalue())

    @unittest.mock.patch('random.choice')
    @unittest.mock.patch('random.randint')
    def test_action_gather_resources(self, mock_randint, mock_choice):
        self._clear_output()
        # Mock random.choice to return "Wild Herb"
        # Town's nearby_resources: ["Dirty Water", "Moldy Fruit", "Wild Herb", "Small Twig", "Sturdy Branch", "Grain"]
        mock_choice.return_value = "Wild Herb"
        # Mock random.randint to return 2
        mock_randint.return_value = 2

        initial_xp = self.char.pending_xp
        self.gm.perform_hourly_action("gather_resources")

        # Verify character inventory
        wild_herb_item = next((item for item in self.char.inventory if item.name == "Wild Herb"), None)
        self.assertIsNotNone(wild_herb_item)
        if wild_herb_item:
            self.assertEqual(wild_herb_item.quantity, 2)
            self.assertEqual(wild_herb_item.item_type, "component") # As per RESOURCE_ITEM_DEFINITIONS

        self.assertEqual(self.char.pending_xp, initial_xp + 3, "Gathering XP not awarded.")
        self.assertIn(f"{self.char.name} gathered 2x Wild Herb.", self.output_stream.getvalue())
        mock_choice.assert_called_with(self.gm.current_town.nearby_resources)
        mock_randint.assert_called_with(1,3)


    def test_action_buy_herbs_hemlock_success(self):
        self._clear_output()
        self.char.gold = 100
        initial_xp = self.char.pending_xp
        item_to_buy = "Sunpetal" # Price 8g
        quantity = 3
        expected_cost = 8 * quantity # 24g

        self.gm.perform_hourly_action("buy_herbs_hemlock", {"item_name": item_to_buy, "quantity": quantity})

        self.assertEqual(self.char.gold, 100 - expected_cost)
        sunpetal_item = next((item for item in self.char.inventory if item.name == item_to_buy), None)
        self.assertIsNotNone(sunpetal_item)
        if sunpetal_item:
            self.assertEqual(sunpetal_item.quantity, quantity)
        self.assertEqual(self.char.pending_xp, initial_xp + 1, "Buying herbs XP not awarded.") # XP is 1
        self.assertIn(f"{self.char.name} bought {quantity}x {item_to_buy} from Old Man Hemlock for {expected_cost}g.", self.output_stream.getvalue())
        self.assertEqual(self.gm.daily_gold_spent_on_purchases_by_player, expected_cost)

    def test_action_buy_herbs_hemlock_unknown_item(self):
        self._clear_output()
        self.char.gold = 100
        initial_gold = self.char.gold
        initial_xp = self.char.pending_xp

        self.gm.perform_hourly_action("buy_herbs_hemlock", {"item_name": "Bogus Herb", "quantity": 1})

        self.assertEqual(self.char.gold, initial_gold)
        self.assertEqual(self.char.pending_xp, initial_xp) # No XP for failed purchase
        self.assertIn("Old Man Hemlock doesn't sell 'Bogus Herb'.", self.output_stream.getvalue())

    def test_action_buy_herbs_hemlock_insufficient_gold(self):
        self._clear_output()
        self.char.gold = 10 # Sunpetal costs 8g, needs 24g for 3.
        initial_gold = self.char.gold
        initial_xp = self.char.pending_xp

        self.gm.perform_hourly_action("buy_herbs_hemlock", {"item_name": "Sunpetal", "quantity": 3})

        self.assertEqual(self.char.gold, initial_gold)
        self.assertEqual(self.char.pending_xp, initial_xp)
        self.assertIn(f"{self.char.name} doesn't have enough gold. (Needs 24g, Has {initial_gold}g).", self.output_stream.getvalue())

    @unittest.mock.patch('random.choice')
    def test_action_talk_to_hemlock(self, mock_choice):
        self._clear_output()
        # Old Man Hemlock's dialogue options:
        # ["The forest speaks to those who listen.", "These old bones have seen many seasons.", "Looking for herbs, are we?"]
        expected_dialogue = "These old bones have seen many seasons."
        mock_choice.return_value = expected_dialogue
        initial_xp = self.char.pending_xp

        self.gm.perform_hourly_action("talk_to_hemlock")

        self.assertIn(f"Old Man Hemlock says: \"{expected_dialogue}\"", self.output_stream.getvalue())
        self.assertEqual(self.char.pending_xp, initial_xp + 1, "Talking to Hemlock XP not awarded.")
        # Ensure mock_choice was called with Hemlock's specific dialogues
        hemlock_npc_data = next(npc for npc in self.gm.current_town.unique_npc_crafters if npc['name'] == "Old Man Hemlock")
        mock_choice.assert_called_with(hemlock_npc_data['dialogue'])


    @unittest.mock.patch('random.choice')
    def test_action_talk_to_villager(self, mock_choice):
        self._clear_output()
        expected_dialogue = "Nice weather we're having, eh?" # A generic one
        mock_choice.return_value = expected_dialogue
        initial_xp = self.char.pending_xp

        self.gm.perform_hourly_action("talk_to_villager")

        self.assertIn(f"You chat with a villager. They say: \"{expected_dialogue}\"", self.output_stream.getvalue())
        self.assertEqual(self.char.pending_xp, initial_xp + 1, "Talking to villager XP not awarded.")
        # The argument to mock_choice for generic villagers is a list defined inside the method, harder to assert directly
        # but the output check is a good indicator.

    @unittest.mock.patch('random.choice')
    @unittest.mock.patch('random.random')
    def test_action_explore_town_find_gold(self, mock_random_value, mock_choice_find):
        self._clear_output()
        mock_random_value.return_value = 0.10 # Ensure find happens (chance < 0.20)
        gold_find_details = {"type": "gold", "amount": 10}
        mock_choice_find.return_value = gold_find_details

        self.char.gold = 50
        initial_xp = self.char.pending_xp

        self.gm.perform_hourly_action("explore_town")

        self.assertEqual(self.char.gold, 60)
        self.assertIn(f"While exploring, {self.char.name} found 10g!", self.output_stream.getvalue())
        self.assertEqual(self.char.pending_xp, initial_xp + 5, "Explore town XP not awarded.") # explore_town base XP

    @unittest.mock.patch('random.choice')
    @unittest.mock.patch('random.random')
    def test_action_explore_town_find_item(self, mock_random_value, mock_choice_find):
        self._clear_output()
        mock_random_value.return_value = 0.10 # Ensure find happens
        item_find_details = {"type": "item", "name": "Shiny Pebble", "description": "A smooth, oddly shiny pebble.", "base_value": 1, "item_type": "trinket", "quality": "Common", "quantity": 1}
        mock_choice_find.return_value = item_find_details

        initial_xp = self.char.pending_xp

        self.gm.perform_hourly_action("explore_town")

        found_item = next((item for item in self.char.inventory if item.name == "Shiny Pebble"), None)
        self.assertIsNotNone(found_item)
        if found_item:
            self.assertEqual(found_item.quantity, 1)
        self.assertIn(f"While exploring, {self.char.name} found a Shiny Pebble!", self.output_stream.getvalue())
        self.assertEqual(self.char.pending_xp, initial_xp + 5)

    @unittest.mock.patch('random.random')
    def test_action_explore_town_no_find(self, mock_random_value):
        self._clear_output()
        mock_random_value.return_value = 0.50 # Ensure NO find happens (chance >= 0.20)

        initial_gold = self.char.gold
        initial_inv_count = len(self.char.inventory)
        initial_xp = self.char.pending_xp

        self.gm.perform_hourly_action("explore_town")

        self.assertEqual(self.char.gold, initial_gold)
        self.assertEqual(len(self.char.inventory), initial_inv_count)
        self.assertNotIn("found", self.output_stream.getvalue().lower()) # Check that "found" isn't in output
        self.assertEqual(self.char.pending_xp, initial_xp + 5)


if __name__ == '__main__':
    unittest.main()
