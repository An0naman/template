import sqlite3

def add_battery_columns():
    conn = sqlite3.connect('data/template.db')
    c = conn.cursor()
    
    try:
        print("Adding last_battery_pct column...")
        c.execute("ALTER TABLE SensorRegistration ADD COLUMN last_battery_pct REAL")
    except sqlite3.OperationalError:
        print("Column last_battery_pct already exists.")

    try:
        print("Adding last_battery_voltage column...")
        c.execute("ALTER TABLE SensorRegistration ADD COLUMN last_battery_voltage REAL")
    except sqlite3.OperationalError:
        print("Column last_battery_voltage already exists.")
        
    conn.commit()
    conn.close()
    print("Done.")

if __name__ == "__main__":
    add_battery_columns()
