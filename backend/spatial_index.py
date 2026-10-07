"""
Spatial Index and LOD (Level of Detail) Dynamic Aggregator

Filters hotspots within visible camera bounding box (North, South, East, West)
and aggregates data based on camera altitude (Space -> Continental -> Country -> City -> Close).
"""

from typing import List, Dict, Any, Tuple
import math
from collections import defaultdict
from .data_generator import ALL_HOTSPOTS

GLOBAL_COUNTRY_ANCHORS = [
    ("Bangladesh", 23.85, 90.35),
    ("India", 20.59, 78.96),
    ("Pakistan", 30.37, 69.34),
    ("China", 35.86, 104.19),
    ("Japan", 36.20, 138.25),
    ("Indonesia", -0.78, 113.92),
    ("Thailand", 15.87, 100.99),
    ("Malaysia", 4.21, 101.97),
    ("Saudi Arabia", 23.88, 45.07),
    ("United Arab Emirates", 23.42, 53.84),
    ("Turkey", 38.96, 35.24),
    ("Iran", 32.42, 53.68),
    ("Iraq", 33.22, 43.67),
    ("United Kingdom", 55.37, -3.43),
    ("Germany", 51.16, 10.45),
    ("France", 46.22, 2.21),
    ("Italy", 41.87, 12.56),
    ("Spain", 40.46, -3.74),
    ("Russia", 61.52, 105.31),
    ("Ukraine", 48.37, 31.16),
    ("Greece", 39.07, 21.82),
    ("Norway", 60.47, 8.46),
    ("Sweden", 60.12, 18.64),
    ("United States", 37.09, -95.71),
    ("Canada", 56.13, -106.34),
    ("Mexico", 23.63, -102.55),
    ("Brazil", -14.23, -51.92),
    ("Argentina", -38.41, -63.61),
    ("Chile", -35.67, -71.54),
    ("Colombia", 4.57, -74.29),
    ("Peru", -9.19, -75.01),
    ("South Africa", -30.55, 22.93),
    ("Egypt", 26.82, 30.80),
    ("Nigeria", 9.08, 8.67),
    ("DR Congo", -4.03, 21.75),
    ("Kenya", -0.02, 37.90),
    ("Morocco", 31.79, -7.09),
    ("Algeria", 28.03, 1.65),
    ("Australia", -25.27, 133.77),
    ("New Zealand", -40.90, 174.88),
    ("Arctic Region", 80.0, 0.0),
    ("Antarctica", -80.0, 0.0),
]

