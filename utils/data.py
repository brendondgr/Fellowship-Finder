import configparser
import os
import pandas as pd
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

class DataProcessor:
    def __init__(self):
        config = configparser.ConfigParser()
        config.read('config.ini')
        self.raw_data_path = config.get('PATHS', 'raw_data', fallback='data/raw/')
        os.makedirs(self.raw_data_path, exist_ok=True)
        self.fellowship_csv_path = os.path.join(self.raw_data_path, "raw_fellowship_list.csv")

    def process_fellowships(self, fellowship_elements):
        print(f"Processing {len(fellowship_elements)} fellowship elements.")
        
        # Load existing data or create a new DataFrame
        if os.path.exists(self.fellowship_csv_path):
            df = pd.read_csv(self.fellowship_csv_path)
            existing_links = set(df['link'].tolist())
            print(f"Loaded existing data from {self.fellowship_csv_path}. Found {len(existing_links)} existing links.")
        else:
            df = pd.DataFrame(columns=['title', 'location', 'continent', 'deadline', 'link', 'description', 'processed'])
            existing_links = set()
            print("No existing data file found. A new one will be created.")

        new_fellowships = []

        for element in fellowship_elements:
            try:
                # Extract title and link
                header = element.find_element(By.CLASS_NAME, "fellowship-content__header")
                link_element = header.find_element(By.TAG_NAME, "a")
                link = link_element.get_attribute("href")

                if link in existing_links:
                    print(f"Skipping duplicate fellowship: {link}")
                    continue

                title = header.find_element(By.TAG_NAME, "h2").text

                # Extract metadata
                meta = element.find_element(By.CLASS_NAME, "fellowship-content__meta")
                
                try:
                    location = meta.find_element(By.CLASS_NAME, "fellowship-meta--organization").text
                except NoSuchElementException:
                    location = None
                
                try:
                    continent = meta.find_element(By.CLASS_NAME, "fellowship-meta--region").text
                except NoSuchElementException:
                    continent = None

                try:
                    deadline = meta.find_element(By.CLASS_NAME, "fellowship-meta--deadline").text
                except NoSuchElementException:
                    deadline = None
                
                # Description
                # The user mentioned "p1" class, which is likely a typo for a <p> tag.
                # I'll look for a `p` tag inside the element.
                try:
                    description = element.find_element(By.TAG_NAME, "p").text
                except NoSuchElementException:
                    description = None


                new_fellowships.append({
                    'title': title,
                    'location': location,
                    'continent': continent,
                    'deadline': deadline,
                    'link': link,
                    'description': description,
                    'processed': 'no'
                })
                
                existing_links.add(link)

            except Exception as e:
                print(f"Error processing a fellowship element: {e}")

        if new_fellowships:
            new_df = pd.DataFrame(new_fellowships)
            # Reorder columns to match user request, adding description
            cols = ['title', 'location', 'continent', 'deadline', 'link', 'description', 'processed']
            new_df = new_df[cols]
            
            df = pd.concat([df, new_df], ignore_index=True)
            df.to_csv(self.fellowship_csv_path, index=False)
            print(f"Added {len(new_fellowships)} new fellowships. Total fellowships: {len(df)}")
        else:
            print("No new fellowships to add.")
