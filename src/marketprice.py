# -*- coding: utf-8 -*-
"""
Created on Sat Aug  8 20:43:14 2026

@author: niker
"""


"""Client for retrieving marketprices via Energy Charts"""

import pandas as pd
import requests
import matplotlib.pyplot as plt

ENERGYCHARTS_URL = "https://api.energy-charts.info/price"
REQUEST_TIMEOUT = 30  # Sekunden


def get_energycharts_prices(bzn: str, start: str, end: str) -> pd.DataFrame:
    """
    Imports hourly Day-Ahead power prices from Energy-Charts.

    """
    params = {"bzn": bzn, "start": start, "end": end}
    response = requests.get(ENERGYCHARTS_URL, params=params, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    data = response.json()

    if "unix_seconds" not in data or "price" not in data:
        raise ValueError(f"unexpected response from Energy Charts: {data}")

    timestamps_raw = data["unix_seconds"]
    prices_raw = data["price"]

    if len(timestamps_raw) != len(prices_raw):
        raise ValueError(
            f"unix_seconds ({len(timestamps_raw)}) and price ({len(prices_raw)}) "
            "are of different lengths"
        )

    df = pd.DataFrame({
        "time": pd.to_datetime(timestamps_raw, unit="s", utc=True),
        "price": pd.to_numeric(prices_raw, errors="coerce"),
    })
    df = df.set_index("time")

    return df


if __name__ == "__main__":
    prices = get_energycharts_prices("DE-LU", "2023-01-01", "2025-12-31")
    print(prices.head())
    print(prices.shape)
    
    prices["RollingMean"] = prices["price"].rolling(window=168, min_periods=1).mean()
    plt.figure(figsize=(10, 6))
    plt.plot(prices.index, prices["price"], label="Original", color="blue", alpha=0.6)
    plt.plot(prices.index, prices["RollingMean"], label=" timesteps Rolling Mean", color="red", linewidth=2)

    # Formatting
    plt.title("Rolling Mean {station} {variable}", fontsize=14)
    plt.xlabel("Date")
    plt.ylabel("{variable}")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()