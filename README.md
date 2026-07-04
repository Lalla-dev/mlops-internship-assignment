<<<<<<< HEAD
# MLOps Internship Assignment

## Project Description

This project loads OHLCV data, computes a rolling mean on the close price, generates trading signals, logs execution details, and writes metrics to a JSON file.

## Local Run

```bash
python run.py --input data.csv --config config.yaml --output metrics.json --log-file run.log
```

## Docker Build

```bash
docker build -t mlops-task .
```

## Docker Run

```bash
docker run --rm mlops-task
```

## Example metrics.json

```json
{
  "version": "v1",
  "rows_processed": 10000,
  "metric": "signal_rate",
  "value": 0.4989,
  "latency_ms": 32,
  "seed": 42,
  "status": "success"
}
```
=======
# Rerir
AI-powered Relationship Intelligence CRM that transforms meetings, conversations, and customer interactions into actionable business intelligence.
>>>>>>> 5c484dbaf463c7060754961b821fc3ab18661dbc
