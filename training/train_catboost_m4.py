import pandas as pd
import json
import time
import os
import joblib
from catboost import CatBoostRegressor
from metrics import calculate_metrics

def main():
    print("Loading prepared datasets...")
    df_train = pd.read_parquet(r"datasets\training\m4_daily\m4_train.parquet")
    df_test = pd.read_parquet(r"datasets\training\m4_daily\m4_test.parquet")
    
    with open(r"reports\m4_daily\m4_feature_columns.json", 'r') as f:
        feature_cols = json.load(f)
        
    print(f"Train shape: {df_train.shape}")
    print(f"Test shape: {df_test.shape}")
    print(f"Training row count: {len(df_train)}")
    print(f"Test row count: {len(df_test)}")
    print(f"Feature count: {len(feature_cols)}")
    
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
    
    print("Training CatBoost model...")
    start_time = time.time()
    model.fit(X_train, y_train)
    train_time = time.time() - start_time
    print(f"Training completed in {train_time:.2f} seconds.")
    
    print("Predicting on test data...")
    y_pred = model.predict(X_test)
    
    metrics = calculate_metrics(y_test, y_pred, df_test)
    metrics['train_time_seconds'] = train_time
    
    print("Metrics:")
    for k, v in metrics.items():
        print(f"  {k}: {v:.4f}")
        
    print("Saving artifacts...")
    joblib.dump(model, r"models\m4_daily\catboost_m4.pkl")
    
    with open(r"reports\m4_daily\catboost_metrics.json", 'w') as f:
        json.dump(metrics, f, indent=4)
        
    df_pred = df_test[['series_name', 'time_index', 'value']].copy()
    df_pred['prediction'] = y_pred
    df_pred.to_parquet(r"reports\m4_daily\catboost_predictions.parquet", index=False)
    
    print("CatBoost pipeline complete!")

if __name__ == "__main__":
    main()
