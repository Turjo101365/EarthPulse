"""
NASA FIRMS Active Fire Telemetry Loader
Loads and harmonizes real satellite observations from:
- MODIS (Terra & Aqua, 1km spatial resolution)
- VIIRS (Suomi-NPP & NOAA-20 / J1, 375m spatial resolution)

Fetches live global active fire CSVs directly from NASA FIRMS Open NRT archive,
caches them locally, and normalizes them into unified spatial records.
"""

import os
import csv
import time
import urllib.request
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Official NASA FIRMS Open Global 24h CSV endpoints
FIRMS_URLS = {
    "MODIS": "https://firms.modaps.eosdis.nasa.gov/data/active_fire/modis-c6.1/csv/MODIS_C6_1_Global_24h.csv",
    "VIIRS_SNPP": "https://firms.modaps.eosdis.nasa.gov/data/active_fire/suomi-npp-viirs-c2/csv/SUOMI_VIIRS_C2_Global_24h.csv",
    "VIIRS_NOAA20": "https://firms.modaps.eosdis.nasa.gov/data/active_fire/noaa-20-viirs-c2/csv/J1_VIIRS_C2_Global_24h.csv",
}

DEFAULT_CACHE_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "firms"


def ensure_cache_dir(cache_dir: Optional[Path] = None) -> Path:
    target = cache_dir or DEFAULT_CACHE_DIR
    target.mkdir(parents=True, exist_ok=True)
    return target


def download_firms_feed(sensor_key: str, dest_path: Path, max_age_hours: float = 12.0) -> bool:
    """
    Downloads a NASA FIRMS CSV file if not present or older than max_age_hours.
    Returns True if downloaded or valid cache exists, False on failure.
    """
    if dest_path.exists():
        file_age_hours = (time.time() - dest_path.stat().st_mtime) / 3600.0
        if file_age_hours < max_age_hours and dest_path.stat().st_size > 500:
            return True

    url = FIRMS_URLS.get(sensor_key)
    if not url:
        return False

    headers = {"User-Agent": "EarthPulse-Wildfire-System/2.0 (Academic/Research Client)"}
    req = urllib.request.Request(url, headers=headers)

    try:
        temp_dest = dest_path.with_suffix(".tmp")
        with urllib.request.urlopen(req, timeout=35) as resp, open(temp_dest, "wb") as f:
            while chunk := resp.read(65536):
                f.write(chunk)
        temp_dest.replace(dest_path)
        return True
    except Exception as e:
        print(f"[FIRMS Loader] Failed downloading {sensor_key} from {url}: {e}")
        if dest_path.exists():
            return True  # Use existing cache despite error
        return False


