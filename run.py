import argparse
import json
import logging
import time

import numpy as np
import pandas as pd
import yaml


logger = logging.getLogger("mlops_job")


def load_settings(path):
    with open(path, "r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def main():
    parser = argparse.ArgumentParser(description="Simple batch job for the internship assignment")
    parser.add_argument("--input", required=True, help="Path to the input CSV file")
    parser.add_argument("--config", required=True, help="Path to the YAML config file")
    parser.add_argument("--output", required=True, help="Where the metrics JSON should be written")
    parser.add_argument("--log-file", required=True, help="Path to the log file")
    args = parser.parse_args()

    logging.basicConfig(
        filename=args.log_file,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    logger.info("Starting the job")
    start_time = time.perf_counter()
    settings = None

    try:
        settings = load_settings(args.config)

        required_keys = ["seed", "window", "version"]
        missing = [key for key in required_keys if key not in settings]
        if missing:
            raise ValueError(f"Missing config fields: {', '.join(missing)}")

        if not isinstance(settings["window"], (int, float)) or settings["window"] <= 0:
            raise ValueError("The window size needs to be a positive number.")

        np.random.seed(settings["seed"])
        logger.info("Config loaded for this run")

        frame = load_market_data(args.input)
        logger.info("Loaded %s rows from the dataset", len(frame))
        validate_market_data(frame)
        logger.info("Dataset checks passed")

        frame = add_signal(frame, settings["window"])
        signal_rate = frame["signal"].mean()
        elapsed_ms = int((time.perf_counter() - start_time) * 1000)

        metrics = {
            "version": settings["version"],
            "rows_processed": len(frame),
            "metric": "signal_rate",
            "value": round(signal_rate, 4),
            "latency_ms": elapsed_ms,
            "seed": settings["seed"],
            "status": "success",
        }

        write_json(args.output, metrics)
        print(json.dumps(metrics, indent=4))
        logger.info("Finished successfully")

    except Exception as exc:
        elapsed_ms = int((time.perf_counter() - start_time) * 1000)
        error_metrics = {
            "version": settings.get("version", "unknown") if settings is not None else "unknown",
            "rows_processed": 0,
            "metric": "signal_rate",
            "value": None,
            "latency_ms": elapsed_ms,
            "seed": settings.get("seed") if settings is not None else None,
            "status": "error",
            "error_message": str(exc),
        }

        write_json(args.output, error_metrics)
        print(json.dumps(error_metrics, indent=4))
        logger.error("Job failed: %s", exc)
        raise


def load_market_data(path):
    try:
        frame = pd.read_csv(path)

        if len(frame.columns) == 1:
            frame = frame.iloc[:, 0].str.split(",", expand=True)

        frame.columns = [
            "timestamp",
            "open",
            "high",
            "low",
            "close",
            "volume_btc",
            "volume_usd",
        ]

        frame["timestamp"] = pd.to_datetime(frame["timestamp"])

        numeric_columns = ["open", "high", "low", "close", "volume_btc", "volume_usd"]
        frame[numeric_columns] = frame[numeric_columns].astype(float)
    except FileNotFoundError as exc:
        raise ValueError("Input file not found.") from exc
    except pd.errors.EmptyDataError as exc:
        raise ValueError("CSV file is empty.") from exc
    except Exception as exc:
        raise ValueError(f"Invalid CSV format: {exc}") from exc

    return frame


def validate_market_data(frame):
    if frame.empty:
        raise ValueError("Dataset is empty.")

    if "close" not in frame.columns:
        raise ValueError("Required column 'close' not found.")

    if frame["close"].isnull().any():
        raise ValueError("Column 'close' contains missing values.")

    if not pd.api.types.is_numeric_dtype(frame["close"]):
        raise ValueError("'close' column must be numeric.")


def add_signal(frame, window):
    frame["rolling_mean"] = frame["close"].rolling(window=window).mean()
    frame["signal"] = (frame["close"] > frame["rolling_mean"]).astype(int)
    return frame


def write_json(path, payload):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=4)


if __name__ == "__main__":
    main()