/**
 * Data Service: Communicates with FastAPI Backend
 * Handles debouncing and request abortion for rapid camera movements.
 */

class DataService {
    constructor() {
        this.currentAbortController = null;
        this.baseUrl = window.location.origin;
    }

    /**
     * Fetches visible hotspots matching camera bounding box and altitude.
     */
    async fetchHotspots({ north, south, east, west, altitude, sensor = 'ALL', minFrp = 0, timeRange = '24h', daynight = 'ALL' }) {
        // Abort previous in-flight request if user is still moving camera
        if (this.currentAbortController) {
            this.currentAbortController.abort();
        }
        this.currentAbortController = new AbortController();

        const params = new URLSearchParams({
            north: north.toFixed(4),
            south: south.toFixed(4),
            east: east.toFixed(4),
            west: west.toFixed(4),
            altitude: Math.round(altitude),
            sensor: sensor,
            min_frp: minFrp,
            time_range: timeRange,
            daynight: daynight
        });

        try {
            const response = await fetch(`${this.baseUrl}/api/hotspots?${params.toString()}`, {
                signal: this.currentAbortController.signal
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (err) {
            if (err.name === 'AbortError') {
                return null; // Normal cancellation due to fast camera pan
            }
            console.error('Failed to fetch hotspots:', err);
            throw err;
        }
    }

    /**
     * Fetches NASA FIRMS Global Environmental Analytics.
     */
    async fetchFirmsAnalytics(timeRange = '24h') {
        try {
            const res = await fetch(`${this.baseUrl}/api/firms/analytics?time_range=${encodeURIComponent(timeRange)}`);
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            return await res.json();
        } catch (err) {
            console.error('Failed to fetch FIRMS analytics:', err);
            return null;
        }
    }

    /**
     * Fetches global baseline statistics.
     */
    async fetchGlobalStats() {
        try {
            const res = await fetch(`${this.baseUrl}/api/stats/global`);
            return await res.json();
        } catch (err) {
            console.error('Failed to fetch global stats:', err);
            return null;
        }
    }

    /**
     * Fetches detailed data for an individual hotspot.
     */
    async fetchHotspotDetail(id) {
        try {
            const res = await fetch(`${this.baseUrl}/api/hotspots/${id}`);
            return await res.json();
        } catch (err) {
            console.error(`Failed to fetch detail for hotspot ${id}:`, err);
            return null;
        }
    }

    /**
     * Fetches client configuration loaded securely from backend .env.
     */
    async fetchConfig() {
        try {
            const res = await fetch(`${this.baseUrl}/api/config`);
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            return await res.json();
        } catch (err) {
            console.warn('Could not fetch /api/config, fallback to defaults:', err);
            return { google_earth_api_key: '' };
        }
    }

    /**
     * Harmonizer Pipeline Status
     */
    async fetchHarmonizerPipeline() {
        try {
            const res = await fetch(`${this.baseUrl}/api/harmonizer/pipeline`);
            return await res.json();
        } catch (err) {
            console.error('Failed to fetch harmonizer pipeline:', err);
            return null;
        }
    }

    /**
     * XGBoost 24-48h Spread Forecast
     */
    async fetchMLForecast(lat, lon, frp = 85.0, hoursAhead = 24) {
        try {
            const res = await fetch(`${this.baseUrl}/api/ml/forecast?lat=${lat}&lon=${lon}&frp=${frp}&hours_ahead=${hoursAhead}`);
            return await res.json();
        } catch (err) {
            console.error('Failed to fetch ML forecast:', err);
            return null;
        }
    }

    /**
     * RL PPO Resource Dispatch
     */
    async fetchRLDispatch(lat, lon, frp = 112.0, sector = 'Valley Sector B') {
        try {
            const res = await fetch(`${this.baseUrl}/api/rl/dispatch?lat=${lat}&lon=${lon}&frp=${frp}&sector=${encodeURIComponent(sector)}`);
            return await res.json();
        } catch (err) {
            console.error('Failed to fetch RL dispatch:', err);
            return null;
        }
    }

    /**
     * LangSmith Traces
     */
    async fetchLangSmithTraces() {
        try {
            const res = await fetch(`${this.baseUrl}/api/telemetry/langsmith`);
            return await res.json();
        } catch (err) {
            console.error('Failed to fetch LangSmith traces:', err);
            return null;
        }
    }

    async emitTestLangSmithTrace() {
        try {
            const res = await fetch(`${this.baseUrl}/api/telemetry/langsmith/test`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            return await res.json();
        } catch (err) {
            console.error('Failed to emit test LangSmith trace:', err);
            return null;
        }
    }

    /**
     * Real-time Mission Control Telemetry Stats
     */
    async fetchTelemetryStats() {
        try {
            const res = await fetch(`${this.baseUrl}/api/telemetry/stats`);
            return await res.json();
        } catch (err) {
            console.error('Failed to fetch telemetry stats:', err);
            return null;
        }
    }

    /**
     * Trigger Mountain Ridge Crisis Response Scenario
     */
    async triggerCrisisScenario() {
        try {
            const res = await fetch(`${this.baseUrl}/api/scenario/crisis-response`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({})
            });
            return await res.json();
        } catch (err) {
            console.error('Failed to trigger crisis scenario:', err);
            return null;
        }
    }
}

window.dataService = new DataService();

