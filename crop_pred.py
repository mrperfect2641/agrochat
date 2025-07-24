import pandas as pd
import difflib
import re

class CropPredictor:
    def __init__(self, data_path='crop_data.csv'):
        self.data = pd.read_csv(data_path)
        self._preprocess_data()

    def _preprocess_data(self):
        """Clean and standardize crop data, stripping punctuation from regions."""
        # Normalize column names
        self.data.columns = self.data.columns.str.strip().str.lower()

        # Clean and normalize regions: lowercase, strip whitespace, remove non-letters/spaces
        self.data['region'] = (
            self.data['region']
            .astype(str)
            .str.strip()
            .str.lower()
            .apply(lambda s: re.sub(r'[^a-z\s]', '', s))
        )

        # Title-case the other text fields
        self.data['crop'] = (
            self.data['crop']
            .astype(str)
            .str.strip()
            .str.title()
        )
        self.data['season'] = (
            self.data['season']
            .astype(str)
            .str.strip()
            .str.title()
        )
        self.data['soil_type'] = (
            self.data['soil_type']
            .astype(str)
            .str.strip()
            .str.title()
        )

        # If there's a 'yield' column, title-case it too
        if 'yield' in self.data.columns:
            self.data['yield'] = (
                self.data['yield']
                .astype(str)
                .str.strip()
                .str.title()
            )

    def get_suitable_crops(self, region):
        """
        Return a dict of recommended crops for the given region.
        If no exact region match, suggest the closest match via fuzzy lookup.
        """
        # 1) Normalize the incoming region: lowercase, strip, remove punctuation
        raw_input = region.strip()
        region_key = raw_input.lower()
        region_key = re.sub(r'[^a-z\s]', '', region_key)

        # 2) Try exact match
        df = self.data[self.data['region'] == region_key]
        suggested = False
        original_query = None

        # 3) If no exact match, attempt fuzzy matching on cleaned region names
        if df.empty:
            all_regions = self.data['region'].unique()
            matches = difflib.get_close_matches(region_key, all_regions, n=1, cutoff=0.6)
            if matches:
                suggested = True
                original_query = raw_input  # preserve the user's original text
                region_key = matches[0]
                df = self.data[self.data['region'] == region_key]

        # 4) If still empty, return None to indicate no data
        if df.empty:
            return None

        # 5) Build the response payload
        result = {
            'region': region_key.title(),
            'recommended_crops': (
                df[['crop', 'season', 'soil_type']]
                .drop_duplicates()
                .to_dict('records')
            )
        }

        # 6) If we used fuzzy-match fallback, include suggestion metadata
        if suggested:
            result['suggested'] = True
            result['original_query'] = original_query

        return result

    def get_crop_details(self, crop_name):
        """
        Return detailed records for a given crop name.
        """
        # Normalize crop lookup
        key = crop_name.strip().lower()
        df = self.data[self.data['crop'].str.lower() == key]

        if df.empty:
            return None

        return df.drop_duplicates().to_dict('records')
