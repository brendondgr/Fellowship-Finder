from google import genai
import pandas as pd
import json
import os
import time
from tqdm import tqdm

class GeminiRefiner:
    def __init__(self, model_name="gemini-2.5-flash-lite"):
        self.enabled = False
        api_key_path = 'configs/api_key.json'
        gemini_api_key = None

        if os.path.exists(api_key_path):
            try:
                with open(api_key_path, 'r') as f:
                    api_key_data = json.load(f)
                    gemini_api_key = api_key_data.get('gemini_api_key')
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not read API key file at {api_key_path}. Error: {e}")
                return

        if not gemini_api_key:
            print("Warning: `gemini_api_key` not found or is empty in `configs/api_key.json`. GeminiRefiner will be disabled.")
            return

        self.enabled = True
        self.model = model_name
        
        if "flash" in self.model.lower():
            self.rate_limit_interval = 60 / 10
        elif "pro" in self.model.lower():
            self.rate_limit_interval = 60 / 5
        else:
            self.rate_limit_interval = 0
        
        self.last_request_time = 0
        
        try:
            self.client = genai.Client(api_key=gemini_api_key)
        except Exception as e:
            print(f"Failed to initialize Gemini client: {e}")
            self.enabled = False
            return
        
        filters_path = 'configs/filters.json'
        if not os.path.exists(filters_path):
            print(f"Warning: Filters file not found at {filters_path}. System instructions will be empty.")
            self.system_instructions = ''
        else:
            with open(filters_path, 'r') as f:
                filters_data = json.load(f)
                self.system_instructions = filters_data.get('system_instructions', '')
                if not self.system_instructions:
                    print("Warning: `system_instructions` not found or empty in `configs/filters.json`")
                
    def refine(self, row):
        if not self.enabled:
            return None

        if self.rate_limit_interval > 0:
            current_time = time.time()
            time_since_last_request = current_time - self.last_request_time
            if time_since_last_request < self.rate_limit_interval:
                wait_time = self.rate_limit_interval - time_since_last_request
                time.sleep(wait_time)
            self.last_request_time = time.time()
            
        # Format the fellowship text
        self.fellowship_text = self._format_fellowship(row)
        
        # Create the prompt
        self.prompt = f"""
The following is a fellowship opportunity:
{self.fellowship_text}

I am looking for you to extract information about the fellowship, and provide me a summary of the fellowship, by returning a JSON Object in the following format:```json
{{
    "total_compensation": "string", 
    "other_funding": "string",
    "subjects": ["string", "string", "string"],
    "length_in_years": int,
    "interest_rating": float,
    "deadline": "YYYY-MM"
}}
```
Subjects should be a list of strings, and should be "science", "medicine", "technology", "engineering", "arts", "social sciences", etc. Not "Minorities", "Full Funding", etc.

"total_compensation" should be a monetary value. If it is $25,000 for 3 years, then the total should be $75,000. If not specified, please write "N/A" instead. "other_funding" should be a string separated by commas, that tells what other funding is available.

Interest rating should be a float between 1.0 and 5.0 (in intervals of 0.5), which is based on your opinion of my interest in the fellowship based on the following information about me:
{self.system_instructions}

You should return a single JSON Object containing the information for the fellowship. Also if any subcategory of the fellowship is not clear, you should return a "N/A" for that subcategory.
"""
        
        max_retries = 5
        backoff_factor = 2
        
        for attempt in range(max_retries):
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=self.prompt
                )
                refined_data = self._parse_response(response.text)
                return refined_data
            except Exception as e:
                print(f"An error occurred on attempt {attempt + 1}/{max_retries}: {e}")
                if "rate limit" in str(e).lower():
                    sleep_time = backoff_factor ** attempt
                    print(f"Rate limit likely reached. Retrying in {sleep_time} seconds...")
                    time.sleep(sleep_time)
                else:
                    return None
        
        print("Failed to get a valid response after several retries.")
        return None

    def _parse_response(self, response_text):
        try:
            # Clean the response text to extract only the JSON part.
            # It might be enclosed in ```json ... ```
            if '```json' in response_text:
                json_str = response_text.split('```json')[1].split('```')[0]
            else:
                json_str = response_text

            return json.loads(json_str)
        except (json.JSONDecodeError, IndexError) as e:
            print(f"Error parsing JSON: {e}")
            return None

    def _format_fellowship(self, row):
        return f"""```markdown
Title: {row['title']}
Location: {row['location']}
Continent: {row['continent']}
Deadline: {row['deadline']}
Link: {row['link']}
Description: {row['description']}
```"""

if __name__ == '__main__':
    # Example usage:
    refiner = GeminiRefiner()

    # Create a dummy dataframe for testing
    data = {
        'title': ['Test Fellowship'],
        'location': ['Test Location'],
        'continent': ['North America'],
        'deadline': ['December'],
        'link': ['http://test.com'],
        'description': ['This is a test fellowship for testing purposes.'],
        'processed': ['no']
    }
    df = pd.DataFrame(data)
    
    # Wrap the loop with tqdm for a progress bar
    for index, row in tqdm(df.iterrows(), total=df.shape[0], desc="Refining Fellowships"):
        refined_info = refiner.refine(row)
        if refined_info:
            print("\nRefined Fellowship Info:")
            print(json.dumps(refined_info, indent=2))
        else:
            print(f"\nFailed to refine row {index}.")
