/**
 * Entry Data Points Section — _entry_data_functions.js
 *
 * Manages the per-entry multi-metric chart + add/edit/delete readings.
 * One instance per section (keyed by section ID).
 */

// ── Per-section state ──────────────────────────────────────────────────────
const _edState = {};

function _edGet(sid) {
    if (!_edState[sid]) {
        _edState[sid] = {
            chart: null,
            metrics: [],
            selectedMetricIds: [],
            dataPoints: [],
            tableVisible: false,
            sourceMode: 'own',        // 'own' | 'related'
            dataMode: 'metrics',      // 'metrics' | 'columns'
            relationships: [],        // from GET /api/entries/<id>/relationships
            relatedEntryIds: [],      // resolved entry IDs when in 'related' mode
            relatedEntryTypeId: null, // entry_type_id of related entries
            columns: [],              // numeric custom columns for related entry type
            selectedColumnIds: [],    // currently selected column IDs
            selectColumns: [],        // select-type custom columns for distribution mode
            selectedSelectColumnId: null, // chosen column for distribution mode
        };
    }
    return _edState[sid];
}

// ── Initialise ────────────────────────────────────────────────────────────
async function edInitSection(sid, entryId) {
    const st = _edGet(sid);
    st.entryId = entryId;

    // Wire up controls
    document.getElementById(`edTimeRange-${sid}`)
        .addEventListener('change', () => edRefresh(sid));
    document.getElementById(`edXAxisType-${sid}`)
        .addEventListener('change', () => edOnXAxisTypeChange(sid));
    document.getElementById(`edXAxisField-${sid}`)
        .addEventListener('change', () => edRefresh(sid));
    const _chartTypeSel = document.getElementById(`edChartType-${sid}`);
    if (_chartTypeSel) {
        _chartTypeSel.addEventListener('change', () => edRefresh(sid));
        // Pie/doughnut are only valid in distribution mode — disable them on init
        ['pie','doughnut'].forEach(v => {
            const o = _chartTypeSel.querySelector(`option[value="${v}"]`);
            if (o) o.disabled = true;
        });
    }

    // Load relationships for the source toggle (don't await — load in parallel)
    edLoadRelationships(sid, entryId);

    // Load metrics available for this entry's type
    await edLoadMetrics(sid, entryId);
    await edRefresh(sid);
}

// ── Source mode (own vs related) ──────────────────────────────────────────
async function edHandleSourceChange(sid) {
    const st = _edGet(sid);
    const radio = document.querySelector(`input[name="edSource-${sid}"]:checked`);
    st.sourceMode = radio ? radio.value : 'own';

    const relDefSel   = document.getElementById(`edRelDef-${sid}`);
    const dataModeRow = document.getElementById(`edDataModeRow-${sid}`);

    if (st.sourceMode === 'related') {
        relDefSel.classList.remove('d-none');
        dataModeRow.classList.remove('d-none');
        // Trigger relationship load if not done yet
        if (!st.relationships.length) {
            await edLoadRelationships(sid, st.entryId);
        }
        // Resolve initial set of entry IDs (all relationships, first def if available)
        await edHandleRelDefChange(sid);
    } else {
        relDefSel.classList.add('d-none');
        dataModeRow.classList.add('d-none');
        document.getElementById(`edSelectColRow-${sid}`).classList.add('d-none');
        st.relatedEntryIds = [];
        // Reset to metrics mode
        st.dataMode = 'metrics';
        const metricsRadio = document.getElementById(`edDataModeMetrics-${sid}`);
        if (metricsRadio) metricsRadio.checked = true;
        document.getElementById(`edMetricDropdown-${sid}`).classList.remove('d-none');
        document.getElementById(`edColumnDropdown-${sid}`).classList.add('d-none');
        document.getElementById(`edTimeRange-${sid}`).classList.remove('d-none');
        document.getElementById(`edXAxisType-${sid}`).classList.remove('d-none');
        const addBtn = document.getElementById(`edAddBtn-${sid}`);
        if (addBtn) addBtn.classList.remove('d-none');
        // Restore non-distribution chart types and reset to line
        const chartTypeSel = document.getElementById(`edChartType-${sid}`);
        if (chartTypeSel) {
            ['line','bar','scatter'].forEach(v => { const o = chartTypeSel.querySelector(`option[value="${v}"]`); if(o) o.disabled = false; });
            ['pie','doughnut'].forEach(v => { const o = chartTypeSel.querySelector(`option[value="${v}"]`); if(o) o.disabled = true; });
            if (['pie','doughnut'].includes(chartTypeSel.value)) chartTypeSel.value = 'line';
        }
        // Reload metrics scoped back to own entry type
        await edLoadMetrics(sid, st.entryId);
        await edRefresh(sid);
    }
}

