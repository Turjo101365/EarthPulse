/**
 * EarthPulse 3D - page_controller.js
 * Master Single-Page-Application (SPA) view router & backend data orchestrator.
 * Dynamically switches between the 3D Globe and full-screen dedicated subsystem pages:
 *   - 'globe'        : 3D Photorealistic Orbital Globe (CesiumJS)
 *   - 'impact'       : Global Earth Impact & FIRMS Biosphere Analytics
 *   - 'architecture' : System Architecture & 5 Core Subsystems
 *   - 'rl'           : Autonomous Reinforcement Learning (PPO) Crisis Dispatch
 *   - 'grafana'      : Grafana Operations & Prometheus Telemetry Hub
 *   - 'langsmith'    : LangSmith AI Reasoning Audit & Guardrails Suite
 */

(function () {
    'use strict';

    class PageController {
        constructor() {
            this.currentPage = 'globe';
            this.currentTimeRange = '24h';
            this.activeArchTab = 'roles';
            this.init();
        }

        init() {
            // Header buttons
            this.btnGlobe = document.getElementById('view-mode-globe');
            this.btnImpact = document.getElementById('btn-firms-analytics');
            this.btnArch = document.getElementById('btn-open-arch');
            this.btnRL = document.getElementById('btn-trigger-crisis-scenario');
            this.btnGrafana = document.getElementById('btn-open-grafana');
            this.btnLangSmith = document.getElementById('btn-open-langsmith');

            // 3D HUD containers to hide when in full-screen pages
            this.leftPanel = document.getElementById('left-panel');
            this.rightPanel = document.getElementById('right-panel');
            this.timelineBar = document.getElementById('firms-timeline-bar');
            this.reopenLeft = document.getElementById('reopen-left-tab');
            this.reopenRight = document.getElementById('reopen-right-tab');
            this.dpadContainer = document.getElementById('dpad-container');

            // Fullscreen page containers
            this.pages = {
                impact: document.getElementById('fullscreen-page-impact'),
                architecture: document.getElementById('fullscreen-page-architecture'),
                rl: document.getElementById('fullscreen-page-rl'),
                grafana: document.getElementById('fullscreen-page-grafana'),
                langsmith: document.getElementById('fullscreen-page-langsmith')
            };

            this.bindNavigation();
            this.bindInternalActions();

            // Hash routing support (e.g. #impact, #architecture)
            window.addEventListener('hashchange', () => this.handleHashChange());
            if (window.location.hash) {
                const target = window.location.hash.replace('#', '');
                if (this.pages[target]) {
                    this.showPage(target);
                }
            }

            console.log('⚡ EarthPulse 3D: Page Controller (SPA Subsystem Router) initialized');
        }

        bindNavigation() {
            // Header buttons click handlers
            if (this.btnGlobe) {
                this.btnGlobe.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.showPage('globe');
                });
            }

            if (this.btnImpact) {
                this.btnImpact.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.showPage('impact');
                });
            }

            if (this.btnArch) {
                this.btnArch.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.showPage('architecture');
                });
            }

            if (this.btnRL) {
                this.btnRL.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.showPage('rl');
                });
            }

            if (this.btnGrafana) {
                this.btnGrafana.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.showPage('grafana');
                });
            }

            if (this.btnLangSmith) {
                this.btnLangSmith.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.showPage('langsmith');
                });
            }

            // All "← Back to 3D Globe" buttons inside the pages
            document.querySelectorAll('.btn-back-to-globe').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.showPage('globe');
                });
            });
        }

        handleHashChange() {
            const hash = window.location.hash.replace('#', '');
            if (hash === 'globe' || !hash) {
                this.showPage('globe');
            } else if (this.pages[hash]) {
                this.showPage(hash);
            }
        }

        showPage(pageName) {
            this.currentPage = pageName;
            window.location.hash = pageName === 'globe' ? '' : pageName;

            // Update Header button active states
            const allBtns = [this.btnGlobe, this.btnImpact, this.btnArch, this.btnRL, this.btnGrafana, this.btnLangSmith];
            allBtns.forEach(b => b?.classList.remove('active'));

            // Hide all full-screen pages
            Object.values(this.pages).forEach(p => p?.classList.remove('active'));

            if (pageName === 'globe') {
                this.btnGlobe?.classList.add('active');
                // Restore 3D Globe HUD panels
                if (this.leftPanel) this.leftPanel.style.display = '';
                if (this.rightPanel) this.rightPanel.style.display = '';
                if (this.timelineBar) this.timelineBar.style.display = '';
                if (this.dpadContainer) this.dpadContainer.style.display = '';
                return;
            }

            // We are entering a full-screen dedicated subsystem page
            // Hide 3D Globe HUD panels so they do not overlap
            if (this.leftPanel) this.leftPanel.style.display = 'none';
            if (this.rightPanel) this.rightPanel.style.display = 'none';
            if (this.timelineBar) this.timelineBar.style.display = 'none';
            if (this.dpadContainer) this.dpadContainer.style.display = 'none';

            // Show target page container
            const targetPage = this.pages[pageName];
            if (targetPage) {
                targetPage.classList.add('active');
                targetPage.scrollTop = 0;
            }

            // Highlight corresponding header button
            switch (pageName) {
                case 'impact':
                    this.btnImpact?.classList.add('active');
                    this.loadImpactData(this.currentTimeRange);
                    break;
                case 'architecture':
                    this.btnArch?.classList.add('active');
                    this.loadArchitectureData();
                    break;
                case 'rl':
                    this.btnRL?.classList.add('active');
                    this.loadRLData();
                    break;
                case 'grafana':
                    this.btnGrafana?.classList.add('active');
                    this.loadGrafanaData();
                    break;
                case 'langsmith':
                    this.btnLangSmith?.classList.add('active');
                    this.loadLangSmithData();
                    break;
            }
        }

        // =====================================================================
        // 1. Earth Impact Page (FIRMS Biosphere Analytics)
        // =====================================================================
        async loadImpactData(timeRange = '24h') {
            try {
                const res = await fetch(`/api/firms/analytics?time_range=${timeRange}`);
                if (!res.ok) return;
                const data = await res.json();
                this.renderImpactData(data);
            } catch (err) {
                console.error('Failed to load impact analytics:', err);
            }
        }

        renderImpactData(data) {
            if (!data) return;

            // KPIs
            const impact = data.impact || data.global_metrics;
            if (impact) {
                const burnedSqKm = impact.estimated_burned_area_sqkm ?? impact.burned_area_sqkm ?? 0;
                const burnedHa = impact.burned_area_hectares ?? (burnedSqKm * 100);
                const carbonMt = impact.carbon_co2_megatons ?? impact.carbon_co2_mt ?? 0;
                const methaneKt = impact.methane_ch4_kt ?? (carbonMt * 4.5);
                const energyGw = impact.total_radiative_energy_gw ?? impact.total_energy_gw ?? 0;
                const totalHotspots = data.active_hotspots_total ?? impact.total_hotspots ?? 0;

                const elBurned = document.getElementById('sp-burned-area');
                if (elBurned) elBurned.innerHTML = `${Math.round(burnedSqKm).toLocaleString()} <span style="font-size:1.1rem; color:#94a3b8;">km²</span>`;

                const elBurnedHa = document.getElementById('sp-burned-ha');
                if (elBurnedHa) elBurnedHa.textContent = `${Math.round(burnedHa).toLocaleString()} hectares across active zones`;

                const elCarbon = document.getElementById('sp-carbon');
                if (elCarbon) elCarbon.innerHTML = `${Number(carbonMt).toFixed(1)} <span style="font-size:1.1rem; color:#94a3b8;">Mt</span>`;

                const elMethane = document.getElementById('sp-methane');
                if (elMethane) elMethane.textContent = `CH₄ Methane: ${Number(methaneKt).toFixed(1)} kt`;

                const elEnergy = document.getElementById('sp-energy');
                if (elEnergy) elEnergy.innerHTML = `${Number(energyGw).toFixed(1)} <span style="font-size:1.1rem; color:#94a3b8;">GW</span>`;

                const elDetections = document.getElementById('sp-detections');
                if (elDetections) elDetections.textContent = totalHotspots.toLocaleString();
            }

            // 7-Day Trend
            const trend = data.trend_7d || data.seven_day_trend;
            if (trend && Array.isArray(trend)) {
                const wrapper = document.getElementById('sp-trend-wrapper');
                if (wrapper) {
                    const maxVal = Math.max(...trend.map(d => d.count), 1);
                    wrapper.innerHTML = trend.map(d => {
                        const heightPct = Math.max((d.count / maxVal) * 100, 6);
                        const label = d.day || d.date || d.label || '';
                        return `
                            <div class="trend-col">
                                <span class="trend-count">${d.count.toLocaleString()}</span>
                                <div class="trend-bar" style="height:${heightPct}%;"></div>
                                <span class="trend-label">${label}</span>
                            </div>
                        `;
                    }).join('');
                }
            }

            // Diurnal passes
            const diurnal = data.diurnal_cycle || data.diurnal;
            if (diurnal) {
                const dayPct = diurnal.daytime_pct ?? diurnal.day_pct ?? 50;
                const dayCount = diurnal.daytime_count ?? diurnal.day_count ?? 0;
                const nightPct = diurnal.nighttime_pct ?? diurnal.night_pct ?? 50;
                const nightCount = diurnal.nighttime_count ?? diurnal.night_count ?? 0;

                const elDay = document.getElementById('sp-daytime-pct');
                if (elDay) elDay.textContent = `${dayPct}% (${dayCount ? dayCount.toLocaleString() : ''} pings)`;
                const elDayBar = document.getElementById('sp-daytime-bar');
                if (elDayBar) elDayBar.style.width = `${dayPct}%`;

                const elNight = document.getElementById('sp-nighttime-pct');
                if (elNight) elNight.textContent = `${nightPct}% (${nightCount ? nightCount.toLocaleString() : ''} pings)`;
                const elNightBar = document.getElementById('sp-nighttime-bar');
                if (elNightBar) elNightBar.style.width = `${nightPct}%`;
            }

            // Country table
            const countries = data.top_countries || data.country_leaderboard;
            if (countries && Array.isArray(countries)) {
                const tbody = document.getElementById('sp-country-tbody');
                if (tbody) {
                    tbody.innerHTML = countries.slice(0, 10).map((c, idx) => {
                        const cnt = c.hotspot_count ?? c.count ?? 0;
                        const frp = c.avg_frp ? Math.round(c.avg_frp) : 0;
                        const riskLabel = (c.high_risk && c.high_risk > 100) ? 'CRITICAL' : 'HIGH';
                        const riskColor = riskLabel === 'CRITICAL' ? '#ef4444' : '#f59e0b';
                        const riskBg = riskLabel === 'CRITICAL' ? 'rgba(239,68,68,0.2)' : 'rgba(245,158,11,0.2)';
                        return `
                            <tr>
                                <td class="country-name">${idx + 1}. ${c.country}</td>
                                <td class="country-count">${cnt.toLocaleString()}</td>
                                <td class="country-frp">${frp} MW</td>
                                <td><span style="background:${riskBg};color:${riskColor};padding:3px 8px;border-radius:4px;font-size:0.72rem;font-weight:700;">${riskLabel}</span></td>
                            </tr>
                        `;
                    }).join('');
                }
            }

            // Biome list
            const biomes = data.biome_breakdown || data.top_biomes;
            if (biomes && Array.isArray(biomes)) {
                const list = document.getElementById('sp-biome-list');
                if (list) {
                    const colors = ['#10b981', '#f59e0b', '#f97316', '#38bdf8', '#8b5cf6'];
                    list.innerHTML = biomes.map((b, i) => {
                        const name = b.name || b.region || 'Forest';
                        return `
                            <div class="biome-row">
                                <div class="biome-meta">
                                    <span>${name}</span>
                                    <span>${b.count.toLocaleString()} fires (${b.pct}%)</span>
                                </div>
                                <div class="biome-track">
                                    <div class="biome-fill" style="width:${b.pct}%; background:${colors[i % colors.length]};"></div>
                                </div>
                            </div>
                        `;
                    }).join('');
                }
            }
        }

        // =====================================================================
        // 2. Architecture Page
        // =====================================================================
        async loadArchitectureData() {
            this.fetchMLMetrics();
            this.fetchTelemetryHUD();
        }

        async fetchMLMetrics() {
            try {
                const res = await fetch('/api/ml/metrics');
                if (!res.ok) return;
                const d = await res.json();
                const elMps = document.getElementById('sp-mps-status');
                if (elMps && d.mps_model && d.mps_model.metrics) {
                    elMps.textContent = `Active (PR-AUC ${d.mps_model.metrics.pr_auc}, ROC-AUC ${d.mps_model.metrics.roc_auc})`;
                }
                const elXgb = document.getElementById('sp-xgb-status');
                if (elXgb && d.firms_model && d.firms_model.metrics) {
                    elXgb.textContent = `Trained (PR-AUC ${d.firms_model.metrics.pr_auc}, ROC-AUC ${d.firms_model.metrics.roc_auc})`;
                }
            } catch (e) {
                console.warn('ML fetch error:', e);
            }
        }

        async fetchTelemetryHUD() {
            try {
                const res = await fetch('/api/telemetry/stats');
                if (!res.ok) return;
                const d = await res.json();
                const elFrp = document.getElementById('sp-telem-frp');
                if (elFrp && d.active_frp_mw !== undefined) elFrp.textContent = `${Math.round(d.active_frp_mw).toLocaleString()} MW`;
                const elLat = document.getElementById('sp-telem-latency');
                if (elLat && d.postgis_latency_ms !== undefined) elLat.textContent = `${d.postgis_latency_ms} ms`;
                const elReward = document.getElementById('sp-telem-reward');
                if (elReward && d.rl_mean_reward !== undefined) elReward.textContent = `+${d.rl_mean_reward}`;
                const elProt = document.getElementById('sp-telem-protected');
                if (elProt && d.forest_protected_ha !== undefined) elProt.textContent = `${Math.round(d.forest_protected_ha).toLocaleString()} ha`;
            } catch (e) {
                console.warn('Telemetry HUD fetch error:', e);
            }
        }

        // =====================================================================
        // 3. Reinforcement Learning (PPO) Page
        // =====================================================================
        loadRLData() {
            // Already rendered in DOM, ready to trigger scenarios
        }

        async triggerCrisisScenario() {
            const btn = document.getElementById('sp-btn-run-scenario');
            const orderBox = document.getElementById('sp-tactical-order');
            const unitsList = document.getElementById('sp-units-list');
            const statusPill = document.getElementById('sp-scenario-status');

            if (btn) {
                btn.classList.add('pulsing');
                btn.innerHTML = `<span>⏳ Simulating 500 PPO Rollouts...</span>`;
            }
            if (statusPill) {
                statusPill.textContent = 'RUNNING POLICY';
                statusPill.style.color = '#f59e0b';
            }

            try {
                const res = await fetch('/api/scenario/crisis-response', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({})
                });
                const data = await res.json();

                if (data) {
                    if (orderBox && data.trace && data.trace.output) {
                        orderBox.textContent = `"${data.trace.output}"`;
                    }
                    if (unitsList && data.rl_plan && data.rl_plan.units) {
                        unitsList.innerHTML = data.rl_plan.units.map(u => `
                            <div class="unit-item">
                                <div class="unit-header">
                                    <span class="unit-badge ${u.unit_type}">${u.unit_name}</span>
                                    <span class="unit-eta">ETA ${u.eta_minutes}m</span>
                                </div>
                                <div class="unit-desc">${u.tactical_rationale}</div>
                            </div>
                        `).join('');
                    }
                    if (statusPill) {
                        statusPill.textContent = 'DISPATCH COMPLETED';
                        statusPill.style.color = '#10b981';
                    }

                    // Save scenario data for 3D globe transition
                    window._pendingCrisisScenarioData = data;
                }
            } catch (err) {
                console.error('Crisis scenario error:', err);
                if (statusPill) statusPill.textContent = 'FAILED';
            } finally {
                if (btn) {
                    btn.classList.remove('pulsing');
                    btn.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg><span>⚡ Run Mountain Ridge Crisis Scenario</span>`;
                }
            }
        }

        // =====================================================================
        // 4. Grafana Operations Page
        // =====================================================================
        async loadGrafanaData() {
            try {
                const res = await fetch('/api/telemetry/stats');
                if (!res.ok) return;
                const d = await res.json();

                const elFrp = document.getElementById('sp-grafana-frp');
                if (elFrp && d.active_frp_mw !== undefined) elFrp.textContent = `${Math.round(d.active_frp_mw).toLocaleString()} MW`;
                const elLat = document.getElementById('sp-grafana-latency');
                if (elLat && d.postgis_latency_ms !== undefined) elLat.textContent = `${d.postgis_latency_ms} ms`;
                const elReward = document.getElementById('sp-grafana-reward');
                if (elReward && d.rl_mean_reward !== undefined) elReward.textContent = `+${d.rl_mean_reward}`;
                const elProt = document.getElementById('sp-grafana-protected');
                if (elProt && d.forest_protected_ha !== undefined) elProt.textContent = `${Math.round(d.forest_protected_ha).toLocaleString()} ha`;
                const elLag = document.getElementById('sp-grafana-lag');
                if (elLag && d.firms_ingestion_lag_sec !== undefined) elLag.textContent = `${d.firms_ingestion_lag_sec}s`;
                const elDrop = document.getElementById('sp-grafana-drop');
                if (elDrop && d.dedup_drop_ratio !== undefined) elDrop.textContent = `${Math.round(d.dedup_drop_ratio * 100)}%`;

                // Fetch Prometheus /metrics preview
                const resMetrics = await fetch('/metrics');
                if (resMetrics.ok) {
                    const text = await resMetrics.text();
                    const elMetrics = document.getElementById('sp-prometheus-feed');
                    if (elMetrics) elMetrics.textContent = text.slice(0, 1500) + '\n... (truncated)';
                }
            } catch (err) {
                console.error('Grafana data load error:', err);
            }
        }

        // =====================================================================
        // 5. LangSmith Audit Page
        // =====================================================================
        async loadLangSmithData() {
            try {
                const res = await fetch('/api/telemetry/langsmith');
                if (!res.ok) return;
                const data = await res.json();
                if (data && data.traces && data.traces.length > 0) {
                    const latest = data.traces[data.traces.length - 1];
                    this.renderLangSmithTrace(latest);
                }
            } catch (err) {
                console.error('LangSmith traces load error:', err);
            }
        }

        renderLangSmithTrace(trace) {
            if (!trace) return;

            const elTraceId = document.getElementById('sp-ls-trace-id');
            if (elTraceId && trace.trace_id) elTraceId.textContent = trace.trace_id;

            const elLatency = document.getElementById('sp-ls-latency');
            if (elLatency) elLatency.textContent = `${trace.latency_ms || 740} ms · $${trace.estimated_cost_usd || '0.00028'}`;

            const elTokens = document.getElementById('sp-ls-tokens');
            if (elTokens && trace.llm_call) {
                elTokens.textContent = `${trace.llm_call.tokens_total || 525} tokens (${trace.llm_call.tokens_prompt || 380} prompt / ${trace.llm_call.tokens_completion || 145} comp)`;
            }

            const elGuardrail = document.getElementById('sp-ls-guardrail');
            if (elGuardrail && trace.hallucination_check) {
                elGuardrail.textContent = `${trace.hallucination_check.status} (${trace.hallucination_check.facts_grounded_pct})`;
            }

            const elInput = document.getElementById('sp-ls-input');
            if (elInput && trace.input_payload) {
                elInput.textContent = JSON.stringify(trace.input_payload, null, 2);
            }

            const elOutput = document.getElementById('sp-ls-output');
            if (elOutput && trace.output) {
                elOutput.textContent = trace.output;
            }
        }

        async emitTestTrace() {
            const btn = document.getElementById('sp-btn-emit-trace');
            if (!btn) return;
            const orig = btn.textContent;
            btn.textContent = 'Emitting...';
            btn.disabled = true;

            try {
                const res = await fetch('/api/telemetry/langsmith/test', { method: 'POST' });
                const data = await res.json();
                if (data && data.trace) {
                    this.renderLangSmithTrace(data.trace);
                }
                btn.textContent = 'Emitted! ⚡';
            } catch (err) {
                console.error('Test trace failed:', err);
                btn.textContent = 'Failed ❌';
            } finally {
                setTimeout(() => {
                    btn.textContent = orig;
                    btn.disabled = false;
                }, 1600);
            }
        }

        // =====================================================================
        // Internal Button Actions & Tab Switching
        // =====================================================================
        bindInternalActions() {
            // Impact page time range buttons
            document.querySelectorAll('.sp-tr-btn').forEach(btn => {
                btn.addEventListener('click', () => {
                    document.querySelectorAll('.sp-tr-btn').forEach(b => b.classList.remove('active'));
                    btn.classList.add('active');
                    this.currentTimeRange = btn.dataset.range;
                    this.loadImpactData(this.currentTimeRange);
                });
            });

            // Architecture page tabs
            document.querySelectorAll('.sp-arch-tab').forEach(btn => {
                btn.addEventListener('click', () => {
                    document.querySelectorAll('.sp-arch-tab').forEach(b => b.classList.remove('active'));
                    document.querySelectorAll('.sp-arch-panel').forEach(p => p.classList.remove('active'));

                    btn.classList.add('active');
                    const target = document.getElementById(`sp-arch-${btn.dataset.tab}`);
                    if (target) target.classList.add('active');
                });
            });

            // RL page run scenario button
            const btnRun = document.getElementById('sp-btn-run-scenario');
            if (btnRun) {
                btnRun.addEventListener('click', () => this.triggerCrisisScenario());
            }

            // LangSmith emit trace button
            const btnEmit = document.getElementById('sp-btn-emit-trace');
            if (btnEmit) {
                btnEmit.addEventListener('click', () => this.emitTestTrace());
            }

            // Retrain XGBoost button
            const btnXgb = document.getElementById('sp-btn-retrain-xgb');
            if (btnXgb) {
                btnXgb.addEventListener('click', () => this.retrainModel('xgboost_arm64', btnXgb));
            }

            // Retrain MPS GPU button
            const btnMps = document.getElementById('sp-btn-retrain-mps');
            if (btnMps) {
                btnMps.addEventListener('click', () => this.retrainModel('torch_mps', btnMps));
            }

            // Sync FIRMS live button
            const btnSync = document.getElementById('sp-btn-sync-firms');
            if (btnSync) {
                btnSync.addEventListener('click', () => this.syncFirms(btnSync));
            }

            // Clear hotspots button
            const btnClear = document.getElementById('sp-btn-clear-hotspots');
            if (btnClear) {
                btnClear.addEventListener('click', () => this.clearHotspots(btnClear));
            }
        }

        async retrainModel(engine, btn) {
            const feedback = document.getElementById('sp-firms-feedback');
            const orig = btn.textContent;
            btn.disabled = true;
            btn.textContent = '⏳ Training...';
            if (feedback) feedback.textContent = `Training ${engine} on real NASA observations...`;

            try {
                const res = await fetch(`/api/ml/train-firms?target_engine=${engine}&max_samples_per_sensor=3000`, { method: 'POST' });
                const d = await res.json();
                if (feedback) feedback.textContent = `✅ Completed in ${d.duration_sec}s! PR-AUC: ${d.report.metrics.pr_auc}`;
                this.fetchMLMetrics();
            } catch (e) {
                if (feedback) feedback.textContent = `❌ ${e.message}`;
            } finally {
                btn.disabled = false;
                btn.textContent = orig;
            }
        }

        async syncFirms(btn) {
            const feedback = document.getElementById('sp-firms-feedback');
            const orig = btn.textContent;
            btn.disabled = true;
            btn.textContent = '⏳ Ingesting...';
            if (feedback) feedback.textContent = 'Downloading live NASA FIRMS telemetry (MODIS & VIIRS)...';

            try {
                const res = await fetch('/api/firms/sync-live?max_samples_per_sensor=2000', { method: 'POST' });
                const d = await res.json();
                if (feedback) feedback.textContent = `✅ Synced ${d.synced_hotspots.toLocaleString()} real active fire hotspots!`;
            } catch (e) {
                if (feedback) feedback.textContent = `❌ ${e.message}`;
            } finally {
                btn.disabled = false;
                btn.textContent = orig;
            }
        }

        async clearHotspots(btn) {
            const feedback = document.getElementById('sp-firms-feedback');
            const orig = btn.textContent;
            btn.disabled = true;
            btn.textContent = '⏳ Clearing...';
            if (feedback) feedback.textContent = 'Clearing all active hotspots...';

            try {
                const res = await fetch('/api/hotspots/clear', { method: 'POST' });
                const d = await res.json();
                if (feedback) feedback.textContent = '🗑️ All data points successfully removed!';
            } catch (e) {
                if (feedback) feedback.textContent = `❌ ${e.message}`;
            } finally {
                btn.disabled = false;
                btn.textContent = orig;
            }
        }
    }

    // Initialize globally
    const pageController = new PageController();
    window.pageController = pageController;

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => pageController.init());
    }
})();
