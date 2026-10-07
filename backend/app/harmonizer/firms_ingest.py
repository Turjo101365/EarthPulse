"""
Real NASA FIRMS Satellite Telemetry Ingestion Engine
Ingests authentic, near real-time satellite active fire observations directly from:
- NASA EOSDIS MODIS C6.1 (Terra & Aqua, 1km spatial resolution)
- NASA VIIRS C2 (Suomi-NPP & NOAA-20, 375m spatial resolution)
Cached locally in backend/cache/firms/ for offline resilience and sub-second loading.
Zero synthetic random generation.
"""

import os
import csv
import urllib.request
from typing import List, Dict, Any, Tuple
from datetime import datetime, timezone
from pathlib import Path

CACHE_DIR = Path(__file__).resolve().parent.parent.parent / "cache" / "firms"

FIRMS_URLS = {
    "modis_24h.csv": "https://firms.modaps.eosdis.nasa.gov/data/active_fire/modis-c6.1/csv/MODIS_C6_1_Global_24h.csv",
    "viirs_snpp_24h.csv": "https://firms.modaps.eosdis.nasa.gov/data/active_fire/suomi-npp-viirs-c2/csv/SUOMI_VIIRS_C2_Global_24h.csv",
    "viirs_noaa20_24h.csv": "https://firms.modaps.eosdis.nasa.gov/data/active_fire/noaa-20-viirs-c2/csv/J1_VIIRS_C2_Global_24h.csv"
}

def ensure_firms_data_downloaded():
    """Ensures real NASA FIRMS global CSV feeds are cached locally."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    headers = {"User-Agent": "FireGuardAI/2.0 (NASA Space Apps Geospatial Pipeline)"}

    for fname, url in FIRMS_URLS.items():
        dest = CACHE_DIR / fname
        if not dest.exists() or dest.stat().st_size == 0:
            try:
                print(f"Downloading real NASA FIRMS data: {fname}...")
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=20) as resp, open(dest, "wb") as out_f:
                    while chunk := resp.read(65536):
                        out_f.write(chunk)
            except Exception as e:
                print(f"Warning: Could not fetch {url}: {e}")

def parse_viirs_confidence(conf_val: str) -> float:
    """Converts categorical VIIRS confidence ('l', 'nominal', 'h') into percentage."""
    clean = str(conf_val).strip().lower()
    if clean in ("h", "high"):
        return 95.0
    elif clean in ("nominal", "n"):
        return 80.0
    elif clean in ("l", "low"):
        return 40.0
    try:
        return float(clean)
    except Exception:
        return 75.0

def get_real_satellite_detections(limit_per_sensor: int = 1500) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Parses genuine NASA FIRMS active fire records from MODIS and VIIRS CSV files if present.
    Returns (modis_detections, viirs_detections).
    """
    modis_detections: List[Dict[str, Any]] = []
    viirs_detections: List[Dict[str, Any]] = []

    # 1. Parse Real MODIS (Terra & Aqua)
    modis_file = CACHE_DIR / "modis_24h.csv"
    if modis_file.exists():
        with open(modis_file, "r", encoding="utf-8", errors="ignore") as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                try:
                    lat = float(row["latitude"])
                    lon = float(row["longitude"])
                    frp = float(row.get("frp", 1.0))
                    conf = float(row.get("confidence", 50.0))
                    bright = float(row.get("brightness", 310.0))
                    sat_code = row.get("satellite", "T")
                    sat_name = "MODIS_AQUA" if sat_code == "A" else "MODIS_TERRA"
                    acq_date = row.get("acq_date", "2026-10-06")
                    acq_time = row.get("acq_time", "1200").zfill(4)
                    iso_time = f"{acq_date}T{acq_time[:2]}:{acq_time[2:]}:00Z"

                    modis_detections.append({
                        "id": f"MODIS-{sat_code}-{count+1:05d}",
                        "latitude": lat,
                        "longitude": lon,
                        "frp": frp,
                        "confidence": conf,
                        "brightness": bright,
                        "sensor": sat_name,
                        "timestamp": iso_time,
                        "day_offset": 0,
                        "daynight": row.get("daynight", "D"),
                        "satellite": sat_name
                    })
                    count += 1
                    if count >= limit_per_sensor:
                        break
                except Exception:
                    continue

    # 2. Parse Real VIIRS (Suomi-NPP & NOAA-20)
    for v_file, sensor_name in [("viirs_snpp_24h.csv", "VIIRS_SNPP"), ("viirs_noaa20_24h.csv", "VIIRS_NOAA20")]:
        path = CACHE_DIR / v_file
        if path.exists():
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                reader = csv.DictReader(f)
                count = 0
                for row in reader:
                    try:
                        lat = float(row["latitude"])
                        lon = float(row["longitude"])
                        frp = float(row.get("frp", 1.0))
                        conf = parse_viirs_confidence(row.get("confidence", "nominal"))
                        bright = float(row.get("bright_ti4", 320.0))
                        acq_date = row.get("acq_date", "2026-10-06")
                        acq_time = row.get("acq_time", "1200").zfill(4)
                        iso_time = f"{acq_date}T{acq_time[:2]}:{acq_time[2:]}:00Z"

                        viirs_detections.append({
                            "id": f"{sensor_name}-{count+1:05d}",
                            "latitude": lat,
                            "longitude": lon,
                            "frp": frp,
                            "confidence": conf,
                            "brightness": bright,
                            "sensor": sensor_name,
                            "timestamp": iso_time,
                            "day_offset": 0,
                            "daynight": row.get("daynight", "D"),
                            "satellite": sensor_name
                        })
                        count += 1
                        if count >= (limit_per_sensor // 2):
                            break
                    except Exception:
                        continue

    return modis_detections, viirs_detections

# Alias for backwards compatibility
get_seed_satellite_detections = get_real_satellite_detections
