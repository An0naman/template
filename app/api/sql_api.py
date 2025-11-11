from flask import Blueprint, request, jsonify, g, current_app
import sqlite3
import logging

# Define a Blueprint for SQL API
sql_api_bp = Blueprint('sql_api', __name__)

def get_db():
    if 'db' not in g:
        from ..db import get_connection
        g.db = get_connection()
        g.db.row_factory = sqlite3.Row
    return g.db

@sql_api_bp.route('/execute', methods=['POST'])
def execute_sql():
    """Execute SQL query - allows SELECT, INSERT, UPDATE, DELETE statements"""
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({'error': 'No query provided'}), 400
        
        query = data['query'].strip()
        
        # No security restrictions - user knows what they're doing
        query_upper = query.upper()
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Execute the query
        cursor.execute(query)
        
        # For INSERT, UPDATE, DELETE operations, commit the changes
        if query_upper.startswith(('INSERT', 'UPDATE', 'DELETE')):
            conn.commit()
            affected_rows = cursor.rowcount
            return jsonify({
                'success': True,
                'message': f'Query executed successfully. {affected_rows} row(s) affected.',
                'affected_rows': affected_rows,
                'query_type': 'modification',
                'query': query
            })
        else:
            # For SELECT queries, fetch results
            rows = cursor.fetchall()
            
            # Get column names
            column_names = [description[0] for description in cursor.description] if cursor.description else []
            
            # Convert rows to list of dictionaries for JSON serialization
            results = []
            for row in rows:
                row_dict = {}
                for i, column_name in enumerate(column_names):
                    row_dict[column_name] = row[i]
                results.append(row_dict)
            
            return jsonify({
                'success': True,
                'results': results,
                'column_names': column_names,
                'row_count': len(results),
                'query_type': 'select',
                'query': query
            })
        
    except sqlite3.Error as e:
        logging.error(f"SQL execution error: {str(e)}")
        return jsonify({
            'error': f'SQL Error: {str(e)}',
            'query_type': 'sql_error'
        }), 400
        
    except Exception as e:
        logging.error(f"Unexpected error in SQL execution: {str(e)}")
        return jsonify({
            'error': f'Unexpected error: {str(e)}',
            'query_type': 'system_error'
        }), 500

@sql_api_bp.route('/sql/tables', methods=['GET'])
def get_tables():
    """Get list of all tables in the database."""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Get all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]
        
        # Get table info for each table
        table_info = {}
        for table_name in tables:
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = []
            for column_row in cursor.fetchall():
                columns.append({
                    'name': column_row[1],
                    'type': column_row[2],
                    'not_null': bool(column_row[3]),
                    'default_value': column_row[4],
                    'primary_key': bool(column_row[5])
                })
            table_info[table_name] = {
                'columns': columns,
                'column_count': len(columns)
            }
        
        return jsonify({
            'success': True,
            'tables': tables,
            'table_info': table_info
        })
        
    except Exception as e:
        logging.error(f"Error getting table information: {str(e)}")
        return jsonify({
            'error': f'Error getting table information: {str(e)}'
        }), 500

@sql_api_bp.route('/table/<table_name>/schema', methods=['GET'])
def get_table_schema(table_name):
    """Get detailed schema information for a specific table"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Get column information
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        # Get foreign key information
        cursor.execute(f"PRAGMA foreign_key_list({table_name})")
        foreign_keys = cursor.fetchall()
        
        # Get index information
        cursor.execute(f"PRAGMA index_list({table_name})")
        indexes = cursor.fetchall()
        
        # Convert to list of dictionaries
        column_info = []
        for col in columns:
            column_info.append({
                'cid': col[0],
                'name': col[1],
                'type': col[2],
                'not_null': bool(col[3]),
                'default_value': col[4],
                'primary_key': bool(col[5])
            })
        
        foreign_key_info = []
        for fk in foreign_keys:
            foreign_key_info.append({
                'id': fk[0],
                'seq': fk[1],
                'table': fk[2],
                'from': fk[3],
                'to': fk[4],
                'on_update': fk[5],
                'on_delete': fk[6],
                'match': fk[7]
            })
        
        index_info = []
        for idx in indexes:
            index_info.append({
                'seq': idx[0],
                'name': idx[1],
                'unique': bool(idx[2]),
                'origin': idx[3],
                'partial': bool(idx[4])
            })
        
        return jsonify({
            'table_name': table_name,
            'columns': column_info,
            'foreign_keys': foreign_key_info,
            'indexes': index_info
        })
        
    except sqlite3.Error as e:
        logging.error(f"Error getting table schema: {str(e)}")
        return jsonify({'error': f'Database error: {str(e)}'}), 500
        
    except Exception as e:
        logging.error(f"Unexpected error getting table schema: {str(e)}")
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500


@sql_api_bp.route('/table/<table_name>/sample', methods=['GET'])
def get_table_sample(table_name):
    """Get a sample of data from a specific table."""
    try:
        # Validate table name to prevent SQL injection
        conn = get_db()
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        if not cursor.fetchone():
            return jsonify({'error': f'Table "{table_name}" does not exist'}), 404
        
        # Get sample data (limit to 100 rows)
        cursor.execute(f"SELECT * FROM [{table_name}] LIMIT 100")
        rows = cursor.fetchall()
        
        # Get column names
        column_names = [description[0] for description in cursor.description] if cursor.description else []
        
        # Convert to list of dictionaries
        results = []
        for row in rows:
            row_dict = {}
            for i, column_name in enumerate(column_names):
                row_dict[column_name] = row[i]
            results.append(row_dict)
        
        return jsonify({
            'success': True,
            'table_name': table_name,
            'results': results,
            'column_names': column_names,
            'row_count': len(results)
        })
        
    except Exception as e:
        logging.error(f"Error getting table sample: {str(e)}")
        return jsonify({
            'error': f'Error getting table sample: {str(e)}'
        }), 500
