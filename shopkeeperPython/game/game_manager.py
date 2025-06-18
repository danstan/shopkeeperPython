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
        self._print("Initializing GameManager (basic)...")

        self.time = GameTime()
        self._print(f"Game time started at {self.time.get_time_string()}.")

        self.character = player_character if player_character else Character(name=None)
        if self.character and self.character.name:
            self._print(f"Initial character reference: {self.character.name}")
        else:
            self._print("GameManager initialized with a default/empty character object.")

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
        self.towns_map = {town.name: town for town in self.towns}

        self.current_town = town_starting
        self._print(f"Default current town set to: {self.current_town.name}")

        self.shop = None
        self.event_manager = None
        self.base_event_chance = 0.05
        self._print(f"Base event chance set to: {self.base_event_chance}")


        self._reset_daily_trackers()
        self._print("Daily trackers reset initially.")

        self.is_game_setup = False
        self._print("GameManager basic initialization complete. Call setup_for_character for full game world setup for a character.")

    def setup_for_character(self, new_character: Character):
        self._print(f"--- Setting up game world for character: {new_character.name if new_character and new_character.name else 'Unnamed/Invalid Character'} ---")

        if not new_character or not new_character.name: # Character must exist and have a name
            self._print("Error: A valid Character object with a name is required for setup.")
            self.is_game_setup = False # Explicitly mark as not setup
            # self.character = Character(name=None) # Optionally revert to a blank character state
            return

        self.character = new_character
        self._print(f"Active character set to: {self.character.name}")

        # Check if character has display_character_info and if it's callable
        if hasattr(self.character, 'display_character_info') and callable(self.character.display_character_info):
            self.character.display_character_info()
        else:
            self._print(f"Character {self.character.name} has no display_character_info method or it's not callable.")


        starting_town_name = "Starting Village" # Default starting town
        selected_starting_town = self.towns_map.get(starting_town_name)

        if not selected_starting_town:
            self._print(f"CRITICAL: Default starting town '{starting_town_name}' not found in towns_map.")
            if self.towns: # Fallback to the first town in the list
                self._print(f"Warning: Falling back to the first town in the list: {self.towns[0].name}")
                selected_starting_town = self.towns[0]
            else: # This is a severe issue: no towns are defined at all.
                self._print("CRITICAL: No towns available at all. Cannot set current_town for character.")
                self.is_game_setup = False # Cannot complete setup
                return

        self.current_town = selected_starting_town
        self._print(f"Player character {self.character.name} starting in/moved to: {self.current_town.name}.")

        # Initialize Shop for the character
        self.shop = Shop(name=f"{self.character.name}'s Emporium", owner_name=self.character.name, town=self.current_town)
        self._print(f"Shop '{self.shop.name}' initialized/updated in {self.current_town.name} for owner {self.character.name}.")

        # Stock initial items in the shop
        self.shop.inventory = [] # Clear any previous inventory
        initial_items = [
            Item(name="Minor Healing Potion", description="A simple potion.", base_value=10, item_type="potion", quality="Common", effects={"healing": 5}, is_consumable=True),
            Item(name="Simple Dagger", description="A basic dagger.", base_value=5, item_type="weapon", quality="Common", effects={"damage": "1d4"}),
            Item(name="Stale Ale", description="Questionable ale.", base_value=1, item_type="food", quality="Common", effects={"stamina_recovery": 1}, is_consumable=True)
        ]
        for item in initial_items:
            self.shop.add_item_to_inventory(item)
        self._print(f"Stocked initial items in {self.shop.name}.")

        # Initialize EventManager for the character
        self.event_manager = EventManager(self.character)
        self._print(f"EventManager initialized/updated for character: {self.character.name}.")

        self._reset_daily_trackers() # Reset daily stats for the new character setup
        self._print("Daily trackers reset for the new character setup.")

        self.is_game_setup = True # Mark the game as successfully set up for this character
        self._print(f"--- Game world setup complete for {self.character.name}. is_game_setup: {self.is_game_setup} ---")

    def _print(self, message: str):
        if self.output_stream:
            self.output_stream.write(message + "\n")
            self.output_stream.flush()
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
        # Ensure time object exists before trying to access current_day
        if hasattr(self, 'time') and self.time:
             self.tracking_day = self.time.current_day
        else:
             self.tracking_day = 1 # Default if time system isn't up yet (e.g. during early __init__)

    def _handle_customer_interaction(self, is_sale_or_purchase_by_player_shop:bool = False):
        # Ensure shop is initialized before proceeding
        if not self.shop:
            return

        self.daily_visitors += 1
        dialogue_chance = 0.3 if is_sale_or_purchase_by_player_shop else 0.1
        if random.random() < dialogue_chance:
            snippet_type = random.choice(["positive", "neutral", "negative"]) # Default choice
            # More specific choices based on shop status
            if self.shop.gold < 200 and not self.shop.inventory:
                 snippet_type = "negative"
            elif len(self.shop.inventory) > 2 :
                 snippet_type = random.choice(["positive", "neutral", "positive"])

            # Fallback logic if snippet_type is invalid or its list is empty
            if snippet_type not in CUSTOMER_DIALOGUE_TEMPLATES or not CUSTOMER_DIALOGUE_TEMPLATES[snippet_type]:
                valid_keys = [k for k in CUSTOMER_DIALOGUE_TEMPLATES.keys() if CUSTOMER_DIALOGUE_TEMPLATES[k]] # Keys with non-empty lists
                all_snippets = [s for k_val in valid_keys for s in CUSTOMER_DIALOGUE_TEMPLATES[k_val]] if valid_keys else []
                if not all_snippets:
                    return # No dialogues to show
                snippet = random.choice(all_snippets)
            else:
                snippet = random.choice(CUSTOMER_DIALOGUE_TEMPLATES[snippet_type])

            town_name_for_dialogue = self.current_town.name if self.current_town else "this town"
            formatted_snippet = snippet.format(town_name=town_name_for_dialogue)
            self.daily_customer_dialogue_snippets.append(formatted_snippet)
            self._print(f"  Overheard: "{formatted_snippet}"")

    def action_talk_to_customer(self, details: dict):
        if not self.shop:
            self._print("  Shop is not initialized. Cannot talk to customers.")
            return

        if not CUSTOMER_DIALOGUE_TEMPLATES:
            self._print("  No customer dialogues defined.") # Should not happen if defined globally
            return

        snippet_type = "neutral" # Default
        if self.shop.gold < 100 and len(self.shop.inventory) == 0:
            snippet_type = "negative"
        else:
            choices = ["positive", "neutral", "positive", "neutral"]
            valid_keys = [k for k in CUSTOMER_DIALOGUE_TEMPLATES.keys() if CUSTOMER_DIALOGUE_TEMPLATES[k]]
            if valid_keys:
                choices.extend(valid_keys)
            snippet_type = random.choice(choices) if choices else "neutral" # Ensure choices is not empty


        if snippet_type not in CUSTOMER_DIALOGUE_TEMPLATES or not CUSTOMER_DIALOGUE_TEMPLATES[snippet_type]:
            valid_keys_fallback = [k for k in CUSTOMER_DIALOGUE_TEMPLATES.keys() if CUSTOMER_DIALOGUE_TEMPLATES[k]]
            all_snippets = [s for k_val in valid_keys_fallback for s in CUSTOMER_DIALOGUE_TEMPLATES[k_val]] if valid_keys_fallback else []
            if not all_snippets:
                self._print("  No customer dialogues available at all.")
                return
            snippet = random.choice(all_snippets)
        else:
            snippet = random.choice(CUSTOMER_DIALOGUE_TEMPLATES[snippet_type])

        town_name_for_dialogue = self.current_town.name if self.current_town else "this place"
        formatted_snippet = snippet.format(town_name=town_name_for_dialogue)
        self._print(f"  You approach a customer. They say: "{formatted_snippet}"")
        self.daily_customer_dialogue_snippets.append(f"(Directly engaged) {formatted_snippet}")

    def send_chat_message(self, recipient, message):
        town_name_display = self.current_town.name if self.current_town else "Unknown Town"
        char_name_display = self.character.name if self.character and self.character.name else "Someone"
        if recipient.lower() == "all" or recipient.lower() == "town_chat":
            self._print(f"  [TOWN CHAT - {town_name_display}] {char_name_display}: {message} (Feature not fully implemented)")
        else:
            self._print(f"  [CHAT] To {recipient}: {message} (Feature not fully implemented)")

    def use_emote(self, emote_name):
        char_name_display = self.character.name if self.character and self.character.name else "Someone"
        self._print(f"  {char_name_display} uses emote: {emote_name}. (Feature not fully implemented)")

    def initiate_trade_with_player(self, other_player_name):
        char_name_display = self.character.name if self.character and self.character.name else "Someone"
        self._print(f"  {char_name_display} attempts to trade with {other_player_name}. (Feature not fully implemented)")

    def send_ingame_mail(self, recipient_name, subject, body):
        char_name_display = self.character.name if self.character and self.character.name else "Someone"
        self._print(f"  Mail sent to {recipient_name} from {char_name_display} | Subject: {subject} | Body: {body} (Feature not fully implemented)")

    def _run_end_of_day_summary(self, day_ended):
        self._print(f"--- End of Day {day_ended} Summary ---")
        self._print(f"  Gold earned from sales: {self.daily_gold_earned_from_sales}")
        self._print(f"  Gold spent by player at shop: {self.daily_gold_spent_on_purchases_by_player}")
        self._print(f"  Gold earned by player selling to shop: {self.daily_gold_player_earned_selling_to_shop}")
        self._print(f"  Visitors: {self.daily_visitors}")
        self._print(f"  Items crafted: {', '.join(self.daily_items_crafted) if self.daily_items_crafted else 'None'}")
        sold_item_names_eod = [name for name, price in self.daily_items_sold_by_shop_to_npcs]
        self._print(f"  Items sold to NPCs: {', '.join(sold_item_names_eod) if sold_item_names_eod else 'None'}")
        self._print(f"  Items player bought: {', '.join(self.daily_items_player_bought_from_shop) if self.daily_items_player_bought_from_shop else 'None'}")
        self._print(f"  Items player sold: {', '.join(self.daily_items_player_sold_to_shop) if self.daily_items_player_sold_to_shop else 'None'}")
        self._print(f"  Special events: {', '.join(self.daily_special_events) if self.daily_special_events else 'None'}")
        if self.daily_customer_dialogue_snippets:
            self._print("  Overheard Customer Snippets (EOD):")
            for snippet in self.daily_customer_dialogue_snippets:
                self._print(f"    - "{snippet}"")

        # Commit XP only if character is alive and exists
        if self.character and hasattr(self.character, 'is_dead') and not self.character.is_dead :
            xp_committed = self.character.commit_pending_xp()
            self._print(f"  XP committed from pending (EOD): {xp_committed}")

        self._reset_daily_trackers() # Reset for the new day
        self._print(f"--- Start of Day {self.time.current_day} ---")


    def perform_hourly_action(self, action_name: str, action_details: dict = None):
        # Guard clause for essential game components
        if not self.is_game_setup or            not self.character or not hasattr(self.character, 'name') or not self.character.name or            not self.shop or            not self.event_manager:
            self._print("Game is not fully set up for a character, or essential components (character, shop, event_manager) are missing. Cannot perform hourly action.")
            # Provide info if character is dead
            if self.character and hasattr(self.character, 'is_dead') and self.character.is_dead:
                 char_name = self.character.name if hasattr(self.character, 'name') else 'Character'
                 self._print(f"{char_name} is resting. Not peacefully.")
            return

        action_details = action_details if action_details else {}

        # EOD Check 1: Action starts on a new day (e.g., game loads at 00:00 after a day passed offline)
        if self.time.current_hour == 0 and self.tracking_day != self.time.current_day:
            self._run_end_of_day_summary(self.tracking_day)

        current_time_str = self.time.get_time_string()
        town_name_display = self.current_town.name if self.current_town else "Unknown Location"
        # Using f-string for newline for clarity
        self._print(f"[{current_time_str}] {self.character.name} (in {town_name_display}) performs action: {action_name}")

        action_xp_reward = 0
        time_advanced_by_action_hours = 0 # Default to 0, action will set if it consumes specific time

        # Handle actions for dead characters separately
        if hasattr(self.character, 'is_dead') and self.character.is_dead:
            self._print(f"  {self.character.name} is dead and cannot perform actions.")
            time_advanced_by_action_hours = 1 # Dead characters still pass time
        else:
            # --- Action Implementations (character is alive) ---
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
                        for item_b in items_bought: # items_bought is a list of Item objects
                            self.daily_items_player_bought_from_shop.append(item_b.name)
                        self.daily_gold_spent_on_purchases_by_player += total_spent
                        self._handle_customer_interaction(is_sale_or_purchase_by_player_shop=True)
                        action_xp_reward = 2
                else:
                    self._print("  Invalid item_name or quantity for buying from shop.")

            elif action_name == "sell_to_own_shop":
                item_name = action_details.get("item_name")
                if item_name:
                    # Find the first instance of the item in inventory
                    item_instance_to_sell = next((item for item in self.character.inventory if item.name == item_name), None)
                    if item_instance_to_sell:
                        price_paid = self.character.sell_item_to_shop(item_instance_to_sell, self.shop)
                        if price_paid > 0: # sell_item_to_shop returns price or 0
                            self.daily_items_player_sold_to_shop.append(item_name)
                            self.daily_gold_player_earned_selling_to_shop += price_paid
                            self._handle_customer_interaction(is_sale_or_purchase_by_player_shop=True)
                            action_xp_reward = 2
                        # else: Character.sell_item_to_shop prints failure reasons
                    else:
                        self._print(f"  Item '{item_name}' not found in {self.character.name}'s inventory.")
                else:
                    self._print("  No item_name provided for selling to shop.")

            elif action_name == "talk_to_self":
                self._print(f"  {self.character.name} mutters something unintelligible.")
                action_xp_reward = 1

            elif action_name == "check_shop_inventory":
                if self.shop: self.shop.display_inventory()
                else: self._print("Shop not available.")


            elif action_name == "check_player_inventory":
                if hasattr(self.character, 'display_character_info') and callable(self.character.display_character_info):
                    self.character.display_character_info()
                else: self._print("Cannot display character info.")

            elif action_name == "sleep_one_hour":
                self._print(f"  {self.character.name} rests for one hour.")
                hp_gained = self.character.heal_hp(1)
                self._print(f"  Gained {hp_gained} HP. Current HP: {self.character.hp}/{self.character.get_effective_max_hp()}")
                time_advanced_by_action_hours = 1 # This action consumes 1 hour

            elif action_name == "sleep_eight_hours":
                self._print(f"  {self.character.name} attempts a long rest...")
                food_available = action_details.get("food_available", True)
                drink_available = action_details.get("drink_available", True)
                rest_results = self.character.attempt_long_rest(food_available=food_available, drink_available=drink_available, hours_of_rest=8)
                self._print(f"  {rest_results.get('message', 'Rest attempt finished.')}")
                time_advanced_by_action_hours = 8 # Consumes 8 hours

            elif action_name == "explore_town":
                town_name_display = self.current_town.name if self.current_town else "the area"
                self._print(f"  {self.character.name} spends an hour exploring {town_name_display}.")
                if self.current_town:
                    self._print(f"    Properties: {', '.join(self.current_town.properties)}")
                    self._print(f"    Nearby Resources: {', '.join(self.current_town.nearby_resources)}")
                    crafters = [f"{c['name']} ({c['specialty']})" for c in self.current_town.unique_npc_crafters]
                    self._print(f"    Unique NPCs: {', '.join(crafters) if crafters else 'None'}")
                action_xp_reward = 5

            elif action_name == "talk_to_customer":
                self.action_talk_to_customer(action_details) # This method handles printing
                action_xp_reward = 2

            elif action_name == "research_market":
                town_name_display = self.current_town.name if self.current_town else "the local"
                self._print(f"  {self.character.name} spends an hour researching the market in {town_name_display}.")
                if self.current_town and self.current_town.market_demand_modifiers:
                    self._print("    Current market demands attention for:")
                    for item_name, modifier in self.current_town.market_demand_modifiers.items():
                        if modifier > 1.1: self._print(f"      - {item_name} (High Demand)")
                        elif modifier < 0.9: self._print(f"      - {item_name} (Low Demand)")
                else:
                    self._print("    No specific market demands noted at this time.")
                action_xp_reward = 5

            elif action_name == "travel_to_town":
                town_name = action_details.get("town_name")
                current_town_name = self.current_town.name if self.current_town else "Unknown"
                if town_name and town_name in self.towns_map:
                    if town_name == current_town_name:
                        self._print(f"  Already in {town_name}.")
                    else:
                        travel_time_hours = 3 # Example fixed travel time
                        self._print(f"  Traveling from {current_town_name} to {town_name}... (This will take {travel_time_hours} hours)")
                        self.current_town = self.towns_map[town_name]
                        if self.shop: # Ensure shop exists before updating its town
                             self.shop.update_town(self.current_town) # Update shop's current town reference
                             self._print(f"  Arrived in {self.current_town.name}. Shop is now operating here.")
                        else: # Should not happen if is_game_setup is True
                             self._print(f"  Arrived in {self.current_town.name}. (Shop not initialized - this is an issue!)")
                        time_advanced_by_action_hours = travel_time_hours
                        action_xp_reward = 15
                else:
                    self._print(f"  Invalid town name for travel: {town_name}. Available: {list(self.towns_map.keys())}")

            elif action_name == "debug_trigger_event":
                if self.event_manager and SAMPLE_EVENTS: # Ensure event_manager and SAMPLE_EVENTS exist
                    if SAMPLE_EVENTS : # Ensure not empty
                        event_to_trigger = random.choice(SAMPLE_EVENTS)
                        self._print(f"  DEBUG: Manually triggering event: {event_to_trigger.name}")
                        self.event_manager.resolve_event(event_to_trigger) # Assumes this prints details
                        self.daily_special_events.append(event_to_trigger.name)
                    else:
                        self._print("  DEBUG: No sample events defined to trigger.")
                else:
                    self._print("  DEBUG: No sample events to trigger or event manager not ready.")

            elif action_name == "wait":
                self._print(f"  {self.character.name} waits for an hour, observing the surroundings.")
                action_xp_reward = 1 # Minimal XP for passing time consciously

            else: # Unrecognized action
                self._print(f"  Action '{action_name}' is not recognized or implemented yet.")

            # Award XP if character is alive and action yielded XP
            if action_xp_reward > 0:
                self.character.award_xp(action_xp_reward)
                self.daily_xp_awarded_this_day += action_xp_reward

        # --- Post-action processing (Time advancement, EOD, Random Events, NPC Sales) ---

        # Determine how many hours to advance game time
        hours_to_advance = time_advanced_by_action_hours if time_advanced_by_action_hours > 0 else 1
        # If character died and action didn't specify time, ensure it's at least 1 hour
        if hasattr(self.character, 'is_dead') and self.character.is_dead and time_advanced_by_action_hours == 0 :
            hours_to_advance = 1

        # Store day before advancing time, to check if day changed due to this action
        day_before_advancing_time = self.time.current_day
        self.time.advance_hour(hours_to_advance) # GameTime's internal state is updated

        # EOD Check 2: Action's duration caused time to cross into a new day
        if self.time.current_day != day_before_advancing_time:
            # The day number has changed. We need to run EOD for 'day_before_advancing_time'.
            # self.tracking_day should ideally be 'day_before_advancing_time' at this point,
            # unless EOD Check 1 already ran for 'day_before_advancing_time' because the action started at 00:00.
            if self.tracking_day == day_before_advancing_time: # Ensure we only run EOD once for a given day
                 self._run_end_of_day_summary(self.tracking_day)
            # If tracking_day is already self.time.current_day, it means EOD Check 1 (action started at 00:00)
            # or a previous action already handled the EOD for day_before_advancing_time.

        # Further post-action events (random events, NPC sales) only if character is alive
        if hasattr(self.character, 'is_dead') and not self.character.is_dead:
            # Random Event Chance
            if self.event_manager and action_name not in ["debug_trigger_event"] and random.random() < self.base_event_chance:
                if SAMPLE_EVENTS: # Ensure SAMPLE_EVENTS is not empty
                    triggered_event_name = self.event_manager.trigger_random_event(SAMPLE_EVENTS)
                    if triggered_event_name: # If an event was actually triggered
                        self.daily_special_events.append(triggered_event_name)
                # else: # Optionally print if no sample events are available
                #     self._print("  (No sample events to randomly trigger.)")

            # NPC Shop Sales Simulation
            # Check if shop exists, has inventory, and action wasn't a direct shop interaction by player
            if self.shop and self.shop.inventory and action_name not in ["buy_from_own_shop", "sell_to_own_shop"]:
                if random.random() < 0.1: # 10% chance for an NPC to buy something
                    item_to_sell_to_npc = random.choice(self.shop.inventory) if self.shop.inventory else None # Defensive choice
                    if item_to_sell_to_npc: # Ensure an item was actually chosen
                        npc_offer_mult = random.uniform(0.8, 1.0) # NPCs offer 80-100% of base sale price
                        sale_price = self.shop.complete_sale_to_npc(item_to_sell_to_npc.name, npc_offer_percentage=npc_offer_mult)
                        if sale_price is not None and sale_price > 0: # If sale was successful
                            self._print(f"  [NPC Sale] {self.shop.name} sold {item_to_sell_to_npc.name} to an NPC for {sale_price}g.")
                            self.daily_items_sold_by_shop_to_npcs.append((item_to_sell_to_npc.name, sale_price))
                            self.daily_gold_earned_from_sales += sale_price
                            self._handle_customer_interaction(is_sale_or_purchase_by_player_shop=True) # A sale is an interaction
            else: # Generic customer interaction if no NPC sale and shop exists
                if self.shop : # Check if shop is initialized
                    self._handle_customer_interaction()
