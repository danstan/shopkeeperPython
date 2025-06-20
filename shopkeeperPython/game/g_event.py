import random
try:
    from .character import Character
    from .item import Item
except ImportError:
    # This is a fallback for direct execution or testing outside a full package structure.
    # print("EventManager: Running g_event.py directly, Character/Item might not be fully available for EventManager testing.")
    class Character: pass # type: ignore
    class Item: pass # type: ignore


class Event:
    def __init__(self, name: str, description: str, outcomes: dict,
                 skill_check_options: list[dict] = None, # Renamed from skill_check
                 effects: dict = None, duration: int = 0, event_type: str = "generic",
                 is_active: bool = False, min_level: int = 1, dc_scaling_factor: float = 0.0):
        self.name = name
        self.description = description
        # skill_check_options is now a list of choices, each a dict.
        self.skill_check_options = skill_check_options if skill_check_options else []
        self.outcomes = outcomes
        self.effects = effects if effects else {} # Event-level direct effects, if any
        self.duration = duration
        self.event_type = event_type
        self.is_active = is_active
        self.min_level = min_level
        self.dc_scaling_factor = dc_scaling_factor

    def __repr__(self):
        num_choices = len(self.skill_check_options) if self.skill_check_options else 0
        return f"Event(name='{self.name}', description='{self.description[:50]}...', choices={num_choices}, min_lvl={self.min_level})"

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

        # Ensure skill_check_options is parsed as a list, defaulting to empty if not present or not a list
        # Attempt to load from "skill_check_options" first, then "skill_check" for backward compatibility
        skill_check_data = data.get("skill_check_options", data.get("skill_check"))

        if not isinstance(skill_check_data, list):
            # If old format (single dict) or None, default to an empty list for the new structure.
            # Conversion from a single dict to a list of choices would require more assumptions
            # about the structure of that single dict.
            skill_check_data = []

        return Event(
            name=data.get("name", "Unnamed Event"),
            description=data.get("description", ""),
            outcomes=outcomes,
            skill_check_options=skill_check_data, # Assign parsed list
            effects=data.get("effects", {}), # Retained for event-level direct effects
            duration=data.get("duration", 0),
            event_type=data.get("event_type", "generic"),
            is_active=data.get("is_active", False),
            min_level=data.get("min_level", 1),
            dc_scaling_factor=data.get("dc_scaling_factor", 0.0)
        )


