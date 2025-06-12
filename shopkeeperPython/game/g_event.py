import random
try:
    from .character import Character
    from .item import Item
except ImportError:
    print("EventManager: Running g_event.py directly, Character/Item might not be fully available for EventManager testing.")
    class Character: pass
    class Item: pass


class Event:
    def __init__(self, name: str, description: str, outcomes: dict, skill_check: dict = None,
                 effects: dict = None, duration: int = 0, event_type: str = "generic", is_active: bool = False): # Added new parameters from_dict might use
        self.name = name
        self.description = description
        self.skill_check = skill_check
        self.outcomes = outcomes # This should be outcome definitions, not applied effects.
        # Direct effects of the event itself, if any, separate from outcomes.
        # However, the current resolve_event primarily uses outcomes.
        # For from_dict, we'll store them but current logic might not use them directly from self.effects.
        self.effects = effects if effects else {}
        self.duration = duration
        self.event_type = event_type
        self.is_active = is_active


    def __repr__(self):
        return f"Event(name='{self.name}', description='{self.description[:50]}...', skill_check={self.skill_check is not None})"

    @staticmethod
    def from_dict(data: dict) -> 'Event':
        direct_effects = data.get("effects")
        outcomes = data.get("outcomes")

        # If direct effects are provided in the data dict, and no specific outcomes structure is given,
        # create a default 'success' outcome that includes these direct effects.
        # This allows a simpler dict structure for events that don't have skill checks or multiple outcomes.
        if direct_effects and not outcomes:
            outcomes = {
                "success": {"message": data.get("description", "Event occurred."), "effects": direct_effects},
                # Optionally, a default failure if not specified, though less relevant if no skill check
                # "failure": {"message": "Event did not occur as expected.", "effects": {}}
            }
        elif not outcomes: # Ensure outcomes is always a dict, even if empty or default
            outcomes = {
                "success": {"message": "Event succeeded by default.", "effects": {}},
                "failure": {"message": "Event failed by default.", "effects": {}}
            }

        # The 'effects' parameter in Event.__init__ is for event-level direct effects,
        # not necessarily the ones tied to outcomes.
        # For this use case, we are packaging what was 'effects' in the dict into an 'outcome'.
        # So, we pass the original data.get("effects") to the constructor's 'effects' param
        # if there's a separate need for it, otherwise it can be None or {}.
        # The key is that 'outcomes' passed to Event() now contains the effects for resolve_event.

        return Event(
            name=data.get("name", "Unnamed Event"),
            description=data.get("description", ""),
            outcomes=outcomes, # This now correctly structures the effects for resolve_event
            skill_check=data.get("skill_check"),
            # effects=data.get("effects", {}), # Keep if Event itself can have effects outside outcomes
            duration=data.get("duration", 0),
            event_type=data.get("event_type", "generic"),
            is_active=data.get("is_active", False)
            # Consider if trigger_conditions should be part of from_dict and __init__ too
            # trigger_conditions=data.get("trigger_conditions", {})
        )


