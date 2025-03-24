import os
import sys

# Add project root to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../../'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import pandas as pd
from utils.logger import logger

# File paths
RAW_PATH = "/Users/kyleroof/Projects/smart-store-kyleroof/data/raw/products_data.csv"
PREPARED_DIR = "/Users/kyleroof/Projects/smart-store-kyleroof/data/prepared"
FILE_NAME = "products_data_prepared.csv"
PREPARED_PATH = os.path.join(PREPARED_DIR, FILE_NAME)

# Valid values
VALID_PRODUCT_NAMES = ['laptop', 'hoodie', 'cable', 'hat', 'football', 'controller', 'jacket', 'protector']
VALID_CATEGORIES = ['Electronics', 'Clothing', 'Sports']

def remove_outliers_with_allowlist(df, column_name, multiplier=4.0, allowed_values=None):
    """
    Removes outliers based on IQR, but keeps any value in the allowed_values list.
    """
    q1 = df[column_name].quantile(0.25)
    q3 = df[column_name].quantile(0.75)
    iqr = q3 - q1
    lower = q1 - multiplier * iqr
    upper = q3 + multiplier * iqr

    if allowed_values is None:
        allowed_values = []

    before = len(df)
    mask = (df[column_name] >= lower) & (df[column_name] <= upper)
    allowed_mask = df[column_name].isin(allowed_values)
    final_mask = mask | allowed_mask

    removed = before - final_mask.sum()
    if removed > 0:
        logger.info(f"Removed {removed} outliers from '{column_name}' using IQR x{multiplier}, keeping allowed values: {allowed_values}")
    return df[final_mask]

def clean_data():
    try:
        # Load data
        df = pd.read_csv(RAW_PATH)
        logger.info("Loaded raw products data successfully.")

        # Standardize column names
        df.columns = df.columns.str.strip()

        # Standardize product names to lowercase for comparison
        df['ProductName'] = df['ProductName'].astype(str).str.lower().str.strip()
        before = len(df)
        df = df[df['ProductName'].isin(VALID_PRODUCT_NAMES)]
        logger.info(f"Removed {before - len(df)} rows with invalid product names.")

        # Validate category
        before = len(df)
        df['Category'] = df['Category'].astype(str).str.strip()
        df = df[df['Category'].isin(VALID_CATEGORIES)]
        logger.info(f"Removed {before - len(df)} rows with invalid categories.")

        # Convert numerical columns
        df['UnitPrice'] = pd.to_numeric(df['UnitPrice'], errors='coerce')
        df['StockQuantity'] = pd.to_numeric(df['StockQuantity'], errors='coerce')

        # Drop rows with NaN in those critical columns
        df = df.dropna(subset=['UnitPrice', 'StockQuantity'])

        # Remove outliere
        df = remove_outliers_with_allowlist(df, 'UnitPrice', multiplier=4.0, allowed_values=[793.12])
        df = remove_outliers_with_allowlist(df, 'StockQuantity', multiplier=4.0)

        # Reset index
        df = df.reset_index(drop=True)

        # Export cleaned data
        os.makedirs(PREPARED_DIR, exist_ok=True)
        df.to_csv(PREPARED_PATH, index=False)
        logger.info(f"Exported cleaned products data to {PREPARED_PATH}")

    except Exception as e:
        logger.exception(f"Error during products data cleaning: {e}")

if __name__ == "__main__":
    clean_data()