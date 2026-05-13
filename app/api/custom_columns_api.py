# template_app/app/api/custom_columns_api.py
"""
Custom Columns API
==================
Provides CRUD for CustomColumn definitions, assignments to entry types,
and reading/writing per-entry values.

Endpoints
---------
CustomColumn definitions:
  GET    /api/custom-columns                          – list all columns
  POST   /api/custom-columns                          – create column
  GET    /api/custom-columns/<id>                     – get column
  PATCH  /api/custom-columns/<id>                     – update column
  DELETE /api/custom-columns/<id>                     – delete column

Assignments (column ↔ entry type):
  GET    /api/entry-types/<et_id>/custom-columns      – list assignments for entry type
  POST   /api/entry-types/<et_id>/custom-columns      – assign column(s) to entry type
  PATCH  /api/custom-column-assignments/<id>          – update placement / order
  DELETE /api/custom-column-assignments/<id>          – remove assignment

Values (per entry):
  GET    /api/entries/<entry_id>/custom-column-values – all values for an entry
  PUT    /api/entries/<entry_id>/custom-column-values – bulk upsert values
"""

from flask import Blueprint, request, jsonify, g
from datetime import datetime, timezone
import logging
import json
import re

custom_columns_api_bp = Blueprint('custom_columns_api', __name__)
logger = logging.getLogger(__name__)

VALID_COLUMN_TYPES = {'text', 'textarea', 'number', 'date', 'select', 'checkbox', 'url', 'email'}
# Keep `custom_columns` for backward compatibility with existing assignments.
VALID_PLACEMENTS = {'header', 'form_fields', 'custom_columns'}

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def get_db():
    if 'db' not in g:
        from ..db import get_connection
        g.db = get_connection()
    return g.db


def _slug(label: str) -> str:
    """Turn a label into a machine-safe name."""
    slug = label.lower().strip()
    slug = re.sub(r'[^a-z0-9]+', '_', slug)
    slug = re.sub(r'_+', '_', slug).strip('_')
    return slug


def _now():
    return datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')


def _has_unit_column(cursor) -> bool:
    """Return True when the CustomColumn.unit column exists."""
    try:
        cursor.execute('SELECT unit FROM CustomColumn LIMIT 1')
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# CustomColumn CRUD
# ---------------------------------------------------------------------------

@custom_columns_api_bp.route('/custom-columns', methods=['GET'])
def list_custom_columns():
    """Return all custom column definitions, optionally filtered by entry_type_id."""
    entry_type_id = request.args.get('entry_type_id', type=int)
    try:
        conn = get_db()
        cursor = conn.cursor()

        has_unit_col = _has_unit_column(cursor)
        if entry_type_id:
            if has_unit_col:
                cursor.execute('''
                      SELECT cc.id, cc.name, cc.label, cc.description, cc.column_type,
                          cc.`options` AS column_options, cc.default_value, cc.is_required,
                          cc.unit, cc.created_at, cc.updated_at,
                           cca.id AS assignment_id, cca.section_placement, cca.display_order, cca.is_visible
                    FROM CustomColumn cc
                    JOIN CustomColumnAssignment cca ON cca.custom_column_id = cc.id
                    WHERE cca.entry_type_id = ?
                    ORDER BY cca.display_order ASC, cc.label ASC
                ''', (entry_type_id,))
            else:
                cursor.execute('''
                      SELECT cc.id, cc.name, cc.label, cc.description, cc.column_type,
                          cc.`options` AS column_options, cc.default_value, cc.is_required,
                          '' AS unit, cc.created_at, cc.updated_at,
                           cca.id AS assignment_id, cca.section_placement, cca.display_order, cca.is_visible
                    FROM CustomColumn cc
                    JOIN CustomColumnAssignment cca ON cca.custom_column_id = cc.id
                    WHERE cca.entry_type_id = ?
                    ORDER BY cca.display_order ASC, cc.label ASC
                ''', (entry_type_id,))
        else:
            if has_unit_col:
                cursor.execute('''
                      SELECT id, name, label, description, column_type,
                          `options` AS column_options, default_value, is_required,
                          unit, created_at, updated_at
                    FROM CustomColumn
                    ORDER BY label ASC
                ''')
            else:
                cursor.execute('''
                      SELECT id, name, label, description, column_type,
                          `options` AS column_options, default_value, is_required,
                          '' AS unit, created_at, updated_at
                    FROM CustomColumn
                    ORDER BY label ASC
                ''')

        rows = cursor.fetchall()
        result = []
        for row in rows:
            col = {
                'id': row['id'],
                'name': row['name'],
                'label': row['label'],
                'description': row['description'],
                'column_type': row['column_type'],
                'options': json.loads(row['column_options']) if row['column_options'] else [],
                'default_value': row['default_value'],
                'is_required': bool(row['is_required']),
                'unit': row['unit'] or '',
                'created_at': row['created_at'],
                'updated_at': row['updated_at'],
            }
            if entry_type_id:
                col['assignment_id'] = row['assignment_id']
                col['section_placement'] = row['section_placement']
                col['display_order'] = row['display_order']
                col['is_visible'] = bool(row['is_visible'])
            result.append(col)
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error listing custom columns: {e}", exc_info=True)
        return jsonify({'error': 'An internal error occurred.'}), 500


