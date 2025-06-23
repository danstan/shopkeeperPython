import unittest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException # Ensure this is imported
import datetime # Ensure this is imported
import logging # Added import

# Configure logging to output to stdout
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class BaseUITest(unittest.TestCase):
    def setUp(self):
        logging.info("BaseUITest.setUp: Initializing WebDriver.")
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        # Optional: Enable browser logging
        options.set_capability('goog:loggingPrefs', {'browser': 'ALL'})

        self.driver = webdriver.Chrome(options=options)
        self.driver.implicitly_wait(5) # Reduced implicit wait, explicit waits are better
        logging.info("BaseUITest.setUp: Navigating to login page.")
        self.driver.get("http://localhost:5001/")

        # Login
        logging.info("BaseUITest.setUp: Attempting login.")
        username_field = self.wait_for_element((By.ID, "login_username"), timeout=15)
        password_field = self.wait_for_element((By.ID, "login_password"))
        login_button = self.wait_for_element((By.XPATH, "//button[text()='Login']"))

        username_field.send_keys("testuser")
        password_field.send_keys("password123")
        login_button.click()
        logging.info("BaseUITest.setUp: Login form submitted.")

        # Wait for login to complete.
        # After login, user might be on character selection or character creation.
        try:
            logging.info("BaseUITest.setUp: Checking for character selection page.")
            char_selection_heading = self.wait_for_element((By.XPATH, "//h2[text()='Select Character']"), timeout=7) # Shorter timeout
            if char_selection_heading:
                logging.info("BaseUITest.setUp: Character selection page found. Selecting first character.")
                first_select_link = self.wait_for_element((By.XPATH, "(//a[text()='Select'])[1]"), timeout=5)
                first_select_link.click()

                logging.info("BaseUITest.setUp: Character selected. Waiting for main game interface markers.")
                # Wait for an element that indicates the main game interface is loaded (e.g. actions tab)
                self.wait_for_element((By.ID, "actions-tab-button"), timeout=15)
                logging.info("BaseUITest.setUp: 'actions-tab-button' found after character selection.")

                logging.info("BaseUITest.setUp: Waiting for body.js-loaded. (after char select)")
                WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located((By.XPATH, "//body[contains(@class, 'js-loaded')]"))
                )
                logging.info("BaseUITest.setUp: body.js-loaded found. (after char select)")

                logging.info("BaseUITest.setUp: Waiting for body.init-main-interface-called. (after char select)")
                WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located((By.XPATH, "//body[contains(@class, 'init-main-interface-called')]"))
                )
                logging.info("BaseUITest.setUp: body.init-main-interface-called found. initializeMainInterfaceInteractions likely called.")

        except TimeoutException:
            logging.info("BaseUITest.setUp: Character selection not found or timed out, assuming character creation page.")
            # Check if we are on the character creation form
            self.wait_for_element((By.ID, "characterCreationForm"), timeout=7)
            logging.info("BaseUITest.setUp: Character creation form confirmed by presence of characterCreationForm.")

            logging.info("BaseUITest.setUp: Waiting for body.js-loaded on char creation page.")
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//body[contains(@class, 'js-loaded')]"))
            )
            logging.info("BaseUITest.setUp: body.js-loaded found on char creation page.")

            logging.info("BaseUITest.setUp: Waiting for body.init-main-interface-called on char creation page.")
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//body[contains(@class, 'init-main-interface-called')]"))
            )
            logging.info("BaseUITest.setUp: body.init-main-interface-called found on char creation page. initializeMainInterfaceInteractions likely called.")

        logging.info("BaseUITest.setUp: Completed.")

    def tearDown(self):
        test_method_name = self.id().split('.')[-1] # Get the name of the test method
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        browser_log_filename = f"browser_log_{test_method_name}_{timestamp}.txt" # Removed /app/

        logging.info(f"BaseUITest.tearDown: Capturing browser logs for {test_method_name} to {browser_log_filename}.")
        try:
            log_entries = self.driver.get_log('browser')
            logging.info(f"Browser logs retrieved. Type: {type(log_entries)}, Value: {log_entries}") # DIAGNOSTIC

            if log_entries is not None:
                logging.info(f"Attempting to open and write to {browser_log_filename}") # DIAGNOSTIC
                with open(browser_log_filename, "w", encoding="utf-8") as f:
                    if not log_entries: # Handles empty list case
                        f.write("No browser logs captured.\n")
                        logging.info("[Browser log] No browser logs captured.")
                    for entry in log_entries:
                        f.write(f"{entry['level']}: {entry['message']}\n")
                        logging.info(f"[Browser log] {entry['level']}: {entry['message']}") # Also print to main log
                logging.info(f"Successfully saved browser logs to {browser_log_filename}")
            else:
                logging.warning(f"Browser logs were None. File {browser_log_filename} will not be created.")

        except Exception as e:
            logging.error(f"Could not retrieve or save browser logs: {e}")

        logging.info("BaseUITest.tearDown: Quitting WebDriver.")
        self.driver.quit()

    def wait_for_element(self, locator, timeout=10, visible=True): # Added visible flag
        """Waits for an element to be present and optionally visible, then returns it."""
        logging.debug(f"Waiting for element {locator} (visible={visible}, timeout={timeout})")
        try:
            if visible:
                element = WebDriverWait(self.driver, timeout).until(
                    EC.visibility_of_element_located(locator)
                )
            else: # Wait for presence, not necessarily visibility
                element = WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located(locator)
                )
            logging.debug(f"Element {locator} found.")
            return element
        except TimeoutException as e:
            logging.warning(f"TimeoutException waiting for element {locator} (visible={visible}).")
            # Save debug info before re-raising
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            screenshot_filename = f"debug_screenshot_{timestamp}.png" # Removed /app/
            pagesource_filename = f"debug_pagesource_{timestamp}.html" # Removed /app/

            try:
                self.driver.save_screenshot(screenshot_filename)
                logging.info(f"Saved screenshot to {screenshot_filename}")
            except Exception as se:
                logging.error(f"Failed to save screenshot: {se}")

            try:
                with open(pagesource_filename, "w", encoding="utf-8") as f:
                    f.write(self.driver.page_source)
                logging.info(f"Saved page source to {pagesource_filename}")
            except Exception as pe:
                logging.error(f"Failed to save page source: {pe}")

            raise e
