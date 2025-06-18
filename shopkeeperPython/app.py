from flask import Flask, render_template, request, redirect, url_for, session, flash, get_flashed_messages
import io
import json
import os # Added for environment variables
from game.game_manager import GameManager
from game.character import Character
# Assuming Item class is available for from_dict as it's used in Character.from_dict
from game.item import Item
from flask_dance.contrib.google import make_google_blueprint, google
from flask_dance.consumer import oauth_authorized, oauth_error # Added for signals
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)
app.secret_key = 'dev_secret_key_!@#$%' # Replace with a strong, random key in production

# --- Google OAuth Configuration ---
# IMPORTANT: Set these environment variables in your shell before running the app.
# For Linux/macOS:
# export GOOGLE_OAUTH_CLIENT_ID="YOUR_CLIENT_ID_HERE"
# export GOOGLE_OAUTH_CLIENT_SECRET="YOUR_CLIENT_SECRET_HERE"
# For Windows (Command Prompt):
# set GOOGLE_OAUTH_CLIENT_ID="YOUR_CLIENT_ID_HERE"
# set GOOGLE_OAUTH_CLIENT_SECRET="YOUR_CLIENT_SECRET_HERE"
# For Windows (PowerShell):
# $env:GOOGLE_OAUTH_CLIENT_ID="YOUR_CLIENT_ID_HERE"
# $env:GOOGLE_OAUTH_CLIENT_SECRET="YOUR_CLIENT_SECRET_HERE"

GOOGLE_OAUTH_CLIENT_ID = os.environ.get("GOOGLE_OAUTH_CLIENT_ID")
GOOGLE_OAUTH_CLIENT_SECRET = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET")

print(f"DEBUG: GOOGLE_OAUTH_CLIENT_ID: {GOOGLE_OAUTH_CLIENT_ID}")
print(f"DEBUG: GOOGLE_OAUTH_CLIENT_SECRET: {'SET' if GOOGLE_OAUTH_CLIENT_SECRET else 'NOT SET'}")

if not GOOGLE_OAUTH_CLIENT_ID or not GOOGLE_OAUTH_CLIENT_SECRET:
    print("WARNING: Google OAuth Client ID or Secret is not set in environment variables.")
    print("Google Login will not work. Please set GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET.")
    # google_bp will not be registered if creds are missing.
