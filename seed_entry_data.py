#!/usr/bin/env python3
"""
Seed script — Brewing showcase data for the Entry Data Points feature.

Creates:
  • 2 EntryTypes  (Brewing Recipe, Brewing Batch)
  • 4 Entries     (1 recipe + 3 batches)
  • 1 RelationshipDefinition + 3 EntryRelationships
  • 3 EntryMetrics (Temperature, Gravity, pH)
  • 72 EntryDataPoints (3 batches × 3 metrics × 8 daily readings)

Usage:
    python seed_entry_data.py          # seed / re-seed (safe to re-run)
    python seed_entry_data.py --wipe   # remove all seeded data and exit
"""

import os, sys, argparse
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.db import get_connection
from flask import current_app

# ─── Mock readings ─────────────────────────────────────────────────────────────

# 8 daily readings per batch per metric
TEMPS = {
    40: [19.9, 20.1, 19.8, 20.0, 19.7, 19.5, 19.3, 19.1],
    41: [17.8, 17.5, 17.3, 17.6, 17.4, 17.2, 17.0, 16.9],
    42: [18.4, 18.1, 17.9, 18.2, 18.0, 17.8, 17.6, 17.5],
}
GRAVITIES = {
    40: [1.054, 1.044, 1.036, 1.029, 1.023, 1.018, 1.015, 1.013],
    41: [1.050, 1.040, 1.033, 1.027, 1.021, 1.017, 1.014, 1.012],
    42: [1.052, 1.042, 1.035, 1.028, 1.022, 1.018, 1.015, 1.013],
}
PH = {
    40: [5.5, 5.4, 5.4, 5.3, 5.3, 5.2, 5.2, 5.1],
    41: [5.3, 5.2, 5.2, 5.1, 5.1, 5.0, 5.0, 4.9],
    42: [5.4, 5.3, 5.3, 5.2, 5.2, 5.1, 5.1, 5.0],
}

def _days_ago(n):
    return (datetime.now() - timedelta(days=n)).strftime('%Y-%m-%d 10:00:00')

BATCH_META = {
    40: {'status': 'complete', 'started': _days_ago(27)},
    41: {'status': 'complete', 'started': _days_ago(20)},
    42: {'status': 'active',   'started': _days_ago(12)},
}

# Custom column values — one row per batch
# Keys match the column `name` field we seed below
BATCH_CUSTOM = {
    40: {
        'brew_batch_size':     23.0,
        'brew_og':             1.054,
        'brew_fg':             1.013,
        'brew_abv':            5.4,
        'brew_ibu':            38.0,
        'brew_efficiency':     76.0,
        'brew_boil_time':      60.0,
    },
    41: {
        'brew_batch_size':     20.0,
        'brew_og':             1.050,
        'brew_fg':             1.012,
        'brew_abv':            5.0,
        'brew_ibu':            36.0,
        'brew_efficiency':     74.0,
        'brew_boil_time':      60.0,
    },
    42: {
        'brew_batch_size':     23.0,
        'brew_og':             1.052,
        'brew_fg':             1.013,   # estimated — batch still active
        'brew_abv':            5.1,
        'brew_ibu':            37.0,
        'brew_efficiency':     75.0,
        'brew_boil_time':      60.0,
    },
}

# Sample readings per batch — 6 samples at day 0, 2, 4, 6, 8, 10 of fermentation
SAMPLE_DAYS = [0, 2, 4, 6, 8, 10]

SAMPLE_DATA = {
    'sample_gravity': {
        40: [1.054, 1.042, 1.031, 1.022, 1.016, 1.013],
        41: [1.050, 1.038, 1.028, 1.020, 1.015, 1.012],
        42: [1.052, 1.040, 1.030, 1.021, 1.018, 1.016],
    },
    'sample_ph': {
        40: [5.5, 5.4, 5.3, 5.3, 5.2, 5.1],
        41: [5.3, 5.2, 5.2, 5.1, 5.0, 5.0],
        42: [5.4, 5.3, 5.3, 5.2, 5.1, 5.0],
    },
    'sample_temp': {
        40: [19.9, 20.0, 19.8, 19.6, 19.4, 19.2],
        41: [17.8, 17.6, 17.4, 17.2, 17.1, 16.9],
        42: [18.4, 18.2, 18.0, 17.9, 17.7, 17.5],
    },
}

