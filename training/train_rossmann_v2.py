data = data.sort_values(["Store", "Date"]).copy()

for lag in [1, 7, 14, 28]:
    data[f"sales_lag_{lag}"] = (
        data.groupby("Store")["Sales"].shift(lag)
    )

data["sales_rolling_mean_7"] = (
    data.groupby("Store")["Sales"]
    .transform(lambda series: series.shift(1).rolling(7).mean())
)

data["sales_rolling_mean_28"] = (
    data.groupby("Store")["Sales"]
    .transform(lambda series: series.shift(1).rolling(28).mean())
)

data["sales_rolling_std_7"] = (
    data.groupby("Store")["Sales"]
    .transform(lambda series: series.shift(1).rolling(7).std())
)

lag_columns = [
    "sales_lag_1",
    "sales_lag_7",
    "sales_lag_14",
    "sales_lag_28",
    "sales_rolling_mean_7",
    "sales_rolling_mean_28",
    "sales_rolling_std_7",
]

data = data.dropna(subset=lag_columns).copy()