@custom_columns_api_bp.route('/custom-columns', methods=['POST'])
def create_custom_column():
    """Create a new custom column definition."""
    data = request.get_json(silent=True) or {}
    label = (data.get('label') or '').strip()
    if not label:
        return jsonify({'error': 'label is required'}), 400

    column_type = data.get('column_type', 'text')
    if column_type not in VALID_COLUMN_TYPES:
        return jsonify({'error': f'column_type must be one of: {", ".join(sorted(VALID_COLUMN_TYPES))}'}), 400

    name = data.get('name') or _slug(label)
    options_raw = data.get('options', [])
    options = json.dumps(options_raw) if isinstance(options_raw, list) else '[]'

    try:
        conn = get_db()
        cursor = conn.cursor()
        now = _now()
        has_unit_col = _has_unit_column(cursor)
        if has_unit_col:
            cursor.execute('''
                INSERT INTO CustomColumn (name, label, description, column_type, `options`,
                                          default_value, is_required, unit, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                name,
                label,
                data.get('description', ''),
                column_type,
                options,
                data.get('default_value', ''),
                1 if data.get('is_required') else 0,
                data.get('unit', '') or '',
                now, now,
            ))
        else:
            cursor.execute('''
                INSERT INTO CustomColumn (name, label, description, column_type, `options`,
                                          default_value, is_required, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                name,
                label,
                data.get('description', ''),
                column_type,
                options,
                data.get('default_value', ''),
                1 if data.get('is_required') else 0,
                now, now,
            ))
        conn.commit()
        new_id = cursor.lastrowid
        return jsonify({'id': new_id, 'name': name, 'label': label}), 201
    except Exception as e:
        if 'UNIQUE' in str(e).upper():
            return jsonify({'error': f'A custom column named "{name}" already exists.'}), 409
        logger.error(f"Error creating custom column: {e}", exc_info=True)
        return jsonify({'error': 'An internal error occurred.'}), 500


@custom_columns_api_bp.route('/custom-columns/<int:column_id>', methods=['GET'])
def get_custom_column(column_id):
    try:
        conn = get_db()
        cursor = conn.cursor()
        has_unit_col = _has_unit_column(cursor)
        if has_unit_col:
            cursor.execute('''
                     SELECT id, name, label, description, column_type, `options` AS column_options,
                       default_value, is_required, unit, created_at, updated_at
                FROM CustomColumn WHERE id = ?
            ''', (column_id,))
        else:
            cursor.execute('''
                     SELECT id, name, label, description, column_type, `options` AS column_options,
                       default_value, is_required, '' AS unit, created_at, updated_at
                FROM CustomColumn WHERE id = ?
            ''', (column_id,))
        row = cursor.fetchone()
        if not row:
            return jsonify({'error': 'Not found'}), 404
        return jsonify({
            'id': row['id'],
            'name': row['name'],
            'label': row['label'],
            'description': row['description'],
            'column_type': row['column_type'],
            'options': json.loads(row['column_options']) if row['column_options'] else [],
            'default_value': row['default_value'],
            'is_required': bool(row['is_required']),
            'unit': row['unit'] or '',
            'created_at': row['created_at'],
            'updated_at': row['updated_at'],
        }), 200
    except Exception as e:
        logger.error(f"Error fetching custom column {column_id}: {e}", exc_info=True)
        return jsonify({'error': 'An internal error occurred.'}), 500


