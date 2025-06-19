import random
import json # Import json for save/load
from .time_system import GameTime
from .character import Character, JournalEntry # Import JournalEntry
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

RESOURCE_ITEM_DEFINITIONS = {
    "Dirty Water": {"description": "Murky water, might need cleaning.", "base_value": 0, "item_type": "component"},
    "Moldy Fruit": {"description": "Fruit that's seen better days.", "base_value": 0, "item_type": "component"},
    "Scrap Metal": {"description": "A piece of discarded metal.", "base_value": 1, "item_type": "component"},
    "Clean Water": {"description": "Potable water.", "base_value": 1, "item_type": "component"},
    "Sturdy Branch": {"description": "A solid tree branch.", "base_value": 1, "item_type": "component"},
    "Grain": {"description": "Handful of wild grain.", "base_value": 1, "item_type": "component"},
    "Rawhide": {"description": "Untreated animal hide.", "base_value": 2, "item_type": "component"},
    "Linen Scrap": {"description": "A small piece of linen cloth.", "base_value": 1, "item_type": "component"},
    "Small Twig": {"description": "A thin twig.", "base_value": 0, "item_type": "component"},
    "Wild Herb": {"description": "A common medicinal herb.", "base_value": 2, "item_type": "component"},
    "Stone Fragment": {"description": "A sharp piece of stone.", "base_value": 0, "item_type": "component"},
    "Bird Feather": {"description": "A bird feather.", "base_value": 1, "item_type": "component"},
    # New ingredients for advanced crafting
    "Iron Ingot": {"description": "A bar of refined iron.", "base_value": 10, "item_type": "component"},
    "Leather Straps": {"description": "Strips of treated leather.", "base_value": 5, "item_type": "component"},
    "Steel Ingot": {"description": "A bar of strong steel.", "base_value": 25, "item_type": "component"},
    "Oak Wood": {"description": "A sturdy piece of oak wood.", "base_value": 8, "item_type": "component"},
    "Concentrated Herbs": {"description": "A potent distillation of magical herbs.", "base_value": 15, "item_type": "component"},
    "Purified Water": {"description": "Magically purified water.", "base_value": 5, "item_type": "component"},
    "Crystal Vial": {"description": "A delicate crystal vial for potions.", "base_value": 10, "item_type": "component"},
    "Dragon's Blood Resin": {"description": "Hardened sap with magical properties.", "base_value": 20, "item_type": "component"},
    "Mountain Flower": {"description": "A rare flower found high in the mountains.", "base_value": 12, "item_type": "component"}
}

HEMLOCK_HERBS = {
   "Sunpetal": {"description": "A bright, sun-shaped flower that aids recovery.", "base_value": 5, "item_type": "herb", "quality": "Common", "price": 8},
   "Moonleaf": {"description": "A silvery leaf that glows faintly, used in calming draughts.", "base_value": 7, "item_type": "herb", "quality": "Common", "price": 12},
   "Bitterroot": {"description": "A pungent root known for its purifying qualities.", "base_value": 4, "item_type": "herb", "quality": "Common", "price": 6}
}

