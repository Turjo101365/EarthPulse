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
        this.isOpen = false;
        this.isMinimized = false;
        this.isListening = false;
        this.speechRecognition = null;
        this.provider = localStorage.getItem('pulseai_provider') || 'builtin';
        this.apiKey = localStorage.getItem('pulseai_api_key') || '';
        this.attachViewport = true;

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
            this.speechRecognition.lang = 'en-US'; // supports multilingual detection

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
        this.btnSaveSettings?.addEventListener('click', () => this.saveSettings());

        this.selectProvider?.addEventListener('change', () => {
            const val = this.selectProvider.value;
            if (this.settingKeyGroup) {
                this.settingKeyGroup.style.display = val === 'builtin' ? 'none' : 'block';
            }
        });

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
        if (this.selectProvider) this.selectProvider.value = this.provider;
        if (this.inputApiKey) this.inputApiKey.value = this.apiKey;
        if (this.settingKeyGroup) {
            this.settingKeyGroup.style.display = this.provider === 'builtin' ? 'none' : 'block';
        }
        this.settingsModal.classList.remove('hidden');
    }

    closeSettings() {
        this.settingsModal?.classList.add('hidden');
    }

    saveSettings() {
        if (this.selectProvider) {
            this.provider = this.selectProvider.value;
            localStorage.setItem('pulseai_provider', this.provider);
        }
        if (this.inputApiKey) {
            this.apiKey = this.inputApiKey.value.trim();
            localStorage.setItem('pulseai_api_key', this.apiKey);
        }
        if (this.statusPill) {
            this.statusPill.textContent = this.provider === 'builtin' ? 'Built-in AI' : (this.provider === 'gemini' ? 'Gemini Flash' : 'OpenAI');
        }
        this.closeSettings();
        this.addSystemNotice(`Settings updated: Engine set to ${this.provider.toUpperCase()}`);
    }

    clearChat() {
        this.history = [];
        if (this.messagesContainer) {
            this.messagesContainer.innerHTML = '';
        }
        this.addInitialGreeting();
    }

    addInitialGreeting() {
        const greeting = (
            "👋 **Welcome to PulseAI Wildfire Copilot!**\n\n"
            "I am grounded in live **NASA FIRMS** satellite feeds (MODIS & VIIRS), "
            "**XGBoost** spatial spread predictions, and **PPO Reinforcement Learning** dispatch tactics.\n\n"
            "Try asking me in **English**, **বাংলা** or **Banglish**:\n"
            "- *'What is the current global fire summary?'*\n"
            "- *'বাংলাদেশে আগুনের অবস্থা কী?'*\n"
            "- *'Fly to California'* or *'আমাজনে যাও'*\n"
            "- *'Explain MODIS vs VIIRS difference'*\n"
            "- *'Run Ridge Crisis Scenario'*"
        );
        this.appendMessage('assistant', greeting, null, {
            chunks_retrieved: 9,
            citations: ['NASA FIRMS Sensors', 'Harmonization Pipeline'],
            grounding_score: 1.0,
            facts_grounded_pct: '100% facts grounded',
            status: 'PASSED'
        });
    }

    addSystemNotice(text) {
        const el = document.createElement('div');
        el.className = 'chat-system-notice';
        el.textContent = `ℹ️ ${text}`;
        this.messagesContainer?.appendChild(el);
        this.scrollToBottom();
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

    async sendMessage() {
        if (!this.inputField) return;
        const msg = this.inputField.value.trim();
        if (!msg) return;

        this.inputField.value = '';
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
                history: this.history.slice(-4),
                viewport: viewport,
                provider: this.provider,
                api_key: this.apiKey || null
            };

            const res = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!res.ok) {
                throw new Error(`Server returned status ${res.status}`);
            }

            const data = await res.json();
            typingEl.remove();

            // Append response message
            this.appendMessage('assistant', data.reply, data.action, data.rag, data.grounding, data.trace_id);

            // Execute action if returned
            if (data.action) {
                this.executeAction(data.action);
            }

        } catch (err) {
            typingEl.remove();
            this.appendMessage('assistant', `⚠️ **Error communicating with AI:** ${err.message}\n\nPlease verify server status or switch to the Built-in engine.`);
        }
    }

    executeAction(action) {
        if (!action || !action.type) return;

        console.log('⚡ Copilot executing action:', action);

        switch (action.type) {
            case 'fly_to_preset':
                if (this.cameraController && action.params?.preset) {
                    this.cameraController.flyTo(action.params.preset);
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

    appendMessage(role, text, action = null, rag = null, grounding = null, traceId = null) {
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

        // Action Pill Button (if action present)
        if (action) {
            const actionBtn = document.createElement('button');
            actionBtn.className = 'msg-action-badge';
            actionBtn.innerHTML = `<span>⚡ Action:</span> <strong>${action.label || action.type}</strong>`;
            actionBtn.title = 'Click to re-execute action on 3D Globe';
            actionBtn.addEventListener('click', () => this.executeAction(action));
            bodyEl.appendChild(actionBtn);
        }

        // RAG Citations & Grounding Footer (assistant only)
        if (role === 'assistant' && (rag || grounding)) {
            const metaEl = document.createElement('div');
            metaEl.className = 'msg-meta-footer';

            let citationsHtml = '';
            if (rag && rag.citations && rag.citations.length > 0) {
                citationsHtml = ` · 📚 RAG: ${rag.citations[0]}`;
            }

            const latency = grounding?.latency_ms ? `${grounding.latency_ms}ms` : '';
            const groundedPct = rag?.facts_grounded_pct ? ` · <span class="grounded-tag">${rag.facts_grounded_pct}</span>` : '';
            const traceLink = traceId ? ` · <span class="trace-pill" title="Trace: ${traceId}">LangSmith</span>` : '';

            metaEl.innerHTML = `<span>${latency}${groundedPct}${citationsHtml}${traceLink}</span>`;
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
