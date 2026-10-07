---
source: NASA Land Processes DAAC (LP DAAC) Product Guide
title: MCD64A1 Product Guide: MODIS 500m Global Burned Area Monthly
category: datasets
dataset: MCD64A1
satellite: Terra, Aqua
date: 2024-02-20
chunk_index: 0
---

# MCD64A1 Product Guide: MODIS 500m Global Burned Area Monthly

## Overview
MCD64A1 is the standard Collection 6.1 Level 3 global burned area product. It maps the spatial extent and approximate Julian day of burning at 500-meter resolution across monthly tiles.

## Hybrid Detection Algorithm
MCD64A1 combines surface reflectance change detection with thermal active fire observations:
1. **Reflectance Time Series**: Analyzes MODIS 500m surface reflectance in Band 5 (1.24 µm) and Band 7 (2.13 µm) to compute a Burn-Sensitive Vegetation Index.
2. **Active Fire Priors**: Uses 1km active fire detections (MOD14/MYD14) as temporal and spatial anchors ('seeds') to train regional statistical models of unburned vs. burned spectral reflectance.
3. **Contextual Growing**: Propagates the perimeter around seed pixels until the burn scar boundary is detected.

## Key Layers
- `Burn Date`: Day of Year (1–366) when the surface burned (0 = unburned; negative values = water, cloud, or snow).
- `Uncertainty`: Standard deviation in days associated with the estimated date.
- `QC`: Quality assessment mask identifying cloud contamination, water bodies, and land cover types.
