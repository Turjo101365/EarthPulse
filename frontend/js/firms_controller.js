/**
 * NASA FIRMS (Fire Information for Resource Management System) Controller
 * 
 * Manages:
 * 1. 2D Equirectangular Flat Map vs 3D Orbital Globe morphing (viewer.scene.morphTo2D / morphTo3D).
 * 2. 7-Day Multi-Temporal Timeline Scrubber & Time-Lapse Playback.
 * 3. Broader Earth Environmental Analytics (Carbon CO2/CH4, Burned Area, Country Leaderboard).
 * 4. Smoke Plumes / Aerosols & Thermal Density Heatmap Overlays.
 * 5. NASA Day vs Night satellite pass color rendering.
 */

export class FIRMSController {
    constructor(viewer, options = {}) {
        this.viewer = viewer;
        this.options = options;

        this.currentMode = 'globe3d'; // 'globe3d' | 'firms2d'
        this.timeRange = '24h';        // '24h' | '48h' | '7d' | 'day_X'
        this.daynightFilter = 'ALL';   // 'ALL' | 'D' | 'N'
        this.colorMode = 'standard';   // 'standard' (FRP) | 'daynight' (NASA FIRMS Day/Night)
        this.showSmokePlumes = false;
        this.showHeatmap = false;

        this.isPlaying = false;
        this.playTimer = null;
        this.currentPlayDay = 6; // Starts at T-6 and plays to Today (0)

        // Custom DataSource for FIRMS Smoke Plumes & Environmental Overlays
        this.smokeDataSource = new Cesium.CustomDataSource('firms_smoke_plumes');
        this.heatmapDataSource = new Cesium.CustomDataSource('firms_heat_density');
        this.viewer.dataSources.add(this.smokeDataSource);
        this.viewer.dataSources.add(this.heatmapDataSource);

        // Callbacks
        this.onFilterChanged = null;
        this.onFlyToCountry = null;

        this.initDOMElements();
        this.bindEvents();
    }

    initDOMElements() {
        // Top Nav Mode Buttons
        this.btnGlobe3D = document.getElementById('view-mode-globe');
        this.btnFirms2D = document.getElementById('view-mode-firms');
        this.btnAnalyticsToggle = document.getElementById('btn-firms-analytics');
        this.lodBadge = document.getElementById('lod-badge');

        // Timeline Bar Elements
        this.timelineBar = document.getElementById('firms-timeline-bar');
        this.btnPlay = document.getElementById('timeline-play-btn');
        this.timelineSlider = document.getElementById('timeline-slider');
        this.timelineDateLabel = document.getElementById('timeline-date-label');
        this.timeRangeButtons = document.querySelectorAll('.tr-btn');

        // Analytics Drawer Elements
        this.analyticsDrawer = document.getElementById('firms-analytics-drawer');
        this.drawerCloseBtn = document.getElementById('analytics-drawer-close');

        // Global Impact Stat Elements
        this.firmsBurnedArea = document.getElementById('firms-burned-area');
        this.firmsBurnedHectares = document.getElementById('firms-burned-hectares');
        this.firmsCarbonCo2 = document.getElementById('firms-carbon-co2');
        this.firmsMethaneCh4 = document.getElementById('firms-methane-ch4');
        this.firmsEnergy = document.getElementById('firms-total-energy');
        this.firmsTotalHotspots = document.getElementById('firms-total-hotspots');
        this.diurnalDayPct = document.getElementById('diurnal-day-pct');
        this.diurnalNightPct = document.getElementById('diurnal-night-pct');
        this.diurnalBarDay = document.getElementById('diurnal-bar-day');
        this.countryLeaderboardList = document.getElementById('country-leaderboard-list');
        this.sevenDayTrendBars = document.getElementById('seven-day-trend-bars');
        this.biomeList = document.getElementById('biome-breakdown-list');

        // Layer Toggles in Drawer & HUD
        this.toggleSmoke = document.getElementById('toggle-smoke-plumes');
        this.toggleHeatmap = document.getElementById('toggle-thermal-heatmap');
        this.toggleDayNightPass = document.getElementById('toggle-daynight-pass');
        this.toggleColorMode = document.getElementById('toggle-firms-colormode');
    }

