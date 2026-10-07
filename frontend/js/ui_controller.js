/**
 * UI Controller: Updates the HUD dashboard, telemetry bar,
 * LOD badges, statistics charts, and hotspot detail modal.
 */

class UIController {
    constructor() {
        // Telemetry DOM
        this.elAltitude = document.getElementById('telem-altitude');
        this.elCoords = document.getElementById('telem-coords');
        this.elOrientation = document.getElementById('telem-orientation');
        this.elLodBadge = document.getElementById('lod-badge');

        // Dynamic Viewport Stats DOM
        this.elRegionName = document.getElementById('active-region-name');
        this.elTotal = document.getElementById('stat-total');
        this.elModis = document.getElementById('stat-modis');
        this.elViirs = document.getElementById('stat-viirs');
        this.elBarModis = document.getElementById('bar-modis');
        this.elBarViirs = document.getElementById('bar-viirs');
        this.elAvgFrp = document.getElementById('stat-avg-frp');
        this.elMaxFrp = document.getElementById('stat-max-frp');
        this.elHighRisk = document.getElementById('stat-high-risk');
        this.elHighConf = document.getElementById('stat-high-conf');
        this.elBurnedArea = document.getElementById('stat-burned-area');
        this.elCarbonCo2 = document.getElementById('stat-carbon-co2');
        this.elEnergy = document.getElementById('stat-energy');
        this.elSpinner = document.getElementById('query-spinner');

        // LOD Explainer DOM
        this.elLodTitle = document.getElementById('lod-title');
        this.elLodDesc = document.getElementById('lod-desc');

        // Modal DOM
        this.elModal = document.getElementById('hotspot-modal');
        this.elModalClose = document.getElementById('modal-close');
        this.elModalRisk = document.getElementById('modal-risk');
        this.elModalTitle = document.getElementById('modal-title');
        this.elModalRegion = document.getElementById('modal-region');
        this.elModalFrp = document.getElementById('modal-frp');
        this.elModalMlProb = document.getElementById('modal-ml-prob');
        this.elModalConf = document.getElementById('modal-conf');
        this.elModalSensor = document.getElementById('modal-sensor');
        this.elModalBrightness = document.getElementById('modal-brightness');
        this.elModalCoords = document.getElementById('modal-coords');
        this.elModalTime = document.getElementById('modal-time');
        this.elModalLand = document.getElementById('modal-land');
        this.elModalZoomBtn = document.getElementById('modal-zoom-btn');

        // Current inspected hotspot data
        this.activeInspectedHotspot = null;

        // Callback hooks
        this.onFilterChanged = null;
        this.onFlyToRequested = null;
        this.onFocusCameraRequested = null;

        this._setupListeners();
    }