async function edLoadRelationships(sid, entryId) {
    const st = _edGet(sid);
    try {
        const resp = await fetch(`/api/entries/${entryId}/relationships`);
        if (!resp.ok) return;
        st.relationships = await resp.json();

        // Build unique definitions from returned relationships
        const defsMap = {};
        st.relationships.forEach(r => {
            if (!defsMap[r.definition_id]) {
                defsMap[r.definition_id] = {
                    id: r.definition_id,
                    name: r.definition_name,
                    label: r.relationship_label,
                };
            }
        });
        const defs = Object.values(defsMap);

        const sel = document.getElementById(`edRelDef-${sid}`);
        if (!defs.length) {
            sel.innerHTML = '<option value="">No relationships found</option>';
            return;
        }
        sel.innerHTML = '<option value="">All related entries</option>'
            + defs.map(d => `<option value="${d.id}">${_edEsc(d.label || d.name)}</option>`).join('');
    } catch (err) {
        console.warn(`[entry_data:${sid}] Could not load relationships`, err);
    }
}

async function edHandleRelDefChange(sid) {
    const st = _edGet(sid);
    const sel = document.getElementById(`edRelDef-${sid}`);
    const selectedDefId = sel ? parseInt(sel.value) || null : null;

    // Filter relationships by chosen definition (or use all if none selected)
    const relevant = selectedDefId
        ? st.relationships.filter(r => r.definition_id === selectedDefId)
        : st.relationships;

    st.relatedEntryIds = [...new Set(relevant.map(r => r.related_entry_id))];
    st.relatedEntryTypeId = null; // reset; will be resolved if needed

    if (st.dataMode === 'columns' || st.dataMode === 'distribution') {
        // Resolve related entry type then reload columns/select columns
        await _edResolveRelatedEntryType(sid);
    } else {
        // Reload metrics — show all since related entries may have any metric
        await edLoadMetrics(sid, st.entryId, true);
        await edRefresh(sid);
    }
}