class EventManager:
    def __init__(self, character: Character):
        self.character = character

    def trigger_random_event(self, possible_events: list[Event]) -> str | None: # Return event name or None
        if not possible_events:
            print("No possible events to trigger.")
            return None

        selected_event = random.choice(possible_events)
        print(f"\n--- Event Triggered: {selected_event.name} ---")
        self.resolve_event(selected_event)
        return selected_event.name # Return the name of the triggered event

    def resolve_event(self, event_instance: Event):
        print(f"Description: {event_instance.description}")
        outcome_key = "success"

        if event_instance.skill_check:
            skill = event_instance.skill_check["skill"]
            dc = event_instance.skill_check["dc"]
            if hasattr(self.character, 'perform_skill_check'):
                check_successful = self.character.perform_skill_check(skill_name=skill, dc=dc)
                if not check_successful:
                    outcome_key = "failure"
            else:
                print(f"Error: Character object does not have 'perform_skill_check' method.")
                if "failure" in event_instance.outcomes:
                    outcome_key = "failure"
                else:
                    print(f"Warning: Skill check required for '{event_instance.name}' but method unavailable. Defaulting to 'success' outcome.")

        chosen_outcome = event_instance.outcomes.get(outcome_key)

        if not chosen_outcome:
            print(f"Error: Outcome '{outcome_key}' not defined for event '{event_instance.name}'.")
            return

        print(f"Outcome: {chosen_outcome.get('message', 'No message for this outcome.')}")

        # Apply XP changes using award_xp (for pending XP system)
        xp_change = 0
        if "xp_reward" in chosen_outcome: # This check is for old structure
            xp_change += chosen_outcome["xp_reward"]
        if "xp_penalty" in chosen_outcome: # This check is for old structure
             xp_change -= chosen_outcome["xp_penalty"]

        # New structure: effects are nested inside chosen_outcome
        outcome_effects = chosen_outcome.get("effects", {})
        if "character_xp_gain" in outcome_effects:
             xp_change += outcome_effects["character_xp_gain"]
        if "character_xp_loss" in outcome_effects: # Assuming a new effect type for loss
             xp_change -= outcome_effects["character_xp_loss"]


        if xp_change != 0 and hasattr(self.character, 'award_xp'):
            self.character.award_xp(xp_change) # award_xp handles positive/negative
        elif xp_change !=0:
             print(f"  Error: Character has no 'award_xp' method for XP change of {xp_change}.")

        # Handle item rewards from outcome_effects
        if "item_reward" in outcome_effects and hasattr(self.character, 'add_item_to_inventory'):
            item_details = outcome_effects["item_reward"]
            item_name = item_details.get("name")
            item_qty = item_details.get("quantity", 1)

            if item_name == "Gold": # Special case for gold
                 if hasattr(self.character, 'gold'):
                    self.character.gold += item_qty
                    print(f"  Gained {item_qty} Gold. Current Gold: {self.character.gold}")
                 else:
                    print(f"  Error: Character has no 'gold' attribute for Gold reward.")
            else:
                print(f"  Attempting to reward item: {item_name} (Quantity: {item_qty})")
                try:
                    reward_item = Item(name=item_name, description="An event reward.", base_value=0, item_type="misc", quality="Common")
                    for _ in range(item_qty):
                        self.character.add_item_to_inventory(reward_item)
                except Exception as e:
                    print(f"  Error creating/adding item reward '{item_name}': {e}")

        # Handle consequences from outcome_effects
        if "consequence" in outcome_effects: # Assuming consequence is now a sub-dict in effects
            consequence_details = outcome_effects["consequence"]
            consequence_type = consequence_details.get("type")
            consequence_value = consequence_details.get("value", 0)

            if consequence_type == "lose_gold" and hasattr(self.character, 'gold'):
                amount_to_lose = consequence_value
                self.character.gold = max(0, self.character.gold - amount_to_lose)
                print(f"  Lost {amount_to_lose} Gold. Current Gold: {self.character.gold}")
            elif consequence_type == "lose_item_value" and hasattr(self.character, 'inventory'):
                print(f"  Lost an item of value around {consequence_value}. (Actual item removal not implemented here yet).")
            # Add more consequence handling here if needed

# --- Sample Event Definitions ---
event_lucky_find = Event(
    name="Lucky Find",
    description="You found a small pouch of gold on the street!",
    skill_check=None,
    outcomes={
        "success": {"message": "You pocket 25 gold pieces.", "xp_reward": 10, "item_reward": {"name": "Gold", "quantity": 25}}
    }
)
event_shady_customer = Event(
    name="Shady Customer",
    description="A shifty-looking individual wants to buy your most expensive-looking item for a suspiciously low price, but hints at a 'generous tip' if you're 'understanding'.",
    skill_check={"skill": "WIS", "dc": 14},
    outcomes={
        "success": {"message": "You see through their ruse and decline politely. They leave in a huff. You feel a bit wiser.", "xp_reward": 50},
        "failure": {"message": "You try to negotiate, but they suddenly snatch a valuable-looking item and run! You lost an item worth around 50 gold.", "consequence": "lose_item_value", "value": 50, "xp_penalty": 10}
    }
)
event_persuade_guard = Event(
    name="Persuade Guard",
    description="A city guard is blocking your way, citing a new toll. You try to persuade them to let you pass.",
    skill_check={"skill": "CHA", "dc": 15},
    outcomes={
        "success": {"message": "The guard grumbles but waves you through, impressed by your argument.", "xp_reward": 30},
        "failure": {"message": "The guard is unmoved and demands you pay the 10 gold toll or turn back.", "consequence": "lose_gold", "value": 10}
    }
)
event_supply_shortage_rumor = Event(
    name="Supply Shortage Rumor",
    description="You hear rumors of a supply shortage for crafting materials you often use.",
    skill_check={"skill": "INT", "dc": 12},
    outcomes={
        "success": {"message": "You investigate and find the rumors are true! You manage to stock up before prices rise.", "xp_reward": 20, "effects": [{"type": "cheaper_materials", "duration": 72}]},
        "failure": {"message": "You dismiss the rumors, but later find out they were true. Material costs have temporarily increased."}
    }
)
SAMPLE_EVENTS = [event_lucky_find, event_shady_customer, event_persuade_guard, event_supply_shortage_rumor]

