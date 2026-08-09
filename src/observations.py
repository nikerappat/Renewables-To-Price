# -*- coding: utf-8 -*-
"""
Created on Sun Aug  9 10:51:24 2026

@author: niker
"""

import requests
import pandas as pd
import re

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
    columns = ["wind_speed", "wind_direction", "FG_LBERG"]
    df[columns] = df[columns].replace(MISSING_VALUE, pd.NA)
    filtered_df=df.loc["2023-01-01":"2025-12-31"]
    return filtered_df

df_arkona = wind_solar_joined(df_wind_arkona, df_solar_arkona)
df_aachen = wind_solar_joined(df_wind_aachen, df_solar_aachen)
df_goerlitz = wind_solar_joined(df_wind_goerlitz, df_solar_goerlitz)
df_zugspitze = wind_solar_joined(df_wind_zugspitze, df_solar_zugspitze)

