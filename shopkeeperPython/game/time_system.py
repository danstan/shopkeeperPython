class GameTime:
    """
    Manages game time including hour and day.
    """
    def __init__(self, start_hour: int = 7, start_day: int = 1):
        """
        Initializes the game time.

        Args:
            start_hour (int): The hour the game starts at (0-23).
            start_day (int): The day the game starts on (1+).
        """
        self.current_hour = max(0, min(23, start_hour))
        self.current_day = max(1, start_day)
        # Suppress print during normal init, only print if explicitly tested or verbose mode
        # print(f"GameTime initialized. Starting at Day {self.current_day}, {self.current_hour:02d}:00.")

    def advance_hour(self, hours: int = 1) -> tuple[int, int]:
        """
        Advances the game time by a specified number of hours.

        Args:
            hours (int): The number of hours to advance. Must be positive.

        Returns:
            tuple[int, int]: A tuple containing (days_passed, new_current_hour).
        """
        if hours < 0:
            # print("Cannot advance time by a negative number of hours.") # Less verbose
            return 0, self.current_hour

        if hours == 0:
            return 0, self.current_hour

        days_passed = 0
        self.current_hour += hours

        while self.current_hour >= 24:
            self.current_hour -= 24
            self.current_day += 1
            days_passed += 1
            print(f"A new day has begun! It is now Day {self.current_day}.")

        return days_passed, self.current_hour

    def get_time_string(self) -> str:
        """
        Returns a formatted string representing the current game time.
        """
        return f"Day {self.current_day}, {self.current_hour:02d}:00"

    def is_night(self) -> bool:
        """
        Checks if it is currently night time.
        Night is defined as hours between 22:00 and 05:00 (inclusive of 22, exclusive of 6).
        """
        return self.current_hour >= 22 or self.current_hour < 6

    def to_dict(self) -> dict:
        """Converts the GameTime object to a dictionary for JSON serialization."""
        return {
            "current_hour": self.current_hour,
            "current_day": self.current_day,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'GameTime':
        """Creates a GameTime instance from a dictionary."""
        return cls(
            start_hour=data.get("current_hour", 7), # Default to 7 if not found
            start_day=data.get("current_day", 1)    # Default to 1 if not found
        )

if __name__ == "__main__":
    print("--- GameTime Test ---")
    time = GameTime(start_hour=6, start_day=1)
    print(f"Initial: {time.get_time_string()} | Is Night: {time.is_night()}")

    time.advance_hour(15)
    print(f"Adv 15h: {time.get_time_string()} | Is Night: {time.is_night()}")

    time.advance_hour(1)
    print(f"Adv 1h: {time.get_time_string()} | Is Night: {time.is_night()}")

    days, hour = time.advance_hour(8)
    print(f"Adv 8h: Days passed: {days}, New hour: {hour} | {time.get_time_string()} | Is Night: {time.is_night()}")

    # Test serialization and deserialization
    print("\n--- Serialization Test ---")
    time_data = time.to_dict()
    print(f"Serialized: {time_data}")
    assert time_data["current_hour"] == time.current_hour
    assert time_data["current_day"] == time.current_day

    loaded_time = GameTime.from_dict(time_data)
    print(f"Deserialized: {loaded_time.get_time_string()} | Is Night: {loaded_time.is_night()}")
    assert loaded_time.current_hour == time.current_hour
    assert loaded_time.current_day == time.current_day

    # Test with default values from_dict
    empty_data = {}
    default_loaded_time = GameTime.from_dict(empty_data)
    print(f"Deserialized from empty: {default_loaded_time.get_time_string()}")
    assert default_loaded_time.current_hour == 7
    assert default_loaded_time.current_day == 1

    print("\n--- GameTime Test Complete ---")
