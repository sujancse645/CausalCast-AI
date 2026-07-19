import json
import pandas as pd
import os

def main():
    models = ['lightgbm', 'xgboost', 'catboost']
    results = []
    
    for m in models:
        path = rf"reports\m4_daily\{m}_metrics.json"
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
    
    # Sort by sMAPE and MASE (lower is better)
    df.sort_values(by=['sMAPE', 'MASE'], ascending=[True, True], inplace=True)
    df.reset_index(drop=True, inplace=True)
    
    print("\n--- Model Comparison Table ---")
    cols = ['Model', 'sMAPE', 'MASE', 'MAE', 'RMSE', 'R2', 'train_time_seconds']
    print(df[cols].to_string(index=False))
    
    best_model = df.loc[0, 'Model']
    print(f"\nRecommended Best Model (based on sMAPE/MASE): {best_model.upper()}")
    
    df.to_csv(r"reports\m4_daily\model_comparison.csv", index=False)
    df.to_json(r"reports\m4_daily\model_comparison.json", orient="records", indent=4)
    
    print("Comparison reports saved.")

if __name__ == "__main__":
    main()
