# RAG validation

- Indexed documents: 43
- Chunks: 6460
- Embedding dimension: 384
- Generator: deterministic_grounded_fallback
- Live chat/search HTTP status: 200/200
- Live reindex HTTP status: 200

## Which model performs best for Tourism Quarterly?

According to the Tourism model comparison, xgboost has the lowest RMSE (123264).

Sources: reports/tourism/model_comparison.json

## What are the Electricity forecasting metrics?

For Electricity, the lowest-RMSE model is LightGBM; its reported metrics are MAE 17181.7, RMSE 25892.7, R2 0.994.

Sources: reports/electricity/model_comparison.csv

## Which datasets are supported?

The validated forecasting datasets are: Rossmann Store Sales, Electricity Load, M4 Daily, Online Retail II, Tourism (yearly source).

Sources: reports/integration/real_forecast_validation.json

## How does the forecasting API work?

`GET /api/v1/forecasting/models` returns the stable baseline registry. `GET /api/v1/forecasting/stats` returns real aggregate experiment statistics. `GET /api/v1/reports/{dataset}` returns the selected comparison record.

Sources: docs/api.md

## What is the architecture of the RAG system?

See [RAG architecture](docs/RAG.md). The RAG subsystem is independent from forecasting and indexes only project knowledge. It excludes environments, dependencies, models, raw/processed/features datasets, vector storage, caches, oversized files, and its own RAG validation reports.

Sources: README.md, docs/RAG.md

## What is the private launch code for the CausalCast Mars mission?

I could not find that information in the project.

Sources: none