def parse_modis_csv(file_path: Path, max_rows: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Parses MODIS C6.1 CSV.
    Header: latitude,longitude,brightness,scan,track,acq_date,acq_time,satellite,confidence,version,bright_t31,frp,daynight
    """
    records = []
    if not file_path.exists():
        return records

    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if max_rows and i >= max_rows:
                break
            try:
                lat = float(row["latitude"])
                lon = float(row["longitude"])
                brightness = float(row.get("brightness", 310.0))
                bright_bg = float(row.get("bright_t31", 290.0))
                frp = float(row.get("frp", 10.0))
                raw_conf = float(row.get("confidence", 50.0))
                sat_code = row.get("satellite", "T").strip().upper()
                satellite_name = "MODIS_TERRA" if sat_code in ("T", "TERRA") else "MODIS_AQUA"
                daynight = row.get("daynight", "D").strip().upper()

                records.append({
                    "id": f"MODIS_{sat_code}_{row.get('acq_date', '')}_{i}",
                    "latitude": round(lat, 5),
                    "longitude": round(lon, 5),
                    "brightness": brightness,
                    "bright_bg": bright_bg,
                    "temp_diff": round(brightness - bright_bg, 2),
                    "frp": max(0.1, frp),
                    "confidence": min(100.0, max(0.0, raw_conf)),
                    "scan": float(row.get("scan", 1.0)),
                    "track": float(row.get("track", 1.0)),
                    "acq_date": row.get("acq_date", ""),
                    "acq_time": row.get("acq_time", ""),
                    "satellite": satellite_name,
                    "sensor_family": "MODIS",
                    "resolution_m": 1000,
                    "daynight": daynight,
                    "is_day": 1 if daynight == "D" else 0,
                })
            except (ValueError, KeyError):
                continue
    return records


def parse_viirs_csv(file_path: Path, sensor_name: str, max_rows: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Parses VIIRS 375m active fire CSV (Suomi-NPP or NOAA-20).
    Header: latitude,longitude,bright_ti4,scan,track,acq_date,acq_time,satellite,confidence,version,bright_ti5,frp,daynight
    """
    records = []
    if not file_path.exists():
        return records

    conf_map = {"l": 35.0, "low": 35.0, "n": 70.0, "nominal": 70.0, "h": 95.0, "high": 95.0}

    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if max_rows and i >= max_rows:
                break
            try:
                lat = float(row["latitude"])
                lon = float(row["longitude"])
                brightness = float(row.get("bright_ti4", 320.0))
                bright_bg = float(row.get("bright_ti5", 295.0))
                frp = float(row.get("frp", 8.0))

                conf_val_str = str(row.get("confidence", "nominal")).strip().lower()
                try:
                    conf = float(conf_val_str)
                except ValueError:
                    conf = conf_map.get(conf_val_str, 65.0)

                sat_code = row.get("satellite", "N").strip()
                daynight = row.get("daynight", "D").strip().upper()

                records.append({
                    "id": f"{sensor_name}_{row.get('acq_date', '')}_{i}",
                    "latitude": round(lat, 5),
                    "longitude": round(lon, 5),
                    "brightness": brightness,
                    "bright_bg": bright_bg,
                    "temp_diff": round(brightness - bright_bg, 2),
                    "frp": max(0.1, frp),
                    "confidence": min(100.0, max(0.0, conf)),
                    "scan": float(row.get("scan", 0.4)),
                    "track": float(row.get("track", 0.4)),
                    "acq_date": row.get("acq_date", ""),
                    "acq_time": row.get("acq_time", ""),
                    "satellite": sensor_name,
                    "sensor_family": "VIIRS",
                    "resolution_m": 375,
                    "daynight": daynight,
                    "is_day": 1 if daynight == "D" else 0,
                })
            except (ValueError, KeyError):
                continue
    return records


def load_all_firms_data(
    cache_dir: Optional[Path] = None,
    download_if_missing: bool = True,
    max_samples_per_sensor: Optional[int] = None
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Downloads and loads all 3 NASA FIRMS feeds (MODIS Terra/Aqua, VIIRS Suomi-NPP, VIIRS NOAA-20).
    Returns combined harmonized detections and ingestion statistics.
    """
    directory = ensure_cache_dir(cache_dir)
    stats: Dict[str, Any] = {"modis_count": 0, "viirs_snpp_count": 0, "viirs_noaa20_count": 0, "total": 0}

    # 1. MODIS Terra & Aqua
    modis_csv = directory / "MODIS_Global_24h.csv"
    if download_if_missing:
        download_firms_feed("MODIS", modis_csv)
    modis_records = parse_modis_csv(modis_csv, max_rows=max_samples_per_sensor)
    stats["modis_count"] = len(modis_records)

    # 2. VIIRS Suomi-NPP
    viirs_snpp_csv = directory / "SUOMI_VIIRS_Global_24h.csv"
    if download_if_missing:
        download_firms_feed("VIIRS_SNPP", viirs_snpp_csv)
    viirs_snpp_records = parse_viirs_csv(viirs_snpp_csv, "VIIRS_SNPP", max_rows=max_samples_per_sensor)
    stats["viirs_snpp_count"] = len(viirs_snpp_records)

    # 3. VIIRS NOAA-20
    viirs_noaa20_csv = directory / "NOAA20_VIIRS_Global_24h.csv"
    if download_if_missing:
        download_firms_feed("VIIRS_NOAA20", viirs_noaa20_csv)
    viirs_noaa20_records = parse_viirs_csv(viirs_noaa20_csv, "VIIRS_NOAA20", max_rows=max_samples_per_sensor)
    stats["viirs_noaa20_count"] = len(viirs_noaa20_records)

    all_records = modis_records + viirs_snpp_records + viirs_noaa20_records
    stats["total"] = len(all_records)

    return all_records, stats


if __name__ == "__main__":
    print("[FIRMS Loader] Loading live NASA FIRMS feeds...")
    records, meta = load_all_firms_data(max_samples_per_sensor=5000)
    print(f"[FIRMS Loader] Success! Ingested: {meta}")
    if records:
        print(f"[FIRMS Loader] Sample record: {records[0]}")
