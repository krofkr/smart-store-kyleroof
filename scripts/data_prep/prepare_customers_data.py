import os
import sys

# Dynamically add project root to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../../'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import pandas as pd
import re
from fuzzywuzzy import fuzz
from datetime import datetime
from utils.logger import logger


# File paths
RAW_PATH = "/Users/kyleroof/Projects/smart-store-kyleroof/data/raw/customers_data.csv"
PREPARED_DIR = "/Users/kyleroof/Projects/smart-store-kyleroof/data/prepared"
FILE_NAME = "customers_data_prepared.csv"
PREPARED_PATH = os.path.join(PREPARED_DIR, FILE_NAME)

# Allowed values
VALID_REGIONS = ['North', 'South', 'East', 'West']
VALID_CONTACT_METHODS = ['phone', 'email']

def standardize_name(name):
    return re.sub(' +', ' ', name.strip().title())

def remove_fuzzy_duplicates(df):
    df = df.sort_values(by='JoinDate')
    to_drop = set()
    for i in range(len(df)):
        if i in to_drop:
            continue
        name1 = df.iloc[i]['Name']
        date1 = df.iloc[i]['JoinDate']
        for j in range(i+1, len(df)):
            if j in to_drop:
                continue
            name2 = df.iloc[j]['Name']
            date2 = df.iloc[j]['JoinDate']
            if pd.to_datetime(date1) == pd.to_datetime(date2):
                if fuzz.ratio(name1, name2) > 90:
                    to_drop.add(j)
    logger.info(f"Removed {len(to_drop)} fuzzy duplicate records.")
    return df.drop(df.index[list(to_drop)])

def correct_repeated_pattern(val):
    """
    Detects and fixes repeated-digit patterns like '505050' -> 50
    """
    try:
        val_str = str(int(val))
        match = re.fullmatch(r'(\d{2,3})\1{1,}', val_str)
        if match:
            corrected = int(match.group(1))
            if corrected <= 100:
                logger.info(f"Corrected loyalty points from {val} to {corrected}")
                return corrected
        return val
    except:
        return val

def clean_data():
    try:
        # Load data
        df = pd.read_csv(RAW_PATH)
        logger.info("Loaded raw data successfully.")

        # Standardize column names
        df.columns = df.columns.str.strip()

        # Standardize Name
        df['Name'] = df['Name'].astype(str).apply(standardize_name)

        # Remove fuzzy duplicates with same JoinDate
        df = remove_fuzzy_duplicates(df)

        # Filter valid Region
        before = len(df)
        df = df[df['Region'].isin(VALID_REGIONS)]
        logger.info(f"Removed {before - len(df)} rows with invalid regions.")

        # Fix transmission errors like 505050 -> 50
        df['LoyaltyPoints'] = df['LoyaltyPoints'].apply(correct_repeated_pattern)

        # Convert to numeric and cap at 100
        df['LoyaltyPoints'] = pd.to_numeric(df['LoyaltyPoints'], errors='coerce')
        df['LoyaltyPoints'] = df['LoyaltyPoints'].clip(upper=100)
        logger.info("Standardized and capped loyalty points.")

        # Validate PreferredContactMethod
        before = len(df)
        df['PreferredContactMethod'] = df['PreferredContactMethod'].str.lower().str.strip()
        df = df[df['PreferredContactMethod'].isin(VALID_CONTACT_METHODS)]
        logger.info(f"Removed {before - len(df)} rows with invalid contact methods.")

        # Ensure JoinDate is a valid date
        df['JoinDate'] = pd.to_datetime(df['JoinDate'], errors='coerce')
        df = df.dropna(subset=['JoinDate'])
        logger.info("Validated JoinDate column.")

        # Reset index
        df = df.reset_index(drop=True)

        # Export cleaned file
        os.makedirs(PREPARED_DIR, exist_ok=True)
        df.to_csv(PREPARED_PATH, index=False)
        logger.info(f"Exported cleaned data to {PREPARED_PATH}")

    except Exception as e:
        logger.exception(f"Error during data cleaning: {e}")

if __name__ == "__main__":
    clean_data()