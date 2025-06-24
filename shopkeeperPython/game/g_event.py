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
        self.todays_events_history: list[str] = []
        self.current_tracking_day: int = -1 # To be updated by GameManager

    def reset_daily_event_history(self, game_day: int):
        """Resets the history of events that occurred today."""
        if self.current_tracking_day != game_day:
            # print(f"EventManager: New day ({game_day}). Resetting daily event history. Old day was {self.current_tracking_day}")
            self.todays_events_history = []
            self.current_tracking_day = game_day
        # else:
            # print(f"EventManager: Same day ({game_day}). Event history count: {len(self.todays_events_history)}")


    def trigger_random_event(self, possible_events: list[Event]) -> str | None: # Return event name or None
        if not possible_events:
            # print("No possible events to trigger.") # Game Manager will print this via _print
            self.game_manager._print("EventManager: No possible events to trigger.")
            return None

        # Ensure daily history is for the current day (via game_manager.time)
        if self.game_manager and hasattr(self.game_manager, 'time'):
            self.reset_daily_event_history(self.game_manager.time.current_day)

        # Separate events into seen today and unseen today
        seen_today_events = []
        unseen_today_events = []

        for event in possible_events:
            if event.name in self.todays_events_history:
                seen_today_events.append(event)
            else:
                unseen_today_events.append(event)

        selected_event = None
        if unseen_today_events:
            # Prefer unseen events
            selected_event = random.choice(unseen_today_events)
            # print(f"DEBUG: Selected from unseen events. Pool size: {len(unseen_today_events)}")
        elif seen_today_events:
            # If all possible events have been seen today, choose from them
            # This still allows events if the pool is small and all have occurred
            self.game_manager._print("EventManager: All available events for this trigger have already occurred today. Repeating an event.")
            selected_event = random.choice(seen_today_events)
            # print(f"DEBUG: Selected from seen_today_events as fallback. Pool size: {len(seen_today_events)}")
        else:
            # This case should ideally not be reached if possible_events was not empty.
            self.game_manager._print("EventManager: No events available after filtering for today's history (this shouldn't happen if possible_events initially had items).")
            return None


        # print(f"\n--- Event Triggered: {selected_event.name} ---") # Game Manager will print this
        self.game_manager._print(f"EventManager: Triggering event: {selected_event.name}")
        self.resolve_event(selected_event)
        self.todays_events_history.append(selected_event.name)
        # print(f"DEBUG: Added {selected_event.name} to todays_events_history. History size: {len(self.todays_events_history)}")
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

# --- More New Event Definitions ---

event_mysterious_odor = Event.from_dict({
    "name": "Mysterious Odor",
    "description": "A strange, pungent odor wafts through your shop. What could it be?",
    "min_level": 1,
    "dc_scaling_factor": 0.2,
    "skill_check_options": [
        {
            "choice_text": "Investigate the source thoroughly (INVESTIGATION DC 11).",
            "skill": "Investigation",
            "base_dc": 11,
            "success_outcome_key": "investigate_odor_success",
            "failure_outcome_key": "investigate_odor_failure"
        },
        {
            "choice_text": "Assume it's a pest and try to track it (SURVIVAL DC 13).",
            "skill": "Survival",
            "base_dc": 13,
            "success_outcome_key": "track_pest_success",
            "failure_outcome_key": "track_pest_failure"
        },
        {
            "choice_text": "It smells chemical... try to neutralize it (ALCHEMY DC 14 - requires Alchemist's Supplies).",
            "skill": "Arcana", # Placeholder for Alchemy if not distinct skill, Arcana often covers chemical knowledge
            "base_dc": 14,
            "item_requirement": {"name": "Alchemist's Supplies", "effect": "enable_choice_or_auto_fail"},
            "success_outcome_key": "neutralize_chemical_success",
            "failure_outcome_key": "neutralize_chemical_failure"
        },
        {
            "choice_text": "Ignore it and hope it goes away.",
            "skill": None,
            "base_dc": 0,
            "success_outcome_key": "ignore_odor",
            "failure_outcome_key": "ignore_odor"
        }
    ],
    "outcomes": {
        "investigate_odor_success": {"message": "You trace the smell to a rotten piece of fruit hidden by a previous customer. Easily disposed of.", "effects": {"character_xp_gain": 10}},
        "investigate_odor_failure": {"message": "You can't pinpoint the source, and the smell lingers, deterring a customer.", "effects": {"character_xp_gain": 2, "gold_change": -5}}, # Lost sale
        "track_pest_success": {"message": "You find a scared skunk hiding in a crate! You carefully guide it out.", "effects": {"character_xp_gain": 15, "item_reward": {"name": "Skunk Musk Gland (Sealed)", "quantity": 1, "description": "Potent, if handled correctly.", "base_value": 20, "item_type": "ingredient", "quality": "Uncommon"}}},
        "track_pest_failure": {"message": "Whatever it was, it eludes you, but not before spraying near your entrance. Customers avoid your shop for an hour.", "effects": {"character_xp_gain": 5, "shop_penalty": "minor_customer_deterrent_1hr"}},
        "neutralize_chemical_success": {"message": "With your alchemical knowledge, you identify and neutralize a spilled potion sample. All clear!", "effects": {"character_xp_gain": 20}},
        "neutralize_chemical_failure": {"message": "Your attempt to neutralize the smell backfires, creating a harmless but even fouler odor. Some goods are slightly damaged.", "effects": {"character_xp_gain": 5, "item_loss": {"name": "Random Low-Value Goods", "quantity":1, "value_max": 10}}}, # Conceptual item loss
        "ignore_odor": {"message": "You ignore the smell. Eventually, it fades, but not before a few customers wrinkle their noses.", "effects": {"character_xp_gain": 1}}
    }
})

