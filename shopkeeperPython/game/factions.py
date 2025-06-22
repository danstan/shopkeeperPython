FACTION_DEFINITIONS = [
    {
        "id": "merchants_guild",
        "name": "The Merchant's Guild",
        "description": "An organization dedicated to commerce and mutual prosperity among traders.",
        "ranks": [
            {"name": "Applicant", "reputation_needed": 0},
            {"name": "Associate", "reputation_needed": 50, "benefits": [{"type": "shop_discount", "value_percentage": 5, "scope": "guild_affiliated_shops"}]},
            {"name": "Full Member", "reputation_needed": 150, "benefits": [{"type": "shop_discount", "value_percentage": 10, "scope": "guild_affiliated_shops"}, {"type": "access_exclusive_wares"}]}
        ],
        "join_requirements": [
            {"type": "gold_payment", "amount": 50},
            {"type": "skill_check", "skill": "Persuasion", "dc": 10}
        ]
    },
    {
        "id": "local_militia",
        "name": "Local Militia",
        "description": "Dedicated to protecting the town and its citizens.",
        "ranks": [
            {"name": "Recruit", "reputation_needed": 0},
            {"name": "Guard", "reputation_needed": 75, "benefits": [{"type": "dialogue_options", "npc_tag": "guard"}]},
            {"name": "Sergeant", "reputation_needed": 200, "benefits": [{"type": "dialogue_options", "npc_tag": "guard"}, {"type": "reduced_crime_chance"}]}
        ],
        "join_requirements": [
            {"type": "oath_of_loyalty"} # Simpler requirement
        ]
    }
]

# Helper function to get a specific faction definition
def get_faction_definition(faction_id: str) -> dict | None:
    for faction in FACTION_DEFINITIONS:
        if faction["id"] == faction_id:
            return faction
    return None

# Helper function to get a specific rank definition within a faction
def get_faction_rank(faction_id: str, rank_name: str) -> dict | None:
    faction = get_faction_definition(faction_id)
    if faction:
        for rank in faction.get("ranks", []):
            if rank["name"] == rank_name:
                return rank
    return None

def get_rank_by_reputation(faction_id: str, reputation_score: int) -> dict | None:
    faction = get_faction_definition(faction_id)
    if not faction:
        return None

    current_rank = None
    for rank_def in sorted(faction.get("ranks", []), key=lambda r: r["reputation_needed"]):
        if reputation_score >= rank_def["reputation_needed"]:
            current_rank = rank_def
        else:
            break # Ranks are sorted by reputation needed
    return current_rank