    bindEvents() {
        // 1. View Mode Switching (3D Globe vs 2D FIRMS Map)
        if (this.btnGlobe3D) {
            this.btnGlobe3D.addEventListener('click', () => this.setMode('globe3d'));
        }
        if (this.btnFirms2D) {
            this.btnFirms2D.addEventListener('click', () => this.setMode('firms2d'));
        }

        // 2. Analytics Drawer Toggle
        if (this.btnAnalyticsToggle) {
            this.btnAnalyticsToggle.addEventListener('click', () => this.toggleAnalyticsDrawer());
        }
        if (this.drawerCloseBtn) {
            this.drawerCloseBtn.addEventListener('click', () => this.toggleAnalyticsDrawer(false));
        }

        // 3. Timeline Range Buttons (Live / 24h, 48h, 7d)
        if (this.timeRangeButtons) {
            this.timeRangeButtons.forEach(btn => {
                btn.addEventListener('click', () => {
                    this.timeRangeButtons.forEach(b => b.classList.remove('active'));
                    btn.classList.add('active');
                    this.stopPlayback();

                    const range = btn.dataset.range;
                    this.timeRange = range;
                    if (this.timelineSlider) {
                        this.timelineSlider.value = range === '7d' ? 6 : (range === '48h' ? 5 : 6);
                    }
                    this.updateTimelineLabel(range);
                    if (this.onFilterChanged) {
                        this.onFilterChanged({ timeRange: this.timeRange });
                    }
                    this.refreshAnalytics();
                });
            });
        }

        // 4. Timeline Slider (Scrubbing Days T-6 to Today)
        if (this.timelineSlider) {
            this.timelineSlider.addEventListener('input', (e) => {
                this.stopPlayback();
                const dayOffset = 6 - parseInt(e.target.value, 10); // 6 is oldest, 0 is today
                this.timeRange = dayOffset === 0 ? '24h' : `day_${dayOffset}`;
                this.timeRangeButtons.forEach(b => b.classList.remove('active'));
                this.updateTimelineLabel(this.timeRange, dayOffset);
                if (this.onFilterChanged) {
                    this.onFilterChanged({ timeRange: this.timeRange });
                }
            });
        }

        // 5. Timeline Play / Pause Button
        if (this.btnPlay) {
            this.btnPlay.addEventListener('click', () => {
                if (this.isPlaying) {
                    this.stopPlayback();
                } else {
                    this.startPlayback();
                }
            });
        }

        // 6. Environmental Layer Toggles
        if (this.toggleSmoke) {
            this.toggleSmoke.addEventListener('change', (e) => {
                this.showSmokePlumes = e.target.checked;
                this.updateSmokePlumes();
            });
        }

        if (this.toggleHeatmap) {
            this.toggleHeatmap.addEventListener('change', (e) => {
                this.showHeatmap = e.target.checked;
                this.updateHeatmap();
            });
        }

        if (this.toggleDayNightPass) {
            this.toggleDayNightPass.addEventListener('change', (e) => {
                const val = e.target.value; // 'ALL', 'D', 'N'
                this.daynightFilter = val;
                if (this.onFilterChanged) {
                    this.onFilterChanged({ daynight: this.daynightFilter });
                }
            });
        }

        if (this.toggleColorMode) {
            this.toggleColorMode.addEventListener('change', (e) => {
                this.colorMode = e.target.checked ? 'daynight' : 'standard';
                if (this.onFilterChanged) {
                    this.onFilterChanged({ colorMode: this.colorMode });
                }
            });
        }
    }

    /**
     * Morphs between 3D Orbital Globe and 2D FIRMS Flat Map.
     */
    setMode(mode) {
        if (mode === this.currentMode) return;
        this.currentMode = mode;

        if (this.btnGlobe3D && this.btnFirms2D) {
            this.btnGlobe3D.classList.toggle('active', mode === 'globe3d');
            this.btnFirms2D.classList.toggle('active', mode === 'firms2d');
        }

        const scene = this.viewer.scene;

        // Cancel any active camera flights and complete previous morph
        this.viewer.camera.cancelFlight();
        if (typeof scene.completeMorph === 'function') {
            scene.completeMorph();
        }

        if (mode === 'firms2d') {
            document.body.classList.add('mode-firms2d');
            // In 2D, disable 3D-only atmosphere features
            if (scene.skyAtmosphere) {
                scene.skyAtmosphere.show = false;
            }
            scene.globe.showGroundAtmosphere = false;
            scene.globe.enableLighting = false;

            // Reset camera orientation straight down before morphing
            this.viewer.camera.setView({
                orientation: {
                    heading: 0.0,
                    pitch: Cesium.Math.toRadians(-90.0),
                    roll: 0.0
                }
            });

            // Morph smoothly to 2D GIS map projection
            scene.morphTo2D(1.2);

            // Reveal timeline bar automatically in FIRMS mode
            if (this.timelineBar) {
                this.timelineBar.classList.add('visible');
            }
            if (this.lodBadge) {
                this.lodBadge.textContent = '2D FLAT MAP • NASA FIRMS GIS';
            }
        } else {
            document.body.classList.remove('mode-firms2d');
            // Morph smoothly back to 3D spherical Earth
            scene.morphTo3D(1.2);
            if (scene.skyAtmosphere) {
                scene.skyAtmosphere.show = true;
            }
            scene.globe.showGroundAtmosphere = true;
            if (this.lodBadge) {
                this.lodBadge.textContent = '3D ORBITAL GLOBE • NASA EYES';
            }
        }

        // Trigger camera framing and data sync after morph completes
        setTimeout(() => {
            if (mode === 'firms2d') {
                // Nicely frame the entire flat world map like official NASA FIRMS
                try {
                    this.viewer.camera.setView({
                        destination: Cesium.Rectangle.fromDegrees(-175.0, -70.0, 175.0, 70.0)
                    });
                } catch (e) {
                    console.warn('2D camera framing fallback:', e);
                }
            }
            if (window.cameraController && typeof window.cameraController._dispatchUpdate === 'function') {
                window.cameraController._dispatchUpdate();
            }
        }, 1300);
    }

