"""
Keyless Geocoding Service for EarthPulse 3D Navigation
Resolves free-form place names ("fly to newyork", "Sylhet e niye jao") into
Cesium camera targets using OpenStreetMap Nominatim with an Open-Meteo fallback.
"""

import re
import json
import unicodedata
import math
import time
import logging
import threading
import urllib.parse
import urllib.request
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

# Common joined / misspelled / abbreviated place names users type in chat.
# Raw geocoders mis-resolve these (e.g. "newyork" -> a shop in Tokyo).
PLACE_ALIASES = {
    "newyork": "New York City", "nyc": "New York City", "new york": "New York City",
    "newyorkcity": "New York City", "ny": "New York City",
    "losangeles": "Los Angeles", "la": "Los Angeles", "sanfrancisco": "San Francisco",
    "sf": "San Francisco", "sandiego": "San Diego", "lasvegas": "Las Vegas",
    "washingtondc": "Washington, D.C.", "dc": "Washington, D.C.",
    "newjersey": "New Jersey", "newmexico": "New Mexico", "neworleans": "New Orleans",
    "newdelhi": "New Delhi", "delhi": "New Delhi", "hongkong": "Hong Kong",
    "kualalumpur": "Kuala Lumpur", "riodejaneiro": "Rio de Janeiro", "rio": "Rio de Janeiro",
    "saopaulo": "São Paulo", "buenosaires": "Buenos Aires", "mexicocity": "Mexico City",
    "capetown": "Cape Town", "abudhabi": "Abu Dhabi", "telaviv": "Tel Aviv",
    "srilanka": "Sri Lanka", "newzealand": "New Zealand", "southafrica": "South Africa",
    "southkorea": "South Korea", "northkorea": "North Korea", "saudiarabia": "Saudi Arabia",
    "usa": "United States", "us": "United States", "america": "United States",
    "uk": "United Kingdom", "england": "England", "uae": "United Arab Emirates",
    "coxsbazar": "Cox's Bazar", "coxs bazar": "Cox's Bazar", "cox bazar": "Cox's Bazar",
    "everest": "Mount Everest", "mounteverest": "Mount Everest",
    "himalaya": "Himalayas", "sahara": "Sahara",
    # Bengali script
    "নিউ ইয়র্ক": "New York City", "নিউইয়র্ক": "New York City", "লন্ডন": "London",
    "প্যারিস": "Paris", "টোকিও": "Tokyo", "দিল্লি": "New Delhi", "কলকাতা": "Kolkata",
    "সিলেট": "Sylhet", "রাজশাহী": "Rajshahi", "খুলনা": "Khulna", "বরিশাল": "Barisal",
    "রংপুর": "Rangpur", "ময়মনসিংহ": "Mymensingh", "কক্সবাজার": "Cox's Bazar",
    "রাঙ্গামাটি": "Rangamati", "বান্দরবান": "Bandarban", "জাপান": "Japan", "ভারত": "India",
    "চীন": "China", "আমেরিকা": "United States", "অস্ট্রেলিয়া": "Australia", "কানাডা": "Canada",
}

# Bengali text can arrive in composed or decomposed form - key aliases by NFC
PLACE_ALIASES = {unicodedata.normalize("NFC", k): v for k, v in PLACE_ALIASES.items()}

# Open-Meteo feature codes -> sensible camera altitude (meters)
_FEATURE_ALTITUDE = {
    "PCLI": 2_500_000, "PCLD": 2_500_000, "PCLS": 1_200_000,  # countries / territories
    "ADM1": 600_000, "ADM2": 250_000,                          # states / districts
    "PPLC": 60_000, "PPLA": 60_000, "PPLA2": 45_000, "PPL": 35_000,  # cities / towns
    "MT": 40_000, "PK": 40_000, "MTS": 400_000, "ISL": 150_000, "LK": 120_000,
}


