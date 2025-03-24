import os
import sys

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../../'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import pandas as pd
from utils.logger import logger

# File paths
RAW_PATH = "/Users/kyleroof/Projects/smart-store-kyleroof/data/raw/sales_data.csv"
PREPARED_DIR = "/Users/kyleroof/Projects/smart-store-kyleroof/data/prepared"
FILE_NAME = "sales_data_prepared.csv"
PREPARED_PATH = os.path.join(PREPARED_DIR, FILE_NAME)

# Allowed payment types
VALID_PAYMENT_TYPES = ['cash', 'debit', 'credit']

def remove_outliers_with_allowlist(df, column_name, multiplier=4.0, allowed_values=None):
    """
    Removes outliers using IQR method but retains specified allowed values.
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
        logger.info("Loaded raw sales data successfully.")

        # Standardize column names
        df.columns = df.columns.str.strip().str.lower()

        # Convert SaleDate to uniform format
        df['saledate'] = pd.to_datetime(df['saledate'], errors='coerce')
        df = df.dropna(subset=['saledate'])
        df['saledate'] = df['saledate'].dt.strftime('%Y-%m-%d')
        logger.info("Standardized 'SaleDate' to YYYY-MM-DD format.")

        # Clean PaymentType
        before = len(df)
        df['paymenttype'] = df['paymenttype'].str.lower().str.strip()
        df = df[df['paymenttype'].isin(VALID_PAYMENT_TYPES)]
        logger.info(f"Removed {before - len(df)} rows with invalid PaymentType values.")

        # Convert SaleAmount and DiscountPercent to numeric
        df['saleamount'] = pd.to_numeric(df['saleamount'], errors='coerce')
        df['discountpercent'] = pd.to_numeric(df['discountpercent'], errors='coerce')
        df = df.dropna(subset=['saleamount', 'discountpercent'])
       
        # Remove outliers in DiscountPercent (but keep 100%)
        df = remove_outliers_with_allowlist(df, 'discountpercent', multiplier=4.0, allowed_values=[100])

        # Reset index
        df = df.reset_index(drop=True)

        # Export cleaned file
        os.makedirs(PREPARED_DIR, exist_ok=True)
        df.to_csv(PREPARED_PATH, index=False)
        logger.info(f"Exported cleaned sales data to {PREPARED_PATH}")

    except Exception as e:
        logger.exception(f"Error during sales data cleaning: {e}")

if __name__ == "__main__":
    clean_data()