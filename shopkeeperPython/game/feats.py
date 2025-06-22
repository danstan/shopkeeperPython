FEAT_DEFINITIONS = [
    {
        "id": "tough",
        "name": "Tough",
        "description": "You become tougher and more resilient.",
        "effects": [
            {"type": "base_max_hp_bonus", "value": 5}
        ]
        # In a fuller system, this might be:
        # "effects": [{"type": "hp_increase_per_level", "value": 2}]
        # For now, a direct base_max_hp bonus is simpler.
    },
    {
        "id": "skill_novice_athletics",
        "name": "Skill Novice (Athletics)",
        "description": "You have a minor knack for Athletics.",
        "effects": [
            {"type": "attribute_bonus", "attribute": "Athletics", "value": 1}
        ]
    },
    {
        "id": "stat_boost_str",
        "name": "Minor Strength Boost",
        "description": "Your Strength increases slightly.",
        "effects": [
            {"type": "stat_bonus", "stat": "STR", "value": 1}
        ]
    }
]

# Example of a more complex feat for future reference:
# {
#     "id": "resilient_wisdom",
#     "name": "Resilient (Wisdom)",
#     "description": "You increase your Wisdom score by 1, to a maximum of 20. You also gain proficiency in Wisdom saving throws.",
#     "effects": [
#         {"type": "stat_increase_capped", "stat": "WIS", "value": 1, "cap": 20},
#         {"type": "saving_throw_proficiency", "stat": "WIS"} # This would require saving throw mechanics
#     ]
# }
