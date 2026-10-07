---
source: NASA Land Processes DAAC (LP DAAC)
title: Burned Area Mapping and Differentiation from Active Fire Hotspots
category: remote_sensing
dataset: BURNED_AREA_SCIENCE
satellite: MODIS, VIIRS
date: 2024-02-01
chunk_index: 0
---

# Burned Area Mapping and Differentiation from Active Fire Hotspots

## Conceptual Distinction: Active Fire vs. Burned Area
Remote sensing literature strictly differentiates between two complementary fire products:
1. **Active Fire Hotspots (Thermal Anomalies)**: Instantaneous measurements of combustion thermal radiation at the exact second of satellite observation. They capture flaming front locations, temperature, and FRP.
2. **Burned Area (Post-Fire Scars)**: Cumulative physical surface transformations resulting from vegetation consumption, charcoal deposition, soil exposure, and canopy loss.

## Why Active Fire Hotspot Counts Do Not Equal Burned Area
- **Cloud/Smoke Obscuration**: A wildfire raging under a dense pyrocumulonimbus cloud or weather system may never be detected by active fire sensors.
- **Temporal Mismatch**: Fast-burning grass fires can ignite, burn through, and extinguish between the 6-hour polar satellite overpass windows.
- **Repeated Detections**: A stationary, slow-moving smoldering peat or heavy timber fire can be observed by Terra, Aqua, and VIIRS over 8 consecutive passes, producing 8 hotspot points for a single physical burn area.
- **Fire Size vs. Pixel Footprint**: A single MODIS 1km hotspot detection does not imply 1 km² was burned; it implies a fire of at least ~100 m² was actively emitting heat within that 1km pixel.

Burned area algorithms (e.g., MCD64A1, VNP64A1) use multi-day surface reflectance time series to measure persistent drop in Normalized Difference Vegetation Index (NDVI) and Normalized Burn Ratio (NBR), mapping the actual physical perimeter of destruction.