@custom_columns_api_bp.route('/custom-columns/<int:column_id>', methods=['PATCH'])
def update_custom_column(column_id):
    data = request.get_json(silent=True) or {}
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM CustomColumn WHERE id = ?', (column_id,))
        existing = cursor.fetchone()
        if not existing:
            return jsonify({'error': 'Not found'}), 404
        has_unit_col = _has_unit_column(cursor)

        column_type = data.get('column_type', existing['column_type'])
        if column_type not in VALID_COLUMN_TYPES:
            return jsonify({'error': f'column_type must be one of: {", ".join(sorted(VALID_COLUMN_TYPES))}'}), 400

        options_raw = data.get('options', None)
        options = json.dumps(options_raw) if isinstance(options_raw, list) else existing['options']

        if has_unit_col:
            cursor.execute('''
                UPDATE CustomColumn
                SET label=?, description=?, column_type=?, `options`=?,
                    default_value=?, is_required=?, unit=?, updated_at=?
                WHERE id=?
            ''', (
                data.get('label', existing['label']),
                data.get('description', existing['description']),
                column_type,
                options,
                data.get('default_value', existing['default_value']),
                1 if data.get('is_required', bool(existing['is_required'])) else 0,
                data.get('unit', existing['unit'] if 'unit' in existing.keys() else '') or '',
                _now(),
                column_id,
            ))
        else:
            cursor.execute('''
                UPDATE CustomColumn
                SET label=?, description=?, column_type=?, `options`=?,
                    default_value=?, is_required=?, updated_at=?
                WHERE id=?
            ''', (
                data.get('label', existing['label']),
                data.get('description', existing['description']),
                column_type,
                options,
                data.get('default_value', existing['default_value']),
                1 if data.get('is_required', bool(existing['is_required'])) else 0,
                _now(),
                column_id,
            ))
        conn.commit()
        return jsonify({'id': column_id, 'updated': True}), 200
    except Exception as e:
        logger.error(f"Error updating custom column {column_id}: {e}", exc_info=True)
        return jsonify({'error': 'An internal error occurred.'}), 500


@custom_columns_api_bp.route('/custom-columns/<int:column_id>', methods=['DELETE'])
def delete_custom_column(column_id):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM CustomColumn WHERE id = ?', (column_id,))
        if not cursor.fetchone():
            return jsonify({'error': 'Not found'}), 404
        # Cascade deletes assignments and values via FK
        cursor.execute('DELETE FROM CustomColumnValue WHERE custom_column_id = ?', (column_id,))
        cursor.execute('DELETE FROM CustomColumnAssignment WHERE custom_column_id = ?', (column_id,))
        cursor.execute('DELETE FROM CustomColumn WHERE id = ?', (column_id,))
        conn.commit()
        return jsonify({'deleted': True}), 200
    except Exception as e:
        logger.error(f"Error deleting custom column {column_id}: {e}", exc_info=True)
        return jsonify({'error': 'An internal error occurred.'}), 500


# ---------------------------------------------------------------------------
# Assignments
# ---------------------------------------------------------------------------

