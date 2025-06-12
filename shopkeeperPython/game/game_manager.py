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
    def __init__(self): # player_character argument removed
        self.time = GameTime()

        # Character creation is now handled by the Character class interactively
        print("--- Starting Character Creation ---")
        self.character = Character.create_character_interactively()
        print("--- Character Creation Finished ---")

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

        # Shop initialization now uses the created character's name
        self.shop = Shop(name=f"{self.character.name}'s Emporium", owner_name=self.character.name, town=self.current_town)

        self.event_manager = EventManager(self.character)
        self.base_event_chance = 0.05
        self._reset_daily_trackers()
        # The character's name is now available after interactive creation
        print(f"GameManager initialized. {self.character.name}'s shop established in {self.current_town.name}.")

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
        print(f"[{self.time.get_time_string()}] Daily trackers have been reset for Day {self.tracking_day}.")

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
            print(f"  Overheard: \"{formatted_snippet}\"")

    def perform_hourly_action(self, action_name: str, action_details: dict = None):
        action_details = action_details if action_details else {}

        current_day_before_action = self.time.current_day
        # current_hour_before_action = self.time.current_hour # Not strictly needed for recap logic now

        # If it's already midnight when starting the action, it means a new day just began due to a previous long rest.
        # The recap for the *previous* day should have already happened.
        if self.time.current_hour == 0 and self.tracking_day != self.time.current_day :
             print(f"DEBUG: New day {self.time.current_day} started. Previous tracking day was {self.tracking_day}.")
             # This indicates trackers should have been reset, or recap for tracking_day is due.
             # However, recap is for the day that *just ended*.
             # The main recap trigger is *after* time advances.

        current_time_str = self.time.get_time_string()
        print(f"\n[{current_time_str}] {self.character.name} (in {self.current_town.name}) performs action: {action_name}")
        action_xp_reward = 0

        if action_name == "craft":
            item_name = action_details.get("item_name")
            if item_name:
                crafted_item = self.shop.craft_item(item_name)
                if crafted_item:
                    self.daily_items_crafted.append(crafted_item.name)
            else: print("  Crafting action chosen, but no item_name specified.")

        elif action_name == "rest_short":
            self.character.take_short_rest(action_details.get("dice_to_spend", 1))

        elif action_name == "sleep_one_hour":
            print(f"  {self.character.name} sleeps for an hour in {self.current_town.name}...")

        elif action_name == "talk_to_customer":
            print(f"  {self.character.name} spends an hour at {self.shop.name} attending to the shop.")
            self._handle_customer_interaction(is_sale_or_purchase_by_player_shop=False)
            if self.shop.inventory and random.random() < 0.3:
                item_to_sell_to_npc = random.choice(self.shop.inventory)
                sale_price = self.shop.complete_sale_to_npc(item_to_sell_to_npc.name)
                if sale_price > 0:
                    self.daily_items_sold_by_shop_to_npcs.append(item_to_sell_to_npc.name)
                    self.daily_gold_earned_from_sales += sale_price
                    print(f"  DEBUG: daily_gold_earned_from_sales updated to: {self.daily_gold_earned_from_sales} after sale of {sale_price}g")
                    self._handle_customer_interaction(is_sale_or_purchase_by_player_shop=True)

        elif action_name == "research_market":
            print(f"  {self.character.name} conducting market research in {self.current_town.name}...")
            print(f"    Current demand modifiers: {self.current_town.market_demand_modifiers}")
            print(f"    Nearby resources: {self.current_town.nearby_resources}")
            if self.current_town.market_demand_modifiers:
                high_demand_items = {item: mod for item, mod in self.current_town.market_demand_modifiers.items() if mod > 1.1}
                if high_demand_items:
                    random_high_demand_item = random.choice(list(high_demand_items.keys()))
                    print(f"    Insight: There seems to be high demand for '{random_high_demand_item}' right now!")
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
                else: print(f"  {self.shop.name} does not have {item_name_to_buy} to be bought by {self.character.name}.")
            else: print("  'buy_from_own_shop' action chosen, but no item_name specified.")
        else:
            print(f"  Action '{action_name}' is recognized but has no specific implementation yet.")

        if action_xp_reward > 0:
            xp_awarded = self.character.award_xp(action_xp_reward)
            # self.daily_xp_awarded_this_day += xp_awarded # This is now handled by commit_pending_xp in recap

        if random.random() < self.base_event_chance:
            print(f"![EVENT CHANCE MET AFTER ACTION {action_name}]!")
            if SAMPLE_EVENTS:
                triggered_event_name = self.event_manager.trigger_random_event(SAMPLE_EVENTS)
                if triggered_event_name:
                     self.daily_special_events.append(triggered_event_name)
            else: print("  (No sample events defined to trigger)")

        days_advanced, new_hour = self.time.advance_hour(1)

        if days_advanced > 0: # Midnight was crossed
             self.generate_end_of_day_recap(day_number=current_day_before_action)

        return {"status": "completed", "action": action_name, "new_time": self.time.get_time_string()}

    def start_long_rest(self, food_available: bool = True, drink_available: bool = True):
        start_time_str = self.time.get_time_string()
        print(f"\n[{start_time_str}] {self.character.name} is starting a long rest (8 hours) in {self.current_town.name}.")
        base_interruption_chance = 0.1

        for i in range(8):
            # The perform_hourly_action will handle recap if midnight is crossed
            self.perform_hourly_action("sleep_one_hour")
            if self.character.exhaustion_level >=6:
                print(f"  {self.character.name} perished during rest due to exhaustion.")
                return

        end_time_str = self.time.get_time_string()
        print(f"  The long rest period (8 hours of sleep actions) concludes at {end_time_str}.")

        if self.character.exhaustion_level < 6:
            result = self.character.attempt_long_rest(
                food_available=food_available, drink_available=drink_available,
                interruption_chance=base_interruption_chance, hours_of_rest=8
            )
            print(f"  Long rest benefits result: {result.get('message', 'No specific result message.')}")
        else:
            print(f"  {self.character.name} cannot gain benefits of rest due to prior death.")

    def generate_end_of_day_recap(self, day_number: int):
        # Ensure this recap is for the trackers of the day that just ended.
        if day_number != self.tracking_day:
            print(f"Warning: Recap called for Day {day_number} but current tracking is for Day {self.tracking_day}. This might indicate a logic issue if not intended.")
            # Still proceed, but use day_number for the printout. Trackers should be for self.tracking_day.

        print(f"\n--- End of Day Recap: Day {day_number} ---")

        committed_xp = self.character.commit_pending_xp()
        self.daily_xp_awarded_this_day = committed_xp

        print(f"Gold Earned (Shop Sales to NPCs): {self.daily_gold_earned_from_sales} G")
        print(f"Gold Spent (Player Buying from Own Shop): {self.daily_gold_spent_on_purchases_by_player} G")
        print(f"Gold Earned (Player Selling Items): {self.daily_gold_player_earned_selling_to_shop} G")
        print(f"Shop Visitors: {self.daily_visitors}")
        print(f"Experience Points Awarded: {self.daily_xp_awarded_this_day} XP")

        print("\nItems Crafted Today:")
        if self.daily_items_crafted:
            for item_name in self.daily_items_crafted: print(f"- {item_name}")
        else: print("- None")

        print("\nItems Sold by Shop Today (to NPCs):")
        if self.daily_items_sold_by_shop_to_npcs:
            for item_name in self.daily_items_sold_by_shop_to_npcs: print(f"- {item_name}")
        else: print("- None")

        print("\nItems Player Bought from Shop Today:")
        if self.daily_items_player_bought_from_shop:
            for item_name in self.daily_items_player_bought_from_shop: print(f"- {item_name}")
        else: print("- None")

        print("\nItems Player Sold to Shop Today:") # Corrected: was missing from previous output
        if self.daily_items_player_sold_to_shop:
            for item_name in self.daily_items_player_sold_to_shop: print(f"- {item_name}")
        else: print("- None")

        print("\nSpecial Events Today:")
        if self.daily_special_events:
            for event_summary in self.daily_special_events: print(f"- {event_summary}")
        else: print("- None")

        print("\nOverheard Customer Dialogue:")
        if self.daily_customer_dialogue_snippets:
            for snippet in self.daily_customer_dialogue_snippets: print(f"- \"{snippet}\"")
        else: print("- None")
        print("-----------------------------------------")

        # Reset trackers for the *new* current day (which GameTime.current_day already reflects)
        self._reset_daily_trackers()

        # Prompt for skill allocation if points are available
        if self.character.skill_points_to_allocate > 0:
            self._prompt_skill_allocation()


    def _prompt_skill_allocation(self):
        """
        Prompts the player to allocate skill points if available.
        """
        print(f"\n--- Skill Point Allocation for {self.character.name} ---")
        while self.character.skill_points_to_allocate > 0:
            print(f"\nYou have {self.character.skill_points_to_allocate} skill point(s) to allocate.")
            self.character.display_character_info() # Show current stats for context

            stat_options = ", ".join(Character.STAT_NAMES)
            prompt_message = f"Choose a skill to increase ({stat_options}), or type 'help' for current stats: "

            try:
                choice = input(prompt_message).strip().upper()
            except (EOFError, KeyboardInterrupt):
                print("\nSkill allocation interrupted. You can allocate points later.")
                return # Exit if input stream is closed or interrupted

            if choice == 'HELP':
                continue # Loop will re-display stats

            if self.character.allocate_skill_point(choice):
                print(f"Successfully allocated point to {choice}.")
                if self.character.skill_points_to_allocate == 0:
                    print("All skill points allocated.")
            else:
                # allocate_skill_point already prints error messages for invalid skill or no points
                print("Please try again or type 'help'.")
        print("--- Skill Point Allocation Finished ---")


    def simulate_hours(self, num_hours: int, base_action:str = "talk_to_customer", action_details:dict=None):
        print(f"\n--- Simulating {num_hours} hours, primarily '{base_action}' ---")
        for _ in range(num_hours):
            self.perform_hourly_action(base_action, action_details)


