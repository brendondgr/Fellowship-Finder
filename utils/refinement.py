from google import genai
import pandas as pd
import json
import os
import time
from tqdm import tqdm
import requests
import sys

class GeminiRefiner:
    def __init__(self, model_name="sonar"):
        print(f'Model Name received in Refiner: {model_name}')
        self.enabled = False
        api_key_path = 'configs/api_key.json'
        gemini_api_key = None
        perplexity_api_key = None

        if os.path.exists(api_key_path):
            try:
                with open(api_key_path, 'r') as f:
                    api_key_data = json.load(f)
                    if "gemini" in model_name.lower():
                        gemini_api_key = api_key_data.get('gemini_api_key')
                    elif "sonar" in model_name.lower():
                        perplexity_api_key = api_key_data.get('perplexity_api_key')
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not read API key file at {api_key_path}. Error: {e}")
                # Keep self.enabled as False, no return here

        print(f"DEBUG Refiner: Loaded Gemini API Key (present and non-empty): {gemini_api_key is not None and len(gemini_api_key) > 0}")
        print(f"DEBUG Refiner: Loaded Perplexity API Key (present and non-empty): {perplexity_api_key is not None and len(perplexity_api_key) > 0}")

        if "gemini" in model_name.lower():
            if not gemini_api_key:
                print("Warning: `gemini_api_key` not found or is empty in `configs/api_key.json`. GeminiRefiner will be disabled.")
                # Keep self.enabled as False, no return here
        elif "sonar" in model_name.lower():
            if not perplexity_api_key:
                print("Warning: `perplexity_api_key` not found or is empty in `configs/api_key.json`. GeminiRefiner will be disabled.")
                # Keep self.enabled as False, no return here

        # Only enable if the relevant key is present
        if ("gemini" in model_name.lower() and gemini_api_key) or \
           ("sonar" in model_name.lower() and perplexity_api_key):
            self.enabled = True
        else:
            self.enabled = False # Explicitly set to False if checks failed

        self.model = model_name
        print(f"DEBUG Refiner: Final self.enabled status: {self.enabled}")
        
        if "flash" in self.model.lower():
            self.rate_limit_interval = 60 / 10  # More generous for Flash
        elif "pro" in self.model.lower():
            self.rate_limit_interval = 60 / 5 # Standard Pro model limit
        elif "sonar" in self.model.lower():
            self.rate_limit_interval = 60 / 50
        else:
            self.rate_limit_interval = 0
        
        self.last_request_time = 0
        
        if "gemini" in self.model.lower():
            try:
                self.client = genai.Client(api_key=gemini_api_key)
            except Exception as e:
                print(f"Failed to initialize Gemini client: {e}")
                self.enabled = False
                return
        elif "sonar" in self.model.lower():
            self.client = Prompter(perplexity_key=perplexity_api_key)
        
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
        self.prompt = self.fellowship_text + f"""\n\n
I need you to find the following information about the fellowinship:
- Total Compensation, specifically the stipend that is typically provided.
- Other Funding, such as travel grants, housing grants, tuition coverage, etc.
- Description in your own words, based on all information provided.
- Guaranteed Length of Fellowship
- Detailed Information about the Fellowship
- Subjects related to the Fellowship

I then need you to rate the fellowship between 0-5 stars based on the following:
{self.system_instructions}

I will then need you to provide a response in the following format JSON Format:
{{
    "total_compensation": int,
    "other_funding": str,
    "subjects": [str, str, str],
    "length_in_years": int,
    "interest_rating": float,
    "deadline": str,
    "description": str,
}}

Keep Total Compensation as a number, no other formatting such as dollar signs, commas, etc (I.e. 100000, not $100,000)

Deadline should be in format "YYYY-MM".

Keep the Subjects limited to 1-2 words at most. They are meant to be general keywords, such as "Health Science", "Deep Learning", "Robotics", etc.

Ensure that this is a Valid JSON Object. Thanks!
"""
        
        max_retries = 5
        backoff_factor = 2
        
        for attempt in range(max_retries):
            try:
                if "gemini" in self.model.lower():
                    print(f'GEMINI DETECTED. Attempt {attempt + 1}. Using model: models/{self.model}')
                    # CORRECTED API CALL: Use self.client.generate_content directly
                    response = self.client.generate_content(
                        model=f'models/{self.model}', # Prepend 'models/' as required
                        contents=self.prompt
                    )
                    print(f'Response Text: {response.text}')
                    refined_data = self._parse_response(response.text)
                    print(f'Refined Data (parsed): {refined_data}')
                elif "sonar" in self.model.lower():
                    print(f'PERPLEXITY DETECTED. Attempt {attempt + 1}.')
                    refined_data = self.client.run(self.prompt)
                    print(f'Refined Data (parsed): {refined_data}')
                else:
                    raise ValueError(f"Invalid model name: {self.model}")
                return refined_data
            except Exception as e:
                tqdm.write(f"An error occurred on attempt {attempt + 1}/{max_retries}: {e}")
                sys.stdout.flush()
                if "rate limit" in str(e).lower():
                    sleep_time = backoff_factor ** attempt
                    tqdm.write(f"Rate limit likely reached. Retrying in {sleep_time} seconds...")
                    sys.stdout.flush()
                    time.sleep(sleep_time)
                else:
                    return None
        
        tqdm.write("Failed to get a valid response after several retries.")
        sys.stdout.flush()
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
            tqdm.write(f"Error parsing JSON: {e}")
            sys.stdout.flush()
            return None

    def _format_fellowship(self, row):
        return f"""
Please find me information about the {row['title']} fellowship, hosted by the {row['location']}

The description I have so far is:
{row['description']}

I know the deadline is {row['deadline']} and it is located in {row['continent']}.
"""

class Prompter:
    def __init__(self, perplexity_key=None):
        if perplexity_key is None:
            raise ValueError("Perplexity API key is required")
        
        self.perplexity_key = perplexity_key
        
    def run(self, prompt):
        try:
            perplexity_result = self.perplexity_generate(prompt)
            # tqdm.write("Perplexity generation complete.")
            return perplexity_result
        except Exception as e:
            error_message = f"Error: {str(e)}"
            tqdm.write(error_message)
            sys.stdout.flush()
            return {"error": error_message}

    def perplexity_generate(self, prompt):
        url = "https://api.perplexity.ai/chat/completions"
        
        payload = {
            "model": "sonar",
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        
        headers = {
            "Authorization": f"Bearer {self.perplexity_key}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(url, json=payload, headers=headers).json()
        
        # Get Text and Convert to JSON...
        filtered_perplexity = response['choices'][0]['message']['content']
        
        file = json.loads(filtered_perplexity)
        
        links=[]
        if 'citations' in response:
            links = response['citations']
        elif 'search_results' in response:
            links = [result['url'] for result in response['search_results']]
        
        file["links"] = links
        
        return file


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
            tqdm.write("\nRefined Fellowship Info:")
            sys.stdout.flush()
            tqdm.write(json.dumps(refined_info, indent=2))
            sys.stdout.flush()
        else:
            tqdm.write(f"\nFailed to refine row {index}.")
            sys.stdout.flush()
