# Import Character for type hinting only to avoid circular dependency at runtime
from typing import TYPE_CHECKING, Tuple
if TYPE_CHECKING:
    from .character import Character
    # from .town import Town # Town for type hinting - already imported below

from .item import Item # Removed QUALITY_TIERS, QUALITY_VALUE_MULTIPLIERS
from .town import Town


class Shop:
    """
    Represents a shop in the Shopkeeper Python game.
    """
    SHOP_LEVEL_CONFIG = {
        1: {"cost_to_upgrade": 500, "max_inventory_slots": 20, "crafting_quality_bonus": 0},
        2: {"cost_to_upgrade": 1500, "max_inventory_slots": 30, "crafting_quality_bonus": 1},
        3: {"cost_to_upgrade": 3000, "max_inventory_slots": 40, "crafting_quality_bonus": 2},
    }
    MAX_SHOP_LEVEL = 3
    MAX_REPUTATION = 100
    MIN_REPUTATION = -20

    CRITICAL_SUCCESS_CHANCE = 0.05
    CRITICAL_FAILURE_CHANCE = 0.05
    CRITICAL_SUCCESS_QUALITY_BONUS = 1  # Index shift in QUALITY_TIERS
    CRITICAL_FAILURE_QUALITY_PENALTY = -1 # Index shift in QUALITY_TIERS

    NPC_MIN_OFFER_PERCENTAGE = 0.7  # NPCs offer at least 70% of calculated sale price
    NPC_MAX_OFFER_PERCENTAGE = 0.9  # NPCs offer at most 90% of calculated sale price
    BASE_NPC_BUY_CHANCE = 0.10      # Base chance an NPC attempts to buy something
    REPUTATION_BUY_CHANCE_MULTIPLIER = 0.001 # How much each reputation point adds to buy chance
    MAX_NPC_BUY_CHANCE_BONUS = 0.20  # Maximum bonus chance from reputation

    SPECIALIZATION_TYPES = ["General Store", "Blacksmith", "Alchemist"]

    ADVANCED_RECIPES = {
        "Blacksmith": {
            "Iron Armor": {"base_value": 50, "type": "armor", "description": "A sturdy set of iron armor.", "crafting_difficulty": 15, "effects": {"defense": 10}, "ingredients": {"Iron Ingot": 5, "Leather Straps": 2}},
            "Steel Sword": {"base_value": 70, "type": "weapon", "description": "A well-crafted steel sword.", "crafting_difficulty": 18, "effects": {"damage": "1d10"}, "ingredients": {"Steel Ingot": 3, "Oak Wood": 1}}
        },
        "Alchemist": {
            "Greater Healing Potion": {"base_value": 50, "type": "potion", "description": "Restores a significant amount of health.", "effects": {"healing": 25}, "crafting_difficulty": 12, "is_consumable": True, "ingredients": {"Concentrated Herbs": 2, "Purified Water": 1, "Crystal Vial": 1}},
            "Potion of Strength": {"base_value": 60, "type": "potion", "description": "Temporarily increases strength.", "effects": {"stat_boost": {"STR": 2, "duration_hours": 1}}, "crafting_difficulty": 16, "is_consumable": True, "ingredients": {"Dragon's Blood Resin": 1, "Mountain Flower": 3, "Crystal Vial": 1}}
        },
        "General Store": {}
    }

    BASIC_RECIPES = {
        "Stale Ale": {"base_value": 1, "type": "food", "description": "Barely drinkable ale.", "crafting_difficulty": 1, "effects": {"stamina_recovery": 1}, "is_consumable": True, "ingredients": {"Dirty Water": 1, "Moldy Fruit": 2}},
        "Simple Dagger": {"base_value": 5, "type": "weapon", "description": "A crude but functional dagger.", "crafting_difficulty": 5, "effects": {"damage": "1d4"}, "ingredients": {"Leather Scraps": 1, "Scrap Metal": 2}},
        "Minor Healing Potion": {"base_value": 10, "type": "potion", "description": "Restores a small amount of health.", "effects": {"healing": 5}, "crafting_difficulty": 3, "is_consumable": True, "ingredients": {"Herb Bundle": 1, "Clean Water": 1}},
        "Wooden Club": {"base_value": 3, "type": "weapon", "description": "A sturdy piece of wood, good for bonking.", "crafting_difficulty": 2, "effects": {"damage": "1d4"}, "ingredients": {"Sturdy Branch": 1}},
        "Traveler's Bread": {"base_value": 2, "type": "food", "description": "A dense, long-lasting loaf of bread.", "crafting_difficulty": 2, "effects": {"stamina_recovery": 2, "healing": 1}, "is_consumable": True, "ingredients": {"Grain": 2, "Clean Water": 1}},
        "Leather Scraps": {"type": "component", "base_value": 4, "description": "Pieces of cured leather, useful for crafting.", "crafting_difficulty": 3, "effects": {}, "ingredients": {"Rawhide": 1}},
        "Simple Bandages": {"type": "healing_item", "base_value": 6, "description": "Clean strips of cloth for dressing minor wounds.", "crafting_difficulty": 4, "effects": {"healing": 3}, "is_consumable": True, "ingredients": {"Linen Scrap": 2}},
        "Crude Lockpick": {"type": "tool", "base_value": 8, "description": "A roughly made lockpick. Might break easily.", "crafting_difficulty": 7, "effects": {"skill_bonus": {"DEX_tools": 1}}, "is_consumable": False, "ingredients": {"Scrap Metal": 1, "Small Twig": 1}},
        "Herb Bundle": {"type": "component", "base_value": 5, "description": "A bundle of common medicinal herbs.", "crafting_difficulty": 1, "effects": {}, "ingredients": {"Wild Herb": 3}},
        "Basic Arrow": {"type": "ammunition", "base_value": 1, "description": "A simple wooden arrow with a stone head. Recipe makes 5.", "crafting_difficulty": 4, "effects": {"damage": "1d6"}, "quantity_produced": 5, "ingredients": {"Small Twig": 5, "Stone Fragment": 5, "Bird Feather": 5}}
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
        self.specialization = "General Store"  # Default to "General Store"
        self.crafting_experience = {}
        self.shop_level = 1
        self.max_inventory_slots = self.SHOP_LEVEL_CONFIG[self.shop_level]["max_inventory_slots"]
        self.reputation = 0
        # self.MAX_REPUTATION = 100 # Moved to class level
        # self.MIN_REPUTATION = -20 # Moved to class level
        self.markup_percentage = 1.2 # Default markup (e.g., 20% over value for player)
        self.buyback_percentage = 0.5 # Default buyback (e.g., 50% of value for player)
        self.temporary_customer_boost = 0.0 # For 'Post Advertisements' action

    def __repr__(self):
        return (f"Shop(name='{self.name}', owner='{self.owner_name}', town='{self.town.name if self.town else 'None'}', "
                f"gold={self.gold}, specialization='{self.specialization}', level={self.shop_level}, reputation={self.reputation}, slots={len(self.inventory)}/{self.max_inventory_slots})")

    def update_town(self, new_town: 'Town'):
        """Updates the shop's associated town."""
        self.town = new_town
        print(f"Shop '{self.name}' has updated its town to {new_town.name}.")

    def add_item_to_inventory(self, item: Item):
        # Check if the item is stackable and already exists in inventory
        for existing_item in self.inventory:
            if existing_item.name == item.name and existing_item.quality == item.quality and hasattr(existing_item, 'quantity') and hasattr(item, 'quantity'):
                existing_item.quantity += item.quantity
                print(f"SHOP: Stacked {item.quantity}x {item.name} (Total: {existing_item.quantity}). Inventory slots: {len(self.inventory)}/{self.max_inventory_slots}.")
                return

        # If not stackable or doesn't exist, check for new slot
        if len(self.inventory) >= self.max_inventory_slots:
            print(f"SHOP: Cannot add {item.name}. Inventory is full ({len(self.inventory)}/{self.max_inventory_slots} slots).")
            return

        # Ensure item has quantity BEFORE accessing it in print or other logic
        if not hasattr(item, 'quantity'):
            item.quantity = 1

        self.inventory.append(item)
        # Now it's safe to access item.quantity
        print(f"SHOP: Added {item.name} (Qty: {item.quantity}) to inventory. Inventory slots: {len(self.inventory)}/{self.max_inventory_slots}.")


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

    def remove_item_from_inventory(self, item_name: str, quantity_to_remove: int = None, specific_item_to_remove: Item = None) -> Item | None:
        item_instance_in_inventory = None

        if specific_item_to_remove and specific_item_to_remove in self.inventory:
            item_instance_in_inventory = specific_item_to_remove
        else: # Fallback to finding by name if specific instance isn't directly provided or matched
            item_instance_in_inventory = next((item for item in self.inventory if item.name == item_name), None)

        if not item_instance_in_inventory:
            # print(f"SHOP: Item '{item_name}' not found in inventory for removal.")
            return None

        if quantity_to_remove is None or quantity_to_remove >= item_instance_in_inventory.quantity:
            # Remove the whole stack
            self.inventory.remove(item_instance_in_inventory)
            # print(f"SHOP: Removed entire stack of {item_instance_in_inventory.quantity}x {item_instance_in_inventory.name} from inventory.")
            return item_instance_in_inventory # Return the original item instance (which includes its original full quantity)
        elif quantity_to_remove > 0 and quantity_to_remove < item_instance_in_inventory.quantity:
            # Decrement quantity from the stack
            item_instance_in_inventory.quantity -= quantity_to_remove
            # print(f"SHOP: Decremented {quantity_to_remove}x from {item_instance_in_inventory.name} stack. New quantity: {item_instance_in_inventory.quantity}.")
            # Return a new Item instance representing the quantity removed
            # This is important so the calling function knows what was "taken out"
            # The original item in inventory remains, but with reduced quantity.
            removed_item_portion = Item(
                name=item_instance_in_inventory.name,
                description=item_instance_in_inventory.description,
                base_value=item_instance_in_inventory.base_value,
                item_type=item_instance_in_inventory.item_type,
                quality=item_instance_in_inventory.quality,
                effects=item_instance_in_inventory.effects.copy(),
                is_magical=item_instance_in_inventory.is_magical,
                is_attunement=item_instance_in_inventory.is_attunement,
                is_consumable=item_instance_in_inventory.is_consumable,
                quantity=quantity_to_remove # This is the key part for the returned item
            )
            return removed_item_portion
        else: # quantity_to_remove is 0 or invalid (e.g. negative, though not expected)
            # print(f"SHOP: Invalid quantity ({quantity_to_remove}) to remove for {item_name}. No items removed.")
            return None


    def can_craft(self, item_name: str, character_skills=None) -> bool:
        if item_name in self.BASIC_RECIPES:
            return True
        if self.specialization in self.ADVANCED_RECIPES and \
           item_name in self.ADVANCED_RECIPES[self.specialization]:
            # TODO: Add skill check here if character_skills are provided and recipes define skill requirements
            return True
        return False

    def _determine_quality(self, item_name: str) -> str:
        base_craft_count = self.crafting_experience.get(item_name, 0)
        quality_bonus = self.SHOP_LEVEL_CONFIG[self.shop_level]["crafting_quality_bonus"]
        effective_craft_count = base_craft_count + quality_bonus

        determined_quality = self.QUALITY_THRESHOLDS[0][1]
        for threshold, quality in self.QUALITY_THRESHOLDS:
            if effective_craft_count >= threshold:
                determined_quality = quality
            else:
                break
        return determined_quality

    def craft_item(self, item_name: str, character: 'Character') -> Item | None:
        if not self.can_craft(item_name):
            # GameManager usually prints this
            # print(f"Cannot craft {item_name}. Recipe unknown or prerequisites not met.")
            return None

        recipe = None
        if item_name in self.BASIC_RECIPES:
            recipe = self.BASIC_RECIPES[item_name]
        elif self.specialization in self.ADVANCED_RECIPES and \
             item_name in self.ADVANCED_RECIPES[self.specialization]:
            recipe = self.ADVANCED_RECIPES[self.specialization][item_name]
        else:
            # This should not be reached if can_craft was called first
            print(f"SHOP: Recipe for {item_name} not found for specialization {self.specialization}.")
            return None

        ingredients = recipe.get("ingredients", {})

        if ingredients:
            can_craft_item, missing_items = character.has_items(ingredients)
            if not can_craft_item:
                missing_items_str = ", ".join([f"{qty} {name}" for name, qty in missing_items.items()])
                print(f"SHOP: Cannot craft {item_name}. Missing ingredients for {character.name}: {missing_items_str}.")
                return None

        # Proceed with crafting if ingredients are present or not required
        self.crafting_experience[item_name] = self.crafting_experience.get(item_name, 0) + 1
        base_quality_name = self._determine_quality(item_name)
        final_quality_name = base_quality_name

        # Critical Success/Failure Roll
        import random # Make sure to import random if not already done globally in the file
        crit_roll = random.random()

        current_quality_names = [q_name for _, q_name in self.QUALITY_THRESHOLDS]

        if crit_roll <= self.CRITICAL_SUCCESS_CHANCE:
            try:
                current_index = current_quality_names.index(base_quality_name)
                new_index = min(current_index + self.CRITICAL_SUCCESS_QUALITY_BONUS, len(current_quality_names) - 1)
                final_quality_name = current_quality_names[new_index]
                if final_quality_name != base_quality_name:
                    print(f"SHOP: Critical Success! Crafted {item_name} resulted in {final_quality_name} quality (up from {base_quality_name}).")
                else:
                    print(f"SHOP: Critical Success! Crafted {item_name} at {base_quality_name} (already max or no change).")
            except ValueError:
                print(f"SHOP: Warning - base quality {base_quality_name} not in defined tiers for critical success.")
        elif crit_roll <= self.CRITICAL_SUCCESS_CHANCE + self.CRITICAL_FAILURE_CHANCE: # Check only if not crit success
            try:
                current_index = current_quality_names.index(base_quality_name)
                new_index = max(current_index + self.CRITICAL_FAILURE_QUALITY_PENALTY, 0)
                final_quality_name = current_quality_names[new_index]
                if final_quality_name != base_quality_name:
                    print(f"SHOP: Critical Failure! Crafted {item_name} resulted in {final_quality_name} quality (down from {base_quality_name}).")
                else:
                     print(f"SHOP: Critical Failure! Crafted {item_name} at {base_quality_name} (already min or no change).")
            except ValueError:
                print(f"SHOP: Warning - base quality {base_quality_name} not in defined tiers for critical failure.")
        else:
            # Normal success, quality remains base_quality_name
            pass


        # Consume ingredients before adding item to inventory
        if ingredients:
            if not character.consume_items(ingredients):
                # This should ideally not happen if has_items check was accurate
                print(f"SHOP: Error consuming ingredients for {item_name} from {character.name}'s inventory. Crafting aborted.")
                # Potentially roll back crafting_experience increment if that's desired
                # self.crafting_experience[item_name] = self.crafting_experience.get(item_name, 1) -1 # example rollback
                return None

        crafted_item = Item(
            name=item_name,
            description=recipe.get("description", "A crafted item."),
            base_value=recipe["base_value"],
            item_type=recipe["type"],
            quality=final_quality_name, # Use the final determined quality
            effects=recipe.get("effects", {}),
            is_magical=recipe.get("is_magical", recipe["type"] in ["potion", "scroll", "weapon", "armor", "ring", "amulet"]),
            is_attunement=recipe.get("is_attunement", False),
            is_consumable=recipe.get("is_consumable", recipe["type"] in ["potion", "food", "scroll"]),
            quantity=recipe.get("quantity_produced", 1) # Pass quantity directly
        )
        # If quantity_produced is > 1, the Item object itself handles this via its quantity field.
        # The shop inventory will store one Item stack.
        self.add_item_to_inventory(crafted_item)
        # GameManager can print success
        # print(f"Crafted {crafted_item.quantity}x {crafted_item.quality} {item_name}. Experience for {item_name}: {self.crafting_experience[item_name]}.")
        return crafted_item

    def stock_item(self, item: Item):
        self.add_item_to_inventory(item)

    def initiate_haggling_for_item_sale(self, item_to_sell: Item, npc_name: str = "A Customer") -> dict | None:
        """
        Initiates a haggling session when an NPC wants to buy an item from the shop.
        Returns a dictionary with haggling state if successful, None otherwise.
        """
        if not item_to_sell or item_to_sell not in self.inventory:
            print(f"SHOP: Cannot initiate haggling. Item '{item_to_sell.name if item_to_sell else 'Unknown'}' not in stock.")
            return None

        # Calculate the shop's "ideal" selling price (player selling to NPC means shop wants higher price)
        # For player selling to NPC, this is the price the shop would normally charge *anyone*
        # Let's use calculate_sale_price without a character_buying, so it's the shop's standard markup.
        standard_shop_price = self.calculate_sale_price(item_to_sell) # This is what the shop *would* sell it for to a player

        # NPC's initial offer is a percentage of this standard shop price.
        # This 'standard_shop_price' is what the player *would* get if they sold directly.
        # The NPC offer should be based on what the NPC thinks it's worth, which is related to item.value.
        # Let's adjust: NPC offer is based on item.value, modified by NPC_MIN/MAX_OFFER_PERCENTAGE.
        # The shop's `calculate_sale_price` is what the *player* would pay if *they* were buying from *this shop*.
        # For an NPC buying from the player's shop, the NPC should offer a % of the item's objective value.

        # Let's use the item's objective value `item_to_sell.value` as the base for NPC's offer.
        # This value already includes quality multipliers.
        base_value_for_npc_offer = item_to_sell.value

        min_offer_actual = base_value_for_npc_offer * self.NPC_MIN_OFFER_PERCENTAGE
        max_offer_actual = base_value_for_npc_offer * self.NPC_MAX_OFFER_PERCENTAGE

        # Reputation influence: higher reputation pushes offers towards the higher end of the range.
        # Normalized reputation: (self.reputation - MIN_REPUTATION) / (MAX_REPUTATION - MIN_REPUTATION)
        # This gives a 0-1 scale. Let's simplify: use raw rep points for a small nudge.
        reputation_influence = (self.reputation / self.MAX_REPUTATION) * (max_offer_actual - min_offer_actual) # Max influence shifts it fully up

        initial_offer_value_float = min_offer_actual + reputation_influence
        # Ensure it doesn't exceed max_offer_actual due to extreme positive rep if formula is off
        initial_offer_value_float = min(initial_offer_value_float, max_offer_actual)
        # Ensure it's not below min_offer_actual due to negative rep
        initial_offer_value_float = max(initial_offer_value_float, min_offer_actual)

        initial_npc_offer = int(initial_offer_value_float) if initial_offer_value_float >= 1.0 else (1 if initial_offer_value_float > 0 else 0)

        # Ensure item_to_sell has a quantity attribute, defaulting to 1 if missing (though it should always exist)
        quantity_for_sale = getattr(item_to_sell, 'quantity', 1)
        if quantity_for_sale <= 0:
            print(f"SHOP: Cannot initiate haggling for {item_to_sell.name}, quantity is {quantity_for_sale}.")
            return None


        haggling_state = {
            "item_name": item_to_sell.name,
            "item_quality": item_to_sell.quality,
            "item_base_value": item_to_sell.base_value, # For reference
            "quantity": quantity_for_sale, # Added quantity
            "item_id_in_shop_inventory": self.inventory.index(item_to_sell), # To identify the exact item
            "npc_name": npc_name,
            "initial_offer": initial_npc_offer,
            "current_offer": initial_npc_offer,
            "shop_target_price": standard_shop_price, # What the shop ideally wants (player selling context)
            "npc_mood": "Neutral",
            "haggle_rounds_attempted": 0,
            "max_haggle_rounds": 3, # Default, can be adjusted
            "context": "player_selling", # Player's shop is selling
            "can_still_haggle": True
        }
        print(f"SHOP: Initiating haggling with {npc_name} for {quantity_for_sale}x {item_to_sell.name}. Initial NPC offer: {initial_npc_offer}g (Shop's ideal price: {standard_shop_price}g).")
        return haggling_state

    def finalize_haggled_sale(self, item_instance_to_sell: Item, final_selling_price: int) -> bool:
        """
        Completes the sale of an item to an NPC after haggling.
        Assumes item_instance_to_sell is the correct instance from inventory.
        It now also takes quantity_sold which comes from the haggle session.
        """
        if not item_instance_to_sell or item_instance_to_sell not in self.inventory: # Check if the instance is in inventory
            print(f"SHOP: Error finalizing sale. Item instance '{item_instance_to_sell.name if item_instance_to_sell else 'Unknown'}' not found in stock by reference.")
            return False

        if quantity_sold <= 0:
            print(f"SHOP: Error finalizing sale. Quantity to sell for '{item_instance_to_sell.name}' is {quantity_sold}.")
            return False

        if item_instance_to_sell.quantity < quantity_sold:
            print(f"SHOP: Error finalizing sale. Shop only has {item_instance_to_sell.quantity} of '{item_instance_to_sell.name}', but NPC tried to buy {quantity_sold}.")
            return False # Should not happen if haggle was initiated correctly with available quantity

        self.gold += final_selling_price

        # Use the modified remove_item_from_inventory with quantity
        # Pass specific_item_to_remove to ensure we're acting on the correct stack.
        item_representing_sold_portion = self.remove_item_from_inventory(
            item_name=item_instance_to_sell.name,
            quantity_to_remove=quantity_sold,
            specific_item_to_remove=item_instance_to_sell
        )

        if not item_representing_sold_portion:
            # This implies an issue with remove_item_from_inventory or inconsistent state
            print(f"SHOP: CRITICAL ERROR - Failed to remove/decrement {quantity_sold}x '{item_instance_to_sell.name}' from inventory during sale. Reverting gold.")
            self.gold -= final_selling_price # Revert gold
            return False

        # Reputation gain logic (based on the item sold, not just the portion)
        rep_change = 0
        quality_rep_bonus = {"Rare": 2, "Very Rare": 3, "Legendary": 4, "Mythical": 5}
        # Use item_instance_to_sell for quality/name as item_representing_sold_portion might be a new object
        if item_instance_to_sell.quality in quality_rep_bonus:
            rep_change += quality_rep_bonus[item_instance_to_sell.quality]

        if self.specialization in self.ADVANCED_RECIPES and \
           item_instance_to_sell.name in self.ADVANCED_RECIPES[self.specialization]:
            rep_change += 1

        if rep_change > 0:
            old_rep = self.reputation
            self.reputation = min(self.reputation + rep_change, self.MAX_REPUTATION)
            if self.reputation != old_rep:
                print(f"SHOP: Selling {quantity_sold}x {item_instance_to_sell.quality} {item_instance_to_sell.name} improved shop reputation to {self.reputation} (+{self.reputation - old_rep}).")

        print(f"SHOP: Successfully sold {quantity_sold}x {item_instance_to_sell.name} for {final_selling_price}g after haggling. Shop gold: {self.gold}.")
        if item_instance_to_sell.quantity > 0 : # If stack still exists
             print(f"SHOP: Remaining quantity of {item_instance_to_sell.name} in shop: {item_instance_to_sell.quantity}.")
        else: # Stack was fully depleted
             print(f"SHOP: Sold out of {item_instance_to_sell.name}.")
        return True

    # calculate_sale_price is primarily for player buying from this shop, or shop setting its own prices.
    # For NPC buying from player's shop, their offer is based on item.value and their own offer percentages.
    # For player buying from other NPCs, that NPC's shop/pricing logic would apply.
    def calculate_sale_price(self, item_or_item_name: (Item | str), character_buying: 'Character' = None) -> int:
        """
        Calculates the price this shop would charge if a character (player or NPC) buys this item from this shop.
        Considers town demand, shop markup, and potential character faction benefits.
        """
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

    # Modified to accept character_buying for faction discount checks
    def calculate_sale_price(self, item_or_item_name: (Item | str), character_buying: 'Character' = None) -> int:
        """Calculates the sale price of an item, considering town demand, shop markup, and character faction benefits."""
        item_instance = None
        if isinstance(item_or_item_name, str):
            for item_in_stock in self.inventory: # Search in current inventory
                if item_in_stock.name == item_or_item_name:
                    item_instance = item_in_stock
                    break
            if not item_instance:
                if item_or_item_name in self.BASIC_RECIPES:
                    item_instance = Item(name=item_or_item_name, base_value=self.BASIC_RECIPES[item_or_item_name]['base_value'], item_type="unknown")
                else:
                    return 0
        elif isinstance(item_or_item_name, Item):
            item_instance = item_or_item_name

        if not item_instance:
            return 0

        town_modifier = 1.0
        if self.town and hasattr(self.town, 'get_item_price_modifier'):
            town_modifier = self.town.get_item_price_modifier(item_instance.name)
        elif self.town and hasattr(self.town, 'market_demand_modifiers'):
             town_modifier = self.town.market_demand_modifiers.get(item_instance.name, 1.0)

        price = int(item_instance.value * town_modifier * self.markup_percentage)

        if character_buying:
            # Check for Merchant's Guild discount
            faction_details = character_buying.get_faction_reputation_details("merchants_guild")
            if faction_details:
                faction_def = character_buying.get_faction_data("merchants_guild")
                current_rank_name = faction_details.get("rank_name")
                if faction_def and current_rank_name:
                    for rank_info in faction_def.get("ranks", []):
                        if rank_info["name"] == current_rank_name:
                            for benefit in rank_info.get("benefits", []):
                                if benefit["type"] == "shop_discount" and \
                                   (benefit.get("scope") == "guild_affiliated_shops" or benefit.get("scope") == "all_shops"):
                                    # Assuming this shop is considered "guild_affiliated" for simplicity
                                    discount_percentage = benefit["value_percentage"]
                                    # price_before_discount = price # For logging if needed
                                    price = int(price * (1 - discount_percentage / 100.0))
                                    # print(f"Debug: Applied {discount_percentage}% discount. Old price: {price_before_discount}, New: {price}") # Optional debug
                                    break
                            break
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

        # Pass the character to calculate_sale_price for potential discounts
        price_to_character = self.calculate_sale_price(item_instance_for_sale, character_wanting_to_buy)

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
        if specialization_type not in self.SPECIALIZATION_TYPES:
            print(f"SHOP: Invalid specialization type '{specialization_type}'. Shop specialization remains {self.specialization}.")
            return
        self.specialization = specialization_type
        print(f"SHOP: {self.name}'s specialization set to: {self.specialization}")

    def upgrade_shop(self) -> bool:
        if self.shop_level >= self.MAX_SHOP_LEVEL:
            print(f"SHOP: {self.name} is already at the maximum level ({self.MAX_SHOP_LEVEL}).")
            return False

        next_level = self.shop_level + 1
        if next_level not in self.SHOP_LEVEL_CONFIG:
            print(f"SHOP: Configuration for level {next_level} not found. Cannot upgrade.")
            return False

        self.shop_level = next_level
        self.max_inventory_slots = self.SHOP_LEVEL_CONFIG[self.shop_level]["max_inventory_slots"]
        quality_bonus = self.SHOP_LEVEL_CONFIG[self.shop_level]["crafting_quality_bonus"]

        print(f"SHOP: {self.name} upgraded to Level {self.shop_level}!")
        print(f"  - Max Inventory Slots: {self.max_inventory_slots}")
        print(f"  - Crafting Quality Bonus: +{quality_bonus}")
        if self.shop_level < self.MAX_SHOP_LEVEL:
             cost_for_next = self.SHOP_LEVEL_CONFIG[self.shop_level +1 ]['cost_to_upgrade'] if self.shop_level + 1 <= self.MAX_SHOP_LEVEL else "N/A" # Check to prevent key error
             if cost_for_next != "N/A" and (self.shop_level +1) in self.SHOP_LEVEL_CONFIG : # Check if next level exists
                  print(f"  - Cost for next upgrade (Level {self.shop_level + 1}): {self.SHOP_LEVEL_CONFIG[self.shop_level + 1]['cost_to_upgrade']}g")
        return True

    def display_inventory(self):
        if not self.inventory:
            print(f"{self.name}'s inventory is empty. (Slots: 0/{self.max_inventory_slots})")
            return
        print(f"\n--- {self.name}'s Inventory (Level {self.shop_level}, Slots: {len(self.inventory)}/{self.max_inventory_slots}) (in {self.town.name if self.town else 'N/A'}) ---")
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
            "reputation": self.reputation,
            "markup_percentage": self.markup_percentage,
            "buyback_percentage": self.buyback_percentage,
            "temporary_customer_boost": self.temporary_customer_boost, # Save the boost
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
        shop.specialization = data.get("specialization", "General Store") # Default to General Store if not in save
        shop.crafting_experience = data.get("crafting_experience", {})
        shop.shop_level = data.get("shop_level", 1)
        shop.reputation = data.get("reputation", 0)
        # Recalculate max_inventory_slots based on loaded shop_level and config
        if shop.shop_level in Shop.SHOP_LEVEL_CONFIG:
            shop.max_inventory_slots = Shop.SHOP_LEVEL_CONFIG[shop.shop_level]["max_inventory_slots"]
        else:
            print(f"Warning: Shop level {shop.shop_level} from save data not found in SHOP_LEVEL_CONFIG. Defaulting slots for level 1.")
            shop.max_inventory_slots = Shop.SHOP_LEVEL_CONFIG[1]["max_inventory_slots"] # Fallback

        shop.markup_percentage = data.get("markup_percentage", 1.2)
        shop.buyback_percentage = data.get("buyback_percentage", 0.5)
        shop.temporary_customer_boost = data.get("temporary_customer_boost", 0.0) # Load the boost
        return shop

if __name__ == "__main__":
    # Dummy Town for testing Shop if run directly
    class MockTown(Town): # Inherit from Town to satisfy type hint
        def __init__(self, name="Default Test Town", market_demand_modifiers=None):
            super().__init__(name, [], [], [], market_demand_modifiers if market_demand_modifiers else {})

    # Dummy Character for testing
    class MockCharacter:
        def __init__(self, name="Test Character", gold=100):
            self.name = name
            self.inventory = []
            self.gold = gold

        def add_item_to_inventory(self, item: Item):
            self.inventory.append(item)
            print(f"DEBUG: Added {item.name} to {self.name}'s inventory. Current: {[i.name for i in self.inventory]}")


        def has_items(self, items_to_check: dict) -> tuple[bool, dict]:
            missing_items = {}
            for item_name, required_qty in items_to_check.items():
                current_qty = sum(1 for item in self.inventory if item.name == item_name)
                if current_qty < required_qty:
                    missing_items[item_name] = required_qty - current_qty
            if missing_items:
                return False, missing_items
            return True, {}

        def consume_items(self, items_to_consume: dict) -> bool:
            print(f"DEBUG: {self.name} attempting to consume: {items_to_consume}")
            # This is a simplified consumption logic for testing.
            # A more robust one would handle stacks or specific item instances.
            for item_name, qty_to_consume in items_to_consume.items():
                consumed_count = 0
                new_inventory = []
                for item in reversed(self.inventory): # Reversed to remove from end, less index issues
                    if item.name == item_name and consumed_count < qty_to_consume:
                        consumed_count += 1
                        print(f"DEBUG: Consuming {item.name} from {self.name}")
                    else:
                        new_inventory.append(item)
                self.inventory = list(reversed(new_inventory)) # Preserve original order if any
                if consumed_count < qty_to_consume:
                    print(f"DEBUG: Failed to consume all {item_name} for {self.name}. Needed {qty_to_consume}, found {consumed_count}")
                    return False # Should not happen if has_items is called first
            print(f"DEBUG: {self.name}'s inventory after consumption: {[i.name for i in self.inventory]}")
            return True

    default_town = MockTown()
    # shop_in_default = Shop(name="The Prancing Pony", owner_name="Barliman Butterbur", town=default_town) # owner_name is str

    # Test with a town that has modifiers
    town_with_mods = MockTown("Whiterun", market_demand_modifiers={"Minor Healing Potion": 1.5, "Simple Dagger": 0.8})
    # The shop owner is just a name, the actual character object is passed during crafting
    shop_in_whiterun = Shop(name="Warmaiden's", owner_name="Adrianne Avenicci", town=town_with_mods)
    shop_in_whiterun.set_specialization("Blacksmith") # Test specialization

    print(f"Initial shop: {shop_in_whiterun}")

    # Create a mock character (the shop owner or a player)
    test_crafter = MockCharacter(name="Test Crafter", gold=100)
    # Add some ingredients to the crafter's inventory for testing
    test_crafter.add_item_to_inventory(Item(name="Herb Bundle", description="Desc", base_value=5, item_type="component", quality="Common"))
    test_crafter.add_item_to_inventory(Item(name="Clean Water", description="Desc", base_value=1, item_type="component", quality="Common"))
    test_crafter.add_item_to_inventory(Item(name="Clean Water", description="Desc", base_value=1, item_type="component", quality="Common")) # more water
    test_crafter.add_item_to_inventory(Item(name="Scrap Metal", description="Desc", base_value=2, item_type="component", quality="Common"))
    test_crafter.add_item_to_inventory(Item(name="Scrap Metal", description="Desc", base_value=2, item_type="component", quality="Common"))
    # Ingredients for advanced recipes
    test_crafter.add_item_to_inventory(Item(name="Iron Ingot", description="Desc", base_value=10, item_type="component", quality="Common"))
    test_crafter.add_item_to_inventory(Item(name="Iron Ingot", description="Desc", base_value=10, item_type="component", quality="Common"))
    test_crafter.add_item_to_inventory(Item(name="Iron Ingot", description="Desc", base_value=10, item_type="component", quality="Common"))
    test_crafter.add_item_to_inventory(Item(name="Iron Ingot", description="Desc", base_value=10, item_type="component", quality="Common"))
    test_crafter.add_item_to_inventory(Item(name="Iron Ingot", description="Desc", base_value=10, item_type="component", quality="Common"))
    test_crafter.add_item_to_inventory(Item(name="Leather Straps", description="Desc", base_value=5, item_type="component", quality="Common"))
    test_crafter.add_item_to_inventory(Item(name="Leather Straps", description="Desc", base_value=5, item_type="component", quality="Common"))


    print("\n--- Crafting Test (Minor Healing Potion) ---")
    # Attempt to craft a Minor Healing Potion - should succeed
    print(f"{test_crafter.name} inventory before potion: {[i.name for i in test_crafter.inventory]}")
    crafted_potion = shop_in_whiterun.craft_item("Minor Healing Potion", test_crafter)
    if crafted_potion:
        print(f"Successfully crafted: {crafted_potion.name} (Quality: {crafted_potion.quality})")
    else:
        print(f"Failed to craft Minor Healing Potion.")
    shop_in_whiterun.display_inventory()
    print(f"{test_crafter.name} inventory after potion: {[i.name for i in test_crafter.inventory]}")

    print("\n--- Crafting Test (Simple Dagger) - Missing Leather Scraps ---")
    # Attempt to craft a Simple Dagger - should fail due to missing Leather Scraps (which itself needs Rawhide)
    print(f"{test_crafter.name} inventory before dagger: {[i.name for i in test_crafter.inventory]}")
    crafted_dagger = shop_in_whiterun.craft_item("Simple Dagger", test_crafter)
    if crafted_dagger:
        print(f"Successfully crafted: {crafted_dagger.name}")
    else:
        print(f"Failed to craft Simple Dagger.")
    shop_in_whiterun.display_inventory()
    print(f"{test_crafter.name} inventory after dagger: {[i.name for i in test_crafter.inventory]}")

    print("\n--- Crafting Test (Iron Armor - Blacksmith Specialization) ---")
    # Shop is Blacksmith, Crafter has Iron Ingots and Leather Straps
    shop_in_whiterun.set_specialization("Blacksmith") # Ensure it's set
    print(f"{test_crafter.name} inventory before Iron Armor: {[i.name for i in test_crafter.inventory]}")
    crafted_armor = shop_in_whiterun.craft_item("Iron Armor", test_crafter)
    if crafted_armor:
        print(f"Successfully crafted: {crafted_armor.name} (Quality: {crafted_armor.quality})")
    else:
        print(f"Failed to craft Iron Armor.")
    shop_in_whiterun.display_inventory()
    print(f"{test_crafter.name} inventory after Iron Armor: {[i.name for i in test_crafter.inventory]}")

    print("\n--- Inventory Slot Limit Test ---")
    # Fill up inventory to test slot limit
    for i in range(shop_in_whiterun.max_inventory_slots - len(shop_in_whiterun.inventory) + 2): # Try to add 2 more than limit
        item_to_add = Item(name=f"Filler Item {i+1}", description="Desc", base_value=1, item_type="misc", quality="Common")
        shop_in_whiterun.add_item_to_inventory(item_to_add) # add_item_to_inventory now prints messages

    # Test stacking
    stackable_item = Item(name="Iron Ingot", description="Desc", base_value=10, item_type="component", quality="Common"); stackable_item.quantity = 1
    shop_in_whiterun.add_item_to_inventory(stackable_item) # Should stack with existing Iron Ingots if any, or add new
    shop_in_whiterun.add_item_to_inventory(stackable_item) # Should stack


    print("\n--- Shop Upgrade Test ---")
    print(f"Shop level before upgrade: {shop_in_whiterun.shop_level}, Slots: {shop_in_whiterun.max_inventory_slots}")
    # Simulate player having enough gold (GameManager would handle this)
    shop_in_whiterun.upgrade_shop() # Level 2
    shop_in_whiterun.upgrade_shop() # Level 3
    shop_in_whiterun.upgrade_shop() # Try to upgrade past max

    print(f"Shop after upgrades: {shop_in_whiterun}")

    print("\n--- Critical Crafting Test (Minor Healing Potion) ---")
    # Temporarily increase chances for testing, or run many times
    # Shop.CRITICAL_SUCCESS_CHANCE = 0.5
    # Shop.CRITICAL_FAILURE_CHANCE = 0.5
    print(f"Shop Level: {shop_in_whiterun.shop_level}, Quality Bonus: {Shop.SHOP_LEVEL_CONFIG[shop_in_whiterun.shop_level]['crafting_quality_bonus']}")
    print(f"Crafting {test_crafter.name} inventory before crit test: {[i.name for i in test_crafter.inventory]}")
    # Ensure crafter has ingredients for many potions
    for _ in range(20):
        test_crafter.add_item_to_inventory(Item(name="Herb Bundle", description="Desc", base_value=5, item_type="component", quality="Common"))
        test_crafter.add_item_to_inventory(Item(name="Clean Water", description="Desc", base_value=1, item_type="component", quality="Common"))

    crit_success_count = 0
    crit_failure_count = 0
    normal_count = 0
    original_quality_tiers = [q_name for _, q_name in Shop.QUALITY_THRESHOLDS]

    for i in range(20): # Craft 20 potions to observe crits
        # Reset crafting experience for this item to get consistent base quality for testing observation
        # shop_in_whiterun.crafting_experience["Minor Healing Potion"] = 0
        crafted_potion = shop_in_whiterun.craft_item("Minor Healing Potion", test_crafter)
        if crafted_potion:
            base_quality_for_this_craft = shop_in_whiterun._determine_quality("Minor Healing Potion") # Recalc base for comparison
            base_idx = original_quality_tiers.index(base_quality_for_this_craft)
            final_idx = original_quality_tiers.index(crafted_potion.quality)

            if final_idx > base_idx : crit_success_count +=1
            elif final_idx < base_idx : crit_failure_count +=1
            else: normal_count +=1
            # print(f"  Crafted: {crafted_potion.name} (Quality: {crafted_potion.quality}, Base: {base_quality_for_this_craft})")
    print(f"Crit Successes: {crit_success_count}/20")
    print(f"Crit Failures: {crit_failure_count}/20")
    print(f"Normal Successes: {normal_count}/20")
    shop_in_whiterun.display_inventory()
    # Reset chances if they were changed for testing
    # Shop.CRITICAL_SUCCESS_CHANCE = 0.05
    # Shop.CRITICAL_FAILURE_CHANCE = 0.05

    print("\n--- Reputation Test (Selling High Quality/Specialized Items) ---")
    # Ensure shop is Blacksmith and has an advanced recipe item
    shop_in_whiterun.set_specialization("Blacksmith")
    # Craft a "Steel Sword" (advanced recipe for Blacksmith) and make it "Rare"
    # To guarantee "Rare", we might need to manipulate crafting_experience or quality directly for test
    shop_in_whiterun.crafting_experience["Steel Sword"] = 20 # Ensure it's high enough for Rare
    steel_ingot_rep_test = Item(name="Steel Ingot", description="Desc", base_value=25, item_type="component", quality="Common"); steel_ingot_rep_test.quantity = 3; test_crafter.add_item_to_inventory(steel_ingot_rep_test)
    oak_wood_rep_test = Item(name="Oak Wood", description="Desc", base_value=8, item_type="component", quality="Common"); oak_wood_rep_test.quantity = 1; test_crafter.add_item_to_inventory(oak_wood_rep_test)

    # Temporarily set crit chances to 0 to ensure predictable quality for this specific test item
    _orig_crit_s = Shop.CRITICAL_SUCCESS_CHANCE
    _orig_crit_f = Shop.CRITICAL_FAILURE_CHANCE
    Shop.CRITICAL_SUCCESS_CHANCE = 0.0
    Shop.CRITICAL_FAILURE_CHANCE = 0.0

    steel_sword = shop_in_whiterun.craft_item("Steel Sword", test_crafter)
    Shop.CRITICAL_SUCCESS_CHANCE = _orig_crit_s # Restore
    Shop.CRITICAL_FAILURE_CHANCE = _orig_crit_f # Restore

    if steel_sword:
        print(f"Crafted for reputation test: {steel_sword}")
        shop_in_whiterun.display_inventory()
        initial_reputation = shop_in_whiterun.reputation
        print(f"Reputation before sale: {initial_reputation}")
        # Simulate NPC buying it
        sale_price = shop_in_whiterun.complete_sale_to_npc(steel_sword.name, quality_to_sell=steel_sword.quality, npc_offer_percentage=0.9)
        if sale_price > 0:
            print(f"Sold {steel_sword.name} to NPC for {sale_price}g.")
            print(f"Reputation after sale: {shop_in_whiterun.reputation}")
            assert shop_in_whiterun.reputation > initial_reputation
        else:
            print(f"Failed to sell {steel_sword.name} to NPC for reputation test.")
    else:
        print("Failed to craft Steel Sword for reputation test.")
    shop_in_whiterun.display_inventory()


    print("\n--- Crafting Test (Greater Healing Potion - Wrong Specialization) ---")
    # Shop is Blacksmith, trying to craft Alchemist recipe
    print(f"{test_crafter.name} inventory before Greater Healing Potion: {[i.name for i in test_crafter.inventory]}")
    # Add ingredients for potion to test can_craft correctly
    test_crafter.add_item_to_inventory(Item(name="Concentrated Herbs", description="Desc", base_value=15, item_type="component", quality="Common"))
    test_crafter.add_item_to_inventory(Item(name="Concentrated Herbs", description="Desc", base_value=15, item_type="component", quality="Common"))
    test_crafter.add_item_to_inventory(Item(name="Purified Water", description="Desc", base_value=5, item_type="component", quality="Common"))
    test_crafter.add_item_to_inventory(Item(name="Crystal Vial", description="Desc", base_value=10, item_type="component", quality="Common"))

    if shop_in_whiterun.can_craft("Greater Healing Potion"):
        crafted_g_potion = shop_in_whiterun.craft_item("Greater Healing Potion", test_crafter)
        if crafted_g_potion:
            print(f"Successfully crafted: {crafted_g_potion.name} (Quality: {crafted_g_potion.quality})")
        else:
            print(f"Failed to craft Greater Healing Potion (craft_item stage).")
    else:
        print(f"Cannot craft Greater Healing Potion: Recipe not available for {shop_in_whiterun.specialization} specialization.")
    shop_in_whiterun.display_inventory() # Should not have the potion
    print(f"{test_crafter.name} inventory after Greater Healing Potion attempt: {[i.name for i in test_crafter.inventory]}")


    print("\n--- Crafting Test (Leather Scraps) - No Rawhide ---")
    # Attempt to craft Leather Scraps - should fail as Test Crafter has no Rawhide
    crafted_scraps = shop_in_whiterun.craft_item("Leather Scraps", test_crafter)
    if crafted_scraps:
        print(f"Successfully crafted: {crafted_scraps.name}")
        test_crafter.add_item_to_inventory(crafted_scraps) # Manually add to crafter for next step if it was shop stock
    else:
        print(f"Failed to craft Leather Scraps.")

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
