"""
Active Fire Hotspots Storage and Management (MODIS & VIIRS)

This module maintains the in-memory store for active fire hotspot records.
All hardcoded mock/synthetic generation logic has been removed.
Real satellite observations from MODIS and VIIRS will be harmonized
and loaded here according to user harmonization specifications.
"""

from typing import List, Dict, Any

# In-memory store for active fire hotspot detections
ALL_HOTSPOTS: List[Dict[str, Any]] = []

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
