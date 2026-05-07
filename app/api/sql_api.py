from flask import Blueprint, request, jsonify, g, current_app
import logging

# Define a Blueprint for SQL API
sql_api_bp = Blueprint('sql_api', __name__)

logger = logging.getLogger(__name__)


def get_db():
    if 'db' not in g:
        from ..db import get_connection
        g.db = get_connection()
    return g.db


def _db_type():
    """Return 'sqlite', 'postgresql', or 'mysql' based on current config."""
    from ..db import get_db_type
    return get_db_type()


# ---------------------------------------------------------------------------
# DB-agnostic introspection helpers
# ---------------------------------------------------------------------------

def _get_tables(cursor):
    """List all user-created tables for the current DB engine."""
    db = _db_type()
    if db == 'postgresql':
        cursor.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'public' AND table_type = 'BASE TABLE' "
            "ORDER BY table_name"
        )
    elif db == 'mysql':
        cursor.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = DATABASE() AND table_type = 'BASE TABLE' "
            "ORDER BY table_name"
        )
    else:  # sqlite
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    return [row[0] for row in cursor.fetchall()]


def _table_exists(cursor, table_name):
    """Return True if the table exists in the current DB."""
    db = _db_type()
    ph = '%s' if db in ('postgresql', 'mysql') else '?'
    if db == 'postgresql':
        cursor.execute(
            "SELECT table_name FROM information_schema.tables "
            f"WHERE table_schema = 'public' AND table_name = {ph}",
            (table_name,)
        )
    elif db == 'mysql':
        cursor.execute(
            "SELECT table_name FROM information_schema.tables "
            f"WHERE table_schema = DATABASE() AND table_name = {ph}",
            (table_name,)
        )
    else:
        cursor.execute(
            f"SELECT name FROM sqlite_master WHERE type='table' AND name={ph}",
            (table_name,)
        )
    return cursor.fetchone() is not None


def _get_columns(cursor, table_name):
    """Return column info list for a table, normalised across DB engines."""
    db = _db_type()
    columns = []
    if db == 'postgresql':
        cursor.execute(
            """
            SELECT
                c.column_name,
                c.data_type,
                CASE WHEN c.is_nullable = 'NO' THEN 1 ELSE 0 END,
                c.column_default,
                CASE WHEN kcu.column_name IS NOT NULL THEN 1 ELSE 0 END
            FROM information_schema.columns c
            LEFT JOIN information_schema.key_column_usage kcu
                ON kcu.table_schema = 'public'
                AND kcu.table_name  = c.table_name
                AND kcu.column_name = c.column_name
                AND kcu.constraint_name IN (
                    SELECT constraint_name
                    FROM information_schema.table_constraints
                    WHERE constraint_type = 'PRIMARY KEY'
                      AND table_schema = 'public'
                      AND table_name = %s
                )
            WHERE c.table_schema = 'public' AND c.table_name = %s
            ORDER BY c.ordinal_position
            """,
            (table_name, table_name)
        )
        for i, row in enumerate(cursor.fetchall()):
            columns.append({
                'cid': i, 'name': row[0], 'type': row[1],
                'not_null': bool(row[2]), 'default_value': row[3],
                'primary_key': bool(row[4])
            })
    elif db == 'mysql':
        cursor.execute(
            """
            SELECT
                column_name,
                column_type,
                CASE WHEN is_nullable = 'NO' THEN 1 ELSE 0 END,
                column_default,
                CASE WHEN column_key = 'PRI' THEN 1 ELSE 0 END
            FROM information_schema.columns
            WHERE table_schema = DATABASE() AND table_name = %s
            ORDER BY ordinal_position
            """,
            (table_name,)
        )
        for i, row in enumerate(cursor.fetchall()):
            columns.append({
                'cid': i, 'name': row[0], 'type': row[1],
                'not_null': bool(row[2]), 'default_value': row[3],
                'primary_key': bool(row[4])
            })
    else:  # sqlite
        cursor.execute(f"PRAGMA table_info({table_name})")
        for row in cursor.fetchall():
            columns.append({
                'cid': row[0], 'name': row[1], 'type': row[2],
                'not_null': bool(row[3]), 'default_value': row[4],
                'primary_key': bool(row[5])
            })
    return columns