# Custom column defs for Brewing Sample entries: (name, label, unit)
SAMPLE_COLUMN_DEFS = [
    ('sample_gravity', 'Gravity',     'SG'),
    ('sample_ph',      'pH',          ''),
    ('sample_temp',    'Temperature', '°C'),
]

# Column definitions: (name, label, unit)
BATCH_COLUMN_DEFS = [
    ('brew_batch_size',  'Batch Size',        'L'),
    ('brew_og',          'Original Gravity',  'SG'),
    ('brew_fg',          'Final Gravity',     'SG'),
    ('brew_abv',         'ABV',               '%'),
    ('brew_ibu',         'IBU',               'IBU'),
    ('brew_efficiency',  'Mash Efficiency',   '%'),
    ('brew_boil_time',   'Boil Time',         'min'),
]

# Default states to create for new entry types (name → color)
DEFAULT_STATES = [
    ('planning',    '#6c757d'),
    ('active',      '#198754'),
    ('fermenting',  '#0d6efd'),
    ('conditioning','#6f42c1'),
    ('complete',    '#adb5bd'),
    ('archived',    '#495057'),
]


# ─── Helpers ───────────────────────────────────────────────────────────────────

def row_id(row):
    """Return the 'id' field from a pymysql.Row or a dict (MySQL DictCursor)."""
    if hasattr(row, 'keys'):        # pymysql.Row
        return row['id']
    if isinstance(row, dict):       # pymysql DictCursor
        return row['id']
    return row[0]                   # fallback: positional


def q(is_mysql):
    """SQL placeholder for this backend."""
    return '%s' if is_mysql else '?'


def ii(is_mysql):
    """INSERT-or-ignore keyword for this backend."""
    return 'INSERT IGNORE' if is_mysql else 'INSERT OR IGNORE'


# ─── Per-table upsert helpers ───────────────────────────────────────────────────

def upsert_entry_type(cur, ph, ign, name, singular, plural):
    cur.execute(
        f"{ign} INTO EntryType (name, singular_label, plural_label, is_primary) "
        f"VALUES ({ph},{ph},{ph},1)",
        (name, singular, plural),
    )
    cur.execute(f"SELECT id FROM EntryType WHERE name = {ph}", (name,))
    return row_id(cur.fetchone())


def ensure_entry_states(cur, ph, ign, type_id, states):
    for name, color in states:
        cur.execute(
            f"{ign} INTO EntryState (entry_type_id, name, color) VALUES ({ph},{ph},{ph})",
            (type_id, name, color),
        )


def upsert_rel_def(cur, ph, ign, from_type_id, to_type_id):
    name = 'Cascade Pale Ale Recipe → Batch'
    cur.execute(
        f"{ign} INTO RelationshipDefinition "
        f"(name, description, entry_type_id_from, entry_type_id_to, "
        f" cardinality_from, cardinality_to, label_from_side, label_to_side) "
        f"VALUES ({ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph})",
        (
            name,
            'Links a Cascade Pale Ale recipe to its brewing batches',
            from_type_id, to_type_id,
            'one', 'many',
            'made into batches', 'based on recipe',
        ),
    )
    cur.execute(f"SELECT id FROM RelationshipDefinition WHERE name = {ph}", (name,))
    return row_id(cur.fetchone())