class EventManager:
    def __init__(self, character: Character, game_manager): # Added game_manager
        self.character = character
        self.game_manager = game_manager # Store game_manager instance

    def trigger_random_event(self, possible_events: list[Event]) -> str | None: # Return event name or None
        if not possible_events:
            print("No possible events to trigger.")
            return None

        selected_event = random.choice(possible_events)
        print(f"\n--- Event Triggered: {selected_event.name} ---")
        self.resolve_event(selected_event)
        return selected_event.name # Return the name of the triggered event

    def resolve_event(self, event_instance: Event) -> list[dict]:
        """
        Prepares and returns the list of choices for the player for a given event.
        Calculates scaled DCs and item requirement descriptions.
        """
        print(f"\n--- Event: {event_instance.name} ---")
        print(f"Description: {event_instance.description}")

        choices_for_ui = []
        if not hasattr(self.character, 'level'):
            # Fallback if character object doesn't have a level (e.g. simplified test character)
            print("Warning: Character has no level attribute. Using level 1 for DC scaling.")
            character_level = 1
        else:
            character_level = self.character.level

        for i, choice in enumerate(event_instance.skill_check_options):
            base_dc = choice.get('base_dc', 10) # Default base_dc if missing

            # Calculate scaled DC
            scaled_dc = base_dc + max(0, (character_level - event_instance.min_level)) * event_instance.dc_scaling_factor
            scaled_dc = int(max(5, scaled_dc)) # Ensure DC is at least 5 and an integer

            item_requirement_desc = None
            item_req = choice.get('item_requirement')
            if item_req:
                item_name = item_req.get('name', 'Unknown Item')
                item_effect = item_req.get('effect', 'unknown effect')
                item_requirement_desc = f"Uses: {item_name} ({item_effect})"
                if item_effect == 'dc_reduction':
                    item_requirement_desc += f" by {item_req.get('value',0)})"


            choice_ui_data = {
                "id": i, # So UI can refer back to choice_index
                "text": choice.get('choice_text', f"Option {i+1}"),
                "skill": choice.get('skill', 'N/A'),
                "dc": scaled_dc,
                "success_outcome_key": choice.get('success_outcome_key', 'success'), # Ensure these exist
                "failure_outcome_key": choice.get('failure_outcome_key', 'failure')  # Ensure these exist
            }
            if item_requirement_desc:
                choice_ui_data["item_requirement_desc"] = item_requirement_desc

            choices_for_ui.append(choice_ui_data)

        if not choices_for_ui and event_instance.outcomes: # Handle events with no skill checks (direct outcomes)
            print("This event has a direct outcome.")
            # If there are no skill check choices, but there are outcomes,
            # we might imply a default action or that the event just happens.
            # For now, this method is about presenting choices. If no choices, it returns empty.
            # A different method or logic in the game loop would handle direct outcome events.
            # Or, we could define a "default" choice if skill_check_options is empty.
            # For simplicity, if no choices, this returns an empty list.
            # The caller (game loop) would then need to decide how to proceed.
            # It could directly call execute_skill_choice with a default choice_index if outcomes exist.
            # This is a design decision for the game loop.
            # For now, we'll just print this. The old logic for direct outcomes is in execute_skill_choice.
            pass


        if choices_for_ui:
            print("\nPlayer Choices:")
            for choice_ui in choices_for_ui:
                req_desc = f" ({choice_ui['item_requirement_desc']})" if 'item_requirement_desc' in choice_ui else ""
                print(f"  {choice_ui['id']}. {choice_ui['text']} [{choice_ui['skill']} DC {choice_ui['dc']}{req_desc}]")

        return choices_for_ui

    def execute_skill_choice(self, event_instance: Event, choice_index: int) -> dict:
        """
        Executes a specific player choice for an event, performs skill checks,
        and applies the outcome.
        """
        if not event_instance.skill_check_options or choice_index >= len(event_instance.skill_check_options):
            # This case handles events that might have direct outcomes without choices,
            # or if an invalid choice_index is provided.
            # If skill_check_options is empty, we look for a default 'success' or 'event_happens' outcome.
            if not event_instance.skill_check_options and "success" in event_instance.outcomes:
                # Default to "success" outcome if no choices defined (e.g. lucky find event)
                selected_choice = None # No specific choice was made
                outcome_key = "success"
                scaled_dc = 0 # No DC for direct outcome
                check_successful = True # Implicitly successful
                auto_success_by_item = False
                final_roll_data = {"status": "direct_outcome", "success": True, "dc": 0}
            elif not event_instance.skill_check_options and event_instance.outcomes:
                # Take the first available outcome if 'success' isn't there
                selected_choice = None
                outcome_key = list(event_instance.outcomes.keys())[0]
                scaled_dc = 0
                check_successful = True
                auto_success_by_item = False
                final_roll_data = {"status": "direct_outcome", "success": True, "dc": 0}
            else:
                print(f"Error: Invalid choice index ({choice_index}) or no skill check options for event '{event_instance.name}'.")
                return {"message": "Error: Invalid choice or event configuration.", "rolled_successfully": False, "details": {}}
        else:
            selected_choice = event_instance.skill_check_options[choice_index]

            if not hasattr(self.character, 'level'):
                character_level = 1 # Fallback
            else:
                character_level = self.character.level

            base_dc = selected_choice.get('base_dc', 10)
            scaled_dc = int(max(5, base_dc + max(0, (character_level - event_instance.min_level)) * event_instance.dc_scaling_factor))

            check_successful = False
            auto_success_by_item = False
            roll_result_dict = {"status": "not_applicable", "dc": scaled_dc, "success": False} # Default initialization

            # Item Interaction Logic
            item_req = selected_choice.get('item_requirement')
            if item_req:
                item_name_req = item_req.get("name")
                found_item_in_inventory = None
                if hasattr(self.character, 'inventory') and isinstance(self.character.inventory, list):
                    for item_instance in self.character.inventory:
                        if hasattr(item_instance, 'name') and item_instance.name == item_name_req:
                            found_item_in_inventory = item_instance
                            break

                if found_item_in_inventory:
                    print(f"Item '{item_name_req}' is available.")
                    if item_req.get('effect') == 'auto_success':
                        check_successful = True
                        auto_success_by_item = True
                        print(f"Outcome automatically successful due to {item_name_req}.")
                        roll_result_dict = {"status": "auto_success", "item_used": item_name_req, "dc": 0, "success": True}
                        # Future: if item_req.get('consumable', False) and hasattr(self.character, 'remove_item_from_inventory'):
                        #     self.character.remove_item_from_inventory(found_item_in_inventory)
                        #     print(f"{item_name_req} was consumed.")
                    elif item_req.get('effect') == 'dc_reduction':
                        reduction_value = item_req.get('value', 0)
                        original_dc = scaled_dc
                        scaled_dc = max(1, scaled_dc - reduction_value)
                        print(f"DC reduced from {original_dc} to {scaled_dc} by {item_name_req}.")
                elif item_req.get('effect') == 'enable_choice_or_auto_fail': # Example of a hard requirement
                    print(f"Item '{item_name_req}' required for this choice but not found. Outcome is failure.")
                    check_successful = False # Force failure if item is essential and missing
                    # This assignment of outcome_key might be too early if check_successful can be True later
                    # outcome_key = selected_choice.get('failure_outcome_key', 'failure')
                    # Better to let the standard logic determine outcome_key based on check_successful

            # Perform Skill Check (if not auto_success)
            if not auto_success_by_item:
                skill_to_check = selected_choice.get('skill')
                # roll_result_dict is already initialized above
                if skill_to_check and hasattr(self.character, 'perform_skill_check'):
                    # print(f"Performing {skill_to_check} check against DC {scaled_dc}.") # perform_skill_check now prints this
                    roll_result_dict = self.character.perform_skill_check(skill_name=skill_to_check, dc=scaled_dc)
                    check_successful = roll_result_dict["success"]
                elif not skill_to_check: # No skill defined, could be auto-pass or auto-fail based on design for that choice
                    print(f"No skill defined for choice '{selected_choice.get('choice_text', 'Unnamed choice')}'. Assuming success as no skill/DC implies narrative choice.")
                    check_successful = True # If no skill and no DC, assume success.
                    roll_result_dict = {"status": "no_skill_check_required", "dc": 0, "success": True}
                else: # Character cannot perform skill checks
                    print(f"Error: Character object does not have 'perform_skill_check' method. Assuming failure for skill check.")
                    check_successful = False
                    roll_result_dict = {"status": "perform_skill_check_missing", "dc": scaled_dc, "success": False}

            outcome_key = selected_choice.get('success_outcome_key', 'success') if check_successful else selected_choice.get('failure_outcome_key', 'failure')
            final_roll_data = roll_result_dict # This will be the detailed dict from perform_skill_check or the simple status dicts

        # Apply Outcome
        chosen_outcome = event_instance.outcomes.get(outcome_key)
        if not chosen_outcome:
            alt_outcome_key = "failure" if outcome_key != "failure" else "success" # Try alternative if primary missing
            chosen_outcome = event_instance.outcomes.get(alt_outcome_key)
            if chosen_outcome:
                print(f"Warning: Outcome key '{outcome_key}' not found. Using alternative '{alt_outcome_key}'.")
            else:
                # Ensure check_successful is defined even if outcome is missing
                if 'check_successful' not in locals(): check_successful = False # Default if not set
                print(f"Error: Outcome key '{outcome_key}' (and alternative) not defined for event '{event_instance.name}'. Using generic failure.")
                return {"message": f"Event '{event_instance.name}' concluded without a specific outcome message (key: {outcome_key}).",
                        "rolled_successfully": check_successful,
                        "outcome_details": {"error": "Outcome not found"},
                        "roll_data": final_roll_data if 'final_roll_data' in locals() else {"status": "error_outcome_not_found"}
                        }

        outcome_message = chosen_outcome.get('message', 'No message for this outcome.')
        print(f"Outcome ({('Success' if check_successful else 'Failure')} - Key: {outcome_key}): {outcome_message}")

        # The 'effects' sub-dictionary of the chosen outcome
        outcome_effects_to_apply = chosen_outcome.get("effects", {})

        # Log actual applied effects for return (can be simpler than full details_log if that's too verbose for caller)
        applied_effects_summary = {}

        # XP Changes
        xp_change = outcome_effects_to_apply.get("character_xp_gain", 0) - outcome_effects_to_apply.get("character_xp_loss", 0)
        if xp_change != 0 and hasattr(self.character, 'award_xp'):
            self.character.award_xp(xp_change)
            applied_effects_summary["xp_change"] = xp_change
            # print(f"  XP Changed by {xp_change}. Current Pending XP: {getattr(self.character, 'pending_xp', 'N/A')}") # Already printed by award_xp
        elif xp_change != 0:
            print(f"  Error: Character has no 'award_xp' method for XP change of {xp_change}.")

        # Gold Changes
        gold_change = outcome_effects_to_apply.get("gold_change", 0)
        if gold_change != 0 and hasattr(self.character, 'gold'):
            self.character.gold += gold_change
            applied_effects_summary["gold_change"] = gold_change
            print(f"  Gold changed by {gold_change}. Current Gold: {self.character.gold}")
        elif gold_change != 0:
             print(f"  Error: Character has no 'gold' attribute for Gold change of {gold_change}.")

        # Item Rewards
        item_reward_details = outcome_effects_to_apply.get("item_reward")
        if item_reward_details and hasattr(self.character, 'add_item_to_inventory'):
            item_name = item_reward_details.get("name")
            item_qty = item_reward_details.get("quantity", 1)
            if item_name == "Gold":
                 if hasattr(self.character, 'gold'):
                    self.character.gold += item_qty
                    applied_effects_summary["gold_change"] = applied_effects_summary.get("gold_change",0) + item_qty
                    # print(f"  Gained {item_qty} Gold (as item). Current Gold: {self.character.gold}") # Printed by character.gold change
            else:
                try:
                    reward_item = Item(name=item_name,
                                       description=item_reward_details.get("description","Event reward"),
                                       base_value=item_reward_details.get("base_value",0), # Corrected from "value"
                                       item_type=item_reward_details.get("item_type","misc"), # Corrected from "type"
                                       quality=item_reward_details.get("quality","Common"))
                    for _ in range(item_qty):
                        self.character.add_item_to_inventory(reward_item)
                    applied_effects_summary.setdefault("items_gained", []).append({"name": item_name, "quantity": item_qty})
                    # print(f"  Gained item: {item_name} (Quantity: {item_qty})") # Printed by add_item_to_inventory
                except Exception as e:
                    print(f"  Error creating/adding item reward '{item_name}': {e}")

        # Item Loss
        item_loss_details = outcome_effects_to_apply.get("item_loss")
        if item_loss_details and hasattr(self.character, 'remove_item_from_inventory') and hasattr(self.character, 'inventory'):
            item_to_lose_name = item_loss_details.get("name")
            item_to_lose_qty = item_loss_details.get("quantity", 1)

            if item_to_lose_name:
                items_removed_count = 0
                for _ in range(item_to_lose_qty):
                    item_instance_to_remove = next((item for item in self.character.inventory if item.name == item_to_lose_name), None)
                    if item_instance_to_remove:
                        # remove_specific_item_from_inventory expects the instance
                        if self.character.remove_specific_item_from_inventory(item_instance_to_remove):
                             items_removed_count +=1
                if items_removed_count > 0:
                    applied_effects_summary.setdefault("items_lost", []).append({"name": item_to_lose_name, "quantity": items_removed_count})
                    # print(f"  Lost {items_removed_count}x {item_to_lose_name}.") # Printed by remove_item
                else:
                    print(f"  Tried to lose {item_to_lose_name}, but not found in inventory or failed to remove.")
            elif item_loss_details.get("type") == "random_valuable":
                print(f"  Placeholder: Player would lose a random valuable item.")

        # HP Loss (example of another direct effect)
        hp_loss = outcome_effects_to_apply.get("hp_loss", 0)
        if hp_loss > 0 and hasattr(self.character, 'hp'):
            # Assuming direct HP reduction, not "damage" which might interact with resistances later
            self.character.hp = max(0, self.character.hp - hp_loss)
            applied_effects_summary["hp_lost"] = hp_loss
            print(f"  Lost {hp_loss} HP. Current HP: {self.character.hp}/{self.character.get_effective_max_hp()}")
            if self.character.hp == 0:
                 print(f"  {self.character.name} has been knocked unconscious or worse!")
                 # Potentially trigger gain_exhaustion or death checks here or in Character class via take_damage method

        # Journal Entry
        if self.game_manager and hasattr(self.game_manager, 'add_journal_entry'):
            journal_details = {
                "event_name": event_instance.name,
                "choice_made": selected_choice.get('choice_text', "Direct Outcome") if selected_choice else "Direct Outcome",
                "skill_used": selected_choice.get('skill', "N/A") if selected_choice else "N/A",
                "dc": scaled_dc, # DC the check was made against
                "rolled_successfully": check_successful,
                "auto_success_by_item": auto_success_by_item,
                "roll_data": final_roll_data if 'final_roll_data' in locals() else {"status": "no_roll_applicable_or_error"},
                "outcome_key": outcome_key,
                "outcome_message": outcome_message,
                "effects_applied_summary": applied_effects_summary
            }
            self.game_manager.add_journal_entry(
                action_type="Game Event Choice",
                summary=f"Event '{event_instance.name}': {selected_choice.get('choice_text', outcome_key) if selected_choice else outcome_key}",
                details=journal_details,
                outcome=outcome_message
            )
        else:
            print("EventManager: GameManager or add_journal_entry not available. Cannot log event to journal.")

        return {
            "message": outcome_message,
            "rolled_successfully": check_successful, # From the skill check or auto_success
            "outcome_details": outcome_effects_to_apply, # The 'effects' dict from the outcome
            "roll_data": final_roll_data if 'final_roll_data' in locals() else {"status": "no_roll_data_captured"}
        }

