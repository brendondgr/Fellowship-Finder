import json
import time
import random
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.firefox import GeckoDriverManager

with open("configs/login.json", "r") as f:
    login_data = json.load(f)

with open("configs/categories.json", "r") as f:
    categories_data = json.load(f)

LOGIN_URL = "https://www.profellow.com/log-in/"

driver = webdriver.Firefox(service=Service(GeckoDriverManager().install()))

try:
    driver.get(LOGIN_URL)

    # Wait for the email input to be visible before interacting
    email_input = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.ID, "wpforms-106652-field_1"))
    )
    for char in login_data["email"]:
        email_input.send_keys(char)
        time.sleep(random.uniform(0.01, 0.05))

    # Password input
    password_input = driver.find_element(By.ID, "wpforms-106652-field_2")
    for char in login_data["password"]:
        password_input.send_keys(char)
        time.sleep(random.uniform(0.01, 0.05))

    # Add a delay before clicking the login button
    time.sleep(random.uniform(0.4, 1.3))

    # Login button
    login_button = driver.find_element(By.ID, "wpforms-submit-106652")
    login_button.click()

    # Wait for successful login by checking for redirection to the dashboard
    WebDriverWait(driver, 10).until(
        EC.url_contains("fellowship")
    )
    print("Login successful!")

    print(f"Current URL: {driver.current_url}")
    print(f"Page title: {driver.title}")

    # Add a 2-4 second delay before additional actions
    time.sleep(random.uniform(2, 4))

    # Click button at ID "filterToggle"
    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "filterToggle"))
    ).click()
    print("Successfully clicked the filter toggle button.")
    time.sleep(random.uniform(0.25, 0.6))

    for category, items in categories_data.items():
        for item in items:
            # Re-find filter blocks each time to avoid stale elements
            filter_blocks = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, "filter-block"))
            )
            for filter_block in filter_blocks:
                # Click the filter-block to open it
                driver.execute_script("arguments[0].click();", filter_block)
                # Wait for the facetwp-toggle to be visible within the filter_block
                facet_toggle = WebDriverWait(filter_block, 10).until(
                    EC.visibility_of_element_located((By.CLASS_NAME, "facetwp-toggle"))
                )
                
                # Use JavaScript to get the text to handle cases where text might not be directly visible
                category_name = driver.execute_script("return arguments[0].innerText;", filter_block).lower()

                if category.replace("_", " ") in category_name:                    
                    # Find and click the facet toggle within the current filter block
                    facet_toggle = filter_block.find_element(By.CLASS_NAME, "facetwp-toggle")
                    if "active" not in filter_block.get_attribute("class"):
                        driver.execute_script("arguments[0].click();", facet_toggle)
                        time.sleep(1) # Wait for the dropdown to open

                    # Re-find checkboxes to ensure we have the latest list
                    checkboxes = filter_block.find_elements(By.CLASS_NAME, "facetwp-checkbox")
                    for checkbox in checkboxes:
                        checkbox_text = checkbox.text.lower()
                        if item in checkbox_text:
                            # Check if the checkbox is already selected
                            if "checked" not in checkbox.get_attribute("class"):
                                driver.execute_script("arguments[0].click();", checkbox)
                                print(f"Clicked checkbox: {checkbox_text}")
                                time.sleep(5) # Wait for the list to refresh
                                # Break from the inner loop to re-find all elements from the start
                                break
                    else:
                        continue # If the inner loop didn't break, continue to the next filter block
                    break # If the inner loop broke, break from the outer loop as well
            else:
                print(f"Category '{category}' not found.")


except Exception as e:
    print(f"An error occurred: {e}")

finally:
    driver.quit()