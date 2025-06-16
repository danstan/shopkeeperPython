from flask import Flask, render_template, request, redirect, url_for, session, flash
import io
import json
from game.game_manager import GameManager
from game.character import Character
# Assuming Item class is available for from_dict as it's used in Character.from_dict
from game.item import Item


app = Flask(__name__)
app.secret_key = 'dev_secret_key_!@#$%' # Replace with a strong, random key in production

# --- Constants ---
MAX_CHARS_PER_USER = 2
USERS_FILE = 'users.json'
CHARACTERS_FILE = 'user_characters.json'

# --- User and Character Data Stores (Global for simplicity) ---
users = {} # username: password
user_characters = {} # username: [list of character_dicts]

# --- Data Persistence Functions ---
def load_data():
    global users, user_characters
    try:
        with open(USERS_FILE, 'r') as f:
            users = json.load(f)
    except FileNotFoundError:
        users = {"testuser": "password123"} # Default if file not found
        save_users() # Create the file with default user
    except json.JSONDecodeError:
        print(f"Warning: Could not decode {USERS_FILE}. Starting with empty users or default.")
        users = {"testuser": "password123"}
        save_users()


    try:
        with open(CHARACTERS_FILE, 'r') as f:
            user_characters = json.load(f)
    except FileNotFoundError:
        user_characters = {} # Start empty if file not found
        save_user_characters() # Create the file
    except json.JSONDecodeError:
        print(f"Warning: Could not decode {CHARACTERS_FILE}. Starting with empty characters.")
        user_characters = {}
        save_user_characters()


def save_users():
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=4)

def save_user_characters():
    with open(CHARACTERS_FILE, 'w') as f:
        json.dump(user_characters, f, indent=4)

# Load data at application startup
load_data()


# Global StringIO object and GameManager instance
output_stream = io.StringIO()
# Initialize player_char with no name; it will be loaded or created.
player_char = Character(name=None)
player_char.gold = 50 # Default starting gold for new characters

game_manager_instance = GameManager(player_character=player_char, output_stream=output_stream)


# --- Authentication Routes ---

@app.route('/login', methods=['POST'])
def login_route():
    username = request.form.get('username')
    password = request.form.get('password')

    if username in users and users[username] == password:
        session['username'] = username
        flash('Login successful!', 'success')
        # When a user logs in, their character should be loaded in display_game_output
    else:
        flash('Invalid username or password.', 'login_error')
    return redirect(url_for('display_game_output'))

@app.route('/logout')
def logout_route():
    session.pop('username', None)
    session.pop('selected_character_slot', None) # Clear selected character on logout
    flash('You have been logged out.', 'success')
    # Reset global player_char to avoid carrying over state
    global player_char, game_manager_instance
    player_char = Character(name=None)
    player_char.gold = 50
    game_manager_instance.character = player_char
    game_manager_instance.is_game_setup = False # Or similar reset logic
    return redirect(url_for('display_game_output'))

@app.route('/register', methods=['GET', 'POST'])
def register_page():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            flash('Username and password are required.', 'error')
            return redirect(url_for('register_page'))

        if username in users:
            flash('Username already exists. Please choose another.', 'error')
            return redirect(url_for('register_page'))

        users[username] = password
        user_characters[username] = []
        save_users() # Save updated users dictionary
        save_user_characters() # Initialize character file for user if it wasn't (though it should be empty list)
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('display_game_output'))

    # For now, as register.html doesn't exist, we'll return a placeholder.
    # In a future step, create templates/register.html
    return """
    <h1>Register</h1>
    <form method="post">
        Username: <input type="text" name="username" required><br>
        Password: <input type="password" name="password" required><br>
        <input type="submit" value="Register">
    </form>
    <p><a href="{{ url_for('display_game_output') }}">Back to Login</a></p>
    """ # Using triple quotes for the multi-line string.
    # return render_template('register.html') # This would be the ideal line


# --- Character Selection and Creation Routes ---

@app.route('/select_character/<int:slot_index>')
def select_character_route(slot_index: int):
    if 'username' not in session:
        flash('Please log in to select a character.', 'error')
        return redirect(url_for('display_game_output'))

    username = session['username']
    characters_list = user_characters.get(username, [])

    if 0 <= slot_index < len(characters_list):
        session['selected_character_slot'] = slot_index
        flash(f"Character slot {slot_index + 1} selected.", "success")
    else:
        flash("Invalid character slot.", "error")

    return redirect(url_for('display_game_output'))

