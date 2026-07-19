import json
import logging
import os
import sys
import pandas as pd
import numpy as np

try:
    from aeon.datasets import load_from_tsf_file
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "aeon"])
    from aeon.datasets import load_from_tsf_file

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def convert_to_serializable(obj):
    if isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    elif pd.isna(obj):
        return None
    elif isinstance(obj, (int, float, np.integer, np.floating)):
        return float(obj) if isinstance(obj, (float, np.floating)) else int(obj)
    return str(obj)

def main():
    file_path = r"datasets\raw\tourism\tourism_quarterly_dataset.tsf"
    report_path = r"reports\tourism\inspection_report.json"
    
    logger.info(f"Loading dataset from {file_path}")
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return
        
    df, metadata = load_from_tsf_file(
        file_path, 
        return_type="tsf_data", 
        value_column_name="value"
    )
    
    df = df.reset_index()
    
    frequency = metadata.get("frequency", "quarterly")
    forecast_horizon = metadata.get("horizon", 8)
    contains_missing_values = metadata.get("missing", False)
    
    logger.info("Inspection in progress...")
    
    lengths = df.groupby('series_name').size()
    
    first_five = df.head(5).copy()
    
    inspection = {
        "metadata": metadata,
        "frequency": frequency,
        "forecast_horizon": forecast_horizon,
        "number_of_series": int(df['series_name'].nunique()),
        "columns": list(df.columns),
        "minimum_series_length": int(lengths.min()),
        "maximum_series_length": int(lengths.max()),
        "average_length": float(lengths.mean()),
        "missing_values_flag": bool(contains_missing_values),
        "first_five_series": first_five.to_dict(orient="records")
    }
    
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, 'w') as f:
        json.dump(inspection, f, indent=4, default=convert_to_serializable)
        
    logger.info(f"Inspection report saved to {report_path}")

if __name__ == "__main__":
    main()
