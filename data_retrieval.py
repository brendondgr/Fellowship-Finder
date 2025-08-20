import argparse
from utils.scrape import ProfellowBot
from utils.files_folders import FileManager
from utils.data import DataProcessor
from utils.refinement import GeminiRefiner
import os
import json

def main():
    # --- File and Folder Setup ---
    file_manager = FileManager()
    file_manager.setup()

    # --- Configuration and Argument Parsing ---
    parser = argparse.ArgumentParser(description="A bot to scrape Profellow.com")
    parser.add_argument('--cleartmp', action='store_true', help="Clear the tmp folder before starting the bot.")
    parser.add_argument('--cleanup', action='store_true', help="Clear both tmp and data folders before starting the bot.")
    parser.add_argument('--cleardata', action='store_true', help="Clear the data folder before starting the bot.")
    parser.add_argument('--refine', action='store_true', help="Refine existing raw data without running the scraper.")
    args = parser.parse_args()

    if args.cleartmp:
        file_manager.clear_tmp_folder()

    if args.cleanup:
        file_manager.clear_tmp_folder()
        file_manager.clear_data_folder()
    elif args.cleardata:
        file_manager.clear_data_folder()

    if args.refine:
        data_processor = DataProcessor()
        
        # Check if the raw data file exists
        raw_csv_path = os.path.join(data_processor.raw_data_path, "raw_fellowship_list.csv")
        if not os.path.exists(raw_csv_path):
            print(f"No raw data file found at '{raw_csv_path}'. Exiting.")
            return

        refiner = GeminiRefiner()
        data_processor.refine_and_save_fellowships(refiner)
    else:
        # Determine the browser to use
        # Read browser from filters.json
        filters_path = os.path.join(os.getcwd(), 'configs', 'filters.json')
        with open(filters_path, 'r') as f:
            filters_config = json.load(f)
        browser = filters_config.get('Browsing', 'firefox')

        # Update the config file if a valid browser is specified via command line
        # --- Bot Execution ---
        bot = ProfellowBot(browser=browser)
        bot.run()

if __name__ == "__main__":
    main()

