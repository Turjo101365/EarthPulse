---
source: NASA/NOAA VIIRS Active Fire Product Specification
title: NASA/NOAA VIIRS Sensor Overview: Suomi-NPP, NOAA-20 and NOAA-21
category: remote_sensing
dataset: VIIRS_375M
satellite: Suomi-NPP, NOAA-20, NOAA-21
date: 2024-01-15
chunk_index: 0
---

# NASA/NOAA VIIRS Sensor Overview: Suomi-NPP, NOAA-20 and NOAA-21

## Spacecraft Constellation and Orbital Phasing
The Visible Infrared Imaging Radiometer Suite (VIIRS) represents the operational successor to MODIS and AVHRR, flying aboard polar-orbiting environmental satellites:
1. **Suomi-NPP (National Polar-orbiting Partnership)**: Launched October 28, 2011; Sun-synchronous orbit at 824 km altitude, afternoon 1:30 PM ascending equator crossing.
2. **NOAA-20 (JPSS-1)**: Launched November 18, 2017; identical orbit phased 50 minutes apart from Suomi-NPP. This 50-minute offset provides rapid repeat observations of rapidly expanding wildfire fronts.
3. **NOAA-21 (JPSS-2)**: Launched November 10, 2022; expanding the Joint Polar Satellite System into an operational three-satellite constellation.

## Sensor Bands and 375m Spatial Resolution
VIIRS features 22 spectral channels divided into Imagery Resolution Bands (I-bands: 375m) and Moderate Resolution Bands (M-bands: 750m). The 375m active fire detection algorithm (Schroeder et al., 2014) utilizes:
- **Band I4 (3.74 µm MIR)**: High-resolution mid-infrared channel with 375-meter spatial resolution at nadir.
- **Band I5 (11.45 µm TIR)**: High-resolution thermal infrared channel for background estimation.
- **Band M13 (4.05 µm MIR)**: Dual-gain moderate-resolution channel capable of measuring extreme high-temperature saturation up to 634 K.

## Pixel Aggregation and Geometric Superiority
Unlike MODIS, VIIRS incorporates a sophisticated multi-detector aggregation scheme that combines 3, 2, or 1 sub-samples across track as the scan angle increases:
- **Swath Width**: 3,040 km, providing zero inter-orbit gaps at the equator.
- **Constrained Pixel Growth**: While MODIS pixels expand by a factor of ~5x at swath edge, VIIRS pixel area expands by only ~2x (from 375m at nadir to ~750m at swath edge).
- **Sub-Pixel Sensitivity**: VIIRS 375m can detect flaming fires as small as 5 m² to 10 m², making it 3 to 4 times more sensitive to early-stage ignitions, small agricultural burns, and smoldering ground fires than MODIS 1km.
