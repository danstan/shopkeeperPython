import random
from .item import Item # Assuming item.py is in the same directory
# To avoid circular import for type hinting if Shop is imported here,
# we can use a string literal for Shop type hint or import it under TYPE_CHECKING.
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .shop import Shop

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

class Character:
    """
    Represents a character in the Shopkeeper Python game.
    """
    LEVEL_XP_THRESHOLDS = {
        1: 0,
        2: 300,
        3: 900,
        4: 2700,
        5: 6500,
    }

    STAT_NAMES = ["STR", "DEX", "CON", "INT", "WIS", "CHA"]

    def __init__(self, name: str = None):
        self.name = name # Can be None initially if using interactive creation
        self.stats = {stat: 0 for stat in self.STAT_NAMES}
        self.stat_bonuses = {stat: 0 for stat in self.STAT_NAMES}
        self.ac_bonus = 0
        self.level = 1
        self.xp = 0
        self.pending_xp = 0 # For GDD: "XP is collected... officially awarded during End-Of-Day Recap"
        self.base_max_hp = 0
        self.hp = 0
        self.hit_dice = 1 # Will be set based on level
        self.max_hit_dice = 1 # Will be set based on level
        self.attunement_slots = 3
        self.attuned_items = []
        self.exhaustion_level = 0
        self.inventory = []
        self.gold = 100
        self.skill_points_to_allocate = 0
        self.speed = 30

    @property
    def max_hp(self):
        hp = self.base_max_hp
        if self.exhaustion_level >= 4:
            hp = self.base_max_hp // 2
        return hp

    def get_effective_max_hp(self) -> int:
        return self.max_hp

    def get_effective_speed(self) -> int:
        if self.exhaustion_level >= 5:
            return 0
        elif self.exhaustion_level >= 2:
            return self.speed // 2
        return self.speed

    def get_effective_stat(self, stat_name: str) -> int:
        return self.stats.get(stat_name, 0) + self.stat_bonuses.get(stat_name, 0)

    def _calculate_modifier(self, stat_score: int, is_base_stat_score: bool = False, stat_name_for_effective: str = "CON") -> int:
        if is_base_stat_score:
            return (stat_score - 10) // 2
        return (self.get_effective_stat(stat_name_for_effective) - 10) // 2

    @staticmethod
    def roll_single_stat() -> int:
        """Rolls 4d6 and returns the sum of the highest 3 dice."""
        return _roll_4d6_drop_lowest()

    @staticmethod
    def roll_all_stats() -> dict:
        """Calls roll_single_stat() for all stats and returns a dictionary."""
        return {stat: Character.roll_single_stat() for stat in Character.STAT_NAMES}

    def roll_stats(self):
        """
        Original method to roll stats. Can be used for NPCs or non-interactive creation.
        Calculates HP based on rolled stats and current level.
        """
        for stat in self.STAT_NAMES:
            self.stats[stat] = Character.roll_single_stat()

        con_modifier = self._calculate_modifier(self.stats["CON"], is_base_stat_score=True)
        # Ensure level is at least 1 for this calculation if called early
        current_level = self.level if self.level > 0 else 1
        self.base_max_hp = 10 + (con_modifier * current_level)
        self.hp = self.get_effective_max_hp()
        self.hit_dice = current_level
        self.max_hit_dice = current_level

        if self.name: # Avoid printing if name is not set yet (e.g. during interactive setup)
            print(f"{self.name} rolled stats: {self.stats}")
            print(f"Initial HP: {self.hp}/{self.get_effective_max_hp()}")

    def prompt_for_name(self):
        """Asks the user to input a character name and sets self.name."""
        while not self.name or self.name.strip() == "":
            try:
                self.name = input("Enter your character's name: ").strip()
                if not self.name:
                    print("Name cannot be empty. Please try again.")
            except EOFError: # Handle cases where input might be piped or unavailable
                print("No input received for name. Defaulting to 'Adventurer'.")
                self.name = "Adventurer"
                break
        print(f"Character name set to: {self.name}")

    def prompt_for_stats(self):
        """
        Handles interactive stat rolling for the player.
        Allows one reroll. Sets chosen stats and calculates HP.
        """
        print(f"\n--- {self.name}, let's roll your stats! ---")
        print("You will roll 4 six-sided dice (4d6) for each stat, and the lowest die is dropped.")

        current_stats = Character.roll_all_stats()
        while True:
            print("\nYour rolled stats are:")
            for stat, value in current_stats.items():
                print(f"  {stat}: {value}")

            valid_input = False
            while not valid_input:
                try:
                    choice = input("Do you want to keep these stats or reroll once? (keep/reroll): ").lower().strip()
                    if choice in ["keep", "reroll"]:
                        valid_input = True
                    else:
                        print("Invalid choice. Please type 'keep' or 'reroll'.")
                except EOFError:
                    print("No input received. Defaulting to 'keep'.")
                    choice = "keep" # Default to keep if no input
                    valid_input = True

            if choice == "keep":
                self.stats = current_stats
                break
            else: # Reroll
                print("\nRerolling stats (this is your only reroll!)...")
                current_stats = Character.roll_all_stats()
                print("\nYour new stats are:")
                for stat, value in current_stats.items():
                    print(f"  {stat}: {value}")
                self.stats = current_stats # This is the final set after the one reroll
                break

        print("\nStats finalized.")
        # Calculate HP and Hit Dice (assuming level 1 at creation)
        self.level = 1 # Ensure level is 1 for initial setup
        con_modifier = self._calculate_modifier(self.stats["CON"], is_base_stat_score=True)
        self.base_max_hp = 10 + con_modifier # For level 1: 10 + CON_modifier
        self.hp = self.get_effective_max_hp()
        self.hit_dice = self.level
        self.max_hit_dice = self.level
        print(f"Based on your CON of {self.stats['CON']} (modifier {con_modifier}), your HP is: {self.hp}/{self.get_effective_max_hp()}")
        print(f"You have {self.hit_dice} Hit Die (d8).")


    @classmethod
    def create_character_interactively(cls):
        """
        Creates a Character instance through interactive prompts for name and stats.
        """
        # Pass None for name to __init__ to signify interactive setup
        player = cls(name=None)

        player.prompt_for_name()
        player.prompt_for_stats() # This now sets level to 1, calculates HP, and sets HD

        print("\n--- Character Creation Complete! ---")
        player.display_character_info() # Display summary
        print("------------------------------------")
        return player

    def allocate_skill_point(self, skill_name: str) -> bool:
        """
        Allocates a skill point to the specified skill if available.
        """
        if self.skill_points_to_allocate <= 0:
            print(f"{self.name} has no skill points to allocate.")
            return False

        skill_to_increase = skill_name.upper() # Case-insensitive

        if skill_to_increase not in Character.STAT_NAMES:
            print(f"Invalid skill '{skill_name}'. Cannot allocate point.")
            return False

        self.stats[skill_to_increase] += 1
        self.skill_points_to_allocate -= 1

        print(f"{self.name} increased {skill_to_increase} by 1. New value: {self.stats[skill_to_increase]}.")
        print(f"{self.skill_points_to_allocate} skill point(s) remaining.")

        # HP recalculation is handled by _check_level_up when CON is involved in HP increase.
        # A direct CON increase here will affect future HP gains or CON-based checks,
        # but does not retroactively change HP from past levels or grant immediate extra HP
        # beyond what the level up itself provided.
        return True

    def award_xp(self, amount: int) -> int:
        """
        Awards XP to the character, which is held as pending until committed.
        Returns the amount of XP awarded.
        """
        if amount <= 0:
            if amount < 0: # Direct XP penalty/loss
                print(f"{self.name} loses {-amount} XP directly.")
                self.xp += amount # Subtract XP
                if self.xp < self.LEVEL_XP_THRESHOLDS.get(self.level, 0) and self.level > 1:
                    print(f"{self.name} might de-level (not implemented). Current XP {self.xp}")
                    # De-leveling logic could be complex, for now just reduces XP.
            return 0

        self.pending_xp += amount
        print(f"{self.name} is due to gain {amount} XP at end of day. Total pending: {self.pending_xp}")
        return amount

    def commit_pending_xp(self) -> int:
        """
        Commits all pending XP to the character's actual XP total and checks for level up.
        Returns the total amount of XP that was committed.
        """
        if self.pending_xp <= 0:
            return 0

        amount_committed = self.pending_xp
        self.xp += self.pending_xp
        print(f"{self.name} officially gains {self.pending_xp} XP. Total XP: {self.xp}")
        self.pending_xp = 0
        self._check_level_up() # Check level up AFTER official gain
        return amount_committed

    def _check_level_up(self):
        leveled_up_this_check = False
        # Check if current XP is less than current level's threshold (for de-leveling, if xp was lost)
        # This is a simplified de-leveling check. True de-leveling is complex.
        while self.xp < self.LEVEL_XP_THRESHOLDS.get(self.level, 0) and self.level > 1:
            print(f"{self.name} has fallen below the XP threshold for Level {self.level}!")
            # De-leveling logic: reduce level, stats, HP, etc. Not fully implemented.
            # For now, just reduce level and max_hit_dice. HP would need careful handling.
            self.level -=1
            self.max_hit_dice = self.level
            self.hit_dice = min(self.hit_dice, self.max_hit_dice) # Cap hit dice to new max
            print(f"{self.name} is now Level {self.level}. Max Hit Dice: {self.max_hit_dice}.")
            # Re-calculate base_max_hp based on new (lower) level.
            # This is complex as it should undo previous level's HP gain.
            # Simplified: just ensure HP is not over new max_hp if base_max_hp were to be reduced.
            # For now, not changing base_max_hp on de-level to avoid complexity.

        next_level_threshold = self.level + 1
        while self.xp >= self.LEVEL_XP_THRESHOLDS.get(next_level_threshold, float('inf')):
            self.level = next_level_threshold
            leveled_up_this_check = True
            print(f"{self.name} leveled up to Level {self.level}!")

            con_modifier = self._calculate_modifier(self.stats["CON"], is_base_stat_score=True)
            hp_increase_fixed = max(1, 6 + con_modifier)
            self.base_max_hp += hp_increase_fixed
            self.hp = self.get_effective_max_hp()

            self.max_hit_dice = self.level
            self.hit_dice = self.max_hit_dice

            self.skill_points_to_allocate += 1
            print(f"Max HP increased to {self.get_effective_max_hp()}. Hit dice restored to {self.hit_dice}.")
            print(f"{self.name} has {self.skill_points_to_allocate} skill point(s) to allocate.")
            next_level_threshold += 1


    def gain_exhaustion(self, amount: int = 1):
        if amount <= 0: return
        old_level = self.exhaustion_level
        self.exhaustion_level = min(self.exhaustion_level + amount, 6)
        print(f"{self.name} gains {amount} level(s) of exhaustion. Current level: {self.exhaustion_level} - {self.get_exhaustion_effects()}")

        if self.exhaustion_level >= 4 and old_level < 4:
            print(f"  Max HP is now halved. Current HP: {self.hp}/{self.get_effective_max_hp()}")
        self.hp = min(self.hp, self.get_effective_max_hp())

        if self.exhaustion_level >= 6:
            print(f"{self.name} has died from exhaustion!")

    def remove_exhaustion(self, amount: int = 1):
        if amount <= 0: return
        old_level = self.exhaustion_level
        self.exhaustion_level = max(0, self.exhaustion_level - amount)
        print(f"{self.name} removes {amount} level(s) of exhaustion. Current level: {self.exhaustion_level} - {self.get_exhaustion_effects()}")

        if old_level >= 4 and self.exhaustion_level < 4:
            self.hp = min(self.hp, self.get_effective_max_hp())
            print(f"  Max HP is no longer halved. Current HP: {self.hp}/{self.get_effective_max_hp()}")

    def get_exhaustion_effects(self) -> str:
        return EXHAUSTION_EFFECTS.get(self.exhaustion_level, "Unknown exhaustion level.")

    def take_short_rest(self, hit_dice_to_spend: int) -> int:
        if hit_dice_to_spend <= 0:
            print("Must spend at least one hit die.")
            return 0
        if hit_dice_to_spend > self.hit_dice:
            print(f"Cannot spend {hit_dice_to_spend} hit dice, only {self.hit_dice} available.")
            return 0
        total_healed = 0
        con_modifier = self._calculate_modifier(self.stats["CON"], is_base_stat_score=True)
        print(f"{self.name} takes a short rest, spending {hit_dice_to_spend} Hit Dice (CON mod: {con_modifier}).")
        for i in range(hit_dice_to_spend):
            roll = random.randint(1, 8)
            healed_this_die = max(0, roll + con_modifier)
            old_hp = self.hp
            self.hp = min(self.get_effective_max_hp(), self.hp + healed_this_die)
            actual_healed = self.hp - old_hp
            total_healed += actual_healed
            print(f"  Spent HD {i+1}: Rolled {roll} + {con_modifier} = {healed_this_die}. Healed {actual_healed} HP. Current HP: {self.hp}/{self.get_effective_max_hp()}")
        self.hit_dice -= hit_dice_to_spend
        print(f"Total HP recovered: {total_healed}. Remaining Hit Dice: {self.hit_dice}/{self.max_hit_dice}")
        return total_healed

    def attempt_long_rest(self, food_available: bool = True, drink_available: bool = True, hours_of_rest: int = 8, interruption_chance: float = 0.1) -> dict:
        print(f"\n{self.name} attempts a long rest...")
        if hours_of_rest < 8:
            msg = "Not enough time for a full long rest."
            print(msg)
            return {"success": False, "message": msg}
        if random.random() < interruption_chance:
            msg = "Long rest interrupted!"
            print(msg)
            if not food_available or not drink_available:
                self.gain_exhaustion(1)
            return {"success": False, "message": msg, "interrupted": True}
        if not food_available or not drink_available:
            self.gain_exhaustion(1)
            msg = "Long rest failed due to lack of food/drink. Gained 1 level of exhaustion."
            print(msg)
            return {"success": False, "message": msg}
        self.hp = self.get_effective_max_hp()
        self.hit_dice = self.max_hit_dice
        self.remove_exhaustion(1)
        msg = f"Long rest successful. HP fully restored to {self.hp}. All Hit Dice restored (now {self.hit_dice}/{self.max_hit_dice}). Exhaustion reduced."
        print(msg)
        return {"success": True, "message": msg}

    def add_item_to_inventory(self, item: Item):
        self.inventory.append(item)
        print(f"{item.name} added to {self.name}'s inventory.")

    def remove_item_from_inventory(self, item_name: str) -> Item | None:
        for item in self.inventory:
            if item.name == item_name:
                self.inventory.remove(item)
                print(f"{item.name} removed from {self.name}'s inventory (first found).")
                return item
        return None

    def remove_specific_item_from_inventory(self, item_instance: Item) -> bool:
        if item_instance in self.inventory:
            self.inventory.remove(item_instance)
            return True
        return False

    def _apply_item_effects(self, item: Item):
        if not item.is_magical: return
        print(f"Applying effects from {item.name}...")
        for effect_type, effect_value in item.effects.items():
            if effect_type == "stat_bonus":
                for stat, bonus in effect_value.items():
                    self.stat_bonuses[stat] = self.stat_bonuses.get(stat, 0) + bonus
                    print(f"  Applied {stat} +{bonus}. New bonus: {self.stat_bonuses[stat]}. Effective {stat}: {self.get_effective_stat(stat)}")
            elif effect_type == "ac_bonus":
                self.ac_bonus += effect_value
                print(f"  Applied AC +{effect_value}. New AC bonus: {self.ac_bonus}")

    def _remove_item_effects(self, item: Item):
        if not item.is_magical: return
        print(f"Removing effects from {item.name}...")
        for effect_type, effect_value in item.effects.items():
            if effect_type == "stat_bonus":
                for stat, bonus in effect_value.items():
                    self.stat_bonuses[stat] = self.stat_bonuses.get(stat, 0) - bonus
                    print(f"  Removed {stat} +{bonus}. New bonus: {self.stat_bonuses[stat]}. Effective {stat}: {self.get_effective_stat(stat)}")
            elif effect_type == "ac_bonus":
                self.ac_bonus -= effect_value
                print(f"  Removed AC +{effect_value}. New AC bonus: {self.ac_bonus}")

    def attune_item(self, item_name: str) -> bool:
        item_to_attune = None
        for item_in_inv in self.inventory:
            if item_in_inv.name == item_name:
                item_to_attune = item_in_inv
                break
        if not item_to_attune:
            print(f"Cannot attune: {item_name} not found in inventory.")
            return False
        if not item_to_attune.is_magical or not item_to_attune.is_attunement:
            print(f"Cannot attune: {item_name} is not a magical item requiring attunement.")
            return False
        if item_to_attune in self.attuned_items:
            print(f"Cannot attune: {item_name} is already attuned.")
            return False
        if len(self.attuned_items) >= self.attunement_slots:
            print(f"Cannot attune: No available attunement slots (Max: {self.attunement_slots}).")
            return False
        if self.remove_specific_item_from_inventory(item_to_attune):
            self.attuned_items.append(item_to_attune)
            self._apply_item_effects(item_to_attune)
            print(f"{item_name} successfully attuned.")
            return True
        else:
            print(f"Error: Could not remove {item_name} from inventory for attunement.")
            return False

    def unattune_item(self, item_name: str) -> bool:
        item_to_unattune = None
        for item_in_attuned in self.attuned_items:
            if item_in_attuned.name == item_name:
                item_to_unattune = item_in_attuned
                break
        if not item_to_unattune:
            print(f"Cannot unattune: {item_name} not currently attuned.")
            return False
        self._remove_item_effects(item_to_unattune)
        self.attuned_items.remove(item_to_unattune)
        self.add_item_to_inventory(item_to_unattune)
        print(f"{item_name} successfully unattuned.")
        return True

    def use_consumable_item(self, item_name: str) -> bool:
        item_to_use = None
        for item_in_inv in self.inventory:
            if item_in_inv.name == item_name:
                item_to_use = item_in_inv
                break
        if not item_to_use:
            print(f"Cannot use: {item_name} not found in inventory.")
            return False
        if not item_to_use.is_consumable:
            print(f"Cannot use: {item_name} is not a consumable item.")
            return False
        print(f"{self.name} uses {item_name}!")
        for effect_type, effect_value in item_to_use.effects.items():
            if effect_type == "heal_hp":
                old_hp = self.hp
                self.hp = min(self.get_effective_max_hp(), self.hp + effect_value)
                print(f"  Healed {self.hp - old_hp} HP. Current HP: {self.hp}/{self.get_effective_max_hp()}")
            elif effect_type == "restore_hit_dice":
                old_hd = self.hit_dice
                self.hit_dice = min(self.max_hit_dice, self.hit_dice + effect_value)
                print(f"  Restored {self.hit_dice - old_hd} Hit Dice. Current HD: {self.hit_dice}/{self.max_hit_dice}")
            elif effect_type == "cast_spell":
                print(f"  {self.name} begins casting {effect_value}!")
        if not self.remove_specific_item_from_inventory(item_to_use):
             print(f"CRITICAL: Failed to remove consumed item {item_name} from inventory.")
        print(f"{item_name} was consumed.")
        return True

    def display_character_info(self):
        print(f"\n--- Character: {self.name} ---")
        print(f"Level: {self.level}, XP: {self.xp} (Pending: {self.pending_xp})") # Show pending XP
        print(f"HP: {self.hp}/{self.get_effective_max_hp()}, HD: {self.hit_dice}/{self.max_hit_dice}")
        print(f"Gold: {self.gold}")
        print(f"Exhaustion: {self.exhaustion_level} ({self.get_exhaustion_effects()})")
        print(f"Speed: {self.get_effective_speed()}")
        print(f"Base Stats: {self.stats}")
        print(f"Stat Bonuses: {self.stat_bonuses}")
        print(f"Effective Stats: {{'STR': {self.get_effective_stat('STR')}, 'DEX': {self.get_effective_stat('DEX')}, "
              f"'CON': {self.get_effective_stat('CON')}, 'INT': {self.get_effective_stat('INT')}, "
              f"'WIS': {self.get_effective_stat('WIS')}, 'CHA': {self.get_effective_stat('CHA')}}}")
        print(f"AC Bonus: {self.ac_bonus}")
        print(f"Attunement Slots Used: {len(self.attuned_items)}/{self.attunement_slots}")
        if self.attuned_items:
            print("Attuned Items:")
            for item in self.attuned_items: print(f"  - {item.name} ({item.quality})")
        else: print("Attuned Items: None")
        if self.inventory:
            print("Inventory:")
            for item in self.inventory: print(f"  - {item.name} ({item.quality})")
        else: print("Inventory: Empty")
        print("-------------------------")

    def buy_item_from_shop(self, item_name: str, quantity: int, shop: 'Shop') -> tuple[list[Item], int]: # Return list of items and total cost
        print(f"\n{self.name} attempting to buy {quantity} x '{item_name}' from {shop.name}.")
        items_bought_successfully = []
        total_spent = 0
        for i in range(quantity):
            # Shop's sell_item_to_character should now return (item_instance, price)
            item_instance, price = shop.sell_item_to_character(item_name, self)

            if item_instance:
                self.add_item_to_inventory(item_instance)
                items_bought_successfully.append(item_instance)
                total_spent += price # Gold deduction is handled by shop method now
                print(f"  Successfully bought one {item_name} for {price}g. ({i+1}/{quantity}) Current gold: {self.gold}")
            else:
                # print(f"  Failed to buy {item_name} ({i+1}/{quantity}). Transaction stopped.") # Message from shop is enough
                break

        if items_bought_successfully:
            print(f"{self.name} successfully purchased {len(items_bought_successfully)} of {item_name}(s) for a total of {total_spent}g.")
        elif quantity > 0 :
             print(f"{self.name} failed to buy any '{item_name}'.")
        return items_bought_successfully, total_spent

    def sell_item_to_shop(self, item_to_sell: Item, shop: 'Shop') -> int: # Return gold_earned
        print(f"\n{self.name} attempting to sell '{item_to_sell.name}' (Quality: {item_to_sell.quality}, Value: {item_to_sell.value}) to {shop.name}.")
        if item_to_sell not in self.inventory:
            print(f"  {self.name} does not possess this specific item: {item_to_sell.name}.")
            return 0 # No gold earned

        # Shop's buy_item_from_character should return True/False and handle gold transfer
        # We need the price it paid to return it. Let's assume buy_item_from_character returns the price paid or 0.
        price_paid = shop.buy_item_from_character(item_to_sell, self)

        if price_paid > 0:
            if self.remove_specific_item_from_inventory(item_to_sell):
                # Gold is already added to character by shop.buy_item_from_character
                print(f"  Item '{item_to_sell.name}' sold and removed from {self.name}'s inventory. Current gold: {self.gold}")
                return price_paid
            else:
                print(f"  CRITICAL ERROR: Sold item {item_to_sell.name} to shop (got {price_paid}g), but failed to remove from character inventory!")
                # This is tricky. Character got gold, shop got item. But item still in char inv.
                # Simplest for now: let the gold transfer stand, but log error.
                return price_paid # Still earned gold, despite inventory error.
        else:
            # Shop declined or error in shop method. Message should come from shop.
            return 0


    def perform_skill_check(self, skill_name: str, dc: int, can_use_reroll_item: bool = True) -> bool:
        if skill_name not in self.stats:
            print(f"Warning: Invalid skill '{skill_name}' for skill check.")
            return False
        roll1 = random.randint(1, 20)
        d20_to_use = roll1
        disadvantage_roll_str = ""
        if self.exhaustion_level >= 1:
            roll2 = random.randint(1, 20)
            d20_to_use = min(roll1, roll2)
            disadvantage_roll_str = f" (rolled {roll1}, {roll2} with disadvantage, took {d20_to_use})"
        modifier = self._calculate_modifier(0, is_base_stat_score=False, stat_name_for_effective=skill_name)
        result = d20_to_use + modifier
        print(f"{self.name} attempts a {skill_name} check (DC {dc}). Rolled {d20_to_use}{disadvantage_roll_str} + {modifier} (from {self.get_effective_stat(skill_name)}) = {result}.")
        if result >= dc:
            print("  Skill check successful!")
            return True
        else:
            print("  Skill check failed.")
            if can_use_reroll_item:
                reroll_item_name = "Lucky Charm"
                reroll_item_instance = None
                for item_idx, item_in_inv in enumerate(self.inventory):
                    if item_in_inv.name == reroll_item_name and item_in_inv.effects.get("allow_reroll"):
                        reroll_item_instance = item_in_inv
                        break
                if reroll_item_instance:
                    print(f"  {self.name} has a {reroll_item_name}!")
                    print(f"  Using {reroll_item_name} for a reroll...")
                    if reroll_item_instance.is_consumable:
                        if self.remove_specific_item_from_inventory(reroll_item_instance):
                             print(f"  {reroll_item_name} was consumed.")
                        else: print(f"  Error: Could not consume {reroll_item_name} after use.")
                    d20_reroll1 = random.randint(1, 20)
                    d20_reroll_to_use = d20_reroll1
                    reroll_disadvantage_str = ""
                    if self.exhaustion_level >= 1:
                        d20_reroll2 = random.randint(1,20)
                        d20_reroll_to_use = min(d20_reroll1, d20_reroll2)
                        reroll_disadvantage_str = f" (rolled {d20_reroll1}, {d20_reroll2} with disadvantage, took {d20_reroll_to_use})"
                    new_result = d20_reroll_to_use + modifier
                    print(f"  Rerolled {d20_reroll_to_use}{reroll_disadvantage_str} + {modifier} (from {self.get_effective_stat(skill_name)}) = {new_result}.")
                    if new_result >= dc:
                        print("  Reroll successful!")
                        return True
                    else:
                        print("  Reroll failed.")
                        return False
            return False