def get_or_create_entry(cur, ph, ign, title, type_id, status, created_at):
    cur.execute(
        f"SELECT id FROM Entry WHERE title = {ph} AND entry_type_id = {ph}",
        (title, type_id),
    )
    row = cur.fetchone()
    if row:
        return row_id(row)
    cur.execute(
        f"INSERT INTO Entry (title, entry_type_id, status, created_at) "
        f"VALUES ({ph},{ph},{ph},{ph})",
        (title, type_id, status, created_at),
    )
    cur.execute(
        f"SELECT id FROM Entry WHERE title = {ph} AND entry_type_id = {ph}",
        (title, type_id),
    )
    return row_id(cur.fetchone())


def upsert_relationship(cur, ph, ign, source_id, target_id, rel_type_id):
    cur.execute(
        f"{ign} INTO EntryRelationship "
        f"(source_entry_id, target_entry_id, relationship_type) "
        f"VALUES ({ph},{ph},{ph})",
        (source_id, target_id, rel_type_id),
    )


def upsert_custom_column(cur, ph, ign, name, label, unit):
    cur.execute(
        f"{ign} INTO CustomColumn (name, label, column_type, unit) "
        f"VALUES ({ph},{ph},{ph},{ph})",
        (name, label, 'number', unit),
    )
    cur.execute(f"SELECT id FROM CustomColumn WHERE name = {ph}", (name,))
    return row_id(cur.fetchone())


def assign_custom_column(cur, ph, ign, col_id, type_id, order_):
    cur.execute(
        f"{ign} INTO CustomColumnAssignment "
        f"(custom_column_id, entry_type_id, section_placement, display_order, is_visible) "
        f"VALUES ({ph},{ph},{ph},{ph},{ph})",
        (col_id, type_id, 'form_fields', order_, 1),
    )


def upsert_metric(cur, ph, ign, name, label, unit, color, type_id, order_):
    cur.execute(
        f"{ign} INTO EntryMetric "
        f"(name, label, unit, color, entry_type_id, display_order) "
        f"VALUES ({ph},{ph},{ph},{ph},{ph},{ph})",
        (name, label, unit, color, type_id, order_),
    )
    cur.execute(f"SELECT id FROM EntryMetric WHERE name = {ph}", (name,))
    return row_id(cur.fetchone())


# ─── Main seed ─────────────────────────────────────────────────────────────────

