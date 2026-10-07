---
source: NASA Land Processes DAAC VIIRS Product Documentation
title: VNP14IMGML Product Specification: Suomi-NPP VIIRS 375m Active Fire
category: datasets
dataset: VNP14IMGML
satellite: Suomi-NPP
date: 2024-02-15
chunk_index: 0
---

# VNP14IMGML Product Specification: Suomi-NPP VIIRS 375m Active Fire

## Overview
VNP14IMGML is the high-resolution vector active fire product derived from the 375-meter I-bands of the VIIRS sensor aboard the Suomi-NPP satellite. It offers a 3x spatial improvement over MODIS MCD14ML.

## Field Schema and Data Dictionary
- `latitude` (float): Latitude of detection centroid.
- `longitude` (float): Longitude of detection centroid.
- `bright_ti4` (float): Brightness temperature of Band I4 (3.74 µm) in Kelvin.
- `scan` (float): Across-track pixel size in kilometers (0.375 km at nadir up to ~0.8 km at edge).
- `track` (float): Along-track pixel size in kilometers (0.375 km).
- `acq_date` (string): Acquisition date in UTC (YYYY-MM-DD).
- `acq_time` (string): Acquisition time in UTC (HHMM).
- `satellite` (string): Satellite identifier: 'N' (Suomi-NPP).
- `confidence` (string): Categorical confidence: 'low', 'nominal', 'high'.
- `version` (string): Algorithm version ('2.0NRT' or 'Collection 2').
- `bright_ti5` (float): Brightness temperature of Band I5 (11.45 µm) in Kelvin.
- `frp` (float): Fire Radiative Power in Megawatts (MW).
- `daynight` (string): Solar illumination condition: 'D' or 'N'.

## Detection Advantages
VNP14IMGML resolves narrow fire lines and detects flaming fronts under moderate canopy cover where MODIS 1km signals are diluted by surrounding unburned forest.