@custom_columns_api_bp.route('/entry-types/<int:entry_type_id>/custom-columns', methods=['GET'])
def list_assignments(entry_type_id):
    """List all custom column assignments for a given entry type."""
    try:
        conn = get_db()
        cursor = conn.cursor()
        has_unit_col = _has_unit_column(cursor)
        if has_unit_col:
            cursor.execute('''
                SELECT cca.id, cca.custom_column_id, cca.section_placement,
                       cca.display_order, cca.is_visible, cca.created_at,
                       cc.name, cc.label, cc.description, cc.column_type,
                       cc.`options` AS column_options, cc.default_value, cc.is_required, cc.unit
                FROM CustomColumnAssignment cca
                JOIN CustomColumn cc ON cc.id = cca.custom_column_id
                WHERE cca.entry_type_id = ?
                ORDER BY cca.display_order ASC, cc.label ASC
            ''', (entry_type_id,))
        else:
            cursor.execute('''
                SELECT cca.id, cca.custom_column_id, cca.section_placement,
                       cca.display_order, cca.is_visible, cca.created_at,
                       cc.name, cc.label, cc.description, cc.column_type,
                       cc.`options` AS column_options, cc.default_value, cc.is_required, '' AS unit
                FROM CustomColumnAssignment cca
                JOIN CustomColumn cc ON cc.id = cca.custom_column_id
                WHERE cca.entry_type_id = ?
                ORDER BY cca.display_order ASC, cc.label ASC
            ''', (entry_type_id,))
        rows = cursor.fetchall()
        result = []
        for row in rows:
            result.append({
                'id': row['id'],
                'custom_column_id': row['custom_column_id'],
                'entry_type_id': entry_type_id,
                'section_placement': row['section_placement'],
                'display_order': row['display_order'],
                'is_visible': bool(row['is_visible']),
                'created_at': row['created_at'],
                'column': {
                    'id': row['custom_column_id'],
                    'name': row['name'],
                    'label': row['label'],
                    'description': row['description'],
                    'column_type': row['column_type'],
                    'options': json.loads(row['column_options']) if row['column_options'] else [],
                    'default_value': row['default_value'],
                    'is_required': bool(row['is_required']),
                    'unit': row['unit'] or '',
                }
            })
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error listing assignments for entry type {entry_type_id}: {e}", exc_info=True)
        return jsonify({'error': 'An internal error occurred.'}), 500


@custom_columns_api_bp.route('/entry-types/<int:entry_type_id>/custom-columns', methods=['POST'])
def create_assignment(entry_type_id):
    """Assign a custom column to an entry type."""
    data = request.get_json(silent=True) or {}
    custom_column_id = data.get('custom_column_id')
    if not custom_column_id:
        return jsonify({'error': 'custom_column_id is required'}), 400

    section_placement = data.get('section_placement', 'form_fields')
    if section_placement == 'custom_columns':
        # Normalize legacy value into the currently supported section.
        section_placement = 'form_fields'
    if section_placement not in VALID_PLACEMENTS:
        return jsonify({'error': f'section_placement must be one of: {", ".join(sorted(VALID_PLACEMENTS))}'}), 400

    try:
        conn = get_db()
        cursor = conn.cursor()
        # Verify column exists
        cursor.execute('SELECT id FROM CustomColumn WHERE id = ?', (custom_column_id,))
        if not cursor.fetchone():
            return jsonify({'error': 'Custom column not found'}), 404

        display_order = data.get('display_order', 0)
        now = _now()
        cursor.execute('''
            INSERT INTO CustomColumnAssignment
                (custom_column_id, entry_type_id, section_placement, display_order, is_visible, created_at)
            VALUES (?, ?, ?, ?, 1, ?)
        ''', (custom_column_id, entry_type_id, section_placement, display_order, now))
        conn.commit()
        return jsonify({'id': cursor.lastrowid, 'created': True}), 201
    except Exception as e:
        if 'UNIQUE' in str(e).upper():
            return jsonify({'error': 'This column is already assigned to this entry type.'}), 409
        logger.error(f"Error creating assignment: {e}", exc_info=True)
        return jsonify({'error': 'An internal error occurred.'}), 500


@custom_columns_api_bp.route('/custom-column-assignments/<int:assignment_id>', methods=['PATCH'])
def update_assignment(assignment_id):
    data = request.get_json(silent=True) or {}
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM CustomColumnAssignment WHERE id = ?', (assignment_id,))
        existing = cursor.fetchone()
        if not existing:
            return jsonify({'error': 'Not found'}), 404

        section_placement = data.get('section_placement', existing['section_placement'])
        if section_placement == 'custom_columns':
            section_placement = 'form_fields'
        if section_placement not in VALID_PLACEMENTS:
            return jsonify({'error': f'section_placement must be one of: {", ".join(sorted(VALID_PLACEMENTS))}'}), 400

        cursor.execute('''
            UPDATE CustomColumnAssignment
            SET section_placement=?, display_order=?, is_visible=?
            WHERE id=?
        ''', (
            section_placement,
            data.get('display_order', existing['display_order']),
            1 if data.get('is_visible', bool(existing['is_visible'])) else 0,
            assignment_id,
        ))
        conn.commit()
        return jsonify({'id': assignment_id, 'updated': True}), 200
    except Exception as e:
        logger.error(f"Error updating assignment {assignment_id}: {e}", exc_info=True)
        return jsonify({'error': 'An internal error occurred.'}), 500


