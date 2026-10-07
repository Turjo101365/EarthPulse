"""
FastAPI Server for Camera-Driven Interactive 3D Earth
"""

import os
import json
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Load environment configuration from .env
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).resolve().parent.parent / ".env"
    load_dotenv(dotenv_path=env_path)
except Exception as e:
    print(f"Notice: .env loading skipped ({e})")

from .spatial_index import spatial_index

app = FastAPI(
    title="EarthPulse 3D Hotspot Monitor",
    description="Camera-driven real-time satellite fire detection streaming with Level-of-Detail (LOD)",
    version="1.0.0",
)

# Enable CORS for external development access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))

@app.get("/api/config")
async def get_client_config():
    """
    Returns client-side configuration loaded securely from backend .env.
    """
    return {
        "google_earth_api_key": os.getenv("GOOGLE_EARTH_API_KEY", ""),
        "version": "1.0.0",
    }

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "total_hotspots_catalog": len(spatial_index.hotspots),
        "version": "1.0.0",
    }

@app.get("/api/stats/global")
async def get_global_stats():
    """
    Returns global aggregate stats across the entire Earth.
    """
    return {
        "lod": {
            "level": 1,
            "name": "Global Overview",
            "description": "Earth Whole-Globe Baseline",
            "altitude_km": 15000.0,
        },
        "summary": spatial_index.global_summary,
    }

@app.get("/api/firms/analytics")
async def get_firms_analytics(
    time_range: str = Query("24h", description="Time range: 24h, 48h, 7d, day_0, day_1..day_6")
):
    """
    Returns global environmental analytics modeled after NASA FIRMS:
    total burned area, carbon emissions (CO2 & CH4), global energy release,
    top country leaderboard, and 7-day trend.
    """
    return spatial_index.get_firms_analytics(time_range=time_range)

@app.get("/api/hotspots")
async def get_visible_hotspots(
    north: float = Query(90.0, ge=-90.0, le=90.0, description="Northern latitude boundary"),
    south: float = Query(-90.0, ge=-90.0, le=90.0, description="Southern latitude boundary"),
    east: float = Query(180.0, ge=-180.0, le=180.0, description="Eastern longitude boundary"),
    west: float = Query(-180.0, ge=-180.0, le=180.0, description="Western longitude boundary"),
    altitude: float = Query(10000000.0, ge=100.0, description="Camera altitude above ground in meters"),
    sensor: str = Query("ALL", description="Sensor filter: ALL, MODIS, or VIIRS"),
    min_frp: float = Query(0.0, ge=0.0, description="Minimum Fire Radiative Power (MW)"),
    time_range: str = Query("24h", description="Time range: 24h, 48h, 7d, day_0..day_6"),
    daynight: str = Query("ALL", description="Satellite pass: ALL, D (day), N (night)"),
    date: Optional[str] = Query(None, description="Detection date ISO string"),
):
    """
    Primary camera-driven endpoint.
    Called whenever Cesium camera moves or zooms.
    Filters by visible bounding box and returns appropriate LOD items and dynamic summary stats.
    """
    result = spatial_index.query(
        north=north,
        south=south,
        east=east,
        west=west,
        altitude=altitude,
        sensor_filter=sensor.upper(),
        min_frp=min_frp,
        time_range=time_range,
        daynight=daynight.upper(),
    )
    return result

GEOCODE_CACHE = {}

@app.get("/api/geocode")
async def geocode_query(q: str = Query(..., min_length=2, description="Place or region query")):
    """
    Geocodes arbitrary locations worldwide with OpenStreetMap Photon API.
    """
    clean_q = q.strip().lower()
    if clean_q in GEOCODE_CACHE:
        return {"query": q, "results": GEOCODE_CACHE[clean_q]}
    
    url = f"https://photon.komoot.io/api/?q={urllib.parse.quote(q)}&limit=6"
    req = urllib.request.Request(url, headers={"User-Agent": "EarthPulse3D/1.0"})
    results = []
    try:
        with urllib.request.urlopen(req, timeout=3.5) as resp:
            data = json.loads(resp.read().decode())
            for feat in data.get("features", []):
                props = feat.get("properties", {})
                coords = feat.get("geometry", {}).get("coordinates", [0, 0])
                name = props.get("name") or props.get("city") or props.get("country")
                if not name:
                    continue
                country = props.get("country", "")
                state = props.get("state", "")
                type_ = props.get("type", "place")
                
                # Determine camera altitude based on type
                if type_ in ("country",):
                    alt = 3500000
                elif type_ in ("state", "administrative"):
                    alt = 900000
                elif type_ in ("city", "town"):
                    alt = 120000
                else:
                    alt = 60000

                label = f"{name}"
                if state and state != name:
                    label += f", {state}"
                if country and country != name:
                    label += f", {country}"

                results.append({
                    "name": label,
                    "short_name": name,
                    "country": country,
                    "lon": coords[0],
                    "lat": coords[1],
                    "alt": alt,
                    "type": type_
                })
        GEOCODE_CACHE[clean_q] = results
    except Exception as e:
        return {"query": q, "results": [], "error": str(e)}

    return {"query": q, "results": results}

@app.get("/api/hotspots/{hotspot_id}")
async def get_hotspot_detail(hotspot_id: str):
    """
    Returns comprehensive ML telemetry for a specific hotspot.
    """
    for p in spatial_index.hotspots:
        if p["id"] == hotspot_id:
            return p
    raise HTTPException(status_code=404, detail="Hotspot not found")

# Serve frontend static assets
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

@app.api_route("/", methods=["GET", "HEAD"])
async def serve_index():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Frontend not found, please check frontend/index.html"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8050, reload=True)