    /**
     * Toggles the Broader Earth Environmental Analytics Drawer.
     */
    toggleAnalyticsDrawer(forceState) {
        if (!this.analyticsDrawer) return;

        const isCurrentlyOpen = this.analyticsDrawer.classList.contains('open');
        const shouldOpen = forceState !== undefined ? forceState : !isCurrentlyOpen;

        if (shouldOpen) {
            this.analyticsDrawer.classList.add('open');
            if (this.btnAnalyticsToggle) this.btnAnalyticsToggle.classList.add('active');
            this.refreshAnalytics();
        } else {
            this.analyticsDrawer.classList.remove('open');
            if (this.btnAnalyticsToggle) this.btnAnalyticsToggle.classList.remove('active');
        }
    }

    /**
     * Fetches and renders global environmental analytics data from backend.
     */
    async refreshAnalytics() {
        if (!window.dataService) return;
        try {
            const data = await window.dataService.fetchFirmsAnalytics(this.timeRange);
            if (!data) return;

            const m = data.global_metrics;
            if (this.firmsBurnedArea) this.firmsBurnedArea.textContent = m.burned_area_sqkm.toLocaleString();
            if (this.firmsBurnedHectares) this.firmsBurnedHectares.textContent = m.burned_area_hectares.toLocaleString();
            if (this.firmsCarbonCo2) this.firmsCarbonCo2.textContent = m.carbon_co2_mt.toFixed(1);
            if (this.firmsMethaneCh4) this.firmsMethaneCh4.textContent = m.methane_ch4_kt.toFixed(1);
            if (this.firmsEnergy) this.firmsEnergy.textContent = `${m.total_energy_gw.toFixed(1)} GW`;
            if (this.firmsTotalHotspots) this.firmsTotalHotspots.textContent = m.total_hotspots.toLocaleString();

            // Diurnal
            if (data.diurnal) {
                const d = data.diurnal;
                if (this.diurnalDayPct) this.diurnalDayPct.textContent = `${d.day_pct}% (${d.day_count.toLocaleString()})`;
                if (this.diurnalNightPct) this.diurnalNightPct.textContent = `${d.night_pct}% (${d.night_count.toLocaleString()})`;
                if (this.diurnalBarDay) this.diurnalBarDay.style.width = `${d.day_pct}%`;
            }

            // Country Leaderboard
            if (this.countryLeaderboardList && data.country_leaderboard) {
                this.renderCountryLeaderboard(data.country_leaderboard);
            }

            // 7-Day Trend Chart
            if (this.sevenDayTrendBars && data.seven_day_trend) {
                this.renderSevenDayTrend(data.seven_day_trend);
            }

            // Top Biomes
            if (this.biomeList && data.top_biomes) {
                this.renderTopBiomes(data.top_biomes);
            }
        } catch (err) {
            console.error('Failed to load FIRMS analytics:', err);
        }
    }

