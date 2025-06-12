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
    LEVEL_XP_THRESHOLDS = { 1: 0, 2: 300, 3: 900, 4: 2700, 5: 6500 }

    STAT_NAMES = ["STR", "DEX", "CON", "INT", "WIS", "CHA"]

    def __init__(self, name: str = None):
        self.name = name # Can be None initially if using interactive creation
        self.stats = {stat: 0 for stat in self.STAT_NAMES}
        self.stat_bonuses = {stat: 0 for stat in self.STAT_NAMES}
        self.ac_bonus = 0
        self.level = 1
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

    def roll_stats(self):

        con_modifier = self._calculate_modifier(self.stats["CON"], is_base_stat_score=True)
        # Ensure level is at least 1 for this calculation if called early
        current_level = self.level if self.level > 0 else 1
        self.base_max_hp = 10 + (con_modifier * current_level)
        self.hp = self.get_effective_max_hp()

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
            if self.exhaustion_level >= 6:
                print(f"  {self.name} has died from exhaustion!")
        elif self.exhaustion_level == old_level and self.exhaustion_level < 6 and amount > 0 : # Only print if change was attempted but resulted in no actual level change (e.g. already at 5, tried to gain 0 but code path led here)
             print(f"  {self.name}'s exhaustion level remains {self.exhaustion_level} ({self.get_exhaustion_effects()}). No effective change from this event, though gain was attempted.")
        # No message if already at 6 and trying to add more, as it's capped and previous condition handles the 5->6 transition.

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

    def add_item_to_inventory(self, item: Item): self.inventory.append(item); print(f"{item.name} added to {self.name}'s inventory.")
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
    def perform_skill_check(self, skill_name:str, dc:int, can_use_reroll_item:bool=True) -> bool:
        if skill_name not in self.stats: print(f"Warning: Invalid skill '{skill_name}'."); return False
        roll1=random.randint(1,20); d20=roll1; dis_str=""
        if self.exhaustion_level>=1: roll2=random.randint(1,20); d20=min(roll1,roll2); dis_str=f" (rolled {roll1},{roll2} dis, took {d20})"
        mod=self._calculate_modifier(0,False,skill_name); res=d20+mod
        print(f"{self.name} {skill_name} check (DC {dc}). Roll: {d20}{dis_str} + {mod} (eff {self.get_effective_stat(skill_name)}) = {res}.")
        if res>=dc: print("  Skill check successful!"); return True
        print("  Skill check failed.")
        if can_use_reroll_item:
            reroll_item=next((i for i in self.inventory if i.name=="Lucky Charm" and i.effects.get("allow_reroll")),None)
            if reroll_item:
                print(f"  {self.name} has Lucky Charm! Using for reroll...");
                if reroll_item.is_consumable:
                    if self.remove_specific_item_from_inventory(reroll_item): print("  Lucky Charm consumed.")
                    else: print("  Error consuming Lucky Charm.")
                r1=random.randint(1,20); d20_r=r1; rdis_str=""
                if self.exhaustion_level>=1: r2=random.randint(1,20); d20_r=min(r1,r2); rdis_str=f" (rolled {r1},{r2} dis, took {d20_r})"
                new_res=d20_r+mod; print(f"  Rerolled {d20_r}{rdis_str} + {mod} = {new_res}.")
                if new_res>=dc: print("  Reroll successful!"); return True
                print("  Reroll failed."); return False
        return False

    def to_dict(self) -> dict:
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
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Character':
        char = cls(data["name"])
        char.stats = data["stats"]
        char.stat_bonuses = data.get("stat_bonuses", {key: 0 for key in char.stats}) # Ensure all keys exist
        char.ac_bonus = data.get("ac_bonus", 0)
        char.level = data["level"]
        char.xp = data["xp"]
        char.pending_xp = data.get("pending_xp", 0)
        char.base_max_hp = data["base_max_hp"]
        char.hp = data["hp"] # This will be capped by effective_max_hp on load if needed
        char.max_hit_dice = data.get("max_hit_dice", char.level) # Default to level if not in save
        char.hit_dice = data["hit_dice"]
        char.attunement_slots = data.get("attunement_slots", 3)
        char.inventory = [Item.from_dict(item_data) for item_data in data.get("inventory", [])]
        # Attuned items are loaded but effects need reapplication
        char.attuned_items = [Item.from_dict(item_data) for item_data in data.get("attuned_items", [])]
        char.exhaustion_level = data["exhaustion_level"]
        char.gold = data["gold"]
        char.skill_points_to_allocate = data.get("skill_points_to_allocate", 0)
        char.speed = data.get("speed", 30)

        # Ensure HP is capped by current effective max HP after loading exhaustion
        char.hp = min(char.hp, char.get_effective_max_hp())
        return char

if __name__ == "__main__":
    pass