// ── Data mode (metrics vs custom columns vs distribution) ─────────────────
async function edHandleDataModeChange(sid) {
    const st = _edGet(sid);
    const radio = document.querySelector(`input[name="edDataMode-${sid}"]:checked`);
    st.dataMode = radio ? radio.value : 'metrics';

    const metricDrop    = document.getElementById(`edMetricDropdown-${sid}`);
    const columnDrop    = document.getElementById(`edColumnDropdown-${sid}`);
    const selectColRow  = document.getElementById(`edSelectColRow-${sid}`);
    const timeRangeSel  = document.getElementById(`edTimeRange-${sid}`);
    const xAxisTypeSel  = document.getElementById(`edXAxisType-${sid}`);
    const xAxisFieldSel = document.getElementById(`edXAxisField-${sid}`);
    const addBtn        = document.getElementById(`edAddBtn-${sid}`);
    const chartTypeSel  = document.getElementById(`edChartType-${sid}`);

    if (st.dataMode === 'columns') {
        metricDrop.classList.add('d-none');
        columnDrop.classList.remove('d-none');
        if (selectColRow) selectColRow.classList.add('d-none');
        timeRangeSel.classList.add('d-none');
        xAxisTypeSel.classList.remove('d-none');
        if (addBtn) addBtn.classList.add('d-none');
        // Restrict chart type to non-distribution options
        if (chartTypeSel) {
            ['line','bar','scatter'].forEach(v => { const o = chartTypeSel.querySelector(`option[value="${v}"]`); if(o) o.disabled = false; });
            ['pie','doughnut'].forEach(v => { const o = chartTypeSel.querySelector(`option[value="${v}"]`); if(o) o.disabled = true; });
            if (['pie','doughnut'].includes(chartTypeSel.value)) chartTypeSel.value = 'line';
        }
        // Default x-axis to entry creation date
        if (xAxisTypeSel && xAxisTypeSel.value === 'recorded_at') {
            xAxisTypeSel.value = 'entry_field';
            if (xAxisFieldSel) {
                xAxisFieldSel.value = 'created_at';
                xAxisFieldSel.classList.remove('d-none');
            }
        }
        // Load columns for the related entry type
        if (!st.relatedEntryTypeId && st.relatedEntryIds.length) {
            await _edResolveRelatedEntryType(sid);
        } else if (st.relatedEntryTypeId) {
            await edLoadColumns(sid, st.relatedEntryTypeId);
            await edRefresh(sid);
        }
    } else if (st.dataMode === 'distribution') {
        metricDrop.classList.add('d-none');
        columnDrop.classList.add('d-none');
        if (selectColRow) selectColRow.classList.remove('d-none');
        timeRangeSel.classList.add('d-none');
        xAxisTypeSel.classList.add('d-none');
        if (xAxisFieldSel) xAxisFieldSel.classList.add('d-none');
        if (addBtn) addBtn.classList.add('d-none');
        // Restrict chart type to pie/doughnut
        if (chartTypeSel) {
            ['line','bar','scatter'].forEach(v => { const o = chartTypeSel.querySelector(`option[value="${v}"]`); if(o) o.disabled = true; });
            ['pie','doughnut'].forEach(v => { const o = chartTypeSel.querySelector(`option[value="${v}"]`); if(o) o.disabled = false; });
            if (!['pie','doughnut'].includes(chartTypeSel.value)) chartTypeSel.value = 'pie';
        }
        // Load select columns for the related entry type
        if (!st.relatedEntryTypeId && st.relatedEntryIds.length) {
            await _edResolveRelatedEntryType(sid);
        } else if (st.relatedEntryTypeId) {
            await edLoadSelectColumns(sid, st.relatedEntryTypeId);
            await edRefresh(sid);
        }
    } else {
        metricDrop.classList.remove('d-none');
        columnDrop.classList.add('d-none');
        if (selectColRow) selectColRow.classList.add('d-none');
        timeRangeSel.classList.remove('d-none');
        xAxisTypeSel.classList.remove('d-none');
        if (addBtn) addBtn.classList.remove('d-none');
        // Re-enable all chart types and default to line
        if (chartTypeSel) {
            ['line','bar','scatter'].forEach(v => { const o = chartTypeSel.querySelector(`option[value="${v}"]`); if(o) o.disabled = false; });
            ['pie','doughnut'].forEach(v => { const o = chartTypeSel.querySelector(`option[value="${v}"]`); if(o) o.disabled = true; });
            if (['pie','doughnut'].includes(chartTypeSel.value)) chartTypeSel.value = 'line';
        }
        await edRefresh(sid);
    }
}

async function _edResolveRelatedEntryType(sid) {
    const st = _edGet(sid);
    if (!st.relatedEntryIds.length) return;
    try {
        const resp = await fetch(`/api/entries/${st.relatedEntryIds[0]}`);
        if (!resp.ok) return;
        const data = await resp.json();
        st.relatedEntryTypeId = data.entry_type_id || (data.entry && data.entry.entry_type_id);
        if (st.relatedEntryTypeId) {
            if (st.dataMode === 'distribution') {
                await edLoadSelectColumns(sid, st.relatedEntryTypeId);
            } else {
                await edLoadColumns(sid, st.relatedEntryTypeId);
            }
            await edRefresh(sid);
        }
    } catch (err) {
        console.warn(`[entry_data:${sid}] Could not resolve related entry type`, err);
    }
}