    renderCountryLeaderboard(countries) {
        this.countryLeaderboardList.innerHTML = '';
        countries.forEach((c, idx) => {
            const item = document.createElement('div');
            item.className = 'country-rank-row';
            item.innerHTML = `
                <div class="cr-left">
                    <span class="cr-index">${idx + 1}</span>
                    <span class="cr-name">${c.country}</span>
                </div>
                <div class="cr-right">
                    <span class="cr-count">${c.count.toLocaleString()} fires</span>
                    <span class="cr-burned">${c.burned_area_sqkm.toLocaleString()} km²</span>
                    <button class="cr-fly-btn" title="Fly to ${c.country}">Fly</button>
                </div>
            `;

            // Fly directly to country on button click
            const btn = item.querySelector('.cr-fly-btn');
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                if (this.onFlyToCountry) {
                    this.onFlyToCountry(c.lat, c.lon, c.country);
                } else if (window.cameraController) {
                    window.cameraController.flyToHotspot(c.lat, c.lon, 1800000);
                }
            });

            this.countryLeaderboardList.appendChild(item);
        });
    }

    renderSevenDayTrend(trend) {
        this.sevenDayTrendBars.innerHTML = '';
        const maxCount = Math.max(...trend.map(t => t.count), 1);

        trend.forEach(t => {
            const pct = Math.max(12, Math.round((t.count / maxCount) * 100));
            const barWrapper = document.createElement('div');
            barWrapper.className = 'trend-bar-wrapper';
            barWrapper.title = `${t.date} (${t.label}): ${t.count.toLocaleString()} fires, ${t.burned_area_sqkm} km² burned`;
            barWrapper.innerHTML = `
                <div class="trend-bar-fill" style="height: ${pct}%;">
                    <span class="trend-val-tooltip">${t.count > 999 ? Math.round(t.count / 1000) + 'k' : t.count}</span>
                </div>
                <span class="trend-bar-label">${t.label}</span>
            `;

            barWrapper.addEventListener('click', () => {
                this.timeRange = t.day_offset === 0 ? '24h' : `day_${t.day_offset}`;
                this.updateTimelineLabel(this.timeRange, t.day_offset);
                if (this.timelineSlider) {
                    this.timelineSlider.value = 6 - t.day_offset;
                }
                if (this.onFilterChanged) {
                    this.onFilterChanged({ timeRange: this.timeRange });
                }
            });

            this.sevenDayTrendBars.appendChild(barWrapper);
        });
    }

    renderTopBiomes(biomes) {
        this.biomeList.innerHTML = '';
        biomes.forEach(b => {
            const row = document.createElement('div');
            row.className = 'biome-row';
            row.innerHTML = `
                <div class="biome-info">
                    <span class="biome-name">${b.region}</span>
                    <span class="biome-pct">${b.pct}%</span>
                </div>
                <div class="biome-bar"><div class="biome-bar-fill" style="width: ${b.pct}%;"></div></div>
            `;
            this.biomeList.appendChild(row);
        });
    }

    /**
     * Updates the timeline text label based on current filter.
     */
    updateTimelineLabel(range, dayOffset = 0) {
        if (!this.timelineDateLabel) return;
        if (range === '24h' || range === 'live') {
            this.timelineDateLabel.textContent = 'PAST 24 HOURS (OCT 03, 2026)';
        } else if (range === '48h') {
            this.timelineDateLabel.textContent = 'PAST 48 HOURS (OCT 02 - 03, 2026)';
        } else if (range === '7d') {
            this.timelineDateLabel.textContent = '7 DAYS ARCHIVE (SEP 27 - OCT 03, 2026)';
        } else if (range.startsWith('day_')) {
            const d = dayOffset !== undefined ? dayOffset : parseInt(range.split('_')[1], 10);
            const dateStr = this.getFormattedDate(d);
            this.timelineDateLabel.textContent = `TIMELINE: ${dateStr} (T-${d} DAYS)`;
        }
    }

    getFormattedDate(dayOffset) {
        const base = new Date(2026, 9, 3); // Oct 3, 2026
        base.setDate(base.getDate() - dayOffset);
        return base.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }).toUpperCase();
    }

    /**
     * Starts time-lapse animation scrubbing through days.
     */
    startPlayback() {
        if (this.isPlaying) return;
        this.isPlaying = true;
        if (this.btnPlay) {
            this.btnPlay.textContent = '⏸ Pause';
            this.btnPlay.classList.add('playing');
        }

        // Loop through days from 6 (oldest) down to 0 (today)
        this.currentPlayDay = 6;
        this.playTimer = setInterval(() => {
            this.currentPlayDay--;
            if (this.currentPlayDay < 0) {
                this.currentPlayDay = 6; // Loop back
            }

            const dayOffset = this.currentPlayDay;
            this.timeRange = dayOffset === 0 ? '24h' : `day_${dayOffset}`;

            if (this.timelineSlider) {
                this.timelineSlider.value = 6 - dayOffset;
            }
            this.updateTimelineLabel(this.timeRange, dayOffset);

            if (this.onFilterChanged) {
                this.onFilterChanged({ timeRange: this.timeRange });
            }
        }, 1800); // 1.8 seconds per day step for smooth cinematic viewing
    }

    stopPlayback() {
        if (!this.isPlaying) return;
        this.isPlaying = false;
        if (this.playTimer) {
            clearInterval(this.playTimer);
            this.playTimer = null;
        }
        if (this.btnPlay) {
            this.btnPlay.textContent = '▶ Play';
            this.btnPlay.classList.remove('playing');
        }
    }

    /**
     * Smoke Plumes & Aerosol Layer
     * Generates simulated atmospheric smoke dispersion drifting downwind from major fire zones.
     */
    updateSmokePlumes() {
        this.smokeDataSource.entities.removeAll();
        if (!this.showSmokePlumes) return;

        // Major global plume source locations with wind vectors [lat, lon, angleDeg, lengthDeg, name]
        const plumeSources = [
            [-8.5, -55.0, 75, 4.5, 'Amazon Basin Heavy Smoke Plume'],
            [-12.0, -60.0, 80, 5.0, 'Cerrado Forest Fire Plume'],
            [-6.0, 22.0, 95, 4.2, 'Central African Savanna Plume'],
            [-11.0, 26.0, 100, 3.8, 'Southern Congo Peat Smoke'],
            [-22.0, 134.0, 120, 6.0, 'Northern Territory Bushfire Smoke'],
            [38.5, -121.0, 45, 3.5, 'California Sierra Nevada Smoke'],
            [56.0, -112.0, 60, 4.0, 'Alberta Boreal Wildfire Plume'],
            [22.8, 91.5, 80, 1.8, 'Chittagong & Delta Agricultural Haze'],
            [-2.5, 112.0, 70, 3.2, 'Kalimantan Peatland Smoke']
        ];

        plumeSources.forEach((src) => {
            const [lat, lon, windAngle, len, title] = src;
            const rad = Cesium.Math.toRadians(windAngle);
            const dLat = Math.sin(rad) * len;
            const dLon = Math.cos(rad) * len;

            // Semi-transparent billowing atmospheric smoke plume corridor
            this.smokeDataSource.entities.add({
                name: title,
                corridor: {
                    positions: Cesium.Cartesian3.fromDegreesArray([
                        lon, lat,
                        lon + dLon * 0.4, lat + dLat * 0.4,
                        lon + dLon, lat + dLat
                    ]),
                    width: 140000.0, // 140 km wide smoke front
                    material: new Cesium.Color(0.85, 0.85, 0.90, 0.28),
                    outline: false,
                    height: 2500.0
                }
            });

            // Core dense plume source ellipse
            this.smokeDataSource.entities.add({
                name: `${title} Core`,
                position: Cesium.Cartesian3.fromDegrees(lon, lat, 1500.0),
                ellipse: {
                    semiMinorAxis: 45000.0,
                    semiMajorAxis: 85000.0,
                    rotation: rad,
                    material: new Cesium.Color(0.95, 0.90, 0.75, 0.42),
                    outline: false
                }
            });
        });
    }

    /**
     * Thermal Density Heatmap Layer
     * Adds glowing thermal intensity circles over dense wildfire biomes.
     */
    updateHeatmap() {
        this.heatmapDataSource.entities.removeAll();
        if (!this.showHeatmap) return;

        const heatmapCenters = [
            [-10.0, -56.0, 450000.0, '#ff1744', 0.35],
            [-7.0, 24.0, 520000.0, '#ff5722', 0.35],
            [-20.0, 136.0, 480000.0, '#ff9800', 0.30],
            [38.0, -120.0, 320000.0, '#ff5722', 0.32],
            [23.5, 90.5, 180000.0, '#ffb300', 0.28],
            [55.0, -114.0, 380000.0, '#ff5722', 0.30],
            [-3.0, 114.0, 300000.0, '#ff9800', 0.32]
        ];

        heatmapCenters.forEach(([lat, lon, radius, colorHex, alpha]) => {
            this.heatmapDataSource.entities.add({
                position: Cesium.Cartesian3.fromDegrees(lon, lat, 500.0),
                ellipse: {
                    semiMinorAxis: radius,
                    semiMajorAxis: radius,
                    material: Cesium.Color.fromCssColorString(colorHex).withAlpha(alpha),
                    outline: false
                }
            });
        });
    }
}
