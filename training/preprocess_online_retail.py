import pandas as pd
import json
import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    file_path = r"datasets\raw\online_retail\online_retail_II.xlsx"
    output_path = r"datasets\processed\online_retail\online_retail_daily.parquet"
    summary_path = r"reports\online_retail\preprocessing_summary.json"
    
    logger.info(f"Loading dataset from {file_path}")
    
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return
        
    try:
        excel_file = pd.ExcelFile(file_path)
        dfs = [excel_file.parse(sheet) for sheet in excel_file.sheet_names]
        df = pd.concat(dfs, ignore_index=True)
        logger.info(f"Loaded {len(df)} rows.")
    except Exception as e:
        logger.error(f"Error loading Excel file: {e}")
        return
        
    initial_rows = len(df)
    
    # Preprocessing steps
    logger.info("Starting preprocessing...")
    
    # Remove duplicates
    df = df.drop_duplicates()
    no_dupes_rows = len(df)
    logger.info(f"Removed duplicates: {initial_rows - no_dupes_rows} rows.")
    
    # Remove missing CustomerID
    df = df.dropna(subset=['Customer ID'])
    no_missing_cust_rows = len(df)
    logger.info(f"Removed missing CustomerID: {no_dupes_rows - no_missing_cust_rows} rows.")
    
    # Remove cancelled invoices (starts with 'C')
    df = df[~df['Invoice'].astype(str).str.startswith('C')]
    no_cancelled_rows = len(df)
    logger.info(f"Removed cancelled invoices: {no_missing_cust_rows - no_cancelled_rows} rows.")
    
    # Remove negative quantity and price
    df = df[(df['Quantity'] > 0) & (df['Price'] >= 0)]
    clean_rows = len(df)
    logger.info(f"Removed negative quantity/price: {no_cancelled_rows - clean_rows} rows.")
    
    # Convert InvoiceDate to datetime and extract Date
    df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'])
    df['Date'] = df['InvoiceDate'].dt.date
    
    # Create Revenue column
    df['Revenue'] = df['Quantity'] * df['Price']
    
    logger.info("Aggregating by Date...")
    
    # Aggregate by DATE
    # Output: Date, Revenue, Transactions, Quantity Sold, Unique Customers, Unique Products
    daily_df = df.groupby('Date').agg(
        Revenue=('Revenue', 'sum'),
        Transactions=('Invoice', 'nunique'),
        Quantity_Sold=('Quantity', 'sum'),
        Unique_Customers=('Customer ID', 'nunique'),
        Unique_Products=('StockCode', 'nunique')
    ).reset_index()
    
    # Convert Date back to datetime for parquet compatibility
    daily_df['Date'] = pd.to_datetime(daily_df['Date'])
    
    # Downcast floats
    daily_df['Revenue'] = daily_df['Revenue'].astype('float32')
    
    logger.info(f"Aggregated down to {len(daily_df)} daily records.")
    
    logger.info(f"Saving to {output_path}")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    daily_df.to_parquet(output_path, index=False)
    
    summary = {
        "initial_rows": initial_rows,
        "clean_rows": clean_rows,
        "daily_records": len(daily_df),
        "total_revenue": float(daily_df['Revenue'].sum())
    }
    
    os.makedirs(os.path.dirname(summary_path), exist_ok=True)
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=4)
        
    logger.info("Preprocessing complete.")

if __name__ == "__main__":
    main()
