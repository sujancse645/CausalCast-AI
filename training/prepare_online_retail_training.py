import pandas as pd
import json
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    input_path = r"datasets\features\online_retail\online_retail_features.parquet"
    train_path = r"datasets\training\online_retail\train.parquet"
    test_path = r"datasets\training\online_retail\test.parquet"
    features_json = r"datasets\training\online_retail\features.json"
    
    logger.info(f"Loading features from {input_path}")
    if not os.path.exists(input_path):
        logger.error(f"File not found: {input_path}")
        return
        
    df = pd.read_parquet(input_path)
    
    # Sort by Date
    logger.info("Sorting by Date...")
    df = df.sort_values('Date').reset_index(drop=True)
    
    # Exclude non-feature columns
    exclude_cols = {'Date', 'Revenue', 'Transactions', 'Quantity_Sold', 'Unique_Customers', 'Unique_Products'}
    feature_cols = [c for c in df.columns if c not in exclude_cols]
    
    logger.info(f"Identified {len(feature_cols)} features.")
    
    # 80/20 chronological split
    split_idx = int(len(df) * 0.8)
    
    train_df = df.iloc[:split_idx].copy()
    test_df = df.iloc[split_idx:].copy()
    
    logger.info(f"Split data: {len(train_df)} train rows, {len(test_df)} test rows.")
    
    # Save
    os.makedirs(os.path.dirname(train_path), exist_ok=True)
    logger.info("Saving training and testing datasets...")
    train_df.to_parquet(train_path, index=False)
    test_df.to_parquet(test_path, index=False)
    
    logger.info(f"Saving feature list to {features_json}")
    with open(features_json, 'w') as f:
        json.dump(feature_cols, f, indent=4)
        
    logger.info("Train/test split complete.")

if __name__ == "__main__":
    main()
