# Real forecast validation

All values below were executed from existing trained artifacts over authentic held-out rows.
They are estimates, not guaranteed future outcomes.

| Dataset | Model | Direct status | API status | API horizon | API first five predictions |
|---|---|---|---|---:|---|
| Rossmann Store Sales | rossmann_xgboost_v1 | passed | passed (200) | 5 | 10138642.9429, 8725303.1902, 8462087.3726, 8996482.6123, 10068999.7451 |
| Electricity Load | lightgbm_electricity | passed | passed (200) | 5 | 665079.2828, 654805.6716, 710126.9333, 569879.7222, 487847.3448 |
| M4 Daily | lightgbm_m4 | passed | passed (200) | 5 | 2051.3367, 2052.1355, 2052.1355, 2052.1355, 2095.2444 |
| Online Retail II | xgboost_model | passed | passed (200) | 5 | 31080.3359, 40461.5039, 42062.4766, 40116.9414, 32519.0000 |
| Tourism (yearly source) | xgboost_model | passed | passed (200) | 5 | 17382.8438, 8628.4297, 6559.2251, 9671.4746, 18378.2422 |
