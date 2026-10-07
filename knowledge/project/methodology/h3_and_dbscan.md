---
source: EarthPulse Geospatial Engineering Documentation
title: Uber H3 Hexagonal Grid Indexing and DBSCAN Clustering
category: methodology
dataset: H3_INDEXING
satellite: MODIS, VIIRS
date: 2024-03-01
chunk_index: 0
---

# Uber H3 Hexagonal Grid Indexing and DBSCAN Clustering

## Why H3 Hexagonal Indexing?
Traditional square grid rasters suffer from two severe mathematical flaws:
1. **Unequal Neighbor Distances**: A square pixel has orthogonal neighbors at distance d and diagonal neighbors at distance d*sqrt(2), distorting directional fire spread models.
2. **Latitude Distortion**: Rectangular latitude-longitude bins shrink drastically towards the poles.

Uber H3 solves this with an icosahedron-projected discrete hexagonal global grid:
- All 6 neighbors are equidistant.
- Equal area across latitudes.
- **Resolution 8**: Average cell area ~0.737 km² (~870m edge), ideal for MODIS 1km footprint.
- **Resolution 9**: Average cell area ~0.105 km² (~330m edge), matching VIIRS 375m footprint.

## DBSCAN Spatial Clustering
To merge concurrent multi-sensor satellite detections into single cohesive fire perimeters, EarthPulse runs Density-Based Spatial Clustering of Applications with Noise (DBSCAN):
- **Epsilon (eps)**: 1,000 meters (maximum distance between points in the same cluster).
- **Min Samples**: 2 points.
Points within eps are fused into a unified cluster, preventing double-counting when Terra, Aqua, and VIIRS observe the same fire in quick succession.
