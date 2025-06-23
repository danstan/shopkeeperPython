import unittest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from .base_ui_test import BaseUITest # Assuming base_ui_test is in the same directory
import time # Added for sleep

class TestMainInterfaceTabs(BaseUITest):
    def test_action_tab_visibility_and_content(self):
        # Wait for the main game interface to load, e.g., by waiting for the Actions tab button
        actions_tab_button = self.wait_for_element((By.ID, "actions-tab-button"))
        self.assertTrue(actions_tab_button.is_displayed(), "Actions tab button is not displayed")

        # Click the 'Actions' tab button
        actions_tab_button.click()
        # setUp ensures actions-panel-content is initially visible.
        # Clicking the already active 'Actions' tab should keep it visible.
        actions_panel_content = self.wait_for_element((By.ID, "actions-panel-content"))
        self.assertTrue(actions_panel_content.is_displayed(), "Actions panel content is not displayed after clicking actions tab.")

        # Assert that the 'Log' panel content is not displayed
        log_panel_content = self.driver.find_element(By.ID, "log-panel-content") # Should exist but not be visible
        self.assertFalse(log_panel_content.is_displayed(), "Log panel content should not be displayed when Actions tab is active.")

        # Assert that the 'Actions' tab button has an 'active' class
        self.assertIn('active-tab-button', actions_tab_button.get_attribute('class'), "Actions tab button does not have 'active-tab-button' class.")

    def test_log_tab_visibility_and_content(self):
        # Wait for the main game interface to load, e.g., by waiting for the Log tab button
        log_tab_button = self.wait_for_element((By.ID, "log-tab-button"))
        self.assertTrue(log_tab_button.is_displayed(), "Log tab button is not displayed")

        # Click the 'Log' tab button
        log_tab_button.click()
        # The JS click handler should add 'panel-visible' and the panel should become visible.
        log_panel_content = self.wait_for_element((By.ID, "log-panel-content"))
        self.assertTrue(log_panel_content.is_displayed(), "Log panel content is not displayed after clicking log tab.")

        # Assert that the 'Actions' panel content is not displayed
        actions_panel_content = self.driver.find_element(By.ID, "actions-panel-content") # Should exist but not be visible
        self.assertFalse(actions_panel_content.is_displayed(), "Actions panel content should not be displayed when Log tab is active.")

        # Assert that the 'Log' tab button has an 'active' class
        self.assertIn('active-tab-button', log_tab_button.get_attribute('class'), "Log tab button does not have 'active-tab-button' class.")

    def test_menu_button_opens_popup(self):
        # Wait for the main game interface to load, e.g., by waiting for the Menu button
        menu_button = self.wait_for_element((By.ID, "top-right-menu-button")) # Corrected ID
        self.assertTrue(menu_button.is_displayed(), "Menu button is not displayed")

        # Click the 'Menu' button
        menu_button.click()
        time.sleep(0.1) # Short delay for JS to execute style change

        # Wait for the menu popup to become visible by waiting for an item within it
        settings_option_li = self.wait_for_element((By.ID, "settings-option"))
        self.assertTrue(settings_option_li.is_displayed(), "Settings option (settings-option) is not displayed after clicking menu button.")

        # Verify presence of expected menu items
        settings_popup = self.driver.find_element(By.ID, "settings-popup") # Get popup itself for further checks if needed
        self.assertTrue(settings_popup.is_displayed(), "Menu popup (settings-popup) is not displayed after clicking menu button.")
        settings_option_li = self.driver.find_element(By.ID, "settings-option") # Corrected ID
        logout_link = self.driver.find_element(By.ID, "logout-option") # Corrected ID
        save_game_button = self.driver.find_element(By.ID, "save-game-button")

        self.assertTrue(settings_option_li.is_displayed(), "Settings option within popup is not displayed.")
        self.assertTrue(logout_link.is_displayed(), "Logout link within popup is not displayed.")
        self.assertTrue(save_game_button.is_displayed(), "Save Game button within popup is not displayed.")

    def test_menu_popup_closes_correctly(self):
        # First, open the menu popup
        menu_button = self.wait_for_element((By.ID, "top-right-menu-button")) # Corrected ID
        menu_button.click()
        time.sleep(0.1) # Short delay for JS to execute style change
        # Wait for an item within the popup to ensure it's open
        self.wait_for_element((By.ID, "settings-option"))
        settings_popup = self.driver.find_element(By.ID, "settings-popup") # Get popup for visibility check
        self.assertTrue(settings_popup.is_displayed(), "Menu popup did not open as precondition for close test.")

        # Simulate clicking outside the popup to close it
        # Using 'map-container' as an element outside the popup
        outside_element = self.wait_for_element((By.ID, "map-container")) # Changed to a reliable outside element
        self.assertTrue(outside_element.is_displayed(), "Outside element for closing popup is not displayed.")
        outside_element.click()

        # Wait for the popup to become invisible
        WebDriverWait(self.driver, 10).until(
            EC.invisibility_of_element_located((By.ID, "settings-popup"))
        )

        # Assert that the menu popup is not displayed
        # Re-find element to check its state, direct reference might be stale
        settings_popup_after_close = self.driver.find_element(By.ID, "settings-popup")
        self.assertFalse(settings_popup_after_close.is_displayed(), "Menu popup (settings-popup) should not be displayed after clicking outside.")

if __name__ == '__main__':
    unittest.main()
