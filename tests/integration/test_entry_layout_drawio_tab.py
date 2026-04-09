#!/usr/bin/env python3
"""Regression tests for dedicated Draw.io tab behavior."""

import json
import sqlite3
from pathlib import Path

from flask import Flask

from app.services.entry_layout_service import EntryLayoutService


SCHEMA_SQL = """
CREATE TABLE EntryType (
    id INTEGER PRIMARY KEY,
    has_sensors INTEGER DEFAULT 0,
    show_labels_section INTEGER DEFAULT 0,
    show_end_dates INTEGER DEFAULT 0
);

CREATE TABLE EntryTypeLayout (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_type_id INTEGER NOT NULL,
    layout_config TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE EntryLayoutTab (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    layout_id INTEGER NOT NULL,
    tab_id TEXT NOT NULL,
    tab_label TEXT,
    tab_icon TEXT,
    display_order INTEGER DEFAULT 0,
    is_visible INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE EntryLayoutSection (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    layout_id INTEGER NOT NULL,
    section_type TEXT NOT NULL,
    title TEXT,
    position_x INTEGER DEFAULT 0,
    position_y INTEGER DEFAULT 0,
    width INTEGER DEFAULT 12,
    height INTEGER DEFAULT 2,
    is_visible INTEGER DEFAULT 1,
    is_collapsible INTEGER DEFAULT 1,
    default_collapsed INTEGER DEFAULT 0,
    config TEXT DEFAULT '{}',
    display_order INTEGER DEFAULT 0,
    tab_id TEXT DEFAULT 'main',
    tab_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


def _init_test_db(db_path: Path) -> None:
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    conn.close()


def _make_test_app(db_path: Path) -> Flask:
    app = Flask(__name__)
    app.config['DATABASE_PATH'] = str(db_path)
    return app


def test_drawio_is_hidden_from_available_section_palette():
    available_sections = EntryLayoutService.get_available_section_types()

    assert all(section['section_type'] != 'drawio' for section in available_sections)


def test_default_layout_is_limited_to_core_sections(tmp_path):
    db_path = tmp_path / 'layout_core_default.db'
    _init_test_db(db_path)

    app = _make_test_app(db_path)

    with app.app_context():
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        conn.execute(
            "INSERT INTO EntryType (id, has_sensors, show_labels_section, show_end_dates) VALUES (?, ?, ?, ?)",
            (3, 0, 0, 0),
        )
        conn.commit()
        conn.close()

        layout = EntryLayoutService.create_default_layout(3)

    section_types = {section['section_type'] for section in layout['sections']}
    assert section_types == {'header', 'notes', 'ai_assistant', 'drawio'}

    main_sections = {section['section_type'] for section in layout['sections_by_tab'].get('main', [])}
    assert main_sections == {'header', 'notes', 'ai_assistant'}

    notes_section = next(section for section in layout['sections'] if section['section_type'] == 'notes')
    ai_section = next(section for section in layout['sections'] if section['section_type'] == 'ai_assistant')
    drawio_section = next(section for section in layout['sections'] if section['section_type'] == 'drawio')

    assert (notes_section['position_x'], notes_section['position_y'], notes_section['width'], notes_section['height']) == (0, 3, 7, 5)
    assert (ai_section['position_x'], ai_section['position_y'], ai_section['width'], ai_section['height']) == (7, 3, 5, 5)
    assert (drawio_section['position_x'], drawio_section['position_y']) == (0, 0)


def test_default_layout_places_drawio_on_dedicated_tab(tmp_path):
    db_path = tmp_path / 'layout_default.db'
    _init_test_db(db_path)

    app = _make_test_app(db_path)

    with app.app_context():
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        conn.execute(
            "INSERT INTO EntryType (id, has_sensors, show_labels_section, show_end_dates) VALUES (?, ?, ?, ?)",
            (1, 0, 0, 0),
        )
        conn.commit()
        conn.close()

        layout = EntryLayoutService.create_default_layout(1)

    tab_ids = {tab['tab_id'] for tab in layout['tabs']}
    assert 'drawio' in tab_ids
    assert any(section['section_type'] == 'drawio' for section in layout['sections_by_tab'].get('drawio', []))
    assert all(section['section_type'] != 'drawio' for section in layout['sections_by_tab'].get('main', []))


def test_existing_drawio_section_is_normalized_to_drawio_tab(tmp_path):
    db_path = tmp_path / 'layout_existing.db'
    _init_test_db(db_path)

    app = _make_test_app(db_path)

    with app.app_context():
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        conn.execute(
            "INSERT INTO EntryType (id, has_sensors, show_labels_section, show_end_dates) VALUES (?, ?, ?, ?)",
            (2, 0, 0, 0),
        )
        conn.execute(
            "INSERT INTO EntryTypeLayout (id, entry_type_id, layout_config) VALUES (?, ?, ?)",
            (10, 2, json.dumps({'cols': 12, 'rowHeight': 80})),
        )
        conn.execute(
            "INSERT INTO EntryLayoutTab (layout_id, tab_id, tab_label, tab_icon, display_order, is_visible) VALUES (?, ?, ?, ?, ?, ?)",
            (10, 'main', 'Overview', 'fa-home', 0, 1),
        )
        conn.execute(
            """
            INSERT INTO EntryLayoutSection (
                layout_id, section_type, title, position_x, position_y, width, height,
                is_visible, is_collapsible, default_collapsed, config, display_order, tab_id, tab_order
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (10, 'drawio', 'Draw.io Diagram', 0, 0, 12, 6, 1, 1, 0, json.dumps({}), 1, 'main', 1),
        )
        conn.commit()
        conn.close()

        tabs = EntryLayoutService.get_tabs_for_layout(10)
        sections_by_tab = EntryLayoutService.get_sections_by_tab(10)

    drawio_tab = next(tab for tab in tabs if tab['tab_id'] == 'drawio')

    assert drawio_tab['id'] is not None
    assert any(section['section_type'] == 'drawio' for section in sections_by_tab.get('drawio', []))
    assert all(section['section_type'] != 'drawio' for section in sections_by_tab.get('main', []))

    with app.app_context():
        assert EntryLayoutService.update_tab(drawio_tab['id'], {'tab_label': 'Blueprint'}) is True
        renamed_tabs = EntryLayoutService.get_tabs_for_layout(10)

    assert next(tab for tab in renamed_tabs if tab['tab_id'] == 'drawio')['tab_label'] == 'Blueprint'