else:
    google_bp = make_google_blueprint(
        client_id=GOOGLE_OAUTH_CLIENT_ID,
        client_secret=GOOGLE_OAUTH_CLIENT_SECRET,
        scope=[
            "openid",
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/userinfo.profile"
        ],
        # redirect_url="/login/google/authorized" # This is the default if not specified with this url_prefix
        # The redirect URI in Google Cloud Console must be: http://localhost:5001/login/google/authorized
        # (or https if using https)
    )
    app.register_blueprint(google_bp, url_prefix="/login")

    # --- OAuth Signal Handlers (defined only if google_bp is created) ---
    @oauth_authorized.connect_via(google_bp)
    def google_logged_in(blueprint, token):
        if not token:
            flash("Failed to log in with Google.", "error")
            return redirect(url_for("display_game_output"))

        resp = blueprint.session.get("/oauth2/v2/userinfo")
        if not resp.ok:
            msg = "Failed to fetch user info from Google."
            flash(msg, "error")
            return redirect(url_for("display_game_output"))

        google_user_info = resp.json()
        google_id = str(google_user_info.get("id"))
        email = google_user_info.get("email")
        name = google_user_info.get("name")
        # picture = google_user_info.get("picture") # Optional, not used currently

        # 1. Check if user exists by google_id
        print(f"DEBUG_GOOGLE_LOGIN: Before calling find_user_by_google_id. Full users dict: {users}")
        username = find_user_by_google_id(google_id)

        if username: # Existing Google-linked user
            session['username'] = username
            session.pop('selected_character_slot', None)
            display_name = users[username].get('display_name_google') or users[username].get('email_google') or name
            flash(f"Welcome back, {display_name}!", "success")
            return redirect(url_for("display_game_output"))

        # 2. Optional: Check if user exists by email (for linking or conflict warning)
        # For this implementation, we'll prioritize google_id. If a user with this email
        # exists but their google_id doesn't match, we'll create a new distinct user for this Google account.
        # More complex linking logic could be added here if desired.
        # existing_user_by_email = find_user_by_email(email)
        # if existing_user_by_email and users[existing_user_by_email].get('google_id') != google_id:
        #     flash(f"An account with email {email} already exists. Please log in using your original method or contact support if you wish to link accounts.", "warning")
        #     return redirect(url_for("display_game_output"))


        # 3. Create new game user if no existing link found
        internal_username_base = email.lower().split('@')[0] if email else "googleuser"
        internal_username = internal_username_base
        counter = 1
        while internal_username in users: # Ensure username is unique
            internal_username = f"{internal_username_base}{counter}"
            counter += 1

        users[internal_username] = {
            'password': None, # No password for Google-only users
            'google_id': google_id,
            'email_google': email,
            'display_name_google': name
        }
        save_users()

        user_characters.setdefault(internal_username, [])
        graveyard.setdefault(internal_username, [])
        save_user_characters()
        save_graveyard()

        session['username'] = internal_username
        session.pop('selected_character_slot', None)
        flash(f"Logged in successfully with Google as {name}! Your game username is {internal_username}.", "success")
        return redirect(url_for("display_game_output"))

    @oauth_error.connect_via(google_bp)
    def google_error(blueprint, error, error_description=None, error_uri=None):
        msg = (
            "OAuth error from {name}! "
            "error={error} description={description} uri={uri}"
        ).format(
            name=blueprint.name,
            error=error,
            description=error_description,
            uri=error_uri,
        )
        flash(msg, "error")
        return redirect(url_for("display_game_output"))


# --- Constants ---
MAX_CHARS_PER_USER = 2
USERS_FILE = 'users.json'
CHARACTERS_FILE = 'user_characters.json'
GRAVEYARD_FILE = 'graveyard.json' # New file path for graveyard

# --- User and Character Data Stores (Global for simplicity) ---
users = {}
user_characters = {}
graveyard = {}

# --- Helper Functions for User Lookup ---
def find_user_by_google_id(google_id_to_find):
    print(f"DEBUG_FIND_USER: Entered function. Full users dict: {users}")
    for username, user_data in users.items():
        print(f"DEBUG_FIND_USER: Iterating. username='{username}', type(user_data)='{type(user_data)}'")
        if not isinstance(user_data, dict):
            print(f"DEBUG_FIND_USER: CRITICAL! user_data for '{username}' is {user_data}")
        if user_data.get('google_id') == google_id_to_find:
            return username
    return None

def find_user_by_email(email_to_find):
    for username, user_data in users.items():
        if user_data.get('email_google') == email_to_find: # Check against Google email
            return username
    return None

