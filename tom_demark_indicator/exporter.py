"""Export chart data to JSON and resolve output paths for images."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pandas as pd

# Project-level folder locations (relative to this file's package root)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
IMAGES_DIR = _PROJECT_ROOT / "images"
DATA_DIR = _PROJECT_ROOT / "data"


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def default_image_path(symbol: str, interval: str) -> str:
    """Return a timestamped PNG path inside the images/ folder."""
    IMAGES_DIR.mkdir(exist_ok=True)
    filename = f"{symbol}_{interval}_{_timestamp()}.png"
    return str(IMAGES_DIR / filename)


def save_data_json(df: pd.DataFrame, symbol: str, interval: str) -> str:
    """Serialise the DataFrame (OHLCV + indicators) to a JSON file in data/.

    Filename format: {SYMBOL}_{interval}_{YYYYMMDD_HHMMSS}.json
    Returns the path of the saved file.
    """
    DATA_DIR.mkdir(exist_ok=True)
    filename = f"{symbol}_{interval}_{_timestamp()}.json"
    path = DATA_DIR / filename

    # Reset index so the DatetimeIndex becomes a regular column
    export_df = df.copy()
    export_df.index = export_df.index.strftime("%Y-%m-%dT%H:%M:%S")
    export_df.index.name = "datetime"
    export_df = export_df.reset_index()

    # Convert bool columns to int for clean JSON output
    bool_cols = export_df.select_dtypes(include="bool").columns
    export_df[bool_cols] = export_df[bool_cols].astype(int)

    records = export_df.to_dict(orient="records")
    payload = {
        "symbol": symbol,
        "interval": interval,
        "exported_at": datetime.now().isoformat(),
        "rows": len(records),
        "columns": list(export_df.columns),
        "data": records,
    }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, default=str)

    return str(path)