def seed(cur, ph, ign):
    # 1. Entry types
    recipe_type_id = upsert_entry_type(cur, ph, ign, 'Brewing Recipe', 'Brewing Recipe', 'Brewing Recipes')
    batch_type_id  = upsert_entry_type(cur, ph, ign, 'Brewing Batch',  'Brewing Batch',  'Brewing Batches')
    print(f"  EntryType IDs — Recipe: {recipe_type_id}, Batch: {batch_type_id}")

    # 2. Default states for both types (so status badges display correctly)
    ensure_entry_states(cur, ph, ign, recipe_type_id, [('planning','#6c757d'),('active','#198754'),('archived','#495057')])
    ensure_entry_states(cur, ph, ign, batch_type_id,  DEFAULT_STATES)
    print("  EntryState rows ensured")

    # 3. Relationship definition
    rel_def_id = upsert_rel_def(cur, ph, ign, recipe_type_id, batch_type_id)
    print(f"  RelationshipDefinition ID: {rel_def_id}")

    # 4. Entries
    recipe_id = get_or_create_entry(cur, ph, ign,
        'Cascade Pale Ale Base (Recipe)', recipe_type_id, 'active', '2026-04-01 09:00:00')

    batch_ids = {}
    for num, meta in BATCH_META.items():
        bid = get_or_create_entry(cur, ph, ign,
            f'Cascade Pale Ale — Batch #{num}',
            batch_type_id, meta['status'], meta['started'])
        batch_ids[num] = bid
    print(f"  Entry IDs — Recipe: {recipe_id}, Batches: {batch_ids}")

    # 5. Link each batch → recipe
    for bid in batch_ids.values():
        upsert_relationship(cur, ph, ign, bid, recipe_id, rel_def_id)
    print("  EntryRelationships linked")

    # 6. Metrics (scoped to Brewing Batch)
    temp_metric_id  = upsert_metric(cur, ph, ign, 'Fermentation Temperature', 'Temperature', '°C',  '#4bc0c0', batch_type_id, 0)
    grav_metric_id  = upsert_metric(cur, ph, ign, 'Fermentation Gravity',     'Gravity',     'SG',  '#ff6384', batch_type_id, 1)
    ph_metric_id    = upsert_metric(cur, ph, ign, 'Fermentation pH',          'pH',          '',    '#36a2eb', batch_type_id, 2)
    print(f"  Metric IDs — Temp: {temp_metric_id}, Gravity: {grav_metric_id}, pH: {ph_metric_id}")

    # 7. Data points — clear existing first so re-runs are idempotent
    all_batch_ids = list(batch_ids.values())
    placeholders  = ','.join([ph] * len(all_batch_ids))
    cur.execute(
        f"DELETE FROM EntryDataPoint WHERE entry_id IN ({placeholders})",
        all_batch_ids,
    )

    total = 0
    for num, bid in batch_ids.items():
        batch_start = datetime.strptime(BATCH_META[num]['started'], '%Y-%m-%d %H:%M:%S')
        for day in range(8):
            ts    = (batch_start + timedelta(days=day)).strftime('%Y-%m-%d %H:%M:%S')
            notes = 'Yeast pitched' if day == 0 else None
            for mid, readings in [
                (temp_metric_id, TEMPS[num]),
                (grav_metric_id, GRAVITIES[num]),
                (ph_metric_id,   PH[num]),
            ]:
                cur.execute(
                    f"INSERT INTO EntryDataPoint (entry_id, metric_id, value, recorded_at, notes) "
                    f"VALUES ({ph},{ph},{ph},{ph},{ph})",
                    (bid, mid, readings[day], ts, notes),
                )
                total += 1

    print(f"  Data points inserted: {total}")

    # 8. Custom columns — define + assign to Batch type
    col_ids = {}
    for order_, (name, label, unit) in enumerate(BATCH_COLUMN_DEFS):
        cid = upsert_custom_column(cur, ph, ign, name, label, unit)
        assign_custom_column(cur, ph, ign, cid, batch_type_id, order_)
        col_ids[name] = cid
    print(f"  Custom columns ensured: {list(col_ids.keys())}")

    # 9. Custom column values for each batch
    for num, bid in batch_ids.items():
        for name, value in BATCH_CUSTOM[num].items():
            cid = col_ids.get(name)
            if not cid:
                continue
            now_ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cur.execute(
                f"INSERT INTO CustomColumnValue "
                f"    (entry_id, custom_column_id, value, created_at, updated_at) "
                f"VALUES ({ph},{ph},{ph},{ph},{ph}) "
                + ("ON DUPLICATE KEY UPDATE value={ph}, updated_at={ph}".format(ph=ph) if ph == '%s'
                   else "ON CONFLICT(entry_id, custom_column_id) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at"),
                ([bid, cid, str(value), now_ts, now_ts] +
                 ([str(value), now_ts] if ph == '%s' else [])),
            )
    print(f"  Custom column values seeded for batches {list(batch_ids.keys())}")

    # 10. Brewing Sample entry type
    sample_type_id = upsert_entry_type(cur, ph, ign, 'Brewing Sample', 'Brewing Sample', 'Brewing Samples')
    ensure_entry_states(cur, ph, ign, sample_type_id, [
        ('pending',  '#6c757d'),
        ('complete', '#198754'),
    ])
    print(f"  EntryType ID — Sample: {sample_type_id}")

    # 11. RelationshipDefinition: Batch → Sample
    sample_rel_name = 'Brewing Batch → Sample'
    cur.execute(
        f"{ign} INTO RelationshipDefinition "
        f"(name, description, entry_type_id_from, entry_type_id_to, "
        f" cardinality_from, cardinality_to, label_from_side, label_to_side) "
        f"VALUES ({ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph})",
        (
            sample_rel_name,
            'Links a brewing batch to its lab sample readings',
            batch_type_id, sample_type_id,
            'one', 'many',
            'has sample readings', 'sample of batch',
        ),
    )
    cur.execute(f"SELECT id FROM RelationshipDefinition WHERE name = {ph}", (sample_rel_name,))
    sample_rel_def_id = row_id(cur.fetchone())
    print(f"  RelDef ID — Batch→Sample: {sample_rel_def_id}")

    # 12. Custom columns for Sample type
    sample_col_ids = {}
    for order_, (name, label, unit) in enumerate(SAMPLE_COLUMN_DEFS):
        cid = upsert_custom_column(cur, ph, ign, name, label, unit)
        assign_custom_column(cur, ph, ign, cid, sample_type_id, order_)
        sample_col_ids[name] = cid
    print(f"  Sample custom columns: {list(sample_col_ids.keys())}")

    # 13. Sample entries + column values
    now_dt = datetime.now()
    sample_entry_count = 0
    for num, bid in batch_ids.items():
        batch_start = datetime.strptime(BATCH_META[num]['started'], '%Y-%m-%d %H:%M:%S')
        for i, day_offset in enumerate(SAMPLE_DAYS):
            sample_dt = batch_start + timedelta(days=day_offset)
            if sample_dt > now_dt:
                break  # don’t create future readings
            created_at = sample_dt.strftime('%Y-%m-%d %H:%M:%S')
            title = f'Batch #{num} — Sample {i + 1}'
            rid = get_or_create_entry(cur, ph, ign, title, sample_type_id, 'complete', created_at)
            upsert_relationship(cur, ph, ign, bid, rid, sample_rel_def_id)
            now_ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            for col_name, by_batch in SAMPLE_DATA.items():
                cid = sample_col_ids.get(col_name)
                if cid is None:
                    continue
                val = str(by_batch[num][i])
                cur.execute(
                    f"INSERT INTO CustomColumnValue "
                    f"    (entry_id, custom_column_id, value, created_at, updated_at) "
                    f"VALUES ({ph},{ph},{ph},{ph},{ph}) "
                    + ("ON DUPLICATE KEY UPDATE value={ph}, updated_at={ph}".format(ph=ph) if ph == '%s'
                       else "ON CONFLICT(entry_id, custom_column_id) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at"),
                    ([rid, cid, val, now_ts, now_ts] +
                     ([val, now_ts] if ph == '%s' else [])),
                )
            sample_entry_count += 1
    print(f"  Brewing Sample entries seeded: {sample_entry_count}")


