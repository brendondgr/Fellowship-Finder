import configparser
import os
import re
import json
import pandas as pd
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from tqdm import tqdm
from utils.data_manager import format_deadline
from datetime import datetime
import sys

class DataProcessor:
    def __init__(self):
        config = configparser.ConfigParser()
        config.read('config.ini')
        self.raw_data_path = config.get('PATHS', 'raw_data', fallback='data/raw/')
        self.processed_data_path = config.get('PATHS', 'processed_data', fallback='data/processed/')
        os.makedirs(self.raw_data_path, exist_ok=True)
        os.makedirs(self.processed_data_path, exist_ok=True)
        self.fellowship_csv_path = os.path.join(self.raw_data_path, "raw_fellowship_list.csv")
        self.processed_fellowship_csv_path = os.path.join(self.processed_data_path, "processed_fellowship_list.csv")
        
        # Load keywords from filters.json
        self.configs_path = config.get('PATHS', 'configs', fallback='configs/')
        filters_path = os.path.join(self.configs_path, "filters.json")
        with open(filters_path, "r") as f:
            filters_data = json.load(f)
            self.keywords_config = filters_data.get("keywords", {})

    def _passes_keyword_filter(self, title, description):
        """Checks if the fellowship passes the keyword filter from filters.json."""
        keyword_type = self.keywords_config.get("type", "OR").upper()
        words = self.keywords_config.get("words", [])

        if not words:
            return True  # No keywords to filter by

        # Combine title and description for searching
        text_to_search = f"{title.lower()} {description.lower() if description else ''}"
        
        lower_words = [word.lower() for word in words]

        if keyword_type == "AND":
            if all(word in text_to_search for word in lower_words):
                print(f"Fellowship '{title}' passed AND filter.")
                return True
            else:
                print(f"Fellowship '{title}' failed AND filter.")
                return False
        elif keyword_type == "OR":
            if any(word in text_to_search for word in lower_words):
                print(f"Fellowship '{title}' passed OR filter.")
                return True
            else:
                print(f"Fellowship '{title}' failed OR filter.")
                return False
        
        return True # Default to passing if type is not AND/OR


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

                # Keyword Filtering
                if not self._passes_keyword_filter(title, description):
                    continue
                
                # Format the deadline
                formatted_deadline = format_deadline(deadline)
                
                new_fellowships.append({
                    'title': title,
                    'location': location,
                    'continent': continent,
                    'deadline': formatted_deadline,
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

    def refine_and_save_fellowships(self, refiner):
        if not os.path.exists(self.fellowship_csv_path):
            print("Raw fellowship data not found.")
            return

        raw_df = pd.read_csv(self.fellowship_csv_path)
        unprocessed_df = raw_df[raw_df['processed'] == 'no']

        if unprocessed_df.empty:
            print("No new fellowships to process.")
            return

        print(f"Found {len(unprocessed_df)} unprocessed fellowships to refine.")
        try:
            refiner_model = getattr(refiner, 'model', 'unknown')
            print(f"Refiner status -> enabled={refiner.enabled}, model={refiner_model}")
        except Exception:
            pass

        if os.path.exists(self.processed_fellowship_csv_path):
            processed_df = pd.read_csv(self.processed_fellowship_csv_path)
            
            # Ensure all necessary columns exist
            expected_cols = [
                'title', 'location', 'continent', 'deadline', 'link', 'description', 
                'subjects', 'total_compensation', 'other_funding', 'length_in_years', 
                'interest_rating', 'favorited', 'show', 'announced'
            ]
            for col in expected_cols:
                if col not in processed_df.columns:
                    # Add missing column with a default value
                    if col in ['favorited', 'length_in_years']:
                        processed_df[col] = 0
                    elif col == 'show':
                        processed_df[col] = 1
                    elif col == 'interest_rating':
                        processed_df[col] = 0.0
                    elif col == 'total_compensation':
                        processed_df[col] = "N/A"
                    elif col == 'subjects':
                        processed_df[col] = []
                    elif col == 'other_funding':
                        processed_df[col] = ""
                    elif col == 'announced':
                        processed_df[col] = "no"
                    elif col == 'links':
                        processed_df[col] = []
                    else:
                        processed_df[col] = ""
            
            # Save the updated DataFrame
            processed_df.to_csv(self.processed_fellowship_csv_path, index=False)
            print(f"Updated processed_fellowship_list.csv with missing columns.")
        else:
            processed_df = pd.DataFrame()

        refined_data_list = []
        
        # Wrap the loop with tqdm for a progress bar
        for index, row in tqdm(unprocessed_df.iterrows(), total=unprocessed_df.shape[0], desc="Refining Fellowships"):
            try:
                if refiner.enabled:
                    refined_data = refiner.refine(row)
                else: # No refiner, create data with defaults
                    refined_data = {
                        "subjects": [],
                        "total_compensation": "N/A",
                        "other_funding": "",
                        "length_in_years": 0,
                        "interest_rating": 0.0,
                        "links": []
                    }

                if refined_data:
                    # Combine raw data with refined data
                    combined_data = row.to_dict()
                    combined_data.update(refined_data)
                    
                    # Clean and validate the combined data
                    cleaned_data = self._clean_and_validate_refined_data(combined_data)
                    
                    if cleaned_data:
                        refined_data_list.append(cleaned_data)
                        raw_df.loc[index, 'processed'] = 'yes'
            except Exception as e:
                tqdm.write(f"An error occurred while refining row {index + 2}: {e}")
                sys.stdout.flush()
                raw_df.loc[index, 'processed'] = 'error'

        if refined_data_list:
            new_processed_df = pd.DataFrame(refined_data_list)

            if processed_df.empty:
                processed_df = new_processed_df
            else:
                processed_df = pd.concat([processed_df, new_processed_df], ignore_index=True)

            processed_df.drop_duplicates(subset=['link'], keep='last', inplace=True)
            processed_df.to_csv(self.processed_fellowship_csv_path, index=False)
            print(f"Saved/updated {len(new_processed_df)} refined fellowships to {self.processed_fellowship_csv_path}")

            raw_df.to_csv(self.fellowship_csv_path, index=False)
            print("Updated raw_fellowship_list.csv with processed status.")

    def _clean_and_validate_refined_data(self, data):
        # Default values for all possible refined keys
        defaults = {
            "subjects": [],
            "total_compensation": "N/A",
            "other_funding": "",
            "length_in_years": 0,
            "interest_rating": 0.0,
            "links": [],
            "favorited": 0,
            "show": 1,
            "announced": "no",
            "deadline": "NA"
        }

        # Use defaults for any missing keys in the data
        for key, value in defaults.items():
            data.setdefault(key, value)
            
        # Clean and validate data types
        try:
            # String fields
            for key in ["title", "location", "continent", "link", "description", "other_funding", "announced"]:
                data[key] = str(data.get(key, ''))

            # Deadline: should be in YYYY-MM format
            deadline = str(data.get("deadline", ""))
            if re.match(r"\d{4}-\d{2}", deadline):
                data["deadline"] = deadline
            else:
                try:
                    # Attempt to parse from "Month, YYYY" format
                    date_obj = datetime.strptime(deadline, "%B, %Y")
                    data["deadline"] = date_obj.strftime("%Y-%m")
                except (ValueError, TypeError):
                    data["deadline"] = "NA"
            
            # Subjects: should be a list of strings
            subjects = data.get("subjects", [])
            if isinstance(subjects, list) and all(isinstance(s, str) for s in subjects):
                data["subjects"] = subjects
            else:
                data["subjects"] = []
            
            # Links: should be a list of strings
            links = data.get("links", [])
            if isinstance(links, list) and all(isinstance(l, str) for l in links):
                data["links"] = links
            else:
                data["links"] = []

            # Total Compensation: should be a string, ensure it's not NaN
            compensation = data.get("total_compensation")
            if pd.isna(compensation):
                data["total_compensation"] = "N/A"
            else:
                data["total_compensation"] = str(compensation)


            # Length in years: should be an integer
            length = data.get("length_in_years")
            data["length_in_years"] = int(length) if str(length).isdigit() else 0

            # Interest rating: should be a float
            rating = data.get("interest_rating")
            data["interest_rating"] = float(rating) if rating is not None else 0.0

            # Favorited and show: should be integers
            data['favorited'] = int(data.get('favorited', 0))
            data['show'] = int(data.get('show', 1))

        except (ValueError, TypeError) as e:
            tqdm.write(f"Data validation error for link {data.get('link', 'N/A')}: {e}")
            sys.stdout.flush()
            # Still return data with defaults even if a field fails validation
            return data

        return data