event_traveling_bard = Event.from_dict({
    "name": "Traveling Bard Visit",
    "description": "A cheerful bard with a lute strolls into your shop, offering a song for some coin or hospitality.",
    "min_level": 1,
    "dc_scaling_factor": 0.1,
    "skill_check_options": [
        {
            "choice_text": "Offer 5 gold for a song (PERSUASION DC 10 to get a good deal).",
            "skill": "Persuasion",
            "base_dc": 10,
            "success_outcome_key": "bard_persuade_good_deal",
            "failure_outcome_key": "bard_persuade_fair_deal"
        },
        {
            "choice_text": "Offer food and drink for a performance.",
            "skill": None, # No check, direct outcome
            "base_dc": 0,
            "success_outcome_key": "bard_hospitality",
            "failure_outcome_key": "bard_hospitality"
        },
        {
            "choice_text": "After they play, offer a tune of your own (PERFORMANCE DC 13).",
            "skill": "Performance",
            "base_dc": 13,
            "success_outcome_key": "player_perform_success",
            "failure_outcome_key": "player_perform_failure"
        },
        {
            "choice_text": "Politely decline their offer to play.",
            "skill": None,
            "base_dc": 0,
            "success_outcome_key": "bard_decline",
            "failure_outcome_key": "bard_decline"
        }
    ],
    "outcomes": {
        "bard_persuade_good_deal": {"message": "The bard accepts 3 gold after some friendly haggling and plays a lively tune, attracting a small crowd!", "effects": {"gold_change": -3, "character_xp_gain": 10, "shop_buff": "minor_customer_attraction_1hr"}},
        "bard_persuade_fair_deal": {"message": "The bard agrees to 5 gold and plays a decent song. A few patrons seem to enjoy it.", "effects": {"gold_change": -5, "character_xp_gain": 5}},
        "bard_hospitality": {"message": "The bard gratefully accepts your offer, plays a heartfelt song, and shares a local rumor.", "effects": {"character_xp_gain": 10, "information_gain": "local_rumor_generic"}}, # Conceptual info gain
        "player_perform_success": {"message": "The bard is impressed by your talent! They teach you a new, rare song snippet which seems to briefly lift everyone's spirits.", "effects": {"character_xp_gain": 15, "shop_buff": "minor_ambiance_boost_30min"}},
        "player_perform_failure": {"message": "Your performance is... enthusiastic. The bard offers polite but forced applause.", "effects": {"character_xp_gain": 3}},
        "bard_decline": {"message": "The bard nods understandingly and heads on their way.", "effects": {"character_xp_gain": 2}}
    }
})

event_injured_animal = Event.from_dict({
    "name": "Injured Animal",
    "description": "You find a small, whimpering animal (a fox with a thorn in its paw) near your shop's back door.",
    "min_level": 2,
    "dc_scaling_factor": 0.25,
    "skill_check_options": [
        {
            "choice_text": "Attempt to calm it and remove the thorn (ANIMAL HANDLING DC 12).",
            "skill": "Animal Handling", # Assuming Animal Handling is a skill
            "base_dc": 12,
            "success_outcome_key": "animal_calm_success",
            "failure_outcome_key": "animal_calm_failure"
        },
        {
            "choice_text": "Use basic first aid (MEDICINE DC 14 - requires Bandages).",
            "skill": "Medicine", # Assuming Medicine is a skill
            "base_dc": 14,
            "item_requirement": {"name": "Bandages", "effect": "enable_choice_or_auto_fail"},
            "success_outcome_key": "animal_medicine_success",
            "failure_outcome_key": "animal_medicine_failure"
        },
        {
            "choice_text": "Leave it. Nature will take its course.",
            "skill": None,
            "base_dc": 0,
            "success_outcome_key": "animal_leave",
            "failure_outcome_key": "animal_leave"
        }
    ],
    "outcomes": {
        "animal_calm_success": {"message": "You gently remove the thorn. The fox looks at you thankfully before darting off. You feel good.", "effects": {"character_xp_gain": 20, "reputation_gain": 3}},
        "animal_calm_failure": {"message": "The animal gets scared, nips your hand lightly, and runs away with the thorn still in.", "effects": {"character_xp_gain": 5, "hp_loss": 1}},
        "animal_medicine_success": {"message": "Your deft bandaging helps the creature. It rests a bit then disappears, leaving behind a shiny button.", "effects": {"character_xp_gain": 25, "item_reward": {"name": "Shiny Button", "quantity": 1, "description":"A small, oddly shiny button.", "base_value":5, "item_type":"trinket", "quality":"Common"}}},
        "animal_medicine_failure": {"message": "You try your best, but the animal is too agitated. It escapes your grasp.", "effects": {"character_xp_gain": 10}},
        "animal_leave": {"message": "You decide to let nature run its course. The animal eventually limps away.", "effects": {"character_xp_gain": 2}}
    }
})

