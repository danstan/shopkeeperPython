import random
from .time_system import GameTime
from .character import Character
from .g_event import EventManager, SAMPLE_EVENTS, Event
from .shop import Shop
from .item import Item
from .town import Town

CUSTOMER_DIALOGUE_TEMPLATES = {
    "positive": [
        "Shopkeeper always has the potions I'm looking for!",
        "I like the decor in this shop.",
        "The prices here are fair for {town_name}.",
        "Found exactly what I needed!",
        "This shop is a gem in {town_name}.",
        "Heard good things about this place.",
    ],
    "neutral": [
        "Just browsing, thanks.",
        "Hmm, interesting selection.",
        "Do you have any enchanted weapons?",
        "What's new today?",
        "Is the owner around?",
    ],
    "negative": [
        "The food items here look a bit stale.",
        "A bit pricey for my taste, even for {town_name}.",
        "Couldn't find what I was looking for.",
        "This place is a bit cluttered.",
        "I've seen better.",
    ]
}

class GameManager:
    def __init__(self, player_character: Character, output_stream=None):
        self.output_stream = output_stream
        self.time = GameTime()
        self.character = player_character

        town_เริ่มต้น = Town(
            name="เริ่มต้น Village",
            properties=["Quiet farming village", "River nearby"],
            nearby_resources=["Fish", "Wheat", "Basic Herbs"],
            unique_npc_crafters=[{"name": "Old Man Hemlock", "specialty": "Herbalism", "services": ["Identifies Herbs"], "quests_available": []}],
            market_demand_modifiers={"Minor Healing Potion": 1.1, "Bread": 0.9, "Fish": 1.05}
        )
        town_เหล็กไหล = Town(
            name="เหล็กไหล City",
            properties=["Major mining hub", "Strong warrior tradition"],
            nearby_resources=["Iron Ore", "Coal", "Stone"],
            unique_npc_crafters=[{"name": "Borin Stonebeard", "specialty": "Blacksmithing", "services": ["Repairs Gear", "Sells Metal Ingots"], "quests_available": ["Clear Mine Pests"]}],
            market_demand_modifiers={"Simple Dagger": 1.25, "Iron Sword": 1.3, "Minor Healing Potion": 1.15, "Stale Ale": 0.8}
        )
        self.towns = [town_เริ่มต้น, town_เหล็กไหล]
        self.current_town = town_เริ่มต้น
        self.shop = Shop(name=f"{player_character.name}'s Emporium", owner_name=player_character.name, town=self.current_town)

        self.event_manager = EventManager(self.character)
        self.base_event_chance = 0.05
        self._reset_daily_trackers()
        self._print(f"GameManager initialized. {player_character.name}'s shop established in {self.current_town.name}.")

    def _print(self, message):
        if self.output_stream:
            self.output_stream.write(message + '\n')
        else:
            print(message)

    def _reset_daily_trackers(self):
        self.daily_gold_earned_from_sales = 0
        self.daily_gold_spent_on_purchases_by_player = 0
        self.daily_gold_player_earned_selling_to_shop = 0
        self.daily_visitors = 0
        self.daily_xp_awarded_this_day = 0
        self.daily_items_crafted = []
        self.daily_items_sold_by_shop_to_npcs = []
        self.daily_items_player_bought_from_shop = []
        self.daily_items_player_sold_to_shop = []
        self.daily_special_events = []
        self.daily_customer_dialogue_snippets = []
        self.tracking_day = self.time.current_day
        self._print(f"[{self.time.get_time_string()}] Daily trackers have been reset for Day {self.tracking_day}.")

    def _handle_customer_interaction(self, is_sale_or_purchase_by_player_shop:bool = False):
        self.daily_visitors += 1
        dialogue_chance = 0.3 if is_sale_or_purchase_by_player_shop else 0.1
        if random.random() < dialogue_chance:
            if self.shop.gold < 200 and len(self.shop.inventory) == 0:
                 snippet_type = "negative"
            elif len(self.shop.inventory) > 2:
                 snippet_type = random.choice(["positive", "neutral", "positive"])
            else:
                 snippet_type = random.choice(list(CUSTOMER_DIALOGUE_TEMPLATES.keys()))

            snippet = random.choice(CUSTOMER_DIALOGUE_TEMPLATES[snippet_type])
            formatted_snippet = snippet.format(town_name=self.current_town.name)
            self.daily_customer_dialogue_snippets.append(formatted_snippet)
            self._print(f"  Overheard: \"{formatted_snippet}\"")

    def perform_hourly_action(self, action_name: str, action_details: dict = None):
        action_details = action_details if action_details else {}

        current_day_before_action = self.time.current_day
        # current_hour_before_action = self.time.current_hour # Not strictly needed for recap logic now

        # If it's already midnight when starting the action, it means a new day just began due to a previous long rest.
        # The recap for the *previous* day should have already happened.
        if self.time.current_hour == 0 and self.tracking_day != self.time.current_day :
             self._print(f"DEBUG: New day {self.time.current_day} started. Previous tracking day was {self.tracking_day}.")
             # This indicates trackers should have been reset, or recap for tracking_day is due.
             # However, recap is for the day that *just ended*.
             # The main recap trigger is *after* time advances.

        current_time_str = self.time.get_time_string()
        self._print(f"\n[{current_time_str}] {self.character.name} (in {self.current_town.name}) performs action: {action_name}")
        action_xp_reward = 0

        if action_name == "craft":
            item_name = action_details.get("item_name")
            if item_name:
                crafted_item = self.shop.craft_item(item_name)
                if crafted_item:
                    self.daily_items_crafted.append(crafted_item.name)
            else: self._print("  Crafting action chosen, but no item_name specified.")

        elif action_name == "rest_short":
            self.character.take_short_rest(action_details.get("dice_to_spend", 1))

        elif action_name == "sleep_one_hour":
            self._print(f"  {self.character.name} sleeps for an hour in {self.current_town.name}...")

        elif action_name == "talk_to_customer":
            self._print(f"  {self.character.name} spends an hour at {self.shop.name} attending to the shop.")
            self._handle_customer_interaction(is_sale_or_purchase_by_player_shop=False)
            if self.shop.inventory and random.random() < 0.3:
                item_to_sell_to_npc = random.choice(self.shop.inventory)
                sale_price = self.shop.complete_sale_to_npc(item_to_sell_to_npc.name)
                if sale_price > 0:
                    self.daily_items_sold_by_shop_to_npcs.append(item_to_sell_to_npc.name)
                    self.daily_gold_earned_from_sales += sale_price
                    self._print(f"  DEBUG: daily_gold_earned_from_sales updated to: {self.daily_gold_earned_from_sales} after sale of {sale_price}g")
                    self._handle_customer_interaction(is_sale_or_purchase_by_player_shop=True)

        elif action_name == "research_market":
            self._print(f"  {self.character.name} conducting market research in {self.current_town.name}...")
            self._print(f"    Current demand modifiers: {self.current_town.market_demand_modifiers}")
            self._print(f"    Nearby resources: {self.current_town.nearby_resources}")
            if self.current_town.market_demand_modifiers:
                high_demand_items = {item: mod for item, mod in self.current_town.market_demand_modifiers.items() if mod > 1.1}
                if high_demand_items:
                    random_high_demand_item = random.choice(list(high_demand_items.keys()))
                    self._print(f"    Insight: There seems to be high demand for '{random_high_demand_item}' right now!")
            action_xp_reward = 5

        elif action_name == "buy_from_own_shop":
            item_name_to_buy = action_details.get("item_name")
            if item_name_to_buy:
                item_in_shop = next((item for item in self.shop.inventory if item.name == item_name_to_buy), None)
                if item_in_shop:
                    bought_items, total_cost = self.character.buy_item_from_shop(item_name_to_buy, 1, self.shop)
                    if bought_items:
                        self.daily_items_player_bought_from_shop.append(bought_items[0].name)
                        self.daily_gold_spent_on_purchases_by_player += total_cost
                        self._handle_customer_interaction(is_sale_or_purchase_by_player_shop=True)
                else: self._print(f"  {self.shop.name} does not have {item_name_to_buy} to be bought by {self.character.name}.")
            else: self._print("  'buy_from_own_shop' action chosen, but no item_name specified.")
        else:
            self._print(f"  Action '{action_name}' is recognized but has no specific implementation yet.")

        if action_xp_reward > 0:
            xp_awarded = self.character.award_xp(action_xp_reward)
            # self.daily_xp_awarded_this_day += xp_awarded # This is now handled by commit_pending_xp in recap

        if random.random() < self.base_event_chance:
            self._print(f"![EVENT CHANCE MET AFTER ACTION {action_name}]!")
            if SAMPLE_EVENTS:
                triggered_event_name = self.event_manager.trigger_random_event(SAMPLE_EVENTS)
                if triggered_event_name:
                     self.daily_special_events.append(triggered_event_name)
            else: self._print("  (No sample events defined to trigger)")

        days_advanced, new_hour = self.time.advance_hour(1)

        if days_advanced > 0: # Midnight was crossed
             self.generate_end_of_day_recap(day_number=current_day_before_action)

        return {"status": "completed", "action": action_name, "new_time": self.time.get_time_string()}

    def start_long_rest(self, food_available: bool = True, drink_available: bool = True):
        start_time_str = self.time.get_time_string()
        self._print(f"\n[{start_time_str}] {self.character.name} is starting a long rest (8 hours) in {self.current_town.name}.")
        base_interruption_chance = 0.1

        for i in range(8):
            # The perform_hourly_action will handle recap if midnight is crossed
            self.perform_hourly_action("sleep_one_hour")
            if self.character.exhaustion_level >=6:
                self._print(f"  {self.character.name} perished during rest due to exhaustion.")
                return

        end_time_str = self.time.get_time_string()
        self._print(f"  The long rest period (8 hours of sleep actions) concludes at {end_time_str}.")

        if self.character.exhaustion_level < 6:
            result = self.character.attempt_long_rest(
                food_available=food_available, drink_available=drink_available,
                interruption_chance=base_interruption_chance, hours_of_rest=8
            )
            self._print(f"  Long rest benefits result: {result.get('message', 'No specific result message.')}")
        else:
            self._print(f"  {self.character.name} cannot gain benefits of rest due to prior death.")

    def generate_end_of_day_recap(self, day_number: int):
        # Ensure this recap is for the trackers of the day that just ended.
        if day_number != self.tracking_day:
            self._print(f"Warning: Recap called for Day {day_number} but current tracking is for Day {self.tracking_day}. This might indicate a logic issue if not intended.")
            # Still proceed, but use day_number for the printout. Trackers should be for self.tracking_day.

        self._print(f"\n--- End of Day Recap: Day {day_number} ---")

        committed_xp = self.character.commit_pending_xp()
        self.daily_xp_awarded_this_day = committed_xp

        self._print(f"Gold Earned (Shop Sales to NPCs): {self.daily_gold_earned_from_sales} G")
        self._print(f"Gold Spent (Player Buying from Own Shop): {self.daily_gold_spent_on_purchases_by_player} G")
        self._print(f"Gold Earned (Player Selling Items): {self.daily_gold_player_earned_selling_to_shop} G")
        self._print(f"Shop Visitors: {self.daily_visitors}")
        self._print(f"Experience Points Awarded: {self.daily_xp_awarded_this_day} XP")

        self._print("\nItems Crafted Today:")
        if self.daily_items_crafted:
            for item_name in self.daily_items_crafted: self._print(f"- {item_name}")
        else: self._print("- None")

        self._print("\nItems Sold by Shop Today (to NPCs):")
        if self.daily_items_sold_by_shop_to_npcs:
            for item_name in self.daily_items_sold_by_shop_to_npcs: self._print(f"- {item_name}")
        else: self._print("- None")

        self._print("\nItems Player Bought from Shop Today:")
        if self.daily_items_player_bought_from_shop:
            for item_name in self.daily_items_player_bought_from_shop: self._print(f"- {item_name}")
        else: self._print("- None")

        self._print("\nItems Player Sold to Shop Today:") # Corrected: was missing from previous output
        if self.daily_items_player_sold_to_shop:
            for item_name in self.daily_items_player_sold_to_shop: self._print(f"- {item_name}")
        else: self._print("- None")

        self._print("\nSpecial Events Today:")
        if self.daily_special_events:
            for event_summary in self.daily_special_events: self._print(f"- {event_summary}")
        else: self._print("- None")

        self._print("\nOverheard Customer Dialogue:")
        if self.daily_customer_dialogue_snippets:
            for snippet in self.daily_customer_dialogue_snippets: self._print(f"- \"{snippet}\"")
        else: self._print("- None")
        self._print("-----------------------------------------")

        # Reset trackers for the *new* current day (which GameTime.current_day already reflects)
        self._reset_daily_trackers()


    def simulate_hours(self, num_hours: int, base_action:str = "talk_to_customer", action_details:dict=None):
        self._print(f"\n--- Simulating {num_hours} hours, primarily '{base_action}' ---")
        for _ in range(num_hours):
            self.perform_hourly_action(base_action, action_details)


