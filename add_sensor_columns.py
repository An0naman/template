
import sqlite3
from app import create_app

app = create_app()
with app.app_context():
    db_path = app.config['DATABASE_PATH']
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute("ALTER TABLE SensorRegistration ADD COLUMN last_temperature REAL")
        print("Added last_temperature column")
    except sqlite3.OperationalError as e:
        print(f"last_temperature column might already exist: {e}")
        
    try:
        cursor.execute("ALTER TABLE SensorRegistration ADD COLUMN last_relay_state INTEGER")
        print("Added last_relay_state column")
    except sqlite3.OperationalError as e:
        print(f"last_relay_state column might already exist: {e}")
        
    conn.commit()
    print("Migration complete")
