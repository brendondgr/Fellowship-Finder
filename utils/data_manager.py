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

    def get_filtered_fellowships(self, filters):
        if self.df is None:
            return pd.DataFrame()

        df_filtered = self.df.copy()

        # Filter by 'show' status
        if not filters.get('show_removed', False):
            df_filtered = df_filtered[df_filtered['show'] == 1]

        # Filter by minimum stars
        min_stars = filters.get('min_stars', 1)
        if min_stars > 1:
            df_filtered = df_filtered[df_filtered['interest_rating'] >= min_stars]

        # Handle 'favorites_first' sorting
        if filters.get('favorites_first', False):
            df_filtered = df_filtered.sort_values(by='favorited', ascending=False)

        # Handle search keywords
        keywords = filters.get('keywords', [])
        if keywords:
            df_filtered['keyword_matches'] = df_filtered.apply(
                lambda row: self._count_keyword_matches(row, keywords), axis=1
            )
            df_filtered = df_filtered[df_filtered['keyword_matches'] > 0]
            df_filtered = df_filtered.sort_values(by='keyword_matches', ascending=False)
        
        return df_filtered

    def _count_keyword_matches(self, row, keywords):
        count = 0
        search_text = ' '.join([
            str(row.get('title', '')),
            str(row.get('description', '')),
            str(row.get('subjects', ''))
        ]).lower()

        for keyword in keywords:
            if keyword.lower() in search_text:
                count += 1
        return count

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
