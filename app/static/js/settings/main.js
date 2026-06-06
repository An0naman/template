        // ---- Section Visibility Manager ----
        const SETTINGS_SECTIONS_KEY = 'settings_visible_sections';
        // Feature flags controlled by section visibility
        const sectionFeatureMap = {
            'section-sensors': 'enable_sensors',
            'section-kanban':  'enable_kanban',
            'section-git':     'git_integration_enabled',
            'section-strava':  'strava_enabled',
            'section-garmin-connect': 'garmin_enabled',
            'section-ntfy':    'ntfy_enabled',
            'section-anycubic': 'anycubic_enabled',
        };
        const settingsSectionDefs = [
            { id: 'section-ai',        label: 'AI Integration' },
            { id: 'section-sensors',   label: 'Sensor Functionality' },
            { id: 'section-kanban',    label: 'Kanban Boards' },
            { id: 'section-git',       label: 'Git Integration' },
            { id: 'section-strava',    label: 'Strava Integration' },
            { id: 'section-garmin-connect', label: 'Garmin Connect Integration' },
            { id: 'section-ntfy',      label: 'Push Notifications' },
            { id: 'section-anycubic',  label: 'Anycubic 3D Printer' },
            { id: 'section-labels',    label: 'Label Printing' },
            { id: 'section-scheduler', label: 'Scheduled Jobs' },
            { id: 'section-logo',      label: 'Project Logo' },
        ];

        function getVisibleSections() {
            try {
                const saved = localStorage.getItem(SETTINGS_SECTIONS_KEY);
                if (saved) return JSON.parse(saved);
            } catch(e) {}
            const defaults = {};
            settingsSectionDefs.forEach(s => defaults[s.id] = true);
            return defaults;
        }

        function applySectionVisibility() {
            const visible = getVisibleSections();
            settingsSectionDefs.forEach(s => {
                const el = document.querySelector('[data-section-id="' + s.id + '"]');
                if (el) el.style.display = (visible[s.id] !== false) ? '' : 'none';
            });

            applySchedulerPanelVisibility();
        }

        function applySchedulerPanelVisibility() {
            const visible = getVisibleSections();
            const selector = document.getElementById('scheduledJobType');
            const overduePanel = document.getElementById('schedulerPanelOverdue');
            const stravaPanel = document.getElementById('schedulerPanelStrava');
            const garminPanel = document.getElementById('schedulerPanelGarmin');
            if (!selector || !overduePanel || !stravaPanel || !garminPanel) return;

            const stravaVisible = (visible['section-strava'] !== false);
            const stravaOption = selector.querySelector('option[value="strava"]');
            if (stravaOption) {
                stravaOption.disabled = !stravaVisible;
                stravaOption.hidden = !stravaVisible;
            }

            const garminVisible = (visible['section-garmin-connect'] !== false);
            const garminOption = selector.querySelector('option[value="garmin"]');
            if (garminOption) {
                garminOption.disabled = !garminVisible;
                garminOption.hidden = !garminVisible;
            }

            if (!stravaVisible && selector.value === 'strava') {
                selector.value = 'overdue';
            }
            if (!garminVisible && selector.value === 'garmin') {
                selector.value = 'overdue';
            }

            overduePanel.style.display = selector.value === 'overdue' ? '' : 'none';
            stravaPanel.style.display = (selector.value === 'strava' && stravaVisible) ? '' : 'none';
            garminPanel.style.display = (selector.value === 'garmin' && garminVisible) ? '' : 'none';
        }

        function openSectionConfigModal() {
            const visible = getVisibleSections();
            settingsSectionDefs.forEach(s => {
                const cb = document.getElementById('toggle_' + s.id);
                if (cb) cb.checked = (visible[s.id] !== false);
            });
            new bootstrap.Modal(document.getElementById('sectionConfigModal')).show();
        }

        async function saveSystemParams(payload, method = 'PATCH') {
            return fetch('/api/system_params', {
                method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
        }

        async function runWithLoadingButton(button, loadingHtml, action) {
            if (!button) {
                return action();
            }
            const originalHtml = button.innerHTML;
            button.disabled = true;
            button.innerHTML = loadingHtml;
            try {
                return await action();
            } finally {
                button.disabled = false;
                button.innerHTML = originalHtml;
            }
        }

        async function saveSystemParamsWithStatus(statusId, payload, successMessage, failureMessage) {
            try {
                const response = await saveSystemParams(payload);
                if (response.ok) {
                    displayStatus(statusId, successMessage, 'alert-success');
                    return true;
                }
                displayStatus(statusId, failureMessage, 'alert-danger');
                return false;
            } catch (error) {
                displayStatus(statusId, '❌ Error: ' + error.message, 'alert-danger');
                return false;
            }
        }

        async function saveSectionConfig() {
            const visible = {};
            const featureUpdates = {};
            settingsSectionDefs.forEach(s => {
                const cb = document.getElementById('toggle_' + s.id);
                visible[s.id] = cb ? cb.checked : true;
                if (sectionFeatureMap[s.id]) {
                    featureUpdates[sectionFeatureMap[s.id]] = (cb && cb.checked) ? '1' : '0';
                }
            });
            localStorage.setItem(SETTINGS_SECTIONS_KEY, JSON.stringify(visible));
            applySectionVisibility();
            try {
                await saveSystemParams(featureUpdates);
            } catch(e) { console.error('Failed to save feature flags', e); }
            bootstrap.Modal.getInstance(document.getElementById('sectionConfigModal')).hide();
        }

        async function resetSectionConfig() {
            localStorage.removeItem(SETTINGS_SECTIONS_KEY);
            settingsSectionDefs.forEach(s => {
                const cb = document.getElementById('toggle_' + s.id);
                if (cb) cb.checked = true;
            });
            applySectionVisibility();
            // Re-enable all feature flags
            const featureUpdates = {};
            Object.values(sectionFeatureMap).forEach(p => featureUpdates[p] = '1');
            try {
                await saveSystemParams(featureUpdates);
            } catch(e) { console.error('Failed to reset feature flags', e); }
        }

        // Apply section visibility as soon as this script runs (DOM is ready — script is at end of body)
        applySectionVisibility();

        const scheduledJobTypeSelector = document.getElementById('scheduledJobType');
        if (scheduledJobTypeSelector) {
            scheduledJobTypeSelector.addEventListener('change', applySchedulerPanelVisibility);
        }

        // Helper function to display status messages
        function displayStatus(elementId, message, type) {
            const el = document.getElementById(elementId);
            if (el) {
                el.className = 'mt-3 alert ' + type;
                el.innerHTML = message;
                el.classList.remove('d-none');
                setTimeout(() => {
                    el.classList.add('d-none');
                }, 5000);
            }
        }

        // Toggle password visibility
        function togglePasswordVisibility(inputId, btn) {
            const input = document.getElementById(inputId);
            const icon = btn.querySelector('i');
            if (input.type === 'password') {
                input.type = 'text';
                icon.classList.remove('fa-eye');
                icon.classList.add('fa-eye-slash');
            } else {
                input.type = 'password';
                icon.classList.remove('fa-eye-slash');
                icon.classList.add('fa-eye');
            }
        }

        async function refreshAiServiceStatus() {
            const aiStatus = document.getElementById('aiServiceStatus');
            if (!aiStatus) return;

            aiStatus.innerHTML = '<span class="badge bg-secondary"><i class="fas fa-spinner fa-spin me-1"></i>Checking...</span>';

            try {
                const response = await fetch('/api/ai/status');
                const data = await response.json();

                if (response.ok && data.available) {
                    aiStatus.innerHTML = `<span class="badge bg-success"><i class="fas fa-check-circle me-1"></i>${data.service}</span>`;
                } else {
                    aiStatus.innerHTML = '<span class="badge bg-warning text-dark"><i class="fas fa-exclamation-triangle me-1"></i>Not Configured</span>';
                }
            } catch (error) {
                aiStatus.innerHTML = '<span class="badge bg-danger"><i class="fas fa-times-circle me-1"></i>Status Unavailable</span>';
            }
        }

        // Test AI Service
        async function testAiService() {
            const statusDiv = document.getElementById('aiStatusMessage');
            statusDiv.className = 'mt-3 alert alert-info';
            statusDiv.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Testing connection...';
            statusDiv.classList.remove('d-none');
            
            // Get selected service
            const serviceSelector = document.getElementById('aiServiceSelector');
            const service = serviceSelector ? serviceSelector.value : 'gemini';
            
            // Get current values based on service
            let apiKey = '';
            let modelName = '';
            let baseUrl = '';
            
            if (service === 'gemini') {
                apiKey = document.getElementById('geminiApiKey').value;
                modelName = document.getElementById('geminiModelName').value;
            } else if (service === 'ollama') {
                baseUrl = document.getElementById('ollamaBaseUrl').value;
                modelName = document.getElementById('ollamaModelName').value;
            }
            
            try {
                const response = await fetch('/api/ai/test_connection', { 
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        service: service,
                        api_key: apiKey,
                        base_url: baseUrl,
                        model_name: modelName
                    })
                });
                const data = await response.json();
                
                if (response.ok && data.success) {
                    statusDiv.className = 'mt-3 alert alert-success';
                    statusDiv.innerHTML = '<i class="fas fa-check-circle me-2"></i>Connection successful! Response: ' + (data.response || 'OK');
                } else {
                    statusDiv.className = 'mt-3 alert alert-danger';
                    statusDiv.innerHTML = '<i class="fas fa-times-circle me-2"></i>Connection failed: ' + (data.error || 'Unknown error');
                }
            } catch (error) {
                statusDiv.className = 'mt-3 alert alert-danger';
                statusDiv.innerHTML = '<i class="fas fa-times-circle me-2"></i>Error: ' + error.message;
            }
        }

        // Load Gemini Models
        async function loadGeminiModels() {
            const modelSelect = document.getElementById('geminiModelName');
            if (!modelSelect) return;
            
            try {
                // Use url_for to ensure correct path handling
                const modelsUrl = (window.SETTINGS_BOOTSTRAP && window.SETTINGS_BOOTSTRAP.urls && window.SETTINGS_BOOTSTRAP.urls.geminiModels) || '/api/ai/models';
                const response = await fetch(modelsUrl);
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                const text = await response.text();
                let data;
                try {
                    data = JSON.parse(text);
                } catch (e) {
                    console.error('Failed to parse JSON response:', text);
                    // Show the first 50 chars of the response in the dropdown to help debugging
                    const preview = text.substring(0, 50).replace(/</g, '&lt;').replace(/>/g, '&gt;');
                    modelSelect.innerHTML = `<option value="">Error: Server returned "${preview}..."</option>`;
                    return;
                }
                
                if (data.models && data.models.length > 0) {
                    modelSelect.innerHTML = '';
                    const currentModel = (window.SETTINGS_BOOTSTRAP && window.SETTINGS_BOOTSTRAP.defaults && window.SETTINGS_BOOTSTRAP.defaults.geminiModelName) || "";
                    let foundCurrent = false;
                    const options = [];
                    
                    data.models.forEach(model => {
                        const option = document.createElement('option');
                        option.value = model.id;
                        option.textContent = model.name;
                        option.title = model.description;
                        
                        if (model.id === currentModel) {
                            option.selected = true;
                            foundCurrent = true;
                        }
                        
                        modelSelect.appendChild(option);
                        options.push({option, model});
                    });
                    
                    if (!foundCurrent) {
                        // If current model not found (e.g. deprecated), select recommended
                        options.forEach(({option, model}) => {
                            if (model.recommended) {
                                option.selected = true;
                            }
                        });
                    }
                    
                    // Update description
                    modelSelect.addEventListener('change', function() {
                        const selectedOption = this.options[this.selectedIndex];
                        const descEl = document.getElementById('modelDescription');
                        if (descEl && selectedOption.title) {
                            descEl.textContent = selectedOption.title;
                        }
                    });
                    
                    // Trigger change to update description
                    modelSelect.dispatchEvent(new Event('change'));
                } else {
                    modelSelect.innerHTML = '<option value="">No models available</option>';
                }
            } catch (error) {
                console.error('Error loading Gemini models:', error);
                modelSelect.innerHTML = '<option value="">Error loading models</option>';
            }
        }

        window.loadOllamaModels = async function() {
            const modelSelect = document.getElementById('ollamaModelName');
            const baseUrlInput = document.getElementById('ollamaBaseUrl');
            const helpText = document.getElementById('ollamaModelHelp');
            if (!modelSelect || !baseUrlInput) return;

            const baseUrl = (baseUrlInput.value || '').trim();
            const configuredModel = (window.SETTINGS_BOOTSTRAP && window.SETTINGS_BOOTSTRAP.defaults && window.SETTINGS_BOOTSTRAP.defaults.ollamaModelName) || 'llama3.2:latest';
            const preferredModel = modelSelect.value || configuredModel;

            if (!baseUrl) {
                modelSelect.innerHTML = `<option value="${configuredModel}">${configuredModel}</option>`;
                if (helpText) helpText.textContent = 'Enter an Ollama URL to detect installed models.';
                return;
            }

            if (helpText) helpText.textContent = 'Detecting installed models...';

            try {
                const response = await fetch(`/api/ai/ollama/models?base_url=${encodeURIComponent(baseUrl)}`);
                const data = await response.json();

                if (!response.ok) {
                    throw new Error(data.error || `HTTP error ${response.status}`);
                }

                const models = Array.isArray(data.models) ? data.models : [];
                modelSelect.innerHTML = '';

                if (helpText && data.warning) {
                    helpText.textContent = data.warning;
                }

                if (!models.length) {
                    modelSelect.innerHTML = `<option value="${preferredModel}">${preferredModel}</option>`;
                    if (helpText) helpText.textContent = 'No models were reported by this Ollama server.';
                    return;
                }

                let foundPreferred = false;
                models.forEach(model => {
                    const modelId = model.id || model.name;
                    const option = document.createElement('option');
                    option.value = modelId;
                    option.textContent = model.name || modelId;

                    if (model.size) {
                        const approxGb = (Number(model.size) / (1024 ** 3)).toFixed(1);
                        option.title = `Approx. ${approxGb} GB`;
                    }

                    if (modelId === preferredModel) {
                        option.selected = true;
                        foundPreferred = true;
                    }

                    modelSelect.appendChild(option);
                });

                if (!foundPreferred && preferredModel) {
                    const option = document.createElement('option');
                    option.value = preferredModel;
                    option.textContent = `${preferredModel} (saved)`;
                    option.selected = true;
                    modelSelect.appendChild(option);
                }

                const apiStyleLabel = data.api_style === 'openai' ? 'OpenAI-compatible' : 'native Ollama';
                if (helpText) {
                    const count = models.length;
                    helpText.textContent = `Detected ${count} installed model${count === 1 ? '' : 's'} from the ${apiStyleLabel} endpoint.`;
                }
            } catch (error) {
                console.error('Error loading Ollama models:', error);
                modelSelect.innerHTML = `<option value="${preferredModel}">${preferredModel}</option>`;
                if (helpText) helpText.textContent = error.message || 'Unable to load Ollama models.';
            }
        };

        window.loadComfyImageModels = async function() {
            const modelSelect = document.getElementById('comfyModelName');
            const manualInput = document.getElementById('comfyModelNameManual');
            const icon = document.getElementById('comfyModelRefreshIcon');
            const helpText = document.getElementById('comfyModelHelp');
            const serverUrlInput = document.getElementById('comfyServerUrl');
            if (!modelSelect) return;

            const configuredModel = (window.SETTINGS_BOOTSTRAP && window.SETTINGS_BOOTSTRAP.defaults && window.SETTINGS_BOOTSTRAP.defaults.comfyModelName) || '';
            const preferred = (manualInput && manualInput.value.trim()) || modelSelect.value || configuredModel || '';

            if (icon) icon.classList.add('fa-spin');
            if (helpText) helpText.textContent = 'Fetching image models from ComfyUI…';

            try {
                const serverUrl = serverUrlInput ? serverUrlInput.value.trim() : '';
                const url = serverUrl
                    ? `/ollama/api/comfy-models?server_url=${encodeURIComponent(serverUrl)}`
                    : '/ollama/api/comfy-models';
                const resp = await fetch(url);
                const data = await resp.json();

                if (!resp.ok) throw new Error(data.error || `HTTP ${resp.status}`);

                const models = Array.isArray(data.models) ? data.models : [];
                modelSelect.innerHTML = '';

                if (!models.length) {
                    modelSelect.innerHTML = preferred
                        ? `<option value="${preferred}">${preferred}</option>`
                        : '<option value="">No models found \u2014 type filename manually below</option>';
                    if (helpText) helpText.textContent = 'ComfyUI reported no checkpoints in its default paths. Type the filename manually below.';
                    return;
                }

                let foundPreferred = false;
                models.forEach(m => {
                    const opt = document.createElement('option');
                    opt.value = m;
                    opt.textContent = m;
                    if (m === preferred) { opt.selected = true; foundPreferred = true; }
                    modelSelect.appendChild(opt);
                });

                if (!foundPreferred && preferred) {
                    const opt = document.createElement('option');
                    opt.value = preferred;
                    opt.textContent = `${preferred} (saved)`;
                    opt.selected = true;
                    modelSelect.appendChild(opt);
                }

                if (helpText) helpText.textContent = `Detected ${models.length} model${models.length === 1 ? '' : 's'}.`;
            } catch (err) {
                console.error('Error loading ComfyUI image models:', err);
                modelSelect.innerHTML = preferred
                    ? `<option value="${preferred}">${preferred}</option>`
                    : '<option value="">ComfyUI unreachable</option>';
                if (helpText) helpText.textContent = err.message || 'Unable to reach ComfyUI.';
            } finally {
                if (icon) icon.classList.remove('fa-spin');
            }
        };

        document.addEventListener('DOMContentLoaded', function() {
            // --- Initialization from Server Params ---
            const params = (window.SETTINGS_BOOTSTRAP && window.SETTINGS_BOOTSTRAP.params) || {};

            // --- General Settings ---
            const sensorMasterToggle = document.getElementById('enableSensorMasterControlToggle');
            const sensorMasterLabel = document.getElementById('sensorMasterControlToggleLabel');

            if (sensorMasterToggle) {
                sensorMasterToggle.checked = (params.enable_sensor_master_control === 'true' || params.enable_sensor_master_control === '1');
                sensorMasterLabel.textContent = sensorMasterToggle.checked ? 'Enabled' : 'Disabled';
                sensorMasterToggle.addEventListener('change', function() {
                    sensorMasterLabel.textContent = this.checked ? 'Enabled' : 'Disabled';
                });
            }

            // General Settings Form Submit
            const generalForm = document.getElementById('generalSettingsForm');
            if (generalForm) {
                generalForm.addEventListener('submit', async function(e) {
                    e.preventDefault();
                    const formData = {
                        project_name: document.getElementById('projectName').value,
                        project_subtitle: document.getElementById('projectSubtitle').value,
                        entry_singular_label: document.getElementById('entrySingularLabel').value,
                        entry_plural_label: document.getElementById('entryPluralLabel').value
                    };

                    await saveSystemParamsWithStatus(
                        'generalStatusMessage',
                        formData,
                        '✅ General settings saved successfully!',
                        '❌ Failed to save settings.'
                    );
                });
            }

            // --- AI Settings ---
            window.switchAiServiceSettings = function() {
                const selector = document.getElementById('aiServiceSelector');
                if (!selector) return;
                const service = selector.value;
                document.querySelectorAll('.ai-service-settings').forEach(el => el.style.display = 'none');
                const target = document.getElementById(service + 'Settings');
                if (target) target.style.display = 'block';

                if (service === 'ollama') {
                    loadOllamaModels();
                }
            };
            
            window.switchPromptEditor = function() {
                const selector = document.getElementById('promptSelector');
                if (!selector) return;
                const prompt = selector.value;
                document.querySelectorAll('.prompt-editor-section').forEach(el => el.style.display = 'none');
                const target = document.getElementById('promptEditor_' + prompt);
                if (target) target.style.display = 'block';
            };

            // Initialize AI Views
            if (document.getElementById('aiServiceSelector')) switchAiServiceSettings();
            if (document.getElementById('promptSelector')) switchPromptEditor();

            const primaryAiProvider = document.getElementById('primaryAiProvider');
            if (primaryAiProvider) {
                primaryAiProvider.addEventListener('change', function() {
                    const serviceSelector = document.getElementById('aiServiceSelector');
                    if (serviceSelector) {
                        serviceSelector.value = this.value;
                        switchAiServiceSettings();
                    }
                });
            }
            
            // Load provider model lists
            loadGeminiModels();
            refreshAiServiceStatus();

            const ollamaBaseUrl = document.getElementById('ollamaBaseUrl');
            if (ollamaBaseUrl) {
                ollamaBaseUrl.addEventListener('change', loadOllamaModels);
                ollamaBaseUrl.addEventListener('blur', loadOllamaModels);
            }

            // AI Form Submit
            const aiForm = document.getElementById('aiSettingsForm');
            if (aiForm) {
                aiForm.addEventListener('submit', async function(e) {
                    e.preventDefault();
                    
                    const formData = {};
                    const elements = aiForm.elements;
                    for (let i = 0; i < elements.length; i++) {
                        const el = elements[i];
                        if (el.id) {
                            if (el.id === 'primaryAiProvider') formData.primary_ai_provider = el.value;
                            else if (el.id === 'geminiApiKey') formData.gemini_api_key = el.value;
                            else if (el.id === 'geminiModelName') formData.gemini_model_name = el.value;
                            else if (el.id === 'ollamaBaseUrl') formData.ollama_base_url = el.value;
                            else if (el.id === 'ollamaModelName') formData.ollama_model_name = el.value;
                            else if (el.id === 'comfyServerUrl') formData.comfy_server_url = el.value;
                            else if (el.id === 'comfyTtsUrl') formData.comfy_tts_url = el.value;
                            else if (el.id === 'comfyModelName') {
                                // Prefer the manual text input if it has a value
                                const manual = document.getElementById('comfyModelNameManual');
                                formData.comfy_model_name = (manual && manual.value.trim()) ? manual.value.trim() : el.value;
                            }

                            else if (el.id === 'geminiBasePrompt') formData.gemini_base_prompt = el.value;
                            else if (el.id === 'promptDescription') formData.prompt_description = el.value;
                            else if (el.id === 'promptNote') formData.prompt_note = el.value;
                            else if (el.id === 'promptSql') formData.prompt_sql = el.value;
                            else if (el.id === 'promptTheme') formData.prompt_theme = el.value;
                            else if (el.id === 'promptChat') formData.prompt_chat = el.value;
                            else if (el.id === 'promptDiagram') formData.prompt_diagram = el.value;
                            else if (el.id === 'promptDiagramRules') formData.prompt_diagram_rules = el.value;
                            else if (el.id === 'promptSummary') formData.prompt_summary = el.value;
                        }
                    }

                    const saved = await saveSystemParamsWithStatus(
                        'aiStatusMessage',
                        formData,
                        '✅ AI settings saved successfully!',
                        '❌ Failed to save AI settings.'
                    );
                    if (saved) {
                        refreshAiServiceStatus();
                    }
                });
            }

            // --- Sensor Settings ---
            const saveSensorBtn = document.getElementById('saveSensorSettingsBtn');
            if (saveSensorBtn) {
                saveSensorBtn.addEventListener('click', async function() {
                    await saveSystemParamsWithStatus(
                        'sensorStatusMessage',
                        { enable_sensor_master_control: sensorMasterToggle && sensorMasterToggle.checked ? '1' : '0' },
                        '✅ Sensor settings saved!',
                        '❌ Failed to save sensor settings.'
                    );
                });
            }

            // --- ntfy Push Notifications ---
            refreshNtfyStatus();

            async function refreshNtfyStatus() {
                try {
                    const resp = await fetch('/api/ntfy/config');
                    const cfg = await resp.json();
                    const indicator = document.getElementById('ntfyStatusIndicator');
                    const text = document.getElementById('ntfyStatusText');
                    const testBtn = document.getElementById('ntfyTestBtn');
                    if (cfg.topic) {
                        indicator.style.background = '#198754';
                        text.textContent = 'Configured — server: ' + (cfg.server_url || 'https://ntfy.sh') + ', topic: ' + cfg.topic;
                        testBtn.disabled = false;
                    } else {
                        indicator.style.background = '#dc3545';
                        text.textContent = 'Not configured — save a topic to activate';
                        testBtn.disabled = true;
                    }
                    // Populate form fields (never reveal auth token)
                    document.getElementById('ntfyServerUrl').value = cfg.server_url || 'https://ntfy.sh';
                    document.getElementById('ntfyTopic').value = cfg.topic || '';
                } catch(e) {
                    document.getElementById('ntfyStatusText').textContent = 'Could not load status';
                }
            }
            window.refreshNtfyStatus = refreshNtfyStatus;

            window.sendNtfyTest = async function() {
                const btn = document.getElementById('ntfyTestBtn');
                const origHtml = btn.innerHTML;
                btn.disabled = true;
                btn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Sending...';
                try {
                    const resp = await fetch('/api/ntfy/test', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ title: 'Test Notification', message: 'Push notifications are working! 🎉', priority: 3 })
                    });
                    const result = await resp.json();
                    if (result.success) {
                        displayStatus('ntfySettingsStatus', '✅ Test notification sent — check your device!', 'alert-success');
                    } else {
                        displayStatus('ntfySettingsStatus', '❌ ' + (result.error || 'Test failed'), 'alert-danger');
                    }
                } catch(e) {
                    displayStatus('ntfySettingsStatus', '❌ Error: ' + e.message, 'alert-danger');
                } finally {
                    btn.innerHTML = origHtml;
                    btn.disabled = false;
                }
            };

            const ntfyForm = document.getElementById('ntfySettingsForm');
            if (ntfyForm) {
                ntfyForm.addEventListener('submit', async function(e) {
                    e.preventDefault();
                    const btn = ntfyForm.querySelector('[type=submit]');
                    const origHtml = btn.innerHTML;
                    btn.disabled = true;
                    btn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Saving...';
                    try {
                        const resp = await fetch('/api/ntfy/config', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                server_url: document.getElementById('ntfyServerUrl').value.trim(),
                                topic: document.getElementById('ntfyTopic').value.trim(),
                                auth_token: document.getElementById('ntfyAuthToken').value.trim()
                            })
                        });
                        if (resp.ok) {
                            displayStatus('ntfySettingsStatus', '✅ ntfy configuration saved!', 'alert-success');
                            refreshNtfyStatus();
                        } else {
                            const err = await resp.json();
                            displayStatus('ntfySettingsStatus', '❌ ' + (err.error || 'Failed to save'), 'alert-danger');
                        }
                    } catch(e) {
                        displayStatus('ntfySettingsStatus', '❌ Error: ' + e.message, 'alert-danger');
                    } finally {
                        btn.disabled = false;
                        btn.innerHTML = origHtml;
                    }
                });
            }

            // --- Git Integration ---
            const gitToggle = null; // removed — section visibility = enabled state
            const gitConfig = document.getElementById('gitConfigSection');
            const gitProvider = document.getElementById('gitProvider');
            const gitlabUrlSection = document.getElementById('gitlabUrlSection');
            
            if (gitProvider) {
                gitProvider.value = params.git_provider || '';
                if (gitlabUrlSection) gitlabUrlSection.style.display = (params.git_provider === 'gitlab') ? 'block' : 'none';
                
                gitProvider.addEventListener('change', function() {
                    if (gitlabUrlSection) gitlabUrlSection.style.display = this.value === 'gitlab' ? 'block' : 'none';
                });
            }
            
            if (document.getElementById('gitlabUrl')) document.getElementById('gitlabUrl').value = params.gitlab_url || '';
            if (document.getElementById('gitToken')) document.getElementById('gitToken').value = params.git_token || '';

            const saveGitBtn = document.getElementById('saveGitConfigBtn');
            if (saveGitBtn) {
                saveGitBtn.addEventListener('click', async function() {
                    const data = {
                        git_integration_enabled: '1',
                        git_provider: gitProvider.value,
                        gitlab_url: document.getElementById('gitlabUrl').value,
                        git_token: document.getElementById('gitToken').value
                    };

                    const saved = await saveSystemParamsWithStatus(
                        'gitSettingsStatus',
                        data,
                        '✅ Git configuration saved!',
                        '❌ Failed to save Git config.'
                    );
                    if (saved) {
                        const discoverBtn = document.getElementById('discoverReposBtn');
                        if (discoverBtn) discoverBtn.disabled = false;
                    }
                });
            }
            
            // --- Anycubic 3D Printer ---
            (function() {
                const apiTypeSelect    = document.getElementById('anycubicApiType');
                const apiKeySection    = document.getElementById('anycubicApiKeySection');
                const networkSection   = document.getElementById('anycubicNetworkSection');
                const connStatusEl     = document.getElementById('anycubicConnectionStatus');
                const settingsStatusEl = document.getElementById('anycubicSettingsStatus');
                const ingestStatusEl   = document.getElementById('anycubicIngestStatus');

                function showAnycubicStatus(el, msg, cls) {
                    if (!el) return;
                    el.className = 'mt-3 alert ' + cls;
                    el.textContent = msg;
                    el.classList.remove('d-none');
                    setTimeout(() => el.classList.add('d-none'), 6000);
                }

                function updateApiTypeVisibility() {
                    if (!apiTypeSelect) return;
                    const isManual = apiTypeSelect.value === 'manual';
                    const isOcto   = apiTypeSelect.value === 'octoprint';
                    if (networkSection) networkSection.style.display = isManual ? 'none' : '';
                    if (apiKeySection)  apiKeySection.style.display  = isOcto   ? ''     : 'none';
                }

                if (apiTypeSelect) {
                    apiTypeSelect.addEventListener('change', updateApiTypeVisibility);
                    updateApiTypeVisibility();
                }

                const toggleApiKeyBtn = document.getElementById('toggleAnycubicApiKeyVisibility');
                if (toggleApiKeyBtn) {
                    toggleApiKeyBtn.addEventListener('click', function() {
                        const inp = document.getElementById('anycubicApiKey');
                        if (!inp) return;
                        const show = inp.type === 'password';
                        inp.type = show ? 'text' : 'password';
                        this.querySelector('i').className = show ? 'fas fa-eye-slash' : 'fas fa-eye';
                    });
                }

                const testBtn = document.getElementById('anycubicTestConnectionBtn');
                if (testBtn) {
                    testBtn.addEventListener('click', async function() {
                        const ip      = document.getElementById('anycubicPrinterIp')?.value.trim();
                        const port    = document.getElementById('anycubicPrinterPort')?.value.trim() || '80';
                        const apiType = apiTypeSelect?.value || 'kobra2_local';
                        const apiKey  = document.getElementById('anycubicApiKey')?.value.trim() || '';
                        if (!ip) { showAnycubicStatus(connStatusEl, 'Enter an IP address first.', 'alert-warning'); return; }
                        testBtn.disabled = true;
                        testBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Testing\u2026';
                        try {
                            const resp = await fetch('/api/anycubic/test_connection', {
                                method: 'POST',
                                headers: {'Content-Type': 'application/json'},
                                body: JSON.stringify({api_type: apiType, ip, port, api_key: apiKey})
                            });
                            const data = await resp.json();
                            showAnycubicStatus(connStatusEl, (data.success ? '\u2705 ' : '\u274c ') + data.message,
                                               data.success ? 'alert-success' : 'alert-danger');
                        } catch(e) {
                            showAnycubicStatus(connStatusEl, '\u274c ' + e.message, 'alert-danger');
                        } finally {
                            testBtn.disabled = false;
                            testBtn.innerHTML = '<i class="fas fa-plug me-1"></i>Test';
                        }
                    });
                }

                const settingsForm = document.getElementById('anycubicSettingsForm');
                if (settingsForm) {
                    settingsForm.addEventListener('submit', async function(e) {
                        e.preventDefault();
                        const payload = {
                            anycubic_enabled:             'true',
                            anycubic_printer_model:       document.getElementById('anycubicPrinterModel')?.value || '',
                            anycubic_api_type:            apiTypeSelect?.value || 'kobra2_local',
                            anycubic_printer_ip:          document.getElementById('anycubicPrinterIp')?.value.trim() || '',
                            anycubic_printer_port:        document.getElementById('anycubicPrinterPort')?.value.trim() || '80',
                            anycubic_api_key:             document.getElementById('anycubicApiKey')?.value.trim() || '',
                            anycubic_polling_enabled:     document.getElementById('anycubicPollingEnabled')?.checked ? 'true' : 'false',
                            anycubic_polling_interval:    document.getElementById('anycubicPollingInterval')?.value || '30',
                            anycubic_auto_create_entries: document.getElementById('anycubicAutoCreateEntries')?.checked ? 'true' : 'false',
                            anycubic_fetch_file:           document.getElementById('anycubicFetchFile')?.checked ? 'true' : 'false',
                            anycubic_entry_type_id:       document.getElementById('anycubicEntryTypeId')?.value || '',
                        };
                        try {
                            const resp = await saveSystemParams(payload, 'POST');
                            const data = await resp.json();
                            showAnycubicStatus(settingsStatusEl,
                                resp.ok ? '\u2705 Anycubic settings saved.' : '\u274c ' + (data.error || 'Save failed.'),
                                resp.ok ? 'alert-success' : 'alert-danger');
                            const pollBtn = document.getElementById('anycubicPollNowBtn');
                            if (pollBtn) pollBtn.disabled = false;
                        } catch(e) {
                            showAnycubicStatus(settingsStatusEl, '\u274c ' + e.message, 'alert-danger');
                        }
                    });
                }

                const pollBtn = document.getElementById('anycubicPollNowBtn');
                if (pollBtn) {
                    pollBtn.addEventListener('click', async function() {
                        pollBtn.disabled = true;
                        pollBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Polling\u2026';
                        try {
                            const resp = await fetch('/api/anycubic/status');
                            const data = await resp.json();
                            if (data.success) {
                                const s = data.status;
                                const msg = 'State: ' + s.state + ' | File: ' + (s.file_name || '\u2014') +
                                    ' | Progress: ' + s.progress + '% | Hotend: ' + s.hotend_temp + '\u00b0C/' + s.hotend_target +
                                    '\u00b0C | Bed: ' + s.bed_temp + '\u00b0C/' + s.bed_target + '\u00b0C';
                                showAnycubicStatus(settingsStatusEl, msg, 'alert-info');
                            } else {
                                showAnycubicStatus(settingsStatusEl, '\u274c ' + data.message, 'alert-danger');
                            }
                        } catch(e) {
                            showAnycubicStatus(settingsStatusEl, '\u274c ' + e.message, 'alert-danger');
                        } finally {
                            pollBtn.disabled = false;
                            pollBtn.innerHTML = '<i class="fas fa-sync me-1"></i>Poll Printer Now';
                        }
                    });
                }

                const manualIngestForm = document.getElementById('anycubicManualIngestForm');
                if (manualIngestForm) {
                    manualIngestForm.addEventListener('submit', async function(e) {
                        e.preventDefault();
                        const fileName    = document.getElementById('manualFileName')?.value.trim();
                        const durationMin = parseFloat(document.getElementById('manualDuration')?.value || '0');
                        const filamentMm  = parseFloat(document.getElementById('manualFilament')?.value || '0');
                        const notes       = document.getElementById('manualNotes')?.value.trim() || '';
                        const fetchFile   = document.getElementById('manualFetchFile')?.checked || false;
                        const entryTypeId = document.getElementById('anycubicEntryTypeId')?.value;
                        if (!fileName) { showAnycubicStatus(ingestStatusEl, 'File/model name is required.', 'alert-warning'); return; }
                        if (!entryTypeId) { showAnycubicStatus(ingestStatusEl, 'Select an entry type above before logging a print job.', 'alert-warning'); return; }
                        try {
                            const resp = await fetch('/api/anycubic/ingest', {
                                method: 'POST',
                                headers: {'Content-Type': 'application/json'},
                                body: JSON.stringify({
                                    file_name: fileName,
                                    duration_seconds: Math.round(durationMin * 60),
                                    filament_used_mm: filamentMm,
                                    notes,
                                    entry_type_id: entryTypeId,
                                    fetch_file: fetchFile
                                })
                            });
                            const data = await resp.json();
                            if (data.success) {
                                showAnycubicStatus(ingestStatusEl, '\u2705 ' + data.message, 'alert-success');
                                manualIngestForm.reset();
                            } else {
                                showAnycubicStatus(ingestStatusEl, '\u274c ' + (data.message || 'Ingest failed.'), 'alert-danger');
                            }
                        } catch(e) {
                            showAnycubicStatus(ingestStatusEl, '\u274c ' + e.message, 'alert-danger');
                        }
                    });
                }

                // ── Field Mapping UI ──────────────────────────────────────────────────
                let _printerFields = [];
                let _customColumns = [];
                let _currentMapping = {};

                async function loadAnycubicMappingData() {
                    const [fieldsResp, mappingResp, colsResp] = await Promise.all([
                        fetch('/api/anycubic/fields'),
                        fetch('/api/anycubic/field_mapping'),
                        fetch('/api/custom-columns'),
                    ]);
                    const fieldsData  = await fieldsResp.json();
                    const mappingData = await mappingResp.json();
                    const colsData    = await colsResp.json();
                    _printerFields  = fieldsData.fields || [];
                    _currentMapping = mappingData.mapping || {};
                    _customColumns  = Array.isArray(colsData) ? colsData : (colsData.columns || colsData.data || []);
                    renderMappingTable();
                }

                function renderMappingTable() {
                    const tbody = document.getElementById('anycubicMappingRows');
                    const table = document.getElementById('anycubicMappingTable');
                    const placeholder = document.getElementById('anycubicMappingPlaceholder');
                    if (!tbody) return;
                    tbody.innerHTML = '';
                    _printerFields.forEach(field => {
                        const selectedId = _currentMapping[field.key] || '';
                        const options = _customColumns.map(col =>
                            `<option value="${col.id}" ${col.id == selectedId ? 'selected' : ''}>${col.label || col.name}</option>`
                        ).join('');
                        const tr = document.createElement('tr');
                        tr.innerHTML = `
                            <td><span class="badge bg-secondary">${field.group}</span></td>
                            <td>${field.label}<br><small class="text-muted font-monospace">${field.key}</small></td>
                            <td>
                                <select class="form-select form-select-sm anycubic-col-select" data-field="${field.key}">
                                    <option value="">— not mapped —</option>
                                    ${options}
                                </select>
                            </td>`;
                        tbody.appendChild(tr);
                    });
                    if (table) table.classList.remove('d-none');
                    if (placeholder) placeholder.classList.add('d-none');
                }

                const loadMappingBtn = document.getElementById('anycubicLoadMappingBtn');
                if (loadMappingBtn) {
                    loadMappingBtn.addEventListener('click', async function() {
                        this.disabled = true;
                        this.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>';
                        try { await loadAnycubicMappingData(); }
                        catch(e) {
                            const el = document.getElementById('anycubicMappingStatus');
                            if (el) { el.className = 'alert alert-danger'; el.textContent = 'Failed to load mapping data: ' + e.message; el.classList.remove('d-none'); }
                        } finally {
                            this.disabled = false;
                            this.innerHTML = '<i class="fas fa-sync-alt me-1"></i>Load';
                        }
                    });
                }

                const saveMappingBtn = document.getElementById('anycubicSaveMappingBtn');
                if (saveMappingBtn) {
                    saveMappingBtn.addEventListener('click', async function() {
                        const rows = document.querySelectorAll('.anycubic-col-select');
                        const mapping = {};
                        rows.forEach(sel => { if (sel.value) mapping[sel.dataset.field] = parseInt(sel.value); });
                        this.disabled = true;
                        this.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Saving\u2026';
                        try {
                            const resp = await fetch('/api/anycubic/field_mapping', {
                                method: 'POST',
                                headers: {'Content-Type': 'application/json'},
                                body: JSON.stringify({mapping})
                            });
                            const data = await resp.json();
                            const el = document.getElementById('anycubicMappingStatus');
                            if (el) {
                                el.className = 'alert ' + (data.success ? 'alert-success' : 'alert-danger');
                                el.textContent = data.success ? '\u2705 Mapping saved.' : '\u274c Save failed.';
                                el.classList.remove('d-none');
                                setTimeout(() => el.classList.add('d-none'), 4000);
                            }
                            if (data.success) _currentMapping = data.mapping;
                        } catch (e) {
                            showAnycubicStatus(settingsStatusEl, '\u274c ' + e.message, 'alert-danger');
                        } finally {
                            this.disabled = false;
                            this.innerHTML = '<i class="fas fa-save me-1"></i>Save mapping';
                        }
                    });
                }

                const autoColumnsBtn = document.getElementById('anycubicAutoColumnsBtn');
                if (autoColumnsBtn) {
                    autoColumnsBtn.addEventListener('click', async function() {
                        const entryTypeId = document.getElementById('anycubicEntryTypeId')?.value;
                        if (!entryTypeId) {
                            showAnycubicStatus(settingsStatusEl, 'Select an entry type above first.', 'alert-warning');
                            return;
                        }
                        if (!confirm('This will create custom columns for every printer field and assign them to the selected entry type. Continue?')) return;
                        this.disabled = true;
                        this.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Creating\u2026';
                        try {
                            const resp = await fetch('/api/anycubic/auto_create_columns', {
                                method: 'POST',
                                headers: {'Content-Type': 'application/json'},
                                body: JSON.stringify({entry_type_id: entryTypeId})
                            });
                            let data;
                            const ct = resp.headers.get('content-type') || '';
                            if (ct.includes('application/json')) {
                                data = await resp.json();
                            } else {
                                const text = await resp.text();
                                throw new Error(`Server error (${resp.status}): ${text.substring(0,200)}`);
                            }
                            const el = document.getElementById('anycubicMappingStatus');
                            if (el) {
                                el.className = 'alert ' + (data.success ? 'alert-success' : 'alert-danger');
                                el.textContent = data.success ? '\u2705 ' + data.message : '\u274c ' + data.message;
                                el.classList.remove('d-none');
                            }
                            if (data.success) {
                                _currentMapping = data.mapping;
                                await loadAnycubicMappingData();
                            }
                        } catch (e) {
                            showAnycubicStatus(settingsStatusEl, '\u274c ' + e.message, 'alert-danger');
                        } finally {
                            this.disabled = false;
                            this.innerHTML = '<i class="fas fa-magic me-1"></i>Auto-create all columns';
                        }
                    });
                }
            })();


            // --- Scheduled Jobs ---
            async function saveSchedulerSettings(statusElementId, payload, successMessage, failureMessage) {
                try {
                    const response = await saveSystemParams(payload);
                    if (response.ok) {
                        displayStatus(statusElementId, successMessage, 'alert-success');
                    } else {
                        displayStatus(statusElementId, failureMessage, 'alert-danger');
                    }
                } catch (error) {
                    displayStatus(statusElementId, '❌ Error: ' + error.message, 'alert-danger');
                }
            }

            const overdueForm = document.getElementById('overdueSettingsForm');
            if (overdueForm) {
                overdueForm.addEventListener('submit', async function(e) {
                    e.preventDefault();
                    const enabled = document.getElementById('overdueCheckEnabled').checked;
                    const schedule = document.getElementById('overdueCheckSchedule').value;

                    await saveSchedulerSettings(
                        'overdueStatusMessage',
                        {
                            overdue_check_enabled: enabled ? '1' : '0',
                            overdue_check_schedule: schedule
                        },
                        '✅ Scheduled job settings saved!',
                        '❌ Failed to save settings.'
                    );
                });
            }
            
            const testOverdueBtn = document.getElementById('testOverdueCheck');
            if (testOverdueBtn) {
                testOverdueBtn.addEventListener('click', async function() {
                    try {
                        const response = await fetch('/api/jobs/run/overdue_check', { method: 'POST' });
                        const data = await response.json();
                        if (response.ok) {
                            displayStatus('overdueStatusMessage', '✅ Job triggered successfully: ' + data.message, 'alert-success');
                        } else {
                            displayStatus('overdueStatusMessage', '❌ Job failed: ' + data.error, 'alert-danger');
                        }
                    } catch (error) {
                        displayStatus('overdueStatusMessage', '❌ Error: ' + error.message, 'alert-danger');
                    }
                });
            }

            const stravaScheduledSyncForm = document.getElementById('stravaScheduledSyncForm');
            if (stravaScheduledSyncForm) {
                stravaScheduledSyncForm.addEventListener('submit', async function(e) {
                    e.preventDefault();
                    const enabled = document.getElementById('stravaSyncEnabled').checked;
                    const schedule = document.getElementById('stravaSyncSchedule').value;

                    await saveSchedulerSettings(
                        'stravaSyncStatusMessage',
                        {
                            strava_sync_enabled: enabled ? '1' : '0',
                            strava_sync_schedule: schedule
                        },
                        '✅ Strava sync job settings saved!',
                        '❌ Failed to save Strava sync job settings.'
                    );
                });
            }

            const clearStravaLastSyncBtn = document.getElementById('clearStravaLastSync');
            if (clearStravaLastSyncBtn) {
                clearStravaLastSyncBtn.addEventListener('click', async function() {
                    try {
                        const response = await fetch('/strava/clear_last_sync', { method: 'POST' });
                        const data = await response.json();
                        if (response.ok) {
                            document.getElementById('stravaLastSyncLabel').textContent = 'Last synced: Not synced yet';
                            displayStatus('stravaSyncStatusMessage', '✅ ' + data.message, 'alert-success');
                        } else {
                            displayStatus('stravaSyncStatusMessage', '❌ ' + (data.message || 'Failed to clear.'), 'alert-danger');
                        }
                    } catch (error) {
                        displayStatus('stravaSyncStatusMessage', '❌ Error: ' + error.message, 'alert-danger');
                    }
                });
            }

            const testStravaSyncNowBtn = document.getElementById('testStravaSyncNow');
            if (testStravaSyncNowBtn) {
                testStravaSyncNowBtn.addEventListener('click', async function() {
                    try {
                        const response = await fetch('/strava/sync', { method: 'POST' });
                        const data = await response.json();
                        if (response.ok) {
                            const msg = data && data.message ? data.message : 'Sync completed.';
                            displayStatus('stravaSyncStatusMessage', '✅ Strava sync triggered: ' + msg, 'alert-success');
                        } else {
                            const msg = data && data.message ? data.message : (data && data.error ? data.error : 'Unknown error');
                            displayStatus('stravaSyncStatusMessage', '❌ Strava sync failed: ' + msg, 'alert-danger');
                        }
                    } catch (error) {
                        displayStatus('stravaSyncStatusMessage', '❌ Error: ' + error.message, 'alert-danger');
                    }
                });
            }

            const garminScheduledSyncForm = document.getElementById('garminScheduledSyncForm');
            if (garminScheduledSyncForm) {
                garminScheduledSyncForm.addEventListener('submit', async function(e) {
                    e.preventDefault();
                    const enabled = document.getElementById('garminSyncEnabled').checked;
                    const schedule = document.getElementById('garminSyncSchedule').value;

                    await saveSchedulerSettings(
                        'garminSyncStatusMessage',
                        {
                            garmin_sync_enabled: enabled ? '1' : '0',
                            garmin_sync_schedule: schedule
                        },
                        '✅ Garmin sync job settings saved!',
                        '❌ Failed to save Garmin sync job settings.'
                    );
                });
            }

            async function clearGarminLastSync(statusId) {
                try {
                    const response = await fetch('/garmin/clear_last_sync', { method: 'POST' });
                    const data = await response.json();
                    if (response.ok) {
                        const scheduledLabel = document.getElementById('garminScheduledLastSyncLabel');
                        if (scheduledLabel) scheduledLabel.textContent = 'Last synced: Not synced yet';
                        const settingsLabel = document.getElementById('garminLastSyncLabel');
                        if (settingsLabel) settingsLabel.textContent = 'Last synced: Not synced yet';
                        displayStatus(statusId, '✅ ' + data.message, 'alert-success');
                    } else {
                        displayStatus(statusId, '❌ ' + (data.message || 'Failed to clear.'), 'alert-danger');
                    }
                } catch (error) {
                    displayStatus(statusId, '❌ Error: ' + error.message, 'alert-danger');
                }
            }

            const clearGarminLastSyncScheduledBtn = document.getElementById('clearGarminLastSyncScheduledBtn');
            if (clearGarminLastSyncScheduledBtn) {
                clearGarminLastSyncScheduledBtn.addEventListener('click', async function() {
                    await clearGarminLastSync('garminSyncStatusMessage');
                });
            }

            const testGarminSyncNowBtn = document.getElementById('testGarminSyncNow');
            if (testGarminSyncNowBtn) {
                testGarminSyncNowBtn.addEventListener('click', async function() {
                    try {
                        const response = await fetch('/garmin/sync', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({}) });
                        const data = await response.json();
                        if (response.ok && data.status === 'success') {
                            displayStatus('garminSyncStatusMessage', '✅ Garmin sync triggered: ' + (data.message || 'Done.'), 'alert-success');
                            setTimeout(() => location.reload(), 900);
                        } else if (response.ok && data.status === 'warning') {
                            displayStatus('garminSyncStatusMessage', '⚠️ ' + data.message, 'alert-warning');
                        } else {
                            displayStatus('garminSyncStatusMessage', '❌ Garmin sync failed: ' + (data.message || 'Unknown error'), 'alert-danger');
                        }
                    } catch (error) {
                        displayStatus('garminSyncStatusMessage', '❌ Error: ' + error.message, 'alert-danger');
                    }
                });
            }

            // --- Project Logo ---
            const logoForm = document.getElementById('logoUploadForm');
            if (logoForm) {
                logoForm.addEventListener('submit', async function(e) {
                    e.preventDefault();
                    const fileInput = document.getElementById('logoFile');
                    if (!fileInput.files.length) {
                        displayStatus('logoStatusMessage', '⚠️ Please select a file first.', 'alert-warning');
                        return;
                    }
                    
                    const formData = new FormData();
                    formData.append('logo', fileInput.files[0]);
                    
                    try {
                        const response = await fetch('/api/system_params/logo', {
                            method: 'POST',
                            body: formData
                        });
                        if (response.ok) {
                            displayStatus('logoStatusMessage', '✅ Logo uploaded successfully! Refreshing...', 'alert-success');
                            setTimeout(() => location.reload(), 1500);
                        } else {
                            const data = await response.json();
                            displayStatus('logoStatusMessage', '❌ Upload failed: ' + data.error, 'alert-danger');
                        }
                    } catch (error) {
                        displayStatus('logoStatusMessage', '❌ Error: ' + error.message, 'alert-danger');
                    }
                });
            }
            
            const removeLogoBtn = document.getElementById('removeLogo');
            if (removeLogoBtn) {
                removeLogoBtn.addEventListener('click', async function() {
                    if (!confirm('Are you sure you want to remove the project logo?')) return;
                    
                    try {
                        const response = await fetch('/api/system_params/logo', { method: 'DELETE' });
                        if (response.ok) {
                            displayStatus('logoStatusMessage', '✅ Logo removed. Refreshing...', 'alert-success');
                            setTimeout(() => location.reload(), 1500);
                        } else {
                            displayStatus('logoStatusMessage', '❌ Failed to remove logo.', 'alert-danger');
                        }
                    } catch (error) {
                        displayStatus('logoStatusMessage', '❌ Error: ' + error.message, 'alert-danger');
                    }
                });
            }

            // --- Strava Sync ---
            const syncStravaBtn = document.getElementById('syncStravaBtn');
            if (syncStravaBtn) {
                syncStravaBtn.addEventListener('click', async function() {
                    const originalText = this.innerHTML;
                    this.disabled = true;
                    this.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Syncing...';

                    try {
                        const response = await fetch('/strava/sync', { method: 'POST' });
                        const data = await response.json();

                        if (response.ok && data.status === 'success') {
                            alert('Sync Complete: ' + data.message);
                            location.reload();
                        } else if (data.status === 'skipped') {
                            alert('Sync Skipped: ' + data.message);
                        } else {
                            alert('Sync Failed: ' + data.message);
                        }
                    } catch (error) {
                        alert('Error syncing with Strava: ' + error.message);
                    } finally {
                        this.disabled = false;
                        this.innerHTML = originalText;
                    }
                });
            }
        });
