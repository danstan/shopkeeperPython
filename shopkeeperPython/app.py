print("DEBUG: Top of app.py", flush=True)
from flask import Flask, render_template, request, redirect, url_for, session, flash, get_flashed_messages
import io
import json
import os # Added for environment variables
import datetime
import shutil

from shopkeeperPython.game.game_manager import GameManager
from shopkeeperPython.game.character import Character
from shopkeeperPython.game.shop import Shop # Ensure Shop is imported
# Item is implicitly used by Character.to_dict/from_dict if inventory has items.
# Pylint might not see this if no direct instantiation of Item happens in app.py.
# For now, let's trust Pylint's static analysis; if runtime errors occur, it can be re-added.
# from shopkeeperPython.game.item import Item
from shopkeeperPython.game.game_manager import HEMLOCK_HERBS, BORIN_ITEMS # Added import
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

# --- Application Context Globals Setup ---
# These will be managed per request using Flask's 'g' object.

@app.before_request
def before_request_setup():
    """
    Ran before each request.
    Initializes request-specific game objects on Flask's 'g' context object.
    """
    from flask import g  # Import g here to avoid circular dependency issues at module level

    g.output_stream = io.StringIO()
    # Default character if no one is logged in or selected
    default_char = Character(name=None)
    default_char.gold = 50 # Default starting gold

    username = session.get('username')
    selected_slot_index = session.get('selected_character_slot')
    active_char_instance = None

    # This flag helps determine if game_manager.setup_for_character() should be called.
    # It's true if an actual character is loaded, false if using the placeholder default_char.
    character_loaded_for_setup = False

    if username and selected_slot_index is not None:
        characters_list = user_characters.get(username, [])
        if 0 <= selected_slot_index < len(characters_list):
            char_data = characters_list[selected_slot_index]
            if not char_data.get('is_dead', False):
                active_char_instance = Character.from_dict(char_data)
                character_loaded_for_setup = True # A specific character is being loaded
            else:
                session.pop('selected_character_slot', None)
                flash(f"The selected character, {char_data.get('name', 'Unknown')}, is dead and cannot be played. Please select another character.", "warning")
                # g.output_stream.write(f"INFO: Selected character {char_data.get('name', 'Unknown')} is dead.\n")
        else: # Invalid slot index
            session.pop('selected_character_slot', None)
            # g.output_stream.write("INFO: Invalid character slot selected.\n")

    if active_char_instance:
        g.player_char = active_char_instance
    else:
        g.player_char = default_char
        # If no active character, ensure game_manager doesn't think it's set up for a real game state
        character_loaded_for_setup = False

    g.game_manager = GameManager(player_character=g.player_char, output_stream=g.output_stream)

    if character_loaded_for_setup:
        # This setup is for an existing, loaded character.
        # It ensures the GM knows about the current town, etc.
        g.game_manager.setup_for_character(g.player_char) # g.player_char is active_char_instance here
        if not g.game_manager.is_game_setup:
            # This implies an issue with loading the character's environment (e.g. town not found)
            flash(f"Warning: Failed to fully initialize game world for {g.player_char.name}. Some features might be unavailable or the character may be in an invalid state. Consider re-selecting or contacting support if issues persist.", "error")
            # Potentially revert to a default state if setup fails critically
            # For now, we proceed with is_game_setup as False, and routes should check this.
    # else:
        # If using default_char, g.game_manager is initialized with it,
        # but g.game_manager.is_game_setup remains False by default in GameManager.
        # No further setup is needed for the default character placeholder.
        pass


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
    session.pop('selected_character_slot', None)
    session.pop('character_creation_stats', None)
    session.pop('character_creation_name', None)
    session.pop('awaiting_event_choice', None) # Clear event flag
    session.pop('pending_event_data', None)    # Clear event data
    get_flashed_messages() # Clear any existing flashed messages before adding new one
    flash('You have been logged out.', 'success')
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
    # return """
    # <h1>Register</h1>
    # <form method="post">
    #     Username: <input type="text" name="username" required><br>
    #     Password: <input type="password" name="password" required><br>
    #     <input type="submit" value="Register">
    # </form>
    # <p><a href="{{ url_for('display_game_output') }}">Back to Login</a></p>
    # """ # Using triple quotes for the multi-line string.
    return render_template('register.html') # This would be the ideal line


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
        session.pop('character_creation_stats', None)
        session.pop('character_creation_name', None)
        session.pop('awaiting_event_choice', None) # Clear event flag
        session.pop('pending_event_data', None)    # Clear event data
        flash(f"Character slot {slot_index + 1} selected.", "success")
    else:
        flash("Invalid character slot.", "error")
        # Even on invalid selection, clear pending event state
        session.pop('awaiting_event_choice', None)
        session.pop('pending_event_data', None)


    return redirect(url_for('display_game_output'))

