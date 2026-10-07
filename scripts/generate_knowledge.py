from pathlib import Path

docs = {
    'knowledge/nasa/modis/modis_sensor_overview.md': """---
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
""",

    'knowledge/nasa/viirs/viirs_sensor_overview.md': """---
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
""",

    'knowledge/nasa/firms/firms_system_and_frp.md': """---
source: NASA FIRMS Documentation & Wooster et al. (2005)
title: NASA FIRMS and Fire Radiative Power (FRP) Science
category: physics_emissions
dataset: FIRMS_GLOBAL
satellite: MODIS, VIIRS
date: 2024-02-01
chunk_index: 0
---

# NASA FIRMS and Fire Radiative Power (FRP) Science

## NASA FIRMS Mission Architecture
The Fire Information for Resource Management System (FIRMS) is operated by the NASA Earth Science Data and Information System (ESDIS) at Goddard Space Flight Center. FIRMS ingests near-real-time (NRT) orbit passes from MODIS (Terra/Aqua) and VIIRS (S-NPP/NOAA-20/NOAA-21), executes spatial detection algorithms, and distributes vector fire footprints within 3 hours of satellite overpass (Ultra-Real-Time within 60 seconds of downlink via direct broadcast).

## Physics of Fire Radiative Power (FRP)
Fire Radiative Power (FRP), expressed in Megawatts (MW), measures the instantaneous rate of radiant thermal energy output from combustion:
- Measured through the MIR radiance method (Wooster et al., 2003, 2005):
  FRP = (A_pix * sigma / a) * (L_4 - L_4_bkg)
  where:
  - A_pix is the ground surface area of the satellite pixel footprint (m²).
  - sigma is the Stefan-Boltzmann constant (5.670374e-8 W/(m² K⁴)).
  - a is a sensor-specific empirical radiance coefficient (W m⁻² sr⁻¹ µm⁻¹ K⁻⁴).
  - L_4 is the 3.9 µm mid-infrared spectral radiance measured for the active fire pixel.
  - L_4_bkg is the mean 3.9 µm radiance of surrounding non-fire background pixels.

## Biomass Consumption and Atmospheric Emissions
The time-integral of FRP yields Fire Radiative Energy (FRE in Joules):
FRE = integral(FRP(t) dt)
Under the Wooster et al. formulation, the mass of dry biomass fuel combusted is directly proportional to FRE:
Biomass_Consumed (kg) = C_rad * FRE
where C_rad = 0.368 ± 0.015 kg/MJ.

From total combusted biomass, atmospheric greenhouse gas and aerosol emissions are calculated via emission factors (EF):
- Carbon Dioxide (CO₂): ~1,600 to 1,800 g CO₂ / kg dry biomass.
- Methane (CH₄): ~4.5 to 6.8 g CH₄ / kg dry biomass (28x higher 100-year Global Warming Potential than CO₂).
- Total Radiative Power: EarthPulse sums instantaneous FRP into Gigawatts (GW) of planetary thermal output.

## Hotspot vs. Confirmed Active Fire Distinction
A satellite hotspot detection is an identified thermal radiation anomaly. It should never be treated as an absolute guarantee of a catastrophic wildfire:
1. Low-intensity hotspots may represent controlled agricultural residue burning, trash incineration, or prescribed forest burns.
2. High-reflectance industrial surfaces, solar panels, and warm desert bare soil can occasionally trigger false alarms.
3. True active wildfires require validation through multi-temporal passes, contextual fire weather, and persistence clustering.
""",

    'knowledge/nasa/burned_area/burned_area_mapping.md': """---
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
""",

    'knowledge/datasets/MCD14ML/mcd14ml_product_guide.md': """---
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
""",

    'knowledge/datasets/VNP14IMGML/vnp14imgml_product_guide.md': """---
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
""",

    'knowledge/datasets/VJ114IMG/vj114img_product_guide.md': """---
source: NOAA/NASA JPSS Mission Office
title: VJ114IMG / VJ114IMGML Product Guide: NOAA-20 VIIRS 375m Active Fire
category: datasets
dataset: VJ114IMG
satellite: NOAA-20
date: 2024-02-15
chunk_index: 0
---

# VJ114IMG / VJ114IMGML Product Guide: NOAA-20 VIIRS 375m Active Fire

## Satellite Mission and Orbit
VJ114IMG represents the 375m active fire product from the VIIRS sensor aboard NOAA-20 (formerly JPSS-1), launched in November 2017. NOAA-20 flies in the same orbital plane as Suomi-NPP but precedes or trails it by exactly 50 minutes.

## Dual-Satellite 50-Minute Observation Advantage
Because NOAA-20 and Suomi-NPP scan the same geographic territory 50 minutes apart:
1. **Fire Front Velocity**: EarthPulse tracks the progression vector of advancing flame perimeters between consecutive passes.
2. **False Positive Suppression**: Ephemeral glint anomalies do not persist across 50 minutes, allowing reliable automated filtering.
3. **Cloud Clearing**: Moving cloud decks often reveal active fires on the second pass that were obscured 50 minutes earlier.
""",

    'knowledge/datasets/VJ214IMG/vj214img_product_guide.md': """---
source: NASA/NOAA JPSS Mission Office
title: VJ214IMG / VJ214IMGML Product Guide: NOAA-21 VIIRS 375m Active Fire
category: datasets
dataset: VJ214IMG
satellite: NOAA-21
date: 2024-02-15
chunk_index: 0
---

# VJ214IMG / VJ214IMGML Product Guide: NOAA-21 VIIRS 375m Active Fire

## NOAA-21 Operational Integration
VJ214IMG delivers 375m active fire data from NOAA-21 (JPSS-2, launched in November 2022). With NOAA-21 operational, the VIIRS constellation comprises three polar-orbiting instruments (Suomi-NPP, NOAA-20, NOAA-21).

## Global Revisit Rate Enhancement
The inclusion of NOAA-21 shortens daytime and nighttime revisit latency, providing global coverage approximately every 4 to 6 hours. This dense temporal sampling bridges the gap between low-earth-orbit spatial sharpness and geostationary temporal monitoring.
""",

    'knowledge/datasets/MCD64A1/mcd64a1_burned_area.md': """---
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
""",

    'knowledge/datasets/VNP64A1/vnp64a1_burned_area.md': """---
source: NASA LP DAAC VIIRS Burned Area User Guide
title: VNP64A1 Product Guide: VIIRS 500m Global Burned Area
category: datasets
dataset: VNP64A1
satellite: Suomi-NPP
date: 2024-02-20
chunk_index: 0
---

# VNP64A1 Product Guide: VIIRS 500m Global Burned Area

## Description and Harmonization Continuity
VNP64A1 is the VIIRS counterpart to the long-running MODIS MCD64A1 product. Produced at 500-meter resolution using Suomi-NPP surface reflectance and 375m active fire priors (VNP14IMGML), it guarantees climate-data record continuity as MODIS Terra and Aqua approach spacecraft decommissioning.
""",

    'knowledge/project/architecture/earthpulse_architecture.md': """---
source: EarthPulse System Architecture Documentation
title: EarthPulse 3D Project Architecture and Technical Topology
category: project_architecture
dataset: EARTHPULSE_CORE
satellite: Multi-Sensor
date: 2024-03-01
chunk_index: 0
---

# EarthPulse 3D Project Architecture and Technical Topology

## System Components
EarthPulse 3D is engineered as a unified full-stack geospatial telemetry platform:
1. **Client Tier**:
   - CesiumJS 3D Virtual Globe: Renders planetary terrain, Google Earth satellite basemaps, and thermal anomaly billboards.
   - 2D NASA FIRMS GIS Morph: Equirectangular projection for global tabular review.
   - Glassmorphism HUD: Real-time telemetry meters, sensor breakdown bars, time-range scrubber.
   - MediaPipe WASM: Touchless AI hand tracking for orbital navigation.
2. **Application Tier (FastAPI)**:
   - Dynamic Spatial Index (`spatial_index.py`): Debounced camera bounding box (`north`, `south`, `east`, `west`) filtering with 5-stage altitude Level-of-Detail (LOD).
   - Multi-Sensor Harmonization Pipeline (`HarmonizationPipeline`): 5-node automated state machine standardizing MODIS and VIIRS feeds.
   - Predictive ML Engine (`FireSpreadPredictor`): XGBoost classifier predicting 24h/48h fire propagation probability isolines.
   - Prescriptive RL Engine (`rl_dispatcher.py`): PPO agent calculating aerial tanker retardant drops and bulldozer firebreaks.
3. **Database & Storage Tier**:
   - PostgreSQL + pgvector: Stores technical documents with 1536-dimensional embeddings for RAG, indexed with HNSW cosine distance.
   - Persistent Chat Storage: Session-based conversation histories and source attribution.
   - NASA FIRMS NRT CSV Cache: Local caching of 24h satellite feeds.
""",

    'knowledge/project/methodology/h3_and_dbscan.md': """---
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
""",

    'knowledge/project/harmonization/modis_viirs_harmonization.md': """---
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
""",

    'knowledge/project/faq/bangladesh_fire_analysis.md': """---
source: Bangladesh Forest Department & EarthPulse Regional Analysis
title: Bangladesh Wildfire and Agricultural Fire Analysis
category: regional_telemetry
dataset: BANGLADESH_SECTOR
satellite: MODIS, VIIRS
date: 2024-03-05
chunk_index: 0
---

# Bangladesh Wildfire and Agricultural Fire Analysis

## Regional Geography and Spatial Bounding Box
- Latitude Range: 20.5° N to 26.5° N
- Longitude Range: 88.0° E to 92.8° E

## Seasonal Fire Profile and Primary Drivers
Unlike catastrophic crown fires in California or Australia, thermal anomalies in Bangladesh are characterized by:
1. **Seasonal Agricultural Residue Burning (Post-Harvest Stubble)**:
   - Peak Activity: February through April (late winter into dry pre-monsoon).
   - Major Zones: Rangpur, Rajshahi, Dinajpur, and Mymensingh plains following Boro and Aman rice harvesting. Farmers burn crop residue to rapidly clear fields for next-cycle planting.
2. **Chittagong Hill Tracts (CHT) Shifting Cultivation (Jhum)**:
   - Districts: Bandarban, Rangamati, Khagrachhari.
   - Slash-and-burn clearing on steep hill slopes creates distinct clusters of high-slope, low-to-moderate FRP hotspots.
3. **Sundarbans Mangrove Buffer Monitoring**:
   - The Sundarbans is a UNESCO World Heritage site and sensitive tidal halophytic mangrove ecosystem. True wildland fires are historically rare in wet mangrove cores, but fires occur on the drier eastern fringe (Chandpai and Sarankhola ranges in Bagerhat) during dry spells.
   - EarthPulse maintains an automated telemetry buffer around the Sundarbans to alert forest officials to thermal anomalies immediately.

## Typical FRP Profile in Bangladesh
Hotspot detections across Bangladesh exhibit low to moderate intensity:
- Average FRP: 15 to 45 MW.
- Rare Peak FRP: 60 to 95 MW (usually concentrated slash piles in dry seasons).
- Dominant Sensor: VIIRS 375m detects ~75% of events due to the localized, small-scale nature of agricultural burning.
""",

    'knowledge/ml/xgboost/spatial_block_holdout.md': """---
source: EarthPulse Machine Learning Engineering Spec
title: Zero-Leakage Spatial Block Holdout ML and XGBoost Engine
category: machine_learning
dataset: ML_XGBOOST
satellite: Multi-Sensor
date: 2024-03-05
chunk_index: 0
---

# Zero-Leakage Spatial Block Holdout ML and XGBoost Engine

## The Problem of Spatial Autocorrelation Leakage
In wildfire geospatial machine learning, traditional random K-Fold cross-validation suffers from severe data leakage. According to Tobler's First Law of Geography, spatial coordinates near an active fire share almost identical fuel moisture, vegetation density, and wind vectors. 
When training and test samples are split randomly, the model 'memorizes' test point outcomes from immediate neighbors, producing artificially inflated metrics (ROC-AUC > 0.96) that collapse in real-world deployment on unseen regions.

## EarthPulse Spatial Block Holdout Strategy
EarthPulse enforces **Spatial Block Holdout**:
- The geographic domain is partitioned into contiguous 50 km × 50 km spatial grid blocks.
- Entire blocks are assigned to either the training set or test set without geographic overlap.
- This forces the model to generalize fire spread dynamics to completely unseen terrain.

## Model Architecture
- Algorithm: XGBoost Classifier with ARM64 histogram tree-building engine (`hist`).
- Hardware Acceleration: Apple Metal Performance Shaders (MPS) PyTorch GPU training.
- Class Weighting: `scale_pos_weight = 14.2` to counter severe wildfire sparsity (less than 2% of pixels are active fires).
- Evaluation Metric: PR-AUC (Precision-Recall AUC = 0.84), which penalizes false alarms in skewed data far more reliably than ROC-AUC.
""",

    'knowledge/ml/features/weather_and_dem_features.md': """---
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
""",

    'knowledge/ml/evaluation/pr_auc_and_class_imbalance.md': """---
source: EarthPulse ML Metrics Guide
title: Model Evaluation: PR-AUC vs ROC-AUC in Severe Wildfire Class Imbalance
category: machine_learning
dataset: ML_EVALUATION
satellite: Multi-Sensor
date: 2024-03-05
chunk_index: 0
---

# Model Evaluation: PR-AUC vs ROC-AUC in Severe Wildfire Class Imbalance

## Why ROC-AUC is Misleading for Wildfire Modeling
Wildfires are extremely rare spatio-temporal events: across 1,000,000 spatial pixels, perhaps only 500 are actively burning (0.05% positive class prevalence).
The Receiver Operating Characteristic (ROC) curve plots True Positive Rate vs False Positive Rate:
FPR = FP / (FP + TN)
Because the number of True Negatives (TN) is immense, even tens of thousands of False Positive false alarms will result in an FPR close to 0.0, yielding a deceptively high ROC-AUC of 0.95+ while flooding firefighters with false alarms.

## Precision-Recall Curve (PR-AUC)
The Precision-Recall curve focuses strictly on the minority positive class:
- Precision = TP / (TP + FP)
- Recall = TP / (TP + FN)
Any false alarm directly reduces precision. EarthPulse achieves a rigorous **PR-AUC of 0.84** under 50km spatial block holdout validation, ensuring that high-risk alert zones are actionable and reliable.
"""
}

for path_str, content in docs.items():
    p = Path(path_str)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, 'w', encoding='utf-8') as f:
        f.write(content.strip() + '\n')
    print(f'Wrote: {path_str}')

print('All 17 knowledge documents generated successfully.')
