# from .g_event import Event # Would be needed if active_local_events stores Event objects

class Town:
    """
    Represents a town in the Shopkeeper Python game, with unique properties and market conditions.
    """
    def __init__(self, name: str, properties: list[str], nearby_resources: list[str],
                 unique_npc_crafters: list[dict], market_demand_modifiers: dict = None,
                 local_events_schedule: list[dict] = None, sub_locations: list[dict] = None):
        """
        Initializes a new town.

        Args:
            name (str): The name of the town.
            properties (list[str]): Descriptive properties of the town.
            nearby_resources (list[str]): Resources found near the town.
            unique_npc_crafters (list[dict]): NPCs in town with specialties.
            market_demand_modifiers (dict, optional): Modifiers for item prices.
                                                      Keys are item names, values are multipliers.
            local_events_schedule (list[dict], optional): Schedule for fixed local events.
            sub_locations (list[dict], optional): Sub-locations within the town.
        """
        self.name = name
        self.properties = properties if properties is not None else []
        self.nearby_resources = nearby_resources if nearby_resources is not None else []
        self.unique_npc_crafters = unique_npc_crafters if unique_npc_crafters is not None else []
        self.market_demand_modifiers = market_demand_modifiers if market_demand_modifiers is not None else {}
        self.local_events_schedule = local_events_schedule if local_events_schedule is not None else []
        self.sub_locations = sub_locations if sub_locations is not None else []
        self.active_local_events = [] # List of active event objects or structs

        print(f"Town '{self.name}' established.")

    def get_item_price_modifier(self, item_name: str) -> float:
        """
        Returns the effective price modifier for an item in this town.
        Checks for specific item name modifiers.
        Future: Could also check item_type or active_local_events.

        Args:
            item_name (str): The name of the item.

        Returns:
            float: The price modifier (e.g., 1.0 for no change, 1.2 for +20%).
        """
        modifier = self.market_demand_modifiers.get(item_name, 1.0)
        # Placeholder for active event effects on price
        # for event in self.active_local_events:
        #     if hasattr(event, 'price_modifiers') and item_name in event.price_modifiers:
        #         modifier *= event.price_modifiers[item_name]
        return modifier

    def add_active_event(self, event_details): # event_details could be an Event object or a dict
        """Adds a dynamic local event to the town."""
        # For now, let's assume event_details is a simple dict for demonstration
        # In future, this would likely be an Event object from g_event.py
        print(f"Event '{event_details.get('name', 'Unnamed Event')}' started in {self.name}.")
        self.active_local_events.append(event_details)
        # Future: Apply event effects, like temporary market demand changes

    def remove_active_event(self, event_name_to_remove: str):
        """Removes an active local event by its name."""
        event_found = None
        for event in self.active_local_events:
            if event.get('name') == event_name_to_remove:
                event_found = event
                break
        if event_found:
            self.active_local_events.remove(event_found)
            print(f"Event '{event_name_to_remove}' ended in {self.name}.")
        else:
            print(f"Could not find active event '{event_name_to_remove}' to remove in {self.name}.")

    def __repr__(self):
        return f"Town(name='{self.name}', properties={len(self.properties)}, resources={len(self.nearby_resources)}, sub_locations={len(self.sub_locations)})"

if __name__ == "__main__":
    print("--- Town System Test ---")
    town1 = Town(
        name="Starting Village",
        properties=["Quiet farming village", "River nearby"],
        nearby_resources=["Fish", "Wheat", "Basic Herbs"],
        unique_npc_crafters=[
            {"name": "Old Man Hemlock", "specialty": "Herbalism", "services": ["Identifies Herbs"], "quests_available": []}
        ],
        market_demand_modifiers={"Minor Healing Potion": 1.1, "Bread": 0.9},
        sub_locations=[
            {"name": "General Store", "description": "A place to buy and sell goods."},
            {"name": "Town Square", "description": "A central gathering place."}
        ]
    )
    print(town1)
    print(f"  Demand for Minor Healing Potion: {town1.get_item_price_modifier('Minor Healing Potion')}") # Expected 1.1
    print(f"  Demand for Simple Dagger: {town1.get_item_price_modifier('Simple Dagger')}") # Expected 1.0 (default)

    town2 = Town(
        name="Steel Flow City",
        properties=["Major mining hub", "Strong warrior tradition"],
        nearby_resources=["Iron Ore", "Coal", "Stone"],
        unique_npc_crafters=[
            {"name": "Borin Stonebeard", "specialty": "Blacksmithing", "services": ["Repairs Gear", "Sells Metal Ingots"], "quests_available": ["Clear Mine Pests"]}
        ],
        market_demand_modifiers={"Simple Dagger": 1.25, "Iron Sword": 1.3},
        sub_locations=[{"name": "City Market", "description": "A bustling marketplace."}]
    )
    print(town2)
    print(f"  Demand for Simple Dagger in {town2.name}: {town2.get_item_price_modifier('Simple Dagger')}") # Expected 1.25

    # Test active events (conceptual, as Event objects are not fully integrated here yet)
    trade_caravan_event = {"name": "Trade Caravan Arrived", "duration_days": 3, "effects": ["demand_up:exotic_goods"]}
    town1.add_active_event(trade_caravan_event)
    print(f"  Active events in {town1.name}: {town1.active_local_events}")
    town1.remove_active_event("Trade Caravan Arrived")
    print(f"  Active events in {town1.name} after removal: {town1.active_local_events}")

    print("--- Town System Test Complete ---")
