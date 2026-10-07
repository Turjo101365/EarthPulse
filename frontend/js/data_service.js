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
}

window.dataService = new DataService();

