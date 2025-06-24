import random
from .item import Item # Assuming item.py is in the same directory
from .backgrounds import BACKGROUND_DEFINITIONS # Added for backgrounds
from .feats import FEAT_DEFINITIONS # Added for feats
from .factions import FACTION_DEFINITIONS, get_faction_definition, get_rank_by_reputation # Added for factions
# To avoid circular import for type hinting if Shop is imported here,
# we can use a string literal for Shop type hint or import it under TYPE_CHECKING.
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .shop import Shop

import datetime # Added for timestamping journal entries
from typing import Optional # Add this import

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
    def __init__(self, timestamp: datetime.datetime, action_type: str, summary: str, details: Optional[dict] = None, outcome: Optional[str] = None):
        self.timestamp = timestamp
        self.action_type = action_type
        self.summary = summary
        self.details = details # Now correctly typed as Optional[dict]
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
    LEVEL_XP_THRESHOLDS = { 1: 0, 2: 300, 3: 900, 4: 2700, 5: 6500 } # XP needed to reach this level
    ASI_FEAT_LEVELS = {4, 8, 12, 16, 19} # Standard D&D 5e levels for ASI/Feat

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

    def __init__(self, name: str = None, background_id: str = None):
        self.name = name # Can be None initially if using interactive creation
        self.background_id = background_id
        self.appearance_data: dict = {}
        self.attribute_bonuses_from_background: dict = {}

        # Feat related initializations
        self.feats: list[str] = []
        self.feat_attribute_bonuses: dict = {}
        self.feat_stat_bonuses: dict = {}

        # Faction related initializations
        self.faction_reputations: dict = {} # E.g. {"merchants_guild": {"score": 0, "rank_name": "Applicant"}}

        # ASI/Feat choice pending flag
        self.pending_asi_feat_choice: bool = False

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
        self.gold = 100 # Default starting gold, can be modified by background
        self.skill_points_to_allocate = 0
        self.chosen_skill_bonuses: dict[str, int] = {} # E.g. {"Persuasion": 1, "Stealth": 2}
        self.speed = 30
        self.is_dead = False # Added for perma-death
        self.current_town_name = "Starting Village" # Initialize current town name
        self.journal = []  # Initialize journal for storing JournalEntry objects

        if self.background_id:
            background_def = next((bg for bg in BACKGROUND_DEFINITIONS if bg["id"] == self.background_id), None)
            if background_def:
                print(f"Applying background: {background_def['name']} for {self.name}")
                # Apply skill bonuses
                for skill_bonus_info in background_def.get("starting_skill_bonuses", []):
                    skill_name = skill_bonus_info["skill"]
                    bonus_amount = skill_bonus_info["bonus"]
                    self.attribute_bonuses_from_background[skill_name] = \
                        self.attribute_bonuses_from_background.get(skill_name, 0) + bonus_amount
                    print(f"  Applied +{bonus_amount} to {skill_name} from background.")

                # Grant starting items
                for item_info in background_def.get("starting_items", []):
                    # We need to create an Item instance.
                    # Assuming Item class can be instantiated from a dict similar to its to_dict structure,
                    # or has a constructor that takes these fields.
                    # For simplicity, we'll assume Item can be created with name, quantity, description, etc.
                    # If Item.from_dict is robust, it's better. Otherwise, direct instantiation.
                    # Let's try creating a dictionary that matches what Item.from_dict expects,
                    # or what the Item constructor expects.
                    item_data = {
                        "name": item_info["item_name"],
                        "quantity": item_info["quantity"],
                        "description": item_info.get("description", ""),
                        "base_value": item_info.get("base_value", 0),
                        "item_type": item_info.get("item_type", "unknown"),
                        "quality": item_info.get("quality", "Common"),
                        "is_magical": item_info.get("is_magical", False), # Default if not specified
                        "effects": item_info.get("effects", {}), # Default if not specified
                        # Add other fields Item might expect, e.g. is_attunement, is_consumable
                        "is_attunement": item_info.get("is_attunement", False),
                        "is_consumable": item_info.get("is_consumable", False),
                        "is_usable_in_combat": item_info.get("is_usable_in_combat", False),
                        "equip_slot": item_info.get("equip_slot", None),
                        "damage": item_info.get("damage", None),
                        "armor_class": item_info.get("armor_class", None),

                    }
                    # It's safer to use Item.from_dict if it can handle potentially missing keys
                    # by providing defaults, or if the item_info structure from backgrounds.py
                    # is guaranteed to match the Item class structure.
                    # For now, let's assume Item.from_dict can handle this:
                    try:
                        new_item = Item.from_dict(item_data)
                        new_item.quantity = item_info["quantity"] # Ensure quantity is set from background
                        self.add_item_to_inventory(new_item)
                        print(f"  Added starting item: {new_item.name} (Qty: {new_item.quantity})")
                    except Exception as e:
                        print(f"  Error creating starting item {item_info['item_name']}: {e}. Item not added.")


                # Add starting gold bonus
                gold_bonus = background_def.get("starting_gold_bonus", 0)
                self.gold += gold_bonus
                if gold_bonus != 0:
                    print(f"  Adjusted starting gold by {gold_bonus}. New total: {self.gold}")
            else:
                print(f"Warning: Background ID '{self.background_id}' not found in BACKGROUND_DEFINITIONS.")

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
        base_stat = self.stats.get(stat_name, 0)
        item_bonus = self.stat_bonuses.get(stat_name, 0) # Bonuses from items
        feat_bonus = self.feat_stat_bonuses.get(stat_name, 0) # Bonuses from feats
        return base_stat + item_bonus + feat_bonus

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

            # HP increase on level up (e.g. roll a hit die + CON mod, or average)
            # For simplicity, let's add a fixed amount + CON mod, or just re-evaluate based on new level for now
            # If roll_stats() is called, it recalculates base_max_hp based on current level and CON.
            # This seems reasonable for level ups.
            # However, roll_stats() also sets HP to max. We might want to just increase max_hp.
            # Let's assume a fixed HP gain per level + CON modifier for now (e.g. 5 + CON_mod for a d8 HD class)
            # Or, more simply, ensure base_max_hp reflects the new level.
            # The existing self.roll_stats() does: self.base_max_hp = 10 + (con_modifier * current_level)
            # This implies a d8 hit die (average 4.5, so 5) + CON, with 10 as a base for level 1 (5+CON + 5 extra).
            # This is a bit different from typical 5e. Let's stick to recalculating with existing formula for now.

            old_max_hp = self.get_effective_max_hp()
            con_modifier = self._calculate_modifier(self.stats["CON"], is_base_stat_score=True) # Assuming direct stat access for this calculation
            self.base_max_hp = 10 + (con_modifier * self.level) # Recalculate base_max_hp for new level
            hp_gained_this_level = self.get_effective_max_hp() - old_max_hp
            self.hp += hp_gained_this_level # Add the HP gained to current HP
            self.hp = min(self.hp, self.get_effective_max_hp()) # Ensure it doesn't exceed new max

            print(f"  {self.name} gained {hp_gained_this_level} HP. Max HP is now {self.get_effective_max_hp()}.")

            if self.level in self.ASI_FEAT_LEVELS:
                self.pending_asi_feat_choice = True
                print(f"  {self.name} has an Ability Score Improvement or Feat choice available!")
                # Skill points are not allocated on ASI/Feat levels
            else:
                self.skill_points_to_allocate += 1 # Standard per GDD for non-ASI levels
                print(f"  {self.name} gained 1 skill point. Total skill points to allocate: {self.skill_points_to_allocate}.")

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
        if hours_of_rest < 8:
            msg = "Not enough time for a full long rest."
            print(msg)
            # No exhaustion gain here, just not enough time.
            return {"success": False, "message": msg, "conditions_met": False, "hours_rested": hours_of_rest}

        if not food_available or not drink_available:
            self.gain_exhaustion(1) # Still gain exhaustion if attempting full rest without supplies
            missing_supplies = []
            if not food_available: missing_supplies.append("Food")
            if not drink_available: missing_supplies.append("Drink")
            msg = f"Long rest conditions not met: missing {', '.join(missing_supplies)}. Gained 1 exhaustion."
            print(msg)
            return {"success": False, "message": msg, "conditions_met": False, "hours_rested": hours_of_rest}

        # Conditions met (food, drink, time), rest can proceed pending interruptions (handled by GameManager)
        # Benefits are NOT applied here anymore. They will be applied by a separate method
        # called by GameManager if no interruption occurs or if an event outcome allows it.
        print(f"  {self.name} settles down for a long rest. Basic conditions (food/drink/time) are met.")
        return {"success": True, "message": "Basic conditions for long rest met. Awaiting completion or interruption.", "conditions_met": True, "hours_rested": hours_of_rest}

    def apply_long_rest_benefits(self, rest_quality: str = "successful"):
        """
        Applies the mechanical benefits of a long rest, potentially modified by an interruption event's outcome.
        Called by GameManager after event resolution or if no event occurred.
        """
        print(f"  {self.name} is concluding their long rest. Outcome quality: '{rest_quality}'.")

        if rest_quality == "failed":
            print(f"  Rest was a failure. No benefits gained. Exhaustion may have increased from event.")
            # Exhaustion gain from the event itself would be handled by the event outcome.
            # If 'failed' means specifically due to sickness event, exhaustion is already applied.
            return

        if rest_quality == "poor": # e.g., minor item loss, very disturbed
            # Partial HD recovery, no exhaustion removal, maybe only partial HP
            self.hp = min(self.get_effective_max_hp(), self.hp + (self.get_effective_max_hp() - self.hp) // 2) # Recover half of missing HP
            recovered_hd = max(1, self.max_hit_dice // 4) # Recover 1/4 HD (min 1)
            self.hit_dice = min(self.max_hit_dice, self.hit_dice + recovered_hd)
            print(f"  Rest was poor. HP partially restored to {self.hp}. Recovered {recovered_hd} HD. No exhaustion relief.")
            return

        if rest_quality == "partial": # Disturbed, but some benefit
            self.hp = min(self.get_effective_max_hp(), self.hp + (self.get_effective_max_hp() - self.hp) * 3 // 4) # Recover 3/4 of missing HP
            recovered_hd = max(1, self.max_hit_dice // 3) # Recover 1/3 HD (min 1)
            self.hit_dice = min(self.max_hit_dice, self.hit_dice + recovered_hd)
            # No exhaustion removal for partial rest, or maybe 1 level if very generous and event didn't add any.
            # For now, no exhaustion removal on partial.
            print(f"  Rest was partial. HP significantly restored to {self.hp}. Recovered {recovered_hd} HD. No exhaustion relief.")
            return

        # "successful" or "mostly_successful" (full benefits)
        self.hp = self.get_effective_max_hp()
        # D&D 5e: recover half of total HD (max_hit_dice), min 1.
        recovered_hd = max(1, self.max_hit_dice // 2)
        self.hit_dice = min(self.max_hit_dice, self.hit_dice + recovered_hd)

        exhaustion_removed_this_rest = 0
        if self.exhaustion_level > 0:
            self.exhaustion_level -= 1
            exhaustion_removed_this_rest = 1
            print(f"  {self.name} feels less exhausted. New level: {self.exhaustion_level} ({self.get_exhaustion_effects()})")
        else:
            pass # No exhaustion to remove.

        # Placeholder for other D&D 5e long rest rules like spell slot recovery
        print(f"  {self.name} completed a {'mostly successful' if rest_quality == 'mostly_successful' else 'successful'} long rest.")
        print(f"  HP fully restored to {self.hp}. Recovered {recovered_hd} HD (Total: {self.hit_dice}/{self.max_hit_dice}). Exhaustion reduced by {exhaustion_removed_this_rest}.")


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

        # Handle quantity
        if item_to_use.quantity > 1:
            item_to_use.quantity -= 1
            print(f"  Used one {item_name}. Quantity remaining: {item_to_use.quantity}.")
        elif item_to_use.quantity == 1:
            if not self.remove_specific_item_from_inventory(item_to_use): # Removes the item instance
                print(f"CRITICAL: Failed to remove consumed {item_name} (quantity 1) from inventory.")
                # Potentially roll back effects or handle error state if removal fails critically
            else:
                print(f"  Consumed the last {item_name}.")
        else: # quantity <= 0, should not happen if item management is correct
            print(f"Warning: Attempted to use {item_name} with quantity {item_to_use.quantity}. Item not properly removed or state error.")
            # Still return True if effects were applied, but log this issue.

        return True

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
            "attuned_items": [item.to_dict() for item in self.attuned_items],
            "exhaustion_level": self.exhaustion_level,
            "inventory": [item.to_dict() for item in self.inventory],
            "gold": self.gold,
            "skill_points_to_allocate": self.skill_points_to_allocate,
            "speed": self.speed,
            "is_dead": self.is_dead, # Added for perma-death
            "current_town_name": town_name_to_save,
            "journal": [entry.to_dict() for entry in self.journal], # Serialize journal entries
            "background_id": self.background_id,
            "appearance_data": self.appearance_data,
            "attribute_bonuses_from_background": self.attribute_bonuses_from_background,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Character':
        # Background_id must be passed to constructor before other things are set up
        # if it influences starting items/gold, which it does.
        # However, the current __init__ applies background effects if background_id is present.
        # So, we pass it during cls instantiation.
        char = cls(name=data["name"], background_id=data.get("background_id"))

        # Restore other attributes after basic initialization
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
        char.current_town_name = data.get("current_town_name", "Starting Village")

        # Load background related fields, providing defaults for older saves
        # background_id is already handled by constructor.
        char.appearance_data = data.get("appearance_data", {})
        # attribute_bonuses_from_background might have been partially populated by __init__
        # if background_id was present. If loading from save, this saved version should take precedence.
        char.attribute_bonuses_from_background = data.get("attribute_bonuses_from_background", {})

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

    def to_dict(self, current_town_name: str = None, current_time_data: dict = None) -> dict:
        # If current_town_name is None, default to "Starting Village"
        town_name_to_save = current_town_name if current_town_name is not None else "Starting Village"
        data = {
            "name": self.name,
            "stats": self.stats.copy(),
            "stat_bonuses": self.stat_bonuses.copy(), # Item stat bonuses
            "ac_bonus": self.ac_bonus,
            "level": self.level,
            "xp": self.xp,
            "pending_xp": self.pending_xp,
            "base_max_hp": self.base_max_hp,
            "hp": self.hp,
            "hit_dice": self.hit_dice,
            "max_hit_dice": self.max_hit_dice,
            "attunement_slots": self.attunement_slots,
            "attuned_items": [item.to_dict() for item in self.attuned_items],
            "exhaustion_level": self.exhaustion_level,
            "inventory": [item.to_dict() for item in self.inventory],
            "gold": self.gold,
            "skill_points_to_allocate": self.skill_points_to_allocate,
            "speed": self.speed,
            "is_dead": self.is_dead,
            "current_town_name": town_name_to_save,
            "journal": [entry.to_dict() for entry in self.journal],
            "background_id": self.background_id,
            "appearance_data": self.appearance_data,
            "attribute_bonuses_from_background": self.attribute_bonuses_from_background,
            "feats": self.feats,
            "feat_attribute_bonuses": self.feat_attribute_bonuses,
            "feat_stat_bonuses": self.feat_stat_bonuses,
            "faction_reputations": self.faction_reputations,
            "pending_asi_feat_choice": self.pending_asi_feat_choice,
            "chosen_skill_bonuses": self.chosen_skill_bonuses.copy(),
        }
        if current_time_data is not None:
            data["game_time_snapshot"] = current_time_data
        return data

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
        base_score = self.attributes.get(attribute_name, 0) # From stat modifier
        background_bonus = self.attribute_bonuses_from_background.get(attribute_name, 0)
        feat_bonus = self.feat_attribute_bonuses.get(attribute_name, 0) # Bonus directly to the attribute/skill
        chosen_skill_bonus = self.chosen_skill_bonuses.get(attribute_name, 0) # Bonus from allocated skill points
        final_score = base_score + background_bonus + feat_bonus + chosen_skill_bonus

        # This print can be very verbose, consider removing or conditionalizing it
        # print(f"DEBUG: get_attribute_score for {attribute_name}: Base={base_score}, BgBonus={background_bonus}, FeatBonus={feat_bonus}, ChosenBonus={chosen_skill_bonus}, Final={final_score}")

        return final_score

    def _recalculate_all_attributes(self):
        """
        Recalculates all attribute scores and stores them in self.attributes.
        """
        # print(f"DEBUG: Recalculating all attributes for {self.name}...") # Optional debug line
        for attr_name in self.ATTRIBUTE_DEFINITIONS.keys():
            self.attributes[attr_name] = self._calculate_attribute_score(attr_name)
        # print(f"DEBUG: Attributes for {self.name}: {self.attributes}") # Optional debug line

    # --- Feat Methods ---
    def apply_feat_effects(self, feat_id: str):
        """
        Applies the effects of a given feat to the character.
        This method is primarily called when a new feat is added.
        It handles direct, one-time changes like base_max_hp_bonus.
        Attribute and stat bonuses are stored in their respective dictionaries
        and are incorporated via get_attribute_score and get_effective_stat.
        """
        feat_def = next((f for f in FEAT_DEFINITIONS if f["id"] == feat_id), None)
        if not feat_def:
            print(f"Warning: Feat ID '{feat_id}' not found in FEAT_DEFINITIONS. No effects applied.")
            return

        print(f"Applying effects for feat: {feat_def['name']} for {self.name}")
        recalculate_attributes = False
        recalculate_stats_dependent = False

        for effect in feat_def.get("effects", []):
            effect_type = effect.get("type")
            value = effect.get("value")

            if effect_type == "base_max_hp_bonus":
                old_max_hp = self.get_effective_max_hp()
                self.base_max_hp += value
                print(f"  Increased base_max_hp by {value}. New base_max_hp: {self.base_max_hp}")
                # Ensure current HP is updated correctly relative to new max HP
                new_max_hp = self.get_effective_max_hp()
                if self.hp == old_max_hp or self.is_dead: # If at full HP (before bonus) or dead, set to new max (or more if previously above new max for some reason)
                    self.hp = new_max_hp
                elif self.hp > 0 : # If damaged, add the bonus HP directly
                    self.hp += (new_max_hp - old_max_hp)

                self.hp = min(self.hp, new_max_hp) # Cap at new max_hp
                if self.is_dead and new_max_hp > 0 : # If was dead but gained HP, no longer dead (though might be at 0 HP)
                    # This doesn't automatically revive, just means max HP is > 0
                    # Actual revival logic is separate.
                    pass


            elif effect_type == "attribute_bonus":
                attribute_name = effect.get("attribute")
                if attribute_name in self.ATTRIBUTE_DEFINITIONS:
                    self.feat_attribute_bonuses[attribute_name] = \
                        self.feat_attribute_bonuses.get(attribute_name, 0) + value
                    print(f"  Applied +{value} to {attribute_name} from feat {feat_id}.")
                    recalculate_attributes = True
                else:
                    print(f"  Warning: Unknown attribute '{attribute_name}' in feat {feat_id}. Effect not applied.")

            elif effect_type == "stat_bonus":
                stat_name = effect.get("stat")
                if stat_name in self.STAT_NAMES:
                    self.feat_stat_bonuses[stat_name] = \
                        self.feat_stat_bonuses.get(stat_name, 0) + value
                    print(f"  Applied +{value} to {stat_name} from feat {feat_id}.")
                    # Recalculating attributes is necessary as they depend on stats
                    recalculate_attributes = True
                    recalculate_stats_dependent = True # To indicate CON dependent things like HP might change.
                else:
                    print(f"  Warning: Unknown stat '{stat_name}' in feat {feat_id}. Effect not applied.")
            else:
                print(f"  Warning: Unknown effect type '{effect_type}' in feat {feat_id}. Effect not applied.")

        if recalculate_attributes: # This implies stats might have changed too
            self._recalculate_all_attributes()
            # If CON changed, max HP might need update (handled by _recalculate_all_attributes if it updates HP)
            # Base max HP is set during roll_stats or by specific bonuses.
            # Let's ensure HP is correctly capped after stat changes.
            # self.roll_stats() might be too much here as it re-rolls HP.
            # A specific call to update HP based on new CON might be needed if not covered.
            # For now, assume _recalculate_all_attributes followed by ensuring HP is capped is enough.
            # If a stat bonus (especially CON) was applied, ensure HP reflects this.
            # self.base_max_hp might need adjustment if a CON score changed, then self.hp.
            # The current roll_stats sets base_max_hp = 10 + (con_modifier * current_level).
            # If a feat changes CON, this should be updated.

            # If CON changed due to a feat, re-evaluate base_max_hp based on the new CON modifier
            if recalculate_stats_dependent and "CON" in self.feat_stat_bonuses: # Check if CON was directly affected
                old_max_hp = self.get_effective_max_hp()
                con_modifier = self._calculate_modifier(self.get_effective_stat("CON")) # Modifier from new effective CON
                # This formula for base_max_hp assumes it's primarily from CON and level.
                # If other sources (like 'tough' feat) also modify base_max_hp, this needs care.
                # The 'tough' feat directly adds to self.base_max_hp.
                # So, we only update the part of base_max_hp derived from CON and level.
                # This is tricky. Let's assume base_max_hp is a sum of initial roll + tough_bonus + con_level_bonus.
                # A simpler model: roll_stats() initializes base_max_hp. Feats add to it.
                # If CON stat changes, then the CON-derived portion of HP should change.
                # This might mean re-evaluating con_modifier * self.level part.
                # For now, direct base_max_hp bonuses are additive. Changes to CON
                # will be reflected via get_effective_stat -> _calculate_modifier -> _recalculate_all_attributes.
                # The max_hp property will then use the new base_max_hp.
                # The current _recalculate_all_attributes does not re-evaluate base_max_hp.
                # This needs to be handled.
                # A simpler approach for now: stat bonuses affect skills/modifiers. HP changes from specific HP feats.
                # Let's assume for now that `_recalculate_all_attributes` handles implications of stat changes on skills.
                # Direct HP effects are separate.
                pass # Rely on _recalculate_all_attributes for skill updates. Max HP via property.

            self.hp = min(self.hp, self.get_effective_max_hp()) # Ensure current HP is capped.


    def add_feat(self, feat_id: str) -> bool:
        """Adds a feat to the character if valid and not already present."""
        feat_def = next((f for f in FEAT_DEFINITIONS if f["id"] == feat_id), None)
        if not feat_def:
            print(f"Error: Feat ID '{feat_id}' is not a valid feat definition.")
            return False
        if feat_id in self.feats:
            print(f"Info: Character {self.name} already has feat '{feat_id}'.")
            return False

        self.feats.append(feat_id)
        print(f"Feat '{feat_def['name']}' added to {self.name}.")
        self.apply_feat_effects(feat_id)
        return True

    def has_feat(self, feat_id: str) -> bool:
        """Checks if the character has a specific feat."""
        return feat_id in self.feats

    def to_dict(self, current_town_name: str = None, current_time_data: dict = None) -> dict:
        # If current_town_name is None, default to "Starting Village"
        town_name_to_save = current_town_name if current_town_name is not None else "Starting Village"
        data = {
            "name": self.name,
            "stats": self.stats.copy(),
            "stat_bonuses": self.stat_bonuses.copy(), # Item stat bonuses
            "ac_bonus": self.ac_bonus,
            "level": self.level,
            "xp": self.xp,
            "pending_xp": self.pending_xp,
            "base_max_hp": self.base_max_hp,
            "hp": self.hp,
            "hit_dice": self.hit_dice,
            "max_hit_dice": self.max_hit_dice,
            "attunement_slots": self.attunement_slots,
            "attuned_items": [item.to_dict() for item in self.attuned_items],
            "exhaustion_level": self.exhaustion_level,
            "inventory": [item.to_dict() for item in self.inventory],
            "gold": self.gold,
            "skill_points_to_allocate": self.skill_points_to_allocate,
            "speed": self.speed,
            "is_dead": self.is_dead,
            "current_town_name": town_name_to_save,
            "journal": [entry.to_dict() for entry in self.journal],
            "background_id": self.background_id,
            "appearance_data": self.appearance_data,
            "attribute_bonuses_from_background": self.attribute_bonuses_from_background,
            "feats": self.feats,
            "feat_attribute_bonuses": self.feat_attribute_bonuses,
            "feat_stat_bonuses": self.feat_stat_bonuses,
            "faction_reputations": self.faction_reputations,
            "pending_asi_feat_choice": self.pending_asi_feat_choice,
        }
        if current_time_data is not None:
            data["game_time_snapshot"] = current_time_data
        return data

    @classmethod
    def from_dict(cls, data: dict) -> 'Character':
        char = cls(name=data["name"], background_id=data.get("background_id"))

        char.stats = data["stats"]
        char.stat_bonuses = data.get("stat_bonuses", {key: 0 for key in char.stats})
        char.ac_bonus = data.get("ac_bonus", 0)
        char.level = data["level"]
        char.xp = data["xp"]
        char.pending_xp = data.get("pending_xp", 0)
        # base_max_hp is loaded directly, assumed to be correct from save.
        # apply_feat_effects is NOT called on load for base_max_hp to avoid double addition.
        char.base_max_hp = data["base_max_hp"]
        char.hp = data["hp"]
        char.max_hit_dice = data.get("max_hit_dice", char.level)
        char.hit_dice = data["hit_dice"]
        char.attunement_slots = data.get("attunement_slots", 3)
        char.inventory = [Item.from_dict(item_data) for item_data in data.get("inventory", [])]
        # Ensuring from_dict uses the same corrected key as to_dict will use.
        char.attuned_items = [Item.from_dict(item_data) for item_data in data.get("attuned_items", [])]
        char.exhaustion_level = data["exhaustion_level"]
        char.gold = data["gold"]
        char.skill_points_to_allocate = data.get("skill_points_to_allocate", 0)
        char.speed = data.get("speed", 30)
        char.is_dead = data.get("is_dead", False)
        char.current_town_name = data.get("current_town_name", "Starting Village")

        char.appearance_data = data.get("appearance_data", {})
        char.attribute_bonuses_from_background = data.get("attribute_bonuses_from_background", {})

        # Load feat data
        char.feats = data.get("feats", [])
        char.feat_attribute_bonuses = data.get("feat_attribute_bonuses", {})
        char.feat_stat_bonuses = data.get("feat_stat_bonuses", {})
        # Note: We are NOT calling apply_feat_effects here for feats loaded from save.
        # The assumption is that their effects (like base_max_hp, attribute bonuses, stat bonuses)
        char.faction_reputations = data.get("faction_reputations", {})

        # Load journal entries
        # are already correctly stored in base_max_hp, feat_attribute_bonuses, and feat_stat_bonuses respectively.
        # This is important to prevent issues like double-adding HP bonuses.
        char.pending_asi_feat_choice = data.get("pending_asi_feat_choice", False)
        char.chosen_skill_bonuses = data.get("chosen_skill_bonuses", {}) # Load chosen skill bonuses

        # Load game time snapshot
        char.loaded_game_time_data = data.get("game_time_snapshot", None) # Store it on the character instance

        journal_data = data.get("journal", [])
        if journal_data:
            char.journal = [JournalEntry.from_dict(entry_data) for entry_data in journal_data]
        else:
            char.journal = []

        if char.is_dead:
            char.hp = 0
        else:
            char.hp = min(char.hp, char.get_effective_max_hp())

        char._recalculate_all_attributes()
        return char

    # --- Skill Point Allocation Method ---
    def allocate_skill_point(self, skill_name: str) -> bool:
        """
        Allocates a skill point to the specified skill.
        """
        if self.skill_points_to_allocate <= 0:
            print(f"Error: {self.name} has no skill points to allocate.")
            return False

        if skill_name not in self.ATTRIBUTE_DEFINITIONS:
            print(f"Error: '{skill_name}' is not a valid skill.")
            return False

        self.chosen_skill_bonuses[skill_name] = self.chosen_skill_bonuses.get(skill_name, 0) + 1
        self.skill_points_to_allocate -= 1
        print(f"{self.name} allocated 1 skill point to {skill_name}. New bonus: {self.chosen_skill_bonuses[skill_name]}. Points remaining: {self.skill_points_to_allocate}.")
        # No need to call _recalculate_all_attributes here, as get_attribute_score directly uses chosen_skill_bonuses.
        return True

    # --- ASI/Feat Choice Methods ---
    def set_pending_asi_feat_choice(self, status: bool):
        """Sets or clears the pending ASI/Feat choice flag."""
        self.pending_asi_feat_choice = status
        if not status:
            print(f"ASI/Feat choice for {self.name} has been made or deferred.")

    def apply_stat_increase_choice(self, stat_primary: str, points_primary: int, stat_secondary: str = None, points_secondary: int = 0) -> bool:
        """Applies an ability score increase choice."""
        if not self.pending_asi_feat_choice:
            print(f"Error: No ASI/Feat choice is currently pending for {self.name}.")
            return False

        valid_points_config = (points_primary == 2 and points_secondary == 0 and not stat_secondary) or \
                              (points_primary == 1 and points_secondary == 1 and stat_secondary and stat_primary != stat_secondary) or \
                              (points_primary == 1 and points_secondary == 0 and not stat_secondary) # Single +1 option

        if not valid_points_config:
            print("Error: Invalid ASI point distribution. Choose +2 to one stat, or +1 to two different stats, or +1 to one stat.")
            return False

        if stat_primary not in self.STAT_NAMES or (stat_secondary and stat_secondary not in self.STAT_NAMES):
            print(f"Error: Invalid stat name provided. Valid stats are: {self.STAT_NAMES}")
            return False

        # Check 20 cap (common 5e rule, can be adjusted)
        MAX_STAT_VALUE = 20 # Can be made a class constant
        can_apply_primary = (self.stats.get(stat_primary, 0) + points_primary) <= MAX_STAT_VALUE
        can_apply_secondary = not stat_secondary or (self.stats.get(stat_secondary, 0) + points_secondary) <= MAX_STAT_VALUE

        if not can_apply_primary or not can_apply_secondary:
            print(f"Error: Stat increase would exceed cap of {MAX_STAT_VALUE}.")
            return False

        # Apply changes
        # Store old CON modifier before applying stat changes to accurately calculate HP delta
        old_con_mod = self._calculate_modifier(self.stats.get("CON", 0), is_base_stat_score=True)

        # Apply changes
        self.stats[stat_primary] = self.stats.get(stat_primary, 0) + points_primary
        print(f"  {stat_primary} increased by {points_primary} to {self.stats[stat_primary]}.")

        if stat_secondary and points_secondary > 0:
            self.stats[stat_secondary] = self.stats.get(stat_secondary, 0) + points_secondary
            print(f"  {stat_secondary} increased by {points_secondary} to {self.stats[stat_secondary]}.")

        self._recalculate_all_attributes() # Updates attribute modifiers based on new stats

        # Check if CON was one of the stats that changed
        new_con_mod = self._calculate_modifier(self.stats.get("CON", 0), is_base_stat_score=True)
        con_mod_changed = (new_con_mod != old_con_mod)

        if con_mod_changed:
            # Calculate the HP change based *only* on the change in CON modifier
            # Each point of CON modifier adds self.level HP to max HP.
            hp_change_from_con_mod_increase = (new_con_mod - old_con_mod) * self.level

            self.base_max_hp += hp_change_from_con_mod_increase
            self.hp += hp_change_from_con_mod_increase # Also increase current HP by the same amount
            self.hp = min(self.hp, self.get_effective_max_hp()) # Ensure current HP doesn't exceed new max
            print(f"  Max HP updated by {hp_change_from_con_mod_increase} due to CON change. New Max HP: {self.get_effective_max_hp()}.")

        self.reapply_attuned_item_effects() # If other stats affect items or if CON change has other implications handled here

        self.set_pending_asi_feat_choice(False)
        print(f"  {self.name} applied Ability Score Increases.")
        return True

    def apply_feat_choice(self, feat_id: str) -> bool:
        """Applies a feat choice."""
        if not self.pending_asi_feat_choice:
            print(f"Error: No ASI/Feat choice is currently pending for {self.name}.")
            return False

        if self.add_feat(feat_id): # add_feat already prints messages and applies effects
            self.set_pending_asi_feat_choice(False)
            print(f"  {self.name} chose feat: {feat_id}.")
            return True
        else:
            # add_feat would print why it failed (e.g., already has feat, invalid feat)
            return False

    # --- Faction Methods ---
    def get_faction_data(self, faction_id: str) -> dict | None:
        """Returns the specific faction's definition from FACTION_DEFINITIONS."""
        return get_faction_definition(faction_id)

    def get_faction_reputation_details(self, faction_id: str) -> dict | None:
        """Returns the character's reputation entry for a specific faction."""
        return self.faction_reputations.get(faction_id)

    def get_faction_score(self, faction_id: str) -> int:
        """Returns the character's reputation score for a faction, defaults to 0."""
        details = self.get_faction_reputation_details(faction_id)
        return details["score"] if details else 0

    def get_current_faction_rank_name(self, faction_id: str) -> str | None:
        """Retrieves the character's current rank name in the specified faction."""
        details = self.get_faction_reputation_details(faction_id)
        return details["rank_name"] if details else None

    def update_faction_reputation(self, faction_id: str, amount: int):
        """
        Updates the character's reputation score for a faction and checks for rank changes.
        """
        if not self.get_faction_data(faction_id):
            print(f"Warning: Faction ID '{faction_id}' not found. Cannot update reputation.")
            return

        current_details = self.faction_reputations.get(faction_id)

        if not current_details:
            # Faction not yet in character's list, initialize it.
            # This case should ideally be handled by join_faction first for clarity,
            # but can be initialized here if reputation is gained before formal joining.
            initial_rank = get_rank_by_reputation(faction_id, 0)
            if not initial_rank: # Should not happen if faction definition is correct
                print(f"Error: Could not determine initial rank for faction '{faction_id}'.")
                return
            self.faction_reputations[faction_id] = {"score": 0, "rank_name": initial_rank["name"]}
            current_details = self.faction_reputations[faction_id]
            print(f"{self.name} now has a reputation with {self.get_faction_data(faction_id)['name']}, starting at {initial_rank['name']}.")

        old_score = current_details["score"]
        new_score = old_score + amount
        current_details["score"] = new_score

        print(f"{self.name}'s reputation with {self.get_faction_data(faction_id)['name']} changed by {amount} to {new_score}.")

        # Check for rank change
        new_rank_def = get_rank_by_reputation(faction_id, new_score)
        if not new_rank_def: # Should not happen
            print(f"Error: Could not determine rank for score {new_score} in faction '{faction_id}'.")
            return

        old_rank_name = current_details["rank_name"]
        new_rank_name = new_rank_def["name"]

        if new_rank_name != old_rank_name:
            current_details["rank_name"] = new_rank_name
            print(f"{self.name} has achieved the rank of {new_rank_name} with {self.get_faction_data(faction_id)['name']}!")
            # Here, you could also trigger application of new rank benefits if they are immediate
            # For now, benefits are mostly checked passively (e.g. shop discounts)

    def join_faction(self, faction_id: str) -> bool:
        """
        Allows the character to join a faction if not already a member.
        Initializes reputation at 0 and the starting rank.
        """
        faction_def = self.get_faction_data(faction_id)
        if not faction_def:
            print(f"Error: Faction ID '{faction_id}' not found. Cannot join.")
            return False

        if faction_id in self.faction_reputations:
            print(f"{self.name} is already a member of {faction_def['name']}.")
            return False

        # Determine initial rank (usually the one requiring 0 reputation)
        initial_rank = get_rank_by_reputation(faction_id, 0)
        if not initial_rank:
            print(f"Error: Could not determine initial rank for faction '{faction_id}'. Joining failed.")
            return False

        self.faction_reputations[faction_id] = {"score": 0, "rank_name": initial_rank["name"]}
        print(f"{self.name} has joined {faction_def['name']} with the rank of {initial_rank['name']}.")
        return True