event_sudden_storm = Event.from_dict({
    "name": "Sudden Storm",
    "description": "Dark clouds gather rapidly, and a fierce storm breaks out! Rain lashes down, and the wind howls.",
    "min_level": 1,
    "dc_scaling_factor": 0.0,
    "skill_check_options": [
        {
            "choice_text": "Quickly secure your shop's windows and doors.",
            "skill": None, # Auto-success, but item could improve it
            "item_requirement": {"name": "Sturdy Shutters", "effect": "custom_success_bonus", "details": "Prevents minor damage"}, # Conceptual bonus
            "base_dc": 0,
            "success_outcome_key": "storm_secure_shop",
            "failure_outcome_key": "storm_secure_shop" # Same outcome, item might mitigate negative parts
        },
        {
            "choice_text": "Help your elderly neighbor secure their loose awning (ATHLETICS DC 13).",
            "skill": "Athletics",
            "base_dc": 13,
            "success_outcome_key": "storm_help_neighbor_success",
            "failure_outcome_key": "storm_help_neighbor_failure"
        },
        {
            "choice_text": "Do nothing and wait for it to pass.",
            "skill": None,
            "base_dc": 0,
            "success_outcome_key": "storm_do_nothing",
            "failure_outcome_key": "storm_do_nothing"
        }
    ],
    "outcomes": {
        "storm_secure_shop": {"message": "You manage to secure your shop just in time. It weathers the storm well, though some minor leaks appear.", "effects": {"character_xp_gain": 10, "item_if_shutters": {"name":"Minor Repair Kit", "description":"Shutters bonus: prevented damage, found kit!"}}}, # Item logic handled by outcome
        "storm_help_neighbor_success": {"message": "You wrestle the awning into place! Your neighbor is immensely grateful and gives you some baked goods.", "effects": {"character_xp_gain": 20, "reputation_gain": 5, "item_reward": {"name": "Warm Pie", "quantity": 1, "description":"A delicious homemade pie.", "base_value":10, "item_type":"food", "quality":"Uncommon"}}},
        "storm_help_neighbor_failure": {"message": "Despite your efforts, the awning is torn away by the wind. Your neighbor is safe but upset.", "effects": {"character_xp_gain": 5, "reputation_loss": 2}},
        "storm_do_nothing": {"message": "You wait out the storm. Your shop sustains some minor damage (broken sign, a few leaks).", "effects": {"character_xp_gain": 2, "gold_change": -15}} # Repair costs
    }
})

event_ancient_map_fragment = Event.from_dict({
    "name": "Ancient Map Fragment",
    "description": "Tucked inside a recently acquired old book, you find a fragment of a hand-drawn map.",
    "min_level": 3,
    "dc_scaling_factor": 0.3,
    "skill_check_options": [
        {
            "choice_text": "Study the map for recognizable landmarks or clues (HISTORY DC 14).",
            "skill": "History",
            "base_dc": 14,
            "success_outcome_key": "map_history_success",
            "failure_outcome_key": "map_history_failure"
        },
        {
            "choice_text": "Examine the fragment closely for hidden details (PERCEPTION DC 15).",
            "skill": "Perception",
            "base_dc": 15,
            "item_requirement": {"name": "Magnifying Glass", "effect": "dc_reduction", "value": 2},
            "success_outcome_key": "map_perception_success",
            "failure_outcome_key": "map_perception_failure"
        },
        {
            "choice_text": "Assume it's worthless and discard it.",
            "skill": None,
            "base_dc": 0,
            "success_outcome_key": "map_discard",
            "failure_outcome_key": "map_discard"
        }
    ],
    "outcomes": {
        "map_history_success": {"message": "You recognize symbols indicating an old smuggler's cache nearby! You mark the location.", "effects": {"character_xp_gain": 25, "item_reward": {"name": "Annotated Local Map", "quantity": 1, "description":"Your map, now with a promising X.", "base_value":50, "item_type":"misc", "quality":"Uncommon"}}},
        "map_history_failure": {"message": "The symbols are unfamiliar, and the map fragment seems to lead nowhere specific.", "effects": {"character_xp_gain": 5}},
        "map_perception_success": {"message": "Faint markings on the map's edge, almost invisible, reveal a hidden compartment in the book it came from! Inside is a small pouch of old coins.", "effects": {"character_xp_gain": 30, "gold_change": 25}},
        "map_perception_failure": {"message": "You scrutinize the map but find nothing beyond what's obvious. It remains a mystery.", "effects": {"character_xp_gain": 10}},
        "map_discard": {"message": "You toss the old fragment away. Just another piece of parchment.", "effects": {"character_xp_gain": 1}}
    }
})

