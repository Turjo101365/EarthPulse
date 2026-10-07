---
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
