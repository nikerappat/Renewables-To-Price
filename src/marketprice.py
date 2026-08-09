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


def get_energycharts_prices(
    bzn: str,
    start: str,
    end: str
) -> pd.DataFrame:

    
    params = {
        "bzn": bzn,
        "start": start,
        "end": end
        }
    response = requests.get(ENERGYCHARTS_URL, params=params, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    data = response.json()


    if "unix_seconds" not in data or "price" not in data:
        raise ValueError(
            f"Unexpected response from Energy Charts: {data}"
        )
        
    
    hourly_data=data["unix_seconds"]
    hourly_data = pd.to_datetime(hourly_data, unit="s")
    prices = data["price"]
    df = pd.DataFrame({
        "time": hourly_data,
        "price": prices,
    })
    
    return df


if __name__ == "__main__":
    prices = get_energycharts_prices(

        "DE-LU",
        "2025-01-01",
        "2025-01-02"
    )
    print(prices.head())
    print(prices.shape)