@app.route('/create_character', methods=['POST'])
def create_character_route():
    from flask import g # Access g for current request context
    global user_characters # Still global for persistent storage, holds all users' characters

    if 'username' not in session:
        flash('You must be logged in to create a character.', 'error')
        return redirect(url_for('display_game_output'))

    username = session['username']
    char_name = request.form.get('character_name')

    app.logger.info(f"CREATE_CHARACTER_ROUTE: User '{username}' attempting to create character. Name: '{char_name}'. Session stats: {session.get('character_creation_stats')}")

    if not char_name or not char_name.strip():
        flash('Character name cannot be empty or just whitespace.', 'error')
        app.logger.warning(f"CREATE_CHARACTER_ROUTE: Character name validation failed for user '{username}'. Name: '{char_name}'")
        session['character_creation_name'] = char_name # Persist name
        return redirect(url_for('display_game_output', action='create_new_char'))

    # --- Global Character Name Uniqueness Check ---
    if is_character_name_taken(char_name, user_characters, graveyard):
        flash(f"Character name '{char_name}' is already taken. Please choose another.", 'error')
        app.logger.warning(f"CREATE_CHARACTER_ROUTE: Character name '{char_name}' taken for user '{username}'.")
        session['character_creation_name'] = char_name # Persist name
        return redirect(url_for('display_game_output', action='create_new_char'))
    # --- End of Uniqueness Check ---

    if username not in user_characters:
        user_characters[username] = [] # Should have been created at registration, but good safeguard
        app.logger.info(f"CREATE_CHARACTER_ROUTE: Initialized empty character list for user '{username}'.")

    active_characters_list = user_characters.get(username, [])
    # The prompt asks to change the limit check to active characters.
    # The previous logic (len(user_characters[username])) checked total slots.
    # Now, it should be len(active_characters_list) because dead chars are moved out.
    if len(active_characters_list) >= MAX_CHARS_PER_USER:
        flash(f'You have reached the maximum of {MAX_CHARS_PER_USER} active characters. A dead character frees up their slot.', 'error')
        app.logger.warning(f"CREATE_CHARACTER_ROUTE: User '{username}' at character limit ({MAX_CHARS_PER_USER}).")
        # Ensure creation stats are cleared if they somehow reach here at limit
        session.pop('character_creation_stats', None)
        return redirect(url_for('display_game_output'))

    if 'character_creation_stats' not in session or 'stats' not in session['character_creation_stats']:
        flash('Character creation session data not found. Please try starting over.', 'error')
        app.logger.error(f"CREATE_CHARACTER_ROUTE: 'character_creation_stats' not found in session for user '{username}'. Current session stats: {session.get('character_creation_stats')}")
        session['character_creation_name'] = char_name # Persist name
        return redirect(url_for('display_game_output', action='create_new_char'))

    creation_data = session['character_creation_stats']
    app.logger.info(f"CREATE_CHARACTER_ROUTE: Proceeding with creation for user '{username}', name '{char_name}', stats: {creation_data}")
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

    # Update g.player_char and g.game_manager for the *current* request context.
    # This makes the newly created character immediately active for this request if needed,
    # though the redirect will trigger before_request_setup again, which will load based on new session.
    g.player_char = new_character
    g.output_stream.truncate(0) # Clear stream for this new character context
    g.output_stream.seek(0)
    # Setup the game manager on g with the new character
    g.game_manager.character = new_character # Assign new char to existing GM on g
    g.game_manager.setup_for_character(new_character) # Now setup this GM instance

    if g.game_manager.is_game_setup:
        success_message = f"Character {new_character.name} (user: {username}) created and game world prepared."
        flash(success_message, "success")
        g.game_manager._print(success_message)
        session.pop('character_creation_stats', None)
        session.pop('character_creation_name', None)
        session.pop('awaiting_event_choice', None) # Clear event state
        session.pop('pending_event_data', None)
    else:
        g.game_manager._print(f"Character {new_character.name} (user: {username}) created, but game world setup failed. is_game_setup is False.")
        error_message = (f"Character {new_character.name} was saved, but there was an issue preparing the game world. "
                         f"You can try selecting the character from the main menu. If issues persist, please note the character name and contact support.")
        flash(error_message, "warning")
        session.pop('character_creation_stats', None)
        session.pop('character_creation_name', None)
        # Also clear event state here in case of failure after creation attempt
        session.pop('awaiting_event_choice', None)
        session.pop('pending_event_data', None)


    return redirect(url_for('display_game_output'))


