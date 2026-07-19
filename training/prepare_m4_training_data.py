import pandas as pd
import numpy as downcast
import json
import os
import gc

def main():
    features_path = r"datasets\features\m4_daily\m4_features.parquet"
    print(f"Loading data from {features_path}...")
    df = pd.read_parquet(features_path)
    
    # Downcast floats to float32
    float_cols = df.select_dtypes(include=['float64']).columns
    df[float_cols] = df[float_cols].astype('float32')
    print("Downcasted float64 to float32.")
    
    # Sort
    print("Sorting by series_name and time_index...")
    df.sort_values(by=['series_name', 'time_index'], inplace=True)
    df.reset_index(drop=True, inplace=True)
    
    # Split: last 14 rows per series as test
    print("Splitting into train and test sets...")
    test_mask = df.groupby('series_name').tail(14).index
    df_test = df.loc[test_mask].copy()
    df_train = df.drop(test_mask).copy()
    
    del df
    gc.collect()
    
    # Sample training
    if len(df_train) > 2000000:
        print(f"Sampling training data from {len(df_train)} to 2,000,000 rows...")
        df_train = df_train.sample(n=2000000, random_state=42)
    else:
        print(f"Training data size ({len(df_train)}) is within limits. No sampling needed.")
        
    df_train.reset_index(drop=True, inplace=True)
    df_test.reset_index(drop=True, inplace=True)
    
    # Features
    exclude_cols = {'series_name', 'timestamp', 'value'}
    feature_cols = [c for c in df_train.columns if c not in exclude_cols]
    
    print(f"Number of feature columns: {len(feature_cols)}")
    
    # Save
    train_out = r"datasets\training\m4_daily\m4_train.parquet"
    test_out = r"datasets\training\m4_daily\m4_test.parquet"
    features_out = r"reports\m4_daily\m4_feature_columns.json"
    summary_out = r"reports\m4_daily\data_split_summary.json"
    
    print("Saving datasets...")
    df_train.to_parquet(train_out, index=False)
    df_test.to_parquet(test_out, index=False)
    
    print("Saving metadata...")
    with open(features_out, 'w') as f:
        json.dump(feature_cols, f, indent=4)
        
    summary = {
        "train_rows": len(df_train),
        "test_rows": len(df_test),
        "num_features": len(feature_cols)
    }
    with open(summary_out, 'w') as f:
        json.dump(summary, f, indent=4)
        
    print("Preparation complete!")

if __name__ == "__main__":
    main()
