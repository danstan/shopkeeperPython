QUALITY_TIERS = ["Common", "Uncommon", "Rare", "Very Rare", "Legendary", "Mythical"]
QUALITY_VALUE_MULTIPLIERS = {
    "Common": 1.0,
    "Uncommon": 1.5,
    "Rare": 2.5,
    "Very Rare": 5.0,
    "Legendary": 10.0,
    "Mythical": 25.0
}

class Item:
    """
    Represents an item in the Shopkeeper Python game.
    """
    def __init__(self, name: str, description: str, base_value: int, item_type: str, quality: str,
                 effects: dict = None, is_magical: bool = False, is_attunement: bool = False, is_consumable: bool = False):
        """
        Initializes a new item.

        Args:
            name: The name of the item.
            description: A description of the item.
            base_value: The base gold value of the item.
            item_type: The type of item (e.g., "potion", "weapon").
            quality: The quality of the item (e.g., "Common", "Uncommon").
            effects: A dictionary describing the item's effects.
            is_magical: Whether the item is magical.
            is_attunement: Whether the item requires attunement.
            is_consumable: Whether the item is consumable.
        """
        self.name = name
        self.description = description
        self.base_value = base_value
        self.item_type = item_type
        if quality not in QUALITY_TIERS:
            raise ValueError(f"Invalid quality: {quality}. Must be one of {QUALITY_TIERS}")
        self.quality = quality
        self.effects = effects if effects else {}
        self.is_magical = is_magical
        self.is_attunement = is_attunement
        self.is_consumable = is_consumable

        # Actual value considering quality
        self.value = int(self.base_value * QUALITY_VALUE_MULTIPLIERS.get(self.quality, 1.0))

    def __repr__(self):
        """
        Returns a string representation of the item.
        """
        return (f"Item(name='{self.name}', type='{self.item_type}', quality='{self.quality}', value={self.value}, "
                f"magical={self.is_magical}, attunement={self.is_attunement}, consumable={self.is_consumable}, effects={self.effects})")

if __name__ == "__main__":
    print("Quality Tiers:", QUALITY_TIERS)
    print("Quality Multipliers:", QUALITY_VALUE_MULTIPLIERS)

    # Example Usage
    potion_old = Item(
        name="Minor Healing Potion (Old)",
        description="A simple potion that heals minor wounds.",
        base_value=10,
        item_type="potion",
        quality="Common",
        effects={"healing": 5} # is_consumable will be False by default
    )
    print(potion_old)

    sword = Item(
        name="Iron Shortsword",
        description="A basic iron shortsword.",
        base_value=15,
        item_type="weapon",
        quality="Uncommon",
        effects={"damage_boost": "1d4"}, # Example effect
        is_magical=False # Explicitly non-magical
    )
    print(sword)

    try:
        bad_item = Item("Broken Hilt", "Useless", 1, "junk", "Awful", is_magical=False)
    except ValueError as e:
        print(f"Error creating item: {e}")

    legendary_arrow = Item(
        name="Arrow of Slaying",
        description="An arrow that can slay mighty beasts.",
        base_value=100,
        item_type="ammunition",
        quality="Legendary",
        effects={"instant_kill_chance": 0.05},
        is_magical=True,
        is_consumable=True # Typically arrows are consumable
    )
    print(legendary_arrow)

    print("\n--- New Item Examples ---")
    ring_of_protection = Item(
        name="Ring of Protection",
        description="Grants +1 to AC",
        base_value=500,
        item_type="ring",
        quality="Uncommon",
        effects={"ac_bonus": 1},
        is_magical=True,
        is_attunement=True
    )
    print(ring_of_protection)

    potion_of_healing = Item(
        name="Potion of Healing",
        description="Restores 10 HP",
        base_value=50,
        item_type="potion",
        quality="Common",
        effects={"heal_hp": 10},
        is_consumable=True,
        is_magical=True # Potions are often considered magical
    )
    print(potion_of_healing)

    scroll_of_fireball = Item(
        name="Scroll of Fireball",
        description="Casts Fireball spell",
        base_value=150,
        item_type="scroll",
        quality="Rare",
        effects={"cast_spell": "Fireball"},
        is_consumable=True,
        is_magical=True
    )
    print(scroll_of_fireball)
