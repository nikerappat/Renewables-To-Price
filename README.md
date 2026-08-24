# \#Renewables To Price

Comparing electricity market prices with observational wind \& solar data from four observation stations in Germany.

The goal is to evaluate whether observations of wind speed and global solar radiation show correlation with the German Day-Ahead-Market Price (DE-LU).



\## 1. Hypothesis and Research Question

Is it possible to detect a recognizable correlation between meteorological data (in this case: wind speed and global solar radiation) and the market price for electricity in the sense of the

Merit-Order-Effect whereby high renewable power input into the grid leads to lower energy prices?



\## 2. Data Sources

* Wind \& Solar: DWD Open Data, hourly observational data from four stations in Germany:

  * Arkona (northernmost)
  * Aachen (westernmost)
  * Görlitz (easternmost)
  * Zugspitze (southernmost, substitute for Oberstorf which would actually be the southernmost station but does not provide solar data)
* Electricity Price: EnergyCharts API, Day-Ahead-Price for bidding Zone DE-LU
* time period: 01.01.2023-31.12.2025 (hourly)





\## 3. Methodology



Preparing the data

* Missing Values: Market Price does not have missing data (NaN), DWD data does (marked as -999; flagged in code as NaN)

  * time based interpolation but only if gaps are more that three consecutive time stamps (hours)
  * longer gaps (systematic) are deliberately left as NaN -> no artificial smoothing of the values
* Time Zone Correction: Market Price and wind data are given in UTC, for solar data there is a conversion from WOZ (true local time) to UTC neccessary

  * conversion of timestamps in solar data to UTC based on longitude offset and equation of time
  * time stamps are then rounded to nearest hour to establish a consistent time basis for comparison with wind data \& electricity prices
* Duplicate timestamps in the index (i.e. because of Time Zone Correction) are checked with a script-bound diagnosis tool and ultimately cleaned

  * if the function detects a duplicated timestamp with different values, it shows a warning and a manual check by the user is needed
* Wind and solar data are joined per station on the time stamp (outer join so NaN remain)



Analysis

* time series and scatter plots
* Pearson correlation between wind/solar data and electricity price for each station
* separate analysis of hours with negative electricity prices

  * comparing average wind/solar values during hours with negative prices against overall average



\## 4. Results

| Station | wind\_corr | solar\_corr | negative\_hours | negative\_share (%) | mean\_wind\_negative | mean\_solar\_negative | mean\_wind\_total | mean\_solar\_total |

|---|---|---|---|---|---|---|---|---|

| Arkona | -0.22 | -0.36 | 1333 | 5.07 | 8.51 | 156.06 | 6.83 | 47.47 |

| Aachen | -0.34 | -0.34 | 1333 | 5.07 | 6.39 | 159.56 | 4.63 | 46.92 |

| Görlitz | -0.27 | -0.37 | 1333 | 5.07 | 5.03 | 162.31 | 3.65 | 48.26 |

| Zugspitze | -0.13 | -0.35 | 1333 | 5.07 | 6.27 | 175.58 | 6.26 | 55.19 |



Note: "neg.hours" and "neg. share" are identical across all four stations since the electricity price is a single nationwide time series across the bidding zone DE-LU

the prices are therefore not station-specific



<!--

!\[Correlation Wind Speed vs. Price for Station Arkona](plots/wind\_corr\_arkona.png)

!\[Correlation Solar Radiation vs. Price for Station Arkona](plots/solar\_corr\_arkona.png)

\-->



\## 5. Interpretation

* all stations show negative correlation between wind/solar observations and electricity price

  * this aligns with the merit-order hypothesis: higher renewable power input through PV or wind turbines correlate with lower energy prices
  * Arkona: !\[alternate text](./images/image.jpg)
* correlation strength is weak to moderate (between 0.13-0.37) -> not a strong relationship but a recognizable pattern
* solar effect is more pronounced than wind (except for Aachen where it is about the same)

  * solar input is concentrated during day time (mainly around noon which results in a sharp midday peak, occuring simultaneously across all of Germany)
  * wind input is more spatially distributed and more evenly spread throughout the day
* particularly strong relationship between energy prices and wind/solar data for hours with negative prices:

  * 5.07% of all hours (1333 hours over the studied period) show negative prices
  * avg. solar radiation during these times is 2.7-3.3 times higher than the overall average, depending on the station
  * wind speed also usually higher during these hours but not as pronounced (roughly 1.0-1.4 times higher)



\## 6. Limitations

* \*\*point measurements as a proxy\*\*: the chosen four stations represent the measured weather in four corners of Germany, not the actual nationwide wind/solar power input that drives the DE-LU price

  * the relationship between weather and energy prices should be understood as an indicator of large-scale weather patterns rather than direct causal evidence at these four locations
* \*\*Forecasts vs. Actuals\*\*: Day-ahead prices are calculated based on forecasts from the previous day. This analysis uses actual, measured data. Forecasts and Actuals usually correlate strongly but this is not evidence of the price formation mechanism
* \*\*Correlation analysis only\*\*: the results presented show statistical associations, not a controlled, multivariate causal analysis. Wind and solar are not independent of each other in the dataset (e.g. due to shared weather patterns), so individual correlations do not net out the other variable's effect.



\## 7. Possible next steps

* multiple regression (wind \& solar)
* comparison against actual nationwide wind/solar energy input
* statistical significance testing
* accounting for time lag between weather \& price



\## 8. Reproducibility



\### Project Structure



```

.

├──   

├── src/

│   ├── observations.py  # Loading, cleaning, and interpolating wind/solar data per station

│   └── marketprice.py/	 # Entry point for the market data

│   └── main.py		 # Visualisation and Analysis of joined observations \& market data

├── DWD Data/

│   ├── wind/           # Raw wind observation files, as referenced in the script

│   └── solar/          # Raw solar observation files, as referenced in the script

└── plots/		 # resulting plots

└── results/		 # table of results

└── README.md

```



observations.py: loading, cleaning, and interpolating wind/solar data per station

main.py: entry point for the station-level analysis

Required packages: pandas, numpy, requests, matplotlib

Data folder structure: DWD Data/wind/, DWD Data/solar/ (raw files as referenced in the script)



\### Requirements



\- Python 3.9+

\- pandas

\- numpy

\- requests

\- matplotlib

