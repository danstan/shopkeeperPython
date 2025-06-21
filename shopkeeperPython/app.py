from flask import Flask, render_template, request, redirect, url_for, session, flash, get_flashed_messages
import io
import json
import os # Added for environment variables
import datetime
import shutil

from shopkeeperPython.game.game_manager import GameManager
from shopkeeperPython.game.character import Character
# Item is implicitly used by Character.to_dict/from_dict if inventory has items.
# Pylint might not see this if no direct instantiation of Item happens in app.py.
# For now, let's trust Pylint's static analysis; if runtime errors occur, it can be re-added.
# from shopkeeperPython.game.item import Item
from shopkeeperPython.game.game_manager import HEMLOCK_HERBS # Added import
from shopkeeperPython.game.g_event import GAME_EVENTS

from flask_dance.contrib.google import make_google_blueprint # Removed google
from flask_dance.consumer import oauth_authorized, oauth_error # Added for signals
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)

# Attempt to load secret key from environment variable
SECRET_KEY = os.environ.get('FLASK_SECRET_KEY')
if SECRET_KEY:
    app.secret_key = SECRET_KEY
    print("INFO: Flask secret key loaded from FLASK_SECRET_KEY environment variable.")
else:
    app.secret_key = 'dev_secret_key_!@#$%' # Default for development
    print("WARNING: FLASK_SECRET_KEY environment variable not set. Using default development secret key.")
    print("WARNING: For production, set a strong, random FLASK_SECRET_KEY environment variable.")

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

# print(f"DEBUG: GOOGLE_OAUTH_CLIENT_ID: {GOOGLE_OAUTH_CLIENT_ID}")
# print(f"DEBUG: GOOGLE_OAUTH_CLIENT_SECRET: {'SET' if GOOGLE_OAUTH_CLIENT_SECRET else 'NOT SET'}")
# For OAuth debugging, consider using app.logger.debug(...) or app.logger.info(...)

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
        # print(f"DEBUG_GOOGLE_LOGIN: Before calling find_user_by_google_id. Full users dict: {users}") # Consider app.logger.debug()
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
    # print(f"DEBUG_FIND_USER: Entered function. Full users dict: {users}") # Consider app.logger.debug()
    for username, user_data in users.items():
        # print(f"DEBUG_FIND_USER: Iterating. username='{username}', type(user_data)='{type(user_data)}'") # Consider app.logger.debug()
        if not isinstance(user_data, dict):
            # print(f"DEBUG_FIND_USER: CRITICAL! user_data for '{username}' is {user_data}") # Consider app.logger.error() or warning
            pass # Added pass to make this a valid block
        if user_data.get('google_id') == google_id_to_find: # Unindented this line
            return username # Unindented this line
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
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
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
        print(f"INFO: {USERS_FILE} not found. Starting with an empty user list.")
        print(f"INFO: Please use the registration page to create the first user.")
        users.clear() # Ensure users is empty
        # user_characters.setdefault(username, []) # This line is not needed here as no user is created
        save_users() # Save the empty users list to create the file
    except json.JSONDecodeError:
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        backup_filename = f"{USERS_FILE}.corrupted.{timestamp}"
        try:
            shutil.copy2(USERS_FILE, backup_filename) # Use copy2 to preserve metadata
            print(f"Warning: Could not decode {USERS_FILE}. It has been backed up to {backup_filename}.")
        except Exception as backup_e:
            print(f"Warning: Could not decode {USERS_FILE}. Failed to create backup: {backup_e}")
        # print("Starting with default user data.") # Old message
        print(f"INFO: {USERS_FILE} was corrupted. Starting with an empty user list after backing up the corrupted file.")
        print(f"INFO: Please use the registration page to create users.")
        users.clear() # Ensure users is empty
        # No default user data should be added here.
        save_users() # Save the empty users list


    try:
        with open(CHARACTERS_FILE, 'r', encoding='utf-8') as f:
            user_characters = json.load(f)
    except FileNotFoundError:
        user_characters = {} # Start empty if file not found
        save_user_characters() # Create the file
    except json.JSONDecodeError:
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        backup_filename = f"{CHARACTERS_FILE}.corrupted.{timestamp}"
        try:
            shutil.copy2(CHARACTERS_FILE, backup_filename)
            print(f"Warning: Could not decode {CHARACTERS_FILE}. It has been backed up to {backup_filename}.")
        except Exception as backup_e:
            print(f"Warning: Could not decode {CHARACTERS_FILE}. Failed to create backup: {backup_e}")
        print("Starting with empty characters data.")
        user_characters = {}
        save_user_characters() # This will overwrite the original corrupted file

    # Load graveyard data
    try:
        with open(GRAVEYARD_FILE, 'r', encoding='utf-8') as f:
            graveyard = json.load(f)
    except FileNotFoundError:
        graveyard = {}
        # Create an empty graveyard file if it doesn't exist
        with open(GRAVEYARD_FILE, 'w', encoding='utf-8') as f:
            json.dump(graveyard, f, indent=4)
        print(f"'{GRAVEYARD_FILE}' not found, created a new one.")
    except json.JSONDecodeError:
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        backup_filename = f"{GRAVEYARD_FILE}.corrupted.{timestamp}"
        try:
            shutil.copy2(GRAVEYARD_FILE, backup_filename)
            print(f"Error decoding '{GRAVEYARD_FILE}'. It has been backed up to {backup_filename}.")
        except Exception as backup_e:
            print(f"Error decoding '{GRAVEYARD_FILE}'. Failed to create backup: {backup_e}")
        print("Initializing empty graveyard data and overwriting original.")
        graveyard = {}
        with open(GRAVEYARD_FILE, 'w', encoding='utf-8') as f: # This overwrites the original
            json.dump(graveyard, f, indent=4)


