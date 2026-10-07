/**
 * Camera Controller: Listens to Cesium camera movements,
 * computes visible geographic bounds, altitude, and manages smooth fly-to animations.
 */

class CameraController {
    constructor(viewer, onCameraUpdate) {
        this.viewer = viewer;
        this.onCameraUpdate = onCameraUpdate;
        this.debounceTimeout = null;
        this.debounceDelayMs = 220; // Debounce to avoid flooding the backend
        this.autoRotateEnabled = false;
        this.isFlying = false;

        this.presets = {
            // 🌎 Whole Earth Space View (27,500 km - Earth completely framed in deep space)
            global: {
                destination: Cesium.Cartesian3.fromDegrees(25.0, 15.0, 27500000),
                orientation: { heading: 0.0, pitch: Cesium.Math.toRadians(-90.0), roll: 0.0 },
                duration: 2.6
            },
            // Continents
            asia: {
                destination: Cesium.Cartesian3.fromDegrees(95.0, 26.0, 9500000),
                orientation: { heading: 0.0, pitch: Cesium.Math.toRadians(-88.0), roll: 0.0 },
                duration: 2.5
            },
            europe: {
                destination: Cesium.Cartesian3.fromDegrees(15.0, 50.0, 5200000),
                orientation: { heading: 0.0, pitch: Cesium.Math.toRadians(-88.0), roll: 0.0 },
                duration: 2.5
            },
            africa: {
                destination: Cesium.Cartesian3.fromDegrees(20.0, 2.0, 8800000),
                orientation: { heading: 0.0, pitch: Cesium.Math.toRadians(-88.0), roll: 0.0 },
                duration: 2.5
            },
            north_america: {
                destination: Cesium.Cartesian3.fromDegrees(-98.0, 40.0, 8200000),
                orientation: { heading: 0.0, pitch: Cesium.Math.toRadians(-88.0), roll: 0.0 },
                duration: 2.5
            },
            south_america: {
                destination: Cesium.Cartesian3.fromDegrees(-60.0, -20.0, 7600000),
                orientation: { heading: 0.0, pitch: Cesium.Math.toRadians(-88.0), roll: 0.0 },
                duration: 2.5
            },
            oceania: {
                destination: Cesium.Cartesian3.fromDegrees(135.0, -25.0, 6500000),
                orientation: { heading: 0.0, pitch: Cesium.Math.toRadians(-88.0), roll: 0.0 },
                duration: 2.5
            },
            middle_east: {
                destination: Cesium.Cartesian3.fromDegrees(46.0, 27.0, 4500000),
                orientation: { heading: 0.0, pitch: Cesium.Math.toRadians(-88.0), roll: 0.0 },
                duration: 2.3
            },
            boreal: {
                destination: Cesium.Cartesian3.fromDegrees(95.0, 60.0, 6200000),
                orientation: { heading: 0.0, pitch: Cesium.Math.toRadians(-88.0), roll: 0.0 },
                duration: 2.5
            },
            polar_north: {
                destination: Cesium.Cartesian3.fromDegrees(0.0, 82.0, 8000000),
                orientation: { heading: 0.0, pitch: Cesium.Math.toRadians(-88.0), roll: 0.0 },
                duration: 2.5
            },
            polar_south: {
                destination: Cesium.Cartesian3.fromDegrees(0.0, -82.0, 8000000),
                orientation: { heading: 0.0, pitch: Cesium.Math.toRadians(-88.0), roll: 0.0 },
                duration: 2.5
            },
            // Bangladesh & Sub-regions
            bangladesh: {
                destination: Cesium.Cartesian3.fromDegrees(90.35, 23.85, 750000),
                orientation: { heading: 0.0, pitch: Cesium.Math.toRadians(-90.0), roll: 0.0 },
                duration: 2.2
            },
            dhaka: {
                destination: Cesium.Cartesian3.fromDegrees(90.4125, 23.8103, 85000),
                orientation: { heading: 0.0, pitch: Cesium.Math.toRadians(-75.0), roll: 0.0 },
                duration: 2.0
            },
            chittagong: {
                destination: Cesium.Cartesian3.fromDegrees(92.1831, 22.3569, 110000),
                orientation: { heading: 0.0, pitch: Cesium.Math.toRadians(-70.0), roll: 0.0 },
                duration: 2.0
            },
            sundarbans: {
                destination: Cesium.Cartesian3.fromDegrees(89.6000, 22.1500, 95000),
                orientation: { heading: 0.0, pitch: Cesium.Math.toRadians(-75.0), roll: 0.0 },
                duration: 2.0
            },
            // Key Global Fire Epicenters & Countries
            india: {
                destination: Cesium.Cartesian3.fromDegrees(78.9629, 20.5937, 3200000),
                orientation: { heading: 0.0, pitch: Cesium.Math.toRadians(-85.0), roll: 0.0 },
                duration: 2.4
            },
            china: {
                destination: Cesium.Cartesian3.fromDegrees(104.1954, 35.8617, 4200000),
                orientation: { heading: 0.0, pitch: Cesium.Math.toRadians(-85.0), roll: 0.0 },
                duration: 2.5
            },
            japan: {
                destination: Cesium.Cartesian3.fromDegrees(138.2529, 36.2048, 2200000),
                orientation: { heading: 0.0, pitch: Cesium.Math.toRadians(-80.0), roll: 0.0 },
                duration: 2.4
            },
            indonesia: {
                destination: Cesium.Cartesian3.fromDegrees(113.9213, -0.7893, 3500000),
                orientation: { heading: 0.0, pitch: Cesium.Math.toRadians(-85.0), roll: 0.0 },
                duration: 2.4
            },
            california: {
                destination: Cesium.Cartesian3.fromDegrees(-119.5, 37.5, 950000),
                orientation: { heading: 0.0, pitch: Cesium.Math.toRadians(-80.0), roll: 0.0 },
                duration: 2.6
            },
            canada: {
                destination: Cesium.Cartesian3.fromDegrees(-106.3468, 56.1304, 4500000),
                orientation: { heading: 0.0, pitch: Cesium.Math.toRadians(-85.0), roll: 0.0 },
                duration: 2.6
            },
            amazon: {
                destination: Cesium.Cartesian3.fromDegrees(-57.0, -8.0, 1800000),
                orientation: { heading: 0.0, pitch: Cesium.Math.toRadians(-85.0), roll: 0.0 },
                duration: 2.6
            },
            brazil: {
                destination: Cesium.Cartesian3.fromDegrees(-51.9253, -14.2350, 4200000),
                orientation: { heading: 0.0, pitch: Cesium.Math.toRadians(-85.0), roll: 0.0 },
                duration: 2.5
            },
            pantanal: {
                destination: Cesium.Cartesian3.fromDegrees(-57.0, -18.5, 1100000),
                orientation: { heading: 0.0, pitch: Cesium.Math.toRadians(-80.0), roll: 0.0 },
                duration: 2.3
            },
            congo: {
                destination: Cesium.Cartesian3.fromDegrees(23.6558, -2.8780, 2800000),
                orientation: { heading: 0.0, pitch: Cesium.Math.toRadians(-85.0), roll: 0.0 },
                duration: 2.5
            },
            greece: {
                destination: Cesium.Cartesian3.fromDegrees(21.8243, 39.0742, 900000),
                orientation: { heading: 0.0, pitch: Cesium.Math.toRadians(-75.0), roll: 0.0 },
                duration: 2.2
            },
            spain: {
                destination: Cesium.Cartesian3.fromDegrees(-3.7492, 40.4637, 1200000),
                orientation: { heading: 0.0, pitch: Cesium.Math.toRadians(-80.0), roll: 0.0 },
                duration: 2.3
            },
            uk: {
                destination: Cesium.Cartesian3.fromDegrees(-2.5, 54.5, 1300000),
                orientation: { heading: 0.0, pitch: Cesium.Math.toRadians(-80.0), roll: 0.0 },
                duration: 2.3
            },
            germany: {
                destination: Cesium.Cartesian3.fromDegrees(10.4515, 51.1657, 1200000),
                orientation: { heading: 0.0, pitch: Cesium.Math.toRadians(-80.0), roll: 0.0 },
                duration: 2.3
            },
            australia: {
                destination: Cesium.Cartesian3.fromDegrees(135.0, -25.0, 2800000),
                orientation: { heading: 0.0, pitch: Cesium.Math.toRadians(-88.0), roll: 0.0 },
                duration: 2.6
            },
            south_africa: {
                destination: Cesium.Cartesian3.fromDegrees(25.0, -29.0, 2400000),
                orientation: { heading: 0.0, pitch: Cesium.Math.toRadians(-85.0), roll: 0.0 },
                duration: 2.4
            }
        };

        this._setupListeners();
    }