# --- New Skill Check Event Definitions ---
event_suspicious_traveler = Event.from_dict({
    "name": "Suspicious Traveler",
    "description": "A nervous-looking traveler offers you a dusty old map for a small price. They claim it leads to a hidden treasure.",
    "min_level": 2,
    "dc_scaling_factor": 0.5,
    "skill_check_options": [
        {
            "choice_text": "Buy the map for 20 gold (INSIGHT DC 12 to sense deception).",
            "skill": "Insight",
            "base_dc": 12,
            "success_outcome_key": "buy_map_insight_success", # Good map
            "failure_outcome_key": "buy_map_insight_failure"  # Bad map
        },
        {
            "choice_text": "Try to haggle for a lower price (PERSUASION DC 14).",
            "skill": "Persuasion",
            "base_dc": 14,
            "success_outcome_key": "haggle_success", # Cheaper map
            "failure_outcome_key": "haggle_failure"  # Traveler walks off
        },
        {
            "choice_text": "Politely decline the offer.",
            "skill": None, # No skill check needed
            "base_dc": 0,
            "success_outcome_key": "decline_offer",
            "failure_outcome_key": "decline_offer" # Same outcome
        }
    ],
    "outcomes": {
        "buy_map_insight_success": {"message": "The map seems genuine! You pay 20 gold. It reveals a nearby hidden cache.", "effects": {"gold_change": -20, "character_xp_gain": 15, "item_reward": {"name": "Genuine Treasure Map", "quantity": 1, "description": "A map leading to a small treasure.", "base_value": 50, "item_type": "misc", "quality": "Uncommon"}}},
        "buy_map_insight_failure": {"message": "You pay 20 gold, but the map turns out to be a child's drawing.", "effects": {"gold_change": -20, "character_xp_gain": 5, "item_reward": {"name": "Fake Map", "quantity": 1, "description": "A worthless drawing.", "base_value": 0, "item_type": "trash", "quality": "Poor"}}},
        "haggle_success": {"message": "You manage to get the map for only 10 gold! It seems real.", "effects": {"gold_change": -10, "character_xp_gain": 20, "item_reward": {"name": "Genuine Treasure Map", "quantity": 1, "description": "A map leading to a small treasure.", "base_value": 50, "item_type": "misc", "quality": "Uncommon"}}},
        "haggle_failure": {"message": "The traveler scoffs at your offer and walks away.", "effects": {"character_xp_gain": 5}},
        "decline_offer": {"message": "You decline. The traveler shrugs and moves on.", "effects": {"character_xp_gain": 2}}
    }
})

