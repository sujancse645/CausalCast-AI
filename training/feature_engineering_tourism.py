import pandas as pd
import numpy as np
import logging
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    input_path = r"datasets\processed\tourism\tourism_long.parquet"
    output_path = r"datasets\features\tourism\tourism_features.parquet"
    
    logger.info(f"Loading data from {input_path}")
    if not os.path.exists(input_path):
        logger.error(f"File not found: {input_path}")
        return
        
    df = pd.read_parquet(input_path)
    df = df.sort_values(['series_name', 'time_index']).reset_index(drop=True)
    
    logger.info("Generating Calendar Features...")
    # Attempt to extract calendar features if timestamp is datetime
    if pd.api.types.is_datetime64_any_dtype(df['timestamp']):
        df['year'] = df['timestamp'].dt.year
        df['quarter'] = df['timestamp'].dt.quarter
        df['month'] = df['timestamp'].dt.month
    else:
        # If timestamp wasn't parsed as datetime (e.g. integer index), create mock calendar features
        # Assuming quarterly frequency
        df['year'] = (df['time_index'] // 4).astype(np.int32)
        df['quarter'] = (df['time_index'] % 4 + 1).astype(np.int8)
        df['month'] = (df['quarter'] * 3).astype(np.int8)
        
    logger.info("Generating Lag Features...")
    grouped = df.groupby('series_name')['value']
    
    lags = [1, 2, 4, 8]
    for lag in lags:
        df[f'lag_{lag}'] = grouped.shift(lag)
        
    logger.info("Generating Rolling Features...")
    windows = [4, 8]
    for w in windows:
        shifted = grouped.shift(1)
        rolling = shifted.rolling(window=w)
        df[f'rolling_mean_{w}'] = rolling.mean().reset_index(0, drop=True)
        df[f'rolling_std_{w}'] = rolling.std().reset_index(0, drop=True)
        df[f'rolling_min_{w}'] = rolling.min().reset_index(0, drop=True)
        df[f'rolling_max_{w}'] = rolling.max().reset_index(0, drop=True)
        
    logger.info("Generating Expanding Features...")
    shifted = grouped.shift(1)
    expanding = shifted.expanding()
    df['expanding_mean'] = expanding.mean().reset_index(0, drop=True)
    df['expanding_std'] = expanding.std().reset_index(0, drop=True)
    
    logger.info("Dropping NaNs...")
    initial_rows = len(df)
    df = df.dropna()
    logger.info(f"Dropped {initial_rows - len(df)} rows due to NaNs. Remaining: {len(df)}")
    
    # Downcast floats
    float_cols = df.select_dtypes(include=['float64']).columns
    df[float_cols] = df[float_cols].astype('float32')
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    logger.info(f"Saving features to {output_path}")
    df.to_parquet(output_path, index=False)
    logger.info("Feature engineering complete.")

if __name__ == "__main__":
    main()
