"""
Prometheus Metrics Exporter for FireGuard AI
Exposes operational metrics: FRP intensity, spatial query latency,
RL agent episode rewards, forest protected, and FIRMS ingestion lag.
"""

from typing import Dict, Any
from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST

class MetricsManager:
    def __init__(self):
        self._active_frp = 0.0
        self._postgis_latency = 0.0
        self._rl_reward = 0.0
        self._forest_protected = 0.0
        self._firms_lag = 0.0
        self._dedup_ratio = 0.0
        self._websocket_latency = 0.0

        # 1. FRP Intensity
        self.active_frp_gauge = Gauge(
            "fireguard_active_frp_mw",
            "Total Calibrated Fire Radiative Power (MW) across active fire catalog"
        )
        self.active_frp_gauge.set(0.0)

        # 2. Spatial Query / PostGIS Latency
        self.spatial_latency_gauge = Gauge(
            "fireguard_postgis_latency_ms",
            "p95 latency of spatial bounding-box queries and PostGIS GiST lookups in milliseconds"
        )
        self.spatial_latency_gauge.set(0.0)

        # 3. RL Mean Episode Reward
        self.rl_reward_gauge = Gauge(
            "fireguard_rl_episode_reward",
            "Mean episode reward achieved by PPO wildfire suppression policy"
        )
        self.rl_reward_gauge.set(0.0)

        # 4. Forest Protected
        self.forest_protected_gauge = Gauge(
            "fireguard_forest_protected_ha",
            "Estimated forest area (hectares) protected from fire propagation"
        )
        self.forest_protected_gauge.set(0.0)

        # 5. Ingestion Lag
        self.firms_lag_gauge = Gauge(
            "fireguard_firms_ingestion_lag_seconds",
            "Latency between satellite acquisition UTC and PostGIS catalog insertion"
        )
        self.firms_lag_gauge.set(0.0)

        # 6. Harmonization Throughput
        self.throughput_counter = Counter(
            "fireguard_harmonizer_throughput_events_total",
            "Total multi-sensor satellite detections processed by 5-node harmonization pipeline"
        )

        # 7. Deduplication Drop Ratio
        self.dedup_ratio_gauge = Gauge(
            "fireguard_harmonizer_dedup_drop_ratio",
            "Ratio of duplicate multi-sensor detections merged by DBSCAN"
        )
        self.dedup_ratio_gauge.set(0.0)

        # 8. WebSocket Stream Latency
        self.websocket_latency_gauge = Gauge(
            "fireguard_websocket_latency_ms",
            "Real-time broadcast latency from backend to Cesium 3D client in milliseconds"
        )
        self.websocket_latency_gauge.set(0.0)

    def record_query(self, latency_ms: float):
        self._postgis_latency = round(latency_ms, 1)
        self.spatial_latency_gauge.set(self._postgis_latency)

    def update_frp(self, total_frp: float):
        self._active_frp = round(total_frp, 1)
        self.active_frp_gauge.set(self._active_frp)

    def update_rl_stats(self, reward: float, hectares: float):
        self._rl_reward = round(reward, 1)
        self._forest_protected = round(hectares, 1)
        self.rl_reward_gauge.set(self._rl_reward)
        self.forest_protected_gauge.set(self._forest_protected)

    def get_summary(self) -> Dict[str, Any]:
        return {
            "active_frp_mw": self._active_frp,
            "postgis_latency_ms": self._postgis_latency,
            "rl_mean_reward": self._rl_reward,
            "forest_protected_ha": self._forest_protected,
            "firms_ingestion_lag_sec": self._firms_lag,
            "dedup_drop_ratio": self._dedup_ratio,
            "websocket_latency_ms": self._websocket_latency
        }

    def generate_metrics_text(self) -> bytes:
        return generate_latest()

metrics_manager = MetricsManager()