@app.route('/create_character', methods=['POST'])
def create_character_route():
    global player_char
    global game_manager_instance
    global user_characters

    if 'username' not in session:
        flash('You must be logged in to create a character.', 'error')
        return redirect(url_for('display_game_output'))

    username = session['username']
    char_name = request.form.get('character_name')

    if username not in user_characters: # Should have been created at registration
        user_characters[username] = []

    if len(user_characters[username]) >= MAX_CHARS_PER_USER: # This checks total slots (alive or dead)
        flash(f'You have reached the maximum of {MAX_CHARS_PER_USER} character slots.', 'error')
        return redirect(url_for('display_game_output'))

    # The prompt simplified this: "The death of a character does *not* free up a slot for this iteration."
    # So, the check above is sufficient. No need to count only 'active_chars' for slot limit here.

    stats = {}
    stat_keys_map = {
        'stat_str': 'STR', 'stat_dex': 'DEX', 'stat_con': 'CON',
        'stat_int': 'INT', 'stat_wis': 'WIS', 'stat_cha': 'CHA'
    }
    for form_key, actual_key in stat_keys_map.items():
        stats[actual_key] = int(request.form.get(form_key, 0))

    new_character = Character(name=char_name)
    new_character.stats = stats

    con_modifier = new_character._calculate_modifier(new_character.stats["CON"], is_base_stat_score=True)
    new_character.base_max_hp = 10 + (con_modifier * new_character.level)
    new_character.hp = new_character.get_effective_max_hp()
    new_character.gold = 50 # Standard starting gold for new characters

    # Store character in user_characters
    user_characters[username].append(new_character.to_dict())
    save_user_characters() # Save after adding a new character

    # Automatically select the newly created character
    session['selected_character_slot'] = len(user_characters[username]) - 1

    # Update global player_char and game_manager_instance
    player_char = new_character
    game_manager_instance.character = player_char
    game_manager_instance.is_game_setup = True # Game is ready with the new character
    output_stream.truncate(0) # Clear any previous messages (e.g. "create char" prompt)
    output_stream.seek(0)
    game_manager_instance._print(f"Character {player_char.name} created for user {username} and selected successfully!")
    game_manager_instance.initialize_game_world_if_needed()

    return redirect(url_for('display_game_output'))


# --- Main Display Route ---

@app.route('/')
def display_game_output():
    global player_char
    global game_manager_instance

    user_logged_in = 'username' in session
    show_character_selection = False
    show_character_creation_form = False
    player_char_loaded_or_selected = False
    characters_for_selection = []
    current_game_output = ""

    # Default values for template if no character is loaded / user not logged in
    player_name_display = "N/A"
    player_stats_display = {}
    player_hp_display = 0
    player_max_hp_display = 0
    player_gold_display = 0
    current_time_display = "N/A"
    current_town_display = "N/A"
    shop_inventory_display = ["Empty"]
    player_inventory_display = ["Empty"]

    if user_logged_in:
        username = session['username']
        characters_list = user_characters.get(username, [])

        # Handle 'action=create_new_char' from URL to switch to creation mode
        if request.args.get('action') == 'create_new_char':
            if len(characters_list) < MAX_CHARS_PER_USER:
                session.pop('selected_character_slot', None) # Clear selection to force creation view
                player_char_loaded_or_selected = False # Ensure we don't think a char is active
                # This will lead to show_character_creation_form = True below
            else:
                flash(f"You cannot create more than {MAX_CHARS_PER_USER} characters.", "warning")
                # Fall through to character selection or current char display

        selected_slot = session.get('selected_character_slot')

        if selected_slot is not None:
            try:
                slot = int(selected_slot)
                if 0 <= slot < len(characters_list):
                    char_data = characters_list[slot]
                    if char_data.get('is_dead', False):
                        flash(f"{char_data.get('name', 'Character')} is dead and cannot be played.", "warning")
                        session.pop('selected_character_slot', None)
                        player_char_loaded_or_selected = False # Force re-evaluation for selection/creation
                    else:
                        player_char = Character.from_dict(char_data)
                        game_manager_instance.character = player_char
                        game_manager_instance.is_game_setup = True
                        player_char_loaded_or_selected = True
                else:
                    session.pop('selected_character_slot', None)
            except (ValueError, TypeError):
                 session.pop('selected_character_slot', None)


        if player_char_loaded_or_selected:
            # This block executes only if a living character is successfully loaded and selected.
            player_name_display = player_char.name
            player_stats_display = player_char.stats
            player_hp_display = player_char.hp
            player_max_hp_display = player_char.get_effective_max_hp()
            player_gold_display = player_char.gold
            current_time_display = game_manager_instance.time.get_time_string()
            current_town_display = game_manager_instance.current_town.name

            shop_items = {}
            for item in game_manager_instance.shop.inventory:
                shop_items[item.name] = shop_items.get(item.name, 0) + 1
            shop_inventory_display = [f"{name} (x{qty})" for name, qty in shop_items.items()] or ["Empty"]

            player_inventory_display = [item.name for item in player_char.inventory] or ["Empty"]
            current_game_output = output_stream.getvalue()
        else: # No character active, decide to show selection or creation
            output_stream.truncate(0) # Clear game log if no character is active
            output_stream.seek(0)
            if characters_list: # User has characters, but none selected (or selection was invalid)
                show_character_selection = True
                for i, char_data_item in enumerate(characters_list):
                    characters_for_selection.append({
                        'name': char_data_item.get('name', 'Unknown'),
                        'level': char_data_item.get('level', 0),
                        'slot_index': i,
                        'is_dead': char_data_item.get('is_dead', False) # Add is_dead status
                    })
                current_game_output = "Please select a character or create a new one."
                player_char = Character(name=None)
                game_manager_instance.character = player_char
                game_manager_instance.is_game_setup = False

            else: # No existing characters for this user
                if len(characters_list) < MAX_CHARS_PER_USER:
                    show_character_creation_form = True
                    player_char = Character(name=None) # Prepare for creation
                    player_char.gold = 50
                    game_manager_instance.character = player_char
                    game_manager_instance.is_game_setup = False
                    current_game_output = "Welcome! Please create your character."
                else: # No characters and no slots left (should ideally not happen if MAX_CHARS handled at creation)
                    current_game_output = "You have no characters and no character slots available. Please contact support."
                    player_char = Character(name=None)
                    game_manager_instance.character = player_char
                    game_manager_instance.is_game_setup = False

    else: # User not logged in
        player_char = Character(name=None)
        player_char.gold = 50
        game_manager_instance.character = player_char
        game_manager_instance.is_game_setup = False
        current_game_output = "Please log in to start your adventure."
        output_stream.truncate(0) # Clear game log for login screen
        output_stream.seek(0)
        output_stream.write(current_game_output)


    return render_template('index.html',
                           user_logged_in=user_logged_in,
                           show_character_selection=show_character_selection,
                           characters_for_selection=characters_for_selection,
                           MAX_CHARS_PER_USER=MAX_CHARS_PER_USER, # Pass to template
                           show_character_creation_form=show_character_creation_form,
                           game_output=current_game_output,
                           player_name=player_name_display,
                           player_stats=player_stats_display,
                           player_hp=player_hp_display,
                           player_max_hp=player_max_hp_display,
                           player_gold=player_gold_display,
                           current_time=current_time_display,
                           current_town_name=current_town_display,
                           shop_inventory=shop_inventory_display,
                           player_inventory=player_inventory_display
                           )