async function edLoadColumns(sid, entryTypeId) {
    const st = _edGet(sid);
    const menu = document.getElementById(`edColumnMenu-${sid}`);
    try {
        const resp = await fetch(`/api/entry-types/${entryTypeId}/custom-columns`);
        if (!resp.ok) throw new Error('Failed to load columns');
        const assignments = await resp.json();

        // Only numeric columns can be meaningfully plotted
        st.columns = assignments
            .filter(a => a.column.column_type === 'number')
            .map(a => ({ id: a.column.id, label: a.column.label, unit: a.column.unit || '' }));

        if (!st.columns.length) {
            if (menu) menu.innerHTML = '<li class="text-muted small px-2 py-1">No numeric columns for this entry type.</li>';
            st.selectedColumnIds = [];
            return;
        }

        // Select all by default
        st.selectedColumnIds = st.columns.map(c => c.id);

        if (menu) {
            menu.innerHTML = st.columns.map(c => `
                <li>
                  <label class="dropdown-item d-flex align-items-center gap-2 py-1">
                    <input type="checkbox" class="form-check-input mt-0"
                           value="${c.id}" checked
                           onchange="edOnColumnToggle('${sid}', ${c.id}, this.checked)">
                    <span>${_edEsc(c.label)}${c.unit ? ' (' + _edEsc(c.unit) + ')' : ''}</span>
                  </label>
                </li>
            `).join('');
        }
        _edUpdateColumnLabel(sid);
    } catch (err) {
        console.error(`[entry_data:${sid}] Error loading columns:`, err);
        if (menu) menu.innerHTML = '<li class="text-danger small px-2 py-1">Failed to load columns.</li>';
    }
}

function edOnColumnToggle(sid, colId, checked) {
    const st = _edGet(sid);
    if (checked) {
        if (!st.selectedColumnIds.includes(colId)) st.selectedColumnIds.push(colId);
    } else {
        st.selectedColumnIds = st.selectedColumnIds.filter(id => id !== colId);
    }
    _edUpdateColumnLabel(sid);
    edRefresh(sid);
}

function _edUpdateColumnLabel(sid) {
    const st = _edGet(sid);
    const total = st.columns.length;
    const sel   = st.selectedColumnIds.length;
    const label = document.getElementById(`edColumnLabel-${sid}`);
    if (!label) return;
    if (sel === 0 || sel === total) {
        label.textContent = 'All Columns';
    } else if (sel === 1) {
        const c = st.columns.find(c => c.id === st.selectedColumnIds[0]);
        label.textContent = c ? c.label : '1 Column';
    } else {
        label.textContent = `${sel} Columns`;
    }
}

// ── Load available metrics ─────────────────────────────────────────────────
async function edLoadMetrics(sid, entryId, allTypes = false) {
    const st = _edGet(sid);
    try {
        // Get entry's type first
        const entryResp = await fetch(`/api/entries/${entryId}`);
        let entryTypeId = null;
        if (entryResp.ok && !allTypes) {
            const entryData = await entryResp.json();
            entryTypeId = entryData.entry_type_id || entryData.entry?.entry_type_id;
        }

        const url = entryTypeId
            ? `/api/entry-metrics?entry_type_id=${entryTypeId}`
            : '/api/entry-metrics';
        const resp = await fetch(url);
        if (!resp.ok) throw new Error('Failed to load metrics');
        st.metrics = await resp.json();

        // Build dropdown checkboxes
        const menu = document.getElementById(`edMetricMenu-${sid}`);
        if (!st.metrics.length) {
            menu.innerHTML = '<li class="text-muted small px-2 py-1">No metrics defined yet.<br>'
                + '<a href="/manage-entry-metrics" class="small">Manage Metrics →</a></li>';
            return;
        }

        // Select all by default
        st.selectedMetricIds = st.metrics.map(m => m.id);

        menu.innerHTML = st.metrics.map(m => `
            <li>
              <label class="dropdown-item d-flex align-items-center gap-2 py-1">
                <input type="checkbox" class="form-check-input mt-0 ed-metric-cb-${sid}"
                       value="${m.id}" checked
                       onchange="edOnMetricToggle('${sid}', ${m.id}, this.checked)">
                <span class="d-inline-block rounded me-1"
                      style="width:10px;height:10px;background:${_edEsc(m.color)};flex-shrink:0;"></span>
                <span>${_edEsc(m.label)}${m.unit ? ' (' + _edEsc(m.unit) + ')' : ''}</span>
              </label>
            </li>
        `).join('');

        // Populate metric select in add modal
        const metricSel = document.getElementById(`edAddMetricId-${sid}`);
        metricSel.innerHTML = '<option value="">Select metric…</option>'
            + st.metrics.map(m =>
                `<option value="${m.id}">${_edEsc(m.label)}${m.unit ? ' (' + _edEsc(m.unit) + ')' : ''}</option>`
            ).join('');

        // Update unit hint when metric changes
        metricSel.addEventListener('change', () => {
            const chosen = st.metrics.find(m => m.id === parseInt(metricSel.value));
            const hint = document.getElementById(`edAddUnit-${sid}`);
            hint.textContent = chosen?.unit ? `Unit: ${chosen.unit}` : '';
        });

    } catch (err) {
        console.error(`[entry_data:${sid}] Error loading metrics:`, err);
    }
}

