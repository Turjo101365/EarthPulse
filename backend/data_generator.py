"""
Active Fire Hotspots Storage and Management (MODIS & VIIRS)
Populated dynamically by the Dual-Sensor Harmonization Pipeline.
"""

from typing import List, Dict, Any

# In-memory store for active fire hotspot detections
ALL_HOTSPOTS: List[Dict[str, Any]] = []

def initialize_harmonized_hotspots() -> List[Dict[str, Any]]:
    """
    Executes the 5-node harmonization pipeline across multi-sensor observations
    to seed the initial active fire catalog.
    """
    global ALL_HOTSPOTS
    try:
        from .app.harmonizer import HarmonizationPipeline, get_real_satellite_detections
        modis, viirs = get_real_satellite_detections(limit_per_sensor=1500)
        pipeline = HarmonizationPipeline()
        state = pipeline.run(modis, viirs)
        ALL_HOTSPOTS = state.postgis_record
    except Exception as e:
        print(f"Notice: Harmonization startup seeding error ({e})")
        ALL_HOTSPOTS = []
    return ALL_HOTSPOTS

def get_all_hotspots() -> List[Dict[str, Any]]:
    """Returns the current list of active hotspots."""
    return ALL_HOTSPOTS

def set_all_hotspots(hotspots: List[Dict[str, Any]]) -> None:
    """Replaces current hotspot store with new list."""
    global ALL_HOTSPOTS
    ALL_HOTSPOTS = hotspots

def add_hotspots(hotspots: List[Dict[str, Any]]) -> None:
    """Appends new hotspots to the active store."""
    global ALL_HOTSPOTS
    ALL_HOTSPOTS.extend(hotspots)

def clear_all_hotspots() -> None:
    """Clears all hotspot records."""
    global ALL_HOTSPOTS
    ALL_HOTSPOTS.clear()
