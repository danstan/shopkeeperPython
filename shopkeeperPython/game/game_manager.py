import random
import json # Import json for save/load
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
    def __init__(self, player_character: Character = None, output_stream=None):
        self.output_stream = output_stream
        # Temporarily use print if _print is not yet defined or defined later
        # self._print("Initializing GameManager...")
        print("Initializing GameManager...")

        self.time = GameTime()
        # self._print(f"Game time started at {self.time.get_time_string()}.")
        print(f"Game time started at {self.time.get_time_string()}.")

        if player_character:
            self.character = player_character
            # self._print(f"Using provided character: {self.character.name}")
            print(f"Using provided character: {self.character.name}")
        else:
            # self._print("--- Starting Character Creation ---")
            print("--- Starting Character Creation ---")
            self.character = Character.create_character_interactively()
            # self._print("--- Character Creation Finished ---")
            print("--- Character Creation Finished ---")

        self.character.display_character_info()

        town_starting = Town(
            name="Starting Village",
            properties=["Quiet farming village", "River nearby"],
            nearby_resources=["Fish", "Wheat", "Basic Herbs"],
            unique_npc_crafters=[{"name": "Old Man Hemlock", "specialty": "Herbalism", "services": ["Identifies Herbs"], "quests_available": []}],
            market_demand_modifiers={"Minor Healing Potion": 1.1, "Bread": 0.9, "Fish": 1.05}
        )
        town_steel_flow = Town(
            name="Steel Flow City",
            properties=["Major mining hub", "Strong warrior tradition"],
            nearby_resources=["Iron Ore", "Coal", "Stone"],
            unique_npc_crafters=[{"name": "Borin Stonebeard", "specialty": "Blacksmithing", "services": ["Repairs Gear", "Sells Metal Ingots"], "quests_available": ["Clear Mine Pests"]}],
            market_demand_modifiers={"Simple Dagger": 1.25, "Iron Sword": 1.3, "Minor Healing Potion": 1.15, "Stale Ale": 0.8}
        )

        self.towns = [town_starting, town_steel_flow]
        self.towns_map = {town.name: town for town in self.towns} # For easy lookup by name

        self.current_town = town_starting

        # self._print(f"Player starting in {self.current_town.name}.")
        print(f"Player starting in {self.current_town.name}.")


        self.shop = Shop(name=f"{self.character.name}'s Emporium", owner_name=self.character.name, town=self.current_town)
        # self._print(f"Shop '{self.shop.name}' initialized in {self.current_town.name}.")
        print(f"Shop '{self.shop.name}' initialized in {self.current_town.name}.")

        initial_items = [
            Item(name="Minor Healing Potion", description="A simple potion.", base_value=10, item_type="potion", quality="Common", effects={"healing": 5}, is_consumable=True),
            Item(name="Simple Dagger", description="A basic dagger.", base_value=5, item_type="weapon", quality="Common", effects={"damage": "1d4"}),
            Item(name="Stale Ale", description="Questionable ale.", base_value=1, item_type="food", quality="Common", effects={"stamina_recovery": 1}, is_consumable=True)
        ]
        for item in initial_items:
            self.shop.add_item_to_inventory(item)
        # self._print(f"Stocked initial items in {self.shop.name}.")
        print(f"Stocked initial items in {self.shop.name}.")

        self.event_manager = EventManager(self.character)
        self.base_event_chance = 0.05
        # self._print("EventManager initialized.")
        print("EventManager initialized.")

        self._reset_daily_trackers()
        # self._print("Daily trackers reset.")
        print("Daily trackers reset.")
        # self._print("GameManager initialization complete.")
        print("GameManager initialization complete.")

    def _print(self, message: str):
        if self.output_stream:
            self.output_stream.write(message + "\n") # Add newline for stream output
            self.output_stream.flush() # Ensure it's written out, useful for Flask app
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

    def send_chat_message(self, recipient, message):
        if recipient.lower() == "all" or recipient.lower() == "town_chat":
            print(f"  [TOWN CHAT - {self.current_town.name}] {self.character.name}: {message} (Feature not fully implemented)")
        else:
            print(f"  [CHAT] To {recipient}: {message} (Feature not fully implemented)")
    def use_emote(self, emote_name):
        print(f"  {self.character.name} uses emote: {emote_name}. (Feature not fully implemented)")
    def initiate_trade_with_player(self, other_player_name):
        print(f"  {self.character.name} attempts to trade with {other_player_name}. (Feature not fully implemented)")
    def send_ingame_mail(self, recipient_name, subject, body):
        print(f"  Mail sent to {recipient_name} from {self.character.name} | Subject: {subject} | Body: {body} (Feature not fully implemented)")

    def perform_hourly_action(self, action_name: str, action_details: dict = None):
        action_details = action_details if action_details else {}
        current_day_before_action = self.time.current_day

        # Check for day change and reset daily trackers if a new day has started
        # This check should happen BEFORE the action's print message, so the new day message appears first.
        if self.time.current_hour == 0 and self.tracking_day != self.time.current_day:
            self._print(f"--- End of Day {self.tracking_day} Summary ---")
            self._print(f"  Gold earned from sales: {self.daily_gold_earned_from_sales}")
            self._print(f"  Gold spent by player at shop: {self.daily_gold_spent_on_purchases_by_player}")
            self._print(f"  Gold earned by player selling to shop: {self.daily_gold_player_earned_selling_to_shop}")
            self._print(f"  Visitors: {self.daily_visitors}")
            self._print(f"  Items crafted: {', '.join(self.daily_items_crafted) if self.daily_items_crafted else 'None'}")
            self._print(f"  Items sold to NPCs: {', '.join(item_name for item_name, _ in self.daily_items_sold_by_shop_to_npcs) if self.daily_items_sold_by_shop_to_npcs else 'None'}")
            self._print(f"  Items player bought: {', '.join(item_name for item_name, _ in self.daily_items_player_bought_from_shop) if self.daily_items_player_bought_from_shop else 'None'}")
            self._print(f"  Items player sold: {', '.join(self.daily_items_player_sold_to_shop) if self.daily_items_player_sold_to_shop else 'None'}")
            self._print(f"  Special events: {', '.join(self.daily_special_events) if self.daily_special_events else 'None'}")
            if self.daily_customer_dialogue_snippets:
                self._print("  Overheard Customer Snippets:")
                for snippet in self.daily_customer_dialogue_snippets:
                    self._print(f"    - \"{snippet}\"")

            # Commit XP at the end of the day
            xp_committed = self.character.commit_pending_xp()
            self._print(f"  XP committed from pending: {xp_committed}")
            self.daily_xp_awarded_this_day += xp_committed # Track committed XP

            self._reset_daily_trackers()
            self._print(f"--- Start of Day {self.time.current_day} ---")


        current_time_str = self.time.get_time_string()
        self._print(f"\n[{current_time_str}] {self.character.name} (in {self.current_town.name}) performs action: {action_name}")

        action_xp_reward = 0
        time_advanced_by_action = False # Flag to check if action handles its own time

        if action_name == "craft":
            item_name = action_details.get("item_name")
            if item_name:
                crafted_item = self.shop.craft_item(item_name)
                if crafted_item:
                    self._print(f"  Successfully crafted {crafted_item.quality} {item_name}.")
                    self.daily_items_crafted.append(item_name)
                    action_xp_reward = 10
                else:
                    self._print(f"  Failed to craft {item_name}.")
            else:
                self._print("  No item_name provided for crafting.")

        elif action_name == "buy_from_own_shop":
            item_name = action_details.get("item_name")
            quantity = int(action_details.get("quantity", 1))
            if item_name and quantity > 0:
                items_bought, total_spent = self.character.buy_item_from_shop(item_name, quantity, self.shop)
                if items_bought:
                    # GameManager's _print would already show shop's messages if output_stream is shared.
                    # self._print(f"  {self.character.name} bought {len(items_bought)} of {item_name}(s) for {total_spent}g.")
                    for item_b in items_bought:
                         self.daily_items_player_bought_from_shop.append(item_b.name)
                    self.daily_gold_spent_on_purchases_by_player += total_spent
                    self._handle_customer_interaction(is_sale_or_purchase_by_player_shop=True)
                    action_xp_reward = 2
                # else:
                    # self._print(f"  Could not buy {item_name}.") # Character.buy_item_from_shop prints details
            else:
                self._print("  Invalid item_name or quantity for buying from shop.")

        elif action_name == "sell_to_own_shop":
            item_name = action_details.get("item_name")
            if item_name:
                item_instance_to_sell = next((item for item in self.character.inventory if item.name == item_name), None)
                if item_instance_to_sell:
                    price_paid = self.character.sell_item_to_shop(item_instance_to_sell, self.shop)
                    if price_paid > 0:
                        # self._print(f"  {self.character.name} sold {item_name} for {price_paid}g.") # Character.sell_item_to_shop prints details
                        self.daily_items_player_sold_to_shop.append(item_name)
                        self.daily_gold_player_earned_selling_to_shop += price_paid
                        self._handle_customer_interaction(is_sale_or_purchase_by_player_shop=True)
                        action_xp_reward = 2
                    # else:
                        # self._print(f"  Could not sell {item_name}.") # Character.sell_item_to_shop prints details
                else:
                    self._print(f"  Item '{item_name}' not found in {self.character.name}'s inventory.")
            else:
                self._print("  No item_name provided for selling to shop.")

        elif action_name == "talk_to_self":
            self._print(f"  {self.character.name} mutters something unintelligible.")
            action_xp_reward = 1

        elif action_name == "check_shop_inventory":
            self.shop.display_inventory() # Assumes Shop.display_inventory prints to the shared stream or stdout

        elif action_name == "check_player_inventory":
            self.character.display_character_info() # This method usually includes inventory

        elif action_name == "sleep_one_hour": # Short rest, effectively
            self._print(f"  {self.character.name} rests for one hour.")
            # Simple HP gain, could be tied to CON mod or a fixed small amount
            hp_gained = self.character.heal_hp(1)
            self._print(f"  Gained {hp_gained} HP. Current HP: {self.character.hp}/{self.character.get_effective_max_hp()}")
            # No XP for just one hour of sleep usually

        elif action_name == "sleep_eight_hours": # Long rest
            self._print(f"  {self.character.name} attempts a long rest...")
            food_available = action_details.get("food_available", True)
            drink_available = action_details.get("drink_available", True)
            rest_results = self.character.attempt_long_rest(food_available=food_available, drink_available=drink_available, hours_of_rest=8)
            if rest_results.get("success"):
                self._print(f"  Long rest successful. {rest_results.get('message', '')}")
                self.time.advance_hour(8) # Action itself accounts for all 8 hours.
                time_advanced_by_action = True # Prevent additional hour advancement by main loop.
            else:
                self._print(f"  Long rest failed or interrupted. {rest_results.get('message', '')}")
                # If interrupted, maybe only a short rest's worth of time passes or partial benefits
                # For now, assume 1 hour still passes due to the attempt if not successful but took time.

        elif action_name == "explore_town":
            self._print(f"  {self.character.name} spends an hour exploring {self.current_town.name}.")
            self._print(f"    Properties: {', '.join(self.current_town.properties)}")
            self._print(f"    Nearby Resources: {', '.join(self.current_town.nearby_resources)}")
            crafters = [f"{c['name']} ({c['specialty']})" for c in self.current_town.unique_npc_crafters]
            self._print(f"    Unique NPCs: {', '.join(crafters) if crafters else 'None'}")
            action_xp_reward = 5

        # ADD THIS NEW BLOCK (comment moved above)
        elif action_name == "research_market":
            self._print(f"  {self.character.name} spends an hour researching the market in {self.current_town.name}.")
            # Add some example market insights based on town demand modifiers
            if self.current_town.market_demand_modifiers:
                self._print("    Current market demands attention for:")
                for item_name, modifier in self.current_town.market_demand_modifiers.items():
                    if modifier > 1.1:
                        self._print(f"      - {item_name} (High Demand)")
                    elif modifier < 0.9:
                        self._print(f"      - {item_name} (Low Demand)")
            else:
                self._print("    No specific market demands noted at this time.")
            action_xp_reward = 5

        elif action_name == "travel_to_town":
            town_name = action_details.get("town_name")
            if town_name and town_name in self.towns_map:
                if town_name == self.current_town.name:
                    self._print(f"  Already in {town_name}.")
                else:
                    # Simple travel: fixed time cost, e.g., 3 hours. Could be variable.
                    travel_time_hours = 3
                    self._print(f"  Traveling from {self.current_town.name} to {town_name}... (This will take {travel_time_hours} hours)")
                    self.current_town = self.towns_map[town_name]
                    self.shop.update_town(self.current_town) # Update shop's town
                    self.time.advance_hour(travel_time_hours -1) # -1 because 1 hour passes at end of this function
                    time_advanced_by_action = True
                    self._print(f"  Arrived in {self.current_town.name}. Shop is now operating here.")
                    action_xp_reward = 15
            else:
                self._print(f"  Invalid town name for travel: {town_name}. Available: {list(self.towns_map.keys())}")

        elif action_name == "debug_trigger_event": # For testing
            if SAMPLE_EVENTS:
                event_to_trigger = random.choice(SAMPLE_EVENTS)
                self._print(f"  DEBUG: Manually triggering event: {event_to_trigger.name}")
                self.event_manager.resolve_event(event_to_trigger)
                self.daily_special_events.append(event_to_trigger.name)
            else:
                self._print("  DEBUG: No sample events to trigger.")

        elif action_name == "wait":
            self._print(f"  {self.character.name} waits for an hour, observing the surroundings.")
            # Small chance of something minor happening or just time passing.
            action_xp_reward = 1

        else:
            self._print(f"  Action '{action_name}' is not recognized or implemented yet.")

        # Award XP if any was gained from the action
        if action_xp_reward > 0:
            self.character.award_xp(action_xp_reward)
            self.daily_xp_awarded_this_day += action_xp_reward # Track all XP awarded, pending or direct.
                                                            # commit_pending_xp will move it from pending.

        # Advance time by 1 hour for the action, unless action handled its own time
        if not time_advanced_by_action:
            days_passed, _ = self.time.advance_hour(1)
            # If a new day ticked over due to this single hour advancement, also trigger EOD summary.
            # This handles cases where an action at 23:00 pushes time to 00:00 of next day.
            if days_passed > 0 and self.tracking_day != self.time.current_day:
                self._print(f"--- End of Day {self.tracking_day} Summary (after action at 23:00) ---")
                # ... (repeat EOD summary logic as above, or refactor to a method)
                xp_committed = self.character.commit_pending_xp()
                self._print(f"  XP committed from pending: {xp_committed}")
                self.daily_xp_awarded_this_day += xp_committed
                self._reset_daily_trackers()
                self._print(f"--- Start of Day {self.time.current_day} ---")

        # Chance to trigger a random event after the action if not a specific event-related action
        if action_name not in ["debug_trigger_event"] and random.random() < self.base_event_chance:
            triggered_event_name = self.event_manager.trigger_random_event(SAMPLE_EVENTS)
            if triggered_event_name:
                self.daily_special_events.append(triggered_event_name)
                # Event manager's resolve_event should handle its own printing.

        # NPC shop sales simulation (if shop has items, NPCs might buy)
        # This can happen passively each hour after player action.
        sale_price = 0 # Initialize sale_price to ensure it's always defined
        if action_name not in ["buy_from_own_shop", "sell_to_own_shop"]: # Avoid double interaction if player just did shop stuff
            if self.shop.inventory and random.random() < 0.1: # Lower chance for passive sales
                item_to_sell = random.choice(self.shop.inventory)
                # NPCs offer a bit less, e.g. 80-100% of base sale price
                npc_offer_mult = random.uniform(0.8, 1.0)
                sale_price = self.shop.complete_sale_to_npc(item_to_sell.name, npc_offer_percentage=npc_offer_mult)
            if sale_price is not None and sale_price > 0: # MODIFIED LINE
                    self._print(f"  [NPC Sale] {self.shop.name} sold {item_to_sell.name} to an NPC for {sale_price}g.")
                    self.daily_items_sold_by_shop_to_npcs.append((item_to_sell.name, sale_price))
                    self.daily_gold_earned_from_sales += sale_price
                    self._handle_customer_interaction(is_sale_or_purchase_by_player_shop=True) # An NPC sale is a shop interaction
            else:
                # Generic customer browsing if no sale
                self._handle_customer_interaction()


        # Display character status briefly if significant changes occurred or periodically
        # For now, we can rely on specific actions like 'check_player_inventory'
        # or print changes directly as they happen (e.g. HP gain).