// ── Metric toggle ──────────────────────────────────────────────────────────
function edOnMetricToggle(sid, metricId, checked) {
    const st = _edGet(sid);
    if (checked) {
        if (!st.selectedMetricIds.includes(metricId)) st.selectedMetricIds.push(metricId);
    } else {
        st.selectedMetricIds = st.selectedMetricIds.filter(id => id !== metricId);
    }
    _edUpdateMetricLabel(sid);
    edRefresh(sid);
}

function _edUpdateMetricLabel(sid) {
    const st = _edGet(sid);
    const total = st.metrics.length;
    const sel = st.selectedMetricIds.length;
    const label = document.getElementById(`edMetricLabel-${sid}`);
    if (!label) return;
    if (sel === 0 || sel === total) {
        label.textContent = 'All Metrics';
    } else if (sel === 1) {
        const m = st.metrics.find(m => m.id === st.selectedMetricIds[0]);
        label.textContent = m ? m.label : '1 Metric';
    } else {
        label.textContent = `${sel} Metrics`;
    }
}

// ── X-axis type change ────────────────────────────────────────────────────
function edOnXAxisTypeChange(sid) {
    const xType = document.getElementById(`edXAxisType-${sid}`).value;
    const fieldSel = document.getElementById(`edXAxisField-${sid}`);
    const timeRangeSel = document.getElementById(`edTimeRange-${sid}`);
    const st = _edGet(sid);
    if (xType === 'entry_field') {
        fieldSel.classList.remove('d-none');
        timeRangeSel.classList.add('d-none');
    } else {
        fieldSel.classList.add('d-none');
        // Time range only relevant in metrics mode with recorded_at
        if (st.dataMode !== 'columns' && xType === 'recorded_at') {
            timeRangeSel.classList.remove('d-none');
        } else if (st.dataMode === 'columns') {
            timeRangeSel.classList.add('d-none');
        } else {
            timeRangeSel.classList.remove('d-none');
        }
    }
    edRefresh(sid);
}

// ── Toggle table ──────────────────────────────────────────────────────────
function edToggleTable(sid) {
    const st = _edGet(sid);
    st.tableVisible = !st.tableVisible;
    const tc = document.getElementById(`edTableContainer-${sid}`);
    if (st.tableVisible) {
        tc.classList.remove('d-none');
        edRenderTable(sid);
    } else {
        tc.classList.add('d-none');
    }
}