event_ruined_shrine = Event.from_dict({
    "name": "Ruined Shrine",
    "description": "You stumble upon a small, overgrown shrine. It looks like it might collapse, but something glints within.",
    "min_level": 3,
    "dc_scaling_factor": 0.25,
    "skill_check_options": [
        {
            "choice_text": "Carefully search the shrine (INVESTIGATION DC 13).",
            "skill": "Investigation",
            "base_dc": 13,
            "item_requirement": {"name": "Lens of Detection", "effect": "dc_reduction", "value": 3},
            "success_outcome_key": "search_shrine_success",
            "failure_outcome_key": "search_shrine_failure"
        },
        {
            "choice_text": "Try to clear the debris with brute force (ATHLETICS DC 15).",
            "skill": "Athletics",
            "base_dc": 15,
            "success_outcome_key": "force_shrine_success",
            "failure_outcome_key": "force_shrine_failure_injury"
        },
        {
            "choice_text": "Leave it alone, it looks too unstable.",
            "skill": None,
            "base_dc": 0,
            "success_outcome_key": "leave_shrine",
            "failure_outcome_key": "leave_shrine"
        }
    ],
    "outcomes": {
        "search_shrine_success": {"message": "Your careful search reveals a small, tarnished silver locket.", "effects": {"character_xp_gain": 25, "item_reward": {"name": "Silver Locket", "quantity": 1, "description": "An old silver locket.", "base_value": 60, "item_type": "jewelry", "quality": "Uncommon"}}},
        "search_shrine_failure": {"message": "You find nothing but dust and crumbling stones.", "effects": {"character_xp_gain": 5}},
        "force_shrine_success": {"message": "You manage to move some heavy stones and find a sturdy iron lockbox!", "effects": {"character_xp_gain": 20, "item_reward": {"name": "Iron Lockbox (Locked)", "quantity": 1, "description": "A heavy, locked box. Might contain valuables.", "base_value": 10, "item_type": "container", "quality": "Common"}}},
        "force_shrine_failure_injury": {"message": "As you heave a rock, the shrine shifts and a stone falls on your foot! Ouch.", "effects": {"character_xp_gain": 5, "hp_loss": 3}}, # Assuming hp_loss is an effect type character handles
        "leave_shrine": {"message": "You decide not to risk it and leave the shrine undisturbed.", "effects": {"character_xp_gain": 2}}
    }
})