# ─── Wipe ──────────────────────────────────────────────────────────────────────

def wipe(cur, ph):
    titles = [
        'Cascade Pale Ale Base (Recipe)',
        'Cascade Pale Ale — Batch #40',
        'Cascade Pale Ale — Batch #41',
        'Cascade Pale Ale — Batch #42',
    ]
    for title in titles:
        cur.execute(f"SELECT id FROM Entry WHERE title = {ph}", (title,))
        row = cur.fetchone()
        if not row:
            continue
        eid = row_id(row)
        cur.execute(f"DELETE FROM EntryDataPoint WHERE entry_id = {ph}", (eid,))
        cur.execute(
            f"DELETE FROM EntryRelationship "
            f"WHERE source_entry_id = {ph} OR target_entry_id = {ph}",
            (eid, eid),
        )
        cur.execute(f"DELETE FROM Entry WHERE id = {ph}", (eid,))
        print(f"  Removed entry: {title}")

    for name in ('Fermentation Temperature', 'Fermentation Gravity', 'Fermentation pH'):
        cur.execute(f"DELETE FROM EntryMetric WHERE name = {ph}", (name,))

    # Remove custom column assignments, values, and definitions
    for name, label, unit in BATCH_COLUMN_DEFS:
        cur.execute(f"SELECT id FROM CustomColumn WHERE name = {ph}", (name,))
        row = cur.fetchone()
        if row:
            cid = row_id(row)
            cur.execute(f"DELETE FROM CustomColumnValue WHERE custom_column_id = {ph}", (cid,))
            cur.execute(f"DELETE FROM CustomColumnAssignment WHERE custom_column_id = {ph}", (cid,))
            cur.execute(f"DELETE FROM CustomColumn WHERE id = {ph}", (cid,))

    rel_name = 'Cascade Pale Ale Recipe → Batch'
    cur.execute(f"DELETE FROM RelationshipDefinition WHERE name = {ph}", (rel_name,))

    # Remove Brewing Sample entries + columns + rel def
    sample_rel_name = 'Brewing Batch → Sample'
    cur.execute(f"SELECT id FROM RelationshipDefinition WHERE name = {ph}", (sample_rel_name,))
    row = cur.fetchone()
    if row:
        srid = row_id(row)
        cur.execute(f"SELECT target_entry_id FROM EntryRelationship WHERE relationship_type = {ph}", (srid,))
        sample_ids = [row_id(r) for r in cur.fetchall()]
        for seid in sample_ids:
            cur.execute(f"DELETE FROM CustomColumnValue WHERE entry_id = {ph}", (seid,))
            cur.execute(
                f"DELETE FROM EntryRelationship "
                f"WHERE source_entry_id = {ph} OR target_entry_id = {ph}",
                (seid, seid),
            )
            cur.execute(f"DELETE FROM Entry WHERE id = {ph}", (seid,))
        cur.execute(f"DELETE FROM RelationshipDefinition WHERE id = {ph}", (srid,))
    for name, label, unit in SAMPLE_COLUMN_DEFS:
        cur.execute(f"SELECT id FROM CustomColumn WHERE name = {ph}", (name,))
        row = cur.fetchone()
        if row:
            cid = row_id(row)
            cur.execute(f"DELETE FROM CustomColumnValue WHERE custom_column_id = {ph}", (cid,))
            cur.execute(f"DELETE FROM CustomColumnAssignment WHERE custom_column_id = {ph}", (cid,))
            cur.execute(f"DELETE FROM CustomColumn WHERE id = {ph}", (cid,))
    cur.execute("DELETE FROM EntryType WHERE name = 'Brewing Sample'")

    # Leave EntryTypes in place — they may be useful to keep
    print("  Metrics + RelationshipDefinitions removed. EntryTypes kept.")


