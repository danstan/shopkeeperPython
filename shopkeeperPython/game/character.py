import random
from .item import Item # Assuming item.py is in the same directory
# To avoid circular import for type hinting if Shop is imported here,
# we can use a string literal for Shop type hint or import it under TYPE_CHECKING.
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .shop import Shop

import datetime # Added for timestamping journal entries

# Helper function for stat rolling (4d6 drop lowest)
def _roll_4d6_drop_lowest():
    rolls = [random.randint(1, 6) for _ in range(4)]
    rolls.sort()
    return sum(rolls[1:])

EXHAUSTION_EFFECTS = {
    0: "No effect",
    1: "Disadvantage on Ability Checks",
    2: "Speed halved",
    3: "Disadvantage on Attack rolls and Saving Throws",
    4: "Hit point maximum halved",
    5: "Speed reduced to 0",
    6: "Death"
}


class JournalEntry:
    def __init__(self, timestamp: datetime.datetime, action_type: str, summary: str, details: str = None, outcome: str = None):
        self.timestamp = timestamp
        self.action_type = action_type
        self.summary = summary
        self.details = details
        self.outcome = outcome

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "action_type": self.action_type,
            "summary": self.summary,
            "details": self.details,
            "outcome": self.outcome,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'JournalEntry':
        return cls(
            timestamp=datetime.datetime.fromisoformat(data["timestamp"]),
            action_type=data["action_type"],
            summary=data["summary"],
            details=data.get("details"),
            outcome=data.get("outcome"),
        )


