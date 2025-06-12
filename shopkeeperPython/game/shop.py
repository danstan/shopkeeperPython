# Import Character for type hinting only to avoid circular dependency at runtime
from typing import TYPE_CHECKING, Tuple
if TYPE_CHECKING:
    from .character import Character
    # from .town import Town # Town for type hinting - already imported below

from .item import Item, QUALITY_TIERS, QUALITY_VALUE_MULTIPLIERS
from .town import Town


class Shop:
    """
    Represents a shop in the Shopkeeper Python game.
    """
    BASIC_RECIPES = {
        "Stale Ale": {"base_value": 1, "type": "food", "description": "Barely drinkable ale.", "crafting_difficulty": 1, "effects": {"stamina_recovery": 1}},
        "Simple Dagger": {"base_value": 5, "type": "weapon", "description": "A crude but functional dagger.", "crafting_difficulty": 5, "effects": {"damage": "1d4"}},
        "Minor Healing Potion": {"base_value": 10, "type": "potion", "description": "Restores a small amount of health.", "effects": {"healing": 5}, "crafting_difficulty": 3}
    }

    QUALITY_THRESHOLDS = [
        (0, "Common"), (6, "Uncommon"), (16, "Rare"),
        (31, "Very Rare"), (51, "Legendary"), (101, "Mythical")
    ]

    def __init__(self, name: str, owner_name: str, town: Town, initial_gold: int = 500):
        self.name = name
        self.owner_name = owner_name
        self.town = town
        self.inventory = []
        self.gold = initial_gold
        self.specialization = "General"
        self.crafting_experience = {}
        self.shop_level = 1
        self.markup_percentage = 1.2 # Default markup (e.g., 20% over value for player)
        self.buyback_percentage = 0.5 # Default buyback (e.g., 50% of value for player)

    def __repr__(self):
        return (f"Shop(name='{self.name}', owner='{self.owner_name}', town='{self.town.name if self.town else 'None'}', "
                f"gold={self.gold}, specialization='{self.specialization}', level={self.shop_level})")

    def update_town(self, new_town: 'Town'):
        """Updates the shop's associated town."""
        self.town = new_town
        print(f"Shop '{self.name}' has updated its town to {new_town.name}.")

    def add_item_to_inventory(self, item: Item):
        self.inventory.append(item)

    def remove_item_from_inventory(self, item_name: str, specific_item_to_remove: Item = None) -> Item | None:
        item_to_remove = None
        if specific_item_to_remove and specific_item_to_remove in self.inventory:
            item_to_remove = specific_item_to_remove
            self.inventory.remove(specific_item_to_remove)
        else:
            for item in self.inventory:
                if item.name == item_name:
                    item_to_remove = item
                    self.inventory.remove(item)
                    break
        if not item_to_remove:
            pass
        return item_to_remove

    def can_craft(self, item_name: str, character_skills=None):
        return item_name in self.BASIC_RECIPES

    def _determine_quality(self, item_name: str) -> str:
        craft_count = self.crafting_experience.get(item_name, 0)
        determined_quality = self.QUALITY_THRESHOLDS[0][1]
        for threshold, quality in self.QUALITY_THRESHOLDS:
            if craft_count >= threshold:
                determined_quality = quality
            else:
                break
        return determined_quality

    def craft_item(self, item_name: str) -> Item | None:
        if not self.can_craft(item_name):
            # print(f"Cannot craft {item_name}. Recipe unknown or prerequisites not met.") # GameManager usually prints this
            return None
        recipe = self.BASIC_RECIPES[item_name]
        self.crafting_experience[item_name] = self.crafting_experience.get(item_name, 0) + 1
        quality = self._determine_quality(item_name)
        crafted_item = Item(
            name=item_name,
            description=recipe.get("description", "A crafted item."),
            base_value=recipe["base_value"],
            item_type=recipe["type"],
            quality=quality,
            effects=recipe.get("effects", {}),
            is_magical=recipe.get("is_magical", recipe["type"] in ["potion", "scroll", "weapon", "armor", "ring", "amulet"]),
            is_attunement=recipe.get("is_attunement", False),
            is_consumable=recipe.get("is_consumable", recipe["type"] in ["potion", "food", "scroll"])
        )
        self.add_item_to_inventory(crafted_item)
        # print(f"Crafted {crafted_item.quality} {item_name}. Experience for {item_name}: {self.crafting_experience[item_name]}.") # GameManager can print success
        return crafted_item

    def stock_item(self, item: Item):
        self.add_item_to_inventory(item)

    def complete_sale_to_npc(self, item_name: str, quality_to_sell: str = None, npc_offer_percentage: float = 1.0) -> int: # Returns price or 0
        item_instance_to_sell = None
        for item_in_stock in self.inventory:
            if item_in_stock.name == item_name:
                if quality_to_sell is None or item_in_stock.quality == quality_to_sell:
                    item_instance_to_sell = item_in_stock
                    break
        if item_instance_to_sell:
            # Use calculate_sale_price for consistency, assuming npc_offer_percentage is a negotiation result on top of base sale price
            base_selling_price = self.calculate_sale_price(item_instance_to_sell)
            final_selling_price = int(base_selling_price * npc_offer_percentage)

            self.gold += final_selling_price
            self.remove_item_from_inventory(item_instance_to_sell.name, specific_item_to_remove=item_instance_to_sell)

        else:
            # print(f"Item '{item_name}' (Quality: {quality_to_sell if quality_to_sell else 'any'}) not found in inventory for sale to NPC.")
            return 0

    def calculate_sale_price(self, item_or_item_name: (Item | str)) -> int:
        """Calculates the sale price of an item, considering town demand and shop markup."""
        item_instance = None
        if isinstance(item_or_item_name, str):
            for item_in_stock in self.inventory: # Search in current inventory
                if item_in_stock.name == item_or_item_name:
                    item_instance = item_in_stock
                    break
            if not item_instance: # If not in inventory, create a temporary item to get its base value
                 # This part is tricky if recipes are complex. Assuming base_value is known or simple items.
                 # For a robust solution, item details (like base_value) should be accessible globally or via Item class static methods.
                 # Let's assume we can get a temporary Item instance or its base_value for calculation.
                 # This path is less ideal. Best if an Item object is passed.
                if item_or_item_name in self.BASIC_RECIPES: # Fallback for known craftable items
                    item_instance = Item(name=item_or_item_name, base_value=self.BASIC_RECIPES[item_or_item_name]['base_value'], item_type="unknown")
                else:
                    # print(f"Warning: Cannot calculate price for unknown item name '{item_or_item_name}' not in inventory without its base value.")
                    return 0 # Or handle error appropriately
        elif isinstance(item_or_item_name, Item):
            item_instance = item_or_item_name

        if not item_instance:
            # print(f"Error: Could not determine item for price calculation: {item_or_item_name}")
            return 0

        town_modifier = 1.0
        if self.town and hasattr(self.town, 'get_item_price_modifier'): # Check if town exists and has the method
            town_modifier = self.town.get_item_price_modifier(item_instance.name)
        elif self.town and hasattr(self.town, 'market_demand_modifiers'): # Fallback to direct dict access
             town_modifier = self.town.market_demand_modifiers.get(item_instance.name, 1.0)


        # Price for player buying from shop (Shop sells high)
        price = int(item_instance.value * town_modifier * self.markup_percentage) # Changed get_value() to .value
        return price

    def sell_item_to_character(self, item_name: str, character_wanting_to_buy: 'Character') -> Tuple[Item | None, int]:
        item_instance_for_sale = None
        for item_in_stock in self.inventory:
            if item_in_stock.name == item_name:
                item_instance_for_sale = item_in_stock
                break
        if not item_instance_for_sale:
            print(f"SHOP: {self.name} does not have '{item_name}' in stock.")
            return None, 0

        price_to_character = self.calculate_sale_price(item_instance_for_sale)

        if character_wanting_to_buy.gold < price_to_character:
            print(f"SHOP: {character_wanting_to_buy.name} cannot afford {item_name} (Cost: {price_to_character}, Has: {character_wanting_to_buy.gold}).")
            return None, 0

        character_wanting_to_buy.gold -= price_to_character
        self.gold += price_to_character

        removed_item = self.remove_item_from_inventory(item_name, specific_item_to_remove=item_instance_for_sale)
        if removed_item:
             print(f"SHOP: {self.name} sold {removed_item.name} to {character_wanting_to_buy.name} for {price_to_character} gold.")
             return removed_item, price_to_character
        else:
            print(f"SHOP: Error - {item_name} was found but could not be removed from shop inventory.")
            character_wanting_to_buy.gold += price_to_character
            self.gold -= price_to_character
            return None, 0

    def buy_item_from_character(self, item_to_buy: Item, character_selling: 'Character') -> int:
        # Calculate price shop pays (Shop buys low)
        town_modifier = 1.0
        if self.town and hasattr(self.town, 'get_item_price_modifier'):
            town_modifier = self.town.get_item_price_modifier(item_to_buy.name)
        elif self.town and hasattr(self.town, 'market_demand_modifiers'):
             town_modifier = self.town.market_demand_modifiers.get(item_to_buy.name, 1.0)

        price_paid_by_shop = int(item_to_buy.value * town_modifier * self.buyback_percentage) # Changed get_value() to .value

        if self.gold < price_paid_by_shop:
            print(f"SHOP: {self.name} cannot afford to buy {item_to_buy.name} (Offered: {price_paid_by_shop}, Shop Gold: {self.gold}).")
            return 0

        self.add_item_to_inventory(item_to_buy)
        self.gold -= price_paid_by_shop
        character_selling.gold += price_paid_by_shop

        print(f"SHOP: {self.name} bought {item_to_buy.name} from {character_selling.name} for {price_paid_by_shop} gold.")
        return price_paid_by_shop

    def set_specialization(self, specialization_type: str):
        self.specialization = specialization_type
        print(f"Shop specialization set to: {self.specialization}")

    def display_inventory(self):
        if not self.inventory:
            print(f"{self.name}'s inventory is empty.")
            return
        print(f"\n--- {self.name}'s Inventory (in {self.town.name if self.town else 'N/A'}) ---")
        for item in self.inventory:
            print(f"- {item}")
        print("---------------------------")

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "owner_name": self.owner_name,
            "town_name": self.town.name if self.town else None, # Save town name
            "inventory": [item.to_dict() for item in self.inventory],
            "gold": self.gold,
            "specialization": self.specialization,
            "crafting_experience": self.crafting_experience.copy(),
            "shop_level": self.shop_level,
            "markup_percentage": self.markup_percentage,
            "buyback_percentage": self.buyback_percentage,
        }

    @classmethod
    def from_dict(cls, data: dict, town_object: Town) -> 'Shop': # town_object must be supplied
        if not town_object and data.get("town_name"):
            # This case should ideally be handled by GameManager: find town by name
            print(f"Warning: Shop.from_dict called for '{data['name']}' without a Town object, but town_name '{data.get('town_name')}' was in save data. Shop will have no town linkage.")
            # One could raise an error or create a dummy town if town_object is critical and missing.
            # For now, we allow it but the shop might not function correctly if town is needed later.

        shop = cls(data["name"], data["owner_name"], town_object, initial_gold=data["gold"])
        shop.inventory = [Item.from_dict(item_data) for item_data in data.get("inventory", [])]
        shop.specialization = data.get("specialization", "General")
        shop.crafting_experience = data.get("crafting_experience", {})
        shop.shop_level = data.get("shop_level", 1)
        shop.markup_percentage = data.get("markup_percentage", 1.2)
        shop.buyback_percentage = data.get("buyback_percentage", 0.5)
        return shop

