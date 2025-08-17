import configparser
import os
import pandas as pd

class DataManager:
    def __init__(self):
        config = configparser.ConfigParser()
        config.read('config.ini')
        self.processed_data_path = config.get('PATHS', 'processed_data', fallback='data/processed/')
        self.fellowship_csv_path = os.path.join(self.processed_data_path, "processed_fellowship_list.csv")
        print(f"DataManager: Checking for processed data file at: {os.path.abspath(self.fellowship_csv_path)}")
        self.df = None
        self.data_available = False
        self.load_fellowship_data()

    def refresh_data_if_needed(self):
        """Checks for the data file and loads it if it wasn't available before."""
        file_exists = os.path.exists(self.fellowship_csv_path)
        # If file now exists, but we previously thought it didn't
        if file_exists and not self.data_available:
            print("DataManager: Data file found on refresh. Reloading...")
            self.load_fellowship_data()
        # If file does not exist, update state
        elif not file_exists:
            self.data_available = False

    def load_fellowship_data(self):
        if not os.path.exists(self.fellowship_csv_path):
            print(f"DataManager: Data file not found at {self.fellowship_csv_path}")
            if self.data_available: # Only print if state is changing
                print("DataManager: Processed data file NOT FOUND.")
            self.data_available = False
            return
        
        if not self.data_available: # Only print if state is changing
            print("DataManager: Processed data file FOUND. Loading data.")
        try:
            print(f"DataManager: Loading data from {self.fellowship_csv_path}")
            self.df = pd.read_csv(self.fellowship_csv_path)
            self.ensure_required_columns()
            self.data_available = True
            print(f"DataManager: Data loaded successfully. Total rows: {len(self.df)}")
        except Exception as e:
            print(f"Error loading fellowship data: {e}")
            self.data_available = False

    def ensure_required_columns(self):
        updated = False
        if 'favorited' not in self.df.columns:
            self.df['favorited'] = 0
            updated = True
        
        if 'show' not in self.df.columns:
            self.df['show'] = 1
            updated = True

        if 'interest_rating' not in self.df.columns:
            self.df['interest_rating'] = 0
            updated = True

        if updated:
            self.save_fellowship_data()

    def save_fellowship_data(self):
        if self.df is not None:
            self.df.to_csv(self.fellowship_csv_path, index=False)

    def get_visible_fellowships(self):
        if self.df is None:
            return pd.DataFrame()
        return self.df[self.df['show'] == 1]

    def update_fellowship_status(self, fellowship_id, status_type, value):
        if self.df is None:
            return False

        try:
            row_index = int(fellowship_id)
            if row_index in self.df.index:
                self.df.loc[row_index, status_type] = int(value)
                self.save_fellowship_data()
                return True
            return False
        except (ValueError, TypeError):
            return False