def _get_foreign_keys(cursor, table_name):
    """Return foreign key info list for a table."""
    db = _db_type()
    fks = []
    if db == 'postgresql':
        cursor.execute(
            """
            SELECT
                kcu.constraint_name,
                kcu.column_name,
                ccu.table_name  AS foreign_table,
                ccu.column_name AS foreign_column,
                rc.update_rule,
                rc.delete_rule
            FROM information_schema.key_column_usage kcu
            JOIN information_schema.referential_constraints rc
                ON rc.constraint_name   = kcu.constraint_name
               AND rc.constraint_schema = 'public'
            JOIN information_schema.constraint_column_usage ccu
                ON ccu.constraint_name = rc.unique_constraint_name
            WHERE kcu.table_schema = 'public' AND kcu.table_name = %s
            """,
            (table_name,)
        )
        for i, row in enumerate(cursor.fetchall()):
            fks.append({
                'id': i, 'seq': i, 'table': row[2], 'from': row[1],
                'to': row[3], 'on_update': row[4], 'on_delete': row[5], 'match': 'NONE'
            })
    elif db == 'mysql':
        cursor.execute(
            """
            SELECT
                kcu.constraint_name,
                kcu.column_name,
                kcu.referenced_table_name,
                kcu.referenced_column_name,
                rc.update_rule,
                rc.delete_rule
            FROM information_schema.key_column_usage kcu
            JOIN information_schema.referential_constraints rc
                ON rc.constraint_name   = kcu.constraint_name
               AND rc.constraint_schema = DATABASE()
            WHERE kcu.table_schema = DATABASE()
              AND kcu.table_name   = %s
              AND kcu.referenced_table_name IS NOT NULL
            """,
            (table_name,)
        )
        for i, row in enumerate(cursor.fetchall()):
            fks.append({
                'id': i, 'seq': i, 'table': row[2], 'from': row[1],
                'to': row[3], 'on_update': row[4], 'on_delete': row[5], 'match': 'NONE'
            })
    else:  # sqlite
        cursor.execute(f"PRAGMA foreign_key_list({table_name})")
        for row in cursor.fetchall():
            fks.append({
                'id': row[0], 'seq': row[1], 'table': row[2], 'from': row[3],
                'to': row[4], 'on_update': row[5], 'on_delete': row[6], 'match': row[7]
            })
    return fks


def _get_indexes(cursor, table_name):
    """Return index info list for a table."""
    db = _db_type()
    indexes = []
    if db == 'postgresql':
        cursor.execute(
            """
            SELECT indexname,
                   CASE WHEN indexdef LIKE 'CREATE UNIQUE%%' THEN 1 ELSE 0 END
            FROM pg_indexes
            WHERE schemaname = 'public' AND tablename = %s
            """,
            (table_name,)
        )
        for i, row in enumerate(cursor.fetchall()):
            indexes.append({
                'seq': i, 'name': row[0], 'unique': bool(row[1]),
                'origin': 'c', 'partial': False
            })
    elif db == 'mysql':
        cursor.execute(f"SHOW INDEX FROM `{table_name}`")
        seen = {}
        for row in cursor.fetchall():
            name = row[2]  # Key_name column
            if name not in seen:
                seen[name] = True
                indexes.append({
                    'seq': len(indexes), 'name': name,
                    'unique': row[1] == 0, 'origin': 'c', 'partial': False
                })
    else:  # sqlite
        cursor.execute(f"PRAGMA index_list({table_name})")
        for row in cursor.fetchall():
            indexes.append({
                'seq': row[0], 'name': row[1], 'unique': bool(row[2]),
                'origin': row[3], 'partial': bool(row[4])
            })
    return indexes


