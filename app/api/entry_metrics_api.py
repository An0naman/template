# app/api/entry_metrics_api.py
"""
Entry Metrics API
=================
CRUD for EntryMetric definitions, EntryDataPoint per-entry readings,
and a chart-data endpoint that powers dashboard line_chart widgets.

Endpoints
---------
Metric definitions:
  GET    /api/entry-metrics                        – list all (optionally ?entry_type_id=)
  POST   /api/entry-metrics                        – create metric
  GET    /api/entry-metrics/<id>                   – get metric
  PATCH  /api/entry-metrics/<id>                   – update metric
  DELETE /api/entry-metrics/<id>                   – delete metric

Data points (per entry):
  GET    /api/entries/<entry_id>/data-points       – list data points
  POST   /api/entries/<entry_id>/data-points       – add data point
  PATCH  /api/data-points/<id>                     – update data point
  DELETE /api/data-points/<id>                     – delete data point

Chart data (dashboard widget + entry section):
  GET    /api/entry-metrics/chart-data
         params: metric_ids, search_id|entry_ids, time_range,
                 x_axis_type, x_axis_field, x_axis_custom_column_id
"""

import json
import logging
import re
from datetime import datetime, timezone, timedelta
from flask import Blueprint, request, jsonify, g
from ..db import get_connection

logger = logging.getLogger(__name__)

