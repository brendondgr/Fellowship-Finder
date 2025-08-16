import json
import time
import random
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.firefox import GeckoDriverManager
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, NoSuchElementException


class ProfellowBot:
    def __init__(self):
        # Load login credentials from a JSON file
        with open("configs/login.json", "r") as f:
            self.login_data = json.load(f)

        # Load categories and items to be selected from a JSON file
        with open("configs/categories.json", "r") as f:
            self.categories_data = json.load(f)

        self.LOGIN_URL = "https://www.profellow.com/log-in/"

        # Initialize the Firefox WebDriver
        self.driver = webdriver.Firefox(service=Service(GeckoDriverManager().install()))

    def _login(self):
        self.driver.get(self.LOGIN_URL)
        print("Navigated to login page.")

        # Wait for the email input to be visible and type the email
        email_input = WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located((By.ID, "wpforms-106652-field_1"))
        )
        for char in self.login_data["email"]:
            email_input.send_keys(char)
            time.sleep(random.uniform(0.01, 0.05))

        # Find the password input and type the password
        password_input = self.driver.find_element(By.ID, "wpforms-106652-field_2")
        for char in self.login_data["password"]:
            password_input.send_keys(char)
            time.sleep(random.uniform(0.01, 0.05))

        # Add a brief delay before clicking the login button
        time.sleep(random.uniform(0.4, 1.3))

        # Find and click the login button
        login_button = self.driver.find_element(By.ID, "wpforms-submit-106652")
        login_button.click()

        # Wait for a successful login by checking for a URL change
        WebDriverWait(self.driver, 10).until(
            EC.url_contains("fellowship")
        )
        print("Login successful!")
        time.sleep(random.uniform(2, 4))

    def _click_filter_button(self):
        try:
            filter_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "filter-button"))
            )
            filter_button.click()
            print("Filter button clicked.")
        except TimeoutException:
            print("Filter button not found or not clickable within the given time.")
        except NoSuchElementException:
            print("Filter button not found.")

    def _get_filter_blocks(self):
        try:
            filter_blocks = WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, "filter-block"))
            )
            print(f"Found {len(filter_blocks)} filter blocks. The names are the following:")
            for block in filter_blocks:
                print(block.text)
            return filter_blocks
        except TimeoutException:
            print("No filter blocks found within the given time.")
            return []

    def _process_filter_blocks(self, filter_blocks):
        if not filter_blocks:
            print("No filter blocks to process.")
            return

        category_keys = list(self.categories_data.keys())

        for i, block in enumerate(filter_blocks):
            if i >= len(category_keys):
                print(f"Warning: No category key in categories.json for filter block {i+1}. Skipping.")
                continue
            
            category_key = category_keys[i]
            items_to_select = self.categories_data[category_key]

            if not items_to_select:
                print(f"No items to select for category '{category_key}'. Skipping.")
                continue

            print(f"Processing filter block {i+1}/{len(filter_blocks)}: '{category_key}' which has title '{block.text}'")

            try:
                # Re-locate the filter block to ensure it's fresh
                clickable_block = block

                # --- 1. Open the filter block if it's not already open ---
                # A simple way to check if it's open is to see if checkboxes are visible.
                try:
                    WebDriverWait(clickable_block, 2).until(
                        EC.visibility_of_element_located((By.CLASS_NAME, "facetwp-checkbox"))
                    )
                    print("Filter block is already open.")
                except TimeoutException:
                    clickable_block.click()
                    print(f"Clicked filter block: {category_key}")
                    time.sleep(1.5) # Wait for animation

                # --- 2. Process checkboxes within this block ---
                self._process_checkboxes_for_category(clickable_block, items_to_select)

                # # --- 3. Close the filter block by clicking the toggle again ---
                # self._click_facetwp_toggle(clickable_block)
                # time.sleep(1) # Wait for animation

            except (TimeoutException, StaleElementReferenceException, NoSuchElementException) as e:
                print(f"Could not process filter block '{category_key}' due to: {e}")
                # It might be good to refresh the page or take other recovery actions here
                
    def _process_checkboxes_for_category(self, filter_block, items_to_select):
        processed_checkbox_texts = set()
        
        while True:
            checkboxes = self._get_facetwp_checkboxes(filter_block)
            time.sleep(1)
            
            if not checkboxes:
                break # No more checkboxes to process in this block

            found_new_checkbox_to_click = False
            for checkbox in checkboxes:
                try:
                    checkbox_text_full = checkbox.text
                    if checkbox_text_full in processed_checkbox_texts:
                        continue

                    # Extract the name and the count
                    checkbox_name = ''.join(filter(lambda x: not x.isdigit(), checkbox_text_full)).strip('() ').lower()
                    
                    print(f"Comparing extracted checkbox name '{checkbox_name}' with items to select: {items_to_select}")
                    if checkbox_name in items_to_select:
                        print(f"Found matching checkbox: '{checkbox_name}'")
                        
                        # Extract number for wait time
                        count_str = ''.join(filter(str.isdigit, checkbox_text_full))
                        if count_str:
                            wait_time = int(count_str) / 100
                            print(f"Waiting for {wait_time:.2f} seconds.")
                        else:
                            wait_time = 1 # Default wait time

                        checkbox.click()
                        time.sleep(wait_time)
                        
                        processed_checkbox_texts.add(checkbox_text_full)
                        found_new_checkbox_to_click = True
                        break # Exit the for-loop to re-fetch checkboxes
                except StaleElementReferenceException:
                    print("Checkbox became stale. Re-fetching...")
                    found_new_checkbox_to_click = True
                    break # Re-fetch
            
            if not found_new_checkbox_to_click:
                break # All selectable checkboxes in the current view are processed

    def _click_facetwp_toggle(self, filter_block):
        try:
            facetwp_toggle = WebDriverWait(filter_block, 10).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "facetwp-toggle"))
            )
            facetwp_toggle.click()
            print("Clicked facetwp-toggle.")
        except (TimeoutException, NoSuchElementException) as e:
            print(f"Could not click facetwp-toggle within the filter block due to: {e}")

    def _get_facetwp_checkboxes(self, filter_block):
        try:
            # First Click "facetwp-toggle" to open the filter block
            facetwp_toggle = WebDriverWait(filter_block, 3).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "facetwp-toggle"))
            )
            facetwp_toggle.click()
            print("Clicked facetwp-toggle.")
            time.sleep(1)
            
            checkboxes = WebDriverWait(filter_block, 10).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, "facetwp-checkbox"))
            )
            print(f"Found {len(checkboxes)} facetwp-checkboxes within the block.")
            return checkboxes
        except TimeoutException:
            print("No facetwp-checkboxes found within the filter block within the given time.")
            
            checkboxes = WebDriverWait(filter_block, 10).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, "facetwp-checkbox"))
            )
            print(f"Found {len(checkboxes)} facetwp-checkboxes within the block.")
            return checkboxes


if __name__ == "__main__":
    bot = ProfellowBot()
    
    # Login
    bot._login()
    
    # Pause 1 second
    time.sleep(1)

    # Click filter button
    bot._click_filter_button()

    # Pause 1 second
    time.sleep(1)

    # Get filter blocks
    filter_blocks = bot._get_filter_blocks()

    # Process filter blocks
    bot._process_filter_blocks(filter_blocks)

