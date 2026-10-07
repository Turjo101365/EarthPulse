"""
Harmonization Module: Multi-Sensor Active Fire Detections (MODIS 1km + VIIRS 375m)
H3 Hexagonal Grid Indexing, Temporal KDTree Matching, and DBSCAN FRP Calibration
"""

from .pipeline import HarmonizationPipeline, HarmonizationState
from .h3_indexer import H3Indexer
from .firms_ingest import get_real_satellite_detections, get_seed_satellite_detections

__all__ = [
    "HarmonizationPipeline",
    "HarmonizationState",
    "H3Indexer",
    "get_real_satellite_detections",
    "get_seed_satellite_detections"
]