# ─── Entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='Seed Entry Data Points showcase data')
    parser.add_argument('--wipe', action='store_true', help='Remove all seeded data and exit')
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        db_url = current_app.config.get('DATABASE_URL', '')
        is_mysql = 'mysql' in db_url.lower() or 'mariadb' in db_url.lower()
        ph  = q(is_mysql)
        ign = ii(is_mysql)
        db_label = f"MariaDB ({db_url.split('@')[-1]})" if is_mysql else f"mariadb ({current_app.config.get('DATABASE_PATH')})"

        conn = get_connection()
        cur  = conn.cursor()

        if args.wipe:
            print(f"🗑  Wiping seed data from {db_label}…")
            wipe(cur, ph)
            conn.commit()
            print("✅ Done.")
            return 0

        print(f"🌱 Seeding showcase data into {db_label}…")
        seed(cur, ph, ign)
        conn.commit()

        print("\n✅ Seed complete! Open the app and try:")
        print("   📖  Entries → 'Cascade Pale Ale Base (Recipe)' → Data Points section")
        print("        → switch to 'Related Entries' to see all 3 batches plotted together")
        print("   🍺  Entries → 'Cascade Pale Ale — Batch #42' → Data Points section")
        print("        → 'This Entry' mode, 3 metrics, 8 daily readings")
        print("   📊  Dashboard → Add Widget → Entry Data Chart")
        print("        → 'Related to Entry' → search 'Cascade Pale Ale Base' → pick the recipe")
        print("        → relationship dropdown → 'Cascade Pale Ale Recipe → Batch'")

    return 0


if __name__ == '__main__':
    sys.exit(main())
