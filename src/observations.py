# -*- coding: utf-8 -*-
"""
Created on Sun Aug  9 10:51:24 2026

@author: niker
"""

"""
DWD Station Analysis: Wind & Solar Radiation for Four German Stations
(Arkona, Aachen, Görlitz, Zugspitze) – North/West/East/South Extreme Points.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests

# --------------------------------------------------------------------------
# Konfiguration
# --------------------------------------------------------------------------
REQUEST_TIMEOUT = 30          # Sekunden für HTTP-Requests
MISSING_VALUE = -999          # DWD-Kennzeichnung für fehlende Werte
START_DATE = pd.Timestamp("2023-01-01")
END_DATE = pd.Timestamp("2025-12-31")
INTERPOLATION_LIMIT = 3       # max. aufeinanderfolgende Zeitschritte, die interpoliert werden

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "DWD Data"

STATION_LIST_URLS = {
    "wind": "https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/hourly/wind/historical/FF_Stundenwerte_Beschreibung_Stationen.txt",
    "solar": "https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/hourly/solar/ST_Stundenwerte_Beschreibung_Stationen.txt",
}


STATIONS = {
    "Arkona": {
        "id": "00183",
        "role": "Norden",
        "wind_file": DATA_DIR / "wind" / "Arkona Wind_produkt_ff_stunde_19730101_20251231_00183.txt",
        "solar_file": DATA_DIR / "solar" / "Arkona Solar_produkt_st_stunde_19810101_20260630_00183.txt",
    },
    "Aachen": {
        "id": "15000",
        "role": "Westen",
        "wind_file": DATA_DIR / "wind" / "Aachen Wind_produkt_ff_stunde_20110401_20251231_15000.txt",
        "solar_file": DATA_DIR / "solar" / "Aachen Solar_produkt_st_stunde_20230101_20260630_15000.txt",
    },
    "Görlitz": {
        "id": "01684",
        "role": "Osten",
        "wind_file": DATA_DIR / "wind" / "Görlitz Wind_produkt_ff_stunde_19630101_20251231_01684.txt",
        "solar_file": DATA_DIR / "solar" / "Görlitz Solar_produkt_st_stunde_20010101_20260630_01684.txt",
    },
    "Zugspitze": {
        "id": "05792",
        "role": "Süden",
        "wind_file": DATA_DIR / "wind" / "Zugspitze Wind_produkt_ff_stunde_19760101_20251231_05792.txt",
        "solar_file": DATA_DIR / "solar" / "Zugspitze Solar_produkt_st_stunde_20130101_20260630_05792.txt",
    },
}


# --------------------------------------------------------------------------
# 1) Load station metadata from DWD (for documentation purposes only)
# --------------------------------------------------------------------------
def get_station_list(url: str) -> pd.DataFrame:
    """Loads and parses the DWD station description file (fixed-width format)."""
    response = requests.get(url, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()

    lines = response.text.splitlines()
    stations = [
        {
            "station_id": line[0:5].strip(),
            "from_date": line[6:14].strip(),
            "to_date": line[15:23].strip(),
            "height": line[36:42].strip(),
            "latitude": line[42:51].strip(),
            "longitude": line[51:61].strip(),
            "name": line[61:102].strip(),
        }
        for line in lines[2:] if line.strip()
    ]

    df = pd.DataFrame(stations)
    for col in ("height", "latitude", "longitude"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["from_date"] = pd.to_datetime(df["from_date"], format="%Y%m%d")
    df["to_date"] = pd.to_datetime(df["to_date"], format="%Y%m%d")
    return df


def document_station_selection() -> None:
    """
    Just for documentation: this shows how the four stations (northernmost,
    southernmost, easternmost, and westernmost, with complete wind AND
    solar coverage during the analysis period) were determined. The result is
    already hard-coded in STATIONS above, because the originally southernmost
    station (Oberstdorf) has no solar data and was replaced
    by the Zugspitze.
    """
    df_wind = get_station_list(STATION_LIST_URLS["wind"])
    df_solar = get_station_list(STATION_LIST_URLS["solar"])

    def coverage_mask(df):
        return (df["from_date"] <= START_DATE) & (df["to_date"] >= END_DATE)

    wind_ok = df_wind.loc[coverage_mask(df_wind)]

    print("northern most wind station:", wind_ok.loc[wind_ok["latitude"].idxmax(), "name"])
    print("southern most wind station:", wind_ok.loc[wind_ok["latitude"].idxmin(), "name"],
          "(has no solar data -> Zugspitze as a substitute)")
    print("eastern most wind station:", wind_ok.loc[wind_ok["longitude"].idxmax(), "name"])
    print("western most wind station:", wind_ok.loc[wind_ok["longitude"].idxmin(), "name"])


# --------------------------------------------------------------------------
# 2) Load & Process Raw Data
# --------------------------------------------------------------------------
def load_wind(path: Path) -> pd.DataFrame:
    """Reads hourly wind data, sorted by time, and renames columns."""
    df = pd.read_csv(path, sep=";", skipinitialspace=True)
    df["time"] = pd.to_datetime(df["MESS_DATUM"].astype(str), format="%Y%m%d%H")
    df = df.set_index("time")
    return df[["F", "D"]].rename(columns={"F": "wind_speed", "D": "wind_direction"})


def load_solar(path: Path) -> pd.DataFrame:
    """
    Reads hourly solar radiation values (global radiation FG_LBERG).
    """
    df = pd.read_csv(path, sep=";")
    df["time"] = pd.to_datetime(df["MESS_DATUM_WOZ"], format="%Y%m%d%H:%M")
    df = df.set_index("time")
    return df[["FG_LBERG"]].rename(columns={"FG_LBERG": "global_solar_radiation"})


def _dedupe_index(df: pd.DataFrame, label: str) -> pd.DataFrame:
    """Removes duplicate timestamps (e.g., due to daylight saving time), and retains the first value."""
    n_dupes = int(df.index.duplicated().sum())
    if n_dupes:
        print(f"  [{label}] {n_dupes} Duplicate timestamps found -> removed (first value retained)")
        df = df[~df.index.duplicated(keep="first")]
    return df.sort_index()


def build_station_dataframe(wind_file: Path, solar_file: Path, label: str) -> pd.DataFrame:
    """Loads, links, and cleans up wind and solar data from a station."""
    df_wind = _dedupe_index(load_wind(wind_file), f"{label} Wind")
    df_solar = _dedupe_index(load_solar(solar_file), f"{label} Solar")

    df = df_wind.join(df_solar, how="outer")

    columns = ["wind_speed", "wind_direction", "global_solar_radiation"]
    df[columns] = df[columns].apply(pd.to_numeric, errors="coerce")
    df[columns] = df[columns].replace(MISSING_VALUE, np.nan)

    return df.loc[START_DATE:END_DATE]


# --------------------------------------------------------------------------
# 3) Handling Invalid Values
# --------------------------------------------------------------------------
def nan_dealer(df: pd.DataFrame) -> pd.DataFrame:
    """
    Interpolates wind and radiation values based on time, but ONLY for gaps
    of up to INTERPOLATION_LIMIT consecutive time steps.
    Longer or systematic gaps are left NaN.

    Wind direction is NOT interpolated, as it is a circular quantity
    """
    df = df.copy()  # IMPORTANT: Prevents in-place mutation of the passed-in data frame
    cols = ["wind_speed", "global_solar_radiation"]
    df[cols] = df[cols].interpolate(
        method="time", limit=INTERPOLATION_LIMIT, limit_direction="both", axis=0
    )
    return df


def gap_report(df: pd.DataFrame, label: str) -> None:
    """Returns the length of the remaining NaN gaps for each column."""
    print(f"--- {label}: remaining gaps after interpolation---")
    for col in ["wind_speed", "wind_direction", "global_solar_radiation"]:
        is_na = df[col].isna()
        n_nan = int(is_na.sum())
        if n_nan == 0:
            print(f"  {col}: no NaN")
            continue
        gap_len = is_na.groupby((~is_na).cumsum()).transform("size") * is_na
        print(f"  {col}: {n_nan} NaN total, longest remaining gap = {int(gap_len.max())}")


# --------------------------------------------------------------------------
# 4) plausibility check
# --------------------------------------------------------------------------
def range_check(df: pd.DataFrame, label: str) -> None:
    """Checks whether values fall within physically plausible ranges."""
    problems = {
        "wind_speed < 0": df[df["wind_speed"] < 0],
        "global_solar_radiation < 0": df[df["global_solar_radiation"] < 0],
        "global_solar_radiation > 1200": df[df["global_solar_radiation"] > 1200],
        "wind_direction außerhalb [0, 360]": df[
            (df["wind_direction"] < 0) | (df["wind_direction"] > 360)
        ],
    }

    issues = {}
    for k, v in problems.items():
        if not v.empty:
            issues[k] = v
    if not issues:
        print(f"{label}: all values in plausible range.")
    else:
        print(f"{label}: Abnormalities Found:")
        for desc, rows in issues.items():
            print(f"  {desc}: {len(rows)} rows")
            print(rows.head())


# --------------------------------------------------------------------------
# 5) visualisation
# --------------------------------------------------------------------------
def plot_rolling_mean(df: pd.DataFrame, variable: str, station: str, window: int) -> None:
    df_rm = df.copy()
    df_rm["RollingMean"] = df_rm[variable].rolling(window=window, min_periods=1).mean()

    plt.figure(figsize=(10, 6))
    plt.plot(df_rm.index, df_rm[variable], label="Original", color="blue", alpha=0.6)
    plt.plot(df_rm.index, df_rm["RollingMean"], label=f"{window} time steps Rolling Mean",
              color="red", linewidth=2)
    plt.title(f"Rolling Mean {station}: {variable}", fontsize=14)
    plt.xlabel("Datum")
    plt.ylabel(variable)
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------
def main():
    raw = {}
    interpolated = {}

    for name, cfg in STATIONS.items():
        print(f"\n=== {name} ({cfg['role']}, Station {cfg['id']}) ===")
        df = build_station_dataframe(cfg["wind_file"], cfg["solar_file"], name)
        raw[name] = df

        missing_share = df.isna().mean() * 100
        print("missing share before interpolation (%):")
        print(missing_share.round(2))

        df_interp = nan_dealer(df)
        interpolated[name] = df_interp

        gap_report(df_interp, name)
        range_check(df_interp, name)

    for name, df_interp in interpolated.items():
        plot_rolling_mean(df_interp, "wind_speed", name, window=168)
        plot_rolling_mean(df_interp, "global_solar_radiation", name, window=168)

    return raw, interpolated


if __name__ == "__main__":
    raw_stations, interpolated_stations = main()
    #Individual access is still possible, for example:
    arkona_interpol = interpolated_stations["Arkona"]
    plot_rolling_mean(arkona_interpol,"wind_speed", "Arkona", window=168)
    
    zugspitze_interpol = interpolated_stations["Zugspitze"]