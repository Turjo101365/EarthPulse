---
source: EarthPulse Harmonization Research Paper
title: MODIS–VIIRS Multi-Sensor Harmonization and Calibrated FRP
category: harmonization
dataset: HARMONIZATION_PIPELINE
satellite: MODIS, VIIRS
date: 2024-03-01
chunk_index: 0
---

# MODIS–VIIRS Multi-Sensor Harmonization and Calibrated FRP

## The Cross-Sensor Discrepancy Problem
A direct summation of raw MODIS and VIIRS hotspot counts produces an artificial 300% to 400% surge in perceived fire occurrence because:
1. VIIRS 375m pixels have ~1/7th the surface area of MODIS 1km pixels, detecting smaller, weaker fires.
2. A single large wildfire that triggers 1 MODIS detection often produces 4 to 8 individual VIIRS detections.

## 5-Node Harmonization State Machine
EarthPulse resolves this through an automated 5-Node pipeline:
- **Node 1 (node_ingest_and_validate)**: Filters cloud edge reflectance, water false positives, and invalid coordinates.
- **Node 2 (node_spatial_h3_matching)**: Quantizes detections onto H3 Resolution 8/9 cells.
- **Node 3 (node_temporal_window_match)**: Employs KDTree spatial-temporal matching with a ±30-minute coincidence window.
- **Node 4 (node_duplicate_clustering_and_frp)**: Merges multi-satellite overlaps using DBSCAN (1000m) and calculates calibrated Fire Radiative Power:
  FRP_harmonized = 0.65 * FRP_VIIRS + 0.35 * FRP_MODIS
  This weighting normalizes the sharper Point Spread Function (PSF) of VIIRS with the broad spatial integration of MODIS.
- **Node 5 (node_feature_synthesis)**: Enriches detections with ECMWF ERA5 weather vectors (RH, 10m Wind U/V, Temperature) and Shuttle Radar Topography Mission (SRTM) DEM slope.