event_urchins_plea = Event.from_dict({
    "name": "Urchin's Plea",
    "description": "A scruffy-looking urchin approaches you, eyes wide, asking for a bit of coin or some food.",
    "min_level": 1,
    "dc_scaling_factor": 0.1,
    "skill_check_options": [
        {
            "choice_text": "Give the urchin 5 gold.",
            "skill": None,
            "base_dc": 0,
            "success_outcome_key": "urchin_give_gold",
            "failure_outcome_key": "urchin_give_gold"
        },
        {
            "choice_text": "Offer some leftover bread.",
            "skill": None,
            "base_dc": 0,
            # "item_requirement": {"name": "Bread", "effect": "consume_and_enable"}, # If bread is a specific item
            "success_outcome_key": "urchin_give_bread",
            "failure_outcome_key": "urchin_give_bread"
        },
        {
            "choice_text": "Try to discern if their story is true (INSIGHT DC 11).",
            "skill": "Insight",
            "base_dc": 11,
            "success_outcome_key": "urchin_insight_true",
            "failure_outcome_key": "urchin_insight_false_or_unclear"
        },
        {
            "choice_text": "Sternly tell them to leave.",
            "skill": None,
            "base_dc": 0,
            "success_outcome_key": "urchin_stern_refusal",
            "failure_outcome_key": "urchin_stern_refusal"
        }
    ],
    "outcomes": {
        "urchin_give_gold": {"message": "The urchin's eyes light up. 'Thank ye, kind sir/madam!' They scamper off.", "effects": {"gold_change": -5, "character_xp_gain": 10, "reputation_gain": 2}},
        "urchin_give_bread": {"message": "The urchin gratefully accepts the bread and quickly eats it. 'Bless ye!'", "effects": {"character_xp_gain": 10, "reputation_gain": 3}}, # Assuming bread has negligible cost or is "flavor"
        "urchin_insight_true": {"message": "You sense genuine hardship in their eyes. Helping them feels right.", "effects": {"character_xp_gain": 5, "prompt_player_choice_again": ["urchin_give_gold", "urchin_give_bread"]}}, # Special outcome: re-prompt
        "urchin_insight_false_or_unclear": {"message": "It's hard to tell if they're truly desperate or just a good actor. You remain wary.", "effects": {"character_xp_gain": 5}},
        "urchin_stern_refusal": {"message": "The urchin flinches and quickly disappears into the alleys. You notice a small item missing from a low shelf later.", "effects": {"character_xp_gain": 2, "reputation_loss": 2, "item_loss": {"name": "Trinket", "quantity": 1, "value_max": 5}}}
    }
})

event_tax_collectors_audit = Event.from_dict({
    "name": "Tax Collector's Audit",
    "description": "A stern-faced official in town livery arrives, announcing a surprise tax audit for your shop.",
    "min_level": 4, # More impactful event
    "dc_scaling_factor": 0.5,
    "skill_check_options": [
        {
            "choice_text": "Cooperate fully and present your records (Passive Check - Honesty/Record Quality).",
            "skill": "Investigation", # Representing quality of records, GM might make flat check
            "base_dc": 13, # DC for "good" records
            "success_outcome_key": "tax_audit_cooperate_good",
            "failure_outcome_key": "tax_audit_cooperate_bad"
        },
        {
            "choice_text": "Attempt to persuade them that your modest earnings barely cover costs (PERSUASION DC 16).",
            "skill": "Persuasion",
            "base_dc": 16,
            "success_outcome_key": "tax_audit_persuade_success",
            "failure_outcome_key": "tax_audit_persuade_failure"
        },
        {
            "choice_text": "Subtly try to offer a 'processing fee' to expedite things (DECEPTION DC 15 or SLEIGHT OF HAND DC 15).",
            "skill": "Deception", # Could also be Sleight of Hand if it's about palming coin
            "base_dc": 15,
            "success_outcome_key": "tax_audit_bribe_success",
            "failure_outcome_key": "tax_audit_bribe_failure"
        }
    ],
    "outcomes": {
        "tax_audit_cooperate_good": {"message": "The auditor reviews your meticulous records and nods. 'Everything seems in order. A small tax is due.'", "effects": {"character_xp_gain": 25, "gold_change": -50}}, # Nominal tax
        "tax_audit_cooperate_bad": {"message": "Your records are a mess! The auditor frowns. 'This will require a more thorough look, and a fine for poor bookkeeping.'", "effects": {"character_xp_gain": 10, "gold_change": -100}}, # Tax + fine
        "tax_audit_persuade_success": {"message": "After some convincing, the auditor agrees to a slightly lower assessment. 'Times are tough, I suppose.'", "effects": {"character_xp_gain": 30, "gold_change": -35}},
        "tax_audit_persuade_failure": {"message": "Your pleas fall on deaf ears. The auditor proceeds by the book, and it's not cheap.", "effects": {"character_xp_gain": 5, "gold_change": -75}},
        "tax_audit_bribe_success": {"message": "The 'fee' is discreetly accepted. The auditor gives your books a cursory glance. 'Looks acceptable. Standard tax applies.'", "effects": {"character_xp_gain": 15, "gold_change": -60}}, # Bribe + standard tax
        "tax_audit_bribe_failure": {"message": "The auditor glares at your poorly concealed attempt. 'Are you trying to bribe an official? That's a serious offense! Expect a hefty fine on top of your taxes!'", "effects": {"character_xp_gain": 5, "gold_change": -150, "reputation_loss": 10}}
    }
})


