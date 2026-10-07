/**
 * FireGuard AI Controller: Orchestrates Dual-Sensor Harmonization,
 * XGBoost 3D Spread Contours, RL PPO Containment Lines,
 * Grafana Telemetry Status, and Mountain Ridge Crisis Scenario.
 */

export class FireGuardController {
    constructor(viewer) {
        this.viewer = viewer;
        this.spreadDataSource = new Cesium.CustomDataSource('xgboost-spread-contours');
        this.rlDataSource = new Cesium.CustomDataSource('rl-containment-lines');
        this.viewer.dataSources.add(this.spreadDataSource);
        this.viewer.dataSources.add(this.rlDataSource);

        this.ws = null;
        this.isSpreadVisible = true;
        this.isRLVisible = true;

        this.initWebSocket();
        this.initUI();
    }

    initWebSocket() {
        try {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws/telemetry`;
            this.ws = new WebSocket(wsUrl);

            this.ws.onopen = () => {
                console.log('⚡ FireGuard AI Telemetry Stream connected');
            };

            this.ws.onmessage = (event) => {
                try {
                    const msg = JSON.parse(event.data);
                    if (msg.type === 'CRISIS_SCENARIO_TRIGGERED') {
                        this.handleRemoteScenario(msg);
                    }
                } catch (e) {
                    console.warn('WS message parse error:', e);
                }
            };

            this.ws.onclose = () => {
                // Auto-reconnect after 4s
                setTimeout(() => this.initWebSocket(), 4000);
            };
        } catch (e) {
            console.warn('WebSocket init skipped:', e);
        }
    }

    initUI() {
        // Wire Architecture Modal tabs
        const archTabs = document.querySelectorAll('.arch-tab-btn');
        archTabs.forEach(btn => {
            btn.addEventListener('click', () => {
                archTabs.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                const target = btn.dataset.tab;
                document.querySelectorAll('.arch-panel-content').forEach(p => {
                    p.classList.toggle('hidden', p.id !== `arch-panel-${target}`);
                });
            });
        });

        // Open / Close Architecture Modal
        const btnOpenArch = document.getElementById('btn-open-arch');
        const modalArch = document.getElementById('fireguard-arch-modal');
        const btnCloseArch = document.getElementById('btn-close-arch');
        if (btnOpenArch && modalArch) {
            btnOpenArch.addEventListener('click', () => modalArch.classList.remove('hidden'));
        }
        if (btnCloseArch && modalArch) {
            btnCloseArch.addEventListener('click', () => modalArch.classList.add('hidden'));
        }

        // Crisis Scenario Button in Header / HUD
        const btnTriggerScenario = document.getElementById('btn-trigger-crisis-scenario');
        if (btnTriggerScenario) {
            btnTriggerScenario.addEventListener('click', () => this.runMountainRidgeScenario());
        }

        // LangSmith Drawer Close Button
        const btnCloseLangsmith = document.getElementById('btn-close-langsmith');
        const drawerLangsmith = document.getElementById('langsmith-drawer');
        if (btnCloseLangsmith && drawerLangsmith) {
            btnCloseLangsmith.addEventListener('click', () => drawerLangsmith.classList.add('collapsed'));
        }

        const btnOpenLangsmith = document.getElementById('btn-open-langsmith');
        if (btnOpenLangsmith && drawerLangsmith) {
            btnOpenLangsmith.addEventListener('click', () => {
                drawerLangsmith.classList.remove('collapsed');
                this.refreshLangSmithTraces();
            });
        }

        // Layer Toggles
        const toggleSpread = document.getElementById('toggle-xgboost-spread');
        if (toggleSpread) {
            toggleSpread.addEventListener('change', (e) => {
                this.isSpreadVisible = e.target.checked;
                this.spreadDataSource.show = this.isSpreadVisible;
            });
        }

        const toggleRL = document.getElementById('toggle-rl-containment');
        if (toggleRL) {
            toggleRL.addEventListener('change', (e) => {
                this.isRLVisible = e.target.checked;
                this.rlDataSource.show = this.isRLVisible;
            });
        }

        // Periodically refresh Grafana telemetry stats
        this.updateTelemetryHUD();
        setInterval(() => this.updateTelemetryHUD(), 6000);
    }

    async updateTelemetryHUD() {
        const stats = await window.dataService.fetchTelemetryStats();
        if (!stats) return;

        const elFrp = document.getElementById('hud-active-frp');
        if (elFrp) elFrp.textContent = `${stats.active_frp_mw.toLocaleString()} MW`;

        const elLatency = document.getElementById('hud-postgis-latency');
        if (elLatency) elLatency.textContent = `${stats.postgis_latency_ms} ms`;

        const elReward = document.getElementById('hud-rl-reward');
        if (elReward) elReward.textContent = `+${stats.rl_mean_reward}`;

        const elProtected = document.getElementById('hud-forest-protected');
        if (elProtected) elProtected.textContent = `${stats.forest_protected_ha.toLocaleString()} ha`;
    }

    /**
     * Executes the full 5-step tactical response scenario:
     * Dry Gale & High-FRP Wildfire Surge along Mountain Ridge
     */
    async runMountainRidgeScenario() {
        const btn = document.getElementById('btn-trigger-crisis-scenario');
        if (btn) {
            btn.classList.add('pulsing');
            btn.innerHTML = `<span class="spinner-inline"></span> Running PPO Rollouts...`;
        }

        try {
            const data = await window.dataService.triggerCrisisScenario();
            if (!data) return;

            // 1. Camera fly-to Mountain Ridge in 3D with pitch angle to showcase DEM slope
            const target = data.target;
            this.viewer.camera.flyTo({
                destination: Cesium.Cartesian3.fromDegrees(target.lon, target.lat, 16000),
                orientation: {
                    heading: Cesium.Math.toRadians(35.0),
                    pitch: Cesium.Math.toRadians(-32.0),
                    roll: 0.0
                },
                duration: 2.8,
                complete: () => {
                    this.renderScenarioGraphics(data);
                }
            });

            // 2. Open LangSmith AI Reasoning Drawer
            this.displayLangSmithTrace(data.trace, data.rl_plan);

            // 3. Update Status Indicators
            this.updateTelemetryHUD();

        } catch (e) {
            console.error('Error running crisis scenario:', e);
        } finally {
            if (btn) {
                btn.classList.remove('pulsing');
                btn.innerHTML = `⚡ Ridge Crisis Scenario`;
            }
        }
    }

    renderScenarioGraphics(data) {
        this.spreadDataSource.entities.removeAll();
        this.rlDataSource.entities.removeAll();

        const forecast = data.forecast;
        const rlPlan = data.rl_plan;
        const hotspot = data.hotspot;

        // 1. Render Active Flame Front Core
        this.spreadDataSource.entities.add({
            position: Cesium.Cartesian3.fromDegrees(hotspot.longitude, hotspot.latitude, 80),
            billboard: {
                image: '/static/assets/logos/logo_concept_07_thermal_flare_core.jpg',
                width: 48,
                height: 48,
                color: Cesium.Color.fromCssColorString('#ff1744'),
                heightReference: Cesium.HeightReference.RELATIVE_TO_GROUND
            },
            label: {
                text: `ACTIVE FRONT (112 MW)\nSpread: 89% to Valley B`,
                font: 'bold 12px "JetBrains Mono", monospace',
                style: Cesium.LabelStyle.FILL_AND_OUTLINE,
                fillColor: Cesium.Color.WHITE,
                outlineColor: Cesium.Color.BLACK,
                outlineWidth: 3,
                verticalOrigin: Cesium.VerticalOrigin.BOTTOM,
                pixelOffset: new Cesium.Cartesian2(0, -28),
                heightReference: Cesium.HeightReference.RELATIVE_TO_GROUND
            }
        });

        // 2. Render XGBoost Spread Hazard Elliptical Contour
        if (forecast && forecast.contour_polygon) {
            const flatCoords = [];
            forecast.contour_polygon.forEach(pt => {
                flatCoords.push(pt[0], pt[1]); // lon, lat
            });

            this.spreadDataSource.entities.add({
                name: 'XGBoost 4-Hour Propagation Hazard Contour',
                polygon: {
                    hierarchy: Cesium.Cartesian3.fromDegreesArray(flatCoords),
                    material: Cesium.Color.fromCssColorString('#ea580c').withAlpha(0.35),
                    outline: true,
                    outlineColor: Cesium.Color.fromCssColorString('#f97316'),
                    outlineWidth: 3,
                    heightReference: Cesium.HeightReference.CLAMP_TO_GROUND
                }
            });

            // Spread Vector Arrow / Label
            this.spreadDataSource.entities.add({
                position: Cesium.Cartesian3.fromDegrees(forecast.center.longitude, forecast.center.latitude, 60),
                label: {
                    text: `XGBOOST SPREAD CONTOUR\nProb: ${Math.round(forecast.spread_probability * 100)}% | ROS: ${forecast.ros_km_h} km/h`,
                    font: 'bold 11px "JetBrains Mono", monospace',
                    fillColor: Cesium.Color.fromCssColorString('#f97316'),
                    outlineColor: Cesium.Color.BLACK,
                    outlineWidth: 3,
                    heightReference: Cesium.HeightReference.RELATIVE_TO_GROUND
                }
            });
        }

        // 3. Render RL Containment Lines & Units
        if (rlPlan && rlPlan.containment_lines) {
            rlPlan.containment_lines.forEach(line => {
                const flatCoords = [];
                line.coordinates.forEach(pt => {
                    flatCoords.push(pt[0], pt[1]);
                });

                const color = Cesium.Color.fromCssColorString(line.color);

                this.rlDataSource.entities.add({
                    name: line.name,
                    polyline: {
                        positions: Cesium.Cartesian3.fromDegreesArray(flatCoords),
                        width: line.width || 5,
                        material: new Cesium.PolylineGlowMaterialProperty({
                            glowPower: 0.3,
                            color: color
                        }),
                        clampToGround: true
                    }
                });

                // Label at start of line
                const startPt = line.coordinates[0];
                this.rlDataSource.entities.add({
                    position: Cesium.Cartesian3.fromDegrees(startPt[0], startPt[1], 100),
                    label: {
                        text: `RL: ${line.name.toUpperCase()}`,
                        font: '600 11px "JetBrains Mono", monospace',
                        fillColor: color,
                        outlineColor: Cesium.Color.BLACK,
                        outlineWidth: 3,
                        verticalOrigin: Cesium.VerticalOrigin.BOTTOM,
                        pixelOffset: new Cesium.Cartesian2(0, -10),
                        heightReference: Cesium.HeightReference.RELATIVE_TO_GROUND
                    }
                });
            });
        }
    }

    displayLangSmithTrace(trace, rlPlan) {
        const drawer = document.getElementById('langsmith-drawer');
        if (!drawer) return;

        drawer.classList.remove('collapsed');

        const elTraceId = document.getElementById('ls-trace-id');
        if (elTraceId) elTraceId.textContent = trace.trace_id;

        const elLatency = document.getElementById('ls-latency');
        if (elLatency) elLatency.textContent = `${trace.latency_ms} ms · $${trace.estimated_cost_usd}`;

        const elTokens = document.getElementById('ls-tokens');
        if (elTokens) elTokens.textContent = `${trace.llm_call.tokens_total} tokens (${trace.llm_call.tokens_prompt} prompt / ${trace.llm_call.tokens_completion} comp)`;

        const elInput = document.getElementById('ls-input-payload');
        if (elInput) elInput.textContent = JSON.stringify(trace.input_payload, null, 2);

        const elOutput = document.getElementById('ls-output-text');
        if (elOutput) elOutput.textContent = trace.output;

        const elGuardrail = document.getElementById('ls-guardrail-status');
        if (elGuardrail) elGuardrail.textContent = `${trace.hallucination_check.status} (${trace.hallucination_check.facts_grounded_pct})`;

        // Populate unit action list
        const unitList = document.getElementById('ls-units-dispatched-list');
        if (unitList && rlPlan && rlPlan.units) {
            unitList.innerHTML = rlPlan.units.map(u => `
                <div class="rl-unit-item">
                    <div class="unit-hdr">
                        <span class="unit-badge ${u.unit_type}">${u.unit_name}</span>
                        <span class="unit-eta">ETA ${u.eta_minutes}m</span>
                    </div>
                    <div class="unit-desc">${u.tactical_rationale}</div>
                </div>
            `).join('');
        }
    }

    async refreshLangSmithTraces() {
        const data = await window.dataService.fetchLangSmithTraces();
        if (data && data.traces && data.traces.length > 0) {
            const latest = data.traces[data.traces.length - 1];
            this.displayLangSmithTrace(latest, null);
        }
    }

    handleRemoteScenario(msg) {
        this.runMountainRidgeScenario();
    }
}