entry_metrics_api_bp = Blueprint('entry_metrics_api', __name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_db():
    if 'db' not in g:
        g.db = get_connection()
    return g.db


def _slug(label: str) -> str:
    slug = label.lower().strip()
    slug = re.sub(r'[^a-z0-9]+', '_', slug)
    slug = re.sub(r'_+', '_', slug).strip('_')
    return slug


def _now():
    return datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')


def _time_filter_dt(time_range: str):
    """Return an ISO timestamp string for the start of the given time range, or None."""
    now = datetime.now(timezone.utc)
    mapping = {'1d': 1, '7d': 7, '30d': 30, '90d': 90, '365d': 365}
    days = mapping.get(time_range)
    if days:
        return (now - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
    return None


def _row_to_metric(row) -> dict:
    return {
        'id': row['id'],
        'entry_type_id': row['entry_type_id'],
        'name': row['name'],
        'label': row['label'],
        'unit': row['unit'] or '',
        'color': row['color'] or '#4bc0c0',
        'display_order': row['display_order'],
        'created_at': row['created_at'],
        'updated_at': row['updated_at'],
    }


def _row_to_datapoint(row) -> dict:
    return {
        'id': row['id'],
        'entry_id': row['entry_id'],
        'metric_id': row['metric_id'],
        'metric_label': row['metric_label'] if 'metric_label' in row.keys() else None,
        'metric_unit': row['metric_unit'] if 'metric_unit' in row.keys() else None,
        'metric_color': row['metric_color'] if 'metric_color' in row.keys() else None,
        'value': row['value'],
        'recorded_at': row['recorded_at'],
        'notes': row['notes'],
        'created_at': row['created_at'],
    }


# ---------------------------------------------------------------------------
# Metric CRUD
# ---------------------------------------------------------------------------

@entry_metrics_api_bp.route('/entry-metrics', methods=['GET'])
def list_entry_metrics():
    """Return all metric definitions, optionally filtered by entry_type_id."""
    entry_type_id = request.args.get('entry_type_id', type=int)
    try:
        conn = get_db()
        cursor = conn.cursor()
        if entry_type_id is not None:
            cursor.execute('''
                SELECT * FROM EntryMetric
                WHERE entry_type_id = ? OR entry_type_id IS NULL
                ORDER BY display_order ASC, label ASC
            ''', (entry_type_id,))
        else:
            cursor.execute('''
                SELECT * FROM EntryMetric
                ORDER BY display_order ASC, label ASC
            ''')
        rows = cursor.fetchall()
        return jsonify([_row_to_metric(r) for r in rows]), 200
    except Exception as e:
        logger.error(f"Error listing entry metrics: {e}", exc_info=True)
        return jsonify({'error': 'An internal error occurred.'}), 500


@entry_metrics_api_bp.route('/entry-metrics', methods=['POST'])
def create_entry_metric():
    data = request.get_json(silent=True) or {}
    label = (data.get('label') or '').strip()
    if not label:
        return jsonify({'error': 'label is required'}), 400

    name = (data.get('name') or _slug(label)).strip()
    if not name:
        return jsonify({'error': 'name could not be derived from label'}), 400

    try:
        conn = get_db()
        cursor = conn.cursor()
        now = _now()
        cursor.execute('''
            INSERT INTO EntryMetric
                (entry_type_id, name, label, unit, color, display_order, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('entry_type_id'),
            name,
            label,
            data.get('unit', ''),
            data.get('color', '#4bc0c0'),
            data.get('display_order', 0),
            now, now,
        ))
        conn.commit()
        metric_id = cursor.lastrowid
        cursor.execute('SELECT * FROM EntryMetric WHERE id = ?', (metric_id,))
        row = cursor.fetchone()
        return jsonify(_row_to_metric(row)), 201
    except Exception as e:
        if 'UNIQUE' in str(e).upper():
            return jsonify({'error': f'A metric named "{name}" already exists.'}), 409
        logger.error(f"Error creating entry metric: {e}", exc_info=True)
        return jsonify({'error': 'An internal error occurred.'}), 500


@entry_metrics_api_bp.route('/entry-metrics/<int:metric_id>', methods=['GET'])
def get_entry_metric(metric_id):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM EntryMetric WHERE id = ?', (metric_id,))
        row = cursor.fetchone()
        if not row:
            return jsonify({'error': 'Not found'}), 404
        return jsonify(_row_to_metric(row)), 200
    except Exception as e:
        logger.error(f"Error getting entry metric {metric_id}: {e}", exc_info=True)
        return jsonify({'error': 'An internal error occurred.'}), 500


@entry_metrics_api_bp.route('/entry-metrics/<int:metric_id>', methods=['PATCH'])
def update_entry_metric(metric_id):
    data = request.get_json(silent=True) or {}
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM EntryMetric WHERE id = ?', (metric_id,))
        existing = cursor.fetchone()
        if not existing:
            return jsonify({'error': 'Not found'}), 404

        label = (data.get('label') or existing['label']).strip()
        name = (data.get('name') or existing['name']).strip()
        now = _now()

        cursor.execute('''
            UPDATE EntryMetric
            SET entry_type_id=?, name=?, label=?, unit=?, color=?,
                display_order=?, updated_at=?
            WHERE id=?
        ''', (
            data.get('entry_type_id', existing['entry_type_id']),
            name,
            label,
            data.get('unit', existing['unit'] or ''),
            data.get('color', existing['color'] or '#4bc0c0'),
            data.get('display_order', existing['display_order']),
            now,
            metric_id,
        ))
        conn.commit()
        cursor.execute('SELECT * FROM EntryMetric WHERE id = ?', (metric_id,))
        return jsonify(_row_to_metric(cursor.fetchone())), 200
    except Exception as e:
        if 'UNIQUE' in str(e).upper():
            return jsonify({'error': 'A metric with that name already exists.'}), 409
        logger.error(f"Error updating entry metric {metric_id}: {e}", exc_info=True)
        return jsonify({'error': 'An internal error occurred.'}), 500


@entry_metrics_api_bp.route('/entry-metrics/<int:metric_id>', methods=['DELETE'])
def delete_entry_metric(metric_id):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM EntryMetric WHERE id = ?', (metric_id,))
        if not cursor.fetchone():
            return jsonify({'error': 'Not found'}), 404
        cursor.execute('DELETE FROM EntryDataPoint WHERE metric_id = ?', (metric_id,))
        cursor.execute('DELETE FROM EntryMetric WHERE id = ?', (metric_id,))
        conn.commit()
        return jsonify({'deleted': True}), 200
    except Exception as e:
        logger.error(f"Error deleting entry metric {metric_id}: {e}", exc_info=True)
        return jsonify({'error': 'An internal error occurred.'}), 500


# ---------------------------------------------------------------------------
# Data Points (per entry)
# ---------------------------------------------------------------------------

@entry_metrics_api_bp.route('/entries/<int:entry_id>/data-points', methods=['GET'])
def list_data_points(entry_id):
    """Return data points for an entry, optionally filtered by metric_id and time_range."""
    metric_id = request.args.get('metric_id', type=int)
    time_range = request.args.get('time_range', 'all')
    try:
        conn = get_db()
        cursor = conn.cursor()

        # Verify entry exists
        cursor.execute('SELECT id FROM Entry WHERE id = ?', (entry_id,))
        if not cursor.fetchone():
            return jsonify({'error': 'Entry not found'}), 404

        query = '''
            SELECT edp.*, em.label AS metric_label, em.unit AS metric_unit,
                   em.color AS metric_color
            FROM EntryDataPoint edp
            JOIN EntryMetric em ON em.id = edp.metric_id
            WHERE edp.entry_id = ?
        '''
        params = [entry_id]

        if metric_id:
            query += ' AND edp.metric_id = ?'
            params.append(metric_id)

        tf = _time_filter_dt(time_range)
        if tf:
            query += ' AND edp.recorded_at >= ?'
            params.append(tf)

        query += ' ORDER BY edp.recorded_at ASC'

        cursor.execute(query, params)
        rows = cursor.fetchall()
        return jsonify([_row_to_datapoint(r) for r in rows]), 200
    except Exception as e:
        logger.error(f"Error listing data points for entry {entry_id}: {e}", exc_info=True)
        return jsonify({'error': 'An internal error occurred.'}), 500


@entry_metrics_api_bp.route('/entries/<int:entry_id>/data-points', methods=['POST'])
def add_data_point(entry_id):
    data = request.get_json(silent=True) or {}
    metric_id = data.get('metric_id')
    value = data.get('value')

    if metric_id is None:
        return jsonify({'error': 'metric_id is required'}), 400
    if value is None:
        return jsonify({'error': 'value is required'}), 400

    try:
        value = float(value)
    except (TypeError, ValueError):
        return jsonify({'error': 'value must be a number'}), 400

    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute('SELECT id FROM Entry WHERE id = ?', (entry_id,))
        if not cursor.fetchone():
            return jsonify({'error': 'Entry not found'}), 404

        cursor.execute('SELECT id FROM EntryMetric WHERE id = ?', (metric_id,))
        if not cursor.fetchone():
            return jsonify({'error': 'Metric not found'}), 404

        recorded_at = data.get('recorded_at') or _now()
        now = _now()

        cursor.execute('''
            INSERT INTO EntryDataPoint (entry_id, metric_id, value, recorded_at, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (entry_id, metric_id, value, recorded_at, data.get('notes'), now))
        conn.commit()
        dp_id = cursor.lastrowid

        cursor.execute('''
            SELECT edp.*, em.label AS metric_label, em.unit AS metric_unit,
                   em.color AS metric_color
            FROM EntryDataPoint edp
            JOIN EntryMetric em ON em.id = edp.metric_id
            WHERE edp.id = ?
        ''', (dp_id,))
        return jsonify(_row_to_datapoint(cursor.fetchone())), 201
    except Exception as e:
        logger.error(f"Error adding data point for entry {entry_id}: {e}", exc_info=True)
        return jsonify({'error': 'An internal error occurred.'}), 500


@entry_metrics_api_bp.route('/data-points/<int:dp_id>', methods=['PATCH'])
def update_data_point(dp_id):
    data = request.get_json(silent=True) or {}
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM EntryDataPoint WHERE id = ?', (dp_id,))
        existing = cursor.fetchone()
        if not existing:
            return jsonify({'error': 'Not found'}), 404

        value = data.get('value', existing['value'])
        try:
            value = float(value)
        except (TypeError, ValueError):
            return jsonify({'error': 'value must be a number'}), 400

        cursor.execute('''
            UPDATE EntryDataPoint
            SET value=?, recorded_at=?, notes=?
            WHERE id=?
        ''', (
            value,
            data.get('recorded_at', existing['recorded_at']),
            data.get('notes', existing['notes']),
            dp_id,
        ))
        conn.commit()

        cursor.execute('''
            SELECT edp.*, em.label AS metric_label, em.unit AS metric_unit,
                   em.color AS metric_color
            FROM EntryDataPoint edp
            JOIN EntryMetric em ON em.id = edp.metric_id
            WHERE edp.id = ?
        ''', (dp_id,))
        return jsonify(_row_to_datapoint(cursor.fetchone())), 200
    except Exception as e:
        logger.error(f"Error updating data point {dp_id}: {e}", exc_info=True)
        return jsonify({'error': 'An internal error occurred.'}), 500


@entry_metrics_api_bp.route('/data-points/<int:dp_id>', methods=['DELETE'])
def delete_data_point(dp_id):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM EntryDataPoint WHERE id = ?', (dp_id,))
        if not cursor.fetchone():
            return jsonify({'error': 'Not found'}), 404
        cursor.execute('DELETE FROM EntryDataPoint WHERE id = ?', (dp_id,))
        conn.commit()
        return jsonify({'deleted': True}), 200
    except Exception as e:
        logger.error(f"Error deleting data point {dp_id}: {e}", exc_info=True)
        return jsonify({'error': 'An internal error occurred.'}), 500


# ---------------------------------------------------------------------------
# Chart data endpoint (used by dashboard widgets and entry section)
# ---------------------------------------------------------------------------

@entry_metrics_api_bp.route('/entry-metrics/chart-data', methods=['GET'])
def get_chart_data():
    """
    Return multi-series chart data for one or more metrics across a set of entries.

    Query parameters
    ----------------
    metric_ids      : comma-separated metric IDs  (required)
    search_id       : ID of a SavedSearch to scope entries  (optional; OR use entry_ids)
    entry_ids       : comma-separated entry IDs  (optional)
    time_range      : 1d | 7d | 30d | 90d | 365d | all  (default: all)
    x_axis_type     : recorded_at | entry_field | custom_column  (default: recorded_at)
    x_axis_field    : Entry field name when x_axis_type=entry_field
                      (commenced_at | created_at | intended_end_date | actual_end_date)
    x_axis_custom_column_id : CustomColumn.id when x_axis_type=custom_column

    Response
    --------
    {
      "series": [
        {
          "metric_id": 1, "label": "ABV", "unit": "%", "color": "#4bc0c0",
          "data_points": [
            {"x": "<ISO timestamp or date string>", "y": 5.2,
             "entry_id": 10, "entry_title": "Batch 1", "notes": null}
          ]
        }
      ],
      "x_axis_type": "recorded_at",
      "x_axis_label": "Time"
    }
    """
    # --- parse params ---
    metric_ids_raw = request.args.get('metric_ids', '')
    try:
        metric_ids = [int(x) for x in metric_ids_raw.split(',') if x.strip()]
    except ValueError:
        return jsonify({'error': 'metric_ids must be comma-separated integers'}), 400

    if not metric_ids:
        return jsonify({'error': 'metric_ids is required'}), 400

    search_id = request.args.get('search_id', type=int)
    entry_ids_raw = request.args.get('entry_ids', '')
    time_range = request.args.get('time_range', 'all')
    x_axis_type = request.args.get('x_axis_type', 'recorded_at')
    x_axis_field = request.args.get('x_axis_field', 'commenced_at')
    x_axis_custom_column_id = request.args.get('x_axis_custom_column_id', type=int)

    VALID_ENTRY_FIELDS = {'commenced_at', 'created_at', 'intended_end_date', 'actual_end_date'}
    if x_axis_type == 'entry_field' and x_axis_field not in VALID_ENTRY_FIELDS:
        return jsonify({'error': f'x_axis_field must be one of: {", ".join(sorted(VALID_ENTRY_FIELDS))}'}), 400

    try:
        conn = get_db()
        cursor = conn.cursor()

        # --- resolve entry IDs ---
        entry_ids = []
        if search_id:
            from ..services.dashboard_service import DashboardService
            search_data = DashboardService.get_saved_search_entries(search_id, ignore_limit=True)
            entry_ids = [e['id'] for e in search_data.get('entries', [])]
        elif entry_ids_raw:
            try:
                entry_ids = [int(x) for x in entry_ids_raw.split(',') if x.strip()]
            except ValueError:
                return jsonify({'error': 'entry_ids must be comma-separated integers'}), 400

        if not entry_ids:
            # No scope restriction – use all entries that have data for these metrics
            cursor.execute(
                'SELECT DISTINCT entry_id FROM EntryDataPoint WHERE metric_id IN ({})'.format(
                    ','.join('?' * len(metric_ids))
                ),
                metric_ids,
            )
            entry_ids = [r['entry_id'] for r in cursor.fetchall()]

        if not entry_ids:
            return jsonify({'series': [], 'x_axis_type': x_axis_type, 'x_axis_label': _x_axis_label(x_axis_type, x_axis_field)}), 200

        # --- fetch metrics ---
        ph = ','.join('?' * len(metric_ids))
        cursor.execute(f'SELECT * FROM EntryMetric WHERE id IN ({ph}) ORDER BY display_order ASC, label ASC', metric_ids)
        metrics = {r['id']: r for r in cursor.fetchall()}

        # --- build series ---
        tf = _time_filter_dt(time_range)
        entry_ph = ','.join('?' * len(entry_ids))

        series = []
        for mid in metric_ids:
            metric = metrics.get(mid)
            if not metric:
                continue

            if x_axis_type == 'recorded_at':
                # Time-series: every data point plotted at its recorded_at timestamp
                query = f'''
                    SELECT edp.entry_id, edp.value, edp.recorded_at, edp.notes,
                           e.title AS entry_title
                    FROM EntryDataPoint edp
                    JOIN Entry e ON e.id = edp.entry_id
                    WHERE edp.metric_id = ? AND edp.entry_id IN ({entry_ph})
                '''
                params = [mid] + entry_ids
                if tf:
                    query += ' AND edp.recorded_at >= ?'
                    params.append(tf)
                query += ' ORDER BY edp.recorded_at ASC'
                cursor.execute(query, params)
                rows = cursor.fetchall()
                data_points = [
                    {
                        'x': r['recorded_at'],
                        'y': r['value'],
                        'entry_id': r['entry_id'],
                        'entry_title': r['entry_title'],
                        'notes': r['notes'],
                    }
                    for r in rows
                ]

            elif x_axis_type == 'entry_field':
                # One aggregated data point per entry; x = a date field on the entry
                query = f'''
                    SELECT edp.entry_id,
                           AVG(edp.value) AS value,
                           e.{x_axis_field} AS x_value,
                           e.title AS entry_title
                    FROM EntryDataPoint edp
                    JOIN Entry e ON e.id = edp.entry_id
                    WHERE edp.metric_id = ? AND edp.entry_id IN ({entry_ph})
                      AND e.{x_axis_field} IS NOT NULL
                    GROUP BY edp.entry_id
                    ORDER BY e.{x_axis_field} ASC
                '''
                params = [mid] + entry_ids
                cursor.execute(query, params)
                rows = cursor.fetchall()
                data_points = [
                    {
                        'x': r['x_value'],
                        'y': round(r['value'], 4),
                        'entry_id': r['entry_id'],
                        'entry_title': r['entry_title'],
                        'notes': None,
                    }
                    for r in rows
                ]

            elif x_axis_type == 'custom_column':
                if not x_axis_custom_column_id:
                    data_points = []
                else:
                    query = f'''
                        SELECT edp.entry_id,
                               AVG(edp.value) AS value,
                               ccv.value AS x_value,
                               e.title AS entry_title
                        FROM EntryDataPoint edp
                        JOIN Entry e ON e.id = edp.entry_id
                        JOIN CustomColumnValue ccv
                          ON ccv.entry_id = edp.entry_id
                         AND ccv.custom_column_id = ?
                        WHERE edp.metric_id = ? AND edp.entry_id IN ({entry_ph})
                          AND ccv.value IS NOT NULL
                        GROUP BY edp.entry_id
                        ORDER BY ccv.value ASC
                    '''
                    params = [x_axis_custom_column_id, mid] + entry_ids
                    cursor.execute(query, params)
                    rows = cursor.fetchall()
                    data_points = [
                        {
                            'x': r['x_value'],
                            'y': round(r['value'], 4),
                            'entry_id': r['entry_id'],
                            'entry_title': r['entry_title'],
                            'notes': None,
                        }
                        for r in rows
                    ]
            else:
                data_points = []

            series.append({
                'metric_id': mid,
                'label': metric['label'] + (f' ({metric["unit"]})' if metric['unit'] else ''),
                'unit': metric['unit'] or '',
                'color': metric['color'] or '#4bc0c0',
                'data_points': data_points,
            })

        return jsonify({
            'series': series,
            'x_axis_type': x_axis_type,
            'x_axis_label': _x_axis_label(x_axis_type, x_axis_field),
        }), 200

    except Exception as e:
        logger.error(f"Error building chart data: {e}", exc_info=True)
        return jsonify({'error': 'An internal error occurred.'}), 500


def _x_axis_label(x_axis_type, x_axis_field=None):
    if x_axis_type == 'recorded_at':
        return 'Time'
    if x_axis_type == 'entry_field':
        labels = {
            'commenced_at': 'Start Date',
            'created_at': 'Created Date',
            'intended_end_date': 'Intended End Date',
            'actual_end_date': 'Actual End Date',
        }
        return labels.get(x_axis_field, x_axis_field or 'Date')
    if x_axis_type == 'custom_column':
        return 'Custom Field'
    return 'X'