    _setupListeners() {
        // Camera changed event is fired during movement
        this.viewer.camera.changed.addEventListener(() => {
            this._handleCameraChange();
        });

        // Camera moveEnd is fired when movement stops (immediate trigger)
        this.viewer.camera.moveEnd.addEventListener(() => {
            if (this.debounceTimeout) {
                clearTimeout(this.debounceTimeout);
            }
            this._dispatchUpdate();
        });

        // Frame tick for auto-rotation
        this.viewer.clock.onTick.addEventListener(() => {
            if (this.autoRotateEnabled && !this.isFlying) {
                this.viewer.scene.camera.rotate(Cesium.Cartesian3.UNIT_Z, 0.0006);
            }
        });

        // Keyboard navigation (WASD & Arrow Keys & Q/E zoom)
        window.addEventListener('keydown', (e) => {
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;

            switch (e.key) {
                case 'ArrowLeft':
                case 'a':
                case 'A':
                    this.panLeft(0.04);
                    break;
                case 'ArrowRight':
                case 'd':
                case 'D':
                    this.panRight(0.04);
                    break;
                case 'ArrowUp':
                case 'w':
                case 'W':
                    this.panUp(0.03);
                    break;
                case 'ArrowDown':
                case 's':
                case 'S':
                    this.panDown(0.03);
                    break;
                case '+':
                case '=':
                case 'q':
                case 'Q':
                    this.zoomIn(0.18);
                    break;
                case '-':
                case '_':
                case 'e':
                case 'E':
                    this.zoomOut(0.18);
                    break;
                case ' ':
                    this.autoRotateEnabled = !this.autoRotateEnabled;
                    const chk = document.getElementById('auto-rotate-toggle');
                    if (chk) chk.checked = this.autoRotateEnabled;
                    e.preventDefault();
                    break;
            }
        });
    }

