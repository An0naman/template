'use strict';

    if (!window.SETTINGS_BOOTSTRAP) {
        const bootstrapDataEl = document.getElementById('settings-bootstrap-data');
        if (bootstrapDataEl) {
            try {
                window.SETTINGS_BOOTSTRAP = JSON.parse(bootstrapDataEl.textContent || '{}');
            } catch (error) {
                console.warn('Failed to parse settings bootstrap data:', error);
                window.SETTINGS_BOOTSTRAP = {};
            }
        } else {
            window.SETTINGS_BOOTSTRAP = {};
        }
    }

document.addEventListener('DOMContentLoaded', function() {
                console.log("Settings page script loaded");
                
                const stravaSettingsForm = document.getElementById('stravaSettingsForm');
                const stravaMappingTable = document.getElementById('stravaMappingTable');
                const commonStravaTypes = ['Run', 'Ride', 'Swim', 'Walk', 'Hike', 'Workout', 'WeightTraining', 'Yoga', 'VirtualRide', 'VirtualRun', 'AlpineSki', 'Snowboard'];
                
                // Load Data
                let entryTypes = [];
                let currentMapping = {};
                
                try {
                    const entryTypesEl = document.getElementById('strava-entry-types-data');
                    if (entryTypesEl) {
                        entryTypes = JSON.parse(entryTypesEl.textContent);
                    }
                    
                    const mappingEl = document.getElementById('strava-mapping-data');
                    if (mappingEl) {
                        let rawContent = mappingEl.textContent.trim();
                        if (!rawContent) rawContent = "{}";
                        
                        // Handle potential single quotes from Python dict string representation
                        // If the string starts with { and contains single quotes, it might be a Python dict string
                        if (rawContent.startsWith('{') && rawContent.includes("'")) {
                            // Replace single quotes with double quotes for valid JSON
                            // This is a simple heuristic and might need refinement for complex strings
                            rawContent = rawContent.replace(/'/g, '"');
                        }

                        // Try to parse
                        let parsed = JSON.parse(rawContent);
                        
                        // Handle double-encoded JSON string if necessary
                        if (typeof parsed === 'string') {
                            try {
                                parsed = JSON.parse(parsed);
                            } catch (e) {
                                console.warn("Mapping was a string but not valid JSON, using as is or empty");
                            }
                        }
                        currentMapping = parsed || {};
                    }
                    console.log("Loaded Strava config:", { entryTypes, currentMapping });
                } catch (e) {
                    console.error("Error loading Strava data:", e);
                }

                function renderMappingTable() {
                    if (!stravaMappingTable) return;
                    stravaMappingTable.innerHTML = '';
                    
                    // Default Row
                    renderMappingRow('Default (All Others)', 'default');
                    
                    // Specific Types
                    commonStravaTypes.forEach(type => {
                        renderMappingRow(type, type);
                    });
                }
                
                function renderMappingRow(label, key) {
                    const tr = document.createElement('tr');
                    
                    const tdLabel = document.createElement('td');
                    tdLabel.textContent = label;
                    if (key === 'default') tdLabel.innerHTML = '<strong>Default (All Others)</strong>';
                    
                    const tdSelect = document.createElement('td');
                    const select = document.createElement('select');
                    select.className = 'form-select form-select-sm strava-mapping-select';
                    select.dataset.stravaType = key;
                    
                    entryTypes.forEach(et => {
                        const option = document.createElement('option');
                        option.value = et.id;
                        option.textContent = et.label;
                        // Check for match (handling string/number differences)
                        if (currentMapping[key] == et.id) option.selected = true;
                        select.appendChild(option);
                    });
                    
                    tdSelect.appendChild(select);
                    tr.appendChild(tdLabel);
                    tr.appendChild(tdSelect);
                    stravaMappingTable.appendChild(tr);
                }
                
                if (stravaMappingTable) renderMappingTable();

                if (stravaSettingsForm) {
                    console.log("Strava form found, attaching listener");
                    
                    // Handle Form Submit
                    stravaSettingsForm.addEventListener('submit', async function(e) {
                        console.log("Strava form submitted");
                        e.preventDefault();

                        const saveBtn = document.getElementById('saveStravaConfigBtn');
                        await runWithLoadingButton(saveBtn, '<i class="fas fa-spinner fa-spin me-1"></i>Saving...', async () => {
                            try {
                                const clientId = document.getElementById('stravaClientId').value;
                                const clientSecret = document.getElementById('stravaClientSecret').value;
                                const refreshToken = document.getElementById('stravaRefreshToken').value;

                                // Collect Mapping Data
                                const mapping = {};
                                document.querySelectorAll('.strava-mapping-select').forEach(select => {
                                    if (select.value) {
                                        mapping[select.dataset.stravaType] = select.value;
                                    }
                                });
                                console.log("Saving mapping:", mapping);

                                const formData = {
                                    strava_enabled: '1',
                                    strava_client_id: clientId,
                                    strava_client_secret: clientSecret,
                                    strava_refresh_token: refreshToken,
                                    strava_activity_mapping: JSON.stringify(mapping)
                                };

                                const response = await saveSystemParams(formData);

                                if (response.ok) {
                                    displayStatus('stravaSettingsStatus', '✅ Strava settings saved successfully!', 'alert-success');
                                } else {
                                    const error = await response.json();
                                    displayStatus('stravaSettingsStatus', 'Failed to save: ' + (error.error || 'Unknown error'), 'alert-danger');
                                }
                            } catch (error) {
                                console.error('Error saving Strava settings:', error);
                                displayStatus('stravaSettingsStatus', 'Error saving Strava settings: ' + error.message, 'alert-danger');
                            }
                        });
                    });
                } else {
                    console.error("Strava form not found!");
                }
            });

            document.addEventListener('DOMContentLoaded', function() {
                const garminForm = document.getElementById('garminConnectSettingsForm');
                const syncNowBtn = document.getElementById('syncGarminNowBtn');

                if (garminForm) {
                    garminForm.addEventListener('submit', async function(e) {
                        e.preventDefault();
                        const saveBtn = document.getElementById('saveGarminConfigBtn');
                        await runWithLoadingButton(saveBtn, '<i class="fas fa-spinner fa-spin me-1"></i>Saving...', async () => {
                            try {
                                const response = await fetch('/garmin/save_config', {
                                    method: 'POST',
                                    headers: { 'Content-Type': 'application/json' },
                                    body: JSON.stringify({
                                        username: document.getElementById('garminUsername').value.trim(),
                                        password: document.getElementById('garminPassword').value.trim(),
                                    })
                                });
                                const data = await response.json();
                                if (response.ok && data.status === 'success') {
                                    displayStatus('garminSettingsStatus', '✅ Garmin credentials saved!', 'alert-success');
                                } else {
                                    displayStatus('garminSettingsStatus', '❌ ' + (data.message || 'Failed to save.'), 'alert-danger');
                                }
                            } catch (error) {
                                displayStatus('garminSettingsStatus', '❌ Error: ' + error.message, 'alert-danger');
                            }
                        });
                    });
                }

                if (syncNowBtn) {
                    syncNowBtn.addEventListener('click', async function() {
                        await runWithLoadingButton(syncNowBtn, '<i class="fas fa-spinner fa-spin me-1"></i>Syncing...', async () => {
                            try {
                                const response = await fetch('/garmin/sync', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({}) });
                                const data = await response.json();
                                if (response.ok && data.status === 'success') {
                                    displayStatus('garminSettingsStatus', '✅ Garmin sync completed: ' + data.message, 'alert-success');
                                    const lbl = document.getElementById('garminLastSyncLabel');
                                    if (lbl) lbl.textContent = 'Last synced: just now';
                                } else if (response.ok && data.status === 'warning') {
                                    displayStatus('garminSettingsStatus', '⚠️ ' + data.message, 'alert-warning');
                                } else {
                                    displayStatus('garminSettingsStatus', '❌ Garmin sync failed: ' + (data.message || 'Unknown error'), 'alert-danger');
                                }
                            } catch (error) {
                                displayStatus('garminSettingsStatus', '❌ Error: ' + error.message, 'alert-danger');
                            }
                        });
                    });
                }
            });

        // HTML escape helper for safe rendering
        function escHtml(str) {
            return String(str || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
        }
        (function() {
            let stravaFieldDefs = [];
            let stravaFieldMapping = {};
            let stravaAllColumns = [];

            async function stravaEnsureColumnsLoaded() {
                if (stravaAllColumns.length) return;
                const r = await fetch('/api/custom-columns');
                if (r.ok) stravaAllColumns = await r.json();
            }

            window.stravaLoadFieldMapping = async function() {
                const statusEl = document.getElementById('stravaFieldMappingStatus');
                const hintEl   = document.getElementById('stravaFieldMappingHint');
                const wrapEl   = document.getElementById('stravaFieldMappingTableWrap');

                statusEl.className = 'mb-2 alert alert-secondary';
                statusEl.textContent = 'Loading…';
                statusEl.classList.remove('d-none');

                try {
                    await stravaEnsureColumnsLoaded();
                    const [fResp, mResp] = await Promise.all([
                        fetch('/api/strava/fields'),
                        fetch('/api/strava/field_mapping'),
                    ]);
                    const fData = await fResp.json();
                    const mData = await mResp.json();
                    stravaFieldDefs    = fData.fields || [];
                    stravaFieldMapping = mData.mapping || {};
                    stravaRenderFieldMappingTable();
                    wrapEl.classList.remove('d-none');
                    hintEl.classList.add('d-none');
                    statusEl.className = 'mb-2 alert alert-success';
                    statusEl.textContent = stravaFieldDefs.length + ' fields loaded.';
                } catch (e) {
                    statusEl.className = 'mb-2 alert alert-danger';
                    statusEl.textContent = 'Error loading fields: ' + e.message;
                }
            };

            function stravaRenderFieldMappingTable() {
                const tbody = document.getElementById('stravaFieldMappingTable');
                tbody.innerHTML = '';
                let lastGroup = null;
                stravaFieldDefs.forEach(field => {
                    const tr = document.createElement('tr');
                    const groupCell = field.group !== lastGroup
                        ? `<td class="text-muted small fw-semibold">${escHtml(field.group)}</td>`
                        : `<td></td>`;
                    lastGroup = field.group;

                    const currentColId = stravaFieldMapping[field.key] || '';
                    let options = '<option value="">— not mapped —</option>';
                    stravaAllColumns.forEach(col => {
                        const sel = String(currentColId) === String(col.id) ? ' selected' : '';
                        options += `<option value="${col.id}"${sel}>${escHtml(col.label)} <span class="text-muted">(${escHtml(col.name)})</span></option>`;
                    });

                    tr.innerHTML = groupCell +
                        `<td class="small">${escHtml(field.label)}</td>` +
                        `<td class="text-muted small font-monospace">${escHtml(field.unit || '')}</td>` +
                        `<td><select class="form-select form-select-sm strava-field-map-select"
                                     data-field-key="${escHtml(field.key)}">${options}</select></td>`;
                    tbody.appendChild(tr);
                });
            }

            window.stravaFieldMappingSave = async function() {
                const statusEl = document.getElementById('stravaFieldMappingStatus');
                const mapping = {};
                document.querySelectorAll('.strava-field-map-select').forEach(sel => {
                    if (sel.value) mapping[sel.dataset.fieldKey] = sel.value;
                });
                statusEl.className = 'mb-2 alert alert-secondary';
                statusEl.textContent = 'Saving…';
                statusEl.classList.remove('d-none');
                try {
                    const r = await fetch('/api/strava/field_mapping', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ mapping }),
                    });
                    const d = await r.json();
                    if (r.ok && d.success) {
                        stravaFieldMapping = d.mapping;
                        statusEl.className = 'mb-2 alert alert-success';
                        statusEl.textContent = 'Field mapping saved!';
                    } else {
                        statusEl.className = 'mb-2 alert alert-danger';
                        statusEl.textContent = d.message || 'Save failed.';
                    }
                } catch (e) {
                    statusEl.className = 'mb-2 alert alert-danger';
                    statusEl.textContent = 'Error: ' + e.message;
                }
            };

            window.stravaAutoCreateColumns = async function() {
                const statusEl = document.getElementById('stravaFieldMappingStatus');
                // Gather all mapped activity types and their entry type IDs
                const mapping = {};
                document.querySelectorAll('.strava-mapping-select').forEach(sel => {
                    if (sel.value) {
                        mapping[sel.dataset.stravaType] = sel.value;
                    }
                });
                if (Object.keys(mapping).length === 0) {
                    statusEl.className = 'mb-2 alert alert-warning';
                    statusEl.textContent = 'Please set at least one Activity Type mapping so we know which entry types to assign columns to.';
                    statusEl.classList.remove('d-none');
                    return;
                }
                statusEl.className = 'mb-2 alert alert-secondary';
                statusEl.textContent = 'Creating columns for all mapped activity types…';
                statusEl.classList.remove('d-none');
                try {
                    const r = await fetch('/api/strava/auto_create_columns', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ activity_type_entry_map: mapping }),
                    });
                    const d = await r.json();
                    if (r.ok && d.success) {
                        stravaFieldMapping = d.mapping;
                        stravaAllColumns = [];  // force reload
                        await stravaLoadFieldMapping();
                        statusEl.className = 'mb-2 alert alert-success';
                        statusEl.textContent = d.message;
                    } else {
                        statusEl.className = 'mb-2 alert alert-danger';
                        statusEl.textContent = d.message || 'Auto-create failed.';
                    }
                } catch (e) {
                    statusEl.className = 'mb-2 alert alert-danger';
                    statusEl.textContent = 'Error: ' + e.message;
                }
            };

            // ── Strava day entry linking ───────────────────────────────────────
            (async function stravaInitDayLink() {
                const relDefSel = document.getElementById('stravaRelDefId');
                const dayTypeSel = document.getElementById('stravaDayEntryTypeId');
                if (!relDefSel) return;

                let allRelDefs = [];

                async function stravaAutoCreateRelDefs(dayTypeId) {
                    if (!dayTypeId) return;
                    const dayLabel = dayTypeSel.options[dayTypeSel.selectedIndex]?.text || 'Day';

                    // Collect unique mapped activity entry types
                    const mappedTypes = new Map();
                    document.querySelectorAll('.strava-mapping-select').forEach(s => {
                        if (!s.value) return;
                        const opt = s.options[s.selectedIndex];
                        mappedTypes.set(String(s.value), opt ? opt.textContent.trim() : `Type ${s.value}`);
                    });
                    if (!mappedTypes.size) return;

                    let created = 0;
                    for (const [actTypeId, actLabel] of mappedTypes) {
                        const exists = allRelDefs.some(d => {
                            const pair = (String(d.entry_type_id_from) === dayTypeId && String(d.entry_type_id_to) === actTypeId)
                                      || (String(d.entry_type_id_to) === dayTypeId && String(d.entry_type_id_from) === actTypeId);
                            return pair && (
                                (Number(d.cardinality_from) === 1 && Number(d.cardinality_to) === -1) ||
                                (Number(d.cardinality_to)   === 1 && Number(d.cardinality_from) === -1)
                            );
                        });
                        if (exists) continue;
                        await fetch('/api/relationship_definitions', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                name:              `${dayLabel}_${actLabel}_1:N`,
                                entry_type_id_from: parseInt(dayTypeId),
                                entry_type_id_to:   parseInt(actTypeId),
                                cardinality_from:  'one',
                                cardinality_to:    'many',
                                label_from_side:   `${actLabel}s`,
                                label_to_side:     dayLabel,
                            }),
                        });
                        created++;
                    }
                    if (created > 0) {
                        const r = await fetch('/api/relationship_definitions');
                        allRelDefs = await r.json();
                    }
                    stravaRepopulateRelDefs();

                    // Auto-select: prefer the rel def covering the Default mapping
                    const defaultTypeId = document.querySelector('.strava-mapping-select[data-strava-type="default"]')?.value;
                    const preferred = defaultTypeId
                        ? allRelDefs.find(d =>
                            ((String(d.entry_type_id_from) === dayTypeId && String(d.entry_type_id_to) === defaultTypeId) ||
                             (String(d.entry_type_id_to) === dayTypeId && String(d.entry_type_id_from) === defaultTypeId)) &&
                            (Number(d.cardinality_from) === 1 || Number(d.cardinality_to) === 1))
                        : null;
                    if (preferred) relDefSel.value = String(preferred.id);
                }

                function stravaRepopulateRelDefs() {
                    const dayTypeId = dayTypeSel ? String(dayTypeSel.value) : '';
                    const savedDef  = relDefSel.dataset.saved || '';
                    relDefSel.innerHTML = '<option value="">-- Select relationship --</option>';

                    // Collect the unique entry-type IDs currently selected in the activity mapping table
                    const mappedTypeIds = new Set(
                        [...document.querySelectorAll('.strava-mapping-select')]
                            .map(s => s.value).filter(Boolean)
                    );

                    const filtered = dayTypeId
                        ? allRelDefs.filter(d => {
                            const fromMatch = String(d.entry_type_id_from) === dayTypeId;
                            const toMatch   = String(d.entry_type_id_to)   === dayTypeId;
                            const validFrom = fromMatch && Number(d.cardinality_from) === 1 && Number(d.cardinality_to) === -1;
                            const validTo   = toMatch   && Number(d.cardinality_to)   === 1 && Number(d.cardinality_from) === -1;
                            return validFrom || validTo;
                          })
                        : allRelDefs;

                    if (dayTypeId && filtered.length === 0) {
                        const opt = document.createElement('option');
                        opt.value = '';
                        opt.textContent = '— no one-to-many relationships for this type —';
                        opt.disabled = true;
                        relDefSel.appendChild(opt);
                        return;
                    }

                    filtered.forEach(d => {
                        // The "other" side is the activity side (not the day type)
                        const otherTypeId = String(d.entry_type_id_from) === dayTypeId
                            ? String(d.entry_type_id_to)
                            : String(d.entry_type_id_from);
                        const otherLabel  = String(d.entry_type_id_from) === dayTypeId
                            ? d.entry_type_to_label
                            : d.entry_type_from_label;

                        // Find which mapped activity types use this entry type
                        const coveredTypes = [...document.querySelectorAll('.strava-mapping-select')]
                            .filter(s => s.value === otherTypeId)
                            .map(s => s.dataset.stravaType === 'default' ? 'Default' : s.dataset.stravaType);

                        let suffix = '';
                        if (mappedTypeIds.size > 0) {
                            if (coveredTypes.length > 0) {
                                suffix = ` ✓ covers: ${coveredTypes.join(', ')}`;
                            } else if (mappedTypeIds.has(otherTypeId)) {
                                suffix = ' ✓ mapped';
                            } else {
                                suffix = ' — not in your activity mapping';
                            }
                        }

                        const opt = document.createElement('option');
                        opt.value = d.id;
                        opt.textContent = `${d.label_from_side || d.name} (${d.entry_type_from_label} → ${otherLabel})${suffix}`;
                        if (String(d.id) === String(savedDef)) opt.selected = true;
                        relDefSel.appendChild(opt);
                    });
                }

                try {
                    const r = await fetch('/api/relationship_definitions');
                    allRelDefs = await r.json();
                    stravaRepopulateRelDefs();
                } catch (e) {
                    console.warn('Could not load relationship definitions for Strava link picker', e);
                }

                if (dayTypeSel) {
                    dayTypeSel.addEventListener('change', () => stravaAutoCreateRelDefs(dayTypeSel.value));
                }
                // Re-annotate when activity mapping selects change
                document.querySelectorAll('.strava-mapping-select').forEach(s => {
                    s.addEventListener('change', stravaRepopulateRelDefs);
                });
            })();

            window.stravaSaveDayLink = async function() {
                const statusEl       = document.getElementById('stravaDayLinkStatus');
                const dayEntryTypeId = document.getElementById('stravaDayEntryTypeId').value || '';
                const relDefId       = document.getElementById('stravaRelDefId').value || '';

                statusEl.className = 'mb-2 alert alert-secondary';
                statusEl.textContent = 'Saving…';
                statusEl.classList.remove('d-none');
                try {
                    const params = [
                        { key: 'strava_day_entry_type_id',   value: dayEntryTypeId },
                        { key: 'strava_relationship_def_id', value: relDefId },
                    ];
                    for (const p of params) {
                        await fetch('/api/system_params', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify(p),
                        });
                    }
                    statusEl.className = 'mb-2 alert alert-success';
                    statusEl.textContent = dayEntryTypeId && relDefId
                        ? 'Saved — each synced activity will be linked to its day entry.'
                        : 'Saved — day auto-grouping disabled.';
                } catch (e) {
                    statusEl.className = 'mb-2 alert alert-danger';
                    statusEl.textContent = 'Error saving: ' + e.message;
                }
            };

            // ── Garmin Field Mapping ──────────────────────────────────────────────
            let garminFieldDefs = [];
            let garminFieldMapping = {};
            let garminAllColumns = [];

            async function garminEnsureColumnsLoaded() {
                if (garminAllColumns.length > 0) return;
                const r = await fetch('/api/custom-columns');
                const d = await r.json();
                garminAllColumns = Array.isArray(d) ? d : (d.columns || d.data || []);
            }

            window.garminLoadFieldMapping = async function() {
                const statusEl = document.getElementById('garminFieldMappingStatus');
                const hintEl   = document.getElementById('garminFieldMappingHint');
                const wrapEl   = document.getElementById('garminFieldMappingTableWrap');

                statusEl.className = 'mb-2 alert alert-secondary';
                statusEl.textContent = 'Loading…';
                statusEl.classList.remove('d-none');

                try {
                    await garminEnsureColumnsLoaded();
                    const [fResp, mResp] = await Promise.all([
                        fetch('/api/garmin/fields'),
                        fetch('/api/garmin/field_mapping'),
                    ]);
                    const fData = await fResp.json();
                    const mData = await mResp.json();
                    garminFieldDefs    = fData.fields || [];
                    garminFieldMapping = mData.mapping || {};
                    garminRenderFieldMappingTable();
                    wrapEl.classList.remove('d-none');
                    hintEl.classList.add('d-none');
                    statusEl.className = 'mb-2 alert alert-success';
                    statusEl.textContent = garminFieldDefs.length + ' metrics loaded.';
                } catch (e) {
                    statusEl.className = 'mb-2 alert alert-danger';
                    statusEl.textContent = 'Error loading metrics: ' + e.message;
                }
            };

            function garminRenderFieldMappingTable() {
                const tbody = document.getElementById('garminFieldMappingTable');
                tbody.innerHTML = '';
                let lastGroup = null;
                garminFieldDefs.forEach(field => {
                    const tr = document.createElement('tr');
                    const groupCell = field.group !== lastGroup
                        ? `<td class="text-muted small fw-semibold">${escHtml(field.group)}</td>`
                        : `<td></td>`;
                    lastGroup = field.group;

                    const currentColId = garminFieldMapping[field.key] || '';
                    let options = '<option value="">— not mapped —</option>';
                    garminAllColumns.forEach(col => {
                        const sel = String(currentColId) === String(col.id) ? ' selected' : '';
                        options += `<option value="${col.id}"${sel}>${escHtml(col.label)} <span class="text-muted">(${escHtml(col.name)})</span></option>`;
                    });

                    tr.innerHTML = groupCell +
                        `<td class="small">${escHtml(field.label)}</td>` +
                        `<td class="text-muted small font-monospace">${escHtml(field.unit || '')}</td>` +
                        `<td><select class="form-select form-select-sm garmin-field-map-select"
                                     data-field-key="${escHtml(field.key)}">${options}</select></td>`;
                    tbody.appendChild(tr);
                });
            }

            window.garminFieldMappingSave = async function() {
                const statusEl = document.getElementById('garminFieldMappingStatus');
                const mapping = {};
                document.querySelectorAll('.garmin-field-map-select').forEach(sel => {
                    if (sel.value) mapping[sel.dataset.fieldKey] = sel.value;
                });
                statusEl.className = 'mb-2 alert alert-secondary';
                statusEl.textContent = 'Saving…';
                statusEl.classList.remove('d-none');
                try {
                    const r = await fetch('/api/garmin/field_mapping', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ mapping }),
                    });
                    const d = await r.json();
                    if (r.ok && d.success) {
                        garminFieldMapping = d.mapping;
                        statusEl.className = 'mb-2 alert alert-success';
                        statusEl.textContent = 'Field mapping saved!';
                    } else {
                        statusEl.className = 'mb-2 alert alert-danger';
                        statusEl.textContent = d.message || 'Save failed.';
                    }
                } catch (e) {
                    statusEl.className = 'mb-2 alert alert-danger';
                    statusEl.textContent = 'Error: ' + e.message;
                }
            };

            window.garminAutoCreateColumns = async function() {
                const statusEl = document.getElementById('garminFieldMappingStatus');
                const entryTypeId = document.getElementById('garminEntryTypeId')?.value;
                if (!entryTypeId) {
                    statusEl.className = 'mb-2 alert alert-warning';
                    statusEl.textContent = 'Select an entry type first, then run auto-create.';
                    statusEl.classList.remove('d-none');
                    return;
                }
                statusEl.className = 'mb-2 alert alert-secondary';
                statusEl.textContent = 'Creating columns for all Garmin metrics…';
                statusEl.classList.remove('d-none');
                try {
                    const r = await fetch('/api/garmin/auto_create_columns', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ entry_type_id: parseInt(entryTypeId) }),
                    });
                    const d = await r.json();
                    if (r.ok && d.success) {
                        garminFieldMapping = d.mapping;
                        garminAllColumns = [];  // force reload
                        await garminLoadFieldMapping();
                        statusEl.className = 'mb-2 alert alert-success';
                        statusEl.textContent = d.message;
                    } else {
                        statusEl.className = 'mb-2 alert alert-danger';
                        statusEl.textContent = d.message || 'Auto-create failed.';
                    }
                } catch (e) {
                    statusEl.className = 'mb-2 alert alert-danger';
                    statusEl.textContent = 'Error: ' + e.message;
                }
            };

            // ── Test pull ──────────────────────────────────────────────
            let _garminTestRows = [];

            window.garminRunTestPull = async function() {
                const btn      = document.getElementById('garminTestPullBtn');
                const spinner  = document.getElementById('garminTestPullSpinner');
                const statusEl = document.getElementById('garminTestPullStatus');
                const wrap     = document.getElementById('garminTestPullWrap');
                const date     = document.getElementById('garminTestDate').value
                              || new Date().toISOString().slice(0,10);

                btn.disabled = true;
                spinner.classList.remove('d-none');
                statusEl.classList.add('d-none');
                wrap.classList.add('d-none');

                try {
                    const r = await fetch(`/api/garmin/test_pull?date=${encodeURIComponent(date)}`);
                    const d = await r.json();

                    if (!r.ok || !d.success) {
                        statusEl.className = 'mb-2 alert alert-danger';
                        statusEl.textContent = d.message || 'Test pull failed.';
                        statusEl.classList.remove('d-none');
                        return;
                    }

                    _garminTestRows = d.results;
                    document.getElementById('garminTestPullSearch').value = '';
                    garminRenderTestTable(_garminTestRows);

                    const errNote = d.errors.length
                        ? ` · ${d.errors.length} source error(s): ${d.errors.join('; ')}`
                        : '';
                    document.getElementById('garminTestPullSummary').textContent =
                        `${d.date} — ${d.fields_with_data}/${d.total_fields} fields returned data${errNote}`;

                    wrap.classList.remove('d-none');
                    if (d.errors.length) {
                        statusEl.className = 'mb-2 alert alert-warning';
                        statusEl.textContent = `${d.errors.length} source(s) returned errors (see summary). Other fields shown below.`;
                        statusEl.classList.remove('d-none');
                    }
                } catch(e) {
                    statusEl.className = 'mb-2 alert alert-danger';
                    statusEl.textContent = 'Error: ' + e.message;
                    statusEl.classList.remove('d-none');
                } finally {
                    btn.disabled = false;
                    spinner.classList.add('d-none');
                }
            };

            window.garminRenderTestTable = function(rows) {
                const tbody = document.getElementById('garminTestPullTable');
                let lastGroup = null, html = '';
                rows.forEach(row => {
                    const hasVal = row.value !== null && row.value !== undefined;
                    const groupLabel = row.group !== lastGroup
                        ? `<tr class="table-secondary"><td colspan="4"><strong>${row.group}</strong></td></tr>` : '';
                    lastGroup = row.group;
                    const valCell = hasVal
                        ? `<td class="text-success fw-semibold">${row.value}</td>`
                        : `<td class="text-muted">—</td>`;
                    html += groupLabel +
                        `<tr data-group="${row.group}" data-label="${row.label.toLowerCase()}">
                            <td class="text-muted small">${row.group}</td>
                            <td>${row.label}</td>
                            ${valCell}
                            <td class="text-muted small">${row.unit || ''}</td>
                        </tr>`;
                });
                tbody.innerHTML = html;
            };

            window.garminFilterTestTable = function(query) {
                const q = query.toLowerCase();
                if (!q) { garminRenderTestTable(_garminTestRows); return; }
                const filtered = _garminTestRows.filter(r =>
                    r.label.toLowerCase().includes(q) ||
                    r.group.toLowerCase().includes(q) ||
                    (r.key && r.key.toLowerCase().includes(q))
                );
                garminRenderTestTable(filtered);
            };

            // ── Day entry type link settings ──────────────────────────────────
            (async function garminInitParentLink() {
                const dayTypeSel = document.getElementById('garminDayEntryTypeId');
                const relDefSel  = document.getElementById('garminRelDefId');
                if (!relDefSel) return;

                let allRelDefs = [];

                async function garminAutoCreateRelDef(dayTypeId) {
                    if (!dayTypeId) return;
                    const dataTypeSel = document.getElementById('garminEntryTypeId');
                    const dataTypeId  = dataTypeSel?.value;
                    if (!dataTypeId) return;

                    const dayLabel  = dayTypeSel.options[dayTypeSel.selectedIndex]?.text || 'Day';
                    const dataLabel = dataTypeSel.options[dataTypeSel.selectedIndex]?.text || 'Garmin Data';

                    const exists = allRelDefs.some(d => {
                        const pair = (String(d.entry_type_id_from) === dayTypeId && String(d.entry_type_id_to) === dataTypeId)
                                  || (String(d.entry_type_id_to) === dayTypeId && String(d.entry_type_id_from) === dataTypeId);
                        return pair && (
                            (Number(d.cardinality_from) === 1 && Number(d.cardinality_to) === -1) ||
                            (Number(d.cardinality_to)   === 1 && Number(d.cardinality_from) === -1)
                        );
                    });

                    if (!exists) {
                        await fetch('/api/relationship_definitions', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                name:              `${dayLabel}_${dataLabel}_1:N`,
                                entry_type_id_from: parseInt(dayTypeId),
                                entry_type_id_to:   parseInt(dataTypeId),
                                cardinality_from:  'one',
                                cardinality_to:    'many',
                                label_from_side:   `${dataLabel}s`,
                                label_to_side:     dayLabel,
                            }),
                        });
                        const r = await fetch('/api/relationship_definitions');
                        allRelDefs = await r.json();
                    }
                    garminRepopulateRelDefs();

                    // Auto-select the relationship between day and data type
                    const match = allRelDefs.find(d =>
                        ((String(d.entry_type_id_from) === dayTypeId && String(d.entry_type_id_to) === dataTypeId) ||
                         (String(d.entry_type_id_to) === dayTypeId && String(d.entry_type_id_from) === dataTypeId)) &&
                        (Number(d.cardinality_from) === 1 || Number(d.cardinality_to) === 1)
                    );
                    if (match) relDefSel.value = String(match.id);
                }

                function garminRepopulateRelDefs() {
                    const dayTypeId = dayTypeSel ? String(dayTypeSel.value) : '';
                    const savedDef  = relDefSel.dataset.saved || '';
                    relDefSel.innerHTML = '<option value="">-- Select relationship --</option>';

                    const filtered = dayTypeId
                        ? allRelDefs.filter(d => {
                            const fromMatch = String(d.entry_type_id_from) === dayTypeId;
                            const toMatch   = String(d.entry_type_id_to)   === dayTypeId;
                            // Day side must be "one" (1), the other side "many" (-1)
                            const validFrom = fromMatch && Number(d.cardinality_from) === 1  && Number(d.cardinality_to) === -1;
                            const validTo   = toMatch   && Number(d.cardinality_to)   === 1  && Number(d.cardinality_from) === -1;
                            return validFrom || validTo;
                          })
                        : allRelDefs;

                    if (dayTypeId && filtered.length === 0) {
                        const opt = document.createElement('option');
                        opt.value = '';
                        opt.textContent = '— no one-to-many relationships for this type —';
                        opt.disabled = true;
                        relDefSel.appendChild(opt);
                        return;
                    }

                    filtered.forEach(d => {
                        const opt = document.createElement('option');
                        opt.value = d.id;
                        opt.textContent = `${d.label_from_side || d.name} (${d.entry_type_from_label} → ${d.entry_type_to_label})`;
                        if (String(d.id) === String(savedDef)) opt.selected = true;
                        relDefSel.appendChild(opt);
                    });
                }

                // Load all relationship definitions once
                try {
                    const r = await fetch('/api/relationship_definitions');
                    allRelDefs = await r.json();
                    garminRepopulateRelDefs();
                } catch (e) {
                    console.warn('Could not load relationship definitions for Garmin link picker', e);
                }

                // Auto-create & select when day entry type changes
                if (dayTypeSel) {
                    dayTypeSel.addEventListener('change', () => garminAutoCreateRelDef(dayTypeSel.value));
                }
            })();

            window.garminSaveParentLink = async function() {
                const statusEl       = document.getElementById('garminParentLinkStatus');
                const dayEntryTypeId = document.getElementById('garminDayEntryTypeId').value || '';
                const relDefId       = document.getElementById('garminRelDefId').value || '';

                statusEl.className = 'mb-2 alert alert-secondary';
                statusEl.textContent = 'Saving…';
                statusEl.classList.remove('d-none');
                try {
                    const params = [
                        { key: 'garmin_day_entry_type_id',   value: dayEntryTypeId },
                        { key: 'garmin_relationship_def_id', value: relDefId },
                    ];
                    for (const p of params) {
                        await fetch('/api/system_params', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify(p),
                        });
                    }
                    statusEl.className = 'mb-2 alert alert-success';
                    statusEl.textContent = dayEntryTypeId && relDefId
                        ? 'Saved — each sync will auto-create a Day entry and link the Garmin data to it.'
                        : 'Saved — day auto-grouping disabled.';
                } catch (e) {
                    statusEl.className = 'mb-2 alert alert-danger';
                    statusEl.textContent = 'Error saving: ' + e.message;
                }
            };

        })();

