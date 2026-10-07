"""
ML Harmonization Model for Multi-Sensor Active Fire Detections (MODIS & VIIRS)

Harmonizes observations between:
- MODIS (Terra/Aqua, 1km spatial resolution)
- VIIRS (S-NPP/NOAA-20, 375m spatial resolution)

Computes normalized Fire Radiative Power (FRP), fused fire confidence,
and risk classification level.
"""

from typing import Dict, Any
import math

class MLHarmonizer:
    def __init__(self):
        # Sensor specific calibration factors (derived from NASA FIRMS validation studies)
        self.sensor_calibration = {
            "MODIS_TERRA": {"frp_scale": 1.00, "spatial_res_m": 1000, "base_confidence_weight": 0.85},
            "MODIS_AQUA":  {"frp_scale": 1.02, "spatial_res_m": 1000, "base_confidence_weight": 0.88},
            "VIIRS_SNPP":  {"frp_scale": 0.89, "spatial_res_m": 375,  "base_confidence_weight": 0.95},
            "VIIRS_NOAA20": {"frp_scale": 0.87, "spatial_res_m": 375,  "base_confidence_weight": 0.96},
        }

    def harmonize_detection(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        """
        Harmonizes a single raw satellite detection into a standardized hotspot record.
        """
        sensor = raw.get("sensor", "VIIRS_SNPP")
        calib = self.sensor_calibration.get(sensor, {"frp_scale": 0.90, "spatial_res_m": 500, "base_confidence_weight": 0.90})

        raw_frp = float(raw.get("frp", 10.0))
        raw_confidence = float(raw.get("confidence", 70.0))
        brightness = float(raw.get("brightness", 320.0)) # Kelvin

        # Harmonized FRP calculation: aligns VIIRS 375m sensitivity with MODIS 1km benchmark
        harmonized_frp = round(raw_frp * calib["frp_scale"], 2)

        # ML-based Fire Probability calculation (Sigmoid fusion of brightness temp, FRP, and sensor confidence)
        # Log-scaled FRP + Temperature delta above typical ambient (300K)
        temp_delta = max(0.0, brightness - 300.0)
        z = (0.04 * temp_delta) + (0.05 * math.log1p(harmonized_frp)) + (0.03 * (raw_confidence - 50.0))
        ml_probability = round(1.0 / (1.0 + math.exp(-z)), 3)

        # Risk Classification
        if harmonized_frp >= 100.0 or ml_probability >= 0.95:
            risk_level = "CRITICAL"
            color_hex = "#ff1744" # Vivid Red/Magenta
        elif harmonized_frp >= 40.0 or ml_probability >= 0.85:
            risk_level = "HIGH"
            color_hex = "#ff5722" # Bright Orange-Red
        elif harmonized_frp >= 15.0 or ml_probability >= 0.65:
            risk_level = "MODERATE"
            color_hex = "#ff9800" # Orange
        else:
            risk_level = "LOW"
            color_hex = "#ffeb3b" # Yellow

        return {
            "id": raw.get("id"),
            "latitude": round(raw.get("latitude", 0.0), 5),
            "longitude": round(raw.get("longitude", 0.0), 5),
            "sensor": sensor,
            "sensor_family": "MODIS" if "MODIS" in sensor else "VIIRS",
            "resolution_m": calib["spatial_res_m"],
            "raw_frp": raw_frp,
            "harmonized_frp": harmonized_frp,
            "confidence": raw_confidence,
            "brightness_k": brightness,
            "ml_probability": ml_probability,
            "risk_level": risk_level,
            "color_hex": color_hex,
            "timestamp": raw.get("timestamp"),
            "day_offset": raw.get("day_offset", 0),
            "daynight": raw.get("daynight", "D"),
            "country": raw.get("country", "Global"),
            "region": raw.get("region", "Unknown"),
            "land_cover": raw.get("land_cover", "Agricultural/Vegetation"),
        }

harmonizer = MLHarmonizer()