event_merchant_distress = Event.from_dict({
    "name": "Merchant in Distress",
    "description": "You hear a cry for help! A merchant's cart is stuck in the mud, and shadowy figures lurk nearby.",
    "min_level": 1,
    "dc_scaling_factor": 0.0, # No scaling for this one, it's an early event
    "skill_check_options": [
        {
            "choice_text": "Attempt to scare off the figures with a warning shout (INTIMIDATION DC 10).",
            "skill": "Intimidation",
            "base_dc": 10,
            "item_requirement": {"name": "Guard Dog Whistle", "effect": "auto_success"}, # Whistle summons a "visual" deterrent
            "success_outcome_key": "scare_success",
            "failure_outcome_key": "scare_failure"
        },
        {
            "choice_text": "Help the merchant pull the cart free (ATHLETICS DC 12).",
            "skill": "Athletics",
            "base_dc": 12,
            "success_outcome_key": "help_cart_success",
            "failure_outcome_key": "help_cart_failure"
        }
    ],
    "outcomes": {
        "scare_success": {"message": "Your shout, (perhaps aided by the whistle!), makes the figures scatter! The merchant is grateful.", "effects": {"character_xp_gain": 15, "gold_change": 25, "reputation_gain": 5}}, # Assuming reputation_gain is a valid effect
        "scare_failure": {"message": "The figures are undeterred and rob the merchant. You managed to stay out of it.", "effects": {"character_xp_gain": 5}},
        "help_cart_success": {"message": "You help the merchant free the cart. They thank you profusely and give you a small reward.", "effects": {"character_xp_gain": 20, "item_reward": {"name": "Bottle of Fine Wine", "quantity": 1, "description": "A surprisingly good wine.", "base_value": 20, "item_type": "luxury_good", "quality": "Uncommon"}}},
        "help_cart_failure": {"message": "Despite your efforts, the cart remains stuck. The merchant is disappointed.", "effects": {"character_xp_gain": 10}}
    }
})