class GeocodingService:
    def __init__(self):
        self.user_agent = "EarthPulse/1.0 (NASA Space Apps Challenge; contact@earthpulse.app)"
        self._cache: Dict[str, Optional[Dict[str, Any]]] = {}
        self._lock = threading.Lock()
        self._last_nominatim_call = 0.0  # Nominatim usage policy: max 1 request/second

    # ------------------------------------------------------------------ #
    @staticmethod
    def normalize_place(name: str) -> str:
        """Maps joined/misspelled/Bengali names to canonical searchable names."""
        cleaned = unicodedata.normalize("NFC", re.sub(r"\s+", " ", name.strip().strip(".,!?;:'\"")).strip())
        key = cleaned.lower()
        if key in PLACE_ALIASES:
            return PLACE_ALIASES[key]
        compact = key.replace(" ", "").replace("'", "")
        if compact in PLACE_ALIASES:
            return PLACE_ALIASES[compact]
        return cleaned

    @staticmethod
    def _altitude_from_bbox(bbox: List[str]) -> int:
        """Derives a camera altitude that frames the place's bounding box."""
        try:
            s, n, w, e = (float(v) for v in bbox)
            mid_lat = math.radians((s + n) / 2.0)
            height_km = abs(n - s) * 111.0
            width_km = abs(e - w) * 111.0 * max(math.cos(mid_lat), 0.2)
            span_km = max(height_km, width_km)
            return int(min(max(span_km * 2200, 15_000), 6_000_000))
        except Exception:
            return 80_000

    # ------------------------------------------------------------------ #
    def _http_json(self, url: str, timeout: float = 6.0) -> Any:
        req = urllib.request.Request(url, headers={"User-Agent": self.user_agent, "Accept-Language": "en"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def _nominatim(self, query: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            wait = 1.05 - (time.time() - self._last_nominatim_call)
            if wait > 0:
                time.sleep(wait)
            self._last_nominatim_call = time.time()
        url = (
            "https://nominatim.openstreetmap.org/search?format=jsonv2&limit=5&q="
            + urllib.parse.quote(query)
        )
        results = self._http_json(url)
        if not results:
            return None
        best = max(results, key=lambda r: float(r.get("importance") or 0.0))
        place_type = best.get("addresstype") or best.get("type") or "place"
        alt = self._altitude_from_bbox(best.get("boundingbox") or [])
        if place_type in ("city", "town", "village", "municipality", "suburb", "city_district", "borough"):
            alt = min(alt, 120_000)
        elif place_type in ("peak", "volcano", "mountain"):
            alt = 40_000
        elif place_type in ("state", "province", "region", "county", "district"):
            alt = min(alt, 1_200_000)
        return {
            "name": best.get("display_name", query),
            "short_name": best.get("name") or query,
            "lat": float(best["lat"]),
            "lon": float(best["lon"]),
            "alt": alt,
            "place_type": place_type,
            "importance": float(best.get("importance") or 0.0),
            "provider": "OpenStreetMap Nominatim",
        }

    def _open_meteo(self, query: str) -> Optional[Dict[str, Any]]:
        url = (
            "https://geocoding-api.open-meteo.com/v1/search?count=5&language=en&name="
            + urllib.parse.quote(query)
        )
        data = self._http_json(url)
        results = (data or {}).get("results") or []
        if not results:
            return None
        best = max(results, key=lambda r: r.get("population") or 0)
        parts = [best.get("name"), best.get("admin1"), best.get("country")]
        return {
            "name": ", ".join(p for p in parts if p),
            "short_name": best.get("name") or query,
            "lat": float(best["latitude"]),
            "lon": float(best["longitude"]),
            "alt": _FEATURE_ALTITUDE.get(best.get("feature_code", ""), 80_000),
            "place_type": best.get("feature_code", "place"),
            "population": best.get("population") or 0,
            "provider": "Open-Meteo Geocoding",
        }

    # ------------------------------------------------------------------ #
    def geocode(self, place: str) -> Optional[Dict[str, Any]]:
        """
        Resolves a place name to {name, lat, lon, alt, ...}. Returns None if not found.
        Results (including misses) are cached in-memory.
        """
        if not place or not place.strip():
            return None
        query = self.normalize_place(place)
        cache_key = query.lower()
        if cache_key in self._cache:
            return self._cache[cache_key]

        result = None
        try:
            result = self._nominatim(query)
        except Exception as e:
            logger.warning(f"Nominatim geocoding failed for '{query}': {e}")

        # Low-importance Nominatim hits are often shops/POIs with a matching name;
        # prefer a populated Open-Meteo settlement in that case.
        if result is None or result.get("importance", 0.0) < 0.3:
            try:
                om = self._open_meteo(query)
                if om and (result is None or om.get("population", 0) > 0):
                    result = om
            except Exception as e:
                logger.warning(f"Open-Meteo geocoding failed for '{query}': {e}")

        self._cache[cache_key] = result
        return result


# Global geocoding singleton
geocoding_service = GeocodingService()