@custom_columns_api_bp.route('/custom-column-assignments/<int:assignment_id>', methods=['DELETE'])
def delete_assignment(assignment_id):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM CustomColumnAssignment WHERE id = ?', (assignment_id,))
        if not cursor.fetchone():
            return jsonify({'error': 'Not found'}), 404
        cursor.execute('DELETE FROM CustomColumnAssignment WHERE id = ?', (assignment_id,))
        conn.commit()
        return jsonify({'deleted': True}), 200
    except Exception as e:
        logger.error(f"Error deleting assignment {assignment_id}: {e}", exc_info=True)
        return jsonify({'error': 'An internal error occurred.'}), 500


# ---------------------------------------------------------------------------
# Values (per entry)
# ---------------------------------------------------------------------------

@custom_columns_api_bp.route('/entries/<int:entry_id>/custom-column-values', methods=['GET'])
def get_entry_values(entry_id):
    """Return all custom column values for an entry, merged with column metadata."""
    try:
        conn = get_db()
        cursor = conn.cursor()

        # Get the entry's type so we know which columns are assigned
        cursor.execute('SELECT entry_type_id FROM Entry WHERE id = ?', (entry_id,))
        entry_row = cursor.fetchone()
        if not entry_row:
            return jsonify({'error': 'Entry not found'}), 404
        entry_type_id = entry_row['entry_type_id']

        cursor.execute('''
            SELECT cca.id AS assignment_id, cca.section_placement, cca.display_order, cca.is_visible,
                   cc.id AS column_id, cc.name, cc.label, cc.description, cc.column_type,
                     cc.`options` AS column_options, cc.default_value, cc.is_required,
                   ccv.id AS value_id, ccv.value
            FROM CustomColumnAssignment cca
            JOIN CustomColumn cc ON cc.id = cca.custom_column_id
            LEFT JOIN CustomColumnValue ccv
                   ON ccv.custom_column_id = cc.id AND ccv.entry_id = ?
            WHERE cca.entry_type_id = ? AND cca.is_visible = 1
            ORDER BY cca.display_order ASC, cc.label ASC
        ''', (entry_id, entry_type_id))

        rows = cursor.fetchall()
        result = []
        for row in rows:
            result.append({
                'assignment_id': row['assignment_id'],
                'section_placement': row['section_placement'],
                'display_order': row['display_order'],
                'column_id': row['column_id'],
                'name': row['name'],
                'label': row['label'],
                'description': row['description'],
                'column_type': row['column_type'],
                'options': json.loads(row['column_options']) if row['column_options'] else [],
                'default_value': row['default_value'],
                'is_required': bool(row['is_required']),
                'value_id': row['value_id'],
                'value': row['value'],
            })
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error fetching custom column values for entry {entry_id}: {e}", exc_info=True)
        return jsonify({'error': 'An internal error occurred.'}), 500


@custom_columns_api_bp.route('/entries/<int:entry_id>/custom-column-values', methods=['PUT'])
def upsert_entry_values(entry_id):
    """
    Bulk upsert custom column values for an entry.
    Body: [{"column_id": 1, "value": "some text"}, ...]
    """
    items = request.get_json(silent=True)
    if not isinstance(items, list):
        return jsonify({'error': 'Expected a JSON array of {column_id, value} objects'}), 400
    try:
        conn = get_db()
        cursor = conn.cursor()
        # Verify entry exists
        cursor.execute('SELECT id FROM Entry WHERE id = ?', (entry_id,))
        if not cursor.fetchone():
            return jsonify({'error': 'Entry not found'}), 404

        now = _now()
        for item in items:
            column_id = item.get('column_id')
            value = item.get('value', '')
            if not column_id:
                continue
            # Use INSERT OR REPLACE for SQLite / REPLACE INTO for MySQL
            # (db.py's _MySQLCursorWrapper rewrites INSERT OR REPLACE → REPLACE INTO)
            cursor.execute('''
                INSERT OR REPLACE INTO CustomColumnValue
                    (entry_id, custom_column_id, value, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (entry_id, column_id, value, now, now))

        conn.commit()
        return jsonify({'saved': True}), 200
    except Exception as e:
        logger.error(f"Error upserting custom column values for entry {entry_id}: {e}", exc_info=True)
        return jsonify({'error': 'An internal error occurred.'}), 500