    _handleCameraChange() {
        if (this.debounceTimeout) {
            clearTimeout(this.debounceTimeout);
        }
        this.debounceTimeout = setTimeout(() => {
            this._dispatchUpdate();
        }, this.debounceDelayMs);
    }

    _dispatchUpdate() {
        const viewData = this.getViewBoundsAndTelemetry();
        if (this.onCameraUpdate && viewData) {
            this.onCameraUpdate(viewData);
        }
    }

    /**
     * Computes the current visible rectangle (North, South, East, West)
     * and cartographic telemetry safely in both 3D Globe and 2D FIRMS Map modes.
     */
    getViewBoundsAndTelemetry() {
        const scene = this.viewer.scene;
        // Don't query during morph animation
        if (scene.mode === Cesium.SceneMode.MORPHING) return null;

        const camera = this.viewer.camera;
        const ellipsoid = scene.globe.ellipsoid;

        // Current camera altitude and position
        let carto;
        let altitudeMeters = 10000000;
        let latDeg = 0.0;
        let lonDeg = 0.0;

        if (scene.mode === Cesium.SceneMode.SCENE2D) {
            // In 2D, camera.position is in projected coordinates
            try {
                carto = scene.mapProjection.unproject(camera.position);
            } catch (e) {
                carto = camera.positionCartographic;
            }
            altitudeMeters = (camera.frustum && camera.frustum.width) ? camera.frustum.width : (carto ? carto.height : 15000000);
        } else {
            carto = camera.positionCartographic;
            if (carto) {
                altitudeMeters = carto.height;
            }
        }

        if (carto) {
            latDeg = Cesium.Math.toDegrees(carto.latitude) || 0.0;
            lonDeg = Cesium.Math.toDegrees(carto.longitude) || 0.0;
        }

        // Heading & Pitch (defensive against undefined during transition)
        const headingDeg = (camera.heading !== undefined && !isNaN(camera.heading)) ? Cesium.Math.toDegrees(camera.heading) : 0;
        const pitchDeg = (camera.pitch !== undefined && !isNaN(camera.pitch)) ? Cesium.Math.toDegrees(camera.pitch) : -90;

        let north = 85.0;
        let south = -85.0;
        let east = 180.0;
        let west = -180.0;

        try {
            let rect = camera.computeViewRectangle(ellipsoid);
            if (rect && !isNaN(rect.north) && !isNaN(rect.south)) {
                north = Math.min(88.0, Math.max(-88.0, Cesium.Math.toDegrees(rect.north)));
                south = Math.min(88.0, Math.max(-88.0, Cesium.Math.toDegrees(rect.south)));
                east = Math.min(180.0, Math.max(-180.0, Cesium.Math.toDegrees(rect.east)));
                west = Math.min(180.0, Math.max(-180.0, Cesium.Math.toDegrees(rect.west)));
            } else {
                const approxSpanDeg = Math.min(65.0, (altitudeMeters / 111000) * 0.9);
                north = Math.min(88.0, latDeg + approxSpanDeg);
                south = Math.max(-88.0, latDeg - approxSpanDeg);
                east = Math.min(180.0, lonDeg + approxSpanDeg);
                west = Math.max(-180.0, lonDeg - approxSpanDeg);
            }
        } catch (e) {
            north = 88.0;
            south = -88.0;
            east = 180.0;
            west = -180.0;
        }

        // Final safety check against NaN
        if (isNaN(north)) north = 85.0;
        if (isNaN(south)) south = -85.0;
        if (isNaN(east)) east = 180.0;
        if (isNaN(west)) west = -180.0;
        if (isNaN(altitudeMeters)) altitudeMeters = 10000000;
        if (isNaN(latDeg)) latDeg = 0.0;
        if (isNaN(lonDeg)) lonDeg = 0.0;

        return {
            bounds: { north, south, east, west },
            telemetry: {
                altitudeMeters,
                altitudeKm: altitudeMeters / 1000.0,
                latDeg,
                lonDeg,
                headingDeg: Math.round(headingDeg),
                pitchDeg: Math.round(pitchDeg)
            }
        };
    }

