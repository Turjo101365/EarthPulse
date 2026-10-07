"""
Active Fire Hotspots Storage & User Dataset Loader
Zero synthetic or automated data generation.
Maintains the active in-memory hotspot catalog populated exclusively from the user's dataset.
"""

import os
import csv
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

DATA_DIR = Path(__file__).resolve().parent / "data"

# In-memory store for active fire hotspot detections
ALL_HOTSPOTS: List[Dict[str, Any]] = []
CURRENT_DATASET_META: Dict[str, Any] = {
    "loaded": False,
    "source": None,
    "count": 0,
    "columns_detected": [],
    "loaded_at": None,
}


def _normalize_row_keys(row: Dict[str, Any]) -> Dict[str, Any]:
    """Case-insensitively strips whitespace and lowercases dictionary keys."""
    return {str(k).strip().lower(): v for k, v in row.items()}


def _parse_confidence(val: Any) -> float:
    if val is None:
        return 80.0
    val_str = str(val).strip().lower()
    if val_str in ("h", "high"):
        return 95.0
    elif val_str in ("n", "nominal", "medium"):
        return 80.0
    elif val_str in ("l", "low"):
        return 50.0
    try:
        return min(100.0, max(0.0, float(val_str)))
    except (ValueError, TypeError):
        return 75.0


def _find_field(row: Dict[str, Any], candidates: List[str], default: Any = None) -> Any:
    for c in candidates:
        if c in row and row[c] not in (None, ""):
            return row[c]
    return default


def _transform_record(raw: Dict[str, Any], index: int) -> Optional[Dict[str, Any]]:
    norm = _normalize_row_keys(raw)

    # Latitude
    lat_val = _find_field(norm, ["latitude", "lat", "y", "lat_deg"])
    # Longitude
    lon_val = _find_field(norm, ["longitude", "lon", "lng", "long", "x", "lon_deg"])

    if lat_val is None or lon_val is None:
        return None

    try:
        lat = float(lat_val)
        lon = float(lon_val)
        if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
            return None
    except (ValueError, TypeError):
        return None

    # FRP / Intensity
    frp_val = _find_field(norm, ["frp", "fire_radiative_power", "intensity", "power", "radiative_power"], 15.0)
    try:
        frp = round(max(0.1, float(frp_val)), 2)
    except (ValueError, TypeError):
        frp = 15.0

    # Confidence
    conf_val = _find_field(norm, ["confidence", "conf", "probability", "certainty"])
    confidence = _parse_confidence(conf_val)

    # Brightness / Temp
    bright_val = _find_field(norm, ["brightness", "bright_ti4", "bright_t31", "temp", "temperature", "brightness_k"], 320.0)
    try:
        brightness = round(float(bright_val), 1)
    except (ValueError, TypeError):
        brightness = 320.0

    # Sensor / Satellite
    sensor = str(_find_field(norm, ["sensor", "satellite", "instrument", "source"], "CUSTOM_DATASET")).strip().upper()
    sensor_family = "MODIS" if "MODIS" in sensor else ("VIIRS" if "VIIRS" in sensor else "CUSTOM")

    # Timestamp
    date_str = str(_find_field(norm, ["acq_date", "date", "detection_date"], "")).strip()
    time_str = str(_find_field(norm, ["acq_time", "time", "detection_time"], "")).strip().zfill(4)
    timestamp = _find_field(norm, ["timestamp", "datetime", "iso_time"])
    if not timestamp:
        if date_str and time_str:
            timestamp = f"{date_str}T{time_str[:2]}:{time_str[2:4]}:00Z"
        elif date_str:
            timestamp = f"{date_str}T12:00:00Z"
        else:
            timestamp = datetime.now(timezone.utc).isoformat()

    # Day/Night
    daynight = str(_find_field(norm, ["daynight", "day_night", "dn"], "D")).strip().upper()
    if daynight not in ("D", "N"):
        daynight = "D"

    # Risk Classification
    if frp >= 100.0 or (frp >= 60.0 and confidence >= 85.0):
        risk_level = "CRITICAL"
        color_hex = "#ff1744"
    elif frp >= 40.0 or (frp >= 25.0 and confidence >= 75.0):
        risk_level = "HIGH"
        color_hex = "#ff5722"
    elif frp >= 15.0:
        risk_level = "MODERATE"
        color_hex = "#ff9800"
    else:
        risk_level = "LOW"
        color_hex = "#ffeb3b"

    rec_id = str(_find_field(norm, ["id", "objectid", "fid", "record_id"], f"FIRE-{index+1:06d}"))

    return {
        "id": rec_id,
        "latitude": round(lat, 5),
        "longitude": round(lon, 5),
        "frp": frp,
        "harmonized_frp": frp,
        "confidence": confidence,
        "brightness": brightness,
        "brightness_k": brightness,
        "sensor": sensor,
        "sensor_family": sensor_family,
        "satellite": sensor,
        "daynight": daynight,
        "risk_level": risk_level,
        "color_hex": color_hex,
        "timestamp": str(timestamp),
        "day_offset": 0,
        "country": str(_find_field(norm, ["country", "nation"], "Global")),
        "region": str(_find_field(norm, ["region", "state", "province"], "Active Zone")),
        "land_cover": str(_find_field(norm, ["land_cover", "biome", "vegetation"], "Vegetation")),
    }


