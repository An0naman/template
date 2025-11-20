#!/usr/bin/env python3
from app import create_app
from app.db import init_db

app = create_app()
with app.app_context():
    init_db()
    print('✅ Database initialized via Flask app context')
