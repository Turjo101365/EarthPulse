"""
H3 Hexagonal Grid Indexer for Multi-Sensor Fire Observations
Normalizes variable satellite footprints (MODIS 1000m, VIIRS 375m)
onto equal-area discrete global hexagonal cells.
"""

from typing import List, Tuple, Dict, Any, Optional
import h3

class H3Indexer:
    def __init__(self, default_resolution: int = 8):
        self.default_resolution = default_resolution

    def point_to_h3(self, lat: float, lon: float, resolution: Optional[int] = None) -> str:
        """Encodes latitude and longitude into an H3 hex string."""
        res = resolution if resolution is not None else self.default_resolution
        return h3.latlng_to_cell(lat, lon, res)

    def h3_to_point(self, h3_index: str) -> Tuple[float, float]:
        """Decodes H3 cell into center (latitude, longitude)."""
        lat, lon = h3.cell_to_latlng(h3_index)
        return round(lat, 6), round(lon, 6)

    def h3_to_boundary(self, h3_index: str) -> List[List[float]]:
        """
        Returns polygon coordinates [[lon, lat], ...] for Cesium / GeoJSON rendering.
        Note: Cesium / GeoJSON convention is [lon, lat].
        """
        boundary = h3.cell_to_boundary(h3_index)
        # boundary is tuple of (lat, lon) pairs
        return [[round(pt[1], 6), round(pt[0], 6)] for pt in boundary]

    def get_k_ring(self, h3_index: str, k: int = 1) -> List[str]:
        """Returns adjacent neighborhood cells within k hops."""
        return list(h3.grid_disk(h3_index, k))

    def resolution_for_altitude(self, altitude_m: float) -> int:
        """
        Selects optimal H3 resolution based on camera altitude.
        High orbit: res 6 (~36 km²)
        Regional: res 8 (~0.7 km²)
        Close inspect: res 9 (~0.1 km²)
        """
        if altitude_m > 3_000_000:
            return 6
        elif altitude_m > 500_000:
            return 7
        elif altitude_m > 100_000:
            return 8
        else:
            return 9

h3_indexer = H3Indexer()
