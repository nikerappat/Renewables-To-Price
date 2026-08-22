# -*- coding: utf-8 -*-

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


"""
Main file for comparing market prices with wind / solar forecasts
"""

from marketprice import get_energycharts_prices
from observations import (
    STATIONS,
    equation_of_time_minutes,
    woz_to_utc,
    load_wind,
    load_solar,
    build_station_dataframe,
    nan_dealer,
    gap_report,
    range_check,
    plot_rolling_mean,
)
prices = get_energycharts_prices("DE-LU", "2023-01-01", "2025-12-31")
prices_hourly = prices.resample("h").mean()
    
def fulldata_df(station: str, prices: pd.DataFrame) -> pd.DataFrame:
    cfg = STATIONS[station]
    df_station = build_station_dataframe(
        cfg["wind_file"],
        cfg["solar_file"],
        cfg["longitude"],
        station
    )

    df_station = nan_dealer(df_station)
    fulldata = df_station.join(prices_hourly, how="inner")

    return fulldata
    
fulldata_arkona = fulldata_df("Arkona", prices_hourly)
fulldata_aachen = fulldata_df("Aachen", prices_hourly)
fulldata_goerlitz = fulldata_df("Görlitz", prices_hourly)
fulldata_zugspitze = fulldata_df("Zugspitze", prices_hourly)

def plot_all_signals(df: pd.DataFrame, station: str) -> None:
    fig, axes = plt.subplots(3, 1, figsize=(14, 10), sharex=True)
    axes[0].plot(df.index, df["price"], color="black")
    axes[0].set_ylabel("Market Price BZN DE-LU (€/MWh)")
    
    axes[1].plot(df.index, df["wind_speed"], color="blue")
    axes[1].set_ylabel("10m wind speed [m/s]")
    
    axes[2].plot(df.index, df["global_solar_radiation"], color="orange")
    axes[2].set_ylabel("global solar radiation J/cm^2")

    fig.suptitle(
    f"Market price vs. solar & wind observations {station}",
    fontsize=14)
        
    plt.tight_layout()
    plt.show()

plot_all_signals(fulldata_arkona,"Arkona")
plot_all_signals(fulldata_aachen, "Aachen")
plot_all_signals(fulldata_goerlitz, "Görlitz")
plot_all_signals(fulldata_zugspitze, "Zugspitze")                


#special case as plots show -500 price
print(fulldata_arkona["price"].min()) #-500
print(fulldata_arkona[fulldata_arkona["price"] == -500.0]) # 2023-07-02 12:00:00+00:00  
print(fulldata_arkona.loc["2023-07-02 12:00:00+00:00"])
# wind_speed                 15.1
# wind_direction            260.0
# global_solar_radiation    259.0
# price                    -500.0
# -> negative price, high wind and high solar radiation

# looking at only timestamps of negative prices
def neg_price_ev(df: pd.DataFrame, station: str) -> None:
    negative_price_hours = df[df["price"] < 0]
    print(f"Anzahl Stunden mit negativem Preis: {len(negative_price_hours)}")
    print(f"Anteil an Gesamtstunden: {len(negative_price_hours) / len(df) * 100:.2f}%")
    print(f"\nDurchschnitt {station} bei negativen Preisen:")
    print(negative_price_hours[["wind_speed", "global_solar_radiation"]].mean())

    print(f"\nDurchschnitt {station} gesamt:")
    print(df[["wind_speed", "global_solar_radiation"]].mean())
    negative_price_hours.groupby(negative_price_hours.index.hour).size().plot(kind="bar")
    plt.title(f"Negative price hours by time of day – {station}")
    plt.show()

neg_price_ev(fulldata_arkona,"Arkona")
neg_price_ev(fulldata_aachen, "Aachen")
neg_price_ev(fulldata_goerlitz, "Görlitz")
neg_price_ev(fulldata_zugspitze, "Zugspitze")    