class Character:
    LEVEL_XP_THRESHOLDS = { 1: 0, 2: 300, 3: 900, 4: 2700, 5: 6500 }

    STAT_NAMES = ["STR", "DEX", "CON", "INT", "WIS", "CHA"]

    ATTRIBUTE_DEFINITIONS = {
        "Acrobatics": "DEX",
        "Animal Handling": "WIS",
        "Arcana": "INT",
        "Athletics": "STR",
        "Deception": "CHA",
        "History": "INT",
        "Insight": "WIS",
        "Intimidation": "CHA",
        "Investigation": "INT",
        "Medicine": "WIS",
        "Nature": "INT",
        "Perception": "WIS",
        "Performance": "CHA",
        "Persuasion": "CHA",
        "Religion": "INT",
        "Sleight of Hand": "DEX",
        "Stealth": "DEX",
        "Survival": "WIS",
    }

    def __init__(self, name: str = None):
        self.name = name # Can be None initially if using interactive creation
        self.stats = {stat: 0 for stat in self.STAT_NAMES}
        self.attributes = {} # Initialize attributes dictionary
        self.stat_bonuses = {stat: 0 for stat in self.STAT_NAMES}
        self.ac_bonus = 0
        self.level = 1
        self.max_hit_dice = self.level # Character starts at level 1
        self.hit_dice = self.max_hit_dice # Starts with all hit dice available
        self.xp = 0
        self.pending_xp = 0
        self.base_max_hp = 0
        self.hp = 0

        self.attunement_slots = 3
        self.attuned_items = []
        self.exhaustion_level = 0 # Ensure this is initialized
        self.inventory = []
        self.gold = 100
        self.skill_points_to_allocate = 0
        self.speed = 30
        self.is_dead = False # Added for perma-death
        self.current_town_name = "Starting Village" # Initialize current town name
        self.journal = []  # Initialize journal for storing JournalEntry objects
        self._recalculate_all_attributes()

    @property
    def max_hp(self):
        hp_val = self.base_max_hp
        if self.exhaustion_level >= 4:
            hp_val = self.base_max_hp // 2
        return hp_val

    def get_effective_max_hp(self) -> int:
        return self.max_hp

    def get_effective_speed(self) -> int:
        if self.exhaustion_level >= 5: return 0
        elif self.exhaustion_level >= 2: return self.speed // 2
        return self.speed

    def get_effective_stat(self, stat_name: str) -> int:
        return self.stats.get(stat_name, 0) + self.stat_bonuses.get(stat_name, 0)

    def _calculate_modifier(self, stat_score: int, is_base_stat_score: bool = False, stat_name_for_effective: str = "CON") -> int:
        if is_base_stat_score: return (stat_score - 10) // 2
        return (self.get_effective_stat(stat_name_for_effective) - 10) // 2

    @staticmethod
    def roll_single_stat() -> int:
        """Rolls 4d6 and returns the sum of the highest 3 dice."""
        return _roll_4d6_drop_lowest()

    @staticmethod
    def roll_all_stats() -> dict:
        """Calls roll_single_stat() for all stats and returns a dictionary."""
        return {stat: Character.roll_single_stat() for stat in Character.STAT_NAMES}

    @staticmethod
    def reroll_single_stat() -> int:
        """Calls _roll_4d6_drop_lowest() to roll a single stat."""
        return _roll_4d6_drop_lowest()

    def roll_stats(self):

        con_modifier = self._calculate_modifier(self.stats["CON"], is_base_stat_score=True)
        # Ensure level is at least 1 for this calculation if called early
        current_level = self.level if self.level > 0 else 1
        self.base_max_hp = 10 + (con_modifier * current_level)
        self.hp = self.get_effective_max_hp()
        self._recalculate_all_attributes()

    def award_xp(self, amount: int) -> int:
        if amount == 0: return 0
        if amount < 0:
            print(f"{self.name} loses {-amount} XP directly.")
            self.xp += amount
            # Basic de-level check (simplified)
            while self.xp < self.LEVEL_XP_THRESHOLDS.get(self.level, 0) and self.level > 1:
                self.level -=1
                self.max_hit_dice = self.level # Recalculate max_hit_dice
                self.hit_dice = min(self.hit_dice, self.max_hit_dice)
                print(f"{self.name} de-leveled to Level {self.level}. Max Hit Dice: {self.max_hit_dice}.")
            return amount # Return negative amount for tracking if needed
        self.pending_xp += amount
        print(f"{self.name} is due to gain {amount} XP at end of day. Total pending: {self.pending_xp}")
        return amount

    def commit_pending_xp(self) -> int:
        if self.pending_xp <= 0: return 0
        amount_committed = self.pending_xp
        self.xp += self.pending_xp
        print(f"{self.name} officially gains {self.pending_xp} XP. Total XP: {self.xp}")
        self.pending_xp = 0
        self._check_level_up()
        return amount_committed

    def _check_level_up(self):
        # De-leveling check (if XP significantly lost before commit)
        while self.xp < self.LEVEL_XP_THRESHOLDS.get(self.level, 0) and self.level > 1:
            print(f"{self.name} has fallen below the XP threshold for Level {self.level}!")
            self.level -=1
            self.max_hit_dice = self.level
            self.hit_dice = min(self.hit_dice, self.max_hit_dice)
            # TODO: Reduce base_max_hp appropriately based on previous level's gain. This is complex.
            # For now, HP will be capped by get_effective_max_hp() if base_max_hp isn't reduced.
            print(f"{self.name} de-leveled to Level {self.level}. Max Hit Dice: {self.max_hit_dice}.")

        # Level up check
        next_level_threshold_xp = self.LEVEL_XP_THRESHOLDS.get(self.level + 1, float('inf'))
        while self.xp >= next_level_threshold_xp:
            self.level += 1
            print(f"{self.name} leveled up to Level {self.level}!")
            self.max_hit_dice = self.level
            self.hit_dice = min(self.hit_dice + 1, self.max_hit_dice) # Gain 1 HD, cap at new max
            con_modifier = self._calculate_modifier(self.stats["CON"], is_base_stat_score=True)

            print(f"{self.name} has {self.skill_points_to_allocate} skill point(s) to allocate.")
            next_level_threshold_xp = self.LEVEL_XP_THRESHOLDS.get(self.level + 1, float('inf'))

    def gain_exhaustion(self, amount: int = 1):
        if amount <= 0: return
        old_level = self.exhaustion_level
        self.exhaustion_level += amount
        self.exhaustion_level = min(self.exhaustion_level, 6) # Cap at 6

        if self.exhaustion_level > old_level:
            print(f"  {self.name} gains {amount} level(s) of exhaustion. New level: {self.exhaustion_level} ({self.get_exhaustion_effects()})")
            if self.exhaustion_level >= 4 and old_level < 4: # HP max halved effect
                self.hp = min(self.hp, self.get_effective_max_hp()) # Adjust current HP if it exceeds new max
                print(f"  HP maximum now {self.get_effective_max_hp()}. Current HP adjusted to {self.hp}.")
            if self.exhaustion_level >= 6 and not self.is_dead : # Check not already dead to print message once
                self.is_dead = True
                self.hp = 0 # Explicitly set HP to 0 on death
                print(f"  {self.name} has succumbed to their ailments and is now dead.")
        elif self.exhaustion_level == old_level and self.exhaustion_level < 6 and amount > 0 and not self.is_dead:
             print(f"  {self.name}'s exhaustion level remains {self.exhaustion_level} ({self.get_exhaustion_effects()}). No effective change from this event, though gain was attempted.")
        # No message if already at 6 and trying to add more, as it's capped.

    def get_exhaustion_effects(self) -> str:
        return EXHAUSTION_EFFECTS.get(self.exhaustion_level, "Unknown exhaustion level.")

    def take_short_rest(self, hit_dice_to_spend: int) -> int:
        if hit_dice_to_spend <= 0: print("Must spend at least one hit die."); return 0
        if hit_dice_to_spend > self.hit_dice: print(f"Cannot spend {hit_dice_to_spend} HD, only {self.hit_dice} available."); return 0
        total_healed = 0; con_mod = self._calculate_modifier(self.stats["CON"], is_base_stat_score=True)
        print(f"{self.name} takes short rest, spending {hit_dice_to_spend} HD (CON mod: {con_mod}).")
        for i in range(hit_dice_to_spend):
            roll = random.randint(1,8); healed_this_die = max(0, roll + con_mod); old_hp = self.hp
            self.hp = min(self.get_effective_max_hp(), self.hp + healed_this_die)
            actual_healed = self.hp - old_hp; total_healed += actual_healed
            print(f"  HD {i+1}: Rolled {roll}+{con_mod}={healed_this_die}. Healed {actual_healed} HP. HP: {self.hp}/{self.get_effective_max_hp()}")
        self.hit_dice -= hit_dice_to_spend
        print(f"Total HP recovered: {total_healed}. HD left: {self.hit_dice}/{self.max_hit_dice}"); return total_healed

    def attempt_long_rest(self, food_available: bool = True, drink_available: bool = True, hours_of_rest: int = 8, interruption_chance: float = 0.1) -> dict:
        print(f"\n{self.name} attempts a long rest...")
        if hours_of_rest < 8: msg = "Not enough time for a full long rest."; print(msg); return {"success": False, "message": msg}
        if random.random() < interruption_chance:
            msg = "Long rest interrupted!"; print(msg)
            if not food_available or not drink_available: self.gain_exhaustion(1)
            return {"success": False, "message": msg, "interrupted": True}
        if not food_available or not drink_available:
            self.gain_exhaustion(1); msg = "Long rest failed: no food/drink. Gained 1 exhaustion."; print(msg)
            return {"success": False, "message": msg}
        # Successful long rest benefits should be applied here before returning
        self.hp = self.get_effective_max_hp()
        self.hit_dice = min(self.max_hit_dice, self.hit_dice + max(1, self.max_hit_dice // 2))
        if self.exhaustion_level > 0:
            self.exhaustion_level -=1 # Reduce exhaustion by 1 on a successful long rest
            print(f"  {self.name} feels less exhausted. New level: {self.exhaustion_level} ({self.get_exhaustion_effects()})")
        else: # Already at 0 exhaustion
             pass # No change, no message needed unless specific "well rested" buff applies

        # Placeholder for other D&D 5e long rest rules like spell slot recovery
        print(f"  {self.name} completed a long rest. HP restored. Hit Dice recovered. Exhaustion reduced.")
        return {"success": True, "message": "Long rest completed successfully."}

    def heal_hp(self, amount_to_heal: int) -> int:
        if amount_to_heal <= 0:
            return 0

        old_hp = self.hp
        self.hp = min(self.get_effective_max_hp(), self.hp + amount_to_heal)
        healed_amount = self.hp - old_hp

        if healed_amount > 0:
            # Optional: print a message here if desired, or let the caller handle it.
            # print(f"{self.name} healed for {healed_amount} HP. Current HP: {self.hp}/{self.get_effective_max_hp()}")
            pass
        return healed_amount

    def add_item_to_inventory(self, item: Item):
        # Ensure the item being added has a quantity, default to 1 if not specified
        if not hasattr(item, 'quantity'):
            item.quantity = 1

        for existing_item in self.inventory:
            if existing_item.name == item.name and existing_item.quality == item.quality:
                # Ensure existing_item also has quantity, though it should if added by this method
                if not hasattr(existing_item, 'quantity'):
                    existing_item.quantity = 0 # Should not happen if items are consistently managed
                existing_item.quantity += item.quantity
                print(f"Stacked {item.quantity}x {item.name} ({item.quality}) in {self.name}'s inventory. New total: {existing_item.quantity}.")
                return

        # If no stackable item found, add as new item
        self.inventory.append(item)
        print(f"{item.name} (Qty: {item.quantity}, Quality: {item.quality}) added as new stack to {self.name}'s inventory.")

    def remove_item_from_inventory(self, item_name: str) -> Item | None:
        for item in self.inventory:
            if item.name == item_name: self.inventory.remove(item); print(f"{item_name} removed (first found)."); return item
        return None
    def remove_specific_item_from_inventory(self, item_instance: Item) -> bool:
        if item_instance in self.inventory: self.inventory.remove(item_instance); return True
        return False

    def _apply_item_effects(self, item: Item):
        if not item.is_magical: return
        print(f"Applying effects from {item.name}...")
        for type, val in item.effects.items():
            if type=="stat_bonus":
                for stat,bonus in val.items(): self.stat_bonuses[stat]=self.stat_bonuses.get(stat,0)+bonus; print(f"  {stat}+{bonus}. New bonus: {self.stat_bonuses[stat]}. Effective: {self.get_effective_stat(stat)}")
            elif type=="ac_bonus": self.ac_bonus+=val; print(f"  AC+{val}. New AC bonus: {self.ac_bonus}")
    def _remove_item_effects(self, item: Item):
        if not item.is_magical: return
        print(f"Removing effects from {item.name}...")
        for type, val in item.effects.items():
            if type=="stat_bonus":
                for stat,bonus in val.items(): self.stat_bonuses[stat]=self.stat_bonuses.get(stat,0)-bonus; print(f"  {stat}-{bonus}. New bonus: {self.stat_bonuses[stat]}. Effective: {self.get_effective_stat(stat)}")
            elif type=="ac_bonus": self.ac_bonus-=val; print(f"  AC-{val}. New AC bonus: {self.ac_bonus}")
    def reapply_attuned_item_effects(self):
        self.stat_bonuses = {stat: 0 for stat in self.stats} # Reset all bonuses
        self.ac_bonus = 0
        print(f"Reapplying effects for {self.name}'s attuned items...")
        for item in self.attuned_items: self._apply_item_effects(item)
        self._recalculate_all_attributes()

    def attune_item(self, item_name: str) -> bool:
        item_to_attune=next((i for i in self.inventory if i.name==item_name),None)
        if not item_to_attune: print(f"Cannot attune: {item_name} not in inventory."); return False
        if not item_to_attune.is_magical or not item_to_attune.is_attunement: print(f"Cannot attune: {item_name} not magical/attunement."); return False
        if item_to_attune in self.attuned_items: print(f"Cannot attune: {item_name} already attuned."); return False
        if len(self.attuned_items) >= self.attunement_slots: print(f"Cannot attune: No slots left."); return False
        if self.remove_specific_item_from_inventory(item_to_attune):
            self.attuned_items.append(item_to_attune); self._apply_item_effects(item_to_attune)
            print(f"{item_name} successfully attuned."); return True
        print(f"Error: Could not remove {item_name} from inventory for attunement."); return False
    def unattune_item(self, item_name: str) -> bool:
        item_to_unattune=next((i for i in self.attuned_items if i.name==item_name),None)
        if not item_to_unattune: print(f"Cannot unattune: {item_name} not attuned."); return False
        self._remove_item_effects(item_to_unattune); self.attuned_items.remove(item_to_unattune)
        self.add_item_to_inventory(item_to_unattune); print(f"{item_name} successfully unattuned."); return True
    def use_consumable_item(self, item_name: str) -> bool:
        item_to_use=next((i for i in self.inventory if i.name==item_name),None)
        if not item_to_use: print(f"Cannot use: {item_name} not in inventory."); return False
        if not item_to_use.is_consumable: print(f"Cannot use: {item_name} not consumable."); return False
        print(f"{self.name} uses {item_name}!");
        for type,val in item_to_use.effects.items():
            if type=="heal_hp": old_hp=self.hp; self.hp=min(self.get_effective_max_hp(),self.hp+val); print(f"  Healed {self.hp-old_hp} HP. HP: {self.hp}/{self.get_effective_max_hp()}")
            elif type=="restore_hit_dice": old_hd=self.hit_dice; self.hit_dice=min(self.max_hit_dice,self.hit_dice+val); print(f"  Restored {self.hit_dice-old_hd} HD. HD: {self.hit_dice}/{self.max_hit_dice}")
            elif type=="cast_spell": print(f"  {self.name} casts {val}!")
        if not self.remove_specific_item_from_inventory(item_to_use): print(f"CRITICAL: Failed to remove consumed {item_name}.")
        print(f"{item_name} consumed."); return True

    def display_character_info(self):
        print(f"\n--- Character: {self.name} ---")
        print(f"Level: {self.level}, XP: {self.xp} (Pending: {self.pending_xp})")
        print(f"HP: {self.hp}/{self.get_effective_max_hp()}, HD: {self.hit_dice}/{self.max_hit_dice}")
        print(f"Gold: {self.gold}")
        print(f"Exhaustion: {self.exhaustion_level} ({self.get_exhaustion_effects()})")
        print(f"Speed: {self.get_effective_speed()}")
        print(f"Base Stats: {self.stats}")
        print(f"Stat Bonuses: {self.stat_bonuses}")
        print(f"Effective Stats: {{'STR':{self.get_effective_stat('STR')}, 'DEX':{self.get_effective_stat('DEX')}, 'CON':{self.get_effective_stat('CON')}, 'INT':{self.get_effective_stat('INT')}, 'WIS':{self.get_effective_stat('WIS')}, 'CHA':{self.get_effective_stat('CHA')}}}")
        print("Attributes:")
        for attr_name in sorted(self.ATTRIBUTE_DEFINITIONS.keys()):
            score = self.get_attribute_score(attr_name)
            print(f"  {attr_name}: {score:+}") # {:+} ensures a sign (+ or -) is shown
        print(f"AC Bonus: {self.ac_bonus}")
        print(f"Attunement Slots Used: {len(self.attuned_items)}/{self.attunement_slots}")
        if self.attuned_items: print("Attuned Items:"); [print(f"  - {i.name} ({i.quality})") for i in self.attuned_items]
        else: print("Attuned Items: None")
        if self.inventory: print("Inventory:"); [print(f"  - {i.name} ({i.quality})") for i in self.inventory]
        else: print("Inventory: Empty")
        print("-------------------------")

    def buy_item_from_shop(self, item_name: str, quantity: int, shop: 'Shop') -> tuple[list[Item], int]:
        items_bought=[]; total_spent=0
        for i in range(quantity):
            item_instance, price = shop.sell_item_to_character(item_name, self)
            if item_instance: items_bought.append(item_instance); self.add_item_to_inventory(item_instance); total_spent+=price; print(f"  Bought {item_name} for {price}g. ({i+1}/{quantity}) Gold: {self.gold}")
            else: break
        if items_bought: print(f"{self.name} bought {len(items_bought)} of {item_name}(s) for {total_spent}g.")
        elif quantity>0: print(f"{self.name} failed to buy any '{item_name}'.")
        return items_bought, total_spent
    def sell_item_to_shop(self, item_to_sell: Item, shop: 'Shop') -> int:
        if item_to_sell not in self.inventory: print(f"  {self.name} doesn't have {item_to_sell.name}."); return 0
        price_paid = shop.buy_item_from_character(item_to_sell, self)
        if price_paid > 0:
            if self.remove_specific_item_from_inventory(item_to_sell): print(f"  {item_to_sell.name} sold. Gold: {self.gold}"); return price_paid
            else: print(f"  CRITICAL: Sold {item_to_sell.name}, but failed to remove from inventory!"); return price_paid
        return 0

    def has_items(self, items_to_check: dict) -> tuple[bool, dict]:
        """
        Checks if the character has enough of specified items in their inventory.

        Args:
            items_to_check: A dictionary like {"item_name": quantity, ...}.

        Returns:
            A tuple: (True, {}) if all items are present in sufficient quantities.
                     (False, missing_items) if any item is insufficient.
                     missing_items dictionary details what's lacking (e.g., {"Scrap Metal": 1}).
        """
        missing_items = {}
        for item_name, required_quantity in items_to_check.items():
            # Count items by name. This assumes items with the same name are stackable for crafting.
            # If specific Item instances matter (e.g. with different qualities), this logic would need adjustment.
            current_quantity = sum(item.quantity for item in self.inventory if item.name == item_name)
            if current_quantity < required_quantity:
                missing_items[item_name] = required_quantity - current_quantity

        if missing_items:
            return False, missing_items
        return True, {}

    def consume_items(self, items_to_consume: dict) -> bool:
        """
        Consumes specified items from the character's inventory.
        This method assumes has_items was called and returned True.

        Args:
            items_to_consume: A dictionary like {"item_name": quantity, ...}.

        Returns:
            True if consumption was successful, False otherwise.
        """
        # First, verify again (optional, but safer)
        can_consume, _ = self.has_items(items_to_consume)
        if not can_consume:
            # This case should ideally be prevented by a prior call to has_items
            print(f"CHARACTER: {self.name} cannot consume items due to insufficient quantities (checked before consumption).")
            return False

        for item_name, quantity_to_consume in items_to_consume.items():
            consumed_so_far = 0
            # Iterate backwards to safely remove items from the list
            for i in range(len(self.inventory) - 1, -1, -1):
                item_in_inventory = self.inventory[i]
                if item_in_inventory.name == item_name:
                    if item_in_inventory.quantity > (quantity_to_consume - consumed_so_far):
                        # Item stack has more than needed, reduce quantity
                        item_in_inventory.quantity -= (quantity_to_consume - consumed_so_far)
                        consumed_so_far = quantity_to_consume
                        break
                    else:
                        # Consume the whole stack (or what's left of it)
                        consumed_so_far += item_in_inventory.quantity
                        self.inventory.pop(i) # Remove the item stack
                if consumed_so_far >= quantity_to_consume:
                    break

            if consumed_so_far < quantity_to_consume:
                # This indicates an issue, as has_items should have caught this.
                # It might happen if items are not stackable and counts are off.
                print(f"CHARACTER: Error consuming {item_name} for {self.name}. Needed {quantity_to_consume}, consumed {consumed_so_far}. Inventory might be inconsistent.")
                # It might be necessary to roll back changes if a partial consumption is not acceptable.
                # For now, we'll return False and log the error.
                return False

        print(f"CHARACTER: {self.name} successfully consumed items: {items_to_consume}")
        return True

    def _perform_single_roll(self, skill_name: str, dc: int) -> dict:
        """Helper function to perform a single d20 roll with disadvantage if applicable."""
        if skill_name not in self.ATTRIBUTE_DEFINITIONS:
            # This case should ideally be caught before calling this internal helper
            print(f"Warning: Invalid attribute/skill '{skill_name}' for check.")
            return {
                "success": False, "d20_roll": 1, "modifier": 0, "total_value": 1, "dc": dc,
                "is_critical_hit": False, "is_critical_failure": True,
                "disadvantage_details": "Invalid skill", "reroll_details": None
            }

        roll1 = random.randint(1, 20)
        d20_final_roll = roll1
        disadvantage_details_str = ""

        if self.exhaustion_level >= 1:  # Disadvantage on ability checks
            roll2 = random.randint(1, 20)
            d20_final_roll = min(roll1, roll2)
            disadvantage_details_str = f"(rolled {roll1},{roll2} dis, took {d20_final_roll})"

        modifier_value = self.get_attribute_score(skill_name)
        total_check_value = d20_final_roll + modifier_value

        is_crit_hit = (d20_final_roll == 20)
        is_crit_fail = (d20_final_roll == 1)
        check_success = (total_check_value >= dc)

        # Critical success/failure rules (5e context: nat 20 usually auto-success on checks, nat 1 auto-fail)
        # For skill checks, this is often DM fiat, but we can implement it.
        # If a nat 20 + mod still fails DC, it's not a success unless house rule.
        # If a nat 1 + mod still meets DC, it's not a failure unless house rule.
        # For now, we'll stick to total_value vs DC for success, but report crits.

        print(f"  {self.name} {skill_name} check (DC {dc}). Roll: {d20_final_roll}{disadvantage_details_str} + {modifier_value} (Attribute Score) = {total_check_value}. {'Success' if check_success else 'Failure'}")

        return {
            "success": check_success,
            "d20_roll": d20_final_roll,
            "modifier": modifier_value,
            "total_value": total_check_value,
            "dc": dc,
            "is_critical_hit": is_crit_hit,
            "is_critical_failure": is_crit_fail,
            "disadvantage_details": disadvantage_details_str
        }

    def perform_skill_check(self, skill_name:str, dc:int, can_use_reroll_item:bool=True) -> dict:
        if skill_name not in self.ATTRIBUTE_DEFINITIONS:
            print(f"Warning: Invalid attribute/skill '{skill_name}' for check.")
            # Return a default failure structure
            return {
                "success": False, "d20_roll": 1, "modifier": 0, "total_value": 1, "dc": dc,
                "is_critical_hit": False, "is_critical_failure": True,
                "disadvantage_details": "Invalid skill", "reroll_details": None
            }

        initial_roll_result = self._perform_single_roll(skill_name, dc)

        # Prepare the final result structure, initially based on the first roll
        final_result = {**initial_roll_result, "reroll_details": None}

        if not initial_roll_result["success"] and can_use_reroll_item:
            # Check for reroll item, e.g., "Lucky Charm"
            # This assumes "Lucky Charm" or similar item would be identified by name.
            # A more robust system might use item tags or specific effect keys.
            reroll_item = next((i for i in self.inventory if "Lucky Charm" in i.name and i.effects.get("allow_reroll")), None)
            if reroll_item:
                print(f"  {self.name} has {reroll_item.name}! Using for reroll...")
                if reroll_item.is_consumable:
                    if self.remove_specific_item_from_inventory(reroll_item):
                        print(f"  {reroll_item.name} consumed.")
                    else:
                        # This should not happen if item was found.
                        print(f"  Error consuming {reroll_item.name}.")

                reroll_attempt_result = self._perform_single_roll(skill_name, dc)
                final_result["reroll_details"] = reroll_attempt_result

                # Update top-level keys to reflect the reroll's outcome
                final_result["success"] = reroll_attempt_result["success"]
                final_result["d20_roll"] = reroll_attempt_result["d20_roll"]
                final_result["modifier"] = reroll_attempt_result["modifier"] # Should be same
                final_result["total_value"] = reroll_attempt_result["total_value"]
                final_result["is_critical_hit"] = reroll_attempt_result["is_critical_hit"]
                final_result["is_critical_failure"] = reroll_attempt_result["is_critical_failure"]
                final_result["disadvantage_details"] = reroll_attempt_result["disadvantage_details"]
                # DC remains the same

        # Add skill_name and formatted_string to the final_result
        final_result["skill_name"] = skill_name

        # Construct the result string based on the final state of final_result
        # This ensures it reflects any rerolls.
        result_string_prefix = "SKILL CHECK"
        if final_result.get("reroll_details"):
            result_string_prefix = "SKILL CHECK (Rerolled)"

        final_formatted_string = (
            f"{result_string_prefix}: {skill_name} DC {final_result['dc']}. "
            f"Rolled {final_result['d20_roll']}{final_result['disadvantage_details']} + {final_result['modifier']} = {final_result['total_value']}. "
            f"{'Success' if final_result['success'] else 'Failure'}"
        )
        final_result["formatted_string"] = final_formatted_string

        # The existing print statement inside _perform_single_roll handles the initial roll's print.
        # If a reroll happened, and we want to print the final outcome string here as well:
        if final_result.get("reroll_details"):
            # This print is optional, as the formatted string is returned for display elsewhere.
            # print(f"  {final_formatted_string}") # Or self._print if available
            pass

        return final_result

    def to_dict(self, current_town_name: str = None) -> dict:
        # If current_town_name is None, default to "Starting Village"
        town_name_to_save = current_town_name if current_town_name is not None else "Starting Village"
        return {
            "name": self.name,
            "stats": self.stats.copy(),
            "stat_bonuses": self.stat_bonuses.copy(),
            "ac_bonus": self.ac_bonus,
            "level": self.level,
            "xp": self.xp,
            "pending_xp": self.pending_xp,
            "base_max_hp": self.base_max_hp,
            "hp": self.hp,
            "hit_dice": self.hit_dice,
            "max_hit_dice": self.max_hit_dice,
            "attunement_slots": self.attunement_slots, # Though fixed, good to save
            "attuned_.items": [item.to_dict() for item in self.attuned_items],
            "exhaustion_level": self.exhaustion_level,
            "inventory": [item.to_dict() for item in self.inventory],
            "gold": self.gold,
            "skill_points_to_allocate": self.skill_points_to_allocate,
            "speed": self.speed,
            "is_dead": self.is_dead, # Added for perma-death
            "current_town_name": town_name_to_save,
            "journal": [entry.to_dict() for entry in self.journal], # Serialize journal entries
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Character':
        char = cls(data["name"])
        char.stats = data["stats"]
        char.stat_bonuses = data.get("stat_bonuses", {key: 0 for key in char.stats})
        char.ac_bonus = data.get("ac_bonus", 0)
        char.level = data["level"]
        char.xp = data["xp"]
        char.pending_xp = data.get("pending_xp", 0)
        char.base_max_hp = data["base_max_hp"]
        char.hp = data["hp"]
        char.max_hit_dice = data.get("max_hit_dice", char.level)
        char.hit_dice = data["hit_dice"]
        char.attunement_slots = data.get("attunement_slots", 3)
        char.inventory = [Item.from_dict(item_data) for item_data in data.get("inventory", [])]
        char.attuned_items = [Item.from_dict(item_data) for item_data in data.get("attuned_items", [])]
        char.exhaustion_level = data["exhaustion_level"]
        char.gold = data["gold"]
        char.skill_points_to_allocate = data.get("skill_points_to_allocate", 0)
        char.speed = data.get("speed", 30)
        char.is_dead = data.get("is_dead", False) # Added for perma-death
        # Load current_town_name, defaulting if not found (e.g., older save files)
        char.current_town_name = data.get("current_town_name", "Starting Village")

        # Load journal entries
        journal_data = data.get("journal", [])
        if journal_data: # Check if journal data exists
            char.journal = [JournalEntry.from_dict(entry_data) for entry_data in journal_data]
        else:
            char.journal = [] # Default to empty list if no journal data

        # If character is dead, ensure HP is 0.
        if char.is_dead:
            char.hp = 0
        else: # Ensure HP is capped by current effective max HP after loading exhaustion
            char.hp = min(char.hp, char.get_effective_max_hp())

        char._recalculate_all_attributes() # Recalculate attributes after loading all data
        return char

    # --- Attribute Calculation Methods ---
    def _calculate_attribute_score(self, attribute_name: str) -> int:
        """
        Calculates the score for a single attribute based on its primary stat.
        """
        primary_stat_name = self.ATTRIBUTE_DEFINITIONS.get(attribute_name)
        if not primary_stat_name:
            print(f"Warning: Attribute '{attribute_name}' not found in ATTRIBUTE_DEFINITIONS.")
            return 0 # Should not happen if called from _recalculate_all_attributes

        effective_stat_score = self.get_effective_stat(primary_stat_name)
        # Use is_base_stat_score=True because get_effective_stat already provides the raw score
        # that _calculate_modifier expects when is_base_stat_score is True.
        return self._calculate_modifier(effective_stat_score, is_base_stat_score=True)

    def get_attribute_score(self, attribute_name: str) -> int:
        """
        Retrieves the pre-calculated score for an attribute.
        """
        score = self.attributes.get(attribute_name)
        if score is None:
            print(f"Warning: Attribute '{attribute_name}' not found or not calculated. Returning 0.")
            return 0
        return score

    def _recalculate_all_attributes(self):
        """
        Recalculates all attribute scores and stores them in self.attributes.
        """
        # print(f"DEBUG: Recalculating all attributes for {self.name}...") # Optional debug line
        for attr_name in self.ATTRIBUTE_DEFINITIONS.keys():
            self.attributes[attr_name] = self._calculate_attribute_score(attr_name)
        # print(f"DEBUG: Attributes for {self.name}: {self.attributes}") # Optional debug line


if __name__ == "__main__":
    pass