    flyTo(targetKey) {
        const target = this.presets[targetKey];
        if (!target) return;

        this.isFlying = true;
        const is2D = this.viewer.scene.mode === Cesium.SceneMode.SCENE2D;
        const orientation = is2D ? {
            heading: 0.0,
            pitch: Cesium.Math.toRadians(-90.0),
            roll: 0.0
        } : target.orientation;

        this.viewer.camera.flyTo({
            destination: target.destination,
            orientation: orientation,
            duration: target.duration,
            complete: () => {
                this.isFlying = false;
                this._dispatchUpdate();
            }
        });
    }

    flyToHotspot(lat, lon, heightMeters = 35000) {
        this.isFlying = true;
        const is2D = this.viewer.scene.mode === Cesium.SceneMode.SCENE2D;
        const pitchRad = is2D ? Cesium.Math.toRadians(-90.0) : Cesium.Math.toRadians(-65.0);

        this.viewer.camera.flyTo({
            destination: Cesium.Cartesian3.fromDegrees(lon, lat, heightMeters),
            orientation: {
                heading: 0.0,
                pitch: pitchRad,
                roll: 0.0
            },
            duration: 1.8,
            complete: () => {
                this.isFlying = false;
                this._dispatchUpdate();
            }
        });
    }

    flyToCoordinates(lon, lat, heightMeters = 1500000, duration = 2.4, pitchDeg = -85.0) {
        this.isFlying = true;
        const is2D = this.viewer.scene.mode === Cesium.SceneMode.SCENE2D;
        const pitchRad = is2D ? Cesium.Math.toRadians(-90.0) : Cesium.Math.toRadians(pitchDeg);

        this.viewer.camera.flyTo({
            destination: Cesium.Cartesian3.fromDegrees(lon, lat, heightMeters),
            orientation: {
                heading: 0.0,
                pitch: pitchRad,
                roll: 0.0
            },
            duration: duration,
            complete: () => {
                this.isFlying = false;
                this._dispatchUpdate();
            }
        });
    }

