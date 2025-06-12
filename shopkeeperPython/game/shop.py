# Import Character for type hinting only to avoid circular dependency at runtime
from typing import TYPE_CHECKING, Tuple
if TYPE_CHECKING:
    from .character import Character
    from .town import Town

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
        self.markup_percentage = 1.2
        self.buyback_percentage = 0.5

    def __repr__(self):
        return (f"Shop(name='{self.name}', owner='{self.owner_name}', town='{self.town.name if self.town else 'None'}', "
                f"gold={self.gold}, specialization='{self.specialization}', level={self.shop_level})")

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
            print(f"Cannot craft {item_name}. Recipe unknown or prerequisites not met.")
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
        print(f"Crafted {crafted_item.quality} {item_name}. Experience for {item_name}: {self.crafting_experience[item_name]}.")
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
            selling_price = int(item_instance_to_sell.value * npc_offer_percentage)
            self.gold += selling_price
            self.remove_item_from_inventory(item_instance_to_sell.name, specific_item_to_remove=item_instance_to_sell)
            print(f"Sold {item_instance_to_sell.quality} {item_name} to NPC for {selling_price} gold.")
            return selling_price # Return the price
        else:
            print(f"Item '{item_name}' (Quality: {quality_to_sell if quality_to_sell else 'any'}) not found in inventory for sale to NPC.")
            return 0 # Return 0 if no sale

    def sell_item_to_character(self, item_name: str, character_wanting_to_buy: 'Character') -> Tuple[Item | None, int]:
        item_instance_for_sale = None
        for item_in_stock in self.inventory:
            if item_in_stock.name == item_name:
                item_instance_for_sale = item_in_stock
                break
        if not item_instance_for_sale:
            print(f"SHOP: {self.name} does not have '{item_name}' in stock.")
            return None, 0

        town_modifier = self.town.get_item_price_modifier(item_instance_for_sale.name) if self.town else 1.0
        price_to_character = int(item_instance_for_sale.value * town_modifier * self.markup_percentage)

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
        town_modifier = self.town.get_item_price_modifier(item_to_buy.name) if self.town else 1.0
        price_paid_by_shop = int(item_to_buy.value * town_modifier * self.buyback_percentage)

        if self.gold < price_paid_by_shop:
            print(f"SHOP: {self.name} cannot afford to buy {item_to_buy.name} (Price: {price_paid_by_shop}, Shop Gold: {self.gold}).")
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

if __name__ == "__main__":
    class MockTown:
        def __init__(self, name="Default Test Town"):
            self.name = name
            self.market_demand_modifiers = {}
        def get_item_price_modifier(self, item_name):
            return self.market_demand_modifiers.get(item_name, 1.0)

    default_town = MockTown()
    my_shop = Shop(name="The Prancing Pony", owner_name="Barliman Butterbur", town=default_town)
    print(my_shop)

    town_with_mods = MockTown("Whiterun")
    town_with_mods.market_demand_modifiers = {"Minor Healing Potion": 1.5, "Simple Dagger": 0.8}
    shop_in_whiterun = Shop(name="Warmaiden's", owner_name="Adrianne", town=town_with_mods)
    print(shop_in_whiterun)

    print("\n--- Crafting Initial Items ---")
    crafted_potion = shop_in_whiterun.craft_item("Minor Healing Potion")
    crafted_dagger = shop_in_whiterun.craft_item("Simple Dagger")
    shop_in_whiterun.display_inventory()
    print(f"Shop Gold: {shop_in_whiterun.gold}")

    class MockCharacter:
        def __init__(self, name="Mock Buyer", gold=100):
            self.name = name
            self.gold = gold
            self.inventory = []
        def add_item_to_inventory(self, item): self.inventory.append(item)

    mock_buyer = MockCharacter(gold=100)

    print("\n--- Testing sell_item_to_character with town modifiers ---")
    if crafted_potion:
        item_sold, price = shop_in_whiterun.sell_item_to_character(crafted_potion.name, mock_buyer)
        if item_sold:
            print(f"Mock Buyer gold after buying potion: {mock_buyer.gold}")
            mock_buyer.add_item_to_inventory(item_sold)

    # Dagger is now the first item if potion was sold and inventory[0] is used below.
    # Better to check by name or use the specific object if available.
    # Let's assume crafted_dagger is the one we want to target.
    if crafted_dagger:
        item_sold_dagger, price_dagger = shop_in_whiterun.sell_item_to_character(crafted_dagger.name, mock_buyer)
        if item_sold_dagger:
             print(f"Mock Buyer gold after buying dagger: {mock_buyer.gold}")
             mock_buyer.add_item_to_inventory(item_sold_dagger)

    shop_in_whiterun.display_inventory()
    print(f"Shop Gold: {shop_in_whiterun.gold}")

    print("\n--- Testing buy_item_from_character with town modifiers ---")
    if mock_buyer.inventory:
        # Find the potion to sell back, assuming it was bought.
        potion_to_sell_back = None
        for item_in_inv in mock_buyer.inventory:
            if item_in_inv.name == "Minor Healing Potion":
                potion_to_sell_back = item_in_inv
                break

        if potion_to_sell_back:
            price_paid = shop_in_whiterun.buy_item_from_character(potion_to_sell_back, mock_buyer)
            if price_paid > 0:
                # Remove from mock buyer's inventory manually for test
                mock_buyer.inventory.remove(potion_to_sell_back)
                print(f"Mock Buyer gold after selling potion: {mock_buyer.gold}")
                print(f"Shop Gold: {shop_in_whiterun.gold}")
        else:
            print("Mock buyer did not have 'Minor Healing Potion' to sell back.")

    shop_in_whiterun.display_inventory()
    print("--- Shop System Test with Town Complete ---")
