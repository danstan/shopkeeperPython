# Shopkeeper Python Project

This project is a Python-based implementation of a whimsical, high-fantasy, turn-based, multiplayer shopkeeper RPG.

## Key Features

*   **User Accounts:** Register and log in with a unique username and password.
*   **Character Creation:** Create characters with rolled stats and one re-roll opportunity.
*   **Multiple Character Slots:** Manage up to two distinct active characters per account.
*   **Persistent Data:** User accounts, active characters, and graveyard data are saved in JSON files.
*   **Perma-death & Graveyard:** Deceased characters are moved to a viewable Graveyard. This frees up their original character slot, allowing for a new active character to be created (up to the account limit).
*   **Web-Based UI:** Interact with the game through a Flask-powered web interface.

## Running the Game

### Command-Line Interface (CLI)

The game can be run by executing the command `python main.py` from the root directory of the project.

### Web Interface

To run the web interface:

1. Navigate to the `shopkeeperPython` directory.
2. Install dependencies: `pip install -r requirements.txt`
3. Run the game: `python app.py` or `flask run`
4. Access the web interface at `http://localhost:5001`.
5. On your first visit, you will need to register a user account and then create a character through the web UI to start playing.