    setAutoRotate(enabled) {
        this.autoRotateEnabled = enabled;
    }

    // Manual camera movement helpers (used by on-screen D-Pad & Keyboard)
    panLeft(speed = 0.05) {
        if (this.viewer.scene.mode === Cesium.SceneMode.SCENE2D) {
            const dist = (this.viewer.camera.frustum.width || 10000000) * 0.08;
            this.viewer.camera.moveLeft(dist);
        } else {
            this.viewer.camera.rotate(Cesium.Cartesian3.UNIT_Z, speed);
        }
        this._handleCameraChange();
    }

    panRight(speed = 0.05) {
        if (this.viewer.scene.mode === Cesium.SceneMode.SCENE2D) {
            const dist = (this.viewer.camera.frustum.width || 10000000) * 0.08;
            this.viewer.camera.moveRight(dist);
        } else {
            this.viewer.camera.rotate(Cesium.Cartesian3.UNIT_Z, -speed);
        }
        this._handleCameraChange();
    }

    panUp(speed = 0.04) {
        if (this.viewer.scene.mode === Cesium.SceneMode.SCENE2D) {
            const dist = (this.viewer.camera.frustum.width || 10000000) * 0.08;
            this.viewer.camera.moveUp(dist);
        } else {
            this.viewer.camera.rotate(this.viewer.camera.right, -speed);
        }
        this._handleCameraChange();
    }

    panDown(speed = 0.04) {
        if (this.viewer.scene.mode === Cesium.SceneMode.SCENE2D) {
            const dist = (this.viewer.camera.frustum.width || 10000000) * 0.08;
            this.viewer.camera.moveDown(dist);
        } else {
            this.viewer.camera.rotate(this.viewer.camera.right, speed);
        }
        this._handleCameraChange();
    }

    zoomIn(factor = 0.25) {
        if (this.viewer.scene.mode === Cesium.SceneMode.SCENE2D) {
            const width = this.viewer.camera.frustum.width || 10000000;
            this.viewer.camera.zoomIn(width * factor);
        } else {
            const height = this.viewer.camera.positionCartographic.height;
            this.viewer.camera.zoomIn(height * factor);
        }
        this._handleCameraChange();
    }

    zoomOut(factor = 0.25) {
        if (this.viewer.scene.mode === Cesium.SceneMode.SCENE2D) {
            const width = this.viewer.camera.frustum.width || 10000000;
            this.viewer.camera.zoomOut(width * factor);
        } else {
            const height = this.viewer.camera.positionCartographic.height;
            this.viewer.camera.zoomOut(height * factor);
        }
        this._handleCameraChange();
    }

