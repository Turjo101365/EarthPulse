/**
 * EarthPulse 3D - header_actions.js
 * Bulletproof, zero-dependency immediate DOM event controller for top header tactical actions:
 *   1. Architecture & Intel Modal (#btn-open-arch)
 *   2. Reinforcement Learning PPO Crisis Dispatch (#btn-trigger-crisis-scenario)
 *   3. Grafana Operations Telemetry (#btn-open-grafana)
 *   4. LangSmith LLM Reasoning Audit Drawer (#btn-open-langsmith)
 *
 * Runs synchronously prior to CesiumJS download & WebGL startup,
 * ensuring immediate click responsiveness regardless of network latency.
 */

(function () {
    'use strict';

    class HeaderActionsController {
        constructor() {
            this.initialized = false;
            this.activeTab = 'roles';
            this.init();
        }

        init() {
            if (this.initialized) return;

            // Cache DOM references
            this.modalArch = document.getElementById('fireguard-arch-modal');
            this.backdropArch = document.getElementById('fireguard-arch-backdrop');
            this.btnOpenArch = document.getElementById('btn-open-arch');
            this.btnCloseArch = document.getElementById('btn-close-arch');

            this.btnOpenGrafana = document.getElementById('btn-open-grafana');
            this.btnOpenLangsmith = document.getElementById('btn-open-langsmith');
            this.btnCloseLangsmith = document.getElementById('btn-close-langsmith');
            this.drawerLangsmith = document.getElementById('langsmith-drawer');

            this.btnTriggerScenario = document.getElementById('btn-trigger-crisis-scenario');
            this.btnLsEmitTest = document.getElementById('btn-ls-test-emit');

            this.tabButtons = document.querySelectorAll('.arch-tab-btn');
            this.panelContents = document.querySelectorAll('.arch-panel-content');
            this.telemPills = document.querySelectorAll('.telem-pill');

            this.bindEvents();
            this.initialized = true;
            console.log('⚡ EarthPulse 3D: Header Actions successfully bound to DOM.');
        }

        bindEvents() {
            // 1. Architecture Trigger -> Switch to Architecture Full-Screen Page
            if (this.btnOpenArch) {
                this.btnOpenArch.addEventListener('click', (e) => {
                    e.preventDefault();
                    if (window.pageController) {
                        window.pageController.showPage('architecture');
                        return;
                    }
                    this.openArchitectureModal('roles');
                });
            }

            // Architecture Modal Close Button
            if (this.btnCloseArch) {
                this.btnCloseArch.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.closeArchitectureModal();
                });
            }

            // Architecture Backdrop Click
            if (this.backdropArch) {
                this.backdropArch.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.closeArchitectureModal();
                });
            }

            // Keyboard Escape
            window.addEventListener('keydown', (e) => {
                if (e.key === 'Escape') {
                    if (window.pageController && window.pageController.currentPage !== 'globe') {
                        window.pageController.showPage('globe');
                        return;
                    }
                    if (this.modalArch && !this.modalArch.classList.contains('hidden')) {
                        this.closeArchitectureModal();
                    }
                }
            });

            // Tab Buttons in Architecture Modal
            this.tabButtons.forEach((btn) => {
                btn.addEventListener('click', (e) => {
                    e.preventDefault();
                    const targetTab = btn.getAttribute('data-tab');
                    if (targetTab) {
                        this.switchTab(targetTab);
                    }
                });
            });

            // 2. Grafana Ops Button -> Switch to Grafana Full-Screen Page
            if (this.btnOpenGrafana) {
                this.btnOpenGrafana.addEventListener('click', (e) => {
                    e.preventDefault();
                    if (window.pageController) {
                        window.pageController.showPage('grafana');
                        return;
                    }
                    this.openArchitectureModal('telemetry');
                    this.fetchTelemetryHUD();
                });
            }

            // 3. LangSmith Audit Button -> Switch to LangSmith Full-Screen Page
            if (this.btnOpenLangsmith) {
                this.btnOpenLangsmith.addEventListener('click', (e) => {
                    e.preventDefault();
                    if (window.pageController) {
                        window.pageController.showPage('langsmith');
                        return;
                    }
                    this.toggleLangSmithDrawer();
                });
            }

            if (this.btnCloseLangsmith) {
                this.btnCloseLangsmith.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.closeLangSmithDrawer();
                });
            }

            // Test Emit Trace
            if (this.btnLsEmitTest) {
                this.btnLsEmitTest.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.emitTestTrace();
                });
            }

            // 4. Crisis Scenario (⚡ Reinforcement RL) -> Switch to RL Full-Screen Page
            if (this.btnTriggerScenario) {
                this.btnTriggerScenario.addEventListener('click', (e) => {
                    e.preventDefault();
                    if (window.pageController) {
                        window.pageController.showPage('rl');
                        return;
                    }
                    this.triggerCrisisScenario();
                });
            }

            // HUD Telemetry Strip Pills
            this.telemPills.forEach((pill) => {
                pill.addEventListener('click', () => {
                    if (pill.classList.contains('rl')) {
                        this.openArchitectureModal('ml-rl');
                    } else {
                        this.openArchitectureModal('telemetry');
                    }
                });
            });

            // Internal ML / FIRMS Action Buttons
            this.bindInternalModalButtons();
        }

        bindInternalModalButtons() {
            const btnXgb = document.getElementById('btn-retrain-xgb');
            const btnMps = document.getElementById('btn-retrain-mps');
            const btnSync = document.getElementById('btn-sync-firms');
            const btnClear = document.getElementById('btn-clear-data');

            if (btnXgb) {
                btnXgb.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.retrainModel('xgboost_arm64', btnXgb);
                });
            }
            if (btnMps) {
                btnMps.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.retrainModel('torch_mps', btnMps);
                });
            }
            if (btnSync) {
                btnSync.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.syncFirmsLive(btnSync);
                });
            }
            if (btnClear) {
                btnClear.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.clearAllData(btnClear);
                });
            }
        }

        openArchitectureModal(tabName = 'roles') {
            if (!this.modalArch) return;
            this.modalArch.classList.remove('hidden');
            if (this.backdropArch) {
                this.backdropArch.classList.remove('hidden');
            }
            if (this.btnOpenArch) {
                this.btnOpenArch.classList.add('active');
            }
            if (tabName === 'telemetry' && this.btnOpenGrafana) {
                this.btnOpenGrafana.classList.add('active');
            }
            this.switchTab(tabName);
        }

        closeArchitectureModal() {
            if (this.modalArch) {
                this.modalArch.classList.add('hidden');
            }
            if (this.backdropArch) {
                this.backdropArch.classList.add('hidden');
            }
            if (this.btnOpenArch) {
                this.btnOpenArch.classList.remove('active');
            }
            if (this.btnOpenGrafana) {
                this.btnOpenGrafana.classList.remove('active');
            }
        }

        switchTab(tabName) {
            this.activeTab = tabName;
            this.tabButtons.forEach((b) => {
                b.classList.toggle('active', b.getAttribute('data-tab') === tabName);
            });
            this.panelContents.forEach((panel) => {
                panel.classList.toggle('hidden', panel.id !== `arch-panel-${tabName}`);
            });
            if (tabName === 'telemetry') {
                this.fetchTelemetryHUD();
            } else if (tabName === 'ml-rl') {
                this.fetchMLMetrics();
            }
        }

        toggleLangSmithDrawer() {
            if (!this.drawerLangsmith) return;
            const isCollapsed = this.drawerLangsmith.classList.contains('collapsed');
            if (isCollapsed) {
                this.openLangSmithDrawer();
            } else {
                this.closeLangSmithDrawer();
            }
        }

        openLangSmithDrawer() {
            if (!this.drawerLangsmith) return;
            this.drawerLangsmith.classList.remove('collapsed');
            if (this.btnOpenLangsmith) {
                this.btnOpenLangsmith.classList.add('active');
            }
            this.fetchLatestLangSmithTrace();
        }

        closeLangSmithDrawer() {
            if (!this.drawerLangsmith) return;
            this.drawerLangsmith.classList.add('collapsed');
            if (this.btnOpenLangsmith) {
                this.btnOpenLangsmith.classList.remove('active');
            }
        }

        async fetchLatestLangSmithTrace() {
            try {
                const res = await fetch('/api/telemetry/langsmith');
                if (!res.ok) return;
                const data = await res.json();
                if (data && data.traces && data.traces.length > 0) {
                    const latest = data.traces[data.traces.length - 1];
                    this.displayLangSmithTrace(latest, null);
                }
            } catch (e) {
                console.warn('Failed fetching latest LangSmith trace:', e);
            }
        }

        displayLangSmithTrace(trace, rlPlan) {
            if (!trace) return;
            if (this.drawerLangsmith) {
                this.drawerLangsmith.classList.remove('collapsed');
            }
            if (this.btnOpenLangsmith) {
                this.btnOpenLangsmith.classList.add('active');
            }

            const elTraceId = document.getElementById('ls-trace-id');
            if (elTraceId && trace.trace_id) elTraceId.textContent = trace.trace_id;

            const elLatency = document.getElementById('ls-latency');
            if (elLatency) elLatency.textContent = `${trace.latency_ms || 740} ms · $${trace.estimated_cost_usd || '0.00028'}`;

            const elTokens = document.getElementById('ls-tokens');
            if (elTokens && trace.llm_call) {
                elTokens.textContent = `${trace.llm_call.tokens_total || 525} tokens (${trace.llm_call.tokens_prompt || 380} prompt / ${trace.llm_call.tokens_completion || 145} comp)`;
            }

            const elInput = document.getElementById('ls-input-payload');
            if (elInput && trace.input_payload) {
                elInput.textContent = JSON.stringify(trace.input_payload, null, 2);
            }

            const elOutput = document.getElementById('ls-output-text');
            if (elOutput && trace.output) {
                elOutput.textContent = trace.output;
            }

            const elGuardrail = document.getElementById('ls-guardrail-status');
            if (elGuardrail && trace.hallucination_check) {
                elGuardrail.textContent = `${trace.hallucination_check.status} (${trace.hallucination_check.facts_grounded_pct})`;
            }

            const elCloudStatus = document.getElementById('ls-cloud-status');
            if (elCloudStatus) {
                if (trace.cloud_synced) {
                    elCloudStatus.textContent = 'Live Synced 🟢';
                    elCloudStatus.style.color = '#10b981';
                } else {
                    elCloudStatus.textContent = 'Local Trace 🟢';
                    elCloudStatus.style.color = '#10b981';
                }
            }

            // Populate unit actions
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

        async emitTestTrace() {
            if (!this.btnLsEmitTest) return;
            const origText = this.btnLsEmitTest.textContent;
            this.btnLsEmitTest.textContent = 'Emitting...';
            this.btnLsEmitTest.disabled = true;

            try {
                let result = null;
                if (window.dataService && typeof window.dataService.emitTestLangSmithTrace === 'function') {
                    result = await window.dataService.emitTestLangSmithTrace();
                } else {
                    const res = await fetch('/api/telemetry/langsmith/test', { method: 'POST' });
                    result = await res.json();
                }
                if (result && result.trace) {
                    this.displayLangSmithTrace(result.trace, null);
                }
                this.btnLsEmitTest.textContent = 'Emitted! ⚡';
            } catch (err) {
                console.error('Test trace emit failed:', err);
                this.btnLsEmitTest.textContent = 'Failed ❌';
            } finally {
                setTimeout(() => {
                    if (this.btnLsEmitTest) {
                        this.btnLsEmitTest.textContent = origText;
                        this.btnLsEmitTest.disabled = false;
                    }
                }, 1800);
            }
        }

        async triggerCrisisScenario() {
            // If FireGuardController is initialized with Cesium, delegate to it
            if (window.fireGuardController && typeof window.fireGuardController.runMountainRidgeScenario === 'function') {
                return window.fireGuardController.runMountainRidgeScenario();
            }

            // Fallback: run scenario immediately even if Cesium 3D is still loading
            const btn = this.btnTriggerScenario;
            if (btn) {
                btn.classList.add('pulsing');
                btn.innerHTML = `<span class="spinner-inline"></span> Running PPO Rollouts...`;
            }

            try {
                this.openLangSmithDrawer();

                const res = await fetch('/api/scenario/crisis-response', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({})
                });
                const data = await res.json();

                if (data) {
                    window._pendingCrisisScenarioData = data;
                    this.displayLangSmithTrace(data.trace, data.rl_plan);
                }
            } catch (err) {
                console.error('Failed to trigger crisis scenario:', err);
            } finally {
                if (btn) {
                    btn.classList.remove('pulsing');
                    btn.innerHTML = `<svg class="btn-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg><span>⚡ Reinforcement RL</span>`;
                }
            }
        }

        async fetchTelemetryHUD() {
            try {
                const res = await fetch('/api/telemetry/stats');
                if (!res.ok) return;
                const data = await res.json();
                const elFrp = document.getElementById('arch-telem-frp') || document.getElementById('telem-frp');
                if (elFrp && data.active_frp_mw !== undefined) elFrp.textContent = `${Math.round(data.active_frp_mw || 0).toLocaleString()} MW`;
                const elLat = document.getElementById('arch-telem-latency') || document.getElementById('telem-latency');
                if (elLat && data.postgis_latency_ms !== undefined) elLat.textContent = `${data.postgis_latency_ms || 0} ms`;
                const elReward = document.getElementById('arch-telem-reward') || document.getElementById('telem-reward');
                if (elReward && data.rl_mean_reward !== undefined) {
                    const r = data.rl_mean_reward;
                    elReward.textContent = r > 0 ? `+${r}` : `${r}`;
                }
                const elProt = document.getElementById('arch-telem-protected') || document.getElementById('telem-protected');
                if (elProt && data.forest_protected_ha !== undefined) elProt.textContent = `${Math.round(data.forest_protected_ha || 0).toLocaleString()} ha`;
            } catch (e) {
                console.warn('Telemetry HUD fetch error:', e);
            }
        }

        async fetchMLMetrics() {
            try {
                const res = await fetch('/api/ml/metrics');
                if (!res.ok) return;
                const data = await res.json();
                const elMps = document.getElementById('mps-status-val');
                if (elMps && data.mps_model && data.mps_model.metrics) {
                    elMps.textContent = `Active (PR-AUC ${data.mps_model.metrics.pr_auc}, ROC-AUC ${data.mps_model.metrics.roc_auc})`;
                }
                const elXgb = document.getElementById('xgb-status-val');
                if (elXgb && data.firms_model && data.firms_model.metrics) {
                    elXgb.textContent = `Trained (PR-AUC ${data.firms_model.metrics.pr_auc}, ROC-AUC ${data.firms_model.metrics.roc_auc})`;
                }
            } catch (e) {
                console.warn('ML metrics fetch error:', e);
            }
        }

        async retrainModel(engine, btnEl) {
            const feedback = document.getElementById('firms-train-feedback');
            const origText = btnEl ? btnEl.textContent : '';
            if (btnEl) {
                btnEl.disabled = true;
                btnEl.textContent = '⏳ Training...';
            }
            if (feedback) feedback.textContent = `Training ${engine} on real NASA FIRMS observations...`;

            try {
                const res = await fetch(`/api/ml/train-firms?target_engine=${engine}&max_samples_per_sensor=3000`, {
                    method: 'POST'
                });
                const data = await res.json();
                if (data.report && data.report.metrics) {
                    const m = data.report.metrics;
                    if (feedback) feedback.textContent = `✅ Completed in ${data.duration_sec}s! PR-AUC: ${m.pr_auc} | ROC-AUC: ${m.roc_auc}`;
                }
                await this.fetchMLMetrics();
            } catch (err) {
                if (feedback) feedback.textContent = `❌ Training error: ${err.message}`;
            } finally {
                if (btnEl) {
                    btnEl.disabled = false;
                    btnEl.textContent = origText;
                }
            }
        }

        async syncFirmsLive(btnEl) {
            const feedback = document.getElementById('firms-train-feedback');
            const origText = btnEl ? btnEl.textContent : '';
            if (btnEl) {
                btnEl.disabled = true;
                btnEl.textContent = '⏳ Ingesting...';
            }
            if (feedback) feedback.textContent = 'Downloading live NASA FIRMS telemetry (MODIS & VIIRS)...';

            try {
                const res = await fetch('/api/firms/sync-live?max_samples_per_sensor=2000', { method: 'POST' });
                const data = await res.json();
                if (data.status === 'SUCCESS') {
                    if (feedback) feedback.textContent = `✅ Synced ${data.synced_hotspots.toLocaleString()} real active fire hotspots in ${data.duration_ms}ms!`;
                    if (window.cameraController) {
                        window.cameraController.scheduleFetch();
                    }
                }
            } catch (err) {
                if (feedback) feedback.textContent = `❌ Sync error: ${err.message}`;
            } finally {
                if (btnEl) {
                    btnEl.disabled = false;
                    btnEl.textContent = origText;
                }
            }
        }

        async clearAllData(btnEl) {
            const feedback = document.getElementById('firms-train-feedback');
            const origText = btnEl ? btnEl.textContent : '';
            if (btnEl) {
                btnEl.disabled = true;
                btnEl.textContent = '⏳ Clearing...';
            }
            if (feedback) feedback.textContent = 'Clearing all active hotspots...';

            try {
                const res = await fetch('/api/hotspots/clear', { method: 'POST' });
                const data = await res.json();
                if (data.status === 'SUCCESS') {
                    if (feedback) feedback.textContent = '🗑️ All data points successfully removed!';
                    if (window.cameraController) {
                        window.cameraController.scheduleFetch();
                    }
                }
            } catch (err) {
                if (feedback) feedback.textContent = `❌ Clear error: ${err.message}`;
            } finally {
                if (btnEl) {
                    btnEl.disabled = false;
                    btnEl.textContent = origText;
                }
            }
        }
    }

    // Initialize immediately
    const headerActions = new HeaderActionsController();
    window.earthPulseHeaderActions = headerActions;

    // Redundant guard on DOMContentLoaded
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => headerActions.init());
    }
})();
