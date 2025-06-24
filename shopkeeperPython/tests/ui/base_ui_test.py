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
        # self.driver.implicitly_wait(5) # Using explicit waits primarily
        logging.info("BaseUITest.setUp: Navigating to login page.")
        self.driver.get("http://localhost:5001/")

        # Basic check: Wait for the login username field to be present or page title
        try:
            logging.info("BaseUITest.setUp: Attempting to find login username field.")
            username_field = self.wait_for_element((By.ID, "login_username"), timeout=20) # Increased timeout for this basic check
            if username_field:
                logging.info("BaseUITest.setUp: Login username field found. Page seems to be loading.")
            else:
                logging.warning("BaseUITest.setUp: Login username field NOT found after wait.")

            # Also check page title
            expected_title = "Shopkeeper Game" # Assuming this is the title from render_template in app.py
            WebDriverWait(self.driver, 10).until(EC.title_is(expected_title))
            logging.info(f"BaseUITest.setUp: Page title is '{self.driver.title}'. Expected '{expected_title}'.")

        except TimeoutException:
            logging.error("BaseUITest.setUp: Timed out waiting for login username field or correct page title. Basic page load failed.")
            # Screenshot/source is saved by wait_for_element on its timeout
            raise # Re-raise the exception to fail the test setup clearly

        logging.info("BaseUITest.setUp (simplified): Basic page load check completed.")

        # NOTE: All further login and navigation logic is temporarily removed for this basic check.
        # If this simplified setUp passes, the issue is likely in the login or post-login navigation logic.

    def tearDown(self):
        # Ensure driver is available before trying to get logs or quit
        if hasattr(self, 'driver') and self.driver:
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