def _quote_table(table_name):
    """Return a safely quoted table identifier for the current DB."""
    db = _db_type()
    if db == 'postgresql':
        return f'"{table_name}"'
    if db == 'mysql':
        return f'`{table_name}`'
    return f'[{table_name}]'  # sqlite


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@sql_api_bp.route('/execute', methods=['POST'])
def execute_sql():
    """Execute a SQL query (SELECT, INSERT, UPDATE, DELETE, DDL)."""
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({'error': 'No query provided'}), 400

        query = data['query'].strip()
        query_upper = query.upper()

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(query)

        if query_upper.startswith(('INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER')):
            conn.commit()
            return jsonify({
                'success': True,
                'message': f'Query executed successfully. {cursor.rowcount} row(s) affected.',
                'affected_rows': cursor.rowcount,
                'query_type': 'modification',
                'query': query
            })
        else:
            rows = cursor.fetchall()
            column_names = [d[0] for d in cursor.description] if cursor.description else []
            results = []
            for row in rows:
                row_dict = {}
                for i, col in enumerate(column_names):
                    val = row[i]
                    if hasattr(val, 'isoformat'):
                        val = val.isoformat()
                    row_dict[col] = val
                results.append(row_dict)
            return jsonify({
                'success': True,
                'results': results,
                'column_names': column_names,
                'row_count': len(results),
                'query_type': 'select',
                'query': query
            })

    except Exception as e:
        logger.error(f"SQL execution error: {str(e)}")
        return jsonify({
            'error': f'SQL Error: {str(e)}',
            'query_type': 'sql_error'
        }), 400


@sql_api_bp.route('/sql/tables', methods=['GET'])
def get_tables():
    """Get list of all tables and their column info."""
    try:
        conn = get_db()
        cursor = conn.cursor()
        tables = _get_tables(cursor)

        table_info = {}
        for table_name in tables:
            columns = _get_columns(cursor, table_name)
            table_info[table_name] = {
                'columns': columns,
                'column_count': len(columns)
            }

        return jsonify({'success': True, 'tables': tables, 'table_info': table_info})

    except Exception as e:
        logger.error(f"Error getting table information: {str(e)}")
        return jsonify({'error': f'Error getting table information: {str(e)}'}), 500


@sql_api_bp.route('/table/<table_name>/schema', methods=['GET'])
def get_table_schema(table_name):
    """Get detailed schema for a specific table."""
    try:
        conn = get_db()
        cursor = conn.cursor()
        return jsonify({
            'table_name': table_name,
            'columns': _get_columns(cursor, table_name),
            'foreign_keys': _get_foreign_keys(cursor, table_name),
            'indexes': _get_indexes(cursor, table_name)
        })

    except Exception as e:
        logger.error(f"Error getting table schema: {str(e)}")
        return jsonify({'error': f'Error getting schema: {str(e)}'}), 500


@sql_api_bp.route('/table/<table_name>/sample', methods=['GET'])
def get_table_sample(table_name):
    """Get up to 100 sample rows from a table."""
    try:
        conn = get_db()
        cursor = conn.cursor()

        if not _table_exists(cursor, table_name):
            return jsonify({'error': f'Table "{table_name}" does not exist'}), 404

        cursor.execute(f"SELECT * FROM {_quote_table(table_name)} LIMIT 100")
        rows = cursor.fetchall()
        column_names = [d[0] for d in cursor.description] if cursor.description else []

        results = []
        for row in rows:
            row_dict = {}
            for i, col in enumerate(column_names):
                val = row[i]
                if hasattr(val, 'isoformat'):
                    val = val.isoformat()
                row_dict[col] = val
            results.append(row_dict)

        return jsonify({
            'success': True,
            'table_name': table_name,
            'results': results,
            'column_names': column_names,
            'row_count': len(results)
        })

    except Exception as e:
        logger.error(f"Error getting table sample: {str(e)}")
        return jsonify({'error': f'Error getting table sample: {str(e)}'}), 500