if __name__ == "__main__":
    print("--- GameManager Test with Daily Recap ---")
    try:
        from .character import Character
        from .shop import Shop
        from .item import Item
        from .town import Town
        print("Successfully imported components for GameManager test.")
    except ImportError as e:
        print(f"Import error during test setup: {e}")
        from character import Character
        from shop import Shop
        from item import Item
        from town import Town
        print("Attempted direct imports.")

    # player_char = Character(name="Recap Player") # Old character creation removed
    # player_char.roll_stats() # Stats are now rolled interactively
    # player_char.stats = {"STR": 12, "DEX": 12, "CON": 12, "INT": 12, "WIS": 12, "CHA": 12} # Manual setting removed
    # player_char.base_max_hp = 10 + player_char._calculate_modifier(player_char.stats["CON"],is_base_stat_score=True) * player_char.level # HP calc is now internal
    # player_char.hp = player_char.get_effective_max_hp()
    # player_char.hit_dice = player_char.max_hit_dice # Hit dice also internal

    # GameManager now handles character creation internally.
    # This will trigger the interactive prompts if __main__ is run.
    gm = GameManager() # No longer takes player_character argument

    # Grant XP to ensure level up for testing skill allocation
    xp_to_grant_for_level_up = 295 # Level 2 is 300 XP. research_market gives 5 XP.
    print(f"\n(Test Setup: Granting {gm.character.name} {xp_to_grant_for_level_up} XP to ensure level up for skill allocation test)")
    gm.character.award_xp(xp_to_grant_for_level_up)
    # Committing XP here would trigger level up before the day starts.
    # We want it to happen at End of Day Recap.

    # The Lucky Charm can be added after character creation if needed for testing specific scenarios,
    # but for a standard run, inventory starts empty unless modified by character creation itself.
    # For now, let's assume the test proceeds without automatically adding it,
    # or it could be added via a game event or initial shop stock.
    # If direct addition for testing is needed:
    # lucky_charm = Item(name="Lucky Charm", description="Reroll", base_value=0, item_type="trinket", quality="Rare", effects={"allow_reroll": True}, is_consumable=True)
    # gm.character.add_item_to_inventory(lucky_charm)
    # print(f"  (Test setup: Added Lucky Charm to {gm.character.name}'s inventory)")


    gm.base_event_chance = 0.15 # Adjusted for more predictable testing

    print(f"\n--- Starting Day {gm.time.current_day} Simulation for {gm.character.name} (target 16 actions + 8 sleep) ---")

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

    stale_ale_to_sell = None
    # Attempt to find Stale Ale if the shop crafted it.
    # The shop inventory might not have it if crafting failed or was not chosen.
    if "Stale Ale" in gm.daily_items_crafted: # Check if it was crafted today
        for item_in_shop_inv in gm.shop.inventory:
            if item_in_shop_inv.name == "Stale Ale":
                # Simulate player acquiring it for selling test.
                stale_ale_to_sell = gm.shop.remove_item_from_inventory("Stale Ale", specific_item_to_remove=item_in_shop_inv)
                if stale_ale_to_sell:
                    gm.character.add_item_to_inventory(stale_ale_to_sell) # Use gm.character
                    print(f"  (Test setup: Player {gm.character.name} acquired {stale_ale_to_sell.name} from shop to sell back)")
                break

    if stale_ale_to_sell:
        # Player sells the item. The action itself does not advance time here.
        # The original code had sell_item_to_shop as part of an hour, let's make it an explicit action.
        # For now, we'll assume selling it is part of the "talk_to_customer" or a dedicated "manage_inventory" hour.
        # To keep the hour structure, let's wrap this in a conceptual action or assume it's quick.
        # The original test structure implies this was part of hour 15->16.
        # We'll log it but not explicitly make it a separate perform_hourly_action call unless necessary.
        # The gold/item tracking should be done within sell_item_to_shop.

        # The original test structure did this:
        # gold_earned = player_char.sell_item_to_shop(stale_ale_to_sell, gm.shop) # 15->16
        # if gold_earned > 0:
        #     gm.daily_gold_player_earned_selling_to_shop += gold_earned
        #     gm.daily_items_player_sold_to_shop.append(stale_ale_to_sell.name)
        # This logic is now mostly within character.sell_item_to_shop and shop.buy_item_from_character
        # We just need to ensure the daily trackers are updated.

        # Let's make selling an explicit action for clarity in the test, even if it's quick.
        print(f"  [{gm.time.get_time_string()}] {gm.character.name} will now attempt to sell {stale_ale_to_sell.name}.")
        gold_earned = gm.character.sell_item_to_shop(stale_ale_to_sell, gm.shop)
        if gold_earned > 0:
            # These trackers should ideally be updated by the sell_item_to_shop or a wrapper in GameManager
            # For now, let's assume the test needs to update them if sell_item_to_shop doesn't.
            # Looking at Character.sell_item_to_shop, it doesn't update GameManager's trackers.
            gm.daily_gold_player_earned_selling_to_shop += gold_earned
            gm.daily_items_player_sold_to_shop.append(stale_ale_to_sell.name)
            print(f"  Action: Sell item {stale_ale_to_sell.name} (completed within current hour). Gold earned: {gold_earned}")
        else:
            print(f"  Action: Sell item {stale_ale_to_sell.name} failed or item was not sold.")
            # If selling failed, put it back in player inventory for test consistency if needed, or handle as lost.
            # For now, assume it's gone or sale failed as per method.
            # If it failed, it should still be in player's inventory.
            if stale_ale_to_sell not in gm.character.inventory: # If it was removed by a partial sell attempt
                 gm.character.add_item_to_inventory(stale_ale_to_sell) # Put it back for test consistency
                 print(f"  (Test info: {stale_ale_to_sell.name} re-added to player inventory after failed sale attempt)")


    else: # If shop didn't have Stale Ale or it wasn't transferred
        print(f"  (Test info: {gm.character.name} does not have Stale Ale to sell, or item not found in shop. Skipping player selling action.)")
        # This hour (15->16) would then proceed with its original action if selling was meant to be "instead of"
        # The original code had this as an else block for a perform_hourly_action.
        # Let's assume the selling attempt was part of the 15->16 hour block.
        # If selling didn't happen, the hour is still spent.

    # The original test had gm.perform_hourly_action("talk_to_customer") in the else block.
    # If selling is a quick part of an hour, the main action for that hour still happens.
    # For simplicity, let's assume the hour 15->16 was "manage shop / attempt sale".
    # So, we'll just advance time with a generic action if no sale was made.
    # This part of the test logic needs to be robust to whether the item exists.
    # The hour 15->16 was originally the sell action. We'll call a generic action if sell didn't happen.
    if not stale_ale_to_sell or gold_earned == 0 :
         gm.perform_hourly_action("talk_to_customer") # 15->16 (if sale didn't occur or wasn't primary action)
    else:
        # If sale happened, the hour was still used. We need to ensure time advances.
        # The original test implies the sale itself was the action for that hour.
        # So, if sale was successful, that WAS the 15->16 action.
        # We need to make sure an action is performed for each hour.
        # The structure was:
        # IF stale_ale_to_sell:
        #   player_char.sell_item_to_shop(...) -> THIS WAS THE ACTION
        # ELSE:
        #   gm.perform_hourly_action("talk_to_customer") -> THIS WAS THE ACTION
        # So, if the sale attempt happened (regardless of success), that was the hour's "event".
        # We need to ensure an `perform_hourly_action` is called or time is advanced.
        # Let's assume "attempt_sell_item" could be an action.
        # For now, if a sale was attempted, we'll consider that the hour's activity.
        # The time advancement is handled by perform_hourly_action.
        # The original code is a bit ambiguous here. Let's ensure an action always consumes the hour.
        # If selling was the action for 15->16:
        if stale_ale_to_sell: # i.e. an attempt was made
            # We need to ensure the time advances for this hour.
            # The original code did not call perform_hourly_action if a sale was made.
            # This is a gap. Let's fix it by wrapping the sell in an action or just advancing time.
            # Simplest: if a sale was attempted, that was the hour's main focus.
            # We'll assume the sell_item_to_shop itself doesn't advance time system.
            # So, we still need perform_hourly_action for time progression and events.
            # Let's make "managing inventory/sales" the action for this hour.
            gm.perform_hourly_action("manage_inventory_sales") # 15->16
        # This means the `else` block for `talk_to_customer` was correct if no sale attempt.

    gm.perform_hourly_action("research_market") # 16->17 (This should be hour after selling attempt)
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
    print(f"\n--- Starting Day {gm.time.current_day} Actions ---")
    gm.perform_hourly_action("research_market") # Day 2, 07:00 -> 08:00 (after long rest)
    gm.perform_hourly_action("talk_to_customer") # Day 2, 08:00 -> 09:00

    # Manually generate recap for Day 2 if simulation ends before midnight
    # This is primarily for test visibility, as the automatic one would only trigger at next midnight.
    if gm.time.current_hour != 0:
        print("\nManually generating recap for current day (Day 2) for testing purposes.")
        gm.generate_end_of_day_recap(day_number=gm.time.current_day)

    print("\n--- GameManager Test with Daily Recap Complete ---")