    _setupListeners() {
        // Modal close
        this.elModalClose.addEventListener('click', () => {
            this.hideDetailModal();
        });

        // Close modal on Escape key
        window.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.hideDetailModal();
            }
        });

        // Focus camera from modal
        this.elModalZoomBtn.addEventListener('click', () => {
            if (this.activeInspectedHotspot && this.onFocusCameraRequested) {
                this.onFocusCameraRequested(
                    this.activeInspectedHotspot.latitude,
                    this.activeInspectedHotspot.longitude
                );
            }
        });

        // =====================================================================
        // Collapsible Accordion Sections in Right Panel
        // =====================================================================
        const accordionHeaders = document.querySelectorAll('.accordion-header');
        accordionHeaders.forEach(header => {
            header.addEventListener('click', () => {
                const section = header.closest('.accordion-section');
                if (section) {
                    section.classList.toggle('expanded');
                }
            });
        });

        // =====================================================================
        // Sidebar Drawers (Zen Mode Map Collapse & Reopen)
        // =====================================================================
        const btnToggleLeft = document.getElementById('btn-toggle-left-panel');
        const btnToggleRight = document.getElementById('btn-toggle-right-panel');
        const reopenLeft = document.getElementById('reopen-left-tab');
        const reopenRight = document.getElementById('reopen-right-tab');
        const leftPanel = document.getElementById('left-panel');
        const rightPanel = document.getElementById('right-panel');

        if (btnToggleLeft && leftPanel) {
            btnToggleLeft.addEventListener('click', () => {
                leftPanel.classList.add('collapsed');
                if (reopenLeft) reopenLeft.classList.remove('hidden');
            });
        }
        if (reopenLeft && leftPanel) {
            reopenLeft.addEventListener('click', () => {
                leftPanel.classList.remove('collapsed');
                reopenLeft.classList.add('hidden');
            });
        }

        if (btnToggleRight && rightPanel) {
            btnToggleRight.addEventListener('click', () => {
                rightPanel.classList.add('collapsed');
                if (reopenRight) reopenRight.classList.remove('hidden');
            });
        }
        if (reopenRight && rightPanel) {
            reopenRight.addEventListener('click', () => {
                rightPanel.classList.remove('collapsed');
                reopenRight.classList.add('hidden');
            });
        }

        // =====================================================================
        // Camera D-Pad Minimizable Controller
        // =====================================================================
        const dpadWidget = document.getElementById('camera-dpad-widget');
        const dpadToggleBtn = document.getElementById('dpad-toggle-btn');
        const dpadMinIcon = document.getElementById('dpad-min-icon');

        if (dpadToggleBtn && dpadWidget) {
            dpadToggleBtn.addEventListener('click', () => {
                const isMinimized = dpadWidget.classList.toggle('minimized');
                if (dpadMinIcon) {
                    dpadMinIcon.textContent = isMinimized ? '▲' : '▼';
                }
            });
        }

        // =====================================================================
        // Whole Earth Navigation: Presets, Continents, Search & Cinematic Tour
        // =====================================================================
        const flyButtons = document.querySelectorAll('.fly-btn');
        flyButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                flyButtons.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                const target = btn.getAttribute('data-target');
                if (this.onFlyToRequested) {
                    this.onFlyToRequested(target);
                }
            });
        });

        // Continent Tabs Filter
        // =====================================================================
        // Hierarchical Area Switcher: Switch to Any Country or Region on Earth
        // =====================================================================
        const continentSelect = document.getElementById('continent-select');
        const countrySelect = document.getElementById('country-select');
        const btnJumpCountry = document.getElementById('btn-jump-country');

        const populateCountryDropdown = (continentId) => {
            if (!countrySelect || !window.WORLD_ATLAS) return;
            const areas = window.WORLD_ATLAS.getAreasByContinent(continentId);

            // Sort areas alphabetically by name, but keep Whole Earth & Bangladesh on top
            const sorted = [...areas].sort((a, b) => {
                if (a.id === 'global') return -1;
                if (b.id === 'global') return 1;
                if (a.id === 'bd') return -1;
                if (b.id === 'bd') return 1;
                return a.name.localeCompare(b.name);
            });

            countrySelect.innerHTML = sorted.map(a => {
                const label = `${a.flag || '📍'} ${a.name}${a.nativeName ? ' (' + a.nativeName + ')' : ''}`;
                return `<option value="${a.id}" data-lat="${a.lat}" data-lon="${a.lon}" data-alt="${a.alt}" data-query="${a.query || ''}">${label}</option>`;
            }).join('');
        };

        if (continentSelect && countrySelect) {
            populateCountryDropdown('all');

            continentSelect.addEventListener('change', (e) => {
                const continentId = e.target.value;
                populateCountryDropdown(continentId);

                // Also update continent tabs active state and fly-to grid filter
                continentTabs.forEach(t => {
                    if (t.getAttribute('data-continent') === continentId) {
                        t.classList.add('active');
                    } else {
                        t.classList.remove('active');
                    }
                });

                flyButtons.forEach(btn => {
                    const btnContinent = btn.getAttribute('data-continent');
                    if (continentId === 'all' || btnContinent === continentId || btnContinent === 'global') {
                        btn.style.display = 'flex';
                    } else {
                        btn.style.display = 'none';
                    }
                });
            });

            const flyToSelectedArea = () => {
                const selectedOpt = countrySelect.options[countrySelect.selectedIndex];
                if (!selectedOpt) return;
                const query = selectedOpt.getAttribute('data-query');
                const lat = parseFloat(selectedOpt.getAttribute('data-lat'));
                const lon = parseFloat(selectedOpt.getAttribute('data-lon'));
                const alt = parseFloat(selectedOpt.getAttribute('data-alt'));

                if (this.hideDetailModal) this.hideDetailModal();

                if (query && window.cameraController && window.cameraController.presets[query]) {
                    if (this.onFlyToRequested) this.onFlyToRequested(query);
                } else if (!isNaN(lat) && !isNaN(lon) && window.cameraController) {
                    window.cameraController.flyToCoordinates(lon, lat, alt || 1500000);
                }
            };

            countrySelect.addEventListener('change', flyToSelectedArea);
            if (btnJumpCountry) {
                btnJumpCountry.addEventListener('click', flyToSelectedArea);
            }
        }

        // Continent Tabs Filter
        const continentTabs = document.querySelectorAll('.cont-tab');
        continentTabs.forEach(tab => {
            tab.addEventListener('click', () => {
                continentTabs.forEach(t => t.classList.remove('active'));
                tab.classList.add('active');
                const selectedContinent = tab.getAttribute('data-continent');

                // Synchronize continent select dropdown
                if (continentSelect) {
                    continentSelect.value = selectedContinent;
                    populateCountryDropdown(selectedContinent);
                }

                flyButtons.forEach(btn => {
                    const btnContinent = btn.getAttribute('data-continent');
                    if (selectedContinent === 'all' || btnContinent === selectedContinent || btnContinent === 'global') {
                        btn.style.display = 'flex';
                    } else {
                        btn.style.display = 'none';
                    }
                });
            });
        });

        // Global Search Input with Fast Autocomplete & Live Geocoding
        const searchInput = document.getElementById('global-search-input');
        const searchClearBtn = document.getElementById('search-clear-btn');
        const autocompleteList = document.getElementById('search-autocomplete-list');
        let geocodeDebounceTimer = null;

        if (searchInput && autocompleteList) {
            const renderSearchResults = (items) => {
                if (!items || items.length === 0) {
                    autocompleteList.innerHTML = `<div class="search-item no-match">No matching geographic zones found</div>`;
                    autocompleteList.classList.remove('hidden');
                    return;
                }

                autocompleteList.innerHTML = items.map(loc => `
                    <div class="search-item" data-query="${loc.query || ''}" data-lon="${loc.lon}" data-lat="${loc.lat}" data-alt="${loc.alt || 1500000}">
                        <span class="search-item-icon">${loc.flag || loc.icon || '📍'}</span>
                        <div class="search-item-info">
                            <span class="search-item-name">${loc.name}${loc.nativeName ? ' (' + loc.nativeName + ')' : ''}</span>
                            <span class="search-item-sub">${(loc.continent || loc.country || loc.type || 'GLOBAL').toUpperCase()}</span>
                        </div>
                        <span class="search-item-badge ${loc.isLive ? 'live' : 'country'}">${loc.isLive ? 'LIVE' : 'ATLAS'}</span>
                        <span class="search-item-arrow">→</span>
                    </div>
                `).join('');

                autocompleteList.classList.remove('hidden');

                autocompleteList.querySelectorAll('.search-item').forEach(item => {
                    item.addEventListener('click', () => {
                        const query = item.getAttribute('data-query');
                        const lon = parseFloat(item.getAttribute('data-lon'));
                        const lat = parseFloat(item.getAttribute('data-lat'));
                        const alt = parseFloat(item.getAttribute('data-alt'));

                        // Highlight matching preset button if any
                        flyButtons.forEach(b => {
                            if (query && b.getAttribute('data-target') === query) {
                                b.classList.add('active');
                            } else {
                                b.classList.remove('active');
                            }
                        });

                        if (this.hideDetailModal) this.hideDetailModal();

                        if (query && window.cameraController && window.cameraController.presets[query]) {
                            if (this.onFlyToRequested) this.onFlyToRequested(query);
                        } else if (!isNaN(lon) && !isNaN(lat) && window.cameraController) {
                            window.cameraController.flyToCoordinates(lon, lat, alt || 1500000);
                        }

                        autocompleteList.classList.add('hidden');
                        searchInput.value = item.querySelector('.search-item-name').textContent;
                    });
                });
            };

            searchInput.addEventListener('input', (e) => {
                const q = e.target.value.trim();
                if (q.length > 0) {
                    if (searchClearBtn) searchClearBtn.classList.remove('hidden');
                } else {
                    if (searchClearBtn) searchClearBtn.classList.add('hidden');
                    autocompleteList.classList.add('hidden');
                    return;
                }

                // 1. Instant local search from WORLD_ATLAS (160+ countries & BD regions)
                let localMatches = [];
                if (window.WORLD_ATLAS) {
                    localMatches = window.WORLD_ATLAS.search(q, 8);
                }

                renderSearchResults(localMatches);

                // 2. Live server geocoder fallback for custom cities/towns/landmarks
                if (geocodeDebounceTimer) clearTimeout(geocodeDebounceTimer);
                if (q.length >= 2) {
                    geocodeDebounceTimer = setTimeout(async () => {
                        try {
                            const res = await fetch(`/api/geocode?q=${encodeURIComponent(q)}`);
                            if (!res.ok) return;
                            const data = await res.json();
                            if (data && data.results && data.results.length > 0) {
                                const liveItems = data.results.map(r => ({
                                    name: r.name,
                                    continent: r.country || r.type,
                                    lat: r.lat,
                                    lon: r.lon,
                                    alt: r.alt,
                                    flag: '🌐',
                                    isLive: true
                                }));

                                const combined = [...localMatches];
                                for (const item of liveItems) {
                                    const exists = combined.some(c => 
                                        Math.abs(c.lat - item.lat) < 0.15 && Math.abs(c.lon - item.lon) < 0.15
                                    );
                                    if (!exists) {
                                        combined.push(item);
                                    }
                                }
                                renderSearchResults(combined.slice(0, 10));
                            }
                        } catch (err) {
                            // Fallback to local matches cleanly
                        }
                    }, 280);
                }
            });

            if (searchClearBtn) {
                searchClearBtn.addEventListener('click', () => {
                    searchInput.value = '';
                    searchClearBtn.classList.add('hidden');
                    autocompleteList.classList.add('hidden');
                });
            }

            document.addEventListener('click', (e) => {
                if (!e.target.closest('.nav-search-container')) {
                    autocompleteList.classList.add('hidden');
                }
            });
        }

        // Cinematic Guided Tour Button
        const cinematicTourBtn = document.getElementById('cinematic-tour-btn');
        if (cinematicTourBtn) {
            cinematicTourBtn.addEventListener('click', () => {
                if (!window.cameraController) return;
                if (window.cameraController.tourActive) {
                    window.cameraController.stopCinematicTour();
                    cinematicTourBtn.classList.remove('touring');
                    cinematicTourBtn.innerHTML = '<span class="btn-icon">🎬</span> Start Global Cinematic Tour';
                } else {
                    cinematicTourBtn.classList.add('touring');
                    cinematicTourBtn.innerHTML = '<span class="btn-icon">⏹️</span> Stop Tour';
                    window.cameraController.startCinematicTour((stop) => {
                        if (stop) {
                            flyButtons.forEach(b => {
                                if (b.getAttribute('data-target') === stop) {
                                    b.classList.add('active');
                                } else {
                                    b.classList.remove('active');
                                }
                            });
                        } else {
                            cinematicTourBtn.classList.remove('touring');
                            cinematicTourBtn.innerHTML = '<span class="btn-icon">🎬</span> Start Global Cinematic Tour';
                        }
                    });
                }
            });
        }

        // Sensor Filter
        const sensorButtons = document.querySelectorAll('.sensor-btn');
        sensorButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                sensorButtons.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                const sensor = btn.getAttribute('data-sensor');
                if (this.onFilterChanged) {
                    this.onFilterChanged({ sensor });
                }
            });
        });

        // FRP Slider
        const frpSlider = document.getElementById('frp-slider');
        const frpValDisplay = document.getElementById('frp-val-display');
        frpSlider.addEventListener('input', (e) => {
            const val = parseFloat(e.target.value);
            frpValDisplay.textContent = `${val} MW`;
            if (this.onFilterChanged) {
                this.onFilterChanged({ minFrp: val });
            }
        });

        // Auto rotate
        const autoRotateCheckbox = document.getElementById('auto-rotate-toggle');
        autoRotateCheckbox.addEventListener('change', (e) => {
            if (window.cameraController) {
                window.cameraController.setAutoRotate(e.target.checked);
            }
        });
    }

    setLoading(isLoading) {
        if (isLoading) {
            this.elSpinner.classList.add('active');
        } else {
            this.elSpinner.classList.remove('active');
        }
    }

    updateTelemetry(telemetry) {
        // Format altitude
        let altStr = '';
        if (telemetry.altitudeKm >= 1000) {
            altStr = `${(telemetry.altitudeKm / 1000).toFixed(1)}k km`;
        } else {
            altStr = `${Math.round(telemetry.altitudeKm)} km`;
        }
        this.elAltitude.textContent = altStr;

        // Coordinates
        const latHemi = telemetry.latDeg >= 0 ? 'N' : 'S';
        const lonHemi = telemetry.lonDeg >= 0 ? 'E' : 'W';
        this.elCoords.textContent = `${Math.abs(telemetry.latDeg).toFixed(2)}° ${latHemi}, ${Math.abs(telemetry.lonDeg).toFixed(2)}° ${lonHemi}`;

        // Orientation
        this.elOrientation.textContent = `${telemetry.headingDeg}° / ${telemetry.pitchDeg}°`;
    }

    updateViewportStats(data) {
        if (!data || !data.summary) return;

        const summary = data.summary;
        const lod = data.lod;

        // Region Name
        this.elRegionName.textContent = summary.region_name || 'Visible Geographic Region';

        // Total Hotspots
        this.elTotal.textContent = Number(summary.total_hotspots).toLocaleString();

        // Sensor counts & Ratio bar
        this.elModis.textContent = Number(summary.modis_count).toLocaleString();
        this.elViirs.textContent = Number(summary.viirs_count).toLocaleString();

        const total = summary.total_hotspots || 1;
        const modisPct = Math.round((summary.modis_count / total) * 100);
        const viirsPct = 100 - modisPct;
        this.elBarModis.style.width = `${modisPct}%`;
        this.elBarViirs.style.width = `${viirsPct}%`;

        // FRP and Risk
        this.elAvgFrp.innerHTML = `${summary.avg_frp.toFixed(1)} <span class="unit">MW</span>`;
        this.elMaxFrp.textContent = `${summary.max_frp.toFixed(1)} MW`;
        this.elHighRisk.textContent = Number(summary.high_risk_count).toLocaleString();
        this.elHighConf.textContent = Number(summary.high_confidence_count).toLocaleString();

        // Environmental Impact in Viewport
        if (this.elBurnedArea && summary.burned_area_sqkm !== undefined) {
            this.elBurnedArea.innerHTML = `${Number(summary.burned_area_sqkm).toLocaleString()} <span class="unit">km²</span>`;
        }
        if (this.elCarbonCo2 && summary.carbon_co2_mt !== undefined) {
            this.elCarbonCo2.textContent = `${summary.carbon_co2_mt} Mt`;
        }
        if (this.elEnergy && summary.total_energy_gw !== undefined) {
            this.elEnergy.innerHTML = `${summary.total_energy_gw} <span class="unit">GW</span>`;
        }

        // LOD Badge and descriptions
        if (lod) {
            this.elLodBadge.textContent = `LOD ${lod.level} • ${lod.name.toUpperCase()}`;
            this.elLodTitle.textContent = `${lod.name} (${lod.description})`;

            let explainer = '';
            if (lod.level === 1) {
                explainer = 'Displaying global macro density clusters to minimize render load. Zoom into continents or countries for localized sensor telemetry.';
            } else if (lod.level === 2) {
                explainer = 'Continental view: Displaying sub-continental fire nodes with aggregated hotspot counts and regional intensity.';
            } else if (lod.level === 3) {
                explainer = 'Country view: Displaying divisional/regional cluster centroids. Zoom closer for individual 375m & 1km detection points.';
            } else if (lod.level === 4) {
                explainer = 'City / District view: Displaying individual MODIS (1km) & VIIRS (375m) satellite detection points with FRP-scaled glowing markers.';
            } else {
                explainer = 'High-Precision view: Displaying high-detail multi-spectral fire detection attributes, flame radiative intensity, and ML fire confidence.';
            }
            this.elLodDesc.textContent = explainer;
        }
    }

    showDetailModal(hotspot) {
        this.activeInspectedHotspot = hotspot;

        // Immediately hide hover tooltip so both cards do not clash
        const hoverTooltip = document.getElementById('hover-tooltip');
        if (hoverTooltip) {
            hoverTooltip.classList.add('hidden');
        }

        // Auto-minimize camera D-Pad to ensure unobstructed center view
        const dpadWidget = document.getElementById('camera-dpad-widget');
        const dpadMinIcon = document.getElementById('dpad-min-icon');
        if (dpadWidget && !dpadWidget.classList.contains('minimized')) {
            dpadWidget.classList.add('minimized');
            if (dpadMinIcon) dpadMinIcon.textContent = '▲';
        }

        this.elModalTitle.textContent = `Hotspot ${hotspot.id || 'N/A'}`;
        this.elModalRegion.textContent = hotspot.region || 'Active Fire Zone';

        // Risk badge
        const risk = hotspot.risk_level || 'HIGH';
        this.elModalRisk.textContent = `${risk} RISK`;
        this.elModalRisk.style.color = hotspot.color_hex || '#ff5722';
        this.elModalRisk.style.borderColor = hotspot.color_hex || '#ff5722';

        // Metrics
        this.elModalFrp.textContent = `${hotspot.harmonized_frp || hotspot.avg_frp || 0} MW`;
        this.elModalMlProb.textContent = hotspot.ml_probability ? `${(hotspot.ml_probability * 100).toFixed(1)}%` : '98.5%';
        this.elModalConf.textContent = `${Math.round(hotspot.confidence || 85)}%`;

        // Details
        this.elModalSensor.textContent = hotspot.sensor ? `${hotspot.sensor.replace('_', ' ')} (${hotspot.resolution_m || 375}m)` : 'Multi-sensor Fusion';
        this.elModalBrightness.textContent = hotspot.brightness_k ? `${hotspot.brightness_k.toFixed(1)} K` : '340.5 K';
        this.elModalCoords.textContent = `${hotspot.latitude.toFixed(4)}° N, ${hotspot.longitude.toFixed(4)}° E`;
        this.elModalTime.textContent = hotspot.timestamp || '2026-10-03 Recent Pass';
        this.elModalLand.textContent = hotspot.land_cover || 'Vegetation / Forest Shrubland';

        this.elModal.classList.remove('hidden');
    }

    hideDetailModal() {
        this.elModal.classList.add('hidden');
        this.activeInspectedHotspot = null;
    }
}

window.UIController = UIController;