    // Cinematic Guided Auto-Tour across the entire Globe
    async startCinematicTour(onStopChange = null) {
        this.tourActive = true;
        const tourStops = [
            'global', 'bangladesh', 'dhaka', 'india', 'indonesia',
            'australia', 'congo', 'europe', 'greece', 'amazon',
            'california', 'canada', 'global'
        ];

        for (const stop of tourStops) {
            if (!this.tourActive) break;
            if (onStopChange) onStopChange(stop);
            this.flyTo(stop);
            await new Promise(r => setTimeout(r, 5200));
        }
        this.tourActive = false;
        if (onStopChange) onStopChange(null);
    }

    stopCinematicTour() {
        this.tourActive = false;
    }
}

// Master World Geographies Registry for Search and Fast Navigation
window.WORLD_LOCATIONS = [
    { name: "Whole Earth (Space View)", query: "global", continent: "global", lon: 25.0, lat: 15.0, alt: 27500000, icon: "🌎" },
    { name: "Asia & Pacific (Continent)", query: "asia", continent: "asia", lon: 95.0, lat: 26.0, alt: 9500000, icon: "🌏" },
    { name: "Europe (Continent)", query: "europe", continent: "europe", lon: 15.0, lat: 50.0, alt: 5200000, icon: "🌍" },
    { name: "Africa (Continent)", query: "africa", continent: "africa", lon: 20.0, lat: 2.0, alt: 8800000, icon: "🌍" },
    { name: "North America (Continent)", query: "north_america", continent: "americas", lon: -98.0, lat: 40.0, alt: 8200000, icon: "🌎" },
    { name: "South America (Continent)", query: "south_america", continent: "americas", lon: -60.0, lat: -20.0, alt: 7600000, icon: "🌎" },
    { name: "Oceania & Australia (Continent)", query: "oceania", continent: "oceania", lon: 135.0, lat: -25.0, alt: 6500000, icon: "🌏" },
    { name: "Arctic & North Pole", query: "polar_north", continent: "polar", lon: 0.0, lat: 82.0, alt: 8000000, icon: "❄️" },
    { name: "Antarctica & South Pole", query: "polar_south", continent: "polar", lon: 0.0, lat: -82.0, alt: 8000000, icon: "🧊" },
    
    // Bangladesh & South Asia
    { name: "Bangladesh", query: "bangladesh", continent: "asia", lon: 90.35, lat: 23.85, alt: 750000, icon: "🇧🇩" },
    { name: "Dhaka Metropolitan", query: "dhaka", continent: "asia", lon: 90.4125, lat: 23.8103, alt: 85000, icon: "📍" },
    { name: "Chittagong Hill Tracts", query: "chittagong", continent: "asia", lon: 92.1831, lat: 22.3569, alt: 110000, icon: "⛰️" },
    { name: "Sundarbans Mangrove Fringe", query: "sundarbans", continent: "asia", lon: 89.6000, lat: 22.1500, alt: 95000, icon: "🌲" },
    { name: "India (Subcontinent)", query: "india", continent: "asia", lon: 78.9629, lat: 20.5937, alt: 3200000, icon: "🇮🇳" },
    { name: "China & East Asia", query: "china", continent: "asia", lon: 104.1954, lat: 35.8617, alt: 4200000, icon: "🇨🇳" },
    { name: "Japan Archipelago", query: "japan", continent: "asia", lon: 138.2529, lat: 36.2048, alt: 2200000, icon: "🇯🇵" },
    { name: "Indonesia & Borneo", query: "indonesia", continent: "asia", lon: 113.9213, lat: -0.7893, alt: 3500000, icon: "🇮🇩" },
    { name: "Thailand & Indochina", query: "thailand", continent: "asia", lon: 100.9925, lat: 15.8700, alt: 2200000, icon: "🇹🇭" },
    { name: "Middle East & Arabian Gulf", query: "middle_east", continent: "asia", lon: 46.0, lat: 27.0, alt: 4500000, icon: "🏜️" },
    { name: "Siberian Boreal Taiga", query: "boreal", continent: "asia", lon: 95.0, lat: 60.0, alt: 6200000, icon: "🌲" },

    // Americas
    { name: "California & West Coast Wildfires", query: "california", continent: "americas", lon: -119.5, lat: 37.5, alt: 950000, icon: "🇺🇸" },
    { name: "Canada Boreal Forest Belt", query: "canada", continent: "americas", lon: -106.3468, lat: 56.1304, alt: 4500000, icon: "🇨🇦" },
    { name: "United States (National)", query: "usa", continent: "americas", lon: -95.7129, lat: 37.0902, alt: 5000000, icon: "🇺🇸" },
    { name: "Mexico & Central America", query: "mexico", continent: "americas", lon: -102.5528, lat: 23.6345, alt: 3200000, icon: "🇲🇽" },
    { name: "Amazon Rainforest Basin", query: "amazon", continent: "americas", lon: -57.0, lat: -8.0, alt: 1800000, icon: "🇧🇷" },
    { name: "Brazil (National View)", query: "brazil", continent: "americas", lon: -51.9253, lat: -14.2350, alt: 4200000, icon: "🇧🇷" },
    { name: "Pantanal Tropical Wetlands", query: "pantanal", continent: "americas", lon: -57.0, lat: -18.5, alt: 1100000, icon: "🌿" },
    { name: "Argentina & Patagonia", query: "argentina", continent: "americas", lon: -63.6167, lat: -38.4161, alt: 3500000, icon: "🇦🇷" },

    // Europe
    { name: "Greece & Aegean Fire Arc", query: "greece", continent: "europe", lon: 21.8243, lat: 39.0742, alt: 900000, icon: "🇬🇷" },
    { name: "Spain & Iberian Peninsula", query: "spain", continent: "europe", lon: -3.7492, lat: 40.4637, alt: 1200000, icon: "🇪🇸" },
    { name: "United Kingdom & Ireland", query: "uk", continent: "europe", lon: -2.5, lat: 54.5, alt: 1300000, icon: "🇬🇧" },
    { name: "Germany & Central Europe", query: "germany", continent: "europe", lon: 10.4515, lat: 51.1657, alt: 1200000, icon: "🇩🇪" },
    { name: "France & Western Europe", query: "france", continent: "europe", lon: 2.2137, lat: 46.2276, alt: 1400000, icon: "🇫🇷" },
    { name: "Italy & Mediterranean Basin", query: "italy", continent: "europe", lon: 12.5674, lat: 41.8719, alt: 1300000, icon: "🇮🇹" },
    { name: "Scandinavia & Nordic", query: "scandinavia", continent: "europe", lon: 15.0, lat: 62.0, alt: 2200000, icon: "❄️" },

    // Africa
    { name: "Congo Rainforest Basin", query: "congo", continent: "africa", lon: 23.6558, lat: -2.8780, alt: 2800000, icon: "🇨🇩" },
    { name: "Southern Africa Savanna Belt", query: "south_africa", continent: "africa", lon: 25.0, lat: -29.0, alt: 2400000, icon: "🇿🇦" },
    { name: "Sahara Desert & North Africa", query: "sahara", continent: "africa", lon: 11.0, lat: 23.0, alt: 4200000, icon: "🏜️" },
    { name: "Kenya & East African Rift", query: "kenya", continent: "africa", lon: 37.9062, lat: 0.0236, alt: 1800000, icon: "🇰🇪" },

    // Oceania
    { name: "Australia Continental Bushfires", query: "australia", continent: "oceania", lon: 135.0, lat: -25.0, alt: 2800000, icon: "🇦🇺" },
    { name: "Sydney & New South Wales", query: "nsw", continent: "oceania", lon: 150.0, lat: -33.5, alt: 600000, icon: "🔥" },
    { name: "New Zealand", query: "new_zealand", continent: "oceania", lon: 174.8860, lat: -40.9006, alt: 1800000, icon: "🇳🇿" }
];

window.CameraController = CameraController;