if __name__ == "__main__":
    print("--- Event System Test ---")
    try:
        from .character import Character
        from .item import Item
        print("Successfully imported .character and .item for testing.")
    except ImportError as e:
        print(f"Could not import .character or .item for full test using relative import: {e}")
        try:
            from character import Character
            from item import Item
            print("Successfully imported character and item using direct import.")
        except ImportError as e2:
            print(f"Could not import Character/Item using direct import either: {e2}")
            print("Using placeholder Character/Item classes. Some event effects might not fully apply.")
            if 'Character' not in globals():
                class Character: # type: ignore
                    def __init__(self, name="Test Player"):
                        self.name = name; self.stats = {"STR":10,"DEX":10,"CON":10,"INT":10,"WIS":10,"CHA":10}; self.stat_bonuses = {}
                        self.xp = 0; self.pending_xp = 0; self.gold = 100; self.inventory = []
                    def get_effective_stat(self,stat_name): return self.stats.get(stat_name,0)+self.stat_bonuses.get(stat_name,0)
                    def _calculate_modifier(self,stat_score,is_base_stat_score=False,stat_name_for_effective="CON"): return (self.get_effective_stat(stat_name_for_effective)-10)//2 if not is_base_stat_score else (stat_score-10)//2
                    def perform_skill_check(self,skill_name,dc,can_use_reroll_item=True): print(f"P-SKILL: {skill_name} DC{dc}"); return random.choice([True,False])
                    def award_xp(self,amount): self.pending_xp +=amount; print(f"P-AWARD_XP: {amount} Pending: {self.pending_xp}"); return amount
                    def commit_pending_xp(self): actual=self.pending_xp; self.xp+=actual; self.pending_xp=0; print(f"P-COMMIT_XP: {actual} Total: {self.xp}"); return actual
                    def add_item_to_inventory(self,item): self.inventory.append(item); print(f"P-ADD_ITEM: {item.name}")
                    def display_character_info(self): print(f"P-INFO: {self.name}, XP:{self.xp}, PendingXP:{self.pending_xp}, Gold:{self.gold}, Inv:{[i.name for i in self.inventory[:2]]}")
                    def roll_stats(self): print("P-ROLL_STATS")
            if 'Item' not in globals(): # type: ignore
                class Item: # type: ignore
                    def __init__(self,name,description,base_value,item_type,quality,effects=None,is_consumable=False,is_magical=False,is_attunement=False):
                        self.name=name;self.description=description;self.effects=effects or {};self.is_consumable=is_consumable;self.base_value=base_value;self.item_type=item_type;self.quality=quality
                    def __repr__(self): return f"Item({self.name})"

    test_char = Character(name="Test Event Player") # type: ignore
    test_char.stats = {"STR": 12, "DEX": 10, "CON": 14, "INT": 10, "WIS": 16, "CHA": 8}
    if hasattr(test_char, 'roll_stats'): test_char.roll_stats()

    try:
        lucky_charm = Item(name="Lucky Charm",description="Reroll",base_value=0,item_type="trinket",quality="Rare",effects={"allow_reroll":True},is_consumable=True)
        if hasattr(test_char, 'add_item_to_inventory'): test_char.add_item_to_inventory(lucky_charm)
    except Exception as e: print(f"Could not create/add Lucky Charm: {e}")

    if hasattr(test_char, 'display_character_info'): test_char.display_character_info()
    event_manager = EventManager(character=test_char)

    print("\n--- Resolving Specific Event: Lucky Find ---")
    event_manager.resolve_event(event_lucky_find)
    if hasattr(test_char, 'display_character_info'): test_char.display_character_info()

    print("\n--- Resolving Specific Event: Shady Customer (WIS DC 14) ---")
    event_manager.resolve_event(event_shady_customer)
    if hasattr(test_char, 'display_character_info'): test_char.display_character_info()

    print("\n--- Resolving Specific Event: Persuade Guard (CHA DC 15) ---")
    event_manager.resolve_event(event_persuade_guard)
    if hasattr(test_char, 'display_character_info'): test_char.display_character_info()

    has_charm = False
    if hasattr(test_char, 'inventory') and isinstance(test_char.inventory, list):
        has_charm = any(getattr(item, 'name', None) == "Lucky Charm" for item in test_char.inventory)
    print(f"Player still has Lucky Charm: {has_charm}")

    print("\n--- Triggering Random Events ---")
    for i in range(3):
        print(f"Random Event {i+1}:")
        event_name = event_manager.trigger_random_event(SAMPLE_EVENTS)
        print(f"Triggered event: {event_name}")
        if hasattr(test_char, 'display_character_info'): test_char.display_character_info()

    if hasattr(test_char, 'commit_pending_xp'):
        print("\n--- Committing XP at end of test ---")
        test_char.commit_pending_xp()
        if hasattr(test_char, 'display_character_info'): test_char.display_character_info()

    print("\n--- Event System Test Complete ---")