def save_users():
    # print(f"DEBUG_SAVE_USERS: Attempting to save users. Current users dict to be saved: {users}") # Consider app.logger.debug()
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=4)

def save_user_characters():
    with open(CHARACTERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(user_characters, f, indent=4)

def save_graveyard(): # New function to save graveyard data
    with open(GRAVEYARD_FILE, 'w', encoding='utf-8') as f:
        json.dump(graveyard, f, indent=4)

# Load data at application startup
load_data()

# --- Helper Function for Global Character Name Uniqueness ---
def is_character_name_taken(name_to_check: str, all_user_chars: dict, all_graveyards: dict) -> bool:
    """
    Checks if a character name is already taken globally, case-insensitively.
    Iterates through all active characters and all characters in graveyards.
    """
    lower_name_to_check = name_to_check.lower()

    # Check active characters
    for username_key in all_user_chars:
        for char_data in all_user_chars[username_key]:
            if isinstance(char_data, dict) and 'name' in char_data:
                if char_data['name'].lower() == lower_name_to_check:
                    return True

    # Check characters in graveyards
    for username_key in all_graveyards:
        for char_data in all_graveyards[username_key]:
            if isinstance(char_data, dict) and 'name' in char_data:
                if char_data['name'].lower() == lower_name_to_check:
                    return True
    return False

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
    session.pop('character_creation_stats', None) # Clear pending creation stats
    session.pop('character_creation_name', None) # Clear pending char name
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
        # Clear pending character creation info when selecting an existing character
        session.pop('character_creation_stats', None)
        session.pop('character_creation_name', None)
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

    # --- Global Character Name Uniqueness Check ---
    if is_character_name_taken(char_name, user_characters, graveyard):
        flash(f"Character name '{char_name}' is already taken. Please choose another.", 'error')
        return redirect(url_for('display_game_output', action='create_new_char'))
    # --- End of Uniqueness Check ---

    if username not in user_characters:
        user_characters[username] = [] # Should have been created at registration, but good safeguard

    active_characters_list = user_characters.get(username, [])
    # The prompt asks to change the limit check to active characters.
    # The previous logic (len(user_characters[username])) checked total slots.
    # Now, it should be len(active_characters_list) because dead chars are moved out.
    if len(active_characters_list) >= MAX_CHARS_PER_USER:
        flash(f'You have reached the maximum of {MAX_CHARS_PER_USER} active characters. A dead character frees up their slot.', 'error')
        # Ensure creation stats are cleared if they somehow reach here at limit
        session.pop('character_creation_stats', None)
        return redirect(url_for('display_game_output'))

    if 'character_creation_stats' not in session or 'stats' not in session['character_creation_stats']:
        flash('Character creation session data not found. Please try starting over.', 'error')
        return redirect(url_for('display_game_output', action='create_new_char'))

    creation_data = session['character_creation_stats']
    stats = creation_data['stats']

    new_character = Character(name=char_name)
    new_character.stats = stats.copy() # Use a copy of the stats

    # CON modifier should be calculated based on the actual stat value
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

    output_stream.truncate(0)
    output_stream.seek(0)

    # Call the new setup method
    game_manager_instance.setup_for_character(new_character)

    # Confirmation message (optional, as setup_for_character is verbose)
    if game_manager_instance.is_game_setup:
        success_message = f"Character {new_character.name} (user: {username}) created and game world prepared."
        flash(success_message, "success")
        game_manager_instance._print(success_message) # Also print to game log if desired
        session.pop('character_creation_stats', None) # Clear stats on full success
        session.pop('character_creation_name', None) # Clear name on full success
    else:
        # Character was saved, but game world setup (e.g., loading current town) failed.
        game_manager_instance._print(f"Character {new_character.name} (user: {username}) created, but game world setup failed. is_game_setup is False.")
        error_message = (f"Character {new_character.name} was saved, but there was an issue preparing the game world. "
                         f"You can try selecting the character from the main menu. If issues persist, please note the character name and contact support.")
        flash(error_message, "warning") # Warning, as character is saved.
        # Clear character creation stats and name as the character is saved and these are used/finalized.
        session.pop('character_creation_stats', None)
        session.pop('character_creation_name', None)

    return redirect(url_for('display_game_output'))


# --- Main Display Route ---

@app.route('/')
def display_game_output():
    global player_char
    global game_manager_instance

    popup_action_result = session.pop('action_result', None) # Get and clear action result from session

    user_logged_in = 'username' in session
    # Initialize these to False. Their final values will be determined by the logic below.
    show_character_selection = False
    show_character_creation_form = False
    player_char_loaded_or_selected = False # This will be true if a character is successfully loaded/selected
    characters_for_selection = []
    current_game_output = ""

    # Default values for template if no character is loaded / user not logged in
    player_name_display = "N/A"
    player_stats_display = {}
    player_hp_display = 0
    player_max_hp_display = 0
    player_gold_display = 0 # Will be set to default if showing creation form
    current_time_display = "N/A"
    current_town_display = "N/A"
    shop_inventory_display = ["Empty"]
    player_inventory_display = ["Empty"]
    player_journal_display = [] # Initialize journal display
    dead_characters_info = []
    character_creation_stats_display = None # For passing to template
    pending_char_name_display = None # For character creation name persistence

    available_towns = list(game_manager_instance.towns_map.keys())
    current_town_sub_locations = []
    all_towns_data = {}
    available_recipes = {}
    google_auth_is_configured = bool(GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET)

    if user_logged_in:
        username = session['username']
        characters_list = user_characters.get(username, [])
        user_graveyard_list = graveyard.get(username, [])

        if user_graveyard_list:
            for dead_char_data in user_graveyard_list:
                dead_characters_info.append({
                    'name': dead_char_data.get('name', 'Unknown'),
                    'level': dead_char_data.get('level', 0),
                })

        is_creating_new_char_action = request.args.get('action') == 'create_new_char'

        if is_creating_new_char_action:
            if len(characters_list) < MAX_CHARS_PER_USER:
                session.pop('selected_character_slot', None)
                player_char_loaded_or_selected = False # Explicitly not loading a character
                show_character_creation_form = True  # GOAL: Show the creation form
                show_character_selection = False     # Do not show selection

                # Prepare for character creation screen (blank character, default gold)
                output_stream.truncate(0)
                output_stream.seek(0)
                unnamed_char = Character(name=None)
                player_char = unnamed_char # Update global
                player_char.gold = 50 # Default gold for creation form display
                game_manager_instance.setup_for_character(unnamed_char) # Reset GM

                # Stat rolling for character creation
                if 'character_creation_stats' not in session:
                    initial_stats = Character.roll_all_stats()
                    session['character_creation_stats'] = {'stats': initial_stats, 'reroll_used': False}
                    flash("Stats rolled for new character! You can reroll one stat if you wish.", "info")

                character_creation_stats_display = session['character_creation_stats']
                pending_char_name_display = session.get('character_creation_name')


                if not characters_list:
                    current_game_output = "Welcome! Please create your first character."
                else:
                    current_game_output = "Create your new character."
            else: # At character limit
                flash(f"You cannot create more than {MAX_CHARS_PER_USER} characters.", "warning")
                # Clear pending creation stats if user hits limit and is sent away from creation screen
                session.pop('character_creation_stats', None)
                session.pop('character_creation_name', None) # Also clear name if at limit
                # Let flow continue to potentially show selected character or selection screen
                # show_character_creation_form remains False


        # This block runs if NOT (is_creating_new_char_action AND slots available)
        # It tries to load a character if one is selected,
        # OR determines if selection/creation should be shown if no character is active.
        if not show_character_creation_form: # Only proceed if not already decided to show creation form
            # If not showing creation form, any pending creation name should be cleared
            session.pop('character_creation_name', None)
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
                        else:
                            loaded_player_char = Character.from_dict(char_data)
                            game_manager_instance.setup_for_character(loaded_player_char)
                            if game_manager_instance.is_game_setup:
                                player_char = loaded_player_char # Update global
                                player_char_loaded_or_selected = True
                            else:
                                flash(f"Failed to set up game world for {loaded_player_char.name}. Please try re-creating or contact support.", "error")
                                player_char_loaded_or_selected = False
                                session.pop('selected_character_slot', None)
                    else: # Invalid slot index
                        session.pop('selected_character_slot', None)
                        player_char_loaded_or_selected = False
                except (ValueError, TypeError): # Invalid slot format
                     session.pop('selected_character_slot', None)
                     player_char_loaded_or_selected = False

            # If a character is loaded and active:
            if player_char_loaded_or_selected:
                player_name_display = player_char.name
                player_stats_display = player_char.stats
                player_hp_display = player_char.hp
                player_max_hp_display = player_char.get_effective_max_hp()
                player_gold_display = player_char.gold
                current_time_display = game_manager_instance.time.get_time_string()
                current_town_display = game_manager_instance.current_town.name
                if game_manager_instance.current_town:
                    current_town_sub_locations = game_manager_instance.current_town.sub_locations
                for town_obj in game_manager_instance.towns_map.values():
                    all_towns_data[town_obj.name] = {"sub_locations": town_obj.sub_locations}
                shop_items = {}
                for item in game_manager_instance.shop.inventory:
                    shop_items[item.name] = shop_items.get(item.name, 0) + 1
                shop_inventory_display = [f"{name} (x{qty})" for name, qty in shop_items.items()] or ["Empty"]
                player_inventory_display = [item.name for item in player_char.inventory] or ["Empty"]
                current_game_output = output_stream.getvalue()
                if game_manager_instance.shop:
                    available_recipes = game_manager_instance.shop.BASIC_RECIPES
                if hasattr(player_char, 'journal'): # Ensure journal attribute exists
                    player_journal_display = player_char.journal
            else: # No character is active/loaded (and not showing creation form from action=create_new_char)
                output_stream.truncate(0)
                output_stream.seek(0)
                unnamed_char = Character(name=None)
                player_char = unnamed_char # Update global
                player_char.gold = 50 # Default gold
                game_manager_instance.setup_for_character(unnamed_char) # Reset GM

                if characters_list: # User has characters, but none are selected/active
                    show_character_selection = True
                    for i, char_data_item in enumerate(characters_list):
                        characters_for_selection.append({
                            'name': char_data_item.get('name', 'Unknown'),
                            'level': char_data_item.get('level', 0),
                            'slot_index': i,
                            'is_dead': char_data_item.get('is_dead', False)
                        })
                    current_game_output = "Please select a character"
                    if len(characters_list) < MAX_CHARS_PER_USER:
                        current_game_output += " or create a new one."
                    # player_gold_display is implicitly 50 from player_char.gold if no char loaded
                else: # No characters exist for this user
                    show_character_creation_form = True # Show creation form
                    current_game_output = "Welcome! Please create your first character."
                    # player_gold_display is implicitly 50 as above
                    # Check if a name was stored from a previous attempt (e.g. failed validation then redirected here)
                    pending_char_name_display = session.get('character_creation_name')


    else: # User not logged in
        output_stream.truncate(0)
        output_stream.seek(0)
        unnamed_char = Character(name=None)
        player_char = unnamed_char # Update global
        player_char.gold = 50
        game_manager_instance.setup_for_character(unnamed_char)
        current_game_output = "Please log in to start your adventure."
        session.pop('character_creation_name', None) # Clear if navigating to login page

    # Ensure player_gold_display reflects the state for creation/no selection
    if show_character_creation_form or (not player_char_loaded_or_selected and not user_logged_in) or (user_logged_in and not player_char_loaded_or_selected):
        player_gold_display = player_char.gold # Should be 50 from unnamed_char
        if show_character_creation_form and not pending_char_name_display: # Ensure display name is fetched if form is shown
            pending_char_name_display = session.get('character_creation_name')


    # If no character is loaded, journal should be empty
    if not player_char_loaded_or_selected:
        player_journal_display = []

    # Retrieve event data from session for template
    awaiting_event_choice = session.get('awaiting_event_choice', False)
    pending_event_data_for_template = session.get('pending_event_data', None) if awaiting_event_choice else None
    last_skill_roll_str = session.pop('last_skill_roll_display_str', None) # Pop to clear after use

    return render_template('index.html',
                           user_logged_in=user_logged_in,
                           show_character_selection=show_character_selection,
                           characters_for_selection=characters_for_selection,
                           MAX_CHARS_PER_USER=MAX_CHARS_PER_USER,
                           dead_characters_info=dead_characters_info,
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
                           available_recipes=available_recipes,
                           player_journal=player_journal_display, # Pass journal to template
                           popup_action_result=popup_action_result, # Pass to template
                           hemlock_herbs_json=json.dumps(HEMLOCK_HERBS), # Added Hemlock's herbs
                           character_creation_stats=character_creation_stats_display, # Pass to template
                           stat_names_ordered=Character.STAT_NAMES, # Added for ordered stats display
                           pending_char_name=pending_char_name_display, # Added for name persistence
                           awaiting_event_choice=awaiting_event_choice,
                           pending_event_data_json=json.dumps(pending_event_data_for_template) if pending_event_data_for_template else None,
                           last_skill_roll_str=last_skill_roll_str
                           )

# --- Reroll Stat Route ---
@app.route('/reroll_stat/<stat_name>', methods=['POST'])
def reroll_stat_route(stat_name):
    if 'username' not in session:
        flash('You must be logged in to reroll stats.', 'error')
        return redirect(url_for('display_game_output'))

    if 'character_creation_stats' not in session:
        flash('No character creation stats found in session. Please start character creation.', 'error')
        return redirect(url_for('display_game_output', action='create_new_char'))

    creation_data = session['character_creation_stats']

    if creation_data.get('reroll_used', False):
        flash('You have already used your reroll for this character.', 'warning')
        return redirect(url_for('display_game_output', action='create_new_char'))

    if stat_name not in Character.STAT_NAMES:
        flash(f"Invalid stat name '{stat_name}' for reroll.", 'error')
        return redirect(url_for('display_game_output', action='create_new_char'))

    new_stat_value = Character.reroll_single_stat()
    creation_data['stats'][stat_name] = new_stat_value
    creation_data['reroll_used'] = True
    session['character_creation_stats'] = creation_data # Re-assign to session to ensure it's saved

    # Preserve character name if provided by JS
    char_name_from_form = request.form.get('character_name')
    if char_name_from_form is not None: # Even empty string should be saved if input was touched
        session['character_creation_name'] = char_name_from_form

    flash(f"{stat_name} rerolled to {new_stat_value}!", "success")
    return redirect(url_for('display_game_output', action='create_new_char'))


def parse_action_details(details_str: str) -> dict:
    """
    Parses a JSON string representing action details into a dictionary.
    If details_str is empty, null, or invalid JSON, returns an empty dictionary.
    """
    if not isinstance(details_str, str) or not details_str or details_str.strip() == "":
        if isinstance(details_str, (int, float)): # Handle if it's a number, which is not valid JSON for this func
            game_manager_instance._print(f"Warning: Action details received as a number: '{details_str}'. Expected a JSON string. Using empty details.")
            return {}
        elif not details_str: # Handles None or empty string before strip()
            return {}
        # If it's not a string but not explicitly handled (e.g. list, dict directly passed),
        # json.loads will raise TypeError later, which is caught.
        # However, the strip() call is the main concern for AttributeError.
        # The above check `not isinstance(details_str, str)` handles non-strings early for strip().
        # If it *is* a string but empty after strip, it's handled by `details_str.strip() == ""`
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
    # Diagnostic prints for the /action route itself
    print(f"DEBUG /action route: app.output_stream ID is {id(output_stream)}")
    print(f"DEBUG /action route: id(game_manager_instance) is {id(game_manager_instance)}")
    if game_manager_instance:
        print(f"DEBUG /action route: game_manager_instance.output_stream ID is {id(game_manager_instance.output_stream) if game_manager_instance.output_stream else 'None'}")
    else:
        print("DEBUG /action route: game_manager_instance is None")

    action_name = request.form.get('action_name')
    action_details_str = request.form.get('action_details', '{}') # Default to empty JSON object string

    # --- Start of Diagnostic Logging ---
    # print(f"\n--- /action route hit ---") # Consider app.logger.debug()
    # print(f"Received action_name: {action_name}") # Consider app.logger.debug()
    # print(f"Received action_details_str: {action_details_str}") # Consider app.logger.debug()
    # print(f"Global player_char: {player_char.name if player_char else 'None'}") # Consider app.logger.debug()
    # if player_char:
        # print(f"Global player_char.is_dead: {player_char.is_dead}") # Consider app.logger.debug()
    # else:
        # print(f"Global player_char.is_dead: N/A") # Consider app.logger.debug()
    # print(f"Global game_manager_instance available: {bool(game_manager_instance)}") # Consider app.logger.debug()
    # if game_manager_instance:
        # print(f"GM.character: {game_manager_instance.character.name if game_manager_instance.character else 'None'}") # Consider app.logger.debug()
        # print(f"GM.is_game_setup: {game_manager_instance.is_game_setup if hasattr(game_manager_instance, 'is_game_setup') else 'Attribute Missing'}") # Consider app.logger.debug()
        # print(f"GM.shop available: {bool(game_manager_instance.shop)}") # Consider app.logger.debug()
        # print(f"GM.event_manager available: {bool(game_manager_instance.event_manager)}") # Consider app.logger.debug()
    # --- End of Diagnostic Logging ---

    # Clear the stream before new action output
    output_stream.truncate(0) # Restore this
    output_stream.seek(0) # Restore this

    # Helper function to format action names for display
    def _format_action_name_for_display(name_technical: str) -> str:
        if not name_technical:
            return "Unknown Action"

        # Simple replacements based on common patterns
        name_display = name_technical.replace('_', ' ').title()

        # Specific overrides for better readability if needed
        if name_technical == "rest_short":
            name_display = "Rest (Short)"
        elif name_technical == "rest_long":
            name_display = "Rest (Long)"
        # Add more specific overrides here if other actions need custom display names

        return name_display

    if not action_name:
        flash("Error: No action selected. Please choose an action.", "error")
        # game_manager_instance._print("Error: No action_name provided.") # Kept for log, flash is for user
        return redirect(url_for('display_game_output'))

    # Use the updated parse_action_details function
    details_dict = parse_action_details(action_details_str)
    # print(f"Parsed action_details_dict: {details_dict}") # Diagnostic print, consider app.logger.debug()

    # Perform the game action
    try:
        action_name_display = _format_action_name_for_display(action_name)

        # Ensure a living character is loaded before performing actions
        if player_char is None or player_char.name is None or player_char.is_dead:
            flash("No active character or character is dead. Cannot perform action.", "error")
            return redirect(url_for('display_game_output'))

        # Crafting specific check: item name must be provided
        if action_name == "craft":
            item_name_to_craft = details_dict.get("item_name")
            if not item_name_to_craft:
                flash("Error: Item name cannot be empty for crafting.", "error")
                # No need to call perform_hourly_action if this fails
                return redirect(url_for('display_game_output'))

        # Explicitly check GameManager's setup status for the current player_char
        # This is crucial because game_manager_instance.character should be the same as player_char
        # and game_manager_instance.is_game_setup should be True if setup was successful.
        if not game_manager_instance.is_game_setup or game_manager_instance.character != player_char:
            # print(f"Action '{action_name}' aborted: GameManager not properly set up for character '{player_char.name}'.") # Consider app.logger.warning()
            # print(f"  GM.is_game_setup: {game_manager_instance.is_game_setup}") # Consider app.logger.debug()
            # print(f"  GM.character: {game_manager_instance.character.name if game_manager_instance.character else 'None'}") # Consider app.logger.debug()
            # print(f"  app.player_char: {player_char.name}") # Consider app.logger.debug()
            flash(f"Cannot perform action. Game world not fully initialized for {player_char.name}. Try re-selecting the character.", "error")
            return redirect(url_for('display_game_output'))

        # The following 'buy_from_npc' block seems like a placeholder or an alternative action path.
        # For the current task, we are focusing on actions going through perform_hourly_action.
        # If 'buy_from_npc' is meant to be a standard action processed by perform_hourly_action,
        # it might not need this special handling here. If it's different, its flash messages
        # would need separate consideration. For now, assuming it's not the primary focus for this refactor.
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
            # Explicit check of player_char (already done above, but can be more specific here if needed)
            if player_char is None or player_char.name is None or player_char.is_dead:
                # print(f"Action '{action_name}' aborted just before perform_hourly_action: No active/living character.") # Consider app.logger.warning()
                flash("No active character or character is dead. Cannot perform action.", "error")
                return redirect(url_for('display_game_output'))
            else:
                # print(f"Proceeding to game_manager_instance.perform_hourly_action for action: {action_name}") # Consider app.logger.info()
                action_result_data = game_manager_instance.perform_hourly_action(action_name, details_dict)

                if isinstance(action_result_data, dict) and action_result_data.get('type') == 'event_pending':
                    session['awaiting_event_choice'] = True
                    session['pending_event_data'] = {
                        'name': action_result_data.get('event_name'),
                        'description': action_result_data.get('event_description'),
                        'choices': action_result_data.get('choices')
                    }
                    flash(f"EVENT: {action_result_data.get('event_name')}! Check Journal or Game Log for details.", "info")
                    game_manager_instance._print(f"EVENT: {action_result_data.get('event_name')} requires your attention!") # Log remains
                else:
                    # Action completed or no event, clear any previous event data
                    session.pop('awaiting_event_choice', None)
                    session.pop('pending_event_data', None)
                    # Default success message for actions that don't trigger an event
                    flash(f"Action '{action_name_display}' performed. Check Journal or Game Log for details.", "info")

        # ---- START NEW SAVE LOGIC ----
        # Save character state if alive and loaded
        # Use global player_char which should be the same as game_manager_instance.character
        if player_char and player_char.name and not player_char.is_dead:
            username = session.get('username')
            slot_index = session.get('selected_character_slot')
            if username and slot_index is not None:
                # Ensure the slot_index is valid for the list of characters for that user
                if username in user_characters and 0 <= slot_index < len(user_characters[username]):
                    user_characters[username][slot_index] = player_char.to_dict(current_town_name=game_manager_instance.current_town.name)
                    save_user_characters()
                    # Optional: game_manager_instance._print("  Character data saved after action.")
                else:
                    # This case should ideally not be reached if session management is correct
                    game_manager_instance._print(f"  Warning: Character slot data mismatch for user {username}, slot {slot_index}. Could not save character state after action.")
            else:
                # This case implies an issue with session state or a scenario where character exists without full session setup
                 game_manager_instance._print("  Warning: User session data (username or slot_index) missing. Could not save character state after action.")
        # ---- END NEW SAVE LOGIC ----

        # Print stream value before setting it to session for diagnostics
        # action_route_stream_value = output_stream.getvalue() # Removed this older diagnostic
        # print(f"DEBUG APP /action: output_stream.getvalue() before setting session is:\n'''{action_route_stream_value}'''")

        # After action, check for death
        if player_char.is_dead:
            username = session.get('username')
            slot_index = session.get('selected_character_slot')
            char_name_for_log = player_char.name if player_char and player_char.name else "Character"

            # Log death to journal
            # Ensure game_manager_instance and its time object are available
            death_timestamp_str = None
            if game_manager_instance and hasattr(game_manager_instance, 'time') and hasattr(game_manager_instance.time, 'get_time_string'):
                death_timestamp_str = game_manager_instance.time.get_time_string()

            # Check if death was already logged for this character instance in this "death event"
            # This is a simple check; a more robust solution might involve a flag on the character object
            # or checking the last few journal entries more thoroughly.
            already_logged_this_death = False
            if game_manager_instance and game_manager_instance.character and hasattr(game_manager_instance.character, 'journal') and game_manager_instance.character.journal:
                last_entry = game_manager_instance.character.journal[-1]
                if last_entry.action_type == "Death" and last_entry.summary.startswith(char_name_for_log):
                    # A death entry for this character is the last one, assume it's this death.
                    # This might not be perfectly accurate if other actions could happen after death but before this block.
                    already_logged_this_death = True

            if not already_logged_this_death and game_manager_instance and hasattr(game_manager_instance, 'add_journal_entry'):
                game_manager_instance.add_journal_entry(
                    action_type="Death", # Using "Death" as type
                    summary=f"{char_name_for_log} has succumbed to their fate.",
                    outcome="Character data moved to graveyard.",
                    timestamp=death_timestamp_str # Pass string timestamp, add_journal_entry handles conversion
                )
                # Save character data one last time to ensure the death journal entry is persisted with the character
                # before they are moved to the graveyard.
                if username and slot_index is not None and user_characters.get(username) and 0 <= slot_index < len(user_characters[username]):
                    # We need to save the version of player_char that has the death entry.
                    # game_manager_instance.character should be player_char.
                    user_characters[username][slot_index] = game_manager_instance.character.to_dict(current_town_name=game_manager_instance.current_town.name if game_manager_instance.current_town else "Unknown")
                    save_user_characters()


            if username and slot_index is not None:
                if username in user_characters and 0 <= slot_index < len(user_characters[username]):
                    dead_char_data = user_characters[username].pop(slot_index)
                    dead_char_data['is_dead'] = True # Ensure it's marked dead
                    # The journal entry should be part of dead_char_data if saved correctly above.
                    graveyard.setdefault(username, []).append(dead_char_data)
                    save_user_characters()
                    save_graveyard()
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
        game_manager_instance._print(f"An error occurred while performing action '{action_name_display}': {e}")
        import traceback
        game_manager_instance._print(f"Traceback: {traceback.format_exc()}")
        flash("An unexpected error occurred. Check the game log for more details.", "error")

    # Capture action result for popup before redirecting
    session['action_result'] = output_stream.getvalue()
    # Clear the main output_stream AFTER capturing its value for the session,
    # so it doesn't get displayed in the main log area on the next page load.
    # However, the game_output for the next page load in display_game_output
    # will re-fetch from output_stream.getvalue().
    # This means the action result WILL appear in the main log as well.
    # If the goal is to ONLY show it in the popup and NOT in the main log,
    # then output_stream must be cleared here.
    # output_stream.truncate(0) # Removed as per new requirement
    # output_stream.seek(0) # Removed as per new requirement

    return redirect(url_for('display_game_output'))

@app.route('/submit_event_choice', methods=['POST'])
def submit_event_choice_route():
    global player_char # To access current character
    global game_manager_instance # To call execute_skill_choice

    if 'username' not in session or not session.get('awaiting_event_choice'):
        flash("Invalid session or no event choice pending.", "error")
        return redirect(url_for('display_game_output'))

    event_name_from_form = request.form.get('event_name')
    choice_index_str = request.form.get('choice_index')

    # Clear the stream before new action output from execute_skill_choice
    output_stream.truncate(0)
    output_stream.seek(0)

    stored_event_data = session.get('pending_event_data')

    if not event_name_from_form or choice_index_str is None or not stored_event_data:
        flash("Missing event data or choice index.", "error")
        session.pop('awaiting_event_choice', None) # Clear flags anyway
        session.pop('pending_event_data', None)
        return redirect(url_for('display_game_output'))

    if stored_event_data.get('name') != event_name_from_form:
        flash("Mismatch between submitted event and pending event. Please try again.", "error")
        session.pop('awaiting_event_choice', None)
        session.pop('pending_event_data', None)
        return redirect(url_for('display_game_output'))

    try:
        choice_index = int(choice_index_str)
    except ValueError:
        flash("Invalid choice index format.", "error")
        session.pop('awaiting_event_choice', None)
        session.pop('pending_event_data', None)
        return redirect(url_for('display_game_output'))

    # Find the event object from GAME_EVENTS
    selected_event_obj = next((event for event in GAME_EVENTS if event.name == event_name_from_form), None)

    if not selected_event_obj:
        flash(f"Event '{event_name_from_form}' not found in game data.", "error")
        session.pop('awaiting_event_choice', None)
        session.pop('pending_event_data', None)
        return redirect(url_for('display_game_output'))

    # Execute the choice
    # The execute_skill_choice method will print to output_stream and log to journal
    execution_outcome = game_manager_instance.event_manager.execute_skill_choice(selected_event_obj, choice_index)

    # Store roll data for display (for the next plan step)
    if isinstance(execution_outcome, dict) and 'roll_data' in execution_outcome and \
       isinstance(execution_outcome['roll_data'], dict) and 'formatted_string' in execution_outcome['roll_data']:
        session['last_skill_roll_display_str'] = execution_outcome['roll_data']['formatted_string']
    else: # Fallback if roll_data or formatted_string isn't there as expected
        session.pop('last_skill_roll_display_str', None)


    # Clear event state from session
    session.pop('awaiting_event_choice', None)
    session.pop('pending_event_data', None)

    # Save character state after event resolution
    if player_char and player_char.name and not player_char.is_dead:
        username = session.get('username')
        slot_idx = session.get('selected_character_slot')
        if username and slot_idx is not None and username in user_characters and 0 <= slot_idx < len(user_characters[username]):
            user_characters[username][slot_idx] = player_char.to_dict(current_town_name=game_manager_instance.current_town.name)
            save_user_characters()
        else:
            game_manager_instance._print("  Warning: Could not save character state after event due to session/slot mismatch.")

    # Check for death after event resolution
    if player_char and player_char.is_dead:
        # Handle character death (similar to how it's done in /action route)
        username = session.get('username')
        slot_idx = session.get('selected_character_slot')
        # char_name_for_log = player_char.name if player_char and player_char.name else "Character" # Already logged by execute_skill_choice
        if username and slot_idx is not None and user_characters.get(username) and 0 <= slot_idx < len(user_characters[username]):
            dead_char_data = user_characters[username].pop(slot_idx)
            dead_char_data['is_dead'] = True
            graveyard.setdefault(username, []).append(dead_char_data)
            save_user_characters()
            save_graveyard()
            flash(f"{dead_char_data.get('name', 'The character')} has died (due to event) and been moved to the graveyard.", "error")
            session.pop('selected_character_slot', None)
            return redirect(url_for('display_game_output')) # Redirect to char selection

    # Capture the output from execute_skill_choice for the popup/main log
    session['action_result'] = output_stream.getvalue()

    return redirect(url_for('display_game_output'))

if __name__ == '__main__':
    # Note: When running with `flask run`, this block might not execute depending on environment.
    # Ensure game_manager_instance is initialized globally as above.
    app.run(debug=True, host='0.0.0.0', port=5001)
