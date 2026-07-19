import pandas as pd
import json
import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def convert_to_serializable(obj):
    if isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    elif pd.isna(obj):
        return None
    elif isinstance(obj, (int, float)):
        return obj
    return str(obj)

def main():
    file_path = r"datasets\raw\online_retail\online_retail_II.xlsx"
    report_path = r"reports\online_retail\inspection_report.json"
    
    logger.info(f"Loading dataset from {file_path}")
    
    # Check if file exists, if not, create a dummy or handle the error
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return
        
    try:
        # Load all sheets
        excel_file = pd.ExcelFile(file_path)
        logger.info(f"Found sheets: {excel_file.sheet_names}")
        
        dfs = []
        for sheet in excel_file.sheet_names:
            logger.info(f"Loading sheet: {sheet}")
            dfs.append(excel_file.parse(sheet))
            
        df = pd.concat(dfs, ignore_index=True)
        logger.info("Sheets merged successfully.")
        
    except Exception as e:
        logger.error(f"Error loading Excel file: {e}")
        return
        
    logger.info("Performing inspection...")
    
    # Calculate revenue for stats
    df['Revenue'] = df['Quantity'] * df['Price']
    
    inspection = {
        "dataset_shape": list(df.shape),
        "column_names": list(df.columns),
        "data_types": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "null_values": df.isnull().sum().to_dict(),
        "duplicate_rows": int(df.duplicated().sum()),
        "unique_customers": int(df['Customer ID'].nunique()),
        "unique_products": int(df['StockCode'].nunique()),
        "date_range": {
            "start": df['InvoiceDate'].min(),
            "end": df['InvoiceDate'].max()
        },
        "invoice_types": {
            "total": int(df['Invoice'].nunique()),
            "cancelled": int(df['Invoice'].astype(str).str.startswith('C').sum())
        },
        "negative_quantities_count": int((df['Quantity'] < 0).sum()),
        "negative_prices_count": int((df['Price'] < 0).sum()),
        "revenue_statistics": {
            "min": float(df['Revenue'].min()),
            "max": float(df['Revenue'].max()),
            "mean": float(df['Revenue'].mean()),
            "sum": float(df['Revenue'].sum())
        }
    }
    
    logger.info(f"Saving inspection report to {report_path}")
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, 'w') as f:
        json.dump(inspection, f, indent=4, default=convert_to_serializable)
        
    logger.info("Inspection complete.")

if __name__ == "__main__":
    main()
