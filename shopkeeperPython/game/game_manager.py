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
        self.towns_map = {town.name: town for town in self.towns} # For easy lookup by name

        self.current_town = town_เริ่มต้น

        # Shop initialization now uses the created character's name
        self.shop = Shop(name=f"{self.character.name}'s Emporium", owner_name=self.character.name, town=self.current_town)

        self.event_manager = EventManager(self.character)
        self.base_event_chance = 0.05
        self._reset_daily_trackers()


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
        if self.time.current_hour == 0 and self.tracking_day != self.time.current_day :

        current_time_str = self.time.get_time_string()
        self._print(f"\n[{current_time_str}] {self.character.name} (in {self.current_town.name}) performs action: {action_name}")
        action_xp_reward = 0
        if action_name == "craft":
            item_name = action_details.get("item_name")
            if item_name:
                crafted_item = self.shop.craft_item(item_name)

            if self.shop.inventory and random.random() < 0.3:
                item_to_sell = random.choice(self.shop.inventory)
                sale_price = self.shop.complete_sale_to_npc(item_to_sell.name)
                if sale_price > 0:

            action_xp_reward = 5
        elif action_name == "buy_from_own_shop":

        for i in range(8):
            self.perform_hourly_action("sleep_one_hour")

