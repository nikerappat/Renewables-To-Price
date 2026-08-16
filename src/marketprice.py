# -*- coding: utf-8 -*-
"""
Created on Sat Aug  8 20:43:14 2026

@author: niker
"""


"""Client for retrieving marketprices via Energy Charts"""

import pandas as pd
import requests

ENERGYCHARTS_URL = "https://api.energy-charts.info/price"
REQUEST_TIMEOUT = 30  # Sekunden


def get_energycharts_prices(bzn: str, start: str, end: str) -> pd.DataFrame:
    """
    Imports hourly Day-Ahead power prices from Energy-Charts.

    Parameters
    ----------
    bzn : str
        Bidding-Zone-Code, e.g. "DE-LU".
    start, end : str
        date in format "YYYY-MM-DD".

    Returns
    -------
    pd.DataFrame
        Index: time (UTC, tz-aware), column: price.
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
    prices = get_energycharts_prices("DE-LU", "2025-01-01", "2025-01-02")
    print(prices.head())
    print(prices.shape)