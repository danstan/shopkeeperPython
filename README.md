# Shopkeeper Python Project

This project is a Python-based implementation of a whimsical, high-fantasy, turn-based, multiplayer shopkeeper RPG.

## Key Features

*   **User Accounts:** Register and log in with a unique username and password.
*   **Character Creation:** Create characters with rolled stats and one re-roll opportunity.
*   **Multiple Character Slots:** Manage up to two distinct active characters per account.
*   **Persistent Data:** User accounts, active characters, and graveyard data are saved in JSON files.
*   **Perma-death & Graveyard:** Deceased characters are moved to a viewable Graveyard. This frees up their original character slot, allowing for a new active character to be created (up to the account limit).
*   **Login with Google (OAuth 2.0):** Optional login/registration using a Google account.
*   **Web-Based UI:** Interact with the game through a Flask-powered web interface.

## Running the Game

### Google OAuth Setup (Important for Developers/Admins)

For the "Login with Google" feature to work, you must configure Google OAuth 2.0 credentials:

1.  **Google Cloud Console:** Go to the [Google Cloud Console](https://console.cloud.google.com/).
2.  **Project:** Create a new project or select an existing one.
3.  **APIs & Services:**
    *   Navigate to "APIs & Services" > "Enabled APIs & services".
    *   Click "+ ENABLE APIS AND SERVICES".
    *   Search for "Google People API" and enable it. (This API is commonly used for fetching user profile information like name, email, and profile picture).
4.  **OAuth Consent Screen:**
    *   Navigate to "APIs & Services" > "OAuth consent screen".
    *   Configure the consent screen. For testing, "External" user type is usually fine. You'll need to provide an app name, user support email, and developer contact information.
    *   Add necessary scopes: `.../auth/userinfo.email`, `.../auth/userinfo.profile`, `openid`. These should already be requested by the application, but ensure they are permitted.
5.  **Credentials:**
    *   Navigate to "APIs & Services" > "Credentials".
    *   Click "+ CREATE CREDENTIALS" > "OAuth client ID".
    *   Select "Web application" as the application type.
    *   **Authorized JavaScript origins:** Add your application's origin (e.g., `http://localhost:5001`).
    *   **Authorized redirect URIs:** Add the redirect URI that Flask-Dance will use. For this application, it's typically `http://localhost:5001/login/google/authorized`.
    *   Click "Create". You will be shown your Client ID and Client Secret.
6.  **Set Environment Variables:**
    *   The application expects the Client ID and Client Secret to be set as environment variables.
    *   **Linux/macOS (bash/zsh):**
        ```bash
        export GOOGLE_OAUTH_CLIENT_ID="YOUR_CLIENT_ID_HERE"
        export GOOGLE_OAUTH_CLIENT_SECRET="YOUR_CLIENT_SECRET_HERE"
        ```
    *   **Windows (Command Prompt):**
        ```cmd
        set GOOGLE_OAUTH_CLIENT_ID="YOUR_CLIENT_ID_HERE"
        set GOOGLE_OAUTH_CLIENT_SECRET="YOUR_CLIENT_SECRET_HERE"
        ```
    *   **Windows (PowerShell):**
        ```powershell
        $env:GOOGLE_OAUTH_CLIENT_ID="YOUR_CLIENT_ID_HERE"
        $env:GOOGLE_OAUTH_CLIENT_SECRET="YOUR_CLIENT_SECRET_HERE"
        ```
    *   Replace `"YOUR_CLIENT_ID_HERE"` and `"YOUR_CLIENT_SECRET_HERE"` with the actual credentials you obtained from the Google Cloud Console.
    *   **Important:** You must set these environment variables in the terminal session where you run the Flask application. If they are not set, Google Login will be disabled (a warning will be printed at startup).

### Command-Line Interface (CLI)

The game can be run by executing the command `python main.py` from the root directory of the project.

### Web Interface

To run the web interface:

1.  **Navigate to the Project Root Directory:**
    Open your terminal and navigate to the root directory of this project (the one containing *this* README.md file).

2.  **Install Dependencies (from project root):**
    If you haven't already, install the required Python packages. It's recommended to use a virtual environment.
    ```bash
    pip install -r shopkeeperPython/requirements.txt
    ```
    **Note on Updates:** If you pull new changes, remember to reinstall dependencies as new ones might have been added.

3.  **Run the Game:**
    From the project root directory, run the application as a module:
    ```bash
    python -m shopkeeperPython.app
    ```

4.  **Access the Web Interface:**
    Open your web browser and navigate to `http://localhost:5001` (or the address shown in your terminal).

5.  **First Use:**
    On your first visit, you will need to register a user account and then create a character through the web UI to start playing.
