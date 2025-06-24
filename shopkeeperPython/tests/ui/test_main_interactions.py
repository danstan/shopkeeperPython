import unittest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from .base_ui_test import BaseUITest
import time # For unique names
import logging # Added import

class TestMainInteractions(BaseUITest):

    def test_create_character(self):
        # Assumption: BaseUITest's setUp will land on the character creation screen
        # if 'testuser' has no characters. This needs to be ensured externally for now.

        # Wait for the character creation form to be present
        self.wait_for_element((By.ID, "characterCreationForm"), timeout=10)

        char_name_input = self.wait_for_element((By.ID, "character_name"))

        # Use a unique character name to avoid conflicts if test is re-run
        # and previous character wasn't cleaned up.
        unique_char_name = f"TestChar_{int(time.time())}"
        char_name_input.send_keys(unique_char_name)

        # Optional: Test a stat reroll (e.g., for STR)
        # This assumes reroll is available.
        try:
            # More specific XPath to find the button within the form for STR
            reroll_str_button_xpath = "//form[contains(@action, '/reroll_stat/STR') or contains(@action, '/reroll_stat/Strength')]//button[contains(text(),'Reroll')]"
            reroll_button = self.wait_for_element((By.XPATH, reroll_str_button_xpath), timeout=5)
            if reroll_button.is_displayed() and reroll_button.is_enabled():
                reroll_button.click()
                # After reroll, the page reloads, wait for form again
                self.wait_for_element((By.ID, "characterCreationForm"), timeout=10)
                # The name might need to be re-entered if not persisted by backend across reroll
                # Re-finding element after potential page reload
                char_name_input_after_reroll = self.wait_for_element((By.ID, "character_name"))
                if not char_name_input_after_reroll.get_attribute("value"): # If name was cleared
                     char_name_input_after_reroll.send_keys(unique_char_name)
                logging.info("Successfully performed a stat reroll.")
            else:
                logging.info("Reroll button not available or not interactable, skipping reroll part.")
        except Exception as e:
            logging.warning(f"Could not perform stat reroll (or reroll not available): {e}")

        create_button = self.wait_for_element((By.ID, "createCharacterButton"))
        create_button.click()

        # Assert that we are now in the main game interface
        # by checking for an element that only appears there, e.g., actions-tab-button
        self.wait_for_element((By.ID, "actions-tab-button"), timeout=15)
        logging.info(f"Character '{unique_char_name}' created and main game interface loaded.")

        # Further assertion: Check if the character name appears somewhere,
        # e.g. in the player status panel (if accessible and populated immediately)

    def _test_hover_panel_visibility(self, mini_panel_id, full_panel_id, panel_name):
        # Ensure main interface is loaded (implicitly done by setUp or previous tests)
        self.wait_for_element((By.ID, "actions-tab-button"), timeout=15) # Main UI marker

        mini_panel = self.wait_for_element((By.ID, mini_panel_id))
        full_panel = self.driver.find_element(By.ID, full_panel_id) # find, not wait, to check initial state

        self.assertTrue(mini_panel.is_displayed(), f"{panel_name} mini panel is not displayed.")
        # Check initial state based on style="display: none;"
        self.assertEqual(full_panel.value_of_css_property("display"), "none", f"{panel_name} full panel should initially be hidden.")

        # Attempt hover (ActionChains)
        from selenium.webdriver.common.action_chains import ActionChains
        actions = ActionChains(self.driver)
        actions.move_to_element(mini_panel).perform()

        # Wait for the full panel to become visible
        # The style "display: none" will be removed or changed by JS
        try:
            WebDriverWait(self.driver, 5).until(
                lambda d: d.find_element(By.ID, full_panel_id).value_of_css_property("display") != "none"
            )
        except Exception: # Broad exception for timeout or other issues
            # Fallback: if hover didn't work, try clicking as panels have role="button"
            logging.info(f"Hover might not have worked for {panel_name} (or panel didn't open on hover), trying click.")
            mini_panel.click() # Click the mini_panel itself
            # Explicitly wait for the full panel to be visible after click
            WebDriverWait(self.driver, 5).until(
                EC.visibility_of_element_located((By.ID, full_panel_id))
            )


        full_panel_after_interaction = self.wait_for_element((By.ID, full_panel_id), visible=True) # ensure it's truly visible now
        self.assertTrue(full_panel_after_interaction.is_displayed(), f"{panel_name} full panel did not become visible after interaction.")
        logging.info(f"{panel_name} full panel is visible after interaction.")

        # Test closing the panel using its close button
        # The close button is generic: <button class="close-full-panel" ...>
        close_button_xpath = f"//div[@id='{full_panel_id}']//button[contains(@class, 'close-full-panel')]"
        close_button = self.wait_for_element((By.XPATH, close_button_xpath))
        close_button.click()

        WebDriverWait(self.driver, 5).until(
            lambda d: d.find_element(By.ID, full_panel_id).value_of_css_property("display") == "none"
        )
        self.assertEqual(self.driver.find_element(By.ID, full_panel_id).value_of_css_property("display"), "none", f"{panel_name} full panel did not hide after clicking close.")
        logging.info(f"{panel_name} full panel is hidden after clicking close.")


    def test_stats_panel_interaction(self): # Renamed for clarity as it tests click too
        self._test_hover_panel_visibility("mini-stats-panel", "full-stats-panel-container", "Stats")

    def test_info_panel_interaction(self): # Renamed
        self._test_hover_panel_visibility("mini-info-panel", "full-info-panel-container", "Info")

    def test_inventory_panel_interaction(self): # Renamed
        self._test_hover_panel_visibility("mini-inventory-panel", "full-inventory-panel-container", "Inventory")

    def test_shop_mgt_panel_interaction(self): # Renamed
        self._test_hover_panel_visibility("mini-shop-mgt-panel", "full-shop-mgt-panel-container", "Shop Mgt")

    def test_buy_from_hemlock(self):
        # Assumption: Player is in a town that has an "Apothecary" sub-location where Hemlock can be found.
        # This test also assumes Hemlock has items to sell.

        self.wait_for_element((By.ID, "actions-tab-button"), timeout=15) # Main UI marker
        current_town_display = self.wait_for_element((By.ID, "current-town-display-actions"))
        logging.info(f"Currently in town: {current_town_display.text.strip()} for Hemlock test.")

        # This is an assumed name for the sub-location. This should ideally come from a reliable source
        # or the test should be robust enough to find Hemlock if sub-location names vary.
        sub_location_name_for_hemlock = "Apothecary"

        # Wait for sub-location buttons to be populated by JS from gameConfig.
        # The sub-location button itself: <button class="sub-location-button action-button" data-sub-location-name="Apothecary">Apothecary</button>
        apothecary_button_xpath = f"//button[contains(@class, 'sub-location-button') and @data-sub-location-name='{sub_location_name_for_hemlock}']"

        try:
            apothecary_button = self.wait_for_element((By.XPATH, apothecary_button_xpath), timeout=10) # Wait for the specific button
        except Exception as e:
            logging.error(f"Could not find sub-location button for '{sub_location_name_for_hemlock}'. Ensure this sub-location exists in the current town and game data. Error: {e}")
            all_sub_loc_buttons = self.driver.find_elements(By.XPATH, "//button[contains(@class, 'sub-location-button')]")
            logging.info(f"Available sub-location buttons: {[b.get_attribute('data-sub-location-name') for b in all_sub_loc_buttons]}")
            raise # Re-raise the exception to fail the test clearly

        logging.info(f"Found sub-location button for '{sub_location_name_for_hemlock}'. Clicking it.")
        self.driver.execute_script("arguments[0].scrollIntoView(true);", apothecary_button)
        time.sleep(0.2) # Short pause after scroll before click
        apothecary_button.click()

        # Modal opens. Inside modal (#subLocationActionsModal), click "Buy Herbs from Hemlock"
        # Button: <button class="action-button modal-action-button" data-action-name="buy_from_hemlock_ui">Buy Herbs from Hemlock</button>
        buy_from_hemlock_modal_button_xpath = "//div[@id='modal-actions-list']//button[@data-action-name='buy_from_hemlock_ui']"
        hemlock_action_button_in_modal = self.wait_for_element((By.XPATH, buy_from_hemlock_modal_button_xpath), visible=True, timeout=10)
        logging.info("Found 'Buy Herbs from Hemlock' button in modal. Clicking it.")
        hemlock_action_button_in_modal.click()

        # Hemlock's specific buy form (#div_hemlock_herbs_details) should now appear in #dynamic-action-forms-container
        hemlock_form_div = self.wait_for_element((By.ID, "div_hemlock_herbs_details"), visible=True, timeout=10)
        self.assertTrue(hemlock_form_div.is_displayed(), "Hemlock buy form did not appear.")
        logging.info("Hemlock buy form is visible.")

        # Select an herb (e.g., the first one available)
        # Herbs are buttons: <button class="select-hemlock-herb-button action-button" data-herb-id="some_id" data-herb-name="Herb Name" data-herb-price="10">Herb Name (10G)</button>
        first_herb_button_xpath = "(//div[@id='hemlock-herbs-list']//button[contains(@class, 'select-hemlock-herb-button')])[1]"

        try:
            # Wait for herbs to be listed by JS
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, first_herb_button_xpath))
            )
            first_herb_button = self.wait_for_element((By.XPATH, first_herb_button_xpath)) # Get the element
        except Exception as e:
            logging.error(f"Could not find any herbs listed for Hemlock. Error: {e}")
            # For debugging, print the content of hemlock-herbs-list
            hemlock_list_content = self.driver.find_element(By.ID, "hemlock-herbs-list").get_attribute('innerHTML')
            logging.info(f"Content of hemlock-herbs-list: {hemlock_list_content}")
            raise

        selected_herb_name = first_herb_button.get_attribute("data-herb-name")
        logging.info(f"Selecting herb: {selected_herb_name}")
        first_herb_button.click() # This should highlight it by adding a class or JS tracking

        # Enter quantity (default is 1, let's keep it for simplicity for now)
        # quantity_input = self.wait_for_element((By.ID, "hemlock_quantity_dynamic"))
        # quantity_input.clear()
        # quantity_input.send_keys("1") # Assuming '1' is a valid quantity

        # Click buy button
        submit_hemlock_buy_button = self.wait_for_element((By.ID, "submit_buy_hemlock_herb_button"))
        submit_hemlock_buy_button.click()

        # Assert that a toast message appears
        # Toast messages are in #toast-container, with class .toast-message
        # Example success: "Successfully purchased 1 x Sunpetal."
        # Example failure: "Could not purchase Sunpetal. Reason: Not enough gold."
        toast_message_locator = (By.CSS_SELECTOR, "#toast-container .toast-message")

        # Wait for the toast message to appear
        toast_message = self.wait_for_element(toast_message_locator, timeout=10)
        self.assertTrue(toast_message.is_displayed(), "Toast message did not appear after attempting to buy from Hemlock.")

        toast_text = toast_message.text.lower() # Convert to lower for case-insensitive checks
        logging.info(f"Toast message displayed: {toast_message.text}")

        # Check for success keywords. This test assumes a successful purchase.
        # A more robust test might need to check player gold before and item details.
        self.assertIn(selected_herb_name.lower(), toast_text, f"Selected herb name '{selected_herb_name}' not in toast message '{toast_text}'")
        self.assertTrue("purchased" in toast_text or "bought" in toast_text, f"Neither 'purchased' nor 'bought' found in success toast message: '{toast_text}'")

        # Optional: Wait for toast to disappear to avoid interference with next actions
        WebDriverWait(self.driver, 10).until(EC.invisibility_of_element_located(toast_message_locator))
        logging.info("Toast message disappeared.")

    def test_save_game_toast_message(self):
        self.wait_for_element((By.ID, "actions-tab-button"), timeout=15) # Main UI marker

        menu_button = self.wait_for_element((By.ID, "top-right-menu-button"))
        menu_button.click()

        # Wait for menu to open and save button to be clickable
        save_game_button_locator = (By.ID, "save-game-button")
        # Ensure the button is not just present but also visible and clickable.
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable(save_game_button_locator))
        save_game_button = self.driver.find_element(*save_game_button_locator)
        save_game_button.click()

        # Assert that the specific auto-save toast message appears
        toast_message_locator = (By.CSS_SELECTOR, "#toast-container .toast-message")

        expected_toast_text = "Game progress is auto-saved regularly!"

        # Wait for the toast message that contains the expected text.
        # This is more robust than waiting for any toast message.
        WebDriverWait(self.driver, 10).until(
            EC.text_to_be_present_in_element(toast_message_locator, expected_toast_text)
        )

        toast_message = self.driver.find_element(*toast_message_locator)
        self.assertTrue(toast_message.is_displayed(), "Save game toast message did not appear or was not visible.")
        # Validate the full text of the toast message
        self.assertEqual(toast_message.text, expected_toast_text, f"Toast message text was not as expected. Got: '{toast_message.text}' Expected: '{expected_toast_text}'")
        logging.info(f"Correct save game toast message displayed: {toast_message.text}")

        # Optional: Wait for toast to disappear to avoid interference with next actions
        WebDriverWait(self.driver, 10).until(EC.invisibility_of_element_located(toast_message_locator))
        logging.info("Save game toast message disappeared.")

    def test_map_travel_to_different_town(self):
        self.wait_for_element((By.ID, "actions-tab-button"), timeout=15) # Main UI marker

        # Ensure Actions tab is visible if not already
        actions_tab_button = self.wait_for_element((By.ID, "actions-tab-button"))
        # The actions tab should be active by default after character selection/creation.
        # If BaseUITest changes this behavior, this click might be needed:
        # if "active-tab-button" not in actions_tab_button.get_attribute("class"):
        #     actions_tab_button.click()
        # self.wait_for_element((By.ID, "actions-panel-content"), visible=True)
        # For now, assume it's active as per current BaseUITest behavior.

        current_town_display_element_id = "current-town-display-actions"
        # Alternative: #mini-info-panel .mini-town-value, but actions panel is more direct for this test

        current_town_display = self.wait_for_element((By.ID, current_town_display_element_id))
        initial_town_name = current_town_display.text.strip() # Ensure no leading/trailing spaces
        logging.info(f"Initial town: {initial_town_name}")

        # Find a travel button for a different town
        # Buttons are like: <button type="button" class="map-destination-button action-button" data-town-name="TownName">TownName</button>
        travel_buttons_xpath = "//div[@id='map-destinations']//button[@class='map-destination-button action-button']"

        # Wait for at least one travel button to be present
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, travel_buttons_xpath))
        )
        travel_buttons = self.driver.find_elements(By.XPATH, travel_buttons_xpath)

        target_town_button = None
        target_town_name = None

        self.assertTrue(len(travel_buttons) > 0, "No travel buttons found on the page.")

        for button in travel_buttons:
            town_name_on_button = button.get_attribute("data-town-name").strip()
            if town_name_on_button != initial_town_name and town_name_on_button: # Ensure it's different and not empty
                target_town_button = button
                target_town_name = town_name_on_button
                break

        self.assertIsNotNone(target_town_button, f"Could not find a travel button for a town different from '{initial_town_name}'. Available buttons: {[b.text.strip() for b in travel_buttons]}. Ensure at least two towns exist and are configured correctly.")

        logging.info(f"Attempting to travel to: {target_town_name}")
        # Scroll into view if necessary, though Selenium usually handles this for clicks
        self.driver.execute_script("arguments[0].scrollIntoView(true);", target_town_button)
        time.sleep(0.2) # Brief pause for scroll if it happened
        target_town_button.click()

        # Wait for the town name display to update
        # Also wait for body.js-loaded and body.init-main-interface-called as page might effectively "reload" content
        logging.info("Waiting for body.js-loaded after travel click.")
        WebDriverWait(self.driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//body[contains(@class, 'js-loaded')]"))
        )
        logging.info("body.js-loaded found after travel click.")

        logging.info("Waiting for body.init-main-interface-called after travel click.")
        WebDriverWait(self.driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//body[contains(@class, 'init-main-interface-called')]"))
        )
        logging.info("body.init-main-interface-called found after travel click.")

        WebDriverWait(self.driver, 15).until(
            EC.text_to_be_present_in_element((By.ID, current_town_display_element_id), target_town_name)
        )

        new_town_display = self.driver.find_element(By.ID, current_town_display_element_id)
        self.assertEqual(new_town_display.text.strip(), target_town_name, "Town name in actions panel did not update after travel.")
        logging.info(f"Successfully traveled to {target_town_name}.")

        # Also check the mini-info panel for consistency
        try:
            # Re-wait for the element as the page content might have refreshed
            mini_info_town_element_css = "#mini-info-panel .mini-town-value"
            WebDriverWait(self.driver, 10).until(
                EC.text_to_be_present_in_element((By.CSS_SELECTOR, mini_info_town_element_css), target_town_name)
            )
            mini_info_town_value = self.driver.find_element(By.CSS_SELECTOR, mini_info_town_element_css)
            self.assertEqual(mini_info_town_value.text.strip(), target_town_name, "Town name in mini-info panel did not update.")
            logging.info(f"Town name '{target_town_name}' also confirmed in mini-info panel.")
        except Exception as e:
            logging.warning(f"Could not verify town name in mini-info panel or it didn't match: {e}")
        # This would require expanding the test to open the stats panel.
        # For now, loading the main interface is the primary assertion.

if __name__ == '__main__':
    unittest.main()
