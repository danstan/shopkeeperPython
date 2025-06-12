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
    def __init__(self, player_character: Character):
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
        self.towns_map = {town.name: town for town in self.towns} # For easy lookup by name

        self.current_town = town_เริ่มต้น
        self.shop = Shop(name=f"{player_character.name}'s Emporium", owner_name=player_character.name, town=self.current_town)

        self.event_manager = EventManager(self.character)
        self.base_event_chance = 0.05
        self._reset_daily_trackers()
        print(f"GameManager initialized. {player_character.name}'s shop established in {self.current_town.name}.")

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
        # print(f"[{self.time.get_time_string()}] Daily trackers have been reset for Day {self.tracking_day}.") # Less verbose for save/load

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
        if self.time.current_hour == 0 and self.tracking_day != self.time.current_day :
             pass
        current_time_str = self.time.get_time_string()
        print(f"\n[{current_time_str}] {self.character.name} (in {self.current_town.name}) performs action: {action_name}")
        action_xp_reward = 0
        if action_name == "craft":
            item_name = action_details.get("item_name")
            if item_name:
                crafted_item = self.shop.craft_item(item_name)
                if crafted_item: self.daily_items_crafted.append(crafted_item.name)
            else: print("  Crafting action chosen, but no item_name specified.")
        elif action_name == "rest_short": self.character.take_short_rest(action_details.get("dice_to_spend", 1))
        elif action_name == "sleep_one_hour": print(f"  {self.character.name} sleeps for an hour...")
        elif action_name == "talk_to_customer":
            print(f"  {self.character.name} at {self.shop.name} attending to customers.")
            self._handle_customer_interaction(False)
            if self.shop.inventory and random.random() < 0.3:
                item_to_sell = random.choice(self.shop.inventory)
                sale_price = self.shop.complete_sale_to_npc(item_to_sell.name)
                if sale_price > 0:
                    self.daily_items_sold_by_shop_to_npcs.append(item_to_sell.name); self.daily_gold_earned_from_sales += sale_price
                    print(f"  DEBUG: daily_gold_earned_from_sales: {self.daily_gold_earned_from_sales} (+{sale_price}g)")
                    self._handle_customer_interaction(True)
        elif action_name == "research_market":
            print(f"  Researching market in {self.current_town.name}..."); print(f"    Demand: {self.current_town.market_demand_modifiers}"); print(f"    Resources: {self.current_town.nearby_resources}")
            action_xp_reward = 5
        elif action_name == "buy_from_own_shop":
            item_name = action_details.get("item_name")
            if item_name and next((i for i in self.shop.inventory if i.name == item_name), None):
                bought_items, cost = self.character.buy_item_from_shop(item_name, 1, self.shop)
                if bought_items: self.daily_items_player_bought_from_shop.append(bought_items[0].name); self.daily_gold_spent_on_purchases_by_player += cost; self._handle_customer_interaction(True)
            elif item_name: print(f"  {self.shop.name} doesn't have {item_name}.")
            else: print("  'buy_from_own_shop' needs item_name.")
        elif action_name == "chat": self.send_chat_message(action_details.get("recipient","all"), action_details.get("message","...")); self._handle_customer_interaction()
        elif action_name == "emote": self.use_emote(action_details.get("emote","waves")); self._handle_customer_interaction()
        elif action_name == "send_mail": self.send_ingame_mail(action_details.get("recipient","Friend"), action_details.get("subject","Hi"), action_details.get("body","..."))
        else: print(f"  Action '{action_name}' not implemented.")
        if action_xp_reward > 0: self.character.award_xp(action_xp_reward)
        if random.random() < self.base_event_chance:
            print(f"![EVENT CHANCE MET AFTER {action_name}]!");
            if SAMPLE_EVENTS: triggered_event_name = self.event_manager.trigger_random_event(SAMPLE_EVENTS);
            if triggered_event_name: self.daily_special_events.append(triggered_event_name)
        days_advanced, _ = self.time.advance_hour(1)
        if days_advanced > 0: self.generate_end_of_day_recap(day_number=current_day_before_action)
        return {"status": "completed", "new_time": self.time.get_time_string()}

    def start_long_rest(self, food_available: bool = True, drink_available: bool = True):
        start_time_str = self.time.get_time_string(); print(f"\n[{start_time_str}] {self.character.name} starts long rest (8h) in {self.current_town.name}.")
        for i in range(8):
            self.perform_hourly_action("sleep_one_hour")
            if self.character.exhaustion_level >=6: print(f"  {self.character.name} perished during rest."); return
        print(f"  Long rest period concludes at {self.time.get_time_string()}.")
        if self.character.exhaustion_level < 6:
            res = self.character.attempt_long_rest(food_available, drink_available, 8, 0.1)
            print(f"  Long rest benefits: {res.get('message', 'No message.')}")

    def generate_end_of_day_recap(self, day_number: int):
        if day_number != self.tracking_day: print(f"Warning: Recap for Day {day_number}, but tracking Day {self.tracking_day}.")
        print(f"\n--- End of Day Recap: Day {day_number} ---"); committed_xp = self.character.commit_pending_xp(); self.daily_xp_awarded_this_day = committed_xp
        print(f"Gold Earned (Shop Sales to NPCs): {self.daily_gold_earned_from_sales} G")
        print(f"Gold Spent (Player Buying from Own Shop): {self.daily_gold_spent_on_purchases_by_player} G")
        print(f"Gold Earned (Player Selling Items): {self.daily_gold_player_earned_selling_to_shop} G")
        print(f"Shop Visitors: {self.daily_visitors}")
        print(f"Experience Points Awarded: {self.daily_xp_awarded_this_day} XP")
        for category, items in [("Crafted",self.daily_items_crafted), ("Sold by Shop (NPCs)",self.daily_items_sold_by_shop_to_npcs), ("Player Bought",self.daily_items_player_bought_from_shop), ("Player Sold",self.daily_items_player_sold_to_shop)]:
            print(f"\nItems {category} Today:"); [print(f"- {name}") for name in items] if items else print("- None")
        print("\nSpecial Events Today:"); [print(f"- {summary}") for summary in self.daily_special_events] if self.daily_special_events else print("- None")
        print("\nOverheard Customer Dialogue:"); [print(f"- \"{snip}\"") for snip in self.daily_customer_dialogue_snippets] if self.daily_customer_dialogue_snippets else print("- None")
        print("-----------------------------------------"); self._reset_daily_trackers()

    def save_game(self, filename="savegame.json"):
        save_data = {
            "character": self.character.to_dict(),
            "shop": self.shop.to_dict(),
            "gametime": self.time.to_dict(),
            "current_town_name": self.current_town.name,
            # Daily trackers are not saved; they are reset on load.
        }
        try:
            with open(filename, 'w') as f:
                json.dump(save_data, f, indent=4)
            print(f"Game saved to {filename}")
        except IOError as e:
            print(f"Error saving game to {filename}: {e}")

    def load_game(self, filename="savegame.json"):
        try:
            with open(filename, 'r') as f:
                loaded_data = json.load(f)

            self.time = GameTime.from_dict(loaded_data["gametime"])

            town_name = loaded_data["current_town_name"]
            self.current_town = self.towns_map.get(town_name)
            if not self.current_town:
                print(f"Error: Town '{town_name}' not found from save. Defaulting to first town.")
                self.current_town = self.towns[0] if self.towns else None # Or handle error more gracefully

            self.character = Character.from_dict(loaded_data["character"])
            if hasattr(self.character, 'reapply_attuned_item_effects'): # Ensure method exists
                self.character.reapply_attuned_item_effects()

            if self.current_town: # Only load shop if town is valid
                self.shop = Shop.from_dict(loaded_data["shop"], self.current_town)
            else:
                print("Error: Cannot load shop as current_town is invalid.")
                # self.shop = None # Or some default state for shop
                # For now, this might lead to issues if shop is accessed before a town is set.

            # Re-link event manager and other necessary references
            self.event_manager.character = self.character
            # If shop owner name is not part of shop save, or needs re-linking:
            # self.shop.owner_name = self.character.name

            self._reset_daily_trackers() # Reset trackers for the new loaded day
            print(f"Game loaded from {filename}. Current time: {self.time.get_time_string()}")
            return True
        except FileNotFoundError:
            print(f"Save file {filename} not found.")
            return False
        except Exception as e:
            print(f"Error loading game from {filename}: {e}")
            return False

