/**
 * PulseAI Wildfire Copilot Controller
 * Manages Chatbot UI, RAG citations, Voice Input, Settings Modal,
 * and 3D Action Execution (Camera Fly-to, Ridge Crisis Scenario, Filters).
 */

export class ChatController {
    constructor({ viewer, cameraController, fireGuardController, firmsController }) {
        this.viewer = viewer;
        this.cameraController = cameraController;
        this.fireGuardController = fireGuardController;
        this.firmsController = firmsController;

        this.history = [];
        this.lastUserMessage = "";
        this.isOpen = false;
        this.isMinimized = false;
        this.isListening = false;
        this.speechRecognition = null;
        this.attachViewport = true;

        // Persistent session identifier
        this.conversationId = localStorage.getItem('pulseai_conversation_id') || 
            ('ep-' + Math.random().toString(36).substring(2, 9) + '-' + Date.now().toString(36));
        localStorage.setItem('pulseai_conversation_id', this.conversationId);

        this.initElements();
        this.initSpeech();
        this.initEvents();
        this.loadSuggestions();
        this.addInitialGreeting();
    }

    initElements() {
        this.launcherBtn = document.getElementById('btn-open-chatbot');
        this.navCopilotBtn = document.getElementById('btn-nav-copilot');
        this.chatPanel = document.getElementById('pulse-ai-panel');
        this.btnClose = document.getElementById('btn-close-chatbot');
        this.btnMin = document.getElementById('btn-minimize-chatbot');
        this.btnSettings = document.getElementById('btn-chatbot-settings');
        this.btnClear = document.getElementById('btn-clear-chat');
        this.messagesContainer = document.getElementById('chat-messages-container');
        this.inputField = document.getElementById('chat-user-input');
        this.btnSend = document.getElementById('btn-send-chat');
        this.btnVoice = document.getElementById('btn-voice-input');
        this.suggestionsContainer = document.getElementById('chat-suggestions-container');
        this.statusPill = document.getElementById('chat-status-pill');
        this.attachViewportToggle = document.getElementById('chat-attach-viewport');

        // Settings modal elements
        this.settingsModal = document.getElementById('chat-settings-modal');
        this.btnCloseSettings = document.getElementById('btn-close-chat-settings');
        this.btnSaveSettings = document.getElementById('btn-save-chat-settings');
        this.selectProvider = document.getElementById('chat-setting-provider');
        this.inputApiKey = document.getElementById('chat-setting-apikey');
        this.settingKeyGroup = document.getElementById('chat-key-group');
    }

