import unittest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from .base_ui_test import BaseUITest # Assuming base_ui_test is in the same directory

class TestMainInterfaceTabs(BaseUITest):
    def test_action_tab_visibility_and_content(self):
        # Wait for the main game interface to load, e.g., by waiting for the Actions tab button
        actions_tab_button = self.wait_for_element((By.ID, "actions-tab-button"))
        self.assertTrue(actions_tab_button.is_displayed(), "Actions tab button is not displayed")

        # Click the 'Actions' tab button
        actions_tab_button.click()

        # Wait for the 'Actions' panel content to become visible
        actions_panel_content = self.wait_for_element((By.ID, "actions-panel-content"))
        self.assertTrue(actions_panel_content.is_displayed(), "Actions panel content is not displayed after clicking tab.")

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

        # Wait for the 'Log' panel content to become visible
        log_panel_content = self.wait_for_element((By.ID, "log-panel-content")) # or By.ID, "journal-entries-list"
        self.assertTrue(log_panel_content.is_displayed(), "Log panel content is not displayed after clicking tab.")

        # Assert that the 'Actions' panel content is not displayed
        actions_panel_content = self.driver.find_element(By.ID, "actions-panel-content") # Should exist but not be visible
        self.assertFalse(actions_panel_content.is_displayed(), "Actions panel content should not be displayed when Log tab is active.")

        # Assert that the 'Log' tab button has an 'active' class
        self.assertIn('active-tab-button', log_tab_button.get_attribute('class'), "Log tab button does not have 'active-tab-button' class.")

    def test_menu_button_opens_popup(self):
        # Wait for the main game interface to load, e.g., by waiting for the Menu button
        menu_button = self.wait_for_element((By.ID, "menu-button"))
        self.assertTrue(menu_button.is_displayed(), "Menu button is not displayed")

        # Click the 'Menu' button
        menu_button.click()

        # Wait for the menu popup to become visible
        settings_popup = self.wait_for_element((By.ID, "settings-popup"))
        self.assertTrue(settings_popup.is_displayed(), "Menu popup (settings-popup) is not displayed after clicking menu button.")

        # Verify presence of expected menu items
        settings_button = self.driver.find_element(By.ID, "settings-button")
        logout_button = self.driver.find_element(By.ID, "logout-button")
        save_game_button = self.driver.find_element(By.ID, "save-game-button")

        self.assertTrue(settings_button.is_displayed(), "Settings button within popup is not displayed.")
        self.assertTrue(logout_button.is_displayed(), "Logout button within popup is not displayed.")
        self.assertTrue(save_game_button.is_displayed(), "Save Game button within popup is not displayed.")

    def test_menu_popup_closes_correctly(self):
        # First, open the menu popup
        menu_button = self.wait_for_element((By.ID, "menu-button"))
        menu_button.click()
        settings_popup = self.wait_for_element((By.ID, "settings-popup"))
        self.assertTrue(settings_popup.is_displayed(), "Menu popup did not open as precondition for close test.")

        # Simulate clicking outside the popup to close it
        # Using 'player-stats-display' as an element outside the popup
        outside_element = self.wait_for_element((By.ID, "player-stats-display"))
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
