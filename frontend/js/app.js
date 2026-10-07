import { FIRMSController } from './firms_controller.js';

/**
 * Main Application Orchestrator for Photorealistic 3D Earth
 */

document.addEventListener('DOMContentLoaded', async () => {
    // =========================================================================
    // 1. Fetch Environment Configuration Securely from Backend (.env)
    // =========================================================================
    const config = await window.dataService.fetchConfig();
    const GOOGLE_MAPS_API_KEY = config?.google_earth_api_key || '';
    if (Cesium.GoogleMaps && GOOGLE_MAPS_API_KEY) {
        Cesium.GoogleMaps.defaultApiKey = GOOGLE_MAPS_API_KEY;
    }

    const webMercator = new Cesium.WebMercatorTilingScheme();

    const basemapProviders = {
        // 🌎 Google Earth Ultra-HD True Satellite (Sub-meter photorealistic satellite imagery)
        google_earth: new Cesium.UrlTemplateImageryProvider({
            url: `https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}${GOOGLE_MAPS_API_KEY ? `&key=${GOOGLE_MAPS_API_KEY}` : ''}`,
            tilingScheme: webMercator,
            maximumLevel: 21,
            credit: '© Google Earth Satellite'
        }),

        // 🏷️ Google Earth Hybrid (Satellite Imagery + Geographic Borders, Roads & Cities)
        google_hybrid: new Cesium.UrlTemplateImageryProvider({
            url: `https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}${GOOGLE_MAPS_API_KEY ? `&key=${GOOGLE_MAPS_API_KEY}` : ''}`,
            tilingScheme: webMercator,
            maximumLevel: 21,
            credit: '© Google Earth Hybrid'
        }),

        // 🛰️ Ultra-High-Resolution Real Satellite (Esri / Maxar)
        satellite: new Cesium.UrlTemplateImageryProvider({
            url: 'https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            tilingScheme: webMercator,
            maximumLevel: 19,
            credit: 'Esri, Maxar, Earthstar Geographics'
        }),

        // 🌍 NASA Blue Marble (Deep ocean bathymetry, topography relief)
        bluemarble: new Cesium.UrlTemplateImageryProvider({
            url: 'https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/BlueMarble_ShadedRelief_Bathymetry/default/GoogleMapsCompatible_Level8/{z}/{y}/{x}.jpeg',
            tilingScheme: webMercator,
            maximumLevel: 8,
            credit: 'NASA GIBS Blue Marble'
        }),

        // ☁️ Real Daily NASA Satellite with Dynamic Cloud Formations
        clouds: new Cesium.UrlTemplateImageryProvider({
            url: 'https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/MODIS_Terra_CorrectedReflectance_TrueColor/default/2024-05-01/GoogleMapsCompatible_Level9/{z}/{y}/{x}.jpg',
            tilingScheme: webMercator,
            maximumLevel: 9,
            credit: 'NASA GIBS MODIS Terra Real-time Clouds & Reflectance'
        }),

        // 🌃 NASA Black Marble (Glowing Earth at Night / City Lights)
        night: new Cesium.UrlTemplateImageryProvider({
            url: 'https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/VIIRS_CityLights_2012/default/2012-04-18/GoogleMapsCompatible_Level8/{z}/{y}/{x}.jpg',
            tilingScheme: webMercator,
            maximumLevel: 8,
            credit: 'NASA GIBS VIIRS Night City Lights'
        })
    };

    // Dedicated Night City Lights provider for the unlit hemisphere
    const nightLightsProvider = new Cesium.UrlTemplateImageryProvider({
        url: 'https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/VIIRS_CityLights_2012/default/2012-04-18/GoogleMapsCompatible_Level8/{z}/{y}/{x}.jpg',
        tilingScheme: webMercator,
        maximumLevel: 8,
        credit: 'NASA GIBS VIIRS Night Lights'
    });

    // 2. Initialize Cesium Viewer with Google Earth 4K Ultra-HD Satellite Base Layer
    const activeBaseLayer = new Cesium.ImageryLayer(basemapProviders.google_earth);

    const viewer = new Cesium.Viewer('cesiumContainer', {
        baseLayer: activeBaseLayer,
        baseLayerPicker: false,
        geocoder: false,
        homeButton: false,
        infoBox: false,
        sceneModePicker: false,
        selectionIndicator: false,
        timeline: false,
        animation: false,
        navigationHelpButton: false,
        fullscreenButton: false,
        skyAtmosphere: new Cesium.SkyAtmosphere(),
        globe: new Cesium.Globe(Cesium.Ellipsoid.WGS84),
        requestRenderMode: false,
        maximumScreenSpaceError: 2
    });

    // =========================================================================
    // 3. Photorealistic Atmosphere & NASA Optics Setup
    // =========================================================================
    const globe = viewer.scene.globe;
    const skyAtmosphere = viewer.scene.skyAtmosphere;

    // Full uniform illumination like NASA Eyes on the Earth (100% full Earth, NO half-darkness!)
    globe.enableLighting = false;
    globe.showGroundAtmosphere = true;
    globe.baseColor = Cesium.Color.fromCssColorString('#020814');
    globe.atmosphereLightIntensity = 10.0;

    // Glowing NASA Black Marble city lights layer (only shown if Day/Night Shadow is explicitly enabled)
    const nightLightsLayer = viewer.imageryLayers.addImageryProvider(nightLightsProvider);
    nightLightsLayer.dayAlpha = 0.0;
    nightLightsLayer.nightAlpha = 1.0;
    nightLightsLayer.show = false;

    // Ensure camera mouse, trackpad, and touch controllers are explicitly active
    const sscController = viewer.scene.screenSpaceCameraController;
    sscController.enableRotate = true;
    sscController.enableTranslate = true;
    sscController.enableZoom = true;
    sscController.enableTilt = true;
    sscController.enableLook = true;
    sscController.inertiaSpin = 0.85;
    sscController.inertiaTranslate = 0.85;
    sscController.inertiaZoom = 0.85;
    sscController.maximumZoomDistance = 80000000.0; // 80,000 km Whole Earth space view
    sscController.minimumZoomDistance = 100.0;      // 100 meters ground detail

    // =========================================================================
    // Space Drag Orbit Engine: Rotate Whole Earth freely even from space background
    // =========================================================================
    let isSpaceDragging = false;
    let spaceDragLastX = 0;
    let spaceDragLastY = 0;

    viewer.canvas.addEventListener('mousedown', (e) => {
        if (e.button !== 0) return; // Only primary left click
        // Only space-drag in 3D mode! In 2D, let Cesium translate/pan normally!
        if (viewer.scene.mode !== Cesium.SceneMode.SCENE3D) return;

        const rect = viewer.canvas.getBoundingClientRect();
        const mouseX = e.clientX - rect.left;
        const mouseY = e.clientY - rect.top;
        const ray = viewer.camera.getPickRay(new Cesium.Cartesian2(mouseX, mouseY));
        const intersection = viewer.scene.globe.pick(ray, viewer.scene);
        if (!Cesium.defined(intersection)) {
            // Click was in outer space outside the Earth globe!
            isSpaceDragging = true;
            spaceDragLastX = e.clientX;
            spaceDragLastY = e.clientY;
        }
    });

    window.addEventListener('mousemove', (e) => {
        if (!isSpaceDragging || viewer.scene.mode !== Cesium.SceneMode.SCENE3D) return;
        const dx = e.clientX - spaceDragLastX;
        const dy = e.clientY - spaceDragLastY;
        spaceDragLastX = e.clientX;
        spaceDragLastY = e.clientY;

        // Proportional rotation around Earth's center
        const rotFactor = 0.0035;
        viewer.camera.rotate(Cesium.Cartesian3.UNIT_Z, dx * rotFactor);
        viewer.camera.rotate(viewer.camera.right, -dy * rotFactor);
    });

    window.addEventListener('mouseup', (e) => {
        if (e.button === 0) {
            isSpaceDragging = false;
        }
    });

    // =========================================================================
    // Dedicated Mac Trackpad & Multi-Touch Zoom Engine (Pinch & 2-Finger Scroll)
    // =========================================================================
    // Prevent default Cesium wheel conflict and handle Mac trackpad directly
    sscController.zoomEventTypes = [Cesium.CameraEventType.RIGHT_DRAG, Cesium.CameraEventType.PINCH];

    // 1. Two-finger scroll & trackpad pinch on macOS (Safari, Chrome, Firefox)
    window.addEventListener('wheel', (e) => {
        // If scrolling inside left/right panels, allow normal sidebar scroll
        if (e.target.closest('.left-panel, .right-panel, .modal-body, .firms-analytics-drawer, .firms-timeline-bar')) {
            return;
        }

        e.preventDefault();

        const camera = viewer.camera;
        if (!camera) return;

        const delta = e.deltaY;
        const isMacPinch = e.ctrlKey;
        const sensitivity = isMacPinch ? 0.0055 : 0.0022;

        if (viewer.scene.mode === Cesium.SceneMode.SCENE2D) {
            // 2D Orthographic Zoom
            const currentWidth = (camera.frustum && camera.frustum.width) ? camera.frustum.width : 20000000;
            const zoomAmount = currentWidth * Math.min(0.35, Math.max(0.04, Math.abs(delta) * sensitivity * 1.8));
            if (delta < 0) {
                camera.zoomIn(zoomAmount);
            } else if (delta > 0) {
                camera.zoomOut(zoomAmount);
            }
            if (window.cameraController) window.cameraController._handleCameraChange();
            return;
        }

        // 3D Altitude Zoom
        if (!camera.positionCartographic) return;

        const altitude = camera.positionCartographic.height;

        // Proportional altitude zoom (butter-smooth across all zoom levels)
        const zoomStep = Math.min(altitude * 0.35, Math.max(80.0, altitude * Math.abs(delta) * sensitivity));

        if (delta < 0) {
            // Scroll UP / Pinch OUT = Zoom In
            camera.zoomIn(zoomStep);
        } else if (delta > 0) {
            // Scroll DOWN / Pinch IN = Zoom Out
            camera.zoomOut(zoomStep);
        }
    }, { passive: false });

    // 2. Safari Native Mac Trackpad Pinch Gesture (gesturestart / gesturechange / gestureend)
    let safariPinchStartScale = 1.0;
    document.addEventListener('gesturestart', (e) => {
        if (!e.target.closest('.left-panel, .right-panel')) {
            e.preventDefault();
            safariPinchStartScale = e.scale;
        }
    }, { passive: false });

    document.addEventListener('gesturechange', (e) => {
        if (!e.target.closest('.left-panel, .right-panel')) {
            e.preventDefault();
            const camera = viewer.camera;
            if (!camera || !camera.positionCartographic) return;

            const altitude = camera.positionCartographic.height;
            const deltaScale = e.scale - safariPinchStartScale;
            safariPinchStartScale = e.scale;

            const zoomStep = altitude * Math.min(0.4, Math.abs(deltaScale) * 0.9);
            if (deltaScale > 0) {
                camera.zoomIn(zoomStep); // Spreading fingers = Zoom IN
            } else if (deltaScale < 0) {
                camera.zoomOut(zoomStep); // Pinching fingers = Zoom OUT
            }
        }
    }, { passive: false });

    document.addEventListener('gestureend', (e) => {
        safariPinchStartScale = 1.0;
    });

    // Authentic Rayleigh (blue sky) & Mie scattering halo
    globe.atmosphereRayleighCoefficient = new Cesium.Cartesian3(5.5e-6, 13.0e-6, 22.4e-6);
    globe.atmosphereMieCoefficient = new Cesium.Cartesian3(21e-6, 21e-6, 21e-6);
    globe.atmosphereRayleighScaleHeight = 8500.0;
    globe.atmosphereMieScaleHeight = 1200.0;
    globe.atmosphereMieAnomaly = 0.85;

    // Atmospheric glow horizon
    skyAtmosphere.show = true;
    skyAtmosphere.atmosphereLightIntensity = 10.0;
    skyAtmosphere.saturationShift = 0.12;
    skyAtmosphere.brightnessShift = 0.05;

    // Deep space background
    viewer.scene.backgroundColor = Cesium.Color.fromCssColorString('#020409');

    // Hotspots Entity Collection
    const hotspotDataSource = new Cesium.CustomDataSource('satellite_hotspots');
    viewer.dataSources.add(hotspotDataSource);

    // =========================================================================
    // 4. Basemap Switcher & Atmosphere Toggles
    // =========================================================================
    let currentBasemapKey = 'google_earth';
    const basemapButtons = document.querySelectorAll('.basemap-btn');

    function switchBasemap(key) {
        if (!basemapProviders[key]) return;
        currentBasemapKey = key;

        // Remove previous base imagery layer
        const layers = viewer.imageryLayers;
        if (layers.length > 0) {
            layers.remove(layers.get(0));
        }

        // Insert new base layer at bottom index 0
        const newLayer = new Cesium.ImageryLayer(basemapProviders[key]);
        layers.add(newLayer, 0);

        basemapButtons.forEach(btn => {
            if (btn.getAttribute('data-map') === key) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });
    }

    basemapButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const key = btn.getAttribute('data-map');
            switchBasemap(key);
        });
    });

    // Google Photorealistic 3D Tiles (3D Buildings & Mesh)
    let google3DTileset = null;
    const google3DToggle = document.getElementById('google-3d-tiles-toggle');
    if (google3DToggle) {
        google3DToggle.addEventListener('change', async (e) => {
            if (e.target.checked) {
                try {
                    Cesium.GoogleMaps.defaultApiKey = GOOGLE_MAPS_API_KEY;
                    if (!google3DTileset) {
                        google3DTileset = await Cesium.createGooglePhotorealistic3DTileset();
                    }
                    viewer.scene.primitives.add(google3DTileset);
                } catch (err) {
                    console.warn('Google 3D Tiles error:', err);
                    google3DToggle.checked = false;
                    alert('Google Earth 4K Ultra-HD Satellite imagery is active and streaming! Note: To also enable 3D Photorealistic mesh buildings, please enable "Map Tiles API" and billing in Google Cloud Console for project 902229379327.');
                }
            } else {
                if (google3DTileset) {
                    viewer.scene.primitives.remove(google3DTileset);
                }
            }
        });
    }

    // Sun Lighting (Day/Night Shadow) Toggle
    const sunLightingCheckbox = document.getElementById('sun-lighting-toggle');
    if (sunLightingCheckbox) {
        sunLightingCheckbox.addEventListener('change', (e) => {
            globe.enableLighting = e.target.checked;
            nightLightsLayer.show = e.target.checked;
        });
    }

    // Atmospheric Glow Toggle
    const atmosphereHaloCheckbox = document.getElementById('atmosphere-halo-toggle');
    if (atmosphereHaloCheckbox) {
        atmosphereHaloCheckbox.addEventListener('change', (e) => {
            skyAtmosphere.show = e.target.checked;
            globe.showGroundAtmosphere = e.target.checked;
        });
    }

    // =========================================================================
    // 5. NASA Eyes on the Earth Holographic Reticle & Radar Blip Renderer
    // =========================================================================
    const iconCache = new Map();

    function createMarkerIcon(colorHex, size, label = null, isCluster = false) {
        const key = `${colorHex}_${size}_${label || ''}_${isCluster}`;
        if (iconCache.has(key)) {
            return iconCache.get(key);
        }

        const canvas = document.createElement('canvas');
        const cSize = Math.max(64, Math.floor(size * 2.4));
        canvas.width = cSize;
        canvas.height = cSize;
        const ctx = canvas.getContext('2d');
        const center = cSize / 2;
        const radius = cSize * 0.42;

        if (isCluster) {
            // =========================================================
            // NASA Eyes Macro Cluster Telemetry Target
            // =========================================================
            // Subtle glowing radar halo
            const aura = ctx.createRadialGradient(center, center, radius * 0.3, center, center, radius);
            aura.addColorStop(0, colorHex + '28');
            aura.addColorStop(0.8, colorHex + '12');
            aura.addColorStop(1, 'transparent');
            ctx.fillStyle = aura;
            ctx.beginPath();
            ctx.arc(center, center, radius, 0, Math.PI * 2);
            ctx.fill();

            // Segmented HUD Radar Ring (4 arcs)
            ctx.strokeStyle = colorHex;
            ctx.lineWidth = 2.2;
            const segments = 4;
            const gap = 0.26;
            const segAngle = (Math.PI * 2 / segments) - gap;
            for (let i = 0; i < segments; i++) {
                const start = i * (segAngle + gap) + 0.13;
                const end = start + segAngle;
                ctx.beginPath();
                ctx.arc(center, center, radius * 0.86, start, end);
                ctx.stroke();
            }

            // Inner dark glass circular badge
            ctx.fillStyle = 'rgba(7, 14, 28, 0.90)';
            ctx.beginPath();
            ctx.arc(center, center, radius * 0.65, 0, Math.PI * 2);
            ctx.fill();
            ctx.strokeStyle = 'rgba(255, 255, 255, 0.45)';
            ctx.lineWidth = 1;
            ctx.stroke();

            // Center neon badge with glowing count
            ctx.fillStyle = '#ffffff';
            ctx.font = `bold ${Math.floor(radius * 0.50)}px "JetBrains Mono", sans-serif`;
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.shadowColor = colorHex;
            ctx.shadowBlur = 8;
            ctx.fillText(label || '', center, center);
            ctx.shadowBlur = 0;

        } else {
            // =========================================================
            // NASA Eyes Holographic Active Fire Blip / Reticle
            // =========================================================
            // 1. Soft Outer Luminous Bloom
            const halo = ctx.createRadialGradient(center, center, radius * 0.1, center, center, radius * 0.96);
            halo.addColorStop(0, colorHex + 'aa');
            halo.addColorStop(0.4, colorHex + '55');
            halo.addColorStop(0.8, colorHex + '15');
            halo.addColorStop(1, 'transparent');
            ctx.fillStyle = halo;
            ctx.beginPath();
            ctx.arc(center, center, radius * 0.96, 0, Math.PI * 2);
            ctx.fill();

            // 2. Outer Thin Neon Targeting Ring
            ctx.strokeStyle = colorHex;
            ctx.lineWidth = 1.6;
            ctx.shadowColor = colorHex;
            ctx.shadowBlur = 6;
            ctx.beginPath();
            ctx.arc(center, center, radius * 0.62, 0, Math.PI * 2);
            ctx.stroke();
            ctx.shadowBlur = 0;

            // 3. Directional Compass Crosshairs (North, South, East, West)
            ctx.strokeStyle = '#ffffff';
            ctx.lineWidth = 1.5;
            const rIn = radius * 0.68;
            const rOut = radius * 0.88;
            ctx.beginPath(); ctx.moveTo(center, center - rIn); ctx.lineTo(center, center - rOut); ctx.stroke();
            ctx.beginPath(); ctx.moveTo(center, center + rIn); ctx.lineTo(center, center + rOut); ctx.stroke();
            ctx.beginPath(); ctx.moveTo(center + rIn, center); ctx.lineTo(center + rOut, center); ctx.stroke();
            ctx.beginPath(); ctx.moveTo(center - rIn, center); ctx.lineTo(center - rOut, center); ctx.stroke();

            // 4. Middle Concentric Ring
            ctx.strokeStyle = 'rgba(255, 255, 255, 0.75)';
            ctx.lineWidth = 1.2;
            ctx.beginPath();
            ctx.arc(center, center, radius * 0.38, 0, Math.PI * 2);
            ctx.stroke();

            // 5. Brilliant White-Hot Luminous Core
            ctx.fillStyle = '#ffffff';
            ctx.shadowColor = colorHex;
            ctx.shadowBlur = 10;
            ctx.beginPath();
            ctx.arc(center, center, radius * 0.22, 0, Math.PI * 2);
            ctx.fill();
            ctx.shadowBlur = 0;
        }

        const dataUrl = canvas.toDataURL();
        iconCache.set(key, dataUrl);
        return dataUrl;
    }

    function renderHotspotsOnGlobe(items, currentAltitude = 10000000) {
        hotspotDataSource.entities.removeAll();

        if (!items || items.length === 0) return;

        const showLaserStalk = currentAltitude < 750000;

        items.forEach(item => {
            const lat = item.latitude;
            const lon = item.longitude;
            const size = item.marker_size || 22;
            const isCluster = item.is_cluster;

            // Color Palette (Standard FRP vs NASA Day/Night Satellite Overpass):
            let color = item.color_hex;
            if (window.firmsController && window.firmsController.colorMode === 'daynight' && !isCluster) {
                // NASA FIRMS standard: Solar Yellow for Day, Infrared Crimson for Night
                color = item.daynight === 'D' ? '#ffd600' : '#ff1744';
            } else if (isCluster) {
                color = '#00e5ff'; // Electric Cyan for clusters
            } else if (item.risk_level === 'CRITICAL') {
                color = '#ff1744'; // Plasma Flare
            } else if (item.sensor_family === 'MODIS') {
                color = '#ffb300'; // NASA Golden Amber
            } else {
                color = '#ff6d00'; // NASA Solar Flame
            }

            const labelText = isCluster ? (item.count > 999 ? `${(item.count/1000).toFixed(1)}k` : `${item.count}`) : null;
            const iconUrl = createMarkerIcon(color, size, labelText, isCluster);

            const is2D = viewer.scene.mode === Cesium.SceneMode.SCENE2D;
            const hoveringHeight = (showLaserStalk && !isCluster && !is2D) ? 1800 : 50;

            const entityConfig = {
                position: Cesium.Cartesian3.fromDegrees(lon, lat, hoveringHeight),
                billboard: {
                    image: iconUrl,
                    width: size * 1.8,
                    height: size * 1.8,
                    verticalOrigin: Cesium.VerticalOrigin.CENTER,
                    horizontalOrigin: Cesium.HorizontalOrigin.CENTER,
                    scaleByDistance: is2D ? undefined : new Cesium.NearFarScalar(5.0e4, 1.25, 1.2e7, 0.7),
                    disableDepthTestDistance: Number.POSITIVE_INFINITY
                },
                properties: {
                    data: item
                }
            };

            // Authentic NASA Eyes Vertical 3D Laser Beacon Stalk (only rendered in 3D mode)
            if (showLaserStalk && !isCluster && !is2D) {
                entityConfig.polyline = {
                    positions: Cesium.Cartesian3.fromDegreesArrayHeights([
                        lon, lat, 0,
                        lon, lat, hoveringHeight
                    ]),
                    width: 1.5,
                    material: new Cesium.ColorMaterialProperty(
                        Cesium.Color.fromCssColorString(color).withAlpha(0.7)
                    )
                };
            }

            hotspotDataSource.entities.add(entityConfig);
        });
    }

    // =========================================================================
    // 6. Camera Controller & Telemetry Synchronization
    // =========================================================================
    const uiController = new UIController();
    let currentFilter = {
        sensor: 'ALL',
        minFrp: 0
    };

    async function handleCameraUpdate(viewData) {
        if (!viewData) return;

        uiController.updateTelemetry(viewData.telemetry);
        uiController.setLoading(true);

        const { north, south, east, west } = viewData.bounds;
        const altitude = viewData.telemetry.altitudeMeters;

        try {
            const timeRange = window.firmsController ? window.firmsController.timeRange : '24h';
            const daynight = window.firmsController ? window.firmsController.daynightFilter : 'ALL';

            const data = await window.dataService.fetchHotspots({
                north,
                south,
                east,
                west,
                altitude,
                sensor: currentFilter.sensor,
                minFrp: currentFilter.minFrp,
                timeRange: timeRange,
                daynight: daynight
            });

            if (data) {
                uiController.updateViewportStats(data);
                renderHotspotsOnGlobe(data.items, altitude);
            }
        } catch (err) {
            console.error('Camera update query failed:', err);
        } finally {
            uiController.setLoading(false);
        }
    }

    const cameraController = new CameraController(viewer, handleCameraUpdate);
    window.cameraController = cameraController;

    // Connect UI callbacks
    uiController.onFilterChanged = (filterUpdate) => {
        currentFilter = { ...currentFilter, ...filterUpdate };
        const viewData = cameraController.getViewBoundsAndTelemetry();
        if (viewData) {
            handleCameraUpdate(viewData);
        }
    };

    uiController.onFlyToRequested = (targetKey) => {
        uiController.hideDetailModal();
        cameraController.flyTo(targetKey);
    };

    uiController.onFocusCameraRequested = (lat, lon) => {
        cameraController.flyToHotspot(lat, lon, 25000);
    };

    // =========================================================================
    // NASA FIRMS (Fire Information for Resource Management System) Controller
    // =========================================================================
    const firmsController = new FIRMSController(viewer);
    window.firmsController = firmsController;

    firmsController.onFilterChanged = (filterUpdate) => {
        const viewData = cameraController.getViewBoundsAndTelemetry();
        if (viewData) {
            handleCameraUpdate(viewData);
        }
    };

    firmsController.onFlyToCountry = (lat, lon, countryName) => {
        cameraController.flyToHotspot(lat, lon, 2200000);
    };

    // =========================================================================
    // 7. Interactive NASA FIRMS & NASA Eyes Hover Tooltip & Click Handlers
    // =========================================================================
    const hoverTooltip = document.getElementById('hover-tooltip');
    const ttBadge = document.getElementById('tt-badge');
    const ttId = document.getElementById('tt-id');
    const ttTitle = document.getElementById('tt-title');
    const ttFrp = document.getElementById('tt-frp');
    const ttConf = document.getElementById('tt-conf');
    const ttTemp = document.getElementById('tt-temp');
    const ttMl = document.getElementById('tt-ml');
    const ttSub = document.getElementById('tt-sub');
    const ttCoords = document.getElementById('tt-coords');
    const ttTime = document.getElementById('tt-time');

    let currentHoveredEntity = null;

    function showHoverTooltip(item, mousePosition) {
        if (!hoverTooltip || !item) return;

        if (item.is_cluster) {
            ttBadge.textContent = 'MACRO CLUSTER';
            ttBadge.style.color = '#00e5ff';
            ttBadge.style.borderColor = '#00e5ff';
            ttId.textContent = item.id;
            ttTitle.textContent = `${item.count} Active Hotspots`;
            ttFrp.textContent = `${item.avg_frp} MW`;
            ttConf.textContent = 'High Density';
            ttTemp.textContent = 'Aggregated';
            ttMl.textContent = `${item.modis_count}M / ${item.viirs_count}V`;
            ttSub.textContent = `Divisional Fire Density Node`;
            ttCoords.textContent = `${item.latitude.toFixed(2)}° N, ${item.longitude.toFixed(2)}° E`;
            ttTime.textContent = 'Live Aggregation';
        } else {
            const isViirs = item.sensor_family === 'VIIRS';
            ttBadge.textContent = `${item.sensor || item.sensor_family} (${item.resolution_m || 375}m)`;
            ttBadge.style.color = item.risk_level === 'CRITICAL' ? '#ff1744' : (isViirs ? '#ff6d00' : '#ffb300');
            ttBadge.style.borderColor = ttBadge.style.color;
            ttId.textContent = item.id;
            ttTitle.textContent = item.region || 'Active Satellite Fire';
            ttFrp.textContent = `${item.harmonized_frp || item.raw_frp} MW`;
            ttConf.textContent = `${Math.round(item.confidence || 85)}%`;
            ttTemp.textContent = `${Math.round(item.brightness_k || 330)} K`;
            ttMl.textContent = `${((item.ml_probability || 0.95) * 100).toFixed(1)}%`;
            ttSub.textContent = item.land_cover || 'Vegetation / Forest Shrubland';
            ttCoords.textContent = `${item.latitude.toFixed(4)}° N, ${item.longitude.toFixed(4)}° E`;
            ttTime.textContent = item.timestamp ? item.timestamp.slice(11, 19) + ' UTC' : 'Recent Pass';
        }

        // Position tooltip smoothly near cursor with screen boundary clamping
        let posX = mousePosition.x + 16;
        let posY = mousePosition.y + 16;
        const ttWidth = 260;
        const ttHeight = 180;

        if (posX + ttWidth > window.innerWidth) {
            posX = mousePosition.x - ttWidth - 10;
        }
        if (posY + ttHeight > window.innerHeight) {
            posY = mousePosition.y - ttHeight - 10;
        }

        hoverTooltip.style.transform = `translate(${posX}px, ${posY}px)`;
        hoverTooltip.classList.remove('hidden');
    }

    function hideHoverTooltip() {
        if (hoverTooltip) {
            hoverTooltip.classList.add('hidden');
        }
    }

    const handler = new Cesium.ScreenSpaceEventHandler(viewer.scene.canvas);

    // MOUSE_MOVE: Real-time NASA FIRMS & NASA Eyes Hover Telemetry
    handler.setInputAction((movement) => {
        // If inspection modal is already open, don't show duplicate hover tooltip
        if (uiController.elModal && !uiController.elModal.classList.contains('hidden')) {
            if (currentHoveredEntity && currentHoveredEntity.billboard) {
                currentHoveredEntity.billboard.scale = 1.0;
                currentHoveredEntity = null;
            }
            hideHoverTooltip();
            return;
        }

        const pickedObject = viewer.scene.pick(movement.endPosition);

        if (Cesium.defined(pickedObject) && pickedObject.id && pickedObject.id.properties) {
            viewer.canvas.style.cursor = 'pointer';
            const entity = pickedObject.id;
            const itemData = entity.properties.data.getValue();

            // Highlight hovered entity
            if (currentHoveredEntity && currentHoveredEntity !== entity && currentHoveredEntity.billboard) {
                currentHoveredEntity.billboard.scale = 1.0;
            }
            currentHoveredEntity = entity;
            if (entity.billboard) {
                entity.billboard.scale = 1.35;
            }

            showHoverTooltip(itemData, movement.endPosition);
        } else {
            viewer.canvas.style.cursor = 'default';
            if (currentHoveredEntity && currentHoveredEntity.billboard) {
                currentHoveredEntity.billboard.scale = 1.0;
                currentHoveredEntity = null;
            }
            hideHoverTooltip();
        }
    }, Cesium.ScreenSpaceEventType.MOUSE_MOVE);

    // LEFT_CLICK: Full Inspection Modal & Cluster Zoom
    handler.setInputAction((movement) => {
        const pickedObject = viewer.scene.pick(movement.position);

        if (Cesium.defined(pickedObject) && pickedObject.id && pickedObject.id.properties) {
            const itemData = pickedObject.id.properties.data.getValue();

            // Always hide hover tooltip on click so it doesn't duplicate
            hideHoverTooltip();

            if (itemData.is_cluster) {
                // Clicked a cluster: Zoom smoothly into its center!
                cameraController.flyToHotspot(itemData.latitude, itemData.longitude, 280000);
            } else {
                // Clicked an individual hotspot: open detailed HUD inspection modal
                uiController.showDetailModal(itemData);
            }
        } else {
            // Clicked empty globe surface
            uiController.hideDetailModal();
        }
    }, Cesium.ScreenSpaceEventType.LEFT_CLICK);

    // =========================================================================
    // 8. Initialize MediaPipe Hand Tracking Controller (DNA Project Engine)
    // =========================================================================
    const handController = new window.MediaPipeHandController(viewer, cameraController);
    window.handController = handController;

    // =========================================================================
    // 9. Wire Up On-Screen Camera D-Pad & Flight Tour
    // =========================================================================
    document.getElementById('dpad-up')?.addEventListener('click', () => cameraController.panUp());
    document.getElementById('dpad-down')?.addEventListener('click', () => cameraController.panDown());
    document.getElementById('dpad-left')?.addEventListener('click', () => cameraController.panLeft());
    document.getElementById('dpad-right')?.addEventListener('click', () => cameraController.panRight());
    document.getElementById('dpad-center')?.addEventListener('click', () => cameraController.flyTo('global'));
    document.getElementById('dpad-zoom-in')?.addEventListener('click', () => cameraController.zoomIn());
    document.getElementById('dpad-zoom-out')?.addEventListener('click', () => cameraController.zoomOut());
    document.getElementById('btn-start-tour')?.addEventListener('click', () => cameraController.startCinematicTour());

    // Initial startup: Fly to whole Earth
    cameraController.flyTo('global');
});
