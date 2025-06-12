from flask import Flask, render_template, request, redirect, url_for
import io
from game.game_manager import GameManager
from game.character import Character
# Assuming other necessary imports like Item, Town, etc. are handled within GameManager or not directly needed here yet.

app = Flask(__name__)

# Global StringIO object and GameManager instance
output_stream = io.StringIO()
player_char = Character(name="Flask Shopkeeper")
# Basic stat setup, similar to game_manager.py's __main__
player_char.roll_stats() # Or set fixed stats for predictability
player_char.stats = {"STR": 10, "DEX": 10, "CON": 10, "INT": 10, "WIS": 10, "CHA": 14} # Example
player_char.base_max_hp = 10 + player_char._calculate_modifier(player_char.stats["CON"],is_base_stat_score=True) * player_char.level
player_char.hp = player_char.get_effective_max_hp()
# player_char.gold = 250 # Example starting gold for the character

game_manager_instance = GameManager(player_character=player_char, output_stream=output_stream)
# game_manager_instance.shop.gold = 500 # Example starting gold for the shop

@app.route('/')
def display_game_output():
    # Player Info
    player_name = game_manager_instance.character.name
    player_stats = game_manager_instance.character.stats
    player_hp = game_manager_instance.character.hp
    player_max_hp = game_manager_instance.character.get_effective_max_hp()
    player_gold = game_manager_instance.character.gold

    # Game Info
    current_time = game_manager_instance.time.get_time_string()
    current_town_name = game_manager_instance.current_town.name

    # Shop Inventory - Basic list of names for now
    # For quantities, you might need to adjust how Shop stores/exposes inventory
    shop_inventory_items = {} # Using a dict to count items
    for item in game_manager_instance.shop.inventory:
        shop_inventory_items[item.name] = shop_inventory_items.get(item.name, 0) + 1

    shop_inventory_display = [f"{name} (x{qty})" for name, qty in shop_inventory_items.items()]
    if not shop_inventory_display:
        shop_inventory_display = ["Empty"]


    # Player Inventory
    player_inventory_items = [item.name for item in game_manager_instance.character.inventory]
    if not player_inventory_items:
        player_inventory_items = ["Empty"]

    return render_template('index.html',
                           game_output=output_stream.getvalue(),
                           player_name=player_name,
                           player_stats=player_stats,
                           player_hp=player_hp,
                           player_max_hp=player_max_hp,
                           player_gold=player_gold,
                           current_time=current_time,
                           current_town_name=current_town_name,
                           shop_inventory=shop_inventory_display,
                           player_inventory=player_inventory_items
                           )

def parse_action_details(details_str: str) -> dict:
    details_dict = {}
    if not details_str:
        return details_dict
    try:
        pairs = details_str.split(',')
        for pair in pairs:
            if '=' in pair:
                key, value = pair.split('=', 1)
                details_dict[key.strip()] = value.strip()
            else:
                # Handle cases where a detail might not be a key-value pair,
                # though current actions mostly expect key-value.
                # For now, we can ignore it or assign a default key.
                pass # Or log a warning: print(f"Warning: Malformed detail part: {pair}")
    except Exception as e:
        # Log parsing error
        game_manager_instance._print(f"Error parsing action_details string '{details_str}': {e}")
        # Potentially return a dict with an error key or raise, depending on desired handling
    return details_dict

@app.route('/action', methods=['POST'])
def perform_action():
    action_name = request.form.get('action_name')
    action_details_str = request.form.get('action_details', '')

    # Clear the stream before new action output
    output_stream.truncate(0)
    output_stream.seek(0)

    if not action_name:
        # Handle missing action_name, perhaps by printing to the game_manager's stream
        game_manager_instance._print("Error: No action_name provided.")
        return redirect(url_for('display_game_output'))

    details_dict = parse_action_details(action_details_str)

    # Perform the game action
    try:
        game_manager_instance.perform_hourly_action(action_name, details_dict)
    except Exception as e:
        # Log exceptions from game logic to the game output stream
        game_manager_instance._print(f"An error occurred while performing action '{action_name}': {e}")
        # Potentially add more robust error handling or logging here

    return redirect(url_for('display_game_output'))

if __name__ == '__main__':
    # Note: When running with `flask run`, this block might not execute depending on environment.
    # Ensure game_manager_instance is initialized globally as above.
    app.run(debug=True, host='0.0.0.0', port=5001)