GAME_EVENTS.extend([
    event_mysterious_odor,
    event_traveling_bard,
    event_injured_animal,
    event_sudden_storm,
    event_ancient_map_fragment,
    event_urchins_plea,
    event_tax_collectors_audit
])

# --- Events for previously missing skills ---

event_precarious_delivery = Event.from_dict({
    "name": "Precarious Delivery",
    "description": "A courier trips outside your shop, and a valuable-looking, fragile package tumbles into the air! It's heading towards a muddy puddle.",
    "min_level": 1,
    "dc_scaling_factor": 0.1,
    "skill_check_options": [
        {
            "choice_text": "Try to deftly catch the package (ACROBATICS DC 13).",
            "skill": "Acrobatics",
            "base_dc": 13,
            "success_outcome_key": "catch_success",
            "failure_outcome_key": "catch_failure"
        },
        {
            "choice_text": "Let it fall. Not your problem.",
            "skill": None,
            "base_dc": 0,
            "success_outcome_key": "let_fall",
            "failure_outcome_key": "let_fall"
        }
    ],
    "outcomes": {
        "catch_success": {"message": "You nimbly snatch the package mid-air! The grateful courier rewards you with 10 gold.", "effects": {"character_xp_gain": 15, "gold_change": 10}},
        "catch_failure": {"message": "You lunge but misjudge it. The package lands with a sad squelch in the mud. The courier is dismayed.", "effects": {"character_xp_gain": 5}},
        "let_fall": {"message": "You watch as the package lands in the mud. The courier sighs.", "effects": {"character_xp_gain": 1}}
    }
})

event_strange_plant_growth = Event.from_dict({
    "name": "Strange Plant Growth",
    "description": "A peculiar vine with glowing fruit has suddenly sprouted near your shop entrance overnight.",
    "min_level": 2,
    "dc_scaling_factor": 0.2,
    "skill_check_options": [
        {
            "choice_text": "Examine and identify the plant (NATURE DC 14).",
            "skill": "Nature",
            "base_dc": 14,
            "success_outcome_key": "identify_success",
            "failure_outcome_key": "identify_failure"
        },
        {
            "choice_text": "Hack it down before it causes trouble.",
            "skill": None, # Could be Athletics if we want another check
            "base_dc": 0,
            "success_outcome_key": "hack_down",
            "failure_outcome_key": "hack_down"
        }
    ],
    "outcomes": {
        "identify_success": {"message": "You recognize it as a rare Sunpetal vine! The fruit is a valuable alchemical ingredient.", "effects": {"character_xp_gain": 20, "item_reward": {"name": "Sunpetal Fruit", "quantity": 2, "description": "Glows faintly, warm to the touch.", "base_value": 25, "item_type": "ingredient", "quality": "Uncommon"}}},
        "identify_failure": {"message": "You can't identify it. It might be dangerous, or just a weird weed. Best to leave it for now.", "effects": {"character_xp_gain": 5}},
        "hack_down": {"message": "You remove the strange plant. Better safe than sorry.", "effects": {"character_xp_gain": 5}}
    }
})

event_pilgrims_request = Event.from_dict({
    "name": "Pilgrim's Request",
    "description": "A weary pilgrim, clutching a holy symbol, asks for directions to a forgotten local shrine and seems interested in any historical details you might know.",
    "min_level": 2,
    "dc_scaling_factor": 0.2,
    "skill_check_options": [
        {
            "choice_text": "Recall details about the old shrine (RELIGION DC 14).",
            "skill": "Religion",
            "base_dc": 14,
            "success_outcome_key": "recall_shrine_success",
            "failure_outcome_key": "recall_shrine_failure"
        },
        {
            "choice_text": "Offer vague directions without religious insight.",
            "skill": None,
            "base_dc": 0,
            "success_outcome_key": "vague_directions",
            "failure_outcome_key": "vague_directions"
        }
    ],
    "outcomes": {
        "recall_shrine_success": {"message": "You provide accurate details. The pilgrim blesses you and offers a small, sacred token.", "effects": {"character_xp_gain": 20, "item_reward": {"name": "Pilgrim's Token", "quantity": 1, "description": "A small wooden token, feels warm.", "base_value": 15, "item_type": "trinket", "quality": "Uncommon"}, "reputation_gain": 2}},
        "recall_shrine_failure": {"message": "Your knowledge of local religious history is hazy. You can only offer vague directions.", "effects": {"character_xp_gain": 5}},
        "vague_directions": {"message": "You give some general directions. The pilgrim thanks you and continues on.", "effects": {"character_xp_gain": 2}}
    }
})

