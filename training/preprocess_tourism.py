import json
import logging
import os
import sys
import pandas as pd

try:
    from aeon.datasets import load_from_tsf_file
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "aeon"])
    from aeon.datasets import load_from_tsf_file

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    file_path = r"datasets\raw\tourism\tourism_quarterly_dataset.tsf"
    output_path = r"datasets\processed\tourism\tourism_long.parquet"
    summary_path = r"reports\tourism\preprocessing_summary.json"
    
    logger.info(f"Loading dataset from {file_path}")
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return
        
    df, metadata = load_from_tsf_file(
        file_path, 
        return_type="tsf_data", 
        value_column_name="value"
    )
    
    logger.info("Converting to long format...")
    # It is already essentially in long format in aeon 1.5.0 but as a MultiIndex
    df = df.reset_index()
    
    # Add time_index
    df['time_index'] = df.groupby('series_name').cumcount()
    
    # Ensure value is float32
    df['value'] = df['value'].astype('float32')
    
    logger.info(f"Generated {len(df)} rows in long format.")
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    logger.info(f"Saving to {output_path}")
    df.to_parquet(output_path, index=False)
    
    summary = {
        "num_series": int(df['series_name'].nunique()),
        "total_observations": len(df),
        "min_value": float(df['value'].min()),
        "max_value": float(df['value'].max())
    }
    
    os.makedirs(os.path.dirname(summary_path), exist_ok=True)
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=4)
        
    logger.info("Preprocessing complete.")

if __name__ == "__main__":
    main()
