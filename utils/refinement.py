from google import genai
import pandas as pd
import json
import os
import time
from tqdm import tqdm

class GeminiRefiner:
    def __init__(self, model_name="gemini-2.5-flash-preview-05-20"):
        # Load the Gemini API key from the api_key.json file
        api_key_path = 'configs/api_key.json'
        if not os.path.exists(api_key_path):
            raise FileNotFoundError(f"API key file not found at {api_key_path}. Please create it.")
        
        with open(api_key_path, 'r') as f:
            api_key_data = json.load(f)
            gemini_api_key = api_key_data.get('gemini_api_key')
            if not gemini_api_key:
                raise ValueError("`gemini_api_key` not found in `configs/api_key.json`")
        
        self.model = model_name
        
        self.client = genai.Client(
            api_key=gemini_api_key
        )
        
        self.interests = f"""
I am currently interested in the applications of Artificial Intellig    `ence and Machine Learning to the field of Medicine. I am currently researching Robotic Surgery and the applications, limitations and opportunities of this in the field. I am a PhD Student studying Scientific Computing and Computational Science. I have a Biochemistry BS.

Generally, I am interested in any forms of technology, science, robotics, and medicine.

I am a male US Citizen, and I am currently living in the United States. I am also of Hispanic ethnicity.
"""
    def refine(self, row):
        # Format the fellowship text
        self.fellowship_text = self._format_fellowship(row)
        
        # Create the prompt
        self.prompt = f"""
The following is a fellowship opportunity:
{self.fellowship_text}

I am looking for you to extract information about the fellowship, and provide me a summary of the fellowship, by returning a JSON Object in the following format:```json
{{
    "title": "string",
    "location": "string",
    "continent": "string",
    "deadline": "string in format YYYY-MM",
    "link": "string",
    "description": "string", 
    "subjects": ["string", "string", "string"], 
    "total_compensation": "$string",
    "length_in_years": int,
    "interest_rating": float
}}
```
Subjects should be a list of strings, and should be "science", "medicine", "technology", "engineering", "arts", "social sciences", etc. Not "Minorities", "Full Funding", etc.

Interest rating should be a float between 1.0 and 4.0, which is based on the following criteria:
- 1: I qualify based on my Citizenship and Residency.
- 2: I qualify based on my Background, specifically the subject I have studied and what I am currently studying.
- 3: The fellowship is correlated with what I am interested in. If it has some overlap, this rating added should be 0.5, instead of 1.0. If no overlap, subtract 1.0 from the entire score.
- 4: The fellowship covers at least a single year. 

My interests are, which should sway how you decide #3, are:
{self.interests}

You should return a single JSON Object containing the information for the fellowship. Also if any subcategory of the fellowship is not clear, you should return a "NA" for that subcategory.
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
            print("Raw response text:")
            print(response_text)
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