def parse_action_details(details_str: str) -> dict:
    """
    Parses a JSON string representing action details into a dictionary.
    If details_str is empty, null, or invalid JSON, returns an empty dictionary.
    """
    if not details_str or details_str.strip() == "":
        return {}
    try:
        details_dict = json.loads(details_str)
        if not isinstance(details_dict, dict):
            # Ensure the loaded JSON is actually a dictionary
            game_manager_instance._print(f"Warning: Action details resolved to non-dictionary type: '{details_str}'. Using empty details.")
            return {}
        return details_dict
    except json.JSONDecodeError as e:
        game_manager_instance._print(f"Error parsing action_details JSON string '{details_str}': {e}. Using empty details.")
        return {}
    except TypeError as e: # Catches errors if details_str is not string-like for json.loads
        game_manager_instance._print(f"Error (TypeError) parsing action_details string '{details_str}': {e}. Using empty details.")
        return {}


@app.route('/action', methods=['POST'])
def perform_action():
    action_name = request.form.get('action_name')
    action_details_str = request.form.get('action_details', '{}') # Default to empty JSON object string

    # Clear the stream before new action output
    output_stream.truncate(0)
    output_stream.seek(0)

    if not action_name:
        game_manager_instance._print("Error: No action_name provided.")
        return redirect(url_for('display_game_output'))

    # Use the updated parse_action_details function
    details_dict = parse_action_details(action_details_str)

    # Perform the game action
    try:
        # Ensure a living character is loaded before performing actions
        if player_char is None or player_char.name is None or player_char.is_dead:
            flash("No active character or character is dead. Cannot perform action.", "error")
            return redirect(url_for('display_game_output'))

        game_manager_instance.perform_hourly_action(action_name, details_dict)

        # After action, check for death
        if player_char.is_dead:
            if 'username' in session and 'selected_character_slot' in session:
                username = session['username']
                slot = session['selected_character_slot']
                if username in user_characters and 0 <= slot < len(user_characters[username]):
                    # Update the stored character data to reflect death
                    user_characters[username][slot] = player_char.to_dict() # This now includes is_dead=True
                    save_user_characters()
                    flash(f"{player_char.name} has died! Their story ends here.", "error")
                    session.pop('selected_character_slot', None) # Clear selection
                    # No need to change global player_char here, display_game_output will handle it
                else:
                    flash("Error recording character death: session data mismatch.", "critical_error")
            else:
                flash("Error recording character death: user or character slot not in session.", "critical_error")

            # Redirect to display_game_output, which will show character selection/creation
            return redirect(url_for('display_game_output'))

    except Exception as e:
        game_manager_instance._print(f"An error occurred while performing action '{action_name}': {e}")
        import traceback
        game_manager_instance._print(f"Traceback: {traceback.format_exc()}")


    return redirect(url_for('display_game_output'))

if __name__ == '__main__':
    # Note: When running with `flask run`, this block might not execute depending on environment.
    # Ensure game_manager_instance is initialized globally as above.
    app.run(debug=True, host='0.0.0.0', port=5001)