# --- Data Persistence Functions ---
def load_data():
    global users, user_characters, graveyard # Add graveyard to globals

    users_migrated = False # Flag to track if migration occurred
    try:
        with open(USERS_FILE, 'r') as f:
            loaded_users_data = json.load(f)

        # Data migration check
        # Operate on a copy if direct modification during iteration is problematic,
        # or build a new dictionary. Here, modifying loaded_users_data directly is fine.
        for username, user_data in loaded_users_data.items():
            if isinstance(user_data, str):
                print(f"Migrating user data for user '{username}' to new format.")
                loaded_users_data[username] = {
                    "password": generate_password_hash(user_data), # Hash the original string password
                    "google_id": None,
                    "email_google": None,
                    "display_name_google": None
                }
                users_migrated = True
            # No need for the elif isinstance(user_data, dict) ... as it does nothing.

        users.clear()
        users.update(loaded_users_data)

        if users_migrated:
            save_users()


    except FileNotFoundError:
        # Default user with a hashed password
        default_user_data = {"testuser": {
            "password": generate_password_hash("password123"),
            "google_id": None,
            "email_google": None,
            "display_name_google": None
            }
        }

        users.clear()
        users.update(default_user_data)
        # No need to call save_users() here if FileNotFoundError, as it will be created with default user
        # and then immediately saved by the users_migrated block if it was the first run.
        # However, to ensure it's saved if the file truly didn't exist and no migration happened (e.g. empty users dict from json.load on empty file that somehow passed FileNotFoundError)
        # it's safer to keep the original save_users() or rely on the migration save.
        # For this refactor, we'll ensure the default user is saved if created.

        save_users()
    except json.JSONDecodeError:
        print(f"Warning: Could not decode {USERS_FILE}. Starting with default user.")
        default_user_data = {"testuser": {
            "password": generate_password_hash("password123"),
            "google_id": None,
            "email_google": None,
            "display_name_google": None
            }
        }

        users.clear()
        users.update(default_user_data)
        save_users() # Save the default user if JSON was corrupted


    try:
        with open(CHARACTERS_FILE, 'r') as f:
            user_characters = json.load(f)
    except FileNotFoundError:
        user_characters = {} # Start empty if file not found
        save_user_characters() # Create the file
    except json.JSONDecodeError:
        print(f"Warning: Could not decode {CHARACTERS_FILE}. Starting with empty characters.")
        user_characters = {}
        save_user_characters() # Ensure file is created if decode error occurred after file existence check

    # Load graveyard data
    try:
        with open(GRAVEYARD_FILE, 'r') as f:
            graveyard = json.load(f)
    except FileNotFoundError:
        graveyard = {}
        # Create an empty graveyard file if it doesn't exist
        with open(GRAVEYARD_FILE, 'w') as f:
            json.dump(graveyard, f, indent=4)
        print(f"'{GRAVEYARD_FILE}' not found, created a new one.")
    except json.JSONDecodeError:
        graveyard = {}
        print(f"Error decoding '{GRAVEYARD_FILE}'. Initializing empty graveyard and overwriting.")
        # Overwrite corrupted file with empty data
        with open(GRAVEYARD_FILE, 'w') as f:
            json.dump(graveyard, f, indent=4)


def save_users():
    print(f"DEBUG_SAVE_USERS: Attempting to save users. Current users dict to be saved: {users}")
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=4)

def save_user_characters():
    with open(CHARACTERS_FILE, 'w') as f:
        json.dump(user_characters, f, indent=4)

def save_graveyard(): # New function to save graveyard data
    with open(GRAVEYARD_FILE, 'w') as f:
        json.dump(graveyard, f, indent=4)

# Load data at application startup
load_data()


# Global StringIO object and GameManager instance
output_stream = io.StringIO()
# Initialize player_char with no name; it will be loaded or created.
player_char = Character(name=None)
player_char.gold = 50 # Default starting gold for new characters

game_manager_instance = GameManager(player_character=player_char, output_stream=output_stream)


# --- Authentication Routes ---

@app.route('/login/google_initiate')
def google_initiate_login_route():
    # Check if Google OAuth is configured (i.e., if client ID and secret are set)
    if not GOOGLE_OAUTH_CLIENT_ID or not GOOGLE_OAUTH_CLIENT_SECRET:
        flash("Google Login is not currently configured by the server administrator.", "error")
        return redirect(url_for('display_game_output')) # Redirect to main page or login page

    # If configured, redirect to Flask-Dance's Google login endpoint.
    # This endpoint is part of the 'google_bp' blueprint which was registered with url_prefix="/login".
    # The default login endpoint in such a blueprint is typically 'google.login'.
    return redirect(url_for('google.login'))