EXPLORATION_FINDS = [
    {"type": "gold", "amount": 5},
    {"type": "gold", "amount": 10},
    {"type": "item", "name": "Old Coin", "description": "A worn, unidentifiable coin.", "base_value": 1, "item_type": "trinket", "quality": "Common", "quantity": 1},
    {"type": "item", "name": "Linen Scrap", "description": "A small piece of linen cloth.", "base_value": 1, "item_type": "component", "quality": "Common", "quantity": 1},
    {"type": "item", "name": "Small Twig", "description": "A thin twig.", "base_value": 0, "item_type": "component", "quality": "Common", "quantity": 1},
    {"type": "item", "name": "Shiny Pebble", "description": "A smooth, oddly shiny pebble.", "base_value": 1, "item_type": "trinket", "quality": "Common", "quantity": 1},
    {"type": "item", "name": "Apple", "description": "A slightly bruised apple.", "base_value": 1, "item_type": "food", "quality": "Common", "quantity": 1, "is_consumable": True, "effects": {"healing": 1}}
]

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
            nearby_resources=["Dirty Water", "Moldy Fruit", "Wild Herb", "Small Twig", "Sturdy Branch", "Grain"],
            unique_npc_crafters=[{
                "name": "Old Man Hemlock",
                "specialty": "Herbalism",
                "services": ["Identifies Herbs"],
                "quests_available": [],
                "dialogue": ["The forest speaks to those who listen.", "These old bones have seen many seasons.", "Looking for herbs, are we?"]
            }],
            market_demand_modifiers={"Minor Healing Potion": 1.1, "Bread": 0.9, "Fish": 1.05},
            sub_locations=[
                {"name": "Village Shop", "description": "Your humble shop.", "actions": ["buy_from_own_shop", "sell_to_own_shop", "check_shop_inventory", "craft"]},
                {"name": "Village Square", "description": "The central gathering point of the village.", "actions": ["explore_town", "talk_to_villager", "research_market"]},
                {"name": "Old Man Hemlock's Hut", "description": "A small, smoky hut belonging to the local herbalist.", "actions": ["talk_to_hemlock", "buy_from_npc"]}
            ]
        )
        town_steel_flow = Town(
            name="Steel Flow City",
            properties=["Major mining hub", "Strong warrior tradition"],
            nearby_resources=["Scrap Metal", "Stone Fragment", "Dirty Water", "Sturdy Branch"],
            unique_npc_crafters=[{
                "name": "Borin Stonebeard",
                "specialty": "Blacksmithing",
                "services": ["Repairs Gear", "Sells Metal Ingots"],
                "quests_available": ["Clear Mine Pests"],
                "dialogue": ["The clang of the hammer is music to my ears.", "Need something sturdy, eh?", "Steel and sweat, that's the way!"]
            }],
            market_demand_modifiers={"Simple Dagger": 1.25, "Iron Sword": 1.3, "Minor Healing Potion": 1.15, "Stale Ale": 0.8},
            sub_locations=[
                {"name": "City Market", "description": "A bustling marketplace.", "actions": ["explore_town", "research_market", "visit_general_store_sfc"]},
                {"name": "The Rusty Pickaxe Tavern", "description": "A rowdy place favored by miners.", "actions": ["buy_drink_tavern", "gather_rumors_tavern"]},
                {"name": "Borin Stonebeard's Smithy", "description": "The workshop of the renowned blacksmith.", "actions": ["talk_to_borin", "repair_gear_borin"]}
            ]
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

    def add_journal_entry(self, action_type: str, summary: str, details: dict = None, outcome: str = None, timestamp: str = None):
        """Adds an entry to the character's journal."""
        if not self.character or not hasattr(self.character, 'journal'):
            self._print("DEBUG: Cannot add journal entry - character or journal not available.")
            return

        # Ensure timestamp is a datetime object
        if timestamp:
            if isinstance(timestamp, str):
                try:
                    entry_timestamp_dt = datetime.datetime.fromisoformat(timestamp)
                except ValueError:
                    self._print(f"  [Journal Error] Invalid timestamp format: {timestamp}. Using current time.")
                    entry_timestamp_dt = self.time.get_current_datetime()
            elif isinstance(timestamp, datetime.datetime): # Ensure datetime is imported
                 entry_timestamp_dt = timestamp
            else:
                self._print(f"  [Journal Error] Unexpected timestamp type: {type(timestamp)}. Using current time.")
                entry_timestamp_dt = self.time.get_current_datetime()
        else:
            entry_timestamp_dt = self.time.get_current_datetime()

        try:
            entry = JournalEntry(
                timestamp=entry_timestamp_dt,
                action_type=action_type,
                summary=summary,
                details=details if details is not None else {},
                outcome=outcome
            )
            self.character.journal.append(entry)
            # self._print(f"  [Journal Added] Type: {action_type}, Summary: {summary}") # Already printed by caller context usually
        except Exception as e:
            self._print(f"  [Journal Error] Failed to add entry for '{action_type}': {e}")


    def _handle_player_craft_item(self, action_details: dict) -> int:
        """Handles player-initiated crafting."""
        item_name_to_craft = action_details.get("item_name")
        if not item_name_to_craft:
            self._print("  No item_name provided for crafting.")
            return 0 # No XP

        if not self.shop or not hasattr(self.shop, 'BASIC_RECIPES'): # Ensure shop and recipes are available
            self._print("  Crafting recipes are not available at the moment.")
            return 0

        recipe = self.shop.BASIC_RECIPES.get(item_name_to_craft)
        if not recipe:
            self._print(f"  Recipe for '{item_name_to_craft}' not found.")
            return 0

        required_ingredients = recipe.get("ingredients", {})
        can_craft, missing_items = self.character.has_items(required_ingredients)

        if not can_craft:
            missing_str = ", ".join([f"{qty}x {name}" for name, qty in missing_items.items()])
            self._print(f"  Cannot craft {item_name_to_craft}. Missing ingredients: {missing_str}.")
            return 0

        # Consume Ingredients
        if not self.character.consume_items(required_ingredients):
            self._print(f"  Error consuming ingredients for {item_name_to_craft}. Crafting failed.")
            # Potentially log more details or handle inconsistent state if consume_items can partially fail
            return 0

        self._print(f"  Successfully consumed ingredients for {item_name_to_craft}.")

        # Create Item
        # Ensure all necessary attributes are pulled from the recipe or defaulted
        crafted_item = Item(
            name=item_name_to_craft,
            description=recipe.get("description", "A crafted item."),
            base_value=recipe.get("base_value", 0),
            item_type=recipe.get("item_type", "misc"),
            quality="Common", # Player crafting defaults to Common for now
            quantity=recipe.get("quantity_produced", 1),
            effects=recipe.get("effects", {}),
            is_consumable=recipe.get("is_consumable", False),
            is_magical=recipe.get("is_magical", False),
            is_attunement=recipe.get("is_attunement", False)
            # Add other relevant fields from Item class if they are in recipe
        )

        self.character.add_item_to_inventory(crafted_item)
        self._print(f"  {self.character.name} successfully crafted {crafted_item.quantity}x {crafted_item.name}.")
        self.daily_items_crafted.append(f"{crafted_item.quantity}x {crafted_item.name}")
        return 5 # XP for successful crafting

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

        # Determine starting town
        loaded_town_name = None
        town_source_message = "(defaulted)" # Assume default initially

        if hasattr(self.character, 'current_town_name') and self.character.current_town_name:
            loaded_town_name = self.character.current_town_name
            selected_starting_town = self.towns_map.get(loaded_town_name)
            if selected_starting_town:
                town_source_message = "(loaded)"
            else:
                self._print(f"Warning: Saved town '{loaded_town_name}' not found or invalid. Falling back to default.")
                loaded_town_name = None # Ensure we fall through to default logic

        if not loaded_town_name: # If no town loaded from character or loaded town was invalid
            default_town_name = "Starting Village"
            selected_starting_town = self.towns_map.get(default_town_name)
            if not selected_starting_town: # Critical fallback for default
                self._print(f"CRITICAL: Default starting town '{default_town_name}' not found in towns_map.")
                if self.towns:
                    self._print(f"Warning: Falling back to the first town in the list: {self.towns[0].name}")
                    selected_starting_town = self.towns[0]
                else:
                    self._print("CRITICAL: No towns available at all. Cannot set current_town for character.")
                    self.is_game_setup = False
                    return
            # town_source_message remains "(defaulted)"

        self.current_town = selected_starting_town
        self._print(f"Player character {self.character.name} starting in/continuing in: {self.current_town.name} {town_source_message}.")

        # Initialize Shop for the character
        self.shop = Shop(name=f"{self.character.name}'s Emporium", owner_name=self.character.name, town=self.current_town)
        self._print(f"Shop '{self.shop.name}' initialized/updated in {self.current_town.name} for owner {self.character.name}.")

        # Set default specialization if not loaded (Shop.from_dict handles this, but good to be explicit)
        if not hasattr(self.shop, 'specialization') or not self.shop.specialization:
            self.shop.set_specialization("General Store") # Explicitly set for new shops
        elif self.shop.specialization not in Shop.SPECIALIZATION_TYPES:
             self._print(f"Warning: Shop loaded with invalid specialization '{self.shop.specialization}'. Resetting to 'General Store'.")
             self.shop.set_specialization("General Store")


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
        self.event_manager = EventManager(self.character, self) # Pass GameManager instance (self)
        self._print(f"EventManager initialized/updated for character: {self.character.name}.")

        self._reset_daily_trackers() # Reset daily stats for the new character setup
        self._print("Daily trackers reset for the new character setup.")

        self.is_game_setup = True # Mark the game as successfully set up for this character
        self._print(f"--- Game world setup complete for {self.character.name}. is_game_setup: {self.is_game_setup} ---")

    def _handle_npc_dialogue(self, npc_name_to_find: str) -> int:
        if not self.current_town or not hasattr(self.current_town, 'unique_npc_crafters'):
            self._print(f"  No town information or NPC crafters defined for {self.current_town.name if self.current_town else 'current location'}.")
            return 0

        for npc in self.current_town.unique_npc_crafters:
            if npc.get('name') == npc_name_to_find:
                dialogue_options = npc.get('dialogue')
                if dialogue_options and isinstance(dialogue_options, list) and len(dialogue_options) > 0:
                    dialogue_line = random.choice(dialogue_options)
                    self._print(f"  {npc_name_to_find} says: \"{dialogue_line}\"")
                    # Journal entry is handled by the calling action in perform_hourly_action
                    return 1  # XP for successful dialogue
                else:
                    self._print(f"  {npc_name_to_find} has nothing to say right now.")
                    # Journal entry for "nothing to say" could be added here or in calling action
                    return 0

        self._print(f"  Could not find '{npc_name_to_find}' in {self.current_town.name}.")
        return 0

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

    def _handle_buy_from_npc(self, details: dict) -> int:
        """Handles the logic for player buying items from an NPC."""
        npc_name = details.get("npc_name")
        item_name_to_buy = details.get("item_name")

        try:
            quantity_to_buy = int(details.get("quantity", 0))
        except ValueError:
            self._print("  Invalid quantity. Please provide a number.")
            return 0 # No XP

        if not npc_name:
            self._print("  NPC name not specified for purchase.")
            return 0
        if not item_name_to_buy:
            self._print("  Item name not specified for purchase.")
            return 0
        if quantity_to_buy <= 0:
            self._print(f"  Please specify a valid quantity (more than 0) to buy {item_name_to_buy}.")
            return 0

        # Find the NPC in the current town
        target_npc_data = None
        if self.current_town and hasattr(self.current_town, 'unique_npc_crafters'):
            for npc_data in self.current_town.unique_npc_crafters:
                if npc_data.get('name') == npc_name:
                    target_npc_data = npc_data
                    break

        if not target_npc_data:
            self._print(f"  NPC '{npc_name}' not found in {self.current_town.name if self.current_town else 'this area'}.")
            return 0

        # --- NPC Specific Logic ---
        if npc_name == "Old Man Hemlock":
            if item_name_to_buy not in HEMLOCK_HERBS:
                self._print(f"  Old Man Hemlock doesn't sell '{item_name_to_buy}'. He has: {', '.join(HEMLOCK_HERBS.keys())}.")
                return 0

            herb_info = HEMLOCK_HERBS[item_name_to_buy]
            total_cost = herb_info["price"] * quantity_to_buy

            if self.character.gold < total_cost:
                self._print(f"  {self.character.name} doesn't have enough gold. (Needs {total_cost}g, Has {self.character.gold}g).")
                return 0

            self.character.gold -= total_cost
            # Ensure Item constructor can handle 'quantity'
            new_herb_item = Item(
                name=item_name_to_buy,
                description=herb_info["description"],
                base_value=herb_info["base_value"],
                item_type=herb_info["item_type"],
                quality=herb_info["quality"],
                quantity=quantity_to_buy # Pass quantity here
            )
            self.character.add_item_to_inventory(new_herb_item)
            outcome_msg = f"Bought {quantity_to_buy}x {item_name_to_buy} for {total_cost}g. Gold: {self.character.gold}."
            self._print(f"  {self.character.name} {outcome_msg}")
            self.add_journal_entry(
                action_type="Purchase (NPC)",
                summary=f"Bought {quantity_to_buy}x {item_name_to_buy} from {npc_name}",
                outcome=outcome_msg,
                details={"item": item_name_to_buy, "quantity": quantity_to_buy, "cost": total_cost, "npc": npc_name}
            )
            self.daily_gold_spent_on_purchases_by_player += total_cost
            return 1 # XP for successful purchase
        else:
            self._print(f"  Buying items from '{npc_name}' is not implemented yet.")
            self.add_journal_entry(
                action_type="Purchase (NPC)",
                summary=f"Attempted to buy from {npc_name}",
                outcome="Purchase not implemented for this NPC.",
                details={"npc": npc_name, "item": item_name_to_buy}
            )
            return 0

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
            self._print(f"  Overheard: {formatted_snippet}")

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
        self._print(f"  You approach a customer. They say: {formatted_snippet}")
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
        summary_details = {
            "gold_earned_sales": self.daily_gold_earned_from_sales,
            "gold_spent_player": self.daily_gold_spent_on_purchases_by_player,
            "gold_earned_player_selling": self.daily_gold_player_earned_selling_to_shop,
            "visitors": self.daily_visitors,
            "items_crafted": self.daily_items_crafted,
            "items_sold_shop_to_npcs": [name for name, price in self.daily_items_sold_by_shop_to_npcs],
            "items_player_bought": self.daily_items_player_bought_from_shop,
            "items_player_sold": self.daily_items_player_sold_to_shop,
            "special_events": self.daily_special_events,
            "customer_dialogue_snippets": self.daily_customer_dialogue_snippets
        }
        self._print(f"  Gold earned from sales: {summary_details['gold_earned_sales']}")
        self._print(f"  Gold spent by player (shop/NPCs): {summary_details['gold_spent_player']}")
        self._print(f"  Gold earned by player selling to shop: {summary_details['gold_earned_player_selling']}")
        self._print(f"  Visitors: {summary_details['visitors']}")
        self._print(f"  Items crafted: {', '.join(summary_details['items_crafted']) if summary_details['items_crafted'] else 'None'}")
        self._print(f"  Items sold to NPCs: {', '.join(summary_details['items_sold_shop_to_npcs']) if summary_details['items_sold_shop_to_npcs'] else 'None'}")
        self._print(f"  Items player bought: {', '.join(summary_details['items_player_bought']) if summary_details['items_player_bought'] else 'None'}")
        self._print(f"  Items player sold: {', '.join(summary_details['items_player_sold']) if summary_details['items_player_sold'] else 'None'}")
        self._print(f"  Special events: {', '.join(summary_details['special_events']) if summary_details['special_events'] else 'None'}")
        if summary_details['customer_dialogue_snippets']:
            self._print("  Overheard Customer Snippets (EOD):")
            for snippet in summary_details['customer_dialogue_snippets']:
                self._print(f"    - {snippet}")

        xp_committed_today = 0
        if self.character and hasattr(self.character, 'is_dead') and not self.character.is_dead :
            xp_committed_today = self.character.commit_pending_xp()
            self._print(f"  XP committed from pending (EOD): {xp_committed_today}")
        summary_details["xp_committed_eod"] = xp_committed_today

        self.add_journal_entry(
            action_type="Daily Summary",
            summary=f"End of Day {day_ended}.",
            details=summary_details,
            outcome=f"Total XP committed: {xp_committed_today}."
        )

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
                 # Logging player death here if not already logged by gain_exhaustion or similar
                 # This might lead to multiple "Player Death" logs if not careful.
                 # A flag self.character.death_logged_in_journal could prevent this.
                 # For now, let's assume death is logged once when it occurs.
                 # However, if an action is attempted *while* dead, it's worth noting.
                 self.add_journal_entry(action_type="Action Attempt (Dead)", summary=f"Attempted {action_name} while dead.", outcome="No action taken.")
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
            char_name_for_log = self.character.name if self.character else "Character"
            self._print(f"  {char_name_for_log} is dead and cannot perform actions.")
            # Check if a death journal entry has been made for this "session" or instance of being dead.
            # This is a simplified check. A more robust way would be a flag on the character.
            last_journal_entry = self.character.journal[-1] if self.character.journal else None
            if not (last_journal_entry and last_journal_entry.action_type == "Player Death" and last_journal_entry.summary.startswith(char_name_for_log)):
                self.add_journal_entry(
                    action_type="Player Death",
                    summary=f"{char_name_for_log} has died.",
                    outcome="Unable to perform actions.",
                    timestamp=self.time.get_time_string() # Use current time for this log
                )
            time_advanced_by_action_hours = 1 # Dead characters still pass time
        else:
            # --- Action Implementations (character is alive) ---
            if action_name == "set_shop_specialization":
                specialization_name = action_details.get("specialization_name")
                if specialization_name:
                    if self.shop:
                        self.shop.set_specialization(specialization_name) # Shop method handles validation and printing
                        action_xp_reward = 10 # XP for changing specialization
                    else:
                        self._print("  Cannot set specialization: Shop not initialized.")
                else:
                    self._print("  No specialization_name provided.")

            elif action_name == "upgrade_shop":
                if not self.shop:
                    self._print("  Shop is not initialized. Cannot upgrade.")
                elif self.shop.shop_level >= Shop.MAX_SHOP_LEVEL:
                    self._print(f"  {self.shop.name} is already at the maximum level (Level {Shop.MAX_SHOP_LEVEL}).")
                else:
                    current_level_config = Shop.SHOP_LEVEL_CONFIG.get(self.shop.shop_level)
                    if not current_level_config:
                         self._print(f"  Error: Configuration for current shop level {self.shop.shop_level} not found.")
                    else:
                        cost_to_upgrade = current_level_config["cost_to_upgrade"]
                        if self.character.gold < cost_to_upgrade:
                            self._print(f"  Not enough gold to upgrade {self.shop.name}. Needs {cost_to_upgrade}g, has {self.character.gold}g.")
                        else:
                            self.character.gold -= cost_to_upgrade
                            if self.shop.upgrade_shop(): # This method now prints success details
                                self._print(f"  {self.character.name} paid {cost_to_upgrade}g to upgrade the shop.")
                                action_xp_reward = 50 # Significant XP for upgrading shop
                            else:
                                # Shop.upgrade_shop() prints failure reasons (e.g. already max level, config issue)
                                # Refund gold if upgrade_shop itself failed for an unexpected reason after cost was deducted.
                                self.character.gold += cost_to_upgrade
                                self._print(f"  Shop upgrade failed for an unexpected reason. Gold refunded.")


            elif action_name == "craft":
                # Modified to use shop's crafting method
                item_name_to_craft = action_details.get("item_name")
                if not item_name_to_craft:
                    self._print("  No item_name provided for crafting.")
                elif not self.shop:
                    self._print("  Cannot craft: Shop not initialized.")
                else:
                    # The shop's craft_item method now handles ingredient checks from character inventory
                    # and adds the item to its own (shop's) inventory.
                    crafted_item_instance = self.shop.craft_item(item_name_to_craft, self.character)
                    if crafted_item_instance:
                        self._print(f"  {self.shop.name} successfully crafted {crafted_item_instance.quantity}x {crafted_item_instance.quality} {crafted_item_instance.name}.")
                        self.daily_items_crafted.append(f"{crafted_item_instance.quantity}x {crafted_item_instance.name} (by shop)")
                        action_xp_reward = 10 # Higher XP for shop crafting
                    else:
                        # shop.craft_item should print failure reasons (missing ingredients, wrong spec, etc.)
                        self._print(f"  {self.shop.name} failed to craft {item_name_to_craft}.")
                    self.add_journal_entry(action_type="Crafting (Shop)", summary=f"Attempted to craft {item_name_to_craft}", outcome="Failed", details={"item": item_name_to_craft, "reason": "See game log for details."}) # Assuming craft_item prints reason

            # Removed redundant 'craft' block that called _handle_player_craft_item directly.
            # All crafting should ideally go through the shop instance now.

            elif action_name == "buy_from_own_shop":
                item_name = action_details.get("item_name")
                quantity = int(action_details.get("quantity", 1))
                outcome_msg = ""
                if item_name and quantity > 0:
                    items_bought, total_spent = self.character.buy_item_from_shop(item_name, quantity, self.shop)
                    if items_bought:
                        for item_b in items_bought: # items_bought is a list of Item objects
                            self.daily_items_player_bought_from_shop.append(item_b.name)
                        self.daily_gold_spent_on_purchases_by_player += total_spent
                        self._handle_customer_interaction(is_sale_or_purchase_by_player_shop=True)
                        action_xp_reward = 2
                        outcome_msg = f"Bought {quantity}x {item_name} for {total_spent}g."
                    else: # Failed to buy
                        outcome_msg = f"Failed to buy {quantity}x {item_name}."
                else:
                    self._print("  Invalid item_name or quantity for buying from shop.")
                    outcome_msg = "Invalid item_name or quantity."
                self.add_journal_entry(action_type="Purchase (Player)", summary=f"Player bought from own shop", details={"item": item_name, "quantity": quantity}, outcome=outcome_msg)


            elif action_name == "sell_to_own_shop":
                item_name = action_details.get("item_name")
                outcome_msg = ""
                if item_name:
                    item_instance_to_sell = next((item for item in self.character.inventory if item.name == item_name), None)
                    if item_instance_to_sell:
                        price_paid = self.character.sell_item_to_shop(item_instance_to_sell, self.shop)
                        if price_paid > 0:
                            self.daily_items_player_sold_to_shop.append(item_name)
                            self.daily_gold_player_earned_selling_to_shop += price_paid
                            self._handle_customer_interaction(is_sale_or_purchase_by_player_shop=True)
                            action_xp_reward = 2
                            outcome_msg = f"Sold {item_name} for {price_paid}g."
                        else: # Failed to sell (e.g. shop won't buy)
                            outcome_msg = f"Failed to sell {item_name} (shop declined or error)."
                    else:
                        self._print(f"  Item '{item_name}' not found in {self.character.name}'s inventory.")
                        outcome_msg = f"Item '{item_name}' not found in inventory."
                else:
                    self._print("  No item_name provided for selling to shop.")
                    outcome_msg = "No item_name provided."
                self.add_journal_entry(action_type="Sale (Player)", summary=f"Player sold to own shop", details={"item": item_name}, outcome=outcome_msg)


            elif action_name == "talk_to_self":
                self._print(f"  {self.character.name} mutters something unintelligible.")
                self.add_journal_entry(action_type="Misc.", summary="Talked to self.", outcome="Muttered unintelligibly.")
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

                exploration_outcome_msg = "Found nothing of note."
                if random.random() < 0.20: # 20% chance to find something
                    found_what = random.choice(EXPLORATION_FINDS)
                    if found_what["type"] == "gold":
                        amount = found_what["amount"]
                        self.character.gold += amount
                        exploration_outcome_msg = f"Found {amount}g!"
                        self._print(f"  While exploring, {self.character.name} {exploration_outcome_msg}")
                    elif found_what["type"] == "item":
                        item_effects = found_what.get("effects", {})
                        item_is_consumable = found_what.get("is_consumable", False)
                        found_item_obj = Item(
                            name=found_what["name"],
                            description=found_what["description"],
                            base_value=found_what["base_value"],
                            item_type=found_what["item_type"],
                            quality=found_what["quality"],
                            quantity=found_what["quantity"],
                            effects=item_effects,
                            is_consumable=item_is_consumable
                        )
                        self.character.add_item_to_inventory(found_item_obj)
                        exploration_outcome_msg = f"Found a {found_item_obj.name}!"
                        self._print(f"  While exploring, {self.character.name} {exploration_outcome_msg}")
                else: # No specific find
                    self._print(f"  {exploration_outcome_msg}")

                self.add_journal_entry(action_type="Exploration", summary=f"Explored {town_name_display}", outcome=exploration_outcome_msg, details={"town": town_name_display})
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
                        travel_outcome = f"Arrived in {self.current_town.name}."
                        if self.shop: # Ensure shop exists before updating its town
                            self.shop.update_town(self.current_town) # Update shop's current town reference
                            self._print(f"  Arrived in {self.current_town.name}. Shop '{self.shop.name}' (Specialization: {self.shop.specialization}) is now operating here.")
                        else: # Should not happen if is_game_setup is True
                            self._print(f"  Arrived in {self.current_town.name}. (Shop not initialized - this is an issue!)")
                        time_advanced_by_action_hours = travel_time_hours
                        action_xp_reward = 15
                        self.add_journal_entry(action_type="Travel", summary=f"Traveled from {current_town_name} to {town_name}", outcome=travel_outcome, details={"from_town": current_town_name, "to_town": town_name, "duration_hours": travel_time_hours})
                else:
                    self._print(f"  Invalid town name for travel: {town_name}. Available: {list(self.towns_map.keys())}")
                    self.add_journal_entry(action_type="Travel", summary=f"Attempted travel to {town_name}", outcome="Invalid town name.", details={"target_town": town_name})


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

            elif action_name == "gather_resources":
                if not self.current_town or not self.current_town.nearby_resources:
                    self._print("  No known resources to gather in this area.")
                else:
                    resource_name = random.choice(self.current_town.nearby_resources)
                    gathered_quantity = random.randint(1, 3)

                    details = RESOURCE_ITEM_DEFINITIONS.get(resource_name)
                    gathering_outcome = ""
                    if details:
                        new_item = Item(
                            name=resource_name,
                            description=details["description"],
                            base_value=details["base_value"],
                            item_type=details["item_type"],
                            quality="Common", # Gathered resources are typically common
                            quantity=gathered_quantity
                        )
                        self.character.add_item_to_inventory(new_item)
                        gathering_outcome = f"Found {new_item.quantity}x {new_item.name}."
                        self._print(f"  {self.character.name} gathered {new_item.quantity}x {new_item.name}.")
                        action_xp_reward = 3
                    else:
                        gathering_outcome = f"Could not find definition for resource: {resource_name}"
                        self._print(f"  {gathering_outcome}")
                    self.add_journal_entry(action_type="Gathering", summary=f"Gathered resources in {self.current_town.name if self.current_town else 'unknown area'}", outcome=gathering_outcome, details={"resource": resource_name, "quantity": gathered_quantity})

            # --- New Placeholder Actions from Sub-locations ---
            elif action_name == "talk_to_villager":
                dialogue_options = [
                    "Nice weather we're having, eh?", "Watch out for the goblins if you're heading east.",
                    "Welcome to our village!", "Hmm? Oh, just admiring the clouds.", "Need something?"
                ]
                if self.current_town:
                    if self.current_town.name == "Steel Flow City":
                        dialogue_options.extend(["This city never sleeps!", "Heard Borin's busy."])
                    elif self.current_town.name == "Starting Village":
                        dialogue_options.extend(["Hemlock knows the woods.", "Crops are good this year."])

                chosen_dialogue = random.choice(dialogue_options)
                self._print(f"  You chat with a villager. They say: \"{chosen_dialogue}\"")
                self.add_journal_entry(action_type="Dialogue", summary="Spoke with Villager", outcome=f"Villager said: '{chosen_dialogue}'", details={"npc_type": "Generic Villager", "town": self.current_town.name if self.current_town else "Unknown"})
                action_xp_reward = 1

            elif action_name == "talk_to_hemlock":
                original_xp = self.character.xp + self.character.pending_xp # Store before _handle_npc_dialogue
                action_xp_reward = self._handle_npc_dialogue("Old Man Hemlock")
                # Find what Hemlock said (this is tricky as _handle_npc_dialogue prints directly)
                # For now, we'll use a generic outcome message for the journal. A better way would be for _handle_npc_dialogue to return the line.
                dialogue_line_for_journal = "Old Man Hemlock responded." # Placeholder
                if self.character.xp + self.character.pending_xp > original_xp or action_xp_reward > 0 : # Implies successful interaction from XP gain
                     # This is a guess, ideally _handle_npc_dialogue returns the actual line.
                     if self.current_town and self.current_town.unique_npc_crafters:
                         hemlock_data = next((n for n in self.current_town.unique_npc_crafters if n['name'] == "Old Man Hemlock"), None)
                         if hemlock_data and hemlock_data.get('dialogue'):
                             # This doesn't guarantee it's the *exact* line shown, but it's a plausible one.
                             dialogue_line_for_journal = f"Hemlock said: '{random.choice(hemlock_data.get('dialogue'))}' (actual line may vary)"
                         else:
                             dialogue_line_for_journal = "Old Man Hemlock spoke."
                else: # Interaction might have failed or no dialogue options
                    dialogue_line_for_journal = "Old Man Hemlock had little to say or interaction failed."

                self.add_journal_entry(action_type="Dialogue", summary="Spoke with Old Man Hemlock", outcome=dialogue_line_for_journal, details={"npc_name": "Old Man Hemlock"})

            elif action_name == "buy_from_npc": # Journal entry for this is now inside _handle_buy_from_npc
                action_xp_reward = self._handle_buy_from_npc(action_details)

            elif action_name == "talk_to_borin":
                original_xp_borin = self.character.xp + self.character.pending_xp
                action_xp_reward = self._handle_npc_dialogue("Borin Stonebeard")
                dialogue_line_for_journal_borin = "Borin Stonebeard responded." # Placeholder
                if self.character.xp + self.character.pending_xp > original_xp_borin or action_xp_reward > 0:
                     if self.current_town and self.current_town.unique_npc_crafters:
                         borin_data = next((n for n in self.current_town.unique_npc_crafters if n['name'] == "Borin Stonebeard"), None)
                         if borin_data and borin_data.get('dialogue'):
                             dialogue_line_for_journal_borin = f"Borin said: '{random.choice(borin_data.get('dialogue'))}' (actual line may vary)"
                         else:
                            dialogue_line_for_journal_borin = "Borin Stonebeard spoke."
                else:
                    dialogue_line_for_journal_borin = "Borin Stonebeard had little to say or interaction failed."
                self.add_journal_entry(action_type="Dialogue", summary="Spoke with Borin Stonebeard", outcome=dialogue_line_for_journal_borin, details={"npc_name": "Borin Stonebeard"})

            # --- Placeholder actions that don't have specific journal entries yet, general one will be added ---
            elif action_name == "visit_general_store_sfc":
                self._print(f"  Action '{action_name}' at '{self.current_town.name}' (sub-location specific) - not fully implemented yet. You enter the general store in Steel Flow City.")
                action_xp_reward = 1
            elif action_name == "buy_drink_tavern":
                self._print(f"  Action '{action_name}' at '{self.current_town.name}' (sub-location specific) - not fully implemented yet. You order a drink at The Rusty Pickaxe.")
                action_xp_reward = 1
            elif action_name == "gather_rumors_tavern":
                self._print(f"  Action '{action_name}' at '{self.current_town.name}' (sub-location specific) - not fully implemented yet. You listen for rumors in the tavern.")
                action_xp_reward = 3
            elif action_name == "repair_gear_borin":
                self._print(f"  Action '{action_name}' at '{self.current_town.name}' (sub-location specific) - not fully implemented yet. You ask Borin about repairs.")
                action_xp_reward = 1
            # --- End New Placeholder Actions ---

            else: # Unrecognized action
                self._print(f"  Action '{action_name}' is not recognized or implemented yet.")
                self.add_journal_entry(action_type="Unknown Action", summary=f"Attempted action: {action_name}", outcome="Action not recognized.")

            # Award XP if character is alive and action yielded XP
            if action_xp_reward > 0:
                # Ensure character exists and has award_xp method
                if self.character and hasattr(self.character, 'award_xp'):
                    self.character.award_xp(action_xp_reward)
                    self.daily_xp_awarded_this_day += action_xp_reward
                elif self.character:
                    self._print(f"Warning: Character {self.character.name} has no award_xp method.")
                # If self.character is None, this block shouldn't be reached due to earlier checks.


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
            if self.shop and self.shop.inventory and action_name not in ["buy_from_own_shop", "sell_to_own_shop", "buy_from_npc"]:
                base_npc_buy_chance = 0.1
                # Adjust buy chance based on reputation, capped at 0.3 (e.g.)
                npc_buy_chance = min(base_npc_buy_chance + (self.shop.reputation * 0.001), 0.3)

                if random.random() < npc_buy_chance:
                    item_to_sell_to_npc = random.choice(self.shop.inventory) if self.shop.inventory else None # Defensive choice
                    if item_to_sell_to_npc: # Ensure an item was actually chosen
                        npc_offer_mult = random.uniform(0.8, 1.0) # NPCs offer 80-100% of base sale price (before shop reputation adjustment in complete_sale_to_npc)
                        sale_price = self.shop.complete_sale_to_npc(item_to_sell_to_npc.name, npc_offer_percentage=npc_offer_mult)
                        if sale_price is not None and sale_price > 0: # If sale was successful
                            self._print(f"  [NPC Sale] {self.shop.name} sold {item_to_sell_to_npc.name} to an NPC for {sale_price}g.")
                            self.daily_items_sold_by_shop_to_npcs.append((item_to_sell_to_npc.name, sale_price))
                            self.daily_gold_earned_from_sales += sale_price
                            self._handle_customer_interaction(is_sale_or_purchase_by_player_shop=True) # A sale is an interaction
            else: # Generic customer interaction if no NPC sale and shop exists
                if self.shop and action_name not in ["buy_from_own_shop", "sell_to_own_shop", "buy_from_npc"]: # Check if shop is initialized and not a shop action
                    self._handle_customer_interaction()
