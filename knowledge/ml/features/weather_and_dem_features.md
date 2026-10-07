---
source: EarthPulse Feature Engineering Documentation
title: Predictive Features: Weather Vectors, Topography, and Lag FRP
category: machine_learning
dataset: ML_FEATURES
satellite: Multi-Sensor
date: 2024-03-05
chunk_index: 0
---

# Predictive Features: Weather Vectors, Topography, and Lag FRP

## Feature Vector Composition
The XGBoost fire spread predictor uses a 9-dimensional synthesized feature vector:
1. `lag_frp` (MW): Fire Radiative Power recorded in the target H3 cell or neighbor 24 hours prior (t - 24h).
2. `fwi` (Fire Weather Index): Canadian Forest Fire Weather Index rating combustible fuel dryness.
3. `rh` (%): Near-surface Relative Humidity (dry air < 25% sharply accelerates rate of spread).
4. `wind_speed_ms` (m/s): 10-meter atmospheric wind speed.
5. `u10` (m/s): Eastward wind vector component.
6. `v10` (m/s): Northward wind vector component.
7. `dem_slope_deg` (degrees): Surface terrain slope derived from SRTM elevation. According to McArthur and Rothermel fire physics, uphill fires burn exponentially faster due to convective preheating of uphill vegetation: Rate_of_Spread ~ exp(0.045 * slope).
8. `ndvi` (0.0 to 1.0): Normalized Difference Vegetation Index indicating biomass fuel density.
9. `brightness` (K): Peak mid-wave infrared brightness temperature.
