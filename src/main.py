# -*- coding: utf-8 -*-

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


"""
Main file for comparing market prices with wind / solar forecasts
"""
# --------------------------------------------------------------------------
# 1) Load Data & Functions from other scripts
# --------------------------------------------------------------------------
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

# --------------------------------------------------------------------------
# 2) Combine Market Information and Wind / Solar Observations
# --------------------------------------------------------------------------
    
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

# --------------------------------------------------------------------------
# 3) First Visualisation of Raw Data
# --------------------------------------------------------------------------
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

# --------------------------------------------------------------------------
# 3.1) Exkurs
# --------------------------------------------------------------------------
# calculation for Arkona for an example of a price of -500 (absolute minimum)
# print(fulldata_arkona["price"].min()) #-500
# print(fulldata_arkona[fulldata_arkona["price"] == -500.0]) # 2023-07-02 12:00:00+00:00  
# print(fulldata_arkona.loc["2023-07-02 12:00:00+00:00"])
# wind_speed                 15.1
# wind_direction            260.0
# global_solar_radiation    259.0
# price                    -500.0
# -> negative price, high wind and high solar radiation

# --------------------------------------------------------------------------
# 4) Analysing negative prices
# --------------------------------------------------------------------------
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

# --------------------------------------------------------------------------
# 5) Correlate prices with observational data
# --------------------------------------------------------------------------
def pearson_corr(df: pd.DataFrame, station: str) -> None:
    r = df.corr()["price"].drop("price")
    print(f"\nPearson-correlation full timeframe – {station}")
    print(r)
    
    # negative_price_hours = df[df["price"] < 0]
    # r_neg = negative_price_hours.corr()["price"].drop("price")
    # print(f"Number of negative-price hours: {len(negative_price_hours)}")
    # print(f"\nPearson-correlation only times of negative prices – {station}")
    # print(r_neg)
    
pearson_corr(fulldata_arkona, "Arkona")
pearson_corr(fulldata_aachen, "Aachen")
pearson_corr(fulldata_goerlitz, "Görlitz")
pearson_corr(fulldata_zugspitze, "Zugspitze")

# --------------------------------------------------------------------------
# 6) Visualisation of correlation
# --------------------------------------------------------------------------
# wind data
def plot_wind_corr(df: pd.DataFrame, station: str) -> None:
    df = df.copy()
    df = df.dropna(subset=["wind_speed"])
    x = df["wind_speed"]
    y = df["price"]
    r = x.corr(y)
    
    negative_prices = df["price"] < 0
    neg_x = df["wind_speed"][negative_prices]
    neg_y = df["price"][negative_prices]
    
    plt.scatter(x, y, color="green", alpha=0.1, s=5)
    plt.scatter(neg_x, neg_y, color="red", s=10)
    
    a, b = np.polyfit(x, y, 1)
    
    x_line = np.linspace(x.min(), x.max(), 100)
    plt.plot(x_line, a * x_line + b, color="black", linewidth=4)
    
    plt.xlabel("wind speed [m/s]")
    plt.ylabel("Market Price BZN DE-LU (€/MWh)")
    plt.title(f"Market Price vs. Wind Speed – {station}")
    plt.text(
    0.05, 0.95,
    f"Pearson r = {r:.3f}",
    transform=plt.gca().transAxes)
    plt.savefig(
    f"plots/wind_corr_{station.lower()}.png",
    dpi=300,
    bbox_inches="tight")
    plt.show()

plot_wind_corr(fulldata_arkona, "Arkona")
plot_wind_corr(fulldata_aachen, "Aachen")
plot_wind_corr(fulldata_goerlitz, "Görlitz")
plot_wind_corr(fulldata_zugspitze, "Zugspitze")

#solar data
def plot_solar_corr(df: pd.DataFrame, station: str) -> None:
    df = df.copy()
    df = df.dropna(subset=["global_solar_radiation"])
    x = df["global_solar_radiation"]
    y = df["price"]
    r = x.corr(y)
    
    negative_prices = df["price"] < 0
    neg_x = df["global_solar_radiation"][negative_prices]
    neg_y = df["price"][negative_prices]
    
    plt.scatter(x, y, color="green", alpha=0.1, s=5)
    plt.scatter(neg_x, neg_y, color="red", s=10)
    
    a, b = np.polyfit(x, y, 1)
    
    x_line = np.linspace(x.min(), x.max(), 100)
    plt.plot(x_line, a * x_line + b, color="black", linewidth=4)
    
    plt.xlabel("global solar radiation J/cm^2")
    plt.ylabel("Market Price BZN DE-LU (€/MWh)")
    plt.title(f"Market Price vs. Global Solar radiation – {station}")
    plt.text(
    0.05, 0.95,
    f"Pearson r = {r:.3f}",
    transform=plt.gca().transAxes)
    plt.savefig(
    f"plots/solar_corr_{station.lower()}.png",
    dpi=300,
    bbox_inches="tight")
    plt.show()

plot_solar_corr(fulldata_arkona, "Arkona")
plot_solar_corr(fulldata_aachen, "Aachen")
plot_solar_corr(fulldata_goerlitz, "Görlitz")
plot_solar_corr(fulldata_zugspitze, "Zugspitze")

# --------------------------------------------------------------------------
# 6) Documentation of results
# --------------------------------------------------------------------------
fulldata = {
    "Arkona": fulldata_arkona,
    "Aachen": fulldata_aachen,
    "Görlitz": fulldata_goerlitz,
    "Zugspitze": fulldata_zugspitze
}

def final_dict(df: pd.DataFrame, station: str) -> dict:
    # Pearson correlations
    r = df.corr()["price"].drop("price")

    # Negative-price hours
    negative_prices = df[df["price"] < 0]

    result = {
        "station": station,

        # Correlations
        "wind_corr": r["wind_speed"],
        "solar_corr": r["global_solar_radiation"],

        # Negative prices
        "negative_hours": len(negative_prices),
        "negative_share": len(negative_prices) / len(df) * 100,

        # Average conditions
        "mean_wind_negative": negative_prices["wind_speed"].mean(),
        "mean_solar_negative": negative_prices["global_solar_radiation"].mean(),

        # Overall averages
        "mean_wind_total": df["wind_speed"].mean(),
        "mean_solar_total": df["global_solar_radiation"].mean(),
    }

    return result


findings = []

for station, df in fulldata.items():
    result = final_dict(df, station)
    findings.append(result)

results_df = pd.DataFrame(findings)

print(results_df)

results_readme = results_df.copy()
results_readme = results_readme.round({"wind_corr": 2, "solar_corr": 2, "negative_hours":0,
"negative_share":2, "mean_wind_negative":2, "mean_solar_negative":2, 
"mean_wind_total":2, "mean_solar_total":2}) 
results_readme.to_csv("results/results.csv", index=False)