// ── Refresh (load data + redraw) ──────────────────────────────────────────
async function edRefresh(sid) {
    const st = _edGet(sid);
    if (!st.entryId) return;

    // Branch: column values mode uses a different data source and endpoint
    if (st.dataMode === 'columns') {
        await edRefreshColumns(sid);
        return;
    }
    if (st.dataMode === 'distribution') {
        await edRefreshDistribution(sid);
        return;
    }

    const metricIds = st.selectedMetricIds.length ? st.selectedMetricIds : st.metrics.map(m => m.id);
    if (!metricIds.length) {
        edShowNoData(sid, true);
        return;
    }

    // In 'related' mode, plot data from related entries; in 'own' mode, plot this entry only
    const targetEntryIds = st.sourceMode === 'related' && st.relatedEntryIds.length
        ? st.relatedEntryIds
        : [st.entryId];

    // If in 'related' mode but no related entries resolved yet, show empty
    if (st.sourceMode === 'related' && !st.relatedEntryIds.length) {
        edShowNoData(sid, true);
        return;
    }

    const timeRange = document.getElementById(`edTimeRange-${sid}`).value;
    const xAxisType = document.getElementById(`edXAxisType-${sid}`).value;
    const xAxisField = document.getElementById(`edXAxisField-${sid}`).value;

    const params = new URLSearchParams({
        metric_ids: metricIds.join(','),
        entry_ids: targetEntryIds.join(','),
        time_range: timeRange,
        x_axis_type: xAxisType,
        x_axis_field: xAxisField,
    });

    try {
        const resp = await fetch(`/api/entry-metrics/chart-data?${params}`);
        if (!resp.ok) throw new Error('Chart data request failed');
        const data = await resp.json();

        const hasData = data.series && data.series.some(s => s.data_points.length > 0);
        edShowNoData(sid, !hasData);

        if (hasData) {
            edRenderChart(sid, data);
            if (st.tableVisible) edRenderTableFromSeries(sid, data.series);
        }

        // Also refresh the raw data points list for the table
        st.lastSeriesData = data.series;

    } catch (err) {
        console.error(`[entry_data:${sid}] Error refreshing:`, err);
    }
}

// ── Column chart refresh ──────────────────────────────────────────────────
async function edRefreshColumns(sid) {
    const st = _edGet(sid);
    if (!st.relatedEntryIds.length) {
        edShowNoData(sid, true);
        return;
    }

    const colIds = st.selectedColumnIds.length ? st.selectedColumnIds : st.columns.map(c => c.id);
    if (!colIds.length) {
        edShowNoData(sid, true);
        return;
    }

    const xAxisType  = document.getElementById(`edXAxisType-${sid}`).value;
    const xAxisField = document.getElementById(`edXAxisField-${sid}`).value;
    // 'recorded_at' has no meaning for column data — treat as entry_name
    const effectiveXType = xAxisType === 'entry_field' ? 'entry_field' : 'entry_name';

    const params = new URLSearchParams({
        entry_ids:   st.relatedEntryIds.join(','),
        column_ids:  colIds.join(','),
        x_axis_type: effectiveXType,
        x_axis_field: xAxisField,
    });

    try {
        const resp = await fetch(`/api/custom-columns/chart-data?${params}`);
        if (!resp.ok) throw new Error('Column chart data request failed');
        const data = await resp.json();

        const hasData = data.series && data.series.some(s => s.data_points.length > 0);
        edShowNoData(sid, !hasData);
        if (hasData) {
            edRenderChart(sid, data);
            if (st.tableVisible) edRenderTableFromSeries(sid, data.series);
        }
        st.lastSeriesData = data.series;
    } catch (err) {
        console.error(`[entry_data:${sid}] Error refreshing columns:`, err);
    }
}

// ── Select-column functions (distribution mode) ──────────────────────────
async function edLoadSelectColumns(sid, entryTypeId) {
    const st = _edGet(sid);
    const picker = document.getElementById(`edSelectColPicker-${sid}`);
    try {
        const resp = await fetch(`/api/entry-types/${entryTypeId}/custom-columns`);
        if (!resp.ok) throw new Error('Failed to load columns');
        const assignments = await resp.json();

        st.selectColumns = assignments
            .filter(a => a.column.column_type === 'select')
            .map(a => ({ id: a.column.id, label: a.column.label }));

        if (!st.selectColumns.length) {
            if (picker) picker.innerHTML = '<option value="">No select columns for this type</option>';
            st.selectedSelectColumnId = null;
            return;
        }

        if (picker) {
            picker.innerHTML = st.selectColumns
                .map(c => `<option value="${c.id}">${_edEsc(c.label)}</option>`)
                .join('');
        }
        st.selectedSelectColumnId = st.selectColumns[0].id;
    } catch (err) {
        console.error(`[entry_data:${sid}] Error loading select columns:`, err);
        if (picker) picker.innerHTML = '<option value="">Failed to load columns</option>';
    }
}

