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

Follow these steps to run the web UI:

1.  **Navigate to this Directory (`shopkeeperPython`):**
    Open your terminal or command prompt. Ensure you are in the `shopkeeperPython` directory (the one containing *this* README.md and `app.py`).
    If you are in the project root, type:
    ```bash
    cd shopkeeperPython
    ```

2.  **Create and Activate a Virtual Environment (Recommended)**:
    It's a best practice to use a virtual environment. If you created one in the project root, ensure it's active. If creating one here:
    ```bash
    # Create a virtual environment (e.g., named .venv)
    python -m venv .venv
    # Activate it
    # On Windows:
    # .venv\Scriptsctivate
    # On macOS/Linux:
    # source .venv/bin/activate
    ```

3.  **Install Dependencies**:
    With your virtual environment active, install the required Python packages from this directory:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the Flask Application (Method 1: Directly):**
    Since `app.py` now uses relative imports, you can run it directly from this directory:
    ```bash
    python app.py
    ```

5.  **Run the Flask Application (Method 2: As a module from parent directory):**
    The standard Python way for packaged applications is to run them as a module from the parent (project root) directory. To do this:
    ```bash
    cd ..
    python -m shopkeeperPython.app
    ```
    (Then, if you want to return to this directory: `cd shopkeeperPython`)


6.  **Open in Browser**:
    Open your web browser and navigate to the address shown in your terminal (e.g., `http://127.0.0.1:5001/`).