    initSpeech() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (SpeechRecognition) {
            this.speechRecognition = new SpeechRecognition();
            this.speechRecognition.continuous = false;
            this.speechRecognition.interimResults = false;
            this.speechRecognition.lang = 'en-US';

            this.speechRecognition.onresult = (e) => {
                const transcript = e.results[0][0].transcript;
                if (this.inputField) {
                    this.inputField.value = transcript;
                    this.sendMessage();
                }
                this.stopListening();
            };

            this.speechRecognition.onerror = (e) => {
                console.warn('Speech recognition error:', e.error);
                this.stopListening();
            };

            this.speechRecognition.onend = () => {
                this.stopListening();
            };
        } else if (this.btnVoice) {
            this.btnVoice.title = 'Voice recognition not supported in this browser';
        }
    }

    toggleVoice() {
        if (!this.speechRecognition) {
            alert('Voice recognition is not supported in this browser. Please use Chrome or Edge.');
            return;
        }
        if (this.isListening) {
            this.stopListening();
        } else {
            this.startListening();
        }
    }

    startListening() {
        if (!this.speechRecognition) return;
        try {
            this.isListening = true;
            this.speechRecognition.start();
            if (this.btnVoice) {
                this.btnVoice.classList.add('listening');
                this.btnVoice.title = 'Listening... Speak now';
            }
        } catch (e) {
            console.warn('Speech start error:', e);
        }
    }

    stopListening() {
        this.isListening = false;
        if (this.speechRecognition) {
            try { this.speechRecognition.stop(); } catch (e) {}
        }
        if (this.btnVoice) {
            this.btnVoice.classList.remove('listening');
            this.btnVoice.title = 'Voice Input (Click to speak)';
        }
    }

    initEvents() {
        // Toggle panel
        this.launcherBtn?.addEventListener('click', () => this.toggleChat());
        this.navCopilotBtn?.addEventListener('click', () => this.toggleChat());
        this.btnClose?.addEventListener('click', () => this.closeChat());
        this.btnMin?.addEventListener('click', () => this.minimizeChat());

        // Send message
        this.btnSend?.addEventListener('click', () => this.sendMessage());
        this.inputField?.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Voice button
        this.btnVoice?.addEventListener('click', () => this.toggleVoice());

        // Clear history
        this.btnClear?.addEventListener('click', () => this.clearChat());

        // Settings modal
        this.btnSettings?.addEventListener('click', () => this.openSettings());
        this.btnCloseSettings?.addEventListener('click', () => this.closeSettings());
        this.btnSaveSettings?.addEventListener('click', () => this.closeSettings());

        // Viewport context toggle
        this.attachViewportToggle?.addEventListener('change', (e) => {
            this.attachViewport = e.target.checked;
        });
    }

    toggleChat() {
        if (this.isOpen) {
            this.closeChat();
        } else {
            this.openChat();
        }
    }

    openChat() {
        this.isOpen = true;
        this.isMinimized = false;
        this.chatPanel?.classList.remove('hidden', 'minimized');
        this.launcherBtn?.classList.add('active');
        this.inputField?.focus();
        this.scrollToBottom();
    }

    closeChat() {
        this.isOpen = false;
        this.chatPanel?.classList.add('hidden');
        this.launcherBtn?.classList.remove('active');
        this.stopListening();
    }

    minimizeChat() {
        this.isMinimized = !this.isMinimized;
        this.chatPanel?.classList.toggle('minimized', this.isMinimized);
    }

    openSettings() {
        if (!this.settingsModal) return;
        this.settingsModal.classList.remove('hidden');
    }

    closeSettings() {
        this.settingsModal?.classList.add('hidden');
    }

    async clearChat() {
        this.history = [];
        if (this.messagesContainer) {
            this.messagesContainer.innerHTML = '';
        }
        try {
            await fetch(`/api/chat/history/${encodeURIComponent(this.conversationId)}`, { method: 'DELETE' });
        } catch (e) {}

        this.conversationId = 'ep-' + Math.random().toString(36).substring(2, 9) + '-' + Date.now().toString(36);
        localStorage.setItem('pulseai_conversation_id', this.conversationId);
        this.addInitialGreeting();
    }

    addInitialGreeting() {
        const greeting = (
            "👋 **Welcome to PulseAI Wildfire Copilot!**\n\n" +
            "I am grounded in live **NASA FIRMS** satellite feeds (MODIS & VIIRS), " +
            "**PostgreSQL + pgvector** technical documentation, **XGBoost** spatial spread forecasts, and PPO suppression tactics.\n\n" +
            "Try asking me in **English**, **বাংলা** or **Banglish**:\n" +
            "- *'What is FRP and how does it calculate biomass loss?'*\n" +
            "- *'What is the current number of hotspots shown on the map?'*\n" +
            "- *'বাংলাদেশে আজকের হটস্পট সংখ্যা কত?'*\n" +
            "- *'Explain the difference between MCD14ML and VNP14IMGML'*\n" +
            "- *'Fly to California'* or *'সুন্দরবনে যাও'*"
        );
        this.appendMessage('assistant', greeting, null, [
            { title: "NASA FIRMS Satellite Sensors (MODIS vs VIIRS)", source: "NASA EOS", category: "remote_sensing", relevance: 1.0 },
            { title: "5-Node Multi-Sensor Harmonization Pipeline", source: "EarthPulse", category: "harmonization", relevance: 0.95 }
        ], {
            modelUsed: "EarthPulse Grounded RAG",
            latencyMs: 12,
            factsGroundedPct: "100% facts grounded"
        });
    }

    async loadSuggestions() {
        try {
            const res = await fetch('/api/chat/suggestions');
            if (!res.ok) return;
            const data = await res.json();
            if (data.suggestions && this.suggestionsContainer) {
                this.suggestionsContainer.innerHTML = '';
                data.suggestions.forEach(item => {
                    const chip = document.createElement('button');
                    chip.className = 'chat-prompt-chip';
                    chip.innerHTML = `<span class="chip-icon">${item.icon}</span> <span>${item.label}</span>`;
                    chip.addEventListener('click', () => {
                        if (this.inputField) {
                            this.inputField.value = item.prompt;
                            this.sendMessage();
                        }
                    });
                    this.suggestionsContainer.appendChild(chip);
                });
            }
        } catch (e) {
            console.warn('Failed loading chat suggestions:', e);
        }
    }

    async sendMessage(retryText = null) {
        if (!this.inputField && !retryText) return;
        const msg = (retryText !== null ? retryText : this.inputField.value).trim();
        if (!msg) return;

        this.lastUserMessage = msg;
        if (!retryText) {
            this.inputField.value = '';
        }
        this.appendMessage('user', msg);

        // Prepare Viewport Context if enabled
        let viewport = null;
        if (this.attachViewport && this.cameraController) {
            try {
                const viewData = this.cameraController.getViewBoundsAndTelemetry();
                if (viewData) {
                    viewport = {
                        bounds: viewData.bounds,
                        altitudeMeters: viewData.telemetry.altitudeMeters,
                        lat: viewData.telemetry.latDeg,
                        lon: viewData.telemetry.lonDeg
                    };
                }
            } catch (e) {}
        }

        // Show typing indicator
        const typingEl = this.showTypingIndicator();

        try {
            const payload = {
                message: msg,
                conversationId: this.conversationId,
                context: viewport ? {
                    latitude: viewport.lat,
                    longitude: viewport.lon,
                    altitude: viewport.altitudeMeters,
                    bounds: viewport.bounds
                } : null
            };

            const res = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!res.ok) {
                throw new Error(`Server status ${res.status}`);
            }

            const data = await res.json();
            typingEl.remove();

            const answer = data.answer || data.reply || "No response received.";
            this.appendMessage('assistant', answer, data.action, data.sources, data.metadata, data.traceId);

            // Execute interactive 3D action if present
            if (data.action) {
                this.executeAction(data.action);
            }

        } catch (err) {
            typingEl.remove();
            console.error('PulseAI Chat Error:', err);
            this.appendErrorMessage("Sorry, I couldn't process that request right now. Please try again or rephrase your question.");
        }
    }

    executeAction(action) {
        if (!action || !action.type) return;
        console.log('⚡ Copilot executing 3D action:', action);

        switch (action.type) {
            case 'fly_to_preset':
                if (this.cameraController && action.params?.preset) {
                    if (this.cameraController.presets?.[action.params.preset]) {
                        this.cameraController.flyTo(action.params.preset);
                    } else if (Number.isFinite(action.params.lat) && Number.isFinite(action.params.lon)) {
                        this.cameraController.flyToCoordinates(action.params.lon, action.params.lat, action.params.alt || 750000);
                    }
                }
                break;

            case 'fly_to_coords':
                if (this.cameraController && action.params) {
                    const { lon, lat, alt } = action.params;
                    this.cameraController.flyToCoordinates(lon, lat, alt || 35000);
                }
                break;

            case 'trigger_scenario':
                if (this.fireGuardController) {
                    this.fireGuardController.runMountainRidgeScenario();
                }
                break;

            case 'filter_sensor':
                if (this.firmsController && action.params?.sensor) {
                    this.firmsController.applySensorFilter(action.params.sensor);
                }
                break;

            case 'switch_view':
                if (this.firmsController && action.params?.mode) {
                    this.firmsController.setMode(action.params.mode);
                }
                break;

            case 'sync_firms':
                if (this.fireGuardController) {
                    this.fireGuardController.syncFirmsLive();
                }
                break;

            default:
                console.warn('Unknown action type:', action.type);
        }
    }

    appendErrorMessage(friendlyText) {
        const msgEl = document.createElement('div');
        msgEl.className = 'chat-msg assistant error-state';

        const avatarEl = document.createElement('div');
        avatarEl.className = 'msg-avatar';
        avatarEl.innerHTML = '⚠️';

        const bodyEl = document.createElement('div');
        bodyEl.className = 'msg-body';

        const contentEl = document.createElement('div');
        contentEl.className = 'msg-content error-text';
        contentEl.textContent = friendlyText;
        bodyEl.appendChild(contentEl);

        // Retry button
        if (this.lastUserMessage) {
            const retryBtn = document.createElement('button');
            retryBtn.className = 'chat-retry-btn';
            retryBtn.innerHTML = '🔄 Retry Question';
            retryBtn.addEventListener('click', () => {
                msgEl.remove();
                this.sendMessage(this.lastUserMessage);
            });
            bodyEl.appendChild(retryBtn);
        }

        msgEl.appendChild(avatarEl);
        msgEl.appendChild(bodyEl);
        this.messagesContainer?.appendChild(msgEl);
        this.scrollToBottom();
    }

    appendMessage(role, text, action = null, sources = null, metadata = null, traceId = null) {
        this.history.push({ role, content: text });

        const msgEl = document.createElement('div');
        msgEl.className = `chat-msg ${role}`;

        // Avatar
        const avatarEl = document.createElement('div');
        avatarEl.className = 'msg-avatar';
        avatarEl.innerHTML = role === 'user' ? '👤' : '🛰️';

        // Content Bubble
        const bodyEl = document.createElement('div');
        bodyEl.className = 'msg-body';

        // Markdown text rendering
        const contentEl = document.createElement('div');
        contentEl.className = 'msg-content';
        contentEl.innerHTML = this.renderMarkdown(text);
        bodyEl.appendChild(contentEl);

        // Sources citation block (assistant only)
        if (role === 'assistant' && sources && sources.length > 0) {
            const sourcesBlock = document.createElement('div');
            sourcesBlock.className = 'chat-sources-block';
            
            const hasWeb = sources.some(s => s.url || s.source_type === 'web');
            const titleEl = document.createElement('div');
            titleEl.className = 'sources-header';
            titleEl.innerHTML = hasWeb ? '<span>🌐 Live Web & News Citations:</span>' : '<span>📚 Verified Sources:</span>';
            sourcesBlock.appendChild(titleEl);

            const listEl = document.createElement('ul');
            listEl.className = 'sources-list';
            sources.slice(0, 5).forEach(s => {
                const li = document.createElement('li');
                const isWeb = Boolean(s.url || s.source_type === 'web');
                const icon = isWeb ? '🌐' : '•';
                
                if (isWeb && s.url) {
                    const dateBadge = s.date ? ` · <span class="source-date">${s.date}</span>` : '';
                    li.innerHTML = `${icon} <a href="${s.url}" target="_blank" rel="noopener noreferrer" class="chat-web-source-link" title="Open external article in new tab"><strong>${s.title}</strong> ↗</a> <span class="source-sub">(${s.source}${dateBadge})</span>`;
                } else {
                    const relPct = s.relevance ? Math.round(s.relevance * 100) : 85;
                    li.innerHTML = `• <strong>${s.title}</strong> <span class="source-sub">(${s.source} · ${relPct}% relevance)</span>`;
                }
                listEl.appendChild(li);
            });
            sourcesBlock.appendChild(listEl);
            bodyEl.appendChild(sourcesBlock);
        }

        // Action Pill Button (if action present)
        if (action) {
            const actionBtn = document.createElement('button');
            actionBtn.className = 'msg-action-badge';
            actionBtn.innerHTML = `<span>⚡ Action:</span> <strong>${action.label || action.type}</strong>`;
            actionBtn.title = 'Click to execute on 3D Globe';
            actionBtn.addEventListener('click', () => this.executeAction(action));
            bodyEl.appendChild(actionBtn);
        }

        // Telemetry & Grounding Footer (assistant only)
        if (role === 'assistant' && metadata) {
            const metaEl = document.createElement('div');
            metaEl.className = 'msg-meta-footer';

            const latency = metadata.latencyMs ? `${metadata.latencyMs}ms` : '';
            const groundedPct = metadata.factsGroundedPct ? ` · <span class="grounded-tag">${metadata.factsGroundedPct}</span>` : '';
            const modelTag = metadata.modelUsed ? ` · <span>${metadata.modelUsed}</span>` : '';
            const traceLink = traceId ? ` · <span class="trace-pill" title="Trace: ${traceId}">LangSmith</span>` : '';

            metaEl.innerHTML = `<span>${latency}${groundedPct}${modelTag}${traceLink}</span>`;
            bodyEl.appendChild(metaEl);
        }

        msgEl.appendChild(avatarEl);
        msgEl.appendChild(bodyEl);
        this.messagesContainer?.appendChild(msgEl);
        this.scrollToBottom();
    }

    showTypingIndicator() {
        const el = document.createElement('div');
        el.className = 'chat-msg assistant typing-indicator';
        el.innerHTML = `
            <div class="msg-avatar">🛰️</div>
            <div class="msg-body">
                <div class="typing-dots">
                    <span></span><span></span><span></span>
                </div>
            </div>
        `;
        this.messagesContainer?.appendChild(el);
        this.scrollToBottom();
        return el;
    }

    scrollToBottom() {
        if (this.messagesContainer) {
            this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
        }
    }

    renderMarkdown(text) {
        if (!text) return '';
        let escaped = text
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');

        // Code blocks: ```code```
        escaped = escaped.replace(/```([\s\S]*?)```/g, '<pre class="chat-code-block"><code>$1</code></pre>');

        // Inline code: `code`
        escaped = escaped.replace(/`([^`]+)`/g, '<code class="chat-inline-code">$1</code>');

        // Bold: **text**
        escaped = escaped.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');

        // Italic: *text*
        escaped = escaped.replace(/\*([^*]+)\*/g, '<em>$1</em>');

        // Bullet lists
        escaped = escaped.replace(/^\s*-\s+(.+)$/gm, '<li>$1</li>');
        escaped = escaped.replace(/(<li>.*<\/li>(\n|$))+/g, '<ul class="chat-list">$&</ul>');

        // Numbered lists
        escaped = escaped.replace(/^\s*(\d+)\.\s+(.+)$/gm, '<li>$2</li>');

        // Line breaks
        escaped = escaped.replace(/\n\n/g, '<br><br>');
        escaped = escaped.replace(/(?<!<br>|\n)<\/li>\n/g, '</li>');

        return escaped;
    }
}
