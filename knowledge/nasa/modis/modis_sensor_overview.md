---
source: NASA Earth Observing System (EOS) Handbook
title: NASA MODIS Sensor Overview: Terra and Aqua Earth Observing System
category: remote_sensing
dataset: MODIS_C6_1
satellite: Terra, Aqua
date: 2024-01-15
chunk_index: 0
---

# NASA MODIS Sensor Overview: Terra and Aqua

## Mission and Orbital Configuration
The Moderate Resolution Imaging Spectroradiometer (MODIS) operates aboard two flagship NASA Earth Observing System (EOS) satellites:
1. **Terra (EOS AM-1)**: Sun-synchronous, near-polar circular orbit at 705 km altitude, descending node crossing the equator at approximately 10:30 AM local solar time. Launched on December 18, 1999.
2. **Aqua (EOS PM-1)**: Sun-synchronous, near-polar circular orbit at 705 km altitude, ascending node crossing the equator at approximately 1:30 PM local solar time. Launched on May 4, 2002.

Together, Terra and Aqua provide 4 daily global overpasses (morning, afternoon, night, and pre-dawn), offering a continuous, climate-quality active fire monitoring baseline spanning more than 24 years (2000 to present).

## Radiometric Bands and Fire Detection Physics
MODIS observes radiation across 36 spectral bands ranging from 0.4 µm to 14.4 µm. The active fire detection and thermal anomaly algorithm (Giglio et al., Collection 6.1) primarily exploits mid-infrared (MIR) and thermal infrared (TIR) channels:
- **Channel 21 (3.96 µm MIR)**: High-saturation channel operating up to ~500 K. Designed specifically for measuring intensely burning, high-temperature active fires without detector saturation.
- **Channel 22 (3.96 µm MIR)**: Low-saturation channel (saturates near ~331 K) with high radiometric sensitivity for ambient background and weak thermal anomalies.
- **Channel 31 (11.0 µm TIR)**: Measures background surface temperature and estimates cloud/smoke attenuation.

According to Wien's Displacement Law (lambda_max = 2898 / T), typical terrestrial wildfires burning between 800 K and 1200 K exhibit peak radiative emission in the 3.0–4.0 µm window. Consequently, even a small sub-pixel flaming fire (as small as 100 m² within a 1,000,000 m² pixel) dramatically raises Channel 21/22 brightness temperature above the surrounding ambient background, whereas Channel 31 brightness temperature changes only slightly.

## Spatial Footprint and Geometric Distortions
- **Nadir Spatial Resolution**: 1,000 meters (1 km) for thermal infrared bands 21, 22, and 31.
- **Swath Width**: 2,330 km across-track, producing complete global coverage every 1–2 days.
- **Panoramic Distortion & Bow-Tie Effect**: Towards the edges of the scan (scan angles approaching ±55°), the ground projection of the instantaneous field of view (IFOV) expands substantially: the along-scan dimension increases up to ~4.8 km and along-track increases to ~2.0 km. Furthermore, consecutive scans overlap at scan edges, causing multiple detections of the same fire unless deduplicated by spatial indexing algorithms.
