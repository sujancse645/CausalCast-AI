import json
import pandas as pd
import os

def main():
    models = ['lightgbm', 'xgboost', 'catboost']
    results = []
    
    for m in models:
        path = rf"reports\tourism\{m}_metrics.json"
        if os.path.exists(path):
            with open(path, 'r') as f:
                metrics = json.load(f)
                metrics['Model'] = m
                results.append(metrics)
        else:
            print(f"Warning: {path} not found.")
            
    if not results:
        print("No metrics found to compare.")
        return
        
    df = pd.DataFrame(results)
    
    # Sort by RMSE, MAE, sMAPE
    df.sort_values(by=['RMSE', 'MAE', 'sMAPE'], ascending=[True, True, True], inplace=True)
    df.reset_index(drop=True, inplace=True)
    
    print("\n--- Model Comparison Table ---")
    cols = ['Model', 'RMSE', 'MAE', 'sMAPE', 'MAPE', 'MASE', 'R2', 'train_time_seconds']
    # Filter only existing columns just in case
    available_cols = [c for c in cols if c in df.columns]
    print(df[available_cols].to_string(index=False))
    
    best_model = df.loc[0, 'Model']
    print(f"\nRecommended Best Model (based on RMSE/MAE): {best_model.upper()}")
    
    df.to_csv(r"reports\tourism\model_comparison.csv", index=False)
    df.to_json(r"reports\tourism\model_comparison.json", orient="records", indent=4)
    
    print("Comparison reports saved.")

if __name__ == "__main__":
    main()
