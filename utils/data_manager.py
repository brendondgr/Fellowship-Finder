import configparser
import os
import pandas as pd
from datetime import datetime

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
            self._coerce_column_types()
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
        
        if 'total_compensation' not in self.df.columns:
            self.df['total_compensation'] = "N/A"
            updated = True
            
        if 'other_funding' not in self.df.columns:
            self.df['other_funding'] = ""
            updated = True
            
        if 'subjects' not in self.df.columns:
            self.df['subjects'] = []
            updated = True
            
        if 'length_in_years' not in self.df.columns:
            self.df['length_in_years'] = 0
            updated = True

        if 'announced' not in self.df.columns:
            self.df['announced'] = "no"
            updated = True

        if updated:
            self.save_fellowship_data()

    def save_fellowship_data(self):
        if self.df is not None:
            self.df.to_csv(self.fellowship_csv_path, index=False)

    def _coerce_column_types(self):
        """Ensure important columns have expected data types for filtering/sorting."""
        if self.df is None:
            return
        try:
            # favorited and show should be 0/1 integers
            for col in ['favorited', 'show']:
                if col in self.df.columns:
                    self.df[col] = pd.to_numeric(self.df[col], errors='coerce', downcast='integer').fillna(0).astype(int)
            # interest_rating should be float
            if 'interest_rating' in self.df.columns:
                self.df['interest_rating'] = pd.to_numeric(self.df['interest_rating'], errors='coerce').fillna(0.0).astype(float)
            # length_in_years should be integer if present
            if 'length_in_years' in self.df.columns:
                self.df['length_in_years'] = pd.to_numeric(self.df['length_in_years'], errors='coerce').fillna(0).astype(int)
        except Exception as e:
            print(f"DataManager: Warning - failed to coerce column types: {e}")

    def get_visible_fellowships(self):
        if self.df is None:
            return pd.DataFrame()
        return self.df[self.df['show'] == 1]

    def get_filtered_fellowships(self, filters):
        if self.df is None:
            return pd.DataFrame()

        df_filtered = self.df.copy()
        print(f"DataManager: Starting filter. total_rows={len(df_filtered)} show_removed={filters.get('show_removed', False)} min_stars={filters.get('min_stars')} favorites_first={filters.get('favorites_first')} keywords_len={len(filters.get('keywords', []))}")

        # Filter by 'show' status
        if not filters.get('show_removed', False):
            before = len(df_filtered)
            df_filtered = df_filtered[df_filtered['show'] == 1]
            print(f"DataManager: After show==1 filter: {len(df_filtered)} (removed {before - len(df_filtered)})")

        # Filter by minimum stars
        min_stars = filters.get('min_stars', 1)
        if min_stars > 1:
            before = len(df_filtered)
            df_filtered = df_filtered[df_filtered['interest_rating'] >= min_stars]
            print(f"DataManager: After min_stars>={min_stars} filter: {len(df_filtered)} (removed {before - len(df_filtered)})")

        # Handle 'favorites_first' sorting
        if filters.get('favorites_first', False):
            df_filtered = df_filtered.sort_values(by='favorited', ascending=False)
            print("DataManager: Sorted with favorites first")

        # Handle search keywords
        keywords = filters.get('keywords', [])
        if keywords:
            df_filtered['keyword_matches'] = df_filtered.apply(
                lambda row: self._count_keyword_matches(row, keywords), axis=1
            )
            before = len(df_filtered)
            df_filtered = df_filtered[df_filtered['keyword_matches'] > 0]
            df_filtered = df_filtered.sort_values(by='keyword_matches', ascending=False)
            print(f"DataManager: After keywords filter: {len(df_filtered)} (removed {before - len(df_filtered)})")
        
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

def format_deadline(deadline_text):
    """
    Formats the deadline string to include the correct year.

    Args:
        deadline_text (str): The raw deadline text (e.g., "August", "Rolling").

    Returns:
        str: The formatted deadline string (e.g., "August, 2024", "Rolling").
    """
    if not deadline_text or "rolling" in deadline_text.lower():
        return deadline_text

    try:
        # Get current month and year
        now = datetime.now()
        current_month = now.month
        current_year = now.year

        # Parse the deadline month
        deadline_month_str = deadline_text.split()[0]
        deadline_datetime = datetime.strptime(deadline_month_str, "%B")
        deadline_month = deadline_datetime.month

        # Determine the year
        if deadline_month >= current_month:
            year = current_year
        else:
            year = current_year + 1

        return f"{deadline_month_str}, {year}"
    except ValueError:
        # If parsing fails, return the original text
        return deadline_text
