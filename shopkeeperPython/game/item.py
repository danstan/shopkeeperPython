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
                 effects: dict = None, is_magical: bool = False, is_attunement: bool = False, is_consumable: bool = False, quantity: int = 1):
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
        self.quantity = quantity
        self.value = int(self.base_value * QUALITY_VALUE_MULTIPLIERS.get(self.quality, 1.0))

    def __repr__(self):
        return (f"Item(name='{self.name}', type='{self.item_type}', quality='{self.quality}', value={self.value}, "
                f"magical={self.is_magical}, attunement={self.is_attunement}, consumable={self.is_consumable}, quantity={self.quantity}, effects={self.effects})")

    def to_dict(self):
        """Converts the item object to a dictionary for JSON serialization."""
        return {
            "name": self.name,
            "description": self.description,
            "base_value": self.base_value,
            "item_type": self.item_type,
            "quality": self.quality,
            "effects": self.effects,
            "is_magical": self.is_magical,
            "is_attunement": self.is_attunement,
            "is_consumable": self.is_consumable,
            "quantity": self.quantity,
            # self.value is derived so not saved
        }

    @classmethod
    def from_dict(cls, data: dict):
        """Creates an Item instance from a dictionary."""
        return cls(
            name=data["name"],
            description=data["description"],
            base_value=data["base_value"],
            item_type=data["item_type"],
            quality=data["quality"],
            effects=data.get("effects", {}), # Use .get for potentially missing keys in older saves
            is_magical=data.get("is_magical", False),
            is_attunement=data.get("is_attunement", False),
            is_consumable=data.get("is_consumable", False),
            quantity=data.get("quantity", 1)  # Default to 1 if not found
        )

if __name__ == "__main__":
    print("Quality Tiers:", QUALITY_TIERS)
    print("Quality Multipliers:", QUALITY_VALUE_MULTIPLIERS)

    potion_old = Item(
        name="Minor Healing Potion (Old)", description="A simple potion that heals minor wounds.",
        base_value=10, item_type="potion", quality="Common", effects={"healing": 5}, quantity=3
    )
    print(potion_old)
    assert potion_old.quantity == 3
    potion_dict = potion_old.to_dict()
    assert potion_dict["quantity"] == 3
    print("Serialized Potion:", potion_dict)
    potion_from_dict = Item.from_dict(potion_dict)
    print("Deserialized Potion:", potion_from_dict)
    assert potion_from_dict.name == potion_old.name
    assert potion_from_dict.value == potion_old.value # value is recalculated
    assert potion_from_dict.quantity == 3

    # Test deserialization of an item without quantity (should default to 1)
    potion_dict_no_quantity = potion_dict.copy()
    del potion_dict_no_quantity["quantity"]
    potion_from_dict_no_quantity = Item.from_dict(potion_dict_no_quantity)
    print("Deserialized Potion (no quantity):", potion_from_dict_no_quantity)
    assert potion_from_dict_no_quantity.quantity == 1


    sword = Item(
        name="Iron Shortsword", description="A basic iron shortsword.", base_value=15,
        item_type="weapon", quality="Uncommon", effects={"damage_boost": "1d4"}, is_magical=False
    )
    print(sword)
    sword_dict = sword.to_dict()
    print("Serialized Sword:", sword_dict)
    sword_from_dict = Item.from_dict(sword_dict)
    print("Deserialized Sword:", sword_from_dict)
    assert sword_from_dict.is_magical == sword.is_magical

    print("\n--- New Item Examples ---")
    ring_of_protection = Item(
        name="Ring of Protection", description="Grants +1 to AC", base_value=500, item_type="ring",
        quality="Uncommon", effects={"ac_bonus": 1}, is_magical=True, is_attunement=True
    )
    print(ring_of_protection)
    ring_dict = ring_of_protection.to_dict()
    print("Serialized Ring:", ring_dict)
    ring_from_dict = Item.from_dict(ring_dict)
    print("Deserialized Ring:", ring_from_dict)
    assert ring_from_dict.is_attunement == ring_of_protection.is_attunement
    assert ring_from_dict.effects == ring_of_protection.effects

    # Test with minimal data (e.g. from an older save format if these fields were optional)
    minimal_data = {
        "name": "Basic Arrow", "description": "A simple arrow.", "base_value": 1,
        "item_type": "ammunition", "quality": "Common" # quantity will default to 1
    }
    arrow_from_minimal = Item.from_dict(minimal_data)
    print("Deserialized Arrow from minimal data:", arrow_from_minimal)
    assert arrow_from_minimal.is_magical is False # Check default
    assert arrow_from_minimal.effects == {}       # Check default
    assert arrow_from_minimal.quantity == 1       # Check default quantity

    print("\n--- Serialization/Deserialization Test Complete ---")
