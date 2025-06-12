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
        print(f"GameTime initialized. Starting at Day {self.current_day}, {self.current_hour:02d}:00.")

    def advance_hour(self, hours: int = 1) -> tuple[int, int]:
        """
        Advances the game time by a specified number of hours.

        Args:
            hours (int): The number of hours to advance. Must be positive.

        Returns:
            tuple[int, int]: A tuple containing (days_passed, new_current_hour).
        """
        if hours < 0:
            print("Cannot advance time by a negative number of hours.")
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

        # print(f"Time advanced by {hours} hour(s). Current time: {self.get_time_string()}")
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

if __name__ == "__main__":
    print("--- GameTime Test ---")
    time = GameTime(start_hour=6, start_day=1)
    print(time.get_time_string()) # Day 1, 06:00
    print(f"Is it night? {time.is_night()}") # False

    time.advance_hour(15) # Advance to 21:00
    print(time.get_time_string()) # Day 1, 21:00
    print(f"Is it night? {time.is_night()}") # False (just before night)

    time.advance_hour(1) # Advance to 22:00
    print(time.get_time_string()) # Day 1, 22:00
    print(f"Is it night? {time.is_night()}") # True

    days, hour = time.advance_hour(8) # Advance to 06:00, Day 2
    print(f"Days passed: {days}, New hour: {hour}")
    print(time.get_time_string()) # Day 2, 06:00
    print(f"Is it night? {time.is_night()}") # False (just after night)

    time.advance_hour(20) # Advance to 02:00, Day 3
    print(time.get_time_string()) # Day 3, 02:00
    print(f"Is it night? {time.is_night()}") # True

    time = GameTime(start_hour=23)
    time.advance_hour(1)
    print(time.get_time_string()) # Day 2, 00:00

    time = GameTime(start_hour=5)
    print(f"Is it night? {time.is_night()}") # True
    time.advance_hour(1)
    print(f"Is it night? {time.is_night()}") # False


    time = GameTime(start_hour=0)
    print(f"Is it night? {time.is_night()}") # True

    time = GameTime(start_hour=23)
    days_passed, new_hour = time.advance_hour(24)
    print(f"Advanced by 24 hours. Days passed: {days_passed}, New hour: {new_hour}. Final time: {time.get_time_string()}") # Day 2, 23:00

    time = GameTime(start_hour=7)
    days_passed, new_hour = time.advance_hour(0) # Test 0 hours
    print(f"Advanced by 0 hours. Days passed: {days_passed}, New hour: {new_hour}. Final time: {time.get_time_string()}")

    days_passed, new_hour = time.advance_hour(-2) # Test negative hours
    print(f"Advanced by -2 hours. Days passed: {days_passed}, New hour: {new_hour}. Final time: {time.get_time_string()}")

    print("--- GameTime Test Complete ---")