if __name__ == "__main__":
    print("--- GameManager Test: Save/Load & Daily Recap ---")
    player = Character(name="SaveLoad Player")
    player.roll_stats()
    gm = GameManager(player_character=player)
    gm.base_event_chance = 0.5 # High chance for testing events in save

    print("\n--- Initial State ---")
    gm.character.display_character_info()
    gm.shop.display_inventory()

    # Simulate some actions
    gm.perform_hourly_action("craft", {"item_name": "Minor Healing Potion"})
    gm.perform_hourly_action("talk_to_customer")
    gm.character.award_xp(20) # Award some pending XP
    gm.perform_hourly_action("research_market")

    # Save the game
    SAVE_FILENAME = "test_save.json"
    gm.save_game(SAVE_FILENAME)

    # Modify game state after saving to ensure load restores previous state
    gm.time.advance_hour(5)
    gm.character.award_xp(1000)
    gm.character.gold += 5000
    original_char_name_before_load = gm.character.name
    # If we were to create a new GameManager, it would reset towns.
    # For this test, we are loading into the *same* GameManager instance,
    # so self.towns and self.towns_map are preserved.

    print("\n--- Loading Game ---")
    load_successful = gm.load_game(SAVE_FILENAME)

    if load_successful:
        print("\n--- State After Loading ---")
        assert gm.character.name == original_char_name_before_load # Name should persist
        gm.character.display_character_info() # Should show XP before the 1000, gold before 5000
        gm.shop.display_inventory()
        print(f"Game time after load: {gm.time.get_time_string()}")

        # Verify a few things that should have been restored
        # Example: Check if pending XP was restored correctly (should be 20+5 = 25 from before save)
        # After load, daily trackers are reset, so pending_xp is not directly in a daily tracker,
        # but it's part of the character's loaded state.
        print(f"Character pending XP after load: {gm.character.pending_xp}")
        # This test relies on the specific XP awarded before save.
        # Initial research_market (5) + event (if any) + award_xp(20)
        # The event manager's XP award also goes to pending_xp. Let's assume one event gave 10xp. So 5+10+20 = 35
        # Check the log from the save portion to confirm actual pending XP.

        # Perform an action to see if game continues
        gm.perform_hourly_action("talk_to_customer")
        # This should trigger recap for the loaded day if it crosses midnight.

    print("\n--- GameManager Save/Load Test Complete ---")
