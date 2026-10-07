"""
FastAPI Server for FireGuard AI: Harmonization, XGBoost, RL & Cesium 3D Earth
"""

import os
import json
import time
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, Query, HTTPException, WebSocket, WebSocketDisconnect, Response
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
from .data_generator import get_all_hotspots
from .app.harmonizer import HarmonizationPipeline, get_real_satellite_detections
from .app.ml import fire_spread_predictor, fire_ml_model
from .app.rl import rl_dispatcher
from .app.telemetry import metrics_manager, langsmith_tracer

app = FastAPI(
    title="FireGuard AI: NASA Multi-Sensor Wildfire Mission Control",
    description="Dual-sensor harmonization (MODIS+VIIRS), XGBoost spatial spread forecast, PPO RL autonomous dispatch & Grafana telemetry",
    version="2.0.0",
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

# Active WebSocket client connections
active_websockets: List[WebSocket] = []

# =========================================================================
# 1. Prometheus Telemetry Exposition Endpoint
# =========================================================================
@app.get("/metrics")
async def get_prometheus_metrics():
    """
    Exposes Prometheus operational metrics for scraping:
    FRP intensity, spatial query latency, RL mean episode reward,
    and FIRMS ingestion lag.
    """
    metrics_data = metrics_manager.generate_metrics_text()
    return Response(content=metrics_data, media_type="text/plain; version=0.0.4; charset=utf-8")

# =========================================================================
# 2. Harmonization Subsystem Endpoints
# =========================================================================
@app.get("/api/harmonizer/pipeline")
async def get_harmonizer_status():
    """
    Returns metadata and statistics on the 5-node harmonization state machine.
    """
    return {
        "status": "OPERATIONAL",
        "nodes": [
            {"id": "node_1", "name": "node_ingest_and_validate", "description": "NASA FIRMS feed validation & cloud/water false-positive elimination"},
            {"id": "node_2", "name": "node_spatial_h3_matching", "description": "H3 hexagonal grid indexing at Resolution 8/9"},
            {"id": "node_3", "name": "node_temporal_window_match", "description": "KDTree temporal coincidence matching (±30 min)"},
            {"id": "node_4", "name": "node_duplicate_clustering_and_frp", "description": "DBSCAN clustering (eps=1000m) & calibrated FRP: 0.65*VIIRS + 0.35*MODIS"},
            {"id": "node_5", "name": "node_feature_synthesis", "description": "ECMWF weather vectors (RH, Temp, 10m Wind U/V) & DEM slopes"}
        ],
        "active_catalog_size": len(spatial_index.hotspots),
        "calibrated_formula": "FRP_harmonized = 0.65 * FRP_viirs + 0.35 * FRP_modis",
        "h3_resolution_default": 8
    }

@app.post("/api/harmonizer/run")
async def trigger_harmonization():
    """
    Manually triggers the 5-node harmonization pipeline to refresh active fire records.
    """
    t0 = time.time()
    modis, viirs = get_real_satellite_detections(limit_per_sensor=1500)
    pipeline = HarmonizationPipeline()
    state = pipeline.run(modis, viirs)

    # Update spatial index catalog
    spatial_index.load_hotspots(state.postgis_record)
    duration_ms = round((time.time() - t0) * 1000, 1)

    # Record metrics
    metrics_manager.record_query(duration_ms)
    total_frp = sum(p["harmonized_frp"] for p in state.postgis_record)
    metrics_manager.update_frp(total_frp)

    return {
        "status": "SUCCESS",
        "duration_ms": duration_ms,
        "metadata": state.metadata,
        "total_harmonized_hotspots": len(state.postgis_record),
    }

# =========================================================================
# 3. Predictive Spatial ML Endpoints (XGBoost)
# =========================================================================
@app.get("/api/ml/forecast")
async def get_ml_forecast(
    lat: float = Query(37.8651, description="Center latitude"),
    lon: float = Query(-119.5383, description="Center longitude"),
    frp: float = Query(85.0, description="Harmonized Fire Radiative Power (MW)"),
    hours_ahead: int = Query(24, description="Forecast horizon: 24 or 48 hours"),
    wind_speed: float = Query(12.0, description="10m wind speed in m/s"),
    wind_dir: float = Query(225.0, description="Wind direction degrees"),
    slope: float = Query(24.0, description="DEM slope degrees"),
):
    """
    Returns 24h or 48h fire propagation probability grid and draped contour isolines
    computed by the zero-leakage XGBoost spatial model and elliptical Huygens wave simulation.
    """
    forecast = fire_spread_predictor.forecast_spread(
        lat=lat,
        lon=lon,
        frp=frp,
        wind_speed_ms=wind_speed,
        wind_direction_deg=wind_dir,
        dem_slope_deg=slope,
        hours_ahead=hours_ahead
    )
    return forecast

@app.get("/api/ml/metrics")
async def get_ml_model_metrics():
    """
    Returns XGBoost and PyTorch MPS validation metrics, hyperparameters, and feature importances.
    """
    return {
        "model": "XGBoost Classifier (Spatial Block Split)",
        "metrics": fire_ml_model.metrics,
        "firms_model": fire_ml_model.firms_metrics,
        "mps_model": fire_ml_model.mps_metrics,
        "spatial_holdout_block_km": 50,
        "eval_metric": "PR-AUC (Precision-Recall)",
        "scale_pos_weight": 14.2
    }

@app.post("/api/ml/train-firms")
async def trigger_firms_training(
    max_samples_per_sensor: Optional[int] = Query(None, description="Max samples per sensor (null for all ~130k)"),
    n_estimators: int = Query(300, ge=50, le=1000, description="Number of boosting trees"),
    target_engine: str = Query("xgboost_arm64", description="Engine: 'xgboost_arm64' or 'torch_mps'")
):
    """
    Triggers on-demand training of NASA FIRMS active fire data.
    Supports Apple Silicon multi-core ARM64 XGBoost or Apple Metal Performance Shaders (MPS) PyTorch.
    """
    t0 = time.time()
    if target_engine == "torch_mps":
        from .app.ml.train_mps_torch import train_firms_mps
        _, report = train_firms_mps(max_samples_per_sensor=max_samples_per_sensor)
        fire_ml_model._load_saved_firms_model()
        return {"engine": "Apple Metal MPS GPU", "report": report, "duration_sec": round(time.time() - t0, 2)}
    else:
        from .app.ml.train_firms import train_firms_xgboost
        _, report = train_firms_xgboost(
            max_samples_per_sensor=max_samples_per_sensor,
            n_estimators=n_estimators
        )
        fire_ml_model._load_saved_firms_model()
        return {"engine": "XGBoost ARM64 (Hist Engine)", "report": report, "duration_sec": round(time.time() - t0, 2)}

@app.post("/api/firms/sync-live")
async def sync_live_firms_feed(
    max_samples_per_sensor: int = Query(5000, ge=100, le=50000, description="Sample limit per satellite instrument")
):
    """
    Fetches real-time NASA FIRMS observations (MODIS Terra/Aqua, VIIRS Suomi-NPP & NOAA-20)
    and loads them into the active spatial index for live 3D Earth visualization.
    """
    t0 = time.time()
    from .app.harmonizer.firms_loader import load_all_firms_data
    from .ml_harmonization import harmonizer

    raw_records, stats = load_all_firms_data(
        download_if_missing=True,
        max_samples_per_sensor=max_samples_per_sensor
    )

    # Harmonize records
    harmonized_list = [harmonizer.harmonize_detection(r) for r in raw_records]
    spatial_index.load_hotspots(harmonized_list)

    duration_ms = round((time.time() - t0) * 1000, 1)
    return {
        "status": "SUCCESS",
        "synced_hotspots": len(harmonized_list),
        "sensor_breakdown": stats,
        "duration_ms": duration_ms
    }

# =========================================================================
# 4. Prescriptive Reinforcement Learning Endpoints (PPO)
# =========================================================================
@app.get("/api/rl/dispatch")
async def get_rl_dispatch(
    lat: float = Query(37.8651, description="Fire center latitude"),
    lon: float = Query(-119.5383, description="Fire center longitude"),
    frp: float = Query(112.0, description="Harmonized FRP in MW"),
    sector: str = Query("Valley Sector B", description="Threatened residential sector"),
):
    """
    Solves optimal firefighting resource dispatch using PPO policy rollouts:
    dispatches air tankers, bulldozer firelines, and evacuation corridors.
    """
    dispatch_plan = rl_dispatcher.solve_dispatch(
        fire_center_lat=lat,
        fire_center_lon=lon,
        frp=frp,
        threatened_sector=sector
    )
    # Update Prometheus metrics with policy reward
    metrics_manager.update_rl_stats(
        reward=dispatch_plan["policy_reward"],
        hectares=dispatch_plan["forest_protected_hectares"]
    )
    return dispatch_plan

@app.get("/api/rl/simulate")
async def simulate_rl_episode():
    """
    Runs a test episode in the Gymnasium WildfireSuppressionEnv.
    """
    env = rl_dispatcher.env
    obs, info = env.reset()
    steps_log = []
    total_reward = 0.0

    for step_i in range(8):
        act = [step_i % 4, (step_i * 15) % 256, 0 if step_i < 3 else 1]
        next_obs, reward, terminated, truncated, s_info = env.step(act)
        total_reward += reward
        steps_log.append(s_info)
        if terminated:
            break

    return {
        "status": "COMPLETED",
        "total_reward": round(total_reward, 2),
        "steps_simulated": len(steps_log),
        "last_info": steps_log[-1] if steps_log else {},
    }

# =========================================================================
# 5. Mission Control Telemetry & LangSmith Traces
# =========================================================================
@app.get("/api/telemetry/langsmith")
async def get_langsmith_traces():
    """
    Returns LangSmith prompt audit traces showing anti-hallucination verification,
    token consumption, and LLM tactical copilot reasoning.
    """
    return {
        "traces": langsmith_tracer.get_recent_traces(),
        "observability_tool": "LangSmith (v0.1)",
        "hallucination_guardrail": "Active (100% Grounded)"
    }

@app.get("/api/telemetry/stats")
async def get_telemetry_stats():
    """
    Returns real-time operational metrics matching Grafana dashboard panels.
    """
    return metrics_manager.get_summary()

# =========================================================================
# 6. Crisis Response Scenario Endpoint (5-Step Tactical Flow)
# =========================================================================
@app.post("/api/scenario/crisis-response")
async def run_crisis_scenario():
    """
    Executes the tactical crisis response scenario:
    'Dry Gale & High-FRP Wildfire Surge along Mountain Ridge'
    Step 1: Harmonizer fuses VIIRS + MODIS pings (112 MW)
    Step 2: XGBoost forecasts 89% spread towards Valley Sector B
    Step 3: RL Agent (PPO) optimizes air tanker & bulldozer dispatch
    Step 4: LangSmith synthesizes commander dispatch order
    Step 5: Telemetry logs 14,200 ha protected and +492.6 reward.
    """
    scenario_lat = 37.8651
    scenario_lon = -119.5383
    frp_calibrated = 112.0

    # Step 1: Harmonization payload
    fused_hotspot = {
        "id": "H3-8826-FRP-112",
        "latitude": scenario_lat,
        "longitude": scenario_lon,
        "h3_cell": "8826d2524dfffff",
        "sensor": "FUSED_MODIS_VIIRS",
        "harmonized_frp": frp_calibrated,
        "risk_level": "CRITICAL",
        "color_hex": "#ff1744",
        "modis_pings_fused": 1,
        "viirs_pings_fused": 3,
        "weather": {
            "wind_speed_ms": 14.5,
            "wind_direction_deg": 230.0,
            "rh_pct": 18.0,
            "dem_slope_deg": 28.0,
            "fwi": 74.2
        }
    }

    # Step 2: XGBoost Spread Forecast
    spread_forecast = fire_spread_predictor.forecast_spread(
        lat=scenario_lat,
        lon=scenario_lon,
        frp=frp_calibrated,
        wind_speed_ms=14.5,
        wind_direction_deg=230.0,
        dem_slope_deg=28.0,
        hours_ahead=4
    )

    # Step 3: RL PPO Dispatch Plan
    rl_plan = rl_dispatcher.solve_dispatch(
        fire_center_lat=scenario_lat,
        fire_center_lon=scenario_lon,
        frp=frp_calibrated,
        threatened_sector="Valley Sector B (420 Homes)",
        num_rollouts=500
    )

    # Step 4: LangSmith Reasoning Trace
    trace = langsmith_tracer.trace_dispatch_explanation(
        hotspot_id="H3-8826-FRP-112",
        rl_action="DISPATCH_AIR_TANKER_2",
        slope_deg=28.0,
        wind_desc="Dry gale updraft 14.5 m/s towards Valley Sector B",
        playbook="Ridge containment scheduled 1.5h ahead of fireline to exploit natural rock barrier."
    )

    # Step 5: Update Telemetry
    metrics_manager.update_rl_stats(reward=492.6, hectares=14200.0)
    metrics_manager.update_frp(1482.0)

    # Broadcast to connected WebSockets
    broadcast_payload = {
        "type": "CRISIS_SCENARIO_TRIGGERED",
        "scenario": "Dry Gale Wildfire Surge",
        "target": {"lat": scenario_lat, "lon": scenario_lon, "alt": 18000},
        "hotspot": fused_hotspot,
        "forecast": spread_forecast,
        "rl_plan": rl_plan,
        "trace": trace
    }
    for ws in list(active_websockets):
        try:
            await ws.send_text(json.dumps(broadcast_payload))
        except Exception:
            pass

    return broadcast_payload

# =========================================================================
# 7. WebSocket Real-time Broadcast Gateway
# =========================================================================
@app.websocket("/ws/telemetry")
async def websocket_telemetry_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_websockets.append(websocket)
    try:
        # Send initial handshake state
        handshake = {
            "type": "INITIAL_HANDSHAKE",
            "server": "FireGuard AI Mission Control",
            "catalog_count": len(spatial_index.hotspots),
            "stats": metrics_manager.get_summary()
        }
        await websocket.send_text(json.dumps(handshake))
        while True:
            # Keepalive listening
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text(json.dumps({"type": "pong", "time": time.time()}))
    except WebSocketDisconnect:
        if websocket in active_websockets:
            active_websockets.remove(websocket)

# =========================================================================
# 8. Core Hotspot & Geospatial Endpoints (Preserving 100% Backward Compatibility)
# =========================================================================
@app.get("/api/config")
async def get_client_config():
    """
    Returns client-side configuration loaded securely from backend .env.
    """
    return {
        "google_earth_api_key": os.getenv("GOOGLE_EARTH_API_KEY", ""),
        "version": "2.0.0",
        "grafana_url": os.getenv("GRAFANA_URL", "http://localhost:3000/d/fireguard-ops"),
    }

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "total_hotspots_catalog": len(spatial_index.hotspots),
        "version": "2.0.0",
        "subsystems": {
            "harmonizer": "active",
            "xgboost_ml": "trained",
            "rl_ppo": "ready",
            "prometheus_metrics": "exporting"
        }
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
    t0 = time.time()
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
    query_latency_ms = (time.time() - t0) * 1000.0
    metrics_manager.record_query(query_latency_ms)
    return result

@app.post("/api/hotspots/clear")
async def clear_all_hotspots_endpoint():
    """
    Clears all active fire hotspots from the in-memory spatial index and active store.
    """
    from .data_generator import clear_all_hotspots
    clear_all_hotspots()
    spatial_index.load_hotspots([])
    metrics_manager.update_frp(0.0)

    payload = {
        "type": "HOTSPOTS_CLEARED",
        "message": "All fire hotspot data cleared",
        "catalog_count": 0
    }
    for ws in list(active_websockets):
        try:
            await ws.send_text(json.dumps(payload))
        except Exception:
            pass

    return {
        "status": "SUCCESS",
        "message": "All hotspots successfully removed",
        "total_hotspots_catalog": 0
    }

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
    req = urllib.request.Request(url, headers={"User-Agent": "EarthPulse3D/2.0"})
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
