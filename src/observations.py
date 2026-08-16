# -*- coding: utf-8 -*-
"""
Created on Sun Aug  9 10:51:24 2026

@author: niker
"""

import requests
import pandas as pd
import re
import matplotlib.pyplot as plt

url_wind = "https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/hourly/wind/historical/FF_Stundenwerte_Beschreibung_Stationen.txt"
url_solar= "https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/hourly/solar/ST_Stundenwerte_Beschreibung_Stationen.txt"


REQUEST_TIMEOUT = 30  # secs
MISSING_VALUE = -999  # DWD-notion for missing values

def get_station_list(url: str) -> pd.DataFrame:
    """
    Download of DWD-Stationsmetadaten.

    Returns
    -------
    pandas.DataFrame
        cols: station_id, from_date, to_date, height, latitude,
        longitude, name.
        """
    response = requests.get(url,timeout=REQUEST_TIMEOUT)
    response.raise_for_status()


    lines = response.text.splitlines()
    stations = []
    for line in lines[2:]:
        if not line.strip():
            continue
    
        station = {
            "station_id": line[0:5].strip(),
            "from_date": line[6:14].strip(),
            "to_date": line[15:23].strip(),
            "height": line[36:42].strip(),
            "latitude": line[42:51].strip(),
            "longitude": line[51:61].strip(),
            "name": line[61:102].strip(),
        }
    
        stations.append(station)

    df = pd.DataFrame(stations)
    # numbered cols come from text file as string
    for col in ("height", "latitude", "longitude"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df

# individual dataframes for wind & solar observations
df_wind = get_station_list(url_wind)
df_solar = get_station_list(url_solar)
# timestamp as datetime
df_wind["from_date"] = pd.to_datetime(df_wind["from_date"].astype(str), format="%Y%m%d")
df_wind["to_date"] = pd.to_datetime(df_wind["to_date"].astype(str), format="%Y%m%d")
df_solar["from_date"] = pd.to_datetime(df_solar["from_date"].astype(str), format="%Y%m%d")
df_solar["to_date"] = pd.to_datetime(df_solar["to_date"].astype(str), format="%Y%m%d")

# set filter for two years 01.01.2023 - 31.12.2025 for test reasons
start_date = pd.Timestamp("2023-01-01")
end_date = pd.Timestamp("2025-12-31")
timefilter_wind = (
    (df_wind["from_date"] <= start_date)
    & (df_wind["to_date"] >= end_date)
)

filtered_df_wind = df_wind.loc[timefilter_wind]

timefilter_solar = (
    (df_solar["from_date"] <= start_date)
    & (df_solar["to_date"] >= end_date)
)

filtered_df_solar = df_solar.loc[timefilter_solar]

# choose four stations: northernmost, southernmost, westernmost, easternmost
north_wind = filtered_df_wind.loc[filtered_df_wind["latitude"].idxmax()]
south_wind = filtered_df_wind.loc[filtered_df_wind["latitude"].idxmin()]
east_wind = filtered_df_wind.loc[filtered_df_wind["longitude"].idxmax()]
west_wind = filtered_df_wind.loc[filtered_df_wind["longitude"].idxmin()]

# check if identified wind stations also have available solar observations
# df_solar[df_solar["station_id"] == "03032"] #List
df_solar[df_solar["station_id"] == "00183"] #Arkona as alternative for List since it has both
#df_solar[df_solar["station_id"] == "03730"] #Oberstorf is the southernmost station but has no solar data recorded
df_wind[df_wind["station_id"] == "05792"] #Zugspitze as alternative for Oberstorf since it has both
df_solar[df_solar["station_id"] == "01684"] #Görlitz
df_solar[df_solar["station_id"] == "15000"] #Aachen

# west_solar = filtered_df_solar.loc[filtered_df_solar["longitude"].idxmin()]
# print(west_solar)

chosen_stations = {
    "north": "00183",   # Arkona
    "south": "05792",   # Zugspitze
    "east": "01684",    # Görlitz
    "west": "15000",    # Aachen
}

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "DWD Data"

wind_aachen = DATA_DIR / "wind" / "Aachen Wind_produkt_ff_stunde_20110401_20251231_15000.txt"

df_wind_aachen = pd.read_csv(
    wind_aachen,
    sep=";",
    skipinitialspace=True
)

wind_arkona = DATA_DIR / "wind" / "Arkona Wind_produkt_ff_stunde_19730101_20251231_00183.txt"

df_wind_arkona = pd.read_csv(
    wind_arkona,
    sep=";",
    skipinitialspace=True
)

wind_goerlitz = DATA_DIR / "wind" / "Görlitz Wind_produkt_ff_stunde_19630101_20251231_01684.txt"

df_wind_goerlitz = pd.read_csv(
    wind_goerlitz,
    sep=";",
    skipinitialspace=True
)

wind_zugspitze = DATA_DIR / "wind" / "Zugspitze Wind_produkt_ff_stunde_19760101_20251231_05792.txt"

df_wind_zugspitze = pd.read_csv(
    wind_zugspitze,
    sep=";",
    skipinitialspace=True
)

solar_aachen = DATA_DIR / "solar" / "Aachen Solar_produkt_st_stunde_20230101_20260630_15000.txt"

df_solar_aachen = pd.read_csv(
    solar_aachen,
    sep=";",
)

solar_arkona = DATA_DIR / "solar" / "Arkona Solar_produkt_st_stunde_19810101_20260630_00183.txt"

df_solar_arkona = pd.read_csv(
    solar_arkona,
    sep=";",
)

solar_goerlitz = DATA_DIR / "solar" / "Görlitz Solar_produkt_st_stunde_20010101_20260630_01684.txt"

df_solar_goerlitz = pd.read_csv(
    solar_goerlitz,
    sep=";",
)

solar_zugspitze = DATA_DIR / "solar" / "Zugspitze Solar_produkt_st_stunde_20130101_20260630_05792.txt"

df_solar_zugspitze = pd.read_csv(
    solar_zugspitze,
    sep=";",
)

def correct_solar(df):
    df["time"] = pd.to_datetime(df["MESS_DATUM_WOZ"],format="%Y%m%d%H:%M")
    df = df.set_index("time")
    df = df[["FG_LBERG"]]
    df = df[["FG_LBERG"]].rename(columns={
        "FG_LBERG": "global solar radiation"})
    return df

df_solar_aachen = correct_solar(df_solar_aachen)
df_solar_arkona = correct_solar(df_solar_arkona)
df_solar_goerlitz = correct_solar(df_solar_goerlitz)
df_solar_zugspitze = correct_solar(df_solar_zugspitze)

def correct_wind(df):
    df = df.copy()
    df["time"] = pd.to_datetime(
        df["MESS_DATUM"].astype(str),
        format="%Y%m%d%H"
    )
    df = df.set_index("time")
    df = df[["F", "D"]].rename(columns={
        "F": "wind_speed",
        "D": "wind_direction"
    })
    return df

df_wind_aachen = correct_wind(df_wind_aachen)
df_wind_arkona = correct_wind(df_wind_arkona)
df_wind_goerlitz = correct_wind(df_wind_goerlitz)
df_wind_zugspitze = correct_wind(df_wind_zugspitze)

def wind_solar_joined(dfwind,dfsolar):
    df = dfwind.join(dfsolar, how="inner")
    MISSING_VALUE= -999
    columns = ["wind_speed", "wind_direction", "global solar radiation"]
    df[columns] = df[columns].replace(MISSING_VALUE, pd.NA)
    filtered_df=df.loc["2023-01-01":"2025-12-31"]
    return filtered_df

df_arkona = wind_solar_joined(df_wind_arkona, df_solar_arkona)
df_aachen = wind_solar_joined(df_wind_aachen, df_solar_aachen)
df_goerlitz = wind_solar_joined(df_wind_goerlitz, df_solar_goerlitz)
df_zugspitze = wind_solar_joined(df_wind_zugspitze, df_solar_zugspitze)


#calculate missing share of filtered values
missing_share_arkona = df_arkona.isna().mean() * 100 
missing_share_achen = df_aachen.isna().mean() * 100 
missing_share_goerlitz = df_goerlitz.isna().mean() * 100 
missing_share_zugspitze = df_zugspitze.isna().mean() * 100

#goes through the data frame and identifies where there are transitions 
#from NaN to a non-NaN value
#marks these transitions and assigns a sequential number to each block
#this is for testing and manual interpretation
blocks = (
    df_aachen["wind_speed"].isna()
    .ne(df_aachen["wind_speed"].isna().shift())
    .cumsum()
)

#identifies the size of these blocks to give an idea if these blocks 
#are in consecutive timesteps, and how long the missing periods are
df_aachen[df_aachen["wind_speed"].isna()].groupby(blocks).size()
#shows the specific timestamps for the missing wind speeds
df_aachen[df_aachen["wind_speed"].isna()]
#for further usage we need to make the numbers numeric


#function for identifying missing values and deals with them in the appropriate manner
def nan_dealer(df):
    df["wind_speed"] = pd.to_numeric(df["wind_speed"], errors="coerce")
    df["wind_direction"] = pd.to_numeric(df["wind_direction"], errors="coerce")
    df["global solar radiation"] = pd.to_numeric(df["global solar radiation"], errors="coerce")
    df[["wind_speed", "global solar radiation"]] = (df[["wind_speed", "global solar radiation"]].interpolate(method="time", limit=3, axis=0, limit_direction="both"))
    return df

arkona_interpol = nan_dealer(df_arkona)
aachen_interpol = nan_dealer(df_aachen)
goerlitz_interpol = nan_dealer(df_goerlitz)
zugspitze_interpol = nan_dealer(df_zugspitze)

#Test because Zugspitze has still a lot of missing values after interpolation
#trying to find out why that is
def diagnose(df, name):
    print(f"--- {name} ---")
    print("Index sorted:", df.index.is_monotonic_increasing)
    print("Index duplicates:", df.index.duplicated().sum())
    print("Index dtype:", df.index.dtype)
    print()
    for col in ["wind_speed", "global solar radiation"]:
        s = pd.to_numeric(df[col], errors="coerce")
        is_na = s.isna()
        n_nan = is_na.sum()
        if n_nan == 0:
            print(f"{col}: no NaN")
            continue
        gap_len = is_na.groupby((~is_na).cumsum()).transform("size") * is_na
        print(f"{col}: {n_nan} NaN total, longest gap = {gap_len.max()}")
        print("distribution of gap lengths:")
        print(gap_len[gap_len > 0].value_counts().sort_index())
        # NaN am Rand?
        print("NaN at the beginning (first 5 values):", is_na.iloc[:5].tolist())
        print("NaN at the end (last 5 values):", is_na.iloc[-5:].tolist())
        print()

diagnose(df_zugspitze, "Zugspitze")
# --- Zugspitze ---
# Index sorted: True
# Index duplicates: 0
# Index dtype: datetime64[ns]

# wind_speed: no NaN
# global solar radiation: 232 NaN total, longest gap = 9
# distribution of gap lengths:
# global solar radiation
# 2      1
# 4      3
# 5     88
# 7    132
# 9      8
# Name: count, dtype: int64
# NaN at the beginning (first 5 values): [False, False, False, False, False]
# NaN at the end (last 5 values): [False, False, False, False, False]

#≤ 3 consecutive missing hourly values: time-based interpolation
#> 3 consecutive values / systematic gaps: retain NaN
#Optional: external radiation product for applications requiring a complete time series.'

# nan_zugspitze=zugspitze_interpol[zugspitze_interpol["global solar radiation"].isna()]
# nan_hours = nan_zugspitze.index.hour
# nan_days = nan_zugspitze.index.day
# print(nan_hours.value_counts().sort_index())
#time
# 8      1
# 9      1
# 10    24 -> loads of missing values
# 11    45 -> loads of missing values
# 12    44 -> loads of missing values
# 13    45 -> loads of missing values
# 14    45 -> loads of missing values
# 15    24 -> loads of missing values
# 16     2
# 17     1

#232 Zugspitze solar radiation values stay NaN, because they seem to be systematic and we don't know the cause 

#now checking if all the values are in the expected range for the respective variables
def range_check(df):
    windspeed = df[df["wind_speed"]<0]
    radiation = df[df["global solar radiation"]<0]
    winddirection = df[
    (df["wind_direction"] < 0) |
    (df["wind_direction"] > 360)]
    
    if windspeed.empty and radiation.empty and winddirection.empty :
        print (True)
    else:
        print(windspeed)
        print(radiation)
        print(winddirection)
        
check_arkona = range_check(arkona_interpol)
check_aachen = range_check(aachen_interpol)    
check_goerlitz = range_check(goerlitz_interpol)
check_zugspitze = range_check(zugspitze_interpol)    
   


def plot_rolling_mean(df, variable, station, window):
    # now plotting to see possible outliers in wind speed & radiation
    df_rm = df.copy()
    df_rm["RollingMean"] = df_rm[variable].rolling(window=window, min_periods=1).mean()

    plt.figure(figsize=(10, 6))
    plt.plot(df_rm.index, df_rm[variable], label="Original", color="blue", alpha=0.6)
    plt.plot(df_rm.index, df_rm["RollingMean"], label=f"{window} timesteps Rolling Mean", color="red", linewidth=2)

    # Formatting
    plt.title(f"Rolling Mean {station} {variable}", fontsize=14)
    plt.xlabel("Date")
    plt.ylabel(f"{variable}")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()
    
plot_rolling_mean(arkona_interpol, "wind_speed", "Arkona", 168)
plot_rolling_mean(arkona_interpol, "global solar radiation", "Arkona", 168)
plot_rolling_mean(aachen_interpol, "wind_speed", "Aachen", 168)
plot_rolling_mean(aachen_interpol, "global solar radiation", "Aachen", 168)
plot_rolling_mean(goerlitz_interpol, "wind_speed", "Görlitz", 168)
plot_rolling_mean(goerlitz_interpol, "global solar radiation", "Görlitz", 168)
plot_rolling_mean(zugspitze_interpol, "wind_speed", "Zugspitze", 168)
plot_rolling_mean(zugspitze_interpol, "global solar radiation", "Zugspitze", 168)