if __name__ == "__main__":
    print("--- Character Class Unit Tests ---")

    # 1. Test Stat Rolling
    print("\n--- Testing Stat Rolling ---")
    for _ in range(20): # Run multiple times for roll_single_stat
        single_roll = Character.roll_single_stat()
        assert 3 <= single_roll <= 18, f"Single stat roll out of range (3-18): {single_roll}"
    print("roll_single_stat() appears to be within range [3, 18].")

    all_rolled_stats = Character.roll_all_stats()
    assert isinstance(all_rolled_stats, dict), "roll_all_stats() should return a dictionary."
    assert len(all_rolled_stats) == len(Character.STAT_NAMES), \
        f"roll_all_stats() should return a dictionary with {len(Character.STAT_NAMES)} stats."
    for stat_name in Character.STAT_NAMES:
        assert stat_name in all_rolled_stats, f"Stat {stat_name} missing in roll_all_stats()."
        stat_value = all_rolled_stats[stat_name]
        assert 3 <= stat_value <= 18, \
            f"Stat {stat_name} value out of range (3-18) in roll_all_stats(): {stat_value}"
    print("roll_all_stats() returns a valid dictionary of stats within range [3, 18].")

    # 2. Test Character Initialization (Non-Interactive Aspects)
    print("\n--- Testing Character Initialization (Non-Interactive) ---")
    test_char = Character(name="TestDummy")
    assert test_char.name == "TestDummy", "Character name not set correctly."
    assert test_char.level == 1, f"Initial level should be 1, got {test_char.level}"
    assert test_char.xp == 0, f"Initial XP should be 0, got {test_char.xp}"
    assert test_char.skill_points_to_allocate == 0, \
        f"Initial skill_points_to_allocate should be 0, got {test_char.skill_points_to_allocate}"

    test_char.roll_stats() # Non-interactive stat rolling
    assert test_char.hp > 0, "Character HP should be > 0 after roll_stats()"
    assert test_char.base_max_hp > 0, "Character base_max_hp should be > 0 after roll_stats()"
    assert test_char.max_hit_dice == test_char.level, \
        f"max_hit_dice ({test_char.max_hit_dice}) should match level ({test_char.level}) after roll_stats()"
    assert test_char.hit_dice == test_char.level, \
        f"hit_dice ({test_char.hit_dice}) should match level ({test_char.level}) after roll_stats()"
    print("Character initializes correctly with default values and roll_stats() sets HP & HD.")

    # 3. Test `award_xp` and `_check_level_up` for Granting Skill Points
    print("\n--- Testing XP Award and Level Up for Skill Points ---")
    level_test_char = Character(name="LevelUpLarry")
    initial_skill_points = level_test_char.skill_points_to_allocate

    xp_for_level_2 = Character.LEVEL_XP_THRESHOLDS[2]
    level_test_char.award_xp(xp_for_level_2)
    level_test_char.commit_pending_xp()

    assert level_test_char.level == 2, f"Character should be level 2, but is {level_test_char.level}"
    assert level_test_char.skill_points_to_allocate == initial_skill_points + 1, \
        f"Skill points should be {initial_skill_points + 1}, but got {level_test_char.skill_points_to_allocate}"
    print("Character levels up correctly and gains a skill point.")

    # 4. Test `allocate_skill_point` Method
    print("\n--- Testing allocate_skill_point Method ---")
    # Re-use level_test_char who should now have 1 skill point.
    assert level_test_char.skill_points_to_allocate == 1, \
        f"Expected 1 skill point for allocation test, got {level_test_char.skill_points_to_allocate}"

    original_str_value = level_test_char.stats["STR"]
    allocation_result_valid = level_test_char.allocate_skill_point("STR")
    assert allocation_result_valid is True, "allocate_skill_point('STR') should return True."
    assert level_test_char.stats["STR"] == original_str_value + 1, \
        f"STR should be {original_str_value + 1}, but is {level_test_char.stats['STR']}"
    assert level_test_char.skill_points_to_allocate == 0, \
        f"Skill points should be 0 after allocation, but got {level_test_char.skill_points_to_allocate}"
    print("Valid skill point allocation successful.")

    # Test allocation to an invalid skill
    original_dex_value = level_test_char.stats["DEX"] # Pick another stat for this check
    skill_points_before_invalid_alloc = level_test_char.skill_points_to_allocate # Should be 0

    allocation_result_invalid_skill = level_test_char.allocate_skill_point("INVALID_SKILL")
    assert allocation_result_invalid_skill is False, "allocate_skill_point('INVALID_SKILL') should return False."
    assert level_test_char.stats["DEX"] == original_dex_value, \
        "DEX should not change after attempting to allocate to an invalid skill."
    assert level_test_char.skill_points_to_allocate == skill_points_before_invalid_alloc, \
        "Skill points should not change after attempting to allocate to an invalid skill."
    print("Attempt to allocate to invalid skill handled correctly.")

    # Test allocation when no points are available
    assert level_test_char.skill_points_to_allocate == 0, \
        f"Ensuring no skill points before testing 'allocate when none available'. Has: {level_test_char.skill_points_to_allocate}"
    original_con_value = level_test_char.stats["CON"]
    allocation_result_no_points = level_test_char.allocate_skill_point("CON")
    assert allocation_result_no_points is False, "allocate_skill_point('CON') with 0 points should return False."
    assert level_test_char.stats["CON"] == original_con_value, \
        "CON should not change when attempting to allocate with no points."
    print("Attempt to allocate skill point with no points available handled correctly.")

    level_test_char.display_character_info() # Display final state for verification

    print("\n--- All Character.py Unit Tests Completed ---")
