"""
EarthPulse / FireGuard AI RAG Knowledge Base
Curated domain knowledge covering NASA FIRMS telemetry, sensor physics,
H3 spatial indexing, XGBoost spatial split ML, PPO reinforcement learning,
and ICS tactical suppression protocols.
"""

from typing import List, Dict, Any

KNOWLEDGE_DOCUMENTS: List[Dict[str, Any]] = [
    {
        "id": "doc_nasa_firms_sensors",
        "title": "NASA FIRMS Satellite Sensors: MODIS vs VIIRS Specification",
        "category": "remote_sensing",
        "tags": ["firms", "modis", "viirs", "satellite", "sensor", "resolution", "terra", "aqua", "snpp", "noaa20"],
        "content": (
            "NASA FIRMS (Fire Information for Resource Management System) operates two primary satellite sensor constellations: "
            "1. MODIS (Moderate Resolution Imaging Spectroradiometer) aboard NASA's Terra (morning pass) and Aqua (afternoon pass) satellites. "
            "MODIS detects thermal anomalies at 1,000-meter (1 km) spatial resolution at nadir using mid-infrared channels (3.9 µm and 11.0 µm). "
            "It provides a consistent 24-year climate baseline (2000 to present) but has a broader Point Spread Function. "
            "2. VIIRS (Visible Infrared Imaging Radiometer Suite) aboard Suomi-NPP and NOAA-20 (JPSS-1). "
            "VIIRS features 375-meter spatial resolution (I-bands: I4 at 3.74 µm and I5 at 11.45 µm), providing 3x sharper spatial resolution, "
            "detecting significantly smaller sub-pixel fires and flaming perimeters with lower optical distortion at swath edges. "
            "EarthPulse harmonizes both feeds onto equal-area H3 hexagonal cells to prevent artificial fire count spikes."
        )
    },
    {
        "id": "doc_frp_and_emissions",
        "title": "Fire Radiative Power (FRP), Biomass Combustion & Atmospheric Emissions",
        "category": "physics_emissions",
        "tags": ["frp", "power", "megawatts", "carbon", "co2", "methane", "ch4", "emissions", "burned_area", "energy"],
        "content": (
            "Fire Radiative Power (FRP), measured in Megawatts (MW), quantifies the rate of radiant thermal energy emitted by actively burning fires. "
            "Under the Wooster et al. (2005) formulation, the time-integral of FRP yields Fire Radiative Energy (FRE in Joules), "
            "which is directly proportional to biomass fuel combusted: Biomass Consumed (kg) ≈ C_rad × FRE, where C_rad ≈ 0.368 ± 0.015 kg/MJ. "
            "EarthPulse computes real-time biospheric impacts: "
            "- Estimated Burned Area: derived from FRP density and sensor spatial resolution footprint (km² and hectares). "
            "- Carbon Dioxide (CO₂): approximately 1,600 to 1,800 grams of CO₂ released per kilogram of dry biomass consumed. "
            "- Methane (CH₄): trace hydrocarbon emissions calculated at ~4.5 to 6.8 g CH₄/kg biomass, carrying 28x the 100-year GWP of CO₂. "
            "- Global Radiative Energy: aggregate Gigawatts (GW) of continuous thermal output."
        )
    },
    {
        "id": "doc_harmonization_pipeline",
        "title": "5-Node Multi-Sensor Harmonization Pipeline & Calibrated FRP",
        "category": "architecture",
        "tags": ["harmonization", "pipeline", "h3", "dbscan", "kdtree", "nodes", "calibrated_frp"],
        "content": (
            "EarthPulse executes an automated 5-Node Harmonization Pipeline to merge MODIS and VIIRS satellite feeds: "
            "Node 1 (node_ingest_and_validate): Ingests FIRMS feeds, validates geographic bounding boxes, filters cloud reflectance false positives. "
            "Node 2 (node_spatial_h3_matching): Indexes points onto Uber H3 equal-area hexagonal cells (Resolution 8: ~0.737 km²; Resolution 9: ~0.105 km²). "
            "Node 3 (node_temporal_window_match): Pairs multi-sensor observations using KDTree temporal distance within a ±30-minute coincidence window. "
            "Node 4 (node_duplicate_clustering_and_frp): Applies DBSCAN clustering (epsilon = 1000m, min_samples = 2) to merge overlapping detections, "
            "computing cross-calibrated Fire Radiative Power via: FRP_harmonized = 0.65 * FRP_viirs + 0.35 * FRP_modis, normalizing Point Spread Functions. "
            "Node 5 (node_feature_synthesis): Enriches fire events with ECMWF weather vectors (RH, Temp, 10m Wind U/V) and DEM elevation slopes."
        )
    },
    {
        "id": "doc_xgboost_spatial_split",
        "title": "Predictive Machine Learning: Zero-Leakage Spatial Block Holdout & XGBoost",
        "category": "machine_learning",
        "tags": ["xgboost", "ml", "spatial_split", "data_leakage", "autocorrelation", "pr_auc", "prediction", "forecast"],
        "content": (
            "Standard random K-Fold cross-validation suffers from severe spatial autocorrelation leakage in wildfire modeling, "
            "producing artificially inflated accuracy by testing on coordinates immediately adjacent to training points. "
            "EarthPulse implements Spatial Block Holdout: the geographic domain is partitioned into contiguous 50 km × 50 km blocks. "
            "Entire spatial blocks are isolated for testing, proving true out-of-region generalization skill. "
            "Model: XGBoost Classifier with histogram tree-building method (ARM64 multi-core) and PyTorch Apple Metal Performance Shaders (MPS). "
            "Key hyperparameter: scale_pos_weight = 14.2 to handle wildfire sparsity. "
            "Evaluation Metric: PR-AUC (Precision-Recall AUC = 0.84), which penalizes false alarms in extreme imbalance far better than ROC-AUC. "
            "Features: Lag-FRP (t-24h), Fire Weather Index (FWI), Relative Humidity, Wind vector alignment, DEM slope, and NDVI fuel index."
        )
    },
    {
        "id": "doc_reinforcement_learning_ppo",
        "title": "Prescriptive Reinforcement Learning: PPO Agent & Wildfire Suppression Env",
        "category": "reinforcement_learning",
        "tags": ["rl", "ppo", "reinforcement_learning", "suppression", "tanker", "bulldozer", "dispatch", "reward"],
        "content": (
            "Rather than merely displaying passive fire heatmaps, FireGuard AI employs Reinforcement Learning (PPO - Proximal Policy Optimization) "
            "to autonomously prescribe optimal firefighting suppression tactics inside a custom Gymnasium environment (`WildfireSuppressionEnv`). "
            "Action Space: Discrete tuple [Unit_ID, Target_H3_Cell, Action_Type], where Action_Type represents: "
            "0 = Aerial Retardant Drop (DC-10 Air Tanker: drops long-term chemical retardant ahead of the fire front), "
            "1 = Bulldozer Fireline Construction (Heavy ground machinery clearing mineral soil breaks), "
            "2 = Evacuation Corridor Enforcement (Securing civilian egress routes). "
            "Reward Formulation: R = -1.0 * (new_burned_hectares) - 100.0 * (structures_threatened) - 0.15 * (flight_fuel_cost) + 80.0 * (containment_established). "
            "The PPO policy learns to exploit natural terrain barriers and establish containment 1.5–2 hours ahead of convective flame fronts."
        )
    },
    {
        "id": "doc_tactical_ics_containment",
        "title": "Incident Command System (ICS): Wildland Fireline Strategy & Ridge Containment",
        "category": "tactical_playbooks",
        "tags": ["ics", "tactics", "ridge", "containment", "air_tanker", "fireline", "windward", "leeward", "topography"],
        "content": (
            "Standard Incident Command System (ICS) wildland fire suppression protocols dictate: "
            "1. Ridge Containment Rule: Fires burning uphill accelerate dramatically due to preheating of fuels by convective thermal plumes. "
            "Direct attack on the flame front during uphill runs is prohibited when flame lengths exceed 8 feet (2.4 m). "
            "Suppression forces must anchor retardant drops and bulldozer lines along reverse mountain ridges (leeward slopes) "
            "exploiting natural rocky outcrops and road barriers where uphill wind velocity diminishes. "
            "2. Anchor and Flank: Containment begins from an anchor point (lake, barren rock, highway) and progresses along the flanks "
            "pinching inward to narrow the active head of the fire. "
            "3. Aerial Retardant Drops: Air Tankers must lay contiguous retardant swaths at least 1.5x the anticipated flame length ahead of the head."
        )
    },
    {
        "id": "doc_observability_langsmith_grafana",
        "title": "Enterprise Observability: Grafana Prometheus Telemetry & LangSmith Traces",
        "category": "observability",
        "tags": ["grafana", "prometheus", "langsmith", "telemetry", "hallucination", "guardrail", "audit"],
        "content": (
            "FireGuard AI integrates enterprise-grade operational observability: "
            "1. Grafana + Prometheus: Scrapes operational metrics at `/metrics`, monitoring active FRP intensity, "
            "PostGIS spatial query latency (p95 < 45ms), RL episode rewards (+492), and FIRMS ingestion lag (<140s) at `http://localhost:3000/d/fireguard-ops`. "
            "2. LangSmith LLM Tracing: Traces every tactical copilot order and chatbot interaction, logging latency, prompt/completion tokens, "
            "and strict anti-hallucination verification. Every advisory is checked against real telemetry and topographical constraints, "
            "ensuring 100% grounded facts with zero hallucinated emergency orders."
        )
    },
    {
        "id": "doc_regional_wildfire_hotspots",
        "title": "Global Wildfire Epicenters: Vulnerable Biomes & Regional Fire Dynamics",
        "category": "geography",
        "tags": ["bangladesh", "chittagong", "sundarbans", "amazon", "california", "pantanal", "congo", "greece", "australia"],
        "content": (
            "Key global wildfire zones monitored by EarthPulse: "
            "1. Bangladesh & South Asia: Seasonal agricultural biomass burning and localized clearing in Chittagong Hill Tracts (CHT) "
            "and periphery of the Sundarbans mangrove forest. Typically low to moderate FRP (15–60 MW) with dense smoke particulates. "
            "2. Amazon Basin & Pantanal (Brazil/Bolivia): Massive deforestation and savanna fires during dry season (July–October), "
            "producing extreme FRP peaks (>800 MW) and gigatons of CO₂ emissions. "
            "3. California & Western US: Chaparral shrub and mixed conifer fires driven by dry foehn winds (Santa Ana, Diablo) with extreme rates of spread. "
            "4. Congo Basin (Central Africa): Extensive agricultural shifting-cultivation fires, high detection density but moderate individual FRP. "
            "5. Mediterranean Arc (Greece, Spain): Extreme heatwave-driven wildfire runs through pine forests and maquis shrublands."
        )
    },
    {
        "id": "doc_earthpulse_lod_and_architecture",
        "title": "EarthPulse 3D: Camera-Driven Viewport Querying & 5-Stage LOD Hierarchy",
        "category": "architecture",
        "tags": ["cesium", "lod", "quadtree", "viewport", "camera", "altitude", "frontend", "fastapi"],
        "content": (
            "EarthPulse uses a camera-driven spatial querying paradigm: "
            "As the user navigates the CesiumJS 3D Earth, the camera transmits its visible bounding box (North, South, East, West) and altitude to `/api/hotspots`. "
            "The backend dynamically evaluates 5 Level-of-Detail (LOD) tiers: "
            "- LOD 1 (Space View, >3,500 km): Macro planetary density clusters and global aggregates. "
            "- LOD 2 (Continental View, 1,200–3,500 km): Continental clustering with regional centroids. "
            "- LOD 3 (Country / State View, 300–1,200 km): Division/state groupings with high-risk highlighting. "
            "- LOD 4 (District / County View, 50–300 km): Individual MODIS & VIIRS satellite detections. "
            "- LOD 5 (Close Inspection, <50 km): High-precision telemetry inspection with weather vectors and FRP heat points."
        )
    }
]