function edHandleSelectColChange(sid) {
    const st = _edGet(sid);
    const picker = document.getElementById(`edSelectColPicker-${sid}`);
    st.selectedSelectColumnId = picker ? (parseInt(picker.value) || null) : null;
    edRefresh(sid);
}

async function edRefreshDistribution(sid) {
    const st = _edGet(sid);
    if (!st.relatedEntryIds.length || !st.selectedSelectColumnId) {
        edShowNoData(sid, true);
        return;
    }

    const params = new URLSearchParams({
        entry_ids: st.relatedEntryIds.join(','),
        column_id: st.selectedSelectColumnId,
    });

    try {
        const resp = await fetch(`/api/custom-columns/distribution?${params}`);
        if (!resp.ok) throw new Error('Distribution request failed');
        const data = await resp.json();

        const hasData = data.categories && data.categories.length > 0;
        edShowNoData(sid, !hasData);
        if (hasData) {
            edRenderDistributionChart(sid, data);
        }
    } catch (err) {
        console.error(`[entry_data:${sid}] Error refreshing distribution:`, err);
    }
}

function edRenderDistributionChart(sid, data) {
    const st = _edGet(sid);
    const ctx = document.getElementById(`edChart-${sid}`);
    if (!ctx) return;

    const chartTypeSel = document.getElementById(`edChartType-${sid}`);
    const chartType = (chartTypeSel && chartTypeSel.value === 'doughnut') ? 'doughnut' : 'pie';

    if (st.chart) {
        st.chart.destroy();
        st.chart = null;
    }

    const labels = data.categories.map(c => c.name);
    const counts = data.categories.map(c => c.count);
    const colors = data.categories.map(c => c.color);

    st.chart = new Chart(ctx, {
        type: chartType,
        data: {
            labels,
            datasets: [{
                label: data.column_label || 'Distribution',
                data: counts,
                backgroundColor: colors,
                borderColor: colors.map(c => c),
                borderWidth: 2,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'right', labels: { usePointStyle: true, padding: 12 } },
                tooltip: {
                    callbacks: {
                        label(context) {
                            const pct = data.total
                                ? ((context.raw / data.total) * 100).toFixed(1)
                                : 0;
                            return ` ${context.label}: ${context.raw} (${pct}%)`;
                        }
                    }
                },
                title: {
                    display: !!data.column_label,
                    text: data.column_label || '',
                },
            },
        },
    });
}

function edShowNoData(sid, show) {
    const noData = document.getElementById(`edNoData-${sid}`);
    const chart = document.getElementById(`edChartContainer-${sid}`);
    if (noData) noData.classList.toggle('d-none', !show);
    if (chart) chart.style.display = show ? 'none' : '';
}

// ── Chart rendering ───────────────────────────────────────────────────────
function edRenderChart(sid, apiData) {
    const st = _edGet(sid);
    const ctx = document.getElementById(`edChart-${sid}`);
    if (!ctx) return;

    const chartType = document.getElementById(`edChartType-${sid}`).value;

    // Build datasets
    const datasets = apiData.series.filter(s => s.data_points.length > 0).map(s => ({
        label: s.label,
        data: s.data_points.map(p => ({ x: p.x, y: p.y, entryId: p.entry_id, entryTitle: p.entry_title })),
        borderColor: s.color,
        backgroundColor: s.color + '33',
        pointBackgroundColor: s.color,
        fill: chartType === 'line',
        tension: 0.3,
        borderWidth: 2,
        pointRadius: 4,
        pointHoverRadius: 6,
    }));

    if (st.chart) {
        st.chart.destroy();
        st.chart = null;
    }

    const isTimeSeries = apiData.x_axis_type === 'recorded_at';

    st.chart = new Chart(ctx, {
        type: chartType === 'scatter' ? 'scatter' : chartType,
        data: { datasets },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: 'nearest', intersect: false },
            plugins: {
                legend: { position: 'top', labels: { usePointStyle: true, padding: 12 } },
                tooltip: {
                    callbacks: {
                        label(context) {
                            const raw = context.raw;
                            let label = `${context.dataset.label}: ${raw.y}`;
                            if (raw.entryTitle) label += ` (${raw.entryTitle})`;
                            return label;
                        }
                    }
                }
            },
            scales: {
                x: {
                    type: isTimeSeries ? 'time' : 'category',
                    ...(isTimeSeries ? { time: { tooltipFormat: 'PPpp', displayFormats: { hour: 'MMM d HH:mm', day: 'MMM d', week: 'MMM d', month: 'MMM yyyy' } } } : {}),
                    title: { display: true, text: apiData.x_axis_label || 'X' },
                },
                y: {
                    beginAtZero: false,
                    title: { display: false },
                }
            }
        }
    });
}