if __name__ == "__main__":
    # Dummy Town for testing Shop if run directly
    class MockTown(Town): # Inherit from Town to satisfy type hint
        def __init__(self, name="Default Test Town", market_demand_modifiers=None):
            super().__init__(name, [], [], [], market_demand_modifiers if market_demand_modifiers else {})

    default_town = MockTown()
    shop_in_default = Shop(name="The Prancing Pony", owner_name="Barliman Butterbur", town=default_town)

    # Test with a town that has modifiers
    town_with_mods = MockTown("Whiterun", market_demand_modifiers={"Minor Healing Potion": 1.5, "Simple Dagger": 0.8})
    shop_in_whiterun = Shop(name="Warmaiden's", owner_name="Adrianne", town=town_with_mods)

    print("\n--- Crafting Initial Items for Serialization Test ---")
    crafted_potion = shop_in_whiterun.craft_item("Minor Healing Potion")
    shop_in_whiterun.display_inventory()

    print("\n--- Serialization Test for Shop ---")
    shop_dict = shop_in_whiterun.to_dict()
    print(f"Serialized Shop: {shop_dict}")

    # For from_dict, we need the actual Town object. GameManager would handle this.
    # Here, we'll reuse town_with_mods for simplicity of the test.
    loaded_shop = Shop.from_dict(shop_dict, town_with_mods)
    print(f"Deserialized Shop: {loaded_shop}")
    loaded_shop.display_inventory()

    assert loaded_shop.name == shop_in_whiterun.name
    assert loaded_shop.town.name == shop_in_whiterun.town.name
    assert len(loaded_shop.inventory) == len(shop_in_whiterun.inventory)
    if loaded_shop.inventory:
        assert loaded_shop.inventory[0].name == shop_in_whiterun.inventory[0].name
    assert loaded_shop.gold == shop_in_whiterun.gold
    assert loaded_shop.crafting_experience == shop_in_whiterun.crafting_experience

    print("\n--- Shop Serialization Test Complete ---")