def load_user_dataset(file_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Loads the user's custom wildfire dataset from the specified path or automatically
    finds custom dataset files in backend/data/.
    Supports CSV, JSON, and GeoJSON.
    Zero synthetic or mock data is generated.
    """
    global ALL_HOTSPOTS, CURRENT_DATASET_META

    target_files: List[Path] = []

    if file_path:
        p = Path(file_path).resolve()
        if p.is_file():
            target_files = [p]
        else:
            raise FileNotFoundError(f"Specified dataset file not found: {file_path}")
    else:
        # Auto-detect any dataset file placed directly in backend/data/ (top-level only)
        if DATA_DIR.exists():
            for pattern in ("*.csv", "*.json", "*.geojson"):
                candidates = sorted([f for f in DATA_DIR.glob(pattern) if f.is_file()])
                if candidates:
                    target_files = candidates
                    break

    if not target_files:
        print("[Dataset Loader] No custom dataset found in backend/data/. Active store remains empty.")
        ALL_HOTSPOTS = []
        CURRENT_DATASET_META = {
            "loaded": False,
            "source": None,
            "count": 0,
            "columns_detected": [],
            "loaded_at": None,
        }
        return ALL_HOTSPOTS

    records: List[Dict[str, Any]] = []
    cols_detected: List[str] = []

    for target_file in target_files:
        suffix = target_file.suffix.lower()
        if suffix == ".csv":
            with open(target_file, "r", encoding="utf-8", errors="ignore") as f:
                reader = csv.DictReader(f)
                if not cols_detected:
                    cols_detected = list(reader.fieldnames or [])
                for row in reader:
                    rec = _transform_record(row, len(records))
                    if rec:
                        records.append(rec)
        elif suffix in (".json", ".geojson"):
            with open(target_file, "r", encoding="utf-8", errors="ignore") as f:
                data = json.load(f)
                raw_list = []
                if isinstance(data, list):
                    raw_list = data
                elif isinstance(data, dict):
                    if "features" in data and isinstance(data["features"], list):
                        for feat in data["features"]:
                            props = dict(feat.get("properties", {}))
                            geom = feat.get("geometry", {})
                            if geom and geom.get("type") == "Point":
                                coords = geom.get("coordinates", [0, 0])
                                props["longitude"] = coords[0]
                                props["latitude"] = coords[1]
                            raw_list.append(props)
                    elif "data" in data and isinstance(data["data"], list):
                        raw_list = data["data"]
                    elif "records" in data and isinstance(data["records"], list):
                        raw_list = data["records"]

                if raw_list and isinstance(raw_list[0], dict) and not cols_detected:
                    cols_detected = list(raw_list[0].keys())
                for item in raw_list:
                    if isinstance(item, dict):
                        rec = _transform_record(item, len(records))
                        if rec:
                            records.append(rec)

    ALL_HOTSPOTS = records
    CURRENT_DATASET_META = {
        "loaded": True,
        "source": ", ".join(f.name for f in target_files),
        "filename": target_files[0].name if target_files else "",
        "count": len(records),
        "columns_detected": cols_detected,
        "loaded_at": datetime.now(timezone.utc).isoformat(),
    }

    print(f"[Dataset Loader] Loaded {len(records)} active fire records from user dataset")
    return ALL_HOTSPOTS


def get_all_hotspots() -> List[Dict[str, Any]]:
    """Returns the active hotspot records (loaded strictly from user dataset)."""
    return ALL_HOTSPOTS


def set_all_hotspots(hotspots: List[Dict[str, Any]]) -> None:
    """Sets the active hotspot records."""
    global ALL_HOTSPOTS
    ALL_HOTSPOTS = hotspots


def add_hotspots(hotspots: List[Dict[str, Any]]) -> None:
    """Appends new hotspots to active store."""
    global ALL_HOTSPOTS
    ALL_HOTSPOTS.extend(hotspots)


def clear_all_hotspots() -> None:
    """Clears all hotspot records and resets dataset status."""
    global ALL_HOTSPOTS, CURRENT_DATASET_META
    ALL_HOTSPOTS.clear()
    CURRENT_DATASET_META = {
        "loaded": False,
        "source": None,
        "count": 0,
        "columns_detected": [],
        "loaded_at": None,
    }


def get_dataset_info() -> Dict[str, Any]:
    """Returns metadata about currently loaded user dataset."""
    return {
        **CURRENT_DATASET_META,
        "active_hotspots_count": len(ALL_HOTSPOTS),
    }


def initialize_harmonized_hotspots() -> List[Dict[str, Any]]:
    """
    Legacy stub. Returns empty list. Zero automatic data generation or loading.
    """
    return ALL_HOTSPOTS

