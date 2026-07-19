from pathlib import Path

import joblib
import pandas as pd
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)
from lightgbm import LGBMRegressor


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA = (
    PROJECT_ROOT
    / "datasets"
    / "features"
    / "electricity"
    / "electricity_features.csv"
)

MODEL_DIR = (
    PROJECT_ROOT
    / "models"
    / "electricity"
)

MODEL_DIR.mkdir(parents=True, exist_ok=True)

MODEL_PATH = MODEL_DIR / "lightgbm_electricity.pkl"

print("=" * 80)
print("TRAINING LIGHTGBM")
print("=" * 80)

df = pd.read_csv(DATA)

target = "total_load"

X = df.drop(columns=["timestamp", target])
y = df[target]

split = int(len(df) * 0.8)

X_train = X.iloc[:split]
X_test = X.iloc[split:]

y_train = y.iloc[:split]
y_test = y.iloc[split:]

print(f"Training Samples : {len(X_train)}")
print(f"Testing Samples  : {len(X_test)}")

model = LGBMRegressor(
    n_estimators=500,
    learning_rate=0.05,
    num_leaves=31,
    random_state=42
)

print("\nTraining...\n")

model.fit(X_train, y_train)

pred = model.predict(X_test)

mae = mean_absolute_error(y_test, pred)
rmse = mean_squared_error(y_test, pred) ** 0.5
r2 = r2_score(y_test, pred)

print("=" * 80)
print("RESULTS")
print("=" * 80)

print(f"MAE  : {mae:.2f}")
print(f"RMSE : {rmse:.2f}")
print(f"R²   : {r2:.4f}")

joblib.dump(model, MODEL_PATH)

print("\nModel saved to:")
print(MODEL_PATH)