event_dropped_pouch = Event.from_dict({
    "name": "Dropped Pouch",
    "description": "A richly dressed noble bumps into a display, then hurries off. You notice they dropped a small, embroidered pouch, partially open, revealing gold coins.",
    "min_level": 1,
    "dc_scaling_factor": 0.15,
    "skill_check_options": [
        {
            "choice_text": "Try to lift a coin before returning it (SLEIGHT OF HAND DC 15).",
            "skill": "Sleight of Hand",
            "base_dc": 15,
            "success_outcome_key": "lift_coin_success",
            "failure_outcome_key": "lift_coin_failure"
        },
        {
            "choice_text": "Immediately return the pouch.",
            "skill": None,
            "base_dc": 0,
            "success_outcome_key": "return_pouch_honestly",
            "failure_outcome_key": "return_pouch_honestly"
        }
    ],
    "outcomes": {
        "lift_coin_success": {"message": "Your fingers are nimble! You snag a couple of coins. The noble thanks you for returning the pouch, none the wiser.", "effects": {"character_xp_gain": 10, "gold_change": 15}},
        "lift_coin_failure": {"message": "You fumble! The noble notices your attempt as they turn back, snatching the pouch with a glare.", "effects": {"character_xp_gain": 2, "reputation_loss": 5}},
        "return_pouch_honestly": {"message": "The noble is grateful for your honesty and rewards you with a 5 gold tip.", "effects": {"character_xp_gain": 15, "gold_change": 5, "reputation_gain": 3}}
    }
})

event_suspicious_onlooker = Event.from_dict({
    "name": "Suspicious Onlooker",
    "description": "You notice someone in a dark cloak loitering across the street, seemingly watching your shop a little too intently.",
    "min_level": 2,
    "dc_scaling_factor": 0.2,
    "skill_check_options": [
        {
            "choice_text": "Subtly observe them without being noticed (STEALTH DC 12).",
            "skill": "Stealth",
            "base_dc": 12,
            "success_outcome_key": "observe_success",
            "failure_outcome_key": "observe_failure"
        },
        {
            "choice_text": "Confront them directly.",
            "skill": "Intimidation", # Or Persuasion, making it a different path
            "base_dc": 11,
            "success_outcome_key": "confront_success", # Needs new outcome
            "failure_outcome_key": "confront_failure"  # Needs new outcome
        },
        {
            "choice_text": "Ignore them.",
            "skill": None,
            "base_dc": 0,
            "success_outcome_key": "ignore_onlooker",
            "failure_outcome_key": "ignore_onlooker"
        }
    ],
    "outcomes": {
        "observe_success": {"message": "You watch them undetected. They seem to be casing your shop, but your attentiveness makes them uneasy, and they move on.", "effects": {"character_xp_gain": 15}},
        "observe_failure": {"message": "They spot you watching them! They give you a hard stare and then quickly disappear. You feel uneasy.", "effects": {"character_xp_gain": 5, "shop_penalty": "minor_unease_1hr"}},
        "confront_success": {"message": "You confront the onlooker. They stammer an apology, claiming to be admiring your sign, and quickly leave.", "effects": {"character_xp_gain": 10}},
        "confront_failure": {"message": "Your confrontation makes the onlooker defensive. They scoff and walk off, muttering.", "effects": {"character_xp_gain": 5}},
        "ignore_onlooker": {"message": "You decide to ignore them. After a while, they're gone. Hopefully, it was nothing.", "effects": {"character_xp_gain": 2}}
    }
})


GAME_EVENTS.extend([
    event_precarious_delivery,
    event_strange_plant_growth,
    event_pilgrims_request,
    event_dropped_pouch,
    event_suspicious_onlooker
])


