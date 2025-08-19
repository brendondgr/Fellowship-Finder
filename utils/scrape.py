import json
import time
import random
from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, NoSuchElementException
import configparser
import os
from utils.data import DataProcessor
from utils.refinement import GeminiRefiner


class ProfellowBot:
    def __init__(self, browser=None):
        config = configparser.ConfigParser()
        config.read('config.ini')
        self.configs_path = config.get('PATHS', 'configs', fallback='configs/')

        # Load filters from JSON file for browser selection and categories
        with open(os.path.join(self.configs_path, "filters.json"), "r") as f:
            filters_data = json.load(f)

        if browser:
            self.browser = browser.lower()
        else:
            self.browser = filters_data.get('Browsing', 'firefox').lower()

        self._initialize_driver()

        # --- Configuration ---
        self.tmp_path = config.get('PATHS', 'tmp', fallback='tmp/')
        
        # --- Data Processor ---
        self.data_processor = DataProcessor()

        # --- Gemini Refiner ---
        self.refiner = GeminiRefiner()

        # Ensure tmp directory exists
        os.makedirs(self.tmp_path, exist_ok=True)

        # Load login credentials from a JSON file
        with open(os.path.join(self.configs_path, "login.json"), "r") as f:
            self.login_data = json.load(f)

        self.categories_data = filters_data["categories"]

        self.LOGIN_URL = "https://www.profellow.com/log-in/"

    def _initialize_driver(self):
        """Initializes the WebDriver based on the selected browser."""
        if self.browser == "firefox":
            service = FirefoxService(GeckoDriverManager().install())
            self.driver = webdriver.Firefox(service=service)
            print("Firefox WebDriver initialized.")
        elif self.browser == "chrome":
            service = ChromeService(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service)
            print("Chrome WebDriver initialized.")
        elif self.browser == "edge":
            service = EdgeService(EdgeChromiumDriverManager().install())
            self.driver = webdriver.Edge(service=service)
            print("Edge WebDriver initialized.")
        elif self.browser == "safari":
            self.driver = webdriver.Safari()
            print("Safari WebDriver initialized.")
        else:
            raise ValueError(f"Unsupported browser: '{self.browser}'. Please choose 'firefox', 'chrome', 'edge', or 'safari'.")
        
    def _are_categories_same(self):
        """Deep compares the filters.json files in configs/ and tmp/."""
        config_cat_path = os.path.join(self.configs_path, "filters.json")
        tmp_cat_path = os.path.join(self.tmp_path, "filters.json")

        if not os.path.exists(tmp_cat_path):
            print("tmp/filters.json does not exist.")
            return False

        try:
            with open(config_cat_path, 'r') as f1, open(tmp_cat_path, 'r') as f2:
                config_data = json.load(f1)["categories"]
                tmp_data = json.load(f2)["categories"]

            if config_data.keys() != tmp_data.keys():
                print("Keys in filters.json files do not match.")
                return False

            for key in config_data:
                if sorted(config_data[key]) != sorted(tmp_data[key]):
                    print(f"Mismatch found in key '{key}' between filters.json files.")
                    return False
            
            print("filters.json files in configs/ and tmp/ are identical.")
            return True
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error comparing filters.json files: {e}")
            return False

    def _get_cached_link(self):
        """Reads the cached link from tmp/link.txt."""
        link_path = os.path.join(self.tmp_path, "link.txt")
        if os.path.exists(link_path):
            with open(link_path, 'r') as f:
                link = f.read().strip()
                if link:
                    print(f"Found cached link: {link}")
                    return link
        print("No cached link found.")
        return None

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
        time.sleep(random.uniform(1, 2))

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
                print(f"Warning: No category key in filters.json for filter block {i+1}. Skipping.")
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
            time.sleep(0.25)
            
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
            time.sleep(0.25)
            
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

    def _click_done_button(self):
        try:
            done_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(.,'Done')]"))
            )
            done_button.click()
            print("Clicked 'Done' button.")
        except TimeoutException:
            print(" 'Done' button not found or not clickable within the given time.")
        except NoSuchElementException:
            print(" 'Done' button not found.")

    def _cache_results(self):
        """Saves the current URL and copies filters.json to tmp/."""
        # Save the current URL
        link_path = os.path.join(self.tmp_path, "link.txt")
        with open(link_path, 'w') as f:
            f.write(self.driver.current_url)
        print(f"Saved current URL to {link_path}")

        # Copy filters.json from configs to tmp
        config_cat_path = os.path.join(self.configs_path, "filters.json")
        tmp_cat_path = os.path.join(self.tmp_path, "filters.json")
        try:
            with open(config_cat_path, 'r') as src, open(tmp_cat_path, 'w') as dst:
                dst.write(src.read())
            print(f"Copied {config_cat_path} to {tmp_cat_path}")
        except FileNotFoundError:
            print(f"Error: {config_cat_path} not found.")

    def run(self):
        """Runs the entire scraping process."""
        try:
            use_cache = self._are_categories_same()
            cached_link = self._get_cached_link()

            if use_cache and cached_link:
                print("Using cached link.")
                self._login()
                self.driver.get(cached_link)
                print(f"Navigated to cached link: {cached_link}")
            else:
                print("Performing a full scrape.")
                self._login()
                self._click_filter_button()
                time.sleep(1)
                filter_blocks = self._get_filter_blocks()
                self._process_filter_blocks(filter_blocks)
                self._click_done_button()
                self._cache_results()
                print("Scraping process completed successfully.")
            
            # Load more results
            self._load_more_results()

            # Keep the browser open for a while to see the result
            print("Process finished. Browser will close in 30 seconds.")
            time.sleep(30)

        except Exception as e:
            print(f"An error occurred during the scraping process: {e}")
        finally:
            print("Closing the browser.")
            self.driver.quit()

            # --- Refine and Save Data ---
            print("Starting data refinement process...")
            self.data_processor.refine_and_save_fellowships(self.refiner)
            print("Data refinement process finished.")

    def _load_more_results(self):
        print("Attempting to load more results...")
        while True:
            # Scroll to the bottom of the page
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2.0)  # Give time for page to load after scroll

            # Scroll up a small amount to bring "facetwp-load-more" into view
            self.driver.execute_script("window.scrollBy(0, -750);")
            time.sleep(1.0)
            
            try:
                load_more_button = WebDriverWait(self.driver, 2).until(
                    EC.element_to_be_clickable((By.CLASS_NAME, "facetwp-load-more"))
                )
                load_more_button.click()
                print("Clicked 'Load More' button. Waiting 2.0 seconds...")
                time.sleep(2.0)  # Wait for content to load
            except TimeoutException:
                print("No more 'Load More' buttons found. All results loaded.")
                break
            except NoSuchElementException:
                print("No 'Load More' button found on the page.")
                break
        
        # Scroll all the way to the top.
        self.driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1.0)

        self._get_fellowship_elements()

    def _get_fellowship_elements(self):
        print("Activating _get_fellowship_elements...")
        try:
            fellowship_elements = self.driver.find_elements(By.CLASS_NAME, "fellowship")
            print(f"Number of 'fellowship' elements found: {len(fellowship_elements)}")
            
            # Process the elements
            self.data_processor.process_fellowships(fellowship_elements)

            return fellowship_elements
        except Exception as e:
            print(f"An error occurred while getting 'fellowship' elements: {e}")
            return []