if __name__ == "__main__":
    # This block will now use standard print, as no output_stream is passed by default here.
    # To test output_stream, you'd do:
    # import io
    # string_io = io.StringIO()
    # player_char = Character(name="Recap Player")
    # gm = GameManager(player_character=player_char, output_stream=string_io)
    # ... run game logic ...
    # print(string_io.getvalue())

    print("--- GameManager Test with Daily Recap (using standard print) ---")
    try:
        from .character import Character
        from .shop import Shop
        from .item import Item
        from .town import Town
        print("Successfully imported components for GameManager test.")
    except ImportError as e:
        print(f"Import error during test setup: {e}")
        # Attempt relative imports for running as a module, then direct for script execution
        try:
            from character import Character
            from shop import Shop
            from item import Item
            from town import Town
            print("Attempted direct imports for script execution.")
        except ImportError:
            print(f"Failed direct imports as well: {e}")
            raise # Re-raise the initial error if all attempts fail

    player_char = Character(name="Recap Player")
    player_char.roll_stats() # Player stats are random by default
    player_char.stats = {"STR": 12, "DEX": 12, "CON": 12, "INT": 12, "WIS": 12, "CHA": 12} # Override for consistency
    player_char.base_max_hp = 10 + player_char._calculate_modifier(player_char.stats["CON"],is_base_stat_score=True) * player_char.level
    player_char.hp = player_char.get_effective_max_hp()
    player_char.hit_dice = player_char.max_hit_dice

    lucky_charm = Item(name="Lucky Charm", description="Reroll", base_value=0, item_type="trinket", quality="Rare", effects={"allow_reroll": True}, is_consumable=True)
    player_char.add_item_to_inventory(lucky_charm)

    # When running this __main__ block, it will use standard print
    gm = GameManager(player_character=player_char)
    # To test with StringIO for this main block:
    # import io
    # test_io_stream = io.StringIO()
    # gm = GameManager(player_character=player_char, output_stream=test_io_stream)

    gm.base_event_chance = 0.15 # Adjusted for more predictable testing

    gm._print(f"\n--- Starting Day {gm.time.current_day} Simulation (target 16 actions + 8 sleep) ---")

    # Day 1 Activities (16 hours of actions)
    # Hour: 07:00 (Start)
    gm.perform_hourly_action("craft", {"item_name": "Minor Healing Potion"}) # 07->08
    gm.perform_hourly_action("talk_to_customer") # 08->09
    gm.perform_hourly_action("craft", {"item_name": "Simple Dagger"})    # 09->10
    gm.perform_hourly_action("research_market") # 10->11

    gm.perform_hourly_action("buy_from_own_shop", {"item_name": "Simple Dagger"}) # 11->12
    gm.perform_hourly_action("talk_to_customer") # 12->13

    player_char.hp -= 7
    gm.perform_hourly_action("rest_short", {"dice_to_spend": 1}) # 13->14

    gm.perform_hourly_action("craft", {"item_name": "Stale Ale"}) # 14->15

    stale_ale_to_sell = None # Find the Stale Ale the shop just crafted
    for item_in_shop_inv in gm.shop.inventory:
        if item_in_shop_inv.name == "Stale Ale":
            # To test player selling, player needs the item. Let's simulate player acquiring it.
            # This is a bit artificial for the test, normally player would craft/find it themselves.
            stale_ale_to_sell = gm.shop.remove_item_from_inventory("Stale Ale", specific_item_to_remove=item_in_shop_inv)
            if stale_ale_to_sell:
                player_char.add_item_to_inventory(stale_ale_to_sell)
                gm._print(f"  (Test setup: Player acquired {stale_ale_to_sell.name} from shop to sell back)")
            break

    if stale_ale_to_sell:
        gold_earned = player_char.sell_item_to_shop(stale_ale_to_sell, gm.shop) # 15->16
        if gold_earned > 0:
            gm.daily_gold_player_earned_selling_to_shop += gold_earned
            gm.daily_items_player_sold_to_shop.append(stale_ale_to_sell.name)
    else: # If shop didn't have Stale Ale (e.g. if crafting failed), just do a default action
        gm._print("  (Test setup: Stale Ale not found in shop to transfer to player for selling test, doing 'talk' instead)")
        gm.perform_hourly_action("talk_to_customer") # 15->16


    gm.perform_hourly_action("research_market") # 16->17
    gm.perform_hourly_action("talk_to_customer") # 17->18
    gm.perform_hourly_action("craft", {"item_name": "Minor Healing Potion"}) # 18->19
    gm.perform_hourly_action("talk_to_customer") # 19->20
    gm.perform_hourly_action("research_market") # 20->21
    gm.perform_hourly_action("talk_to_customer") # 21->22
    gm.perform_hourly_action("craft", {"item_name": "Simple Dagger"}) # 22->23. Day 1 activities end.

    gm.character.display_character_info() # Status before long rest

    # Long rest will take from 23:00 Day 1 to 07:00 Day 2.
    # The recap for Day 1 should trigger when the first hour of sleep ticks over to 00:00 Day 2.
    gm.start_long_rest(food_available=True, drink_available=True)

    # Actions for Day 2
    gm._print(f"\n--- Starting Day {gm.time.current_day} Actions ---")
    gm.perform_hourly_action("research_market") # Day 2, 07:00 -> 08:00 (after long rest)
    gm.perform_hourly_action("talk_to_customer") # Day 2, 08:00 -> 09:00

    # Manually generate recap for Day 2 if simulation ends before midnight
    # This is primarily for test visibility, as the automatic one would only trigger at next midnight.
    if gm.time.current_hour != 0:
        gm._print("\nManually generating recap for current day (Day 2) for testing purposes.")
        gm.generate_end_of_day_recap(day_number=gm.time.current_day)

    gm._print("\n--- GameManager Test with Daily Recap Complete ---")
    # if test_io_stream:
    #     print("\n--- Captured output from test_io_stream: ---")
    #     print(test_io_stream.getvalue())
    #     test_io_stream.close()
