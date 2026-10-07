---
source: NASA University of Maryland MODIS Fire Product User Guide
title: MCD14ML Product Specification: Global Monthly Fire Location Data
category: datasets
dataset: MCD14ML
satellite: Terra, Aqua
date: 2024-02-15
chunk_index: 0
---

# MCD14ML Product Specification: Global Monthly Fire Location Data

## Overview and File Format
MCD14ML is the standard global monthly active fire vector product generated from MODIS observations aboard Terra (MOD14) and Aqua (MYD14). Distributed in ASCII text and CSV format, each row represents an individual 1km thermal anomaly detection.

## Field Schema and Data Dictionary
- `latitude` (float): Latitude of the center of the 1km fire pixel (-90.0 to 90.0).
- `longitude` (float): Longitude of the center of the 1km fire pixel (-180.0 to 180.0).
- `brightness` (float): Brightness temperature of Channel 21/22 in Kelvin (range 300.0 to 500.0 K).
- `scan` (float): Along-scan pixel dimension in kilometers (1.0 at nadir up to ~4.8 km at scan edge).
- `track` (float): Along-track pixel dimension in kilometers (1.0 at nadir up to ~2.0 km at scan edge).
- `acq_date` (string): Acquisition date in UTC (YYYY-MM-DD).
- `acq_time` (string): Acquisition time in UTC (HHMM).
- `satellite` (string): Satellite identifier: 'Terra' (T) or 'Aqua' (A).
- `instrument` (string): 'MODIS'.
- `confidence` (integer): Detection quality confidence score (0 to 100%).
  - Low Confidence: 0–30% (borderline temperature delta, possible cloud edge noise).
  - Nominal Confidence: 30–80% (standard reliable detection).
  - High Confidence: 80–100% (saturated MIR channel, unambiguous flaming fire).
- `version` (string): Collection algorithm version ('6.1NRT' or '6.1').
- `bright_t31` (float): Brightness temperature of Channel 31 (11.0 µm) in Kelvin.
- `frp` (float): Fire Radiative Power in Megawatts (MW).
- `daynight` (string): Overpass condition: 'D' = Day, 'N' = Night.

## Harmonization Role in EarthPulse
EarthPulse ingests MCD14ML records, projects them onto H3 Resolution 8 cells, and pairs them with VIIRS passes within a ±30 minute coincidence window to calculate cross-sensor calibrated FRP.
