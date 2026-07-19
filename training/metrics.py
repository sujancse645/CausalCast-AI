import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

def smape(y_true, y_pred):
    denominator = (np.abs(y_true) + np.abs(y_pred)) / 2.0
    diff = np.abs(y_true - y_pred) / denominator
    diff[denominator == 0] = 0.0
    return np.mean(diff) * 100

def calculate_metrics(y_true, y_pred, df_test=None):
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    r2 = r2_score(y_true, y_pred)
    sm = smape(y_true, y_pred)
    
    # Calculate MAPE
    non_zero = y_true != 0
    if np.any(non_zero):
        mape = np.mean(np.abs((y_true[non_zero] - y_pred[non_zero]) / y_true[non_zero])) * 100
    else:
        mape = np.nan
    
    # Calculate MASE: using naive forecast (lag_1) on the test set if available
    if df_test is not None and 'lag_1' in df_test.columns:
        naive_mae = mean_absolute_error(y_true, df_test['lag_1'])
        mase = mae / naive_mae if naive_mae > 0 else np.nan
    else:
        mase = np.nan
        
    return {
        "MAE": float(mae),
        "RMSE": float(rmse),
        "R2": float(r2),
        "sMAPE": float(sm),
        "MAPE": float(mape),
        "MASE": float(mase) if not np.isnan(mase) else None
    }
