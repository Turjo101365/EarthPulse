"""
Fire Spread Predictor & Contour Generator
Generates 24h and 48h fire propagation probability isolines and H3 forecast grids
for 3D Cesium terrain draping.
"""

from typing import List, Dict, Any, Tuple
import math
from .model import fire_ml_model
from ..harmonizer.h3_indexer import h3_indexer

class FireSpreadPredictor:
    def __init__(self):
        self.ml_model = fire_ml_model

    def forecast_spread(
        self,
        lat: float,
        lon: float,
        frp: float = 85.0,
        wind_speed_ms: float = 12.0,
        wind_direction_deg: float = 225.0,  # SW wind pushing NE
        dem_slope_deg: float = 24.0,
        hours_ahead: int = 24
    ) -> Dict[str, Any]:
        """
        Calculates 24h or 48h fire propagation probability grid and contour polygons.
        Models elliptical Huygens wavefront driven by wind vector and slope.
        """
        # Wind pushes fire downwind (wind_direction is where wind comes from; spread is direction + 180)
        spread_azimuth_deg = (wind_direction_deg + 180.0) % 360.0
        spread_azimuth_rad = math.radians(spread_azimuth_deg)

        # Rate of spread (km/h) based on Rothermel simplified model
        # Base spread + wind multiplier + slope factor (uphill burns faster: e^(0.069 * slope))
        slope_factor = math.exp(0.045 * min(45.0, dem_slope_deg))
        wind_factor = 1.0 + 0.12 * (wind_speed_ms ** 1.3)
        frp_factor = 1.0 + math.log1p(frp) * 0.18

        ros_km_h = round(0.18 * wind_factor * slope_factor * frp_factor, 2)
        total_distance_km = ros_km_h * hours_ahead

        # Length-to-width ratio of fire ellipse
        l_w_ratio = max(1.2, min(4.5, 1.0 + 0.15 * wind_speed_ms))

        semi_major_km = total_distance_km / 2.0
        semi_minor_km = semi_major_km / l_w_ratio

        # Ellipse center offset from ignition point towards spread azimuth
        offset_distance_km = semi_major_km * 0.75
        center_lat = lat + (offset_distance_km / 111.0) * math.cos(spread_azimuth_rad)
        center_lon = lon + (offset_distance_km / (111.0 * math.cos(math.radians(lat)))) * math.sin(spread_azimuth_rad)

        # Generate contour perimeter polygon points (24 points for smooth polygon)
        contour_coords: List[List[float]] = []
        n_points = 24
        for i in range(n_points):
            angle = 2.0 * math.pi * (i / n_points)
            # Unrotated ellipse coordinates (x = minor, y = major)
            ex = semi_minor_km * math.cos(angle)
            ey = semi_major_km * math.sin(angle)

            # Rotate ellipse by spread azimuth
            rx = ex * math.cos(spread_azimuth_rad) - ey * math.sin(spread_azimuth_rad)
            ry = ex * math.sin(spread_azimuth_rad) + ey * math.cos(spread_azimuth_rad)

            pt_lat = round(center_lat + (ry / 111.0), 6)
            pt_lon = round(center_lon + (rx / (111.0 * math.cos(math.radians(lat)))), 6)
            # GeoJSON format: [lon, lat]
            contour_coords.append([pt_lon, pt_lat])

        # Close the polygon ring
        contour_coords.append(contour_coords[0])

        # Predict probability at the leading edge using XGBoost
        u10 = round(wind_speed_ms * math.sin(spread_azimuth_rad), 2)
        v10 = round(wind_speed_ms * math.cos(spread_azimuth_rad), 2)
        fwi = round(min(98.0, 30.0 + wind_speed_ms * 2.5 + frp * 0.15), 1)

        features = [
            frp * 0.85,  # lag_frp
            fwi,
            max(15.0, 45.0 - wind_speed_ms),  # rh
            wind_speed_ms,
            u10,
            v10,
            dem_slope_deg,
            0.65,  # ndvi
            345.0  # brightness
        ]
        spread_probability = self.ml_model.predict_probability(features)

        # Surrounding H3 cells within the spread zone
        center_h3 = h3_indexer.point_to_h3(center_lat, center_lon, resolution=8)
        affected_h3_cells = h3_indexer.get_k_ring(center_h3, k=2)

        return {
            "origin": {"latitude": lat, "longitude": lon},
            "hours_ahead": hours_ahead,
            "ros_km_h": ros_km_h,
            "max_distance_km": round(total_distance_km, 2),
            "spread_probability": max(0.85, spread_probability),
            "spread_azimuth_deg": round(spread_azimuth_deg, 1),
            "center": {"latitude": round(center_lat, 6), "longitude": round(center_lon, 6)},
            "contour_polygon": contour_coords,
            "affected_h3_count": len(affected_h3_cells),
            "affected_h3_cells": affected_h3_cells[:12],
            "risk_status": "CRITICAL SPREAD HAZARD" if spread_probability > 0.8 else "ELEVATED"
        }

fire_spread_predictor = FireSpreadPredictor()
