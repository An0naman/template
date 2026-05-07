#!/usr/bin/env python3
"""
migrate_to_mariadb.py
Migrates an app's SQLite database to a MariaDB database.

Usage:
    python scripts/migrate_to_mariadb.py \
        --sqlite /home/an0naman/apps/recipes/data/template.db \
        --mariadb mysql://appuser:password@100.84.208.29:3306/recipes

Run this once per app. After migration, add DATABASE_URL to the app's docker-compose.yml.
The script creates the MariaDB database and user if you provide --root-url.
"""

import argparse
import sqlite3
import sys
import re
from urllib.parse import urlparse

try:
    import pymysql
    import pymysql.cursors
except ImportError:
    sys.exit("PyMySQL not installed. Run: pip install PyMySQL")


def sqlite_connect(path):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def mysql_connect(url):
    p = urlparse(url)
    conn = pymysql.connect(
        host=p.hostname,
        port=p.port or 3306,
        user=p.username,
        password=p.password,
        database=p.path.lstrip('/'),
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
    )
    return conn


def adapt_ddl(sql):
    """Convert SQLite DDL to MariaDB DDL."""
    sql = sql.replace('AUTOINCREMENT', 'AUTO_INCREMENT')
    # Strip inline SQL comments (-- comment) which confuse MySQL parser
    sql = re.sub(r'--[^\n]*', '', sql)
    # Convert DEFAULT "x" → DEFAULT 'x' (string literals) before touching other quotes
    sql = re.sub(r'DEFAULT "([^"]*)"', r"DEFAULT '\1'", sql)
    # Convert double-quoted identifiers → backtick-quoted (SQLite → MySQL)
    sql = re.sub(r'"([A-Za-z_][A-Za-z0-9_]*)"', r'`\1`', sql)
    # Remove inline CHECK(...) from column definitions (handles one level of nested parens)
    sql = re.sub(r'\s+CHECK\s*\((?:[^()]*|\([^()]*\))*\)', '', sql, flags=re.IGNORECASE)
    # Remove standalone FOREIGN KEY lines (line-based, preserves previous line's comma)
    lines = sql.split('\n')
    filtered = [line for line in lines if not line.upper().strip().startswith('FOREIGN KEY')]
    sql = '\n'.join(filtered)
    # Clean up any trailing commas before the closing paren (left over after FK removal)
    sql = re.sub(r',(\s*\))', r'\1', sql)
    return sql


def get_tables(sqlite_conn):
    cur = sqlite_conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")
    return [row[0] for row in cur.fetchall()]


def get_create_statement(sqlite_conn, table):
    cur = sqlite_conn.cursor()
    cur.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (table,))
    row = cur.fetchone()
    return row[0] if row else None


def get_rows(sqlite_conn, table):
    cur = sqlite_conn.cursor()
    cur.execute(f"SELECT * FROM `{table}`")
    return cur.fetchall()


def create_database(root_url, db_name, app_user, app_password):
    """Create the database and a dedicated user (requires root access)."""
    p = urlparse(root_url)
    conn = pymysql.connect(
        host=p.hostname,
        port=p.port or 3306,
        user=p.username,
        password=p.password,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
    )
    with conn.cursor() as cur:
        cur.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        cur.execute(f"CREATE USER IF NOT EXISTS '{app_user}'@'%' IDENTIFIED BY '{app_password}'")
        cur.execute(f"GRANT ALL PRIVILEGES ON `{db_name}`.* TO '{app_user}'@'%'")
        cur.execute("FLUSH PRIVILEGES")
    conn.close()
    print(f"Created database `{db_name}` and user `{app_user}`")


def migrate_table(sqlite_conn, mysql_conn, table, verbose=True):
    ddl = get_create_statement(sqlite_conn, table)
    if not ddl:
        print(f"  [skip] No DDL found for {table}")
        return

    ddl = adapt_ddl(ddl)

    with mysql_conn.cursor() as cur:
        # Drop and recreate (migration is destructive — run on fresh DB only)
        cur.execute(f"DROP TABLE IF EXISTS `{table}`")
        try:
            cur.execute(ddl)
        except Exception as e:
            print(f"  [error] Creating {table}: {e}")
            print(f"  DDL was:\n{ddl}\n")
            raise

    rows = get_rows(sqlite_conn, table)
    if not rows:
        if verbose:
            print(f"  {table}: 0 rows")
        return

    # Build INSERT from first row's keys
    cols = list(rows[0].keys())
    placeholders = ', '.join(['%s'] * len(cols))
    col_names = ', '.join(f'`{c}`' for c in cols)
    insert_sql = f"INSERT INTO `{table}` ({col_names}) VALUES ({placeholders})"

    batch = [[row[c] for c in cols] for row in rows]
    with mysql_conn.cursor() as cur:
        cur.executemany(insert_sql, batch)
    mysql_conn.commit()

    if verbose:
        print(f"  {table}: {len(rows)} rows migrated")


def main():
    parser = argparse.ArgumentParser(description='Migrate SQLite → MariaDB')
    parser.add_argument('--sqlite', required=True, help='Path to SQLite .db file')
    parser.add_argument('--mariadb', required=True, help='MariaDB URL: mysql://user:pass@host:port/dbname')
    parser.add_argument('--root-url', help='MariaDB root URL to create DB/user (optional)')
    parser.add_argument('--app-user', default='appuser', help='App DB username to create (with --root-url)')
    parser.add_argument('--app-password', default='', help='App DB password (with --root-url)')
    parser.add_argument('--tables', nargs='*', help='Only migrate specific tables (default: all)')
    args = parser.parse_args()

    parsed = urlparse(args.mariadb)
    db_name = parsed.path.lstrip('/')

    if args.root_url:
        create_database(args.root_url, db_name, args.app_user, args.app_password)

    print(f"\nConnecting to SQLite: {args.sqlite}")
    sqlite_conn = sqlite_connect(args.sqlite)

    print(f"Connecting to MariaDB: {parsed.hostname}/{db_name}")
    mysql_conn = mysql_connect(args.mariadb)

    tables = args.tables or get_tables(sqlite_conn)
    print(f"\nMigrating {len(tables)} tables:\n")

    # Disable FK checks during migration to avoid ordering issues
    with mysql_conn.cursor() as cur:
        cur.execute("SET FOREIGN_KEY_CHECKS = 0")

    errors = []
    for table in tables:
        try:
            migrate_table(sqlite_conn, mysql_conn, table)
        except Exception as e:
            errors.append((table, str(e)))

    with mysql_conn.cursor() as cur:
        cur.execute("SET FOREIGN_KEY_CHECKS = 1")

    sqlite_conn.close()
    mysql_conn.close()

    if errors:
        print(f"\n{len(errors)} table(s) failed:")
        for t, e in errors:
            print(f"  {t}: {e}")
        sys.exit(1)
    else:
        print(f"\nMigration complete. Add to your app's docker-compose.yml:")
        print(f"  DATABASE_URL: {args.mariadb}")


if __name__ == '__main__':
    main()
