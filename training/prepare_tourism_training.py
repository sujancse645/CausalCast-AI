import pandas as pd
import json
import logging
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    input_path = r"datasets\features\tourism\tourism_features.parquet"
    train_path = r"datasets\training\tourism\train.parquet"
    test_path = r"datasets\training\tourism\test.parquet"
    features_json = r"datasets\training\tourism\features.json"
    summary_path = r"datasets\training\tourism\split_summary.json"
    inspection_path = r"reports\tourism\inspection_report.json"
    
    logger.info(f"Loading features from {input_path}")
    if not os.path.exists(input_path):
        logger.error(f"File not found: {input_path}")
        return
        
    df = pd.read_parquet(input_path)
    
    # Sort by series_name and time_index
    logger.info("Sorting by series_name and time_index...")
    df = df.sort_values(['series_name', 'time_index']).reset_index(drop=True)
    
    # Exclude non-feature columns
    exclude_cols = {'series_name', 'timestamp', 'time_index', 'value'}
    feature_cols = [c for c in df.columns if c not in exclude_cols]
    
    logger.info(f"Identified {len(feature_cols)} features.")
    
    # Read forecast horizon
    try:
        with open(inspection_path, 'r') as f:
            inspection = json.load(f)
            forecast_horizon = int(inspection.get('forecast_horizon', 8)) # default to 8 if not found
    except Exception as e:
        logger.warning(f"Could not read forecast horizon from {inspection_path}, defaulting to 8. Error: {e}")
        forecast_horizon = 8
        
    logger.info(f"Using forecast horizon: {forecast_horizon} as test set per series.")
    
    # Split: last H observations per series as test
    test_mask = df.groupby('series_name').tail(forecast_horizon).index
    test_df = df.loc[test_mask].copy()
    train_df = df.drop(test_mask).copy()
    
    logger.info(f"Split data: {len(train_df)} train rows, {len(test_df)} test rows.")
    
    # Save
    os.makedirs(os.path.dirname(train_path), exist_ok=True)
    logger.info("Saving training and testing datasets...")
    train_df.to_parquet(train_path, index=False)
    test_df.to_parquet(test_path, index=False)
    
    logger.info(f"Saving feature list to {features_json}")
    with open(features_json, 'w') as f:
        json.dump(feature_cols, f, indent=4)
        
    summary = {
        "train_rows": len(train_df),
        "test_rows": len(test_df),
        "num_features": len(feature_cols),
        "forecast_horizon": forecast_horizon
    }
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=4)
        
    logger.info("Train/test split complete.")

if __name__ == "__main__":
    main()