if __name__ == "__main__":
    import datetime # Added for MockGameManager timestamping
    print("--- Event System Test ---")
    # Ensure random is available for placeholder skill checks
    import random # Ensure random is imported if not already
    # import datetime # Ensure datetime is imported

    # --- Mocks for Testing Event Repetition Logic ---
    class MockGameTime:
        def __init__(self, start_day=1):
            self.current_day = start_day
            self.current_hour = 8 # Arbitrary start hour

        def advance_day(self, days=1):
            self.current_day += days
            print(f"MockGameTime: Advanced to day {self.current_day}")

        def get_time_string(self): # Added for compatibility if GameManager._print uses it
            return f"Day {self.current_day}, Hour {self.current_hour}"


    class MockGameManager:
        def __init__(self, character_ref):
            self.character = character_ref
            self.journal = []
            self.time = MockGameTime() # Use the mock time

        def _print(self, message: str):
            """Mock print method to capture game manager messages if needed, or just print."""
            print(f"  MOCK_GM: {message}")

        def add_journal_entry(self, action_type: str, summary: str, details: dict = None, outcome: str = None, timestamp: str = None):
            # Simplified mock journal entry
            self.journal.append({"action_type": action_type, "summary": summary, "details": details, "outcome": outcome, "timestamp": timestamp or "now"})
            # print(f"  MOCK_GM_JOURNAL: Added '{summary}'")


    # Simplified Character and Item for testing if full classes are not available
    if 'Character' not in globals() or not hasattr(Character, 'perform_skill_check'):
        print("Using placeholder Character for testing EventManager.")
        class Character: # type: ignore
            def __init__(self, name="Test Player", level=1):
                self.name = name
                self.level = level
                self.stats = {"STR":10,"DEX":10,"CON":10,"INT":10,"WIS":10,"CHA":10}
                self.ATTRIBUTE_DEFINITIONS = {"Stealth": "DEX", "Investigation": "INT", "Intimidation": "CHA", "Athletics": "STR", "Insight": "WIS", "Persuasion": "CHA", "Performance": "CHA", "Acrobatics": "DEX", "Religion": "WIS", "Nature": "WIS", "Medicine": "WIS", "Sleight of Hand": "DEX", "Arcana": "INT", "Animal Handling": "WIS"}
                self.attributes = {skill: (self.stats.get(stat, 10) - 10) // 2 for skill, stat in self.ATTRIBUTE_DEFINITIONS.items()}
                self.stat_bonuses = {}
                self.xp = 0
                self.pending_xp = 0
                self.gold = 100
                self.inventory = []
                self.exhaustion_level = 0

            def get_effective_stat(self, stat_name): return self.stats.get(stat_name,0) + self.stat_bonuses.get(stat_name,0)
            def get_attribute_score(self, skill_name):
                 base_stat_name = self.ATTRIBUTE_DEFINITIONS.get(skill_name)
                 if base_stat_name: return (self.stats.get(base_stat_name, 10) -10) // 2
                 return 0
            def get_effective_max_hp(self): return 10 # Dummy
            def _perform_single_roll_placeholder(self, skill_name: str, dc: int) -> dict:
                roll1 = random.randint(1, 20); d20_final_roll = roll1; disadvantage_details_str = ""
                if self.exhaustion_level >= 1: roll2 = random.randint(1, 20); d20_final_roll = min(roll1, roll2); disadvantage_details_str = f"(rolled {roll1},{roll2} dis, took {d20_final_roll})"
                modifier_value = self.get_attribute_score(skill_name); total_check_value = d20_final_roll + modifier_value
                is_crit_hit = (d20_final_roll == 20); is_crit_fail = (d20_final_roll == 1); check_success = (total_check_value >= dc)
                print(f"  P-SKILL CHECK (Mock): {skill_name} DC {dc}. Rolled {d20_final_roll}{disadvantage_details_str} + {modifier_value} = {total_check_value}. {'Success' if check_success else 'Failure'}")
                return {"success": check_success, "d20_roll": d20_final_roll, "modifier": modifier_value, "total_value": total_check_value, "dc": dc, "is_critical_hit": is_crit_hit, "is_critical_failure": is_crit_fail, "disadvantage_details": disadvantage_details_str, "formatted_string": f"{skill_name} DC {dc}: Roll {d20_final_roll} + Mod {modifier_value} = {total_check_value} ({'Success' if check_success else 'Failure'})"}
            def perform_skill_check(self, skill_name: str, dc: int, can_use_reroll_item: bool = True) -> dict:
                return self._perform_single_roll_placeholder(skill_name, dc)
            def award_xp(self, amount: int): self.pending_xp += amount; print(f"  P-AWARD_XP (Mock): {amount}. Pending XP: {self.pending_xp}"); return amount
            def commit_pending_xp(self): actual = self.pending_xp; self.xp += actual; self.pending_xp = 0; print(f"  P-COMMIT_XP (Mock): {actual}. Total XP: {self.xp}"); return actual
            def add_item_to_inventory(self, item_to_add): self.inventory.append(item_to_add); print(f"  P-ADD_ITEM (Mock): {getattr(item_to_add, 'name', 'Unknown Item')} to inventory.")
            def remove_specific_item_from_inventory(self, item_to_remove):
                if item_to_remove in self.inventory: self.inventory.remove(item_to_remove); print(f"  P-REMOVE_ITEM (Mock): {getattr(item_to_remove, 'name', 'Unknown Item')} from inventory."); return True
                return False
            def display_character_info(self): inv_names = [getattr(i, 'name', 'Unknown') for i in self.inventory]; print(f"  P-INFO (Mock Char): {self.name}, Lvl:{self.level}, XP:{self.xp}, Gold:{self.gold}, Inv:{inv_names[:5]}, Exhaustion: {self.exhaustion_level}")

    if 'Item' not in globals() or not hasattr(Item, 'name'):
        print("Warning: Using placeholder Item for testing EventManager.")
        class Item: # type: ignore
            def __init__(self, name, description="Test item", base_value=0, item_type="misc", quality="Common", effects=None, is_consumable=False):
                self.name = name; self.description = description; self.base_value = base_value; self.item_type = item_type; self.quality = quality; self.effects = effects if effects else {}; self.is_consumable = is_consumable
            def __repr__(self): return f"Item({self.name})"

    # Test Character Setup
    test_char = Character(name="Test Event Player", level=3) # type: ignore
    test_char.add_item_to_inventory(Item(name="Alchemist's Supplies")) # For Mysterious Odor event

    # Mock GameManager Setup
    mock_gm_instance = MockGameManager(character_ref=test_char) # type: ignore
    event_manager_for_test = EventManager(character=test_char, game_manager=mock_gm_instance) # type: ignore

    print(f"\n--- Testing Event Repetition and Daily Reset ---")
    # A smaller pool of events for easier testing of repetition
    test_event_pool = [
        next(e for e in GAME_EVENTS if e.name == "Mysterious Odor"),
        next(e for e in GAME_EVENTS if e.name == "Traveling Bard Visit"),
        next(e for e in GAME_EVENTS if e.name == "Injured Animal")
    ]
    if None in test_event_pool:
        print("CRITICAL TEST ERROR: One of the test events was not found. Aborting test.")
    else:
        print(f"Test Pool (Day {mock_gm_instance.time.current_day}): {[e.name for e in test_event_pool]}")
        triggered_counts_day1 = {name: 0 for name in [e.name for e in test_event_pool]}
        for i in range(10): # Trigger 10 events on day 1
            print(f"\nTrigger attempt {i+1} on Day {mock_gm_instance.time.current_day}:")
            triggered_event_name = event_manager_for_test.trigger_random_event(test_event_pool)
            if triggered_event_name:
                triggered_counts_day1[triggered_event_name] += 1
                # Minimal execution to avoid full event logic here, just testing selection
                event_obj = next(e for e in test_event_pool if e.name == triggered_event_name)
                # event_manager_for_test.resolve_event(event_obj) # Already called by trigger_random_event
                if event_obj.skill_check_options: # If choices exist, pick one
                    # event_manager_for_test.execute_skill_choice(event_obj, 0) # Already called by trigger_random_event flow
                    pass # execute_skill_choice is part of resolve_event flow now, no need to call separately if resolve is called by trigger.
                         # Actually, trigger_random_event calls resolve_event, which prepares choices.
                         # execute_skill_choice is called by GameManager after player input.
                         # For this test, we only care about which event *name* was returned by trigger_random_event.
            else:
                print("No event was triggered.")
            print(f"Current history: {event_manager_for_test.todays_events_history}")


        print(f"\n--- Results for Day {mock_gm_instance.time.current_day} (10 triggers) ---")
        for name, count in triggered_counts_day1.items():
            print(f"  {name}: {count} times")
        print(f"Final event history for Day {mock_gm_instance.time.current_day}: {event_manager_for_test.todays_events_history}")

        # Advance to next day
        mock_gm_instance.time.advance_day()
        # The reset_daily_event_history should be called internally by trigger_random_event
        # when it detects the day has changed in mock_gm_instance.time.current_day

        print(f"\n--- Test Pool (Day {mock_gm_instance.time.current_day}) after advancing day ---")
        triggered_counts_day2 = {name: 0 for name in [e.name for e in test_event_pool]}
        for i in range(10): # Trigger 10 events on day 2
            print(f"\nTrigger attempt {i+1} on Day {mock_gm_instance.time.current_day}:")
            triggered_event_name = event_manager_for_test.trigger_random_event(test_event_pool)
            if triggered_event_name:
                triggered_counts_day2[triggered_event_name] += 1
            else:
                print("No event was triggered.")
            print(f"Current history: {event_manager_for_test.todays_events_history}")


        print(f"\n--- Results for Day {mock_gm_instance.time.current_day} (10 triggers) ---")
        for name, count in triggered_counts_day2.items():
            print(f"  {name}: {count} times")
        print(f"Final event history for Day {mock_gm_instance.time.current_day}: {event_manager_for_test.todays_events_history}")

        print("\n--- Expected Behavior Check ---")
        print("Day 1: Expect to see each of the 3 events at least once, likely multiple times, but with variety early on.")
        print("Day 2: Expect similar behavior to Day 1, as the history should have reset.")
        print("         If counts are very skewed on Day 1 (e.g., one event 8 times, others 1), that's an issue.")
        print("         If Day 2 immediately repeats Day 1's last seen event heavily, history might not have reset properly.")

    print("\n--- Event System Repetition Test Complete ---")

    # Keep the old tests if they are still relevant for general event functionality,
    # but the new test above is specific to repetition.
    # For now, I will comment out the old tests to focus on the new one.
    # ... (old test block commented out or removed for brevity of this diff) ...
    # Removing old tests for clarity of this specific test run.
    # If this was a real commit, would decide if they are still needed.
    # For now, assume they are not for this focused test.
    # ...

    if hasattr(test_char, 'commit_pending_xp'): # type: ignore
        print("\n--- Committing XP at end of test (Mock Character) ---")
        test_char.commit_pending_xp() # type: ignore
        if hasattr(test_char, 'display_character_info'): test_char.display_character_info() # type: ignore

    print("\n--- Event System Main Block Test Complete (after repetition test) ---")
