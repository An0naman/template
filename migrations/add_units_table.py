#!/usr/bin/env python3
"""
Migration: Add units table for maintaining unit types
"""

import sqlite3
import sys
import os

# Add the parent directory to the path so we can import the app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def migrate():
    """Add units table and populate with default units"""
    
    # Connect to database
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'template.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Create units table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS units (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                category TEXT NOT NULL,
                display_order INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Default units data
        default_units = [
            # Mass
            ('g', 'mass', 1), ('grams', 'mass', 2), ('kg', 'mass', 3), ('kilograms', 'mass', 4),
            ('lb', 'mass', 5), ('lbs', 'mass', 6), ('pounds', 'mass', 7), ('oz', 'mass', 8),
            ('ounces', 'mass', 9), ('mg', 'mass', 10), ('milligrams', 'mass', 11),
            ('tonnes', 'mass', 12), ('tons', 'mass', 13),
            
            # Volume
            ('ml', 'volume', 1), ('milliliters', 'volume', 2), ('l', 'volume', 3), ('liters', 'volume', 4),
            ('litres', 'volume', 5), ('cup', 'volume', 6), ('cups', 'volume', 7), ('tbsp', 'volume', 8),
            ('tablespoons', 'volume', 9), ('tsp', 'volume', 10), ('teaspoons', 'volume', 11),
            ('fl oz', 'volume', 12), ('fluid ounces', 'volume', 13), ('pt', 'volume', 14),
            ('pints', 'volume', 15), ('qt', 'volume', 16), ('quarts', 'volume', 17),
            ('gal', 'volume', 18), ('gallons', 'volume', 19),
            
            # Length
            ('mm', 'length', 1), ('millimeters', 'length', 2), ('cm', 'length', 3), ('centimeters', 'length', 4),
            ('m', 'length', 5), ('meters', 'length', 6), ('metres', 'length', 7), ('km', 'length', 8),
            ('kilometers', 'length', 9), ('in', 'length', 10), ('inches', 'length', 11),
            ('ft', 'length', 12), ('feet', 'length', 13), ('yd', 'length', 14), ('yards', 'length', 15),
            ('mi', 'length', 16), ('miles', 'length', 17),
            
            # Temperature
            ('°C', 'temperature', 1), ('celsius', 'temperature', 2), ('°F', 'temperature', 3),
            ('fahrenheit', 'temperature', 4), ('K', 'temperature', 5), ('kelvin', 'temperature', 6),
            
            # Time
            ('sec', 'time', 1), ('seconds', 'time', 2), ('min', 'time', 3), ('minutes', 'time', 4),
            ('hr', 'time', 5), ('hours', 'time', 6), ('day', 'time', 7), ('days', 'time', 8),
            ('week', 'time', 9), ('weeks', 'time', 10), ('month', 'time', 11), ('months', 'time', 12),
            ('year', 'time', 13), ('years', 'time', 14),
            
            # Count
            ('pcs', 'count', 1), ('pieces', 'count', 2), ('units', 'count', 3), ('items', 'count', 4),
            ('each', 'count', 5), ('dozen', 'count', 6), ('pair', 'count', 7), ('pairs', 'count', 8),
            ('set', 'count', 9), ('sets', 'count', 10), ('box', 'count', 11), ('boxes', 'count', 12),
            ('pack', 'count', 13), ('packs', 'count', 14),
            
            # Percentage
            ('%', 'percentage', 1), ('percent', 'percentage', 2), ('percentage', 'percentage', 3),
            
            # Energy
            ('J', 'energy', 1), ('joules', 'energy', 2), ('kJ', 'energy', 3), ('kilojoules', 'energy', 4),
            ('cal', 'energy', 5), ('calories', 'energy', 6), ('kcal', 'energy', 7), ('kilocalories', 'energy', 8),
            ('Wh', 'energy', 9), ('watt-hours', 'energy', 10), ('kWh', 'energy', 11), ('kilowatt-hours', 'energy', 12),
            
            # Other
            ('ratio', 'other', 1), ('parts', 'other', 2), ('drops', 'other', 3), ('pinch', 'other', 4),
            ('dash', 'other', 5), ('serving', 'other', 6), ('servings', 'other', 7), ('portion', 'other', 8),
            ('portions', 'other', 9), ('sheet', 'other', 10), ('sheets', 'other', 11)
        ]
        
        # Insert default units
        cursor.executemany('''
            INSERT OR IGNORE INTO units (name, category, display_order)
            VALUES (?, ?, ?)
        ''', default_units)
        
        conn.commit()
        print("✅ Units table created and populated with default units")
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    migrate()