// ── Table ─────────────────────────────────────────────────────────────────
function edRenderTable(sid) {
    const st = _edGet(sid);
    if (st.lastSeriesData) {
        edRenderTableFromSeries(sid, st.lastSeriesData);
    }
}

function edRenderTableFromSeries(sid, series) {
    const tbody = document.getElementById(`edTableBody-${sid}`);
    if (!tbody) return;

    // Flatten all data points, add metric label
    const rows = [];
    series.forEach(s => {
        s.data_points.forEach(p => {
            rows.push({ metric: s.label, unit: s.unit, ...p });
        });
    });

    // Sort by x (time) descending
    rows.sort((a, b) => (b.x > a.x ? 1 : -1));

    if (!rows.length) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-muted text-center">No data</td></tr>';
        return;
    }

    tbody.innerHTML = rows.map(r => `
        <tr>
            <td><span class="badge bg-secondary">${_edEsc(r.metric)}</span></td>
            <td class="fw-semibold">${r.y}${r.unit ? ' ' + _edEsc(r.unit) : ''}</td>
            <td class="text-muted small">${r.x ? new Date(r.x).toLocaleString() : '—'}</td>
            <td class="text-muted small">${r.notes ? _edEsc(r.notes) : '—'}</td>
            <td></td>
        </tr>
    `).join('');
}

// ── Add / Edit modal ───────────────────────────────────────────────────────
function edOpenAddModal(sid) {
    document.getElementById(`edEditDpId-${sid}`).value = '';
    document.getElementById(`edAddMetricId-${sid}`).value = '';
    document.getElementById(`edAddValue-${sid}`).value = '';
    document.getElementById(`edAddNotes-${sid}`).value = '';
    // Default recorded_at to now
    const now = new Date();
    now.setSeconds(0, 0);
    document.getElementById(`edAddRecordedAt-${sid}`).value = now.toISOString().slice(0, 16);
    document.getElementById(`edAddModalLabel-${sid}`).textContent = 'Add Reading';
    new bootstrap.Modal(document.getElementById(`edAddModal-${sid}`)).show();
}

async function edSaveReading(sid) {
    const st = _edGet(sid);
    const metricId = parseInt(document.getElementById(`edAddMetricId-${sid}`).value);
    const value = parseFloat(document.getElementById(`edAddValue-${sid}`).value);
    const recordedAt = document.getElementById(`edAddRecordedAt-${sid}`).value;
    const notes = document.getElementById(`edAddNotes-${sid}`).value.trim();
    const dpId = document.getElementById(`edEditDpId-${sid}`).value;

    if (!metricId || isNaN(value)) {
        alert('Metric and a numeric value are required.');
        return;
    }

    const payload = {
        metric_id: metricId,
        value,
        notes: notes || null,
        recorded_at: recordedAt ? new Date(recordedAt).toISOString() : undefined,
    };

    try {
        let resp;
        if (dpId) {
            resp = await fetch(`/api/data-points/${dpId}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ value, recorded_at: payload.recorded_at, notes: payload.notes }),
            });
        } else {
            resp = await fetch(`/api/entries/${st.entryId}/data-points`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });
        }

        if (!resp.ok) {
            const err = await resp.json();
            alert(err.error || 'Save failed.');
            return;
        }

        bootstrap.Modal.getInstance(document.getElementById(`edAddModal-${sid}`))?.hide();
        await edRefresh(sid);

    } catch (err) {
        alert('An error occurred.');
        console.error(err);
    }
}

// ── Utilities ─────────────────────────────────────────────────────────────
function _edEsc(str) {
    return String(str || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
