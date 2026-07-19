import pandas as pd
import json
import time
import os
import joblib
import logging
from catboost import CatBoostRegressor

import sys
sys.path.append(os.path.dirname(__file__))
from metrics import calculate_metrics

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    logger.info("Loading training and testing datasets...")
    df_train = pd.read_parquet(r"datasets\training\tourism\train.parquet")
    df_test = pd.read_parquet(r"datasets\training\tourism\test.parquet")
    
    with open(r"datasets\training\tourism\features.json", 'r') as f:
        feature_cols = json.load(f)
        
    X_train = df_train[feature_cols]
    y_train = df_train['value']
    
    X_test = df_test[feature_cols]
    y_test = df_test['value']
    
    model = CatBoostRegressor(
        loss_function='RMSE',
        iterations=500,
        learning_rate=0.05,
        depth=8,
        thread_count=-1,
        verbose=False,
        random_seed=42
    )
    
    logger.info("Training CatBoost model...")
    start_time = time.time()
    model.fit(X_train, y_train)
    train_time = time.time() - start_time
    logger.info(f"Training completed in {train_time:.2f} seconds.")
    
    logger.info("Predicting on test data...")
    y_pred = model.predict(X_test)
    
    metrics = calculate_metrics(y_test, y_pred, df_test)
    metrics['train_time_seconds'] = train_time
    
    logger.info("Metrics:")
    for k, v in metrics.items():
        logger.info(f"  {k}: {v}")
        
    logger.info("Saving artifacts...")
    os.makedirs(r"models\tourism", exist_ok=True)
    os.makedirs(r"reports\tourism", exist_ok=True)
    
    joblib.dump(model, r"models\tourism\catboost_model.pkl")
    
    with open(r"reports\tourism\catboost_metrics.json", 'w') as f:
        json.dump(metrics, f, indent=4)
        
    df_pred = df_test[['series_name', 'time_index', 'value']].copy()
    df_pred['prediction'] = y_pred
    df_pred.to_parquet(r"reports\tourism\catboost_predictions.parquet", index=False)
    
    logger.info("CatBoost pipeline complete.")

if __name__ == "__main__":
    main()
