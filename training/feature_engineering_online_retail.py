import pandas as pd
import numpy as np
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    input_path = r"datasets\processed\online_retail\online_retail_daily.parquet"
    output_path = r"datasets\features\online_retail\online_retail_features.parquet"
    
    logger.info(f"Loading data from {input_path}")
    if not os.path.exists(input_path):
        logger.error(f"File not found: {input_path}")
        return
        
    df = pd.read_parquet(input_path)
    df = df.sort_values('Date').reset_index(drop=True)
    
    logger.info("Generating Calendar Features...")
    df['Year'] = df['Date'].dt.year
    df['Month'] = df['Date'].dt.month
    df['Quarter'] = df['Date'].dt.quarter
    df['Week'] = df['Date'].dt.isocalendar().week.astype('int32')
    df['Day'] = df['Date'].dt.day
    df['Weekday'] = df['Date'].dt.weekday
    df['DayOfYear'] = df['Date'].dt.dayofyear
    df['IsWeekend'] = df['Weekday'].isin([5, 6]).astype('int8')
    
    logger.info("Generating Lag Features...")
    lags = [1, 2, 3, 7, 14, 28]
    for lag in lags:
        df[f'lag_{lag}'] = df['Revenue'].shift(lag)
        
    logger.info("Generating Rolling Features...")
    windows = [7, 14, 28]
    for w in windows:
        # We must shift by 1 to avoid leakage (rolling features should only use past data)
        shifted_revenue = df['Revenue'].shift(1)
        rolling = shifted_revenue.rolling(window=w)
        df[f'rolling_mean_{w}'] = rolling.mean()
        df[f'rolling_std_{w}'] = rolling.std()
        df[f'rolling_min_{w}'] = rolling.min()
        df[f'rolling_max_{w}'] = rolling.max()
        
    logger.info("Generating Expanding Features...")
    shifted_revenue = df['Revenue'].shift(1)
    expanding = shifted_revenue.expanding()
    df['expanding_mean'] = expanding.mean()
    df['expanding_std'] = expanding.std()
    
    logger.info("Dropping NaNs...")
    initial_rows = len(df)
    df = df.dropna()
    logger.info(f"Dropped {initial_rows - len(df)} rows due to NaNs. Remaining: {len(df)}")
    
    # Downcast floats
    float_cols = df.select_dtypes(include=['float64']).columns
    df[float_cols] = df[float_cols].astype('float32')
    
    logger.info(f"Saving features to {output_path}")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_parquet(output_path, index=False)
    logger.info("Feature engineering complete.")

if __name__ == "__main__":
    main()