@app.route('/login', methods=['POST'])
def login_route():
    username = request.form.get('username')
    password = request.form.get('password')
    user_data = users.get(username)

    if user_data and user_data.get('password') and check_password_hash(user_data['password'], password):
        session['username'] = username
        flash('Login successful!', 'success')
    else:
        flash('Invalid username or password.', 'login_error')
    return redirect(url_for('display_game_output'))

@app.route('/logout')
def logout_route():
    session.pop('username', None)
    session.pop('selected_character_slot', None) # Clear selected character on logout
    get_flashed_messages()
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

        users[username] = {
            'password': generate_password_hash(password),
            'google_id': None,
            'email_google': None,
            'display_name_google': None
        }
        user_characters[username] = []
        save_users()
        save_user_characters()
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

    if not char_name or not char_name.strip():
        flash('Character name cannot be empty or just whitespace.', 'error')
        return redirect(url_for('display_game_output', action='create_new_char'))

    if username not in user_characters:
        user_characters[username] = [] # Should have been created at registration, but good safeguard

    active_characters_list = user_characters.get(username, [])
    # The prompt asks to change the limit check to active characters.
    # The previous logic (len(user_characters[username])) checked total slots.
    # Now, it should be len(active_characters_list) because dead chars are moved out.
    if len(active_characters_list) >= MAX_CHARS_PER_USER:
        flash(f'You have reached the maximum of {MAX_CHARS_PER_USER} active characters. A dead character frees up their slot.', 'error')
        return redirect(url_for('display_game_output'))

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

    # Update global player_char (still useful for immediate context if needed before full setup)
    player_char = new_character
    # game_manager_instance.character = player_char # Redundant
    # game_manager_instance.is_game_setup = True # Redundant

    output_stream.truncate(0)
    output_stream.seek(0)

    # Call the new setup method
    game_manager_instance.setup_for_character(new_character)

    # Confirmation message (optional, as setup_for_character is verbose)
    if game_manager_instance.is_game_setup:
        game_manager_instance._print(f"Character {new_character.name} (user: {username}) created and game world prepared.")
    else:
        game_manager_instance._print(f"Attempted to create character {new_character.name}, but game world setup failed. Check logs.")
        flash(f"Failed to initialize game for {new_character.name}. The character data might be incomplete or corrupted. Please try creating the character again or contact support if the issue persists.", "error")

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
    dead_characters_info = [] # Initialize for passing to template

    # --- Data for new UI elements ---
    available_towns = list(game_manager_instance.towns_map.keys())
    current_town_sub_locations = []
    all_towns_data = {}
    available_recipes = {} # Initialize
    # --- End Data for new UI elements ---

    # Check if Google OAuth is configured
    google_auth_is_configured = bool(GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET)

    if user_logged_in:
        username = session['username']
        characters_list = user_characters.get(username, [])
        user_graveyard_list = graveyard.get(username, []) # Load user's graveyard

        # Prepare graveyard info for template
        if user_graveyard_list:
            for dead_char_data in user_graveyard_list:
                dead_characters_info.append({
                    'name': dead_char_data.get('name', 'Unknown'),
                    'level': dead_char_data.get('level', 0),
                    # Add other details if needed, e.g., from dead_char_data['stats']
                })

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
                        player_char_loaded_or_selected = False
                        # Explicitly reset game_manager_instance if a dead character was selected then deselected.
                        # This ensures that if no other character is subsequently loaded, GM doesn't retain old state.
                        # The existing logic for "No character active, decide to show selection or creation"
                        # already handles setting player_char to Character(name=None) and is_game_setup = False.
                        # So, just ensuring player_char_loaded_or_selected = False is enough here.
                    else:
                        loaded_player_char = Character.from_dict(char_data)
                        # Call setup_for_character with the loaded character
                        game_manager_instance.setup_for_character(loaded_player_char)

                        if game_manager_instance.is_game_setup:
                            # Update the global player_char in app.py to reflect the loaded character
                            player_char = loaded_player_char
                            player_char_loaded_or_selected = True
                            # flash(f"Character {player_char.name} loaded successfully.", "success") # Optional: can be noisy
                        else:
                            # Setup failed for some reason (e.g., bad character data, though from_dict should catch some)
                            flash(f"Failed to set up game world for {loaded_player_char.name}. Please try re-creating or contact support.", "error")
                            player_char_loaded_or_selected = False
                            session.pop('selected_character_slot', None) # Deselect problematic character
                else: # Invalid slot
                    session.pop('selected_character_slot', None)
                    player_char_loaded_or_selected = False # Ensure this is false
            except (ValueError, TypeError):
                 session.pop('selected_character_slot', None)
                 player_char_loaded_or_selected = False # Ensure this is false on error too


        if player_char_loaded_or_selected:
            # This block executes only if a living character is successfully loaded and selected.
            player_name_display = player_char.name
            player_stats_display = player_char.stats
            player_hp_display = player_char.hp
            player_max_hp_display = player_char.get_effective_max_hp()
            player_gold_display = player_char.gold
            current_time_display = game_manager_instance.time.get_time_string()
            current_town_display = game_manager_instance.current_town.name
            # Populate sub-locations and all_towns_data if a character is loaded
            if game_manager_instance.current_town:
                current_town_sub_locations = game_manager_instance.current_town.sub_locations

            for town_obj in game_manager_instance.towns_map.values():
                all_towns_data[town_obj.name] = {
                    "sub_locations": town_obj.sub_locations
                }

            shop_items = {}
            for item in game_manager_instance.shop.inventory:
                shop_items[item.name] = shop_items.get(item.name, 0) + 1
            shop_inventory_display = [f"{name} (x{qty})" for name, qty in shop_items.items()] or ["Empty"]

            player_inventory_display = [item.name for item in player_char.inventory] or ["Empty"]
            current_game_output = output_stream.getvalue()

            # Fetch recipes if shop is available
            if game_manager_instance.shop:
                available_recipes = game_manager_instance.shop.BASIC_RECIPES
            else:
                available_recipes = {} # Ensure it's an empty dict if no shop

        else: # No character active (either not selected, selection invalid, or selection was a dead char)
            output_stream.truncate(0)
            output_stream.seek(0)

            unnamed_char = Character(name=None) # Character with no name
            player_char = unnamed_char # Update global player_char
            player_char.gold = 50 # Default gold for display on creation form

            # Call setup_for_character with the unnamed char.
            # This will internally set game_manager_instance.is_game_setup to False
            # and reset other GM properties based on an unnamed character.
            game_manager_instance.setup_for_character(unnamed_char)

            if characters_list: # User has characters, but none selected (or selection was invalid/dead)
                show_character_selection = True
                for i, char_data_item in enumerate(characters_list):
                    characters_for_selection.append({
                        'name': char_data_item.get('name', 'Unknown'),
                        'level': char_data_item.get('level', 0),
                        'slot_index': i,
                        'is_dead': char_data_item.get('is_dead', False) # Add is_dead status
                    })
                current_game_output = "Please select a character or create a new one."
                # player_char and game_manager_instance already handled by unnamed_char logic above

            else: # No existing characters for this user
                if len(characters_list) < MAX_CHARS_PER_USER: # Check against characters_list for creation possibility
                    show_character_creation_form = True
                    # player_char already set to unnamed_char with default gold
                    current_game_output = "Welcome! Please create your character."
                else: # No characters and no slots left
                    current_game_output = "You have no characters and no character slots available. Please contact support."
                # player_char and game_manager_instance already handled by unnamed_char logic above

    else: # User not logged in
        unnamed_char_for_logout = Character(name=None)
        player_char = unnamed_char_for_logout
        player_char.gold = 50
        # Ensure GameManager is also reset when user logs out
        game_manager_instance.setup_for_character(unnamed_char_for_logout)
        current_game_output = "Please log in to start your adventure."
        output_stream.truncate(0) # Clear game log for login screen
        output_stream.seek(0)
        output_stream.write(current_game_output)


    return render_template('index.html',
                           user_logged_in=user_logged_in,
                           show_character_selection=show_character_selection,
                           characters_for_selection=characters_for_selection,
                           MAX_CHARS_PER_USER=MAX_CHARS_PER_USER,
                           dead_characters_info=dead_characters_info, # Pass graveyard data
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
                           player_inventory=player_inventory_display,
                           google_auth_is_configured=google_auth_is_configured,
                           available_towns=available_towns,
                           current_town_sub_locations_json=json.dumps(current_town_sub_locations),
                           all_towns_data_json=json.dumps(all_towns_data),
                           available_recipes=available_recipes
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

        if action_name == "buy_from_npc":
            npc_name = request.form.get('npc_name')
            item_name = request.form.get('item_name')
            quantity = request.form.get('quantity', 1) # Default to 1 if not provided
            try:
                quantity = int(quantity)
            except ValueError:
                game_manager_instance._print(f"Invalid quantity: {quantity}. Defaulting to 1.")
                quantity = 1

            if npc_name and item_name and quantity > 0:
                game_manager_instance._print(f"Attempting to buy {quantity} of {item_name} from {npc_name}.")
                # Actual buying logic will be added later.
                # For now, just log the attempt.
                # Example: game_manager_instance.buy_item_from_npc(npc_name, item_name, quantity)
            else:
                game_manager_instance._print("Missing details for buying from NPC.")
        else:
            # Existing actions are handled by perform_hourly_action
            game_manager_instance.perform_hourly_action(action_name, details_dict)

        # ---- START NEW SAVE LOGIC ----
        # Save character state if alive and loaded
        # Use global player_char which should be the same as game_manager_instance.character
        if player_char and player_char.name and not player_char.is_dead:
            username = session.get('username')
            slot_index = session.get('selected_character_slot')
            if username and slot_index is not None:
                # Ensure the slot_index is valid for the list of characters for that user
                if username in user_characters and 0 <= slot_index < len(user_characters[username]):
                    user_characters[username][slot_index] = player_char.to_dict()
                    save_user_characters()
                    # Optional: game_manager_instance._print("  Character data saved after action.")
                else:
                    # This case should ideally not be reached if session management is correct
                    game_manager_instance._print(f"  Warning: Character slot data mismatch for user {username}, slot {slot_index}. Could not save character state after action.")
            else:
                # This case implies an issue with session state or a scenario where character exists without full session setup
                 game_manager_instance._print("  Warning: User session data (username or slot_index) missing. Could not save character state after action.")
        # ---- END NEW SAVE LOGIC ----

        # After action, check for death
        if player_char.is_dead: # This check should be safe even if player_char was reset due to death
            username = session.get('username')
            slot_index = session.get('selected_character_slot')

            if username and slot_index is not None:
                if username in user_characters and 0 <= slot_index < len(user_characters[username]):
                    # Move character from active list to graveyard
                    dead_char_data = user_characters[username].pop(slot_index)
                    # Ensure 'is_dead' is explicitly true in the data moved to graveyard,
                    # though player_char.to_dict() should already handle this.
                    dead_char_data['is_dead'] = True

                    graveyard.setdefault(username, []).append(dead_char_data)

                    save_user_characters() # Save updated (shorter) list of active characters
                    save_graveyard()       # Save updated graveyard

                    flash(f"{dead_char_data.get('name', 'The character')} has died and been moved to the graveyard. Their slot is now free.", "error")
                    session.pop('selected_character_slot', None)
                else:
                    flash("Error processing character death: Character slot data mismatch.", "critical_error")
                    # Still clear the slot, as it's likely invalid or pointing to a now-gone character
                    session.pop('selected_character_slot', None)
            else:
                flash("Error processing character death: User session data missing.", "critical_error")
                session.pop('selected_character_slot', None) # Clear potentially problematic slot

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