GAME_EVENTS = [
    event_suspicious_traveler,
    event_ruined_shrine,
    event_merchant_distress
]


if __name__ == "__main__":
    import datetime # Added for MockGameManager timestamping
    print("--- Event System Test ---")
    # Ensure random is available for placeholder skill checks
    import random # Ensure random is imported if not already
    # import datetime # Ensure datetime is imported # Already imported above

    # Simplified Character and Item for testing if full classes are not available
    if 'Character' not in globals() or not hasattr(Character, 'perform_skill_check'):
        print("Using placeholder Character for testing EventManager.")
        class Character: # type: ignore
            def __init__(self, name="Test Player", level=1):
                self.name = name
                self.level = level
                self.stats = {"STR":10,"DEX":10,"CON":10,"INT":10,"WIS":10,"CHA":10}
                # For placeholder, ensure ATTRIBUTE_DEFINITIONS and get_attribute_score exist for skill checks
                self.ATTRIBUTE_DEFINITIONS = {"Stealth": "DEX", "Investigation": "INT", "Intimidation": "CHA", "Athletics": "STR", "Insight": "WIS", "Persuasion": "CHA"} # Simplified
                self.attributes = {skill: (self.stats.get(stat, 10) - 10) // 2 for skill, stat in self.ATTRIBUTE_DEFINITIONS.items()}

                self.stat_bonuses = {}
                self.xp = 0
                self.pending_xp = 0
                self.gold = 100
                self.inventory = []
                self.exhaustion_level = 0 # Needed for disadvantage checks

            def get_effective_stat(self, stat_name): return self.stats.get(stat_name,0) + self.stat_bonuses.get(stat_name,0)

            def get_attribute_score(self, skill_name): # Simplified for placeholder
                 base_stat_name = self.ATTRIBUTE_DEFINITIONS.get(skill_name)
                 if base_stat_name:
                     return (self.stats.get(base_stat_name, 10) -10) // 2
                 return 0


            def _perform_single_roll_placeholder(self, skill_name: str, dc: int) -> dict:
                """Placeholder for the Character class's _perform_single_roll."""
                roll1 = random.randint(1, 20)
                d20_final_roll = roll1
                disadvantage_details_str = ""
                if self.exhaustion_level >= 1:
                    roll2 = random.randint(1, 20)
                    d20_final_roll = min(roll1, roll2)
                    disadvantage_details_str = f"(rolled {roll1},{roll2} dis, took {d20_final_roll})"

                modifier_value = self.get_attribute_score(skill_name)
                total_check_value = d20_final_roll + modifier_value
                is_crit_hit = (d20_final_roll == 20)
                is_crit_fail = (d20_final_roll == 1)
                check_success = (total_check_value >= dc)

                print(f"  P-SKILL CHECK (Placeholder): {skill_name} DC {dc}. Rolled {d20_final_roll}{disadvantage_details_str} + {modifier_value} = {total_check_value}. {'Success' if check_success else 'Failure'}")

                return {
                    "success": check_success, "d20_roll": d20_final_roll, "modifier": modifier_value,
                    "total_value": total_check_value, "dc": dc, "is_critical_hit": is_crit_hit,
                    "is_critical_failure": is_crit_fail, "disadvantage_details": disadvantage_details_str
                }

            def perform_skill_check(self, skill_name: str, dc: int, can_use_reroll_item: bool = True) -> dict:
                """Placeholder for Character.perform_skill_check returning the new dict structure."""
                initial_roll = self._perform_single_roll_placeholder(skill_name, dc)
                final_roll_data = {**initial_roll, "reroll_details": None}

                if not initial_roll["success"] and can_use_reroll_item:
                    # Simplified Lucky Charm check for placeholder
                    lucky_charm_item = next((i for i in self.inventory if "Lucky Charm" in i.name), None)
                    if lucky_charm_item:
                        print(f"  P-PLACEHOLDER: Using Lucky Charm for reroll...")
                        # Assume consumable for placeholder test
                        # self.inventory.remove(lucky_charm_item)

                        reroll_data = self._perform_single_roll_placeholder(skill_name, dc)
                        final_roll_data["reroll_details"] = reroll_data
                        # Update top-level keys with reroll data
                        for key_to_update in ["success", "d20_roll", "modifier", "total_value", "is_critical_hit", "is_critical_failure", "disadvantage_details"]:
                            final_roll_data[key_to_update] = reroll_data[key_to_update]
                return final_roll_data

            def award_xp(self, amount: int):
                # print(f"  P-AWARD_XP: {amount}. Pending XP: {self.pending_xp}") # GameManager prints this now
                self.pending_xp += amount
                # print(f"  P-AWARD_XP: {amount}. Pending XP: {self.pending_xp}") # GameManager prints this now
                return amount

            def commit_pending_xp(self):
                actual = self.pending_xp; self.xp += actual; self.pending_xp = 0
                # print(f"  P-COMMIT_XP: {actual}. Total XP: {self.xp}") # GameManager prints this
                return actual

            def add_item_to_inventory(self, item_to_add):
                self.inventory.append(item_to_add)
                # print(f"  P-ADD_ITEM: {getattr(item_to_add, 'name', 'Unknown Item')} to inventory.") # GameManager prints this

            def remove_specific_item_from_inventory(self, item_to_remove): # Renamed for clarity
                if item_to_remove in self.inventory:
                    self.inventory.remove(item_to_remove)
                    # print(f"  P-REMOVE_ITEM: {getattr(item_to_remove, 'name', 'Unknown Item')} from inventory.") # GameManager prints
                    return True
                # print(f"  P-REMOVE_ITEM: {getattr(item_to_remove, 'name', 'Unknown Item')} not found for removal by instance.")
                return False

            def display_character_info(self): # Keep this for test visibility
                inv_names = [getattr(i, 'name', 'Unknown') for i in self.inventory]
                print(f"  P-INFO (Placeholder Char): {self.name}, Lvl:{self.level}, XP:{self.xp}, PendingXP:{self.pending_xp}, Gold:{self.gold}, Inv:{inv_names[:5]}, Exhaustion: {self.exhaustion_level}")

    if 'Item' not in globals() or not hasattr(Item, 'name'): # Should be fine if Item class is robust
        print("Warning: Using placeholder Item for testing EventManager, but main Item class preferred.")
        class Item: # type: ignore
            def __init__(self, name, description="Test item", base_value=0, item_type="misc", quality="Common", effects=None, is_consumable=False):
                self.name = name
                self.description = description
                self.base_value = base_value
                self.item_type = item_type
                self.quality = quality
                self.effects = effects if effects else {}
                self.is_consumable = is_consumable
            def __repr__(self): return f"Item({self.name})"

    # Test Character Setup
    test_char = Character(name="Test Event Player", level=3) # type: ignore
    # Give character an item for testing item requirements
    # For event_ruined_shrine
    lens_of_detection = Item(name="Lens of Detection", description="Aids in finding hidden things.", item_type="tool", quality="Uncommon") # type: ignore
    test_char.add_item_to_inventory(lens_of_detection)
    # For event_merchant_distress
    dog_whistle = Item(name="Guard Dog Whistle", description="Summons a fierce (looking) hound.", item_type="trinket", quality="Rare") # type: ignore
    test_char.add_item_to_inventory(dog_whistle)

    # For general testing, e.g. if one of the above is consumed or lost
    thieves_tools = Item(name="Thieves' Tools", description="Useful for disarming traps and picking locks.", item_type="tool", quality="Common", effects={"dc_reduction_stealth": 2}) # type: ignore
    invisibility_potion = Item(name="Invisibility Potion", description="Grants invisibility.", item_type="potion", quality="Rare", effects={"auto_success_stealth": True}, is_consumable=True) # type: ignore
    test_char.add_item_to_inventory(thieves_tools)
    test_char.add_item_to_inventory(invisibility_potion)
    if hasattr(test_char, 'display_character_info'): test_char.display_character_info()

    # Mock GameManager for EventManager testing
    if 'MockGameManager' not in globals() or not hasattr(MockGameManager, 'add_journal_entry'):
        class MockGameManager:
            def __init__(self, character_ref): # Store character reference
                self.time_module = lambda: None # Mock time object
                setattr(self.time_module, 'get_current_datetime', datetime.datetime.now)
                self.character = character_ref # EventManager needs character for some operations
                self.journal = []

            def add_journal_entry(self, action_type, summary, details=None, outcome=None, timestamp=None):
                ts = timestamp if timestamp else (self.time_module.get_current_datetime() if hasattr(self.time_module, 'get_current_datetime') else datetime.datetime.now())
                if isinstance(ts, str): ts = datetime.datetime.fromisoformat(ts)

                entry = {"ts": ts, "type": action_type, "summary": summary, "details": details, "outcome": outcome}
                self.journal.append(entry)
                print(f"  MOCK_GM_JOURNAL: Type='{action_type}', Summary='{summary}', Outcome='{outcome}'")
                # print(f"    Details: {details}")


    mock_gm = MockGameManager(character_ref=test_char) # Pass character to Mock GM
    event_manager = EventManager(character=test_char, game_manager=mock_gm)

    # Sample Event from ALL_SKILL_CHECK_EVENTS
    if ALL_SKILL_CHECK_EVENTS:
        test_event_instance = ALL_SKILL_CHECK_EVENTS[2] # event_merchant_distress (index 2)
        # This event uses "Guard Dog Whistle" for auto-success on one choice.
        # The test_char should have this item.

        print(f"\n--- Test Event: {test_event_instance.name} (Player Level: {test_char.level}) ---") # type: ignore
        print(f"Representation: {test_event_instance}")

        # 1. Resolve event to get choices
        print("\n--- Resolving event to get choices: ---")
        available_choices = event_manager.resolve_event(test_event_instance)
        # `resolve_event` already prints the choices with their DCs.

        # 2. Execute a choice (e.g., the first one with Guard Dog Whistle)
        if available_choices:
            print(f"\n--- Executing Choice 0: '{available_choices[0]['text']}' (Should use Guard Dog Whistle) ---")
            if hasattr(test_char, 'display_character_info'): test_char.display_character_info()
            choice_result_0 = event_manager.execute_skill_choice(test_event_instance, 0)
            print(f"Execution Result (Choice 0): {choice_result_0.get('message')}")
            print(f"  Success: {choice_result_0.get('rolled_successfully')}, Outcome Details: {choice_result_0.get('outcome_details')}")
            print(f"  Roll Data: {choice_result_0.get('roll_data')}")
            if hasattr(test_char, 'display_character_info'): test_char.display_character_info()

            # For testing: remove the whistle and try again to see skill check path
            whistle_item = next((item for item in test_char.inventory if item.name == "Guard Dog Whistle"), None)
            if whistle_item:
                test_char.remove_specific_item_from_inventory(whistle_item) # Use specific instance removal
                print(f"  INFO: Removed '{whistle_item.name}' for further testing.")
                if hasattr(test_char, 'display_character_info'): test_char.display_character_info()

                print(f"\n--- Re-Executing Choice 0: '{available_choices[0]['text']}' (Whistle is gone) ---")
                choice_result_0_again = event_manager.execute_skill_choice(test_event_instance, 0)
                print(f"Execution Result (Choice 0 again): {choice_result_0_again.get('message')}")
                print(f"  Success: {choice_result_0_again.get('rolled_successfully')}, Outcome Details: {choice_result_0_again.get('outcome_details')}")
                print(f"  Roll Data: {choice_result_0_again.get('roll_data')}")
                if hasattr(test_char, 'display_character_info'): test_char.display_character_info()


            # 3. Execute the second choice (Athletics check)
            if len(available_choices) > 1:
                print(f"\n--- Executing Choice 1: '{available_choices[1]['text']}' ---")
                if hasattr(test_char, 'display_character_info'): test_char.display_character_info()
                choice_result_1 = event_manager.execute_skill_choice(test_event_instance, 1)
                print(f"Execution Result (Choice 1): {choice_result_1.get('message')}")
                print(f"  Success: {choice_result_1.get('rolled_successfully')}, Outcome Details: {choice_result_1.get('outcome_details')}")
                print(f"  Roll Data: {choice_result_1.get('roll_data')}")
                if hasattr(test_char, 'display_character_info'): test_char.display_character_info()
        else:
            print(f"Event {test_event_instance.name} offered no choices.")
    else:
        print("No events in ALL_SKILL_CHECK_EVENTS to test.")


    # Test direct outcome if no choices (e.g. a simple "Lucky Find" event)
    lucky_find_event_data = {
        "name": "Simple Lucky Find",
        "description": "You found 10 gold!",
        "skill_check_options": [], # No choices
        "outcomes": {"success": {"message": "You pocket 10 gold.", "effects": {"gold_change": 10, "character_xp_gain": 5}}}
    }
    lucky_event = Event.from_dict(lucky_find_event_data)
    print(f"\n--- Testing Direct Outcome Event: {lucky_event.name} ---")
    if hasattr(test_char, 'display_character_info'): test_char.display_character_info() # type: ignore
    direct_outcome_result = event_manager.execute_skill_choice(lucky_event, 0) # choice_index 0 for direct
    print(f"Execution Result (Direct): {direct_outcome_result.get('message')}")
    print(f"  Success: {direct_outcome_result.get('rolled_successfully')}, Details: {direct_outcome_result.get('details')}")
    if hasattr(test_char, 'display_character_info'): test_char.display_character_info() # type: ignore


    if hasattr(test_char, 'commit_pending_xp'): # type: ignore
        print("\n--- Committing XP at end of test ---")
        test_char.commit_pending_xp()
        if hasattr(test_char, 'display_character_info'): test_char.display_character_info()

    print("\n--- Event System Test Complete ---")