class SpatialHotspotIndex:
    def __init__(self, data: List[Dict[str, Any]] = None):
        self.hotspots = data if data is not None else ALL_HOTSPOTS
        # Pre-compute global summary statistics
        self.global_summary = self._compute_summary(self.hotspots, "Global Earth")

    def load_hotspots(self, new_data: List[Dict[str, Any]]) -> None:
        """Dynamically reload or replace hotspot catalog."""
        self.hotspots = new_data
        self.global_summary = self._compute_summary(self.hotspots, "Global Earth")

    def _in_bbox(self, lat: float, lon: float, north: float, south: float, east: float, west: float) -> bool:
        if not (south <= lat <= north):
            return False
        if west <= east:
            return west <= lon <= east
        else:
            return lon >= west or lon <= east

    def _compute_summary(self, points: List[Dict[str, Any]], region_name: str) -> Dict[str, Any]:
        total = len(points)
        if total == 0:
            return {
                "region_name": region_name,
                "total_hotspots": 0,
                "modis_count": 0,
                "viirs_count": 0,
                "avg_frp": 0.0,
                "max_frp": 0.0,
                "high_confidence_count": 0,
                "high_risk_count": 0,
                "burned_area_sqkm": 0.0,
                "carbon_co2_mt": 0.0,
                "total_energy_gw": 0.0,
            }

        modis = sum(1 for p in points if p["sensor_family"] == "MODIS")
        viirs = total - modis
        total_frp = sum(p["harmonized_frp"] for p in points)
        avg_frp = round(total_frp / total, 1)
        max_frp = round(max(p["harmonized_frp"] for p in points), 1)
        high_conf = sum(1 for p in points if p["confidence"] >= 80.0)
        high_risk = sum(1 for p in points if p["risk_level"] in ("HIGH", "CRITICAL"))

        # NASA Environmental Impact estimates
        burned_area_sqkm = round(total_frp * 0.082, 1)
        carbon_co2_mt = round(burned_area_sqkm * 0.0152, 2)
        total_energy_gw = round(total_frp / 1000.0, 2)

        return {
            "region_name": region_name,
            "total_hotspots": total,
            "modis_count": modis,
            "viirs_count": viirs,
            "avg_frp": avg_frp,
            "max_frp": max_frp,
            "high_confidence_count": high_conf,
            "high_risk_count": high_risk,
            "burned_area_sqkm": burned_area_sqkm,
            "carbon_co2_mt": carbon_co2_mt,
            "total_energy_gw": total_energy_gw,
        }

    def _determine_region_name(self, points: List[Dict[str, Any]], north: float, south: float, east: float, west: float) -> str:
        lat_span = abs(north - south)
        lon_span = abs(east - west) if west <= east else (360 - west + east)
        c_lat = (north + south) / 2.0
        c_lon = (east + west) / 2.0 if west <= east else ((west + east + 360) / 2.0) % 360

        if lat_span > 60.0 or lon_span > 100.0:
            return "Global Earth View"

        # Check Bangladesh specific sub-regions
        if 20.0 <= south and north <= 27.5 and 87.5 <= west and east <= 93.5:
            if lat_span < 1.5 and lon_span < 1.5:
                if 23.4 <= c_lat <= 24.3 and 90.0 <= c_lon <= 90.8:
                    return "Dhaka Metropolitan & Industrial Region"
                elif c_lat < 23.0 and c_lon > 91.5:
                    return "Chittagong Hill Tracts Region"
                elif c_lat < 22.8 and c_lon < 90.0:
                    return "Sundarbans Fringe & Khulna Coast"
                elif c_lat > 24.5 and c_lon > 91.2:
                    return "Sylhet Division & Tea Highlands"
                elif c_lat > 24.0 and c_lon < 89.5:
                    return "Rajshahi Agricultural Belt"
                return "Bangladesh Local Sector"
            return "Bangladesh"

        # If points are present, find dominant region name
        if points:
            region_counts = defaultdict(int)
            for p in points:
                region_counts[p.get("region", "Regional Sector")] += 1
            top_region = max(region_counts.items(), key=lambda x: x[1])[0]
            if lat_span > 20.0:
                return f"{top_region} & Surrounding Continents"
            else:
                return top_region

        # If no pre-baked points, determine nearest country from global anchors
        nearest_country = "Visible Geographic Region"
        min_dist = float("inf")
        for country, a_lat, a_lon in GLOBAL_COUNTRY_ANCHORS:
            dist = ((c_lat - a_lat) ** 2 + ((c_lon - a_lon) * math.cos(math.radians(c_lat))) ** 2) ** 0.5
            if dist < min_dist:
                min_dist = dist
                nearest_country = country

        if min_dist < 18.0:
            return f"{nearest_country} Sector"
        return "Visible Geographic Region"

    def _cluster_points(self, points: List[Dict[str, Any]], grid_size_deg: float) -> List[Dict[str, Any]]:
        """
        Groups points into grid cells to create LOD clusters.
        """
        grid = defaultdict(list)
        for p in points:
            gx = math.floor(p["longitude"] / grid_size_deg)
            gy = math.floor(p["latitude"] / grid_size_deg)
            grid[(gy, gx)].append(p)

        clusters = []
        cluster_id = 1
        for (gy, gx), group in grid.items():
            count = len(group)
            avg_lat = sum(p["latitude"] for p in group) / count
            avg_lon = sum(p["longitude"] for p in group) / count
            avg_frp = sum(p["harmonized_frp"] for p in group) / count
            modis_cnt = sum(1 for p in group if p["sensor_family"] == "MODIS")
            viirs_cnt = count - modis_cnt

            # Determine dominant risk
            if any(p["risk_level"] == "CRITICAL" for p in group) or avg_frp > 60:
                risk = "CRITICAL"
                color = "#ff1744"
            elif any(p["risk_level"] == "HIGH" for p in group) or avg_frp > 35:
                risk = "HIGH"
                color = "#ff5722"
            elif avg_frp > 15:
                risk = "MODERATE"
                color = "#ff9800"
            else:
                risk = "LOW"
                color = "#ffeb3b"

            clusters.append({
                "id": f"cluster_{cluster_id}",
                "is_cluster": True,
                "latitude": round(avg_lat, 5),
                "longitude": round(avg_lon, 5),
                "count": count,
                "modis_count": modis_cnt,
                "viirs_count": viirs_cnt,
                "avg_frp": round(avg_frp, 1),
                "risk_level": risk,
                "color_hex": color,
                "label": f"{count} Fires (Avg {round(avg_frp, 0)} MW)",
                # Cluster marker radius proportional to count
                "marker_size": min(48, max(16, int(14 + math.log10(count + 1) * 12))),
            })
            cluster_id += 1

        return clusters

    def query(
        self,
        north: float = 90.0,
        south: float = -90.0,
        east: float = 180.0,
        west: float = -180.0,
        altitude: float = 10000000.0, # Camera height in meters
        sensor_filter: str = "ALL",
        min_frp: float = 0.0,
        time_range: str = "24h",
        daynight: str = "ALL",
    ) -> Dict[str, Any]:
        """
        Executes camera-driven spatial bounding box query with altitude-based LOD,
        temporal filtering (24h, 48h, 7d, or day index), and day/night satellite passes.
        """
        # Clamp inputs
        north = min(90.0, max(-90.0, north))
        south = min(90.0, max(-90.0, south))
        if south > north:
            south, north = north, south

        # Filter by bounding box, sensor, FRP, time_range, and daynight
        filtered = []
        for p in self.hotspots:
            if sensor_filter != "ALL" and p["sensor_family"] != sensor_filter:
                continue
            if p["harmonized_frp"] < min_frp:
                continue
            if daynight != "ALL" and p.get("daynight") != daynight:
                continue
            if time_range in ("24h", "live") and p.get("day_offset", 0) != 0:
                continue
            elif time_range == "48h" and p.get("day_offset", 0) > 1:
                continue
            elif time_range in ("7d", "all") and p.get("day_offset", 0) > 6:
                continue
            elif time_range.startswith("day_"):
                try:
                    target_day = int(time_range.split("_")[1])
                    if p.get("day_offset", 0) != target_day:
                        continue
                except Exception:
                    pass
            if self._in_bbox(p["latitude"], p["longitude"], north, south, east, west):
                filtered.append(p)

        region_name = self._determine_region_name(filtered, north, south, east, west)

        summary = self._compute_summary(filtered, region_name)

        # Determine Level of Detail (LOD) based on altitude
        if altitude > 3500000:
            # Space View: > 3500 km
            lod_level = 1
            lod_name = "Space View"
            lod_desc = "Global Aggregated Density"
            # Macro grid clustering (approx 8.0 degree cells)
            render_items = self._cluster_points(filtered, grid_size_deg=8.0)

        elif altitude > 1200000:
            # Continental View: 1200 km - 3500 km
            lod_level = 2
            lod_name = "Continental View"
            lod_desc = "Country / Sub-continental Clusters"
            # Medium grid clustering (approx 3.0 degree cells)
            render_items = self._cluster_points(filtered, grid_size_deg=3.0)

        elif altitude > 300000:
            # Country / Regional View: 300 km - 1200 km
            lod_level = 3
            lod_name = "Country View"
            lod_desc = "Regional / Division Hotspots"
            # Fine grid clustering (approx 0.8 degree cells)
            render_items = self._cluster_points(filtered, grid_size_deg=0.8)

        elif altitude > 50000:
            # City / District View: 50 km - 300 km
            lod_level = 4
            lod_name = "City / District View"
            lod_desc = "Individual MODIS & VIIRS Detections"
            # Return individual points (capped at 1200 for smooth 60fps)
            render_items = [
                {
                    **p,
                    "is_cluster": False,
                    "marker_size": min(28, max(12, int(8 + (p["harmonized_frp"] ** 0.5) * 2.2))),
                }
                for p in filtered[:1200]
            ]

        else:
            # Very Close / High-Precision View: < 50 km
            lod_level = 5
            lod_name = "High-Precision View"
            lod_desc = "Full Sensor Telemetry + FRP + ML Prob"
            # Full individual points with rich details
            render_items = [
                {
                    **p,
                    "is_cluster": False,
                    "marker_size": min(36, max(16, int(12 + (p["harmonized_frp"] ** 0.5) * 3))),
                }
                for p in filtered[:800]
            ]

        return {
            "lod": {
                "level": lod_level,
                "name": lod_name,
                "description": lod_desc,
                "altitude_km": round(altitude / 1000.0, 1),
            },
            "summary": summary,
            "items_count": len(render_items),
            "items": render_items,
        }

    def get_firms_analytics(self, time_range: str = "24h") -> Dict[str, Any]:
        """
        Computes broader NASA FIRMS Earth environmental analytics:
        - Global burned area (km² and hectares), carbon emissions (Mt CO2), total energy (GW)
        - Country leaderboard with top fire counts & burned area
        - 7-day historical time-series
        - Day/Night diurnal cycle breakdown
        - Key biome breakdown
        """
        from datetime import datetime, timezone, timedelta

        tr = time_range.lower()
        if tr in ("live", "24h"):
            active_pts = [p for p in self.hotspots if p.get("day_offset", 0) == 0]
        elif tr == "48h":
            active_pts = [p for p in self.hotspots if p.get("day_offset", 0) <= 1]
        elif tr.startswith("day_"):
            try:
                target_day = int(tr.split("_")[1])
                active_pts = [p for p in self.hotspots if p.get("day_offset", 0) == target_day]
            except Exception:
                active_pts = [p for p in self.hotspots if p.get("day_offset", 0) == 0]
        else: # "7d", "all"
            active_pts = [p for p in self.hotspots if p.get("day_offset", 0) <= 6]

        total_pts = len(active_pts)
        modis_cnt = sum(1 for p in active_pts if p["sensor_family"] == "MODIS")
        viirs_cnt = total_pts - modis_cnt
        total_frp = sum(p["harmonized_frp"] for p in active_pts)
        avg_frp = round(total_frp / max(1, total_pts), 1)

        # Environmental Impact formulas
        burned_sqkm = round(total_frp * 0.082, 1)
        burned_hectares = int(burned_sqkm * 100.0)
        carbon_co2_mt = round(burned_sqkm * 0.0152, 2)
        methane_ch4_kt = round(carbon_co2_mt * 4.5, 2)
        total_energy_gw = round(total_frp / 1000.0, 2)

        # Diurnal Day vs Night
        day_cnt = sum(1 for p in active_pts if p.get("daynight") == "D")
        night_cnt = total_pts - day_cnt

        # Country Leaderboard
        country_counts = defaultdict(lambda: {"count": 0, "frp": 0.0, "high_risk": 0})
        for p in active_pts:
            c = p.get("country", "Unknown")
            country_counts[c]["count"] += 1
            country_counts[c]["frp"] += p["harmonized_frp"]
            if p.get("risk_level") in ("HIGH", "CRITICAL"):
                country_counts[c]["high_risk"] += 1

        anchor_map = {name.lower(): (lat, lon) for name, lat, lon in GLOBAL_COUNTRY_ANCHORS}
        leaderboard = []
        for c_name, stats in sorted(country_counts.items(), key=lambda x: x[1]["count"], reverse=True):
            if c_name in ("Global", "Unknown"):
                continue
            c_cnt = stats["count"]
            c_frp = stats["frp"]
            c_burned = round(c_frp * 0.082, 1)
            coords = anchor_map.get(c_name.lower(), (20.0, 0.0))
            leaderboard.append({
                "country": c_name,
                "count": c_cnt,
                "pct_of_global": round((c_cnt / max(1, total_pts)) * 100.0, 1),
                "avg_frp": round(c_frp / max(1, c_cnt), 1),
                "burned_area_sqkm": c_burned,
                "high_risk": stats["high_risk"],
                "lat": coords[0],
                "lon": coords[1],
            })

        # 7-Day Trend Chart
        base_time = datetime(2026, 10, 3, 16, 30, tzinfo=timezone.utc)
        day_stats = defaultdict(lambda: {"count": 0, "frp": 0.0})
        for p in self.hotspots:
            d = p.get("day_offset", 0)
            if d <= 6:
                day_stats[d]["count"] += 1
                day_stats[d]["frp"] += p["harmonized_frp"]

        seven_day_trend = []
        for d in reversed(range(7)):
            d_date = (base_time - timedelta(days=d)).strftime("%b %d")
            d_cnt = day_stats[d]["count"]
            d_frp = day_stats[d]["frp"]
            seven_day_trend.append({
                "day_offset": d,
                "label": "Today" if d == 0 else f"-{d}d",
                "date": d_date,
                "count": d_cnt,
                "avg_frp": round(d_frp / max(1, d_cnt), 1) if d_cnt else 0,
                "burned_area_sqkm": round(d_frp * 0.082, 1),
            })

        # Biome / Region breakdown
        region_stats = defaultdict(int)
        for p in active_pts:
            region_stats[p.get("region", "Other")] += 1
        top_biomes = [
            {"region": r, "count": cnt, "pct": round((cnt / max(1, total_pts)) * 100, 1)}
            for r, cnt in sorted(region_stats.items(), key=lambda x: x[1], reverse=True)[:6]
        ]

        return {
            "time_range": time_range,
            "global_metrics": {
                "total_hotspots": total_pts,
                "modis_count": modis_cnt,
                "viirs_count": viirs_cnt,
                "avg_frp": avg_frp,
                "burned_area_sqkm": burned_sqkm,
                "burned_area_hectares": burned_hectares,
                "carbon_co2_mt": carbon_co2_mt,
                "methane_ch4_kt": methane_ch4_kt,
                "total_energy_gw": total_energy_gw,
            },
            "diurnal": {
                "day_count": day_cnt,
                "night_count": night_cnt,
                "day_pct": round((day_cnt / max(1, total_pts)) * 100.0, 1),
                "night_pct": round((night_cnt / max(1, total_pts)) * 100.0, 1),
            },
            "country_leaderboard": leaderboard[:12],
            "seven_day_trend": seven_day_trend,
            "top_biomes": top_biomes,
        }

# Global singleton index
spatial_index = SpatialHotspotIndex()
