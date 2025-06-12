from shopkeeperPython.game import GameManager, Character

def main():
    # Create a player character
    player = Character(name="Player")
    player.roll_stats() # Initialize player stats

    # Create a game manager
    game_manager = GameManager(player_character=player)

    # Basic game loop
    while True:
        print("\n--- Game Menu ---")
        # Assuming GameManager will have a way to get current time
        print(f"Current Time: {game_manager.time.get_time_string()}")
        print("Available Actions:")
        print("- rest_short")
        print("- talk_to_customer")
        print("- research_market")
        print("- craft")
        print("- quit")

        action = input("Enter your action: ").strip().lower()

        result_message = None # Store messages for the user
        action_details = {}

        if action == "rest_short":
            # Assuming default 1 hit die for a short rest from main menu
            action_details = {"dice_to_spend": 1}
            # perform_hourly_action will print its own results,
            # but we can add a general confirmation.
            game_manager.perform_hourly_action("rest_short", action_details)
            result_message = f"Attempted short rest. Check console for details. Current time: {game_manager.time.get_time_string()}"
        elif action == "talk_to_customer":
            game_manager.perform_hourly_action("talk_to_customer")
            result_message = f"Spent time talking to customers. Check console for details. Current time: {game_manager.time.get_time_string()}"
        elif action == "research_market":
            game_manager.perform_hourly_action("research_market")
            result_message = f"Spent time researching the market. Check console for details. Current time: {game_manager.time.get_time_string()}"
        elif action == "craft":
            item_name = input("Enter the item name to craft: ").strip()
            if item_name:
                action_details = {"item_name": item_name}
                game_manager.perform_hourly_action("craft", action_details)
                result_message = f"Attempted to craft {item_name}. Check console for details. Current time: {game_manager.time.get_time_string()}"
            else:
                result_message = "Error: Item name cannot be empty for crafting."
        elif action == "quit":
            print("Exiting game. Goodbye!")
            break
        else:
            result_message = "Error: Invalid action. Please choose from the available actions."

        if result_message: # Print the custom message from main.py
            print(f"\nGame Info:\n{result_message}")

if __name__ == "__main__":
    main()