# --- Main Display Route ---

@app.route('/')
def display_game_output():
    from flask import g # Access g for current request context
    # player_char, game_manager_instance, and output_stream are now on g,
    # initialized by before_request_setup.

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
    player_gold_display = 0 # Will be derived from g.player_char.gold later
    current_time_display = "N/A"
    current_town_display = "N/A"
    shop_inventory_display = ["Empty"]
    player_inventory_display = ["Empty"]
    player_journal_display = []
    dead_characters_info = []
    character_creation_stats_display = None
    pending_char_name_display = None

    # available_towns will be derived from g.game_manager later
    available_towns = list(g.game_manager.towns_map.keys()) if g.game_manager else []
    current_town_sub_locations = []
    all_towns_data = {}
    available_recipes = {}
    google_auth_is_configured = bool(GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET)

    if user_logged_in:
        username = session['username']
        # These still come from global persistent storage
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
            # Check against active characters for the user (non-dead ones)
            active_user_chars = [char_data for char_data in characters_list if not char_data.get('is_dead', False)]
            if len(active_user_chars) < MAX_CHARS_PER_USER:
                session.pop('selected_character_slot', None) # Ensure no character is "selected"
                # This should cause before_request_setup on the *next* request to use default char,
                # or if this is a POST-redirect-GET, it might already be default.
                # For current request, we want to show creation form.
                player_char_loaded_or_selected = False
                show_character_creation_form = True
                show_character_selection = False
                # flash("DEBUG: In display_game_output for create_new_char action. show_character_creation_form set to true.", "debug")
                app.logger.info(f"DISPLAY_GAME_OUTPUT: User '{username}' creating new char. Show creation form. Session stats: {session.get('character_creation_stats')}, Session name: {session.get('character_creation_name')}")

                # Ensure g.player_char is the default, and g.output_stream is clear for creation.
                # before_request_setup should have set g.player_char to default if selected_character_slot is None.
                # If g.player_char is not default, or to be absolutely sure for this path:
                if g.player_char.name is not None: # If a character was somehow loaded
                    g.player_char = Character(name=None)
                    g.player_char.gold = 50
                    g.game_manager.character = g.player_char
                    g.game_manager.is_game_setup = False # Reset GM state for default character

                g.output_stream.truncate(0)
                g.output_stream.seek(0)
                # g.player_char.gold is already 50 for default char.
                # g.game_manager is already using this g.player_char.

                # Ensure character_creation_stats are initialized if missing or invalid
                character_creation_data = session.get('character_creation_stats')
                if not character_creation_data or 'stats' not in character_creation_data:
                    initial_stats = Character.roll_all_stats()  # This class method call is fine
                    session['character_creation_stats'] = {'stats': initial_stats, 'reroll_used': False}
                    flash("Your initial stats have been rolled. You can reroll one stat once.", "info")
                    app.logger.info(f"DISPLAY_GAME_OUTPUT: Initial stats rolled for '{username}' due to missing/invalid session data. New stats: {session['character_creation_stats']}")
                    # print("DEBUG: Initial stats rolled and saved to session due to missing/invalid data.", flush=True)
                else:
                    app.logger.info(f"DISPLAY_GAME_OUTPUT: Using existing session stats for '{username}': {character_creation_data}")


                character_creation_stats_display = session['character_creation_stats']
                pending_char_name_display = session.get('character_creation_name')
                app.logger.info(f"DISPLAY_GAME_OUTPUT: For creation form - User '{username}', Pending Name: '{pending_char_name_display}', Stats Display: {character_creation_stats_display}")


                # Game output for creation screen
                if not characters_list: # Message based on whether user has ANY characters
                    g.output_stream.write("Welcome! Please create your first character.")
                else:
                    g.output_stream.write("Create your new character.")
                # current_game_output will be built from g.output_stream at the end of the function
            else: # At character limit
                flash(f"You cannot create more than {MAX_CHARS_PER_USER} active characters.", "warning")
                session.pop('character_creation_stats', None)
                session.pop('character_creation_name', None)
                # Fall through to display existing character or selection screen
                # show_character_creation_form remains False, so next block will execute


        # This block runs if NOT (is_creating_new_char_action AND slots available)
        # It tries to load a character if one is selected,
        # OR determines if selection/creation should be shown if no character is active.
        if not show_character_creation_form: # Only proceed if not already decided to show creation form
            session.pop('character_creation_name', None) # Clear if not on creation form

            # g.player_char and g.game_manager are already set up by before_request_setup
            # based on session['selected_character_slot'] or to defaults.
            # We need to determine if a real character was loaded for player_char_loaded_or_selected.
            # g.game_manager.is_game_setup is True if setup_for_character was successful for a loaded char.
            if g.player_char and g.player_char.name is not None and g.game_manager.is_game_setup:
                player_char_loaded_or_selected = True
            else:
                player_char_loaded_or_selected = False
                # If a character was supposed to be loaded (selected_slot was not None) but failed
                # (e.g. dead, invalid slot, or GM setup failed), before_request_setup might have flashed
                # a message and potentially reverted g.player_char to default.
                # The g.output_stream might already contain messages from before_request_setup.
                # If g.output_stream is empty, it means a default char was loaded without issues.

            if player_char_loaded_or_selected:
                player_name_display = g.player_char.name
                player_stats_display = g.player_char.stats
                player_hp_display = g.player_char.hp
                player_max_hp_display = g.player_char.get_effective_max_hp()
                # player_gold_display is handled globally at the end of display_game_output from g.player_char
                current_time_display = g.game_manager.time.get_time_string()
                current_town_display = g.game_manager.current_town.name if g.game_manager.current_town else "Unknown"
                if g.game_manager.current_town:
                    current_town_sub_locations = g.game_manager.current_town.sub_locations
                for town_obj in g.game_manager.towns_map.values(): # towns_map is on GM instance
                    all_towns_data[town_obj.name] = {"sub_locations": town_obj.sub_locations}
                shop_items = {}
                if g.game_manager.shop: # Check if shop exists on GM instance
                    for item_in_shop in g.game_manager.shop.inventory: # Use item_in_shop to avoid conflict
                        shop_items[item_in_shop.name] = shop_items.get(item_in_shop.name, 0) + 1
                shop_inventory_display = [f"{name} (x{qty})" for name, qty in shop_items.items()] or ["Empty"]
                player_inventory_display = [item.name for item in g.player_char.inventory] or ["Empty"]
                # current_game_output will be built from g.output_stream at the end
                if g.game_manager.shop:
                    available_recipes = g.game_manager.shop.BASIC_RECIPES # Assuming this is a static/class member or simple property
                if hasattr(g.player_char, 'journal'):
                    player_journal_display = g.player_char.journal
            else: # No character is active/loaded (and not decided to show creation form by action=create_new_char)
                  # g.player_char is default, g.game_manager is default.
                  # g.output_stream might have messages from before_request_setup (e.g. dead char selected).
                if username: # Only show selection/creation options if logged in
                    if characters_list: # User has characters, but none are selected/active
                        show_character_selection = True
                        for i, char_data_item in enumerate(characters_list):
                            characters_for_selection.append({
                                'name': char_data_item.get('name', 'Unknown'),
                                'level': char_data_item.get('level', 0),
                                'slot_index': i,
                                'is_dead': char_data_item.get('is_dead', False)
                            })
                        # If g.output_stream is empty, add a default message. Otherwise, preserve message from before_request.
                        if not g.output_stream.getvalue().strip():
                            g.output_stream.write("Please select a character")
                            # Check active (non-dead) characters for the "or create new" part
                            active_user_chars = [cd for cd in characters_list if not cd.get('is_dead', False)]
                            if len(active_user_chars) < MAX_CHARS_PER_USER:
                                g.output_stream.write(" or create a new one.")
                    else: # No characters exist for this user
                        show_character_creation_form = True # Show creation form
                        if not g.output_stream.getvalue().strip(): # If stream is empty
                            g.output_stream.write("Welcome! Please create your first character.")
                        # Check if a name was stored from a previous attempt
                        pending_char_name_display = session.get('character_creation_name')
                # player_gold_display will be from g.player_char (default) at the end


    else: # User not logged in
        # g.player_char and g.game_manager are default from before_request_setup.
        # g.output_stream might have content if before_request_setup wrote to it (though unlikely for non-logged in).
        # If stream is empty, provide a login message.
        if not g.output_stream.getvalue().strip():
            g.output_stream.write("Please log in to start your adventure.")
        session.pop('character_creation_name', None) # Clear any pending creation name

    # Consolidate current_game_output from g.output_stream
    # current_game_output was initialized to ""
    # If any messages were written to g.output_stream by logic above (e.g. for char creation, selection prompts),
    # they will be included here.
    current_game_output += g.output_stream.getvalue()

    # player_gold_display is always from g.player_char (which is either active or default)
    player_gold_display = g.player_char.gold
    if show_character_creation_form and not pending_char_name_display:
        # If we decided to show creation form, ensure pending name is fetched if it exists
        pending_char_name_display = session.get('character_creation_name')

    if not player_char_loaded_or_selected: # If no specific character active, journal is empty
        player_journal_display = []

    # available_towns from g.game_manager (already set if GM exists)
    if g.game_manager:
        available_towns = list(g.game_manager.towns_map.keys())
    else: # Should not happen if before_request_setup is correct
        available_towns = []


    # Retrieve event data from session
    awaiting_event_choice_session = session.get('awaiting_event_choice', False)
    pending_event_data_session = session.get('pending_event_data', None)

    # Determine actual event display state for the template
    # If showing character creation or selection, suppress event pop-up and clear session flags
    if show_character_creation_form or show_character_selection:
        awaiting_event_choice_for_template = False
        pending_event_data_for_template = None
        # Clear the actual session flags as we are in a non-gameplay state
        if session.get('awaiting_event_choice'): # Check before popping
            session.pop('awaiting_event_choice')
        if session.get('pending_event_data'): # Check before popping
            session.pop('pending_event_data')
    else:
        awaiting_event_choice_for_template = awaiting_event_choice_session
        pending_event_data_for_template = pending_event_data_session if awaiting_event_choice_for_template else None

    last_skill_roll_str = session.pop('last_skill_roll_display_str', None) # Pop to clear after use

    # Shop data for UI
    shop_data_for_ui = None
    if g.game_manager and g.game_manager.shop:
        shop_instance = g.game_manager.shop
        next_level_cost = None
        next_level_slots = None
        next_level_quality_bonus = None
        if shop_instance.shop_level < Shop.MAX_SHOP_LEVEL:
            next_level_config = Shop.SHOP_LEVEL_CONFIG.get(shop_instance.shop_level + 1)
            if next_level_config: # Should always exist if not max level
                next_level_cost = next_level_config["cost_to_upgrade"]
                next_level_slots = next_level_config["max_inventory_slots"]
                next_level_quality_bonus = next_level_config["crafting_quality_bonus"]

        shop_data_for_ui = {
            "name": shop_instance.name,
            "level": shop_instance.shop_level,
            "specialization": shop_instance.specialization,
            "inventory_count": len(shop_instance.inventory),
            "max_inventory_slots": shop_instance.max_inventory_slots,
            "current_quality_bonus": Shop.SHOP_LEVEL_CONFIG[shop_instance.shop_level]["crafting_quality_bonus"],
            "next_level_cost": next_level_cost,
            "next_level_slots": next_level_slots,
            "next_level_quality_bonus": next_level_quality_bonus,
            "max_level_reached": shop_instance.shop_level >= Shop.MAX_SHOP_LEVEL
        }

    shop_config_for_ui = {
        "specialization_types": Shop.SPECIALIZATION_TYPES,
        "max_shop_level": Shop.MAX_SHOP_LEVEL
    }

    return render_template('index.html',
                           user_logged_in=user_logged_in,
                           show_character_selection=show_character_selection,
                           characters_for_selection=characters_for_selection,
                           MAX_CHARS_PER_USER=MAX_CHARS_PER_USER, # This is a module global constant
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
                           google_auth_is_configured=google_auth_is_configured, # Module global constant
                           available_towns=available_towns,
                           current_town_sub_locations_json=json.dumps(current_town_sub_locations),
                           all_towns_data_json=json.dumps(all_towns_data),
                           available_recipes=available_recipes,
                           player_journal=player_journal_display,
                           popup_action_result=popup_action_result,
                           hemlock_herbs_json=json.dumps(HEMLOCK_HERBS), # Module global constant
                           borin_items_json=json.dumps(BORIN_ITEMS), # Added for Borin's items

                           shop_data_json=json.dumps(shop_data_for_ui),
                           shop_config_json=json.dumps(shop_config_for_ui),

                           character_creation_stats=character_creation_stats_display,
                           stat_names_ordered=Character.STAT_NAMES, # Class attribute
                           pending_char_name=pending_char_name_display,
                           awaiting_event_choice=awaiting_event_choice_for_template, # Use the conditioned variable
                           pending_event_data_json=json.dumps(pending_event_data_for_template) if pending_event_data_for_template else None, # Use the conditioned variable
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
    from flask import g # Ensure g is accessible

    # Check if g.game_manager is available; if not, cannot print, but can still attempt parse.
    # This situation should be rare in normal operation if before_request_setup works.
    gm_available = hasattr(g, 'game_manager') and g.game_manager is not None

    if not isinstance(details_str, str) or not details_str or details_str.strip() == "":
        if isinstance(details_str, (int, float)):
            if gm_available:
                g.game_manager._print(f"Warning: Action details received as a number: '{details_str}'. Expected a JSON string. Using empty details.")
            return {}
        elif not details_str:
            return {}
    try:
        details_dict = json.loads(details_str)
        if not isinstance(details_dict, dict):
            if gm_available:
                g.game_manager._print(f"Warning: Action details resolved to non-dictionary type: '{details_str}'. Using empty details.")
            return {}
        return details_dict
    except json.JSONDecodeError as e:
        if gm_available:
            g.game_manager._print(f"Error parsing action_details JSON string '{details_str}': {e}. Using empty details.")
        return {}
    except TypeError as e:
        if gm_available:
            g.game_manager._print(f"Error (TypeError) parsing action_details string '{details_str}': {e}. Using empty details.")
        return {}


@app.route('/action', methods=['POST'])
def perform_action():
    from flask import g # Access g for current request context
    # output_stream, player_char, game_manager_instance are now on g.

    # Diagnostic prints using g
    # print(f"DEBUG /action route: g.output_stream ID is {id(g.output_stream)}")
    # print(f"DEBUG /action route: id(g.game_manager) is {id(g.game_manager)}")
    # if g.game_manager:
    #     print(f"DEBUG /action route: g.game_manager.output_stream ID is {id(g.game_manager.output_stream) if g.game_manager.output_stream else 'None'}")
    # else:
    #     print("DEBUG /action route: g.game_manager is None")

    action_name = request.form.get('action_name')
    action_details_str = request.form.get('action_details', '{}')

    # --- Start of Diagnostic Logging (using g) ---
    # print(f"\n--- /action route hit ---")
    # print(f"Received action_name: {action_name}")
    # print(f"Received action_details_str: {action_details_str}")
    # print(f"g.player_char: {g.player_char.name if g.player_char else 'None'}")
    # if g.player_char:
    #     print(f"g.player_char.is_dead: {g.player_char.is_dead}")
    # print(f"g.game_manager available: {bool(g.game_manager)}")
    # if g.game_manager:
    #     print(f"GM.character: {g.game_manager.character.name if g.game_manager.character else 'None'}")
    #     print(f"GM.is_game_setup: {g.game_manager.is_game_setup if hasattr(g.game_manager, 'is_game_setup') else 'Attribute Missing'}")
    # --- End of Diagnostic Logging ---

    g.output_stream.truncate(0) # Use g.output_stream
    g.output_stream.seek(0)   # Use g.output_stream

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
    details_dict = parse_action_details(action_details_str) # parse_action_details now uses g.game_manager

    # Perform the game action
    try:
        action_name_display = _format_action_name_for_display(action_name) # This helper is fine

        # Ensure a living character is loaded (now from g)
        if g.player_char is None or g.player_char.name is None or g.player_char.is_dead:
            flash("No active character or character is dead. Cannot perform action.", "error")
            return redirect(url_for('display_game_output'))

        # Crafting specific check: item name must be provided
        if action_name == "craft":
            item_name_to_craft = details_dict.get("item_name")
            if not item_name_to_craft:
                flash("Error: Item name cannot be empty for crafting.", "error")
                # No need to call perform_hourly_action if this fails
                return redirect(url_for('display_game_output'))

        # Explicitly check GameManager's setup status for the current g.player_char
        # This is crucial because g.game_manager.character should be the same as g.player_char
        # and g.game_manager.is_game_setup should be True if setup was successful via before_request_setup.
        if not g.game_manager.is_game_setup or g.game_manager.character != g.player_char:
            flash(f"Cannot perform action. Game world not fully initialized for {g.player_char.name}. Try re-selecting the character or ensure the character is valid.", "error")
            return redirect(url_for('display_game_output'))

        # The following 'buy_from_npc' block seems like a placeholder or an alternative action path.
        # For the current task, we are focusing on actions going through perform_hourly_action.
        # If 'buy_from_npc' is meant to be a standard action processed by perform_hourly_action,
        # it might not need this special handling here. If it's different, its flash messages
        # would need separate consideration. For now, assuming it's not the primary focus for this refactor.
        #
        # Removed special handling for "buy_from_npc" here.
        # It will now be processed by g.game_manager.perform_hourly_action like other actions.
        # The details_dict (parsed from action_details_str) should contain npc_name, item_name, quantity.
        #
        # Existing actions are handled by perform_hourly_action using g.game_manager
        if g.player_char is None or g.player_char.name is None or g.player_char.is_dead: # Redundant due to earlier check, but safe
            flash("No active character or character is dead. Cannot perform action.", "error")
            return redirect(url_for('display_game_output'))
        else:
            action_result_data = g.game_manager.perform_hourly_action(action_name, details_dict)

            if isinstance(action_result_data, dict) and action_result_data.get('type') == 'event_pending':
                    event_details = action_result_data.get('event_data', {}) # Get the nested dict, default to empty dict
                    session['awaiting_event_choice'] = True
                    session['pending_event_data'] = {
                        'name': event_details.get('name'), # Access from event_details
                        'description': event_details.get('description'), # Access from event_details
                        'choices': event_details.get('choices') # Access from event_details
                    }
                    # Use event_details for flash and print as well
                    event_name_for_flash = event_details.get('name', 'An event') # Fallback name
                    flash(f"EVENT: {event_name_for_flash}! Check Journal or Game Log for details.", "info")
                    g.game_manager._print(f"EVENT: {event_name_for_flash} requires your attention!")
            else:
                session.pop('awaiting_event_choice', None)
                session.pop('pending_event_data', None)
                # Default success message for actions that don't trigger an event
                flash(f"Action '{action_name_display}' performed. Check Journal or Game Log for details.", "info")

        # ---- START SAVE LOGIC (using g.player_char and g.game_manager) ----
        if g.player_char and g.player_char.name and not g.player_char.is_dead:
            username = session.get('username')
            slot_index = session.get('selected_character_slot')
            if username and slot_index is not None:
                if username in user_characters and 0 <= slot_index < len(user_characters[username]):
                    current_town_name_to_save = g.game_manager.current_town.name if g.game_manager.current_town else "Unknown"
                    user_characters[username][slot_index] = g.player_char.to_dict(current_town_name=current_town_name_to_save)
                    save_user_characters() # Global save function is fine
                else:
                    g.game_manager._print(f"  Warning: Character slot data mismatch for user {username}, slot {slot_index}. Could not save character state after action.")
            else:
                 g.game_manager._print("  Warning: User session data missing. Could not save character state after action.")
        # ---- END SAVE LOGIC ----

        # After action, check for death (using g.player_char)
        if g.player_char.is_dead:
            username = session.get('username')
            slot_index = session.get('selected_character_slot')
            char_name_for_log = g.player_char.name if g.player_char and g.player_char.name else "Character"

            death_timestamp_str = None
            if g.game_manager and hasattr(g.game_manager, 'time') and hasattr(g.game_manager.time, 'get_time_string'):
                death_timestamp_str = g.game_manager.time.get_time_string()

            already_logged_this_death = False
            if g.game_manager and g.player_char and hasattr(g.player_char, 'journal') and g.player_char.journal:
                last_entry = g.player_char.journal[-1]
                if last_entry.action_type == "Death" and last_entry.summary.startswith(char_name_for_log):
                    already_logged_this_death = True

            if not already_logged_this_death and g.game_manager and hasattr(g.game_manager, 'add_journal_entry'):
                g.game_manager.add_journal_entry( # Uses g.game_manager which has g.player_char
                    action_type="Death",
                    summary=f"{char_name_for_log} has succumbed to their fate.",
                    outcome="Character data moved to graveyard.",
                    timestamp=death_timestamp_str
                )
                if username and slot_index is not None and user_characters.get(username) and 0 <= slot_index < len(user_characters[username]):
                    current_town_name_death_save = g.game_manager.current_town.name if g.game_manager.current_town else "Unknown"
                    user_characters[username][slot_index] = g.player_char.to_dict(current_town_name=current_town_name_death_save)
                    save_user_characters()

            if username and slot_index is not None:
                if username in user_characters and 0 <= slot_index < len(user_characters[username]):
                    dead_char_data = user_characters[username].pop(slot_index)
                    dead_char_data['is_dead'] = True
                    graveyard.setdefault(username, []).append(dead_char_data)
                    save_user_characters()
                    save_graveyard()
                    flash(f"{dead_char_data.get('name', 'The character')} has died and been moved to the graveyard. Their slot is now free.", "error")
                    session.pop('selected_character_slot', None)
                else:
                    flash("Error processing character death: Character slot data mismatch.", "critical_error")
                    session.pop('selected_character_slot', None)
            else:
                flash("Error processing character death: User session data missing.", "critical_error")
                session.pop('selected_character_slot', None)
            return redirect(url_for('display_game_output'))

    except Exception as e:
        # Ensure g.game_manager is used for printing the error
        error_gm = getattr(g, 'game_manager', None)
        if error_gm:
            error_gm._print(f"An error occurred while performing action '{action_name_display}': {e}")
            import traceback
            error_gm._print(f"Traceback: {traceback.format_exc()}")
        else: # Fallback if g.game_manager itself is missing
            print(f"CRITICAL ERROR in /action, g.game_manager not found: {e}")
            print(f"Traceback: {traceback.format_exc()}")
        flash("An unexpected error occurred. Check the game log for more details.", "error")

    session['action_result'] = g.output_stream.getvalue() # Use g.output_stream
    return redirect(url_for('display_game_output'))

@app.route('/submit_event_choice', methods=['POST'])
def submit_event_choice_route():
    from flask import g # Access g for current request context
    # player_char and game_manager are now on g.

    if 'username' not in session or not session.get('awaiting_event_choice'):
        flash("Invalid session or no event choice pending.", "error")
        return redirect(url_for('display_game_output'))

    event_name_from_form = request.form.get('event_name')
    choice_index_str = request.form.get('choice_index')

    g.output_stream.truncate(0) # Use g.output_stream
    g.output_stream.seek(0)   # Use g.output_stream

    stored_event_data = session.get('pending_event_data') # Session data is fine

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
    # The execute_skill_choice method will print to g.output_stream and log to journal
    # It uses g.game_manager.character which is g.player_char
    execution_outcome = g.game_manager.event_manager.execute_skill_choice(selected_event_obj, choice_index)

    if isinstance(execution_outcome, dict) and 'roll_data' in execution_outcome and \
       isinstance(execution_outcome['roll_data'], dict) and 'formatted_string' in execution_outcome['roll_data']:
        session['last_skill_roll_display_str'] = execution_outcome['roll_data']['formatted_string']
    else:
        session.pop('last_skill_roll_display_str', None)


    # Clear event state from session
    session.pop('awaiting_event_choice', None)
    session.pop('pending_event_data', None)

    # Save character state after event resolution (using g.player_char, g.game_manager)
    if g.player_char and g.player_char.name and not g.player_char.is_dead:
        username = session.get('username')
        slot_idx = session.get('selected_character_slot')
        if username and slot_idx is not None and username in user_characters and 0 <= slot_idx < len(user_characters[username]):
            current_town_name_event_save = g.game_manager.current_town.name if g.game_manager.current_town else "Unknown"
            user_characters[username][slot_idx] = g.player_char.to_dict(current_town_name=current_town_name_event_save)
            save_user_characters()
        else:
            g.game_manager._print("  Warning: Could not save character state after event due to session/slot mismatch.")

    # Check for death after event resolution (using g.player_char)
    if g.player_char and g.player_char.is_dead: # Death check using g.player_char
        username = session.get('username')
        slot_idx = session.get('selected_character_slot')
        if username and slot_idx is not None and user_characters.get(username) and 0 <= slot_idx < len(user_characters[username]):
            dead_char_data = user_characters[username].pop(slot_idx)
            dead_char_data['is_dead'] = True
            graveyard.setdefault(username, []).append(dead_char_data)
            save_user_characters()
            save_graveyard()
            flash(f"{dead_char_data.get('name', 'The character')} has died (due to event) and been moved to the graveyard.", "error")
            session.pop('selected_character_slot', None)
            return redirect(url_for('display_game_output'))

    session['action_result'] = g.output_stream.getvalue() # Use g.output_stream
    return redirect(url_for('display_game_output'))

if __name__ == '__main__':
    # Note: game_manager_instance, player_char, and output_stream are no longer global module variables.
    # They are managed by before_request_setup on a per-request basis.
    app.run(debug=True, host='0.0.0.0', port=5001)
