# Shopkeeper Python

A Python-based implementation of a whimsical, high-fantasy, turn-based, multiplayer shopkeeper RPG.
This project aims to recreate and expand upon the concepts from the original C# Shopkeeper game, based on the provided game design document.

## Features (Planned)

*   Character Management (Stats, XP, Leveling)
*   Shopkeeping (Crafting, Selling, Specialization)
*   Economy & Itemization (Gold, Magical Items, Consumables)
*   Dynamic Event System
*   Rest Mechanics (Short/Long Rests, Exhaustion)
*   In-game Time System
*   Interactive World (Towns with unique properties)
*   Player Save States (JSON)

## Project Structure

*   `shopkeeperPython/game/`: Core game logic modules.
*   `shopkeeperPython/game/data/`: Game data files (e.g., item definitions, event templates).
*   `shopkeeperPython/tests/`: Unit tests.
*   `shopkeeperPython/docs/`: Project documentation.
*   `shopkeeperPython/main.py`: Main entry point for the game (will be created later).
*   `shopkeeperPython/app.py`: Flask web server for the playtesting UI.
*   `shopkeeperPython/requirements.txt`: Python dependencies for the project, including Flask.
*   `shopkeeperPython/static/`: Static files for the web UI (CSS, JS).
*   `shopkeeperPython/templates/`: HTML templates for the web UI.

## Web UI for Playtesting

This project includes a simple web-based user interface to allow for interactive playtesting and debugging of the game mechanics. The UI displays the current game log, player status, game state, and provides input fields to perform game actions.

### Running the Web UI

The recommended way to run the web UI is from the project's root directory (the directory *above* this one).

1.  **Navigate to the Project Root Directory:**
    Open your terminal or command prompt. If you are currently in the `shopkeeperPython` directory (where this README is), navigate up one level:
    ```bash
    cd ..
    ```
    You should now be in the project root directory (the one that contains the main `README.md` and the `shopkeeperPython` folder).

2.  **Create and Activate a Virtual Environment (Recommended, from project root)**:
    It's a best practice to use a virtual environment from the project root.
    ```bash
    # Create a virtual environment (e.g., named .venv)
    python -m venv .venv
    # Activate it
    # On Windows:
    # .venv\Scriptsctivate
    # On macOS/Linux:
    # source .venv/bin/activate
    ```

3.  **Install Dependencies (from project root)**:
    With your virtual environment active, install the required Python packages. The `requirements.txt` file is located within the `shopkeeperPython` directory.
    ```bash
    pip install -r shopkeeperPython/requirements.txt
    ```

4.  **Run the Flask Application (as a module from project root)**:
    Execute the application as a module:
    ```bash
    python -m shopkeeperPython.app
    ```

5.  **Open in Browser**:
    Open your web browser and navigate to the address shown in your terminal (e.g., `http://127.0.0.1:5001/`).
