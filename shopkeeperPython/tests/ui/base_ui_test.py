import unittest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class BaseUITest(unittest.TestCase):
    def setUp(self):
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        self.driver = webdriver.Chrome(options=options)
        self.driver.implicitly_wait(10)
        self.driver.get("http://localhost:5000/")  # Assuming the app runs on port 5000

        # Login
        username_field = self.wait_for_element((By.ID, "username")) # Assuming username field has id "username"
        password_field = self.wait_for_element((By.ID, "password")) # Assuming password field has id "password"
        login_button = self.wait_for_element((By.XPATH, "//button[text()='Login']")) # Assuming login button has text "Login"

        username_field.send_keys("testuser") # Replace with actual test username
        password_field.send_keys("password") # Replace with actual test password
        login_button.click()

        # Wait for login to complete by checking for an element on the next page
        # This could be a character selection screen or main game page element
        self.wait_for_element((By.ID, "character-selection")) # Example: wait for character selection screen

        # Character selection (if applicable)
        # character_to_select = self.wait_for_element((By.XPATH, "//div[contains(text(), 'TestCharacter')]")) # Example
        # character_to_select.click()
        # self.wait_for_element((By.ID, "main-game-area")) # Example: wait for main game area

    def tearDown(self):
        self.driver.quit()

    def wait_for_element(self, locator, timeout=10):
        """Waits for an element to be present and returns it."""
        return WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located(locator)
        )
