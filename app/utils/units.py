"""
Unit suggestions and validation for relationships
"""

import sqlite3
import os
import logging

def get_db_connection_direct():
    """Get database connection without Flask context dependency"""
    try:
        # Try to use Flask context first
        from app.db import get_connection
        return get_connection()
    except RuntimeError:
        # Fall back to direct connection if outside Flask context
        from app.config import DATABASE_PATH
        return sqlite3.connect(DATABASE_PATH)

def get_unit_suggestions():
    """
    Returns a flat list of all active units for autocomplete
    """
    try:
        conn = get_db_connection_direct()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT name FROM units 
            WHERE is_active = 1 
            ORDER BY category, display_order, name
        """)
        
        units = [row['name'] for row in cursor.fetchall()]
        conn.close()
        
        return units
        
    except Exception as e:
        logging.error(f"Error fetching unit suggestions: {e}")
        # Fallback to basic units
        return ['g', 'kg', 'ml', 'l', 'cup', 'tbsp', 'tsp', 'pcs', 'units', 'each']

def get_unit_suggestions_by_category():
    """
    Returns units organized by category for grouped dropdown
    """
    try:
        conn = get_db_connection_direct()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT name, category FROM units 
            WHERE is_active = 1 
            ORDER BY category, display_order, name
        """)
        
        units_by_category = {}
        for row in cursor.fetchall():
            category = row['category']
            if category not in units_by_category:
                units_by_category[category] = []
            units_by_category[category].append(row['name'])
        
        conn.close()
        return units_by_category
        
    except Exception as e:
        logging.error(f"Error fetching units by category: {e}")
        # Fallback to basic categorized units
        return {
            'mass': ['g', 'kg', 'lb', 'oz'],
            'volume': ['ml', 'l', 'cup', 'tbsp', 'tsp'],
            'count': ['pcs', 'units', 'each', 'dozen']
        }

def suggest_units_for_relationship(relationship_name, from_type=None, to_type=None):
    """
    Suggest relevant units based on relationship context
    
    Args:
        relationship_name: Name of the relationship definition
        from_type: The "from" entry type label
        to_type: The "to" entry type label
    
    Returns:
        List of suggested units
    """
    try:
        # Convert to lowercase for matching
        rel_name = relationship_name.lower() if relationship_name else ""
        from_type_lower = from_type.lower() if from_type else ""
        to_type_lower = to_type.lower() if to_type else ""
        
        # Combine all text for analysis
        context = f"{rel_name} {from_type_lower} {to_type_lower}"
        
        # Get units by category from database
        units_by_category = get_unit_suggestions_by_category()
        suggestions = []
        
        # Suggest based on relationship context
        if any(word in context for word in ['ingredient', 'recipe', 'cook', 'food', 'meal']):
            suggestions.extend(units_by_category.get('mass', []))
            suggestions.extend(units_by_category.get('volume', []))
            # Add common cooking units if they exist
            cooking_units = ['cup', 'tbsp', 'tsp', 'pinch', 'dash']
            suggestions.extend([u for u in cooking_units if u in get_unit_suggestions()])
        
        elif any(word in context for word in ['component', 'part', 'assembly', 'material']):
            suggestions.extend(units_by_category.get('count', []))
            suggestions.extend(units_by_category.get('mass', []))
            suggestions.extend(units_by_category.get('length', []))
        
        elif any(word in context for word in ['batch', 'production', 'manufacturing']):
            suggestions.extend(units_by_category.get('count', []))
            suggestions.extend(units_by_category.get('mass', []))
            suggestions.extend(units_by_category.get('volume', []))
        
        elif any(word in context for word in ['chemical', 'solution', 'mixture']):
            suggestions.extend(units_by_category.get('volume', []))
            suggestions.extend(units_by_category.get('mass', []))
            suggestions.extend(units_by_category.get('percentage', []))
        
        # If no specific context found, return most common units
        if not suggestions:
            all_units = get_unit_suggestions()
            common_units = ['pcs', 'units', 'g', 'kg', 'ml', 'l', 'cup', 'each', '%']
            suggestions = [u for u in common_units if u in all_units]
        
        # Remove duplicates and return (preserves order)
        return list(dict.fromkeys(suggestions))
        
    except Exception as e:
        logging.error(f"Error getting unit suggestions for relationship: {e}")
        # Fallback to basic suggestions
        return ['pcs', 'units', 'g', 'kg', 'ml', 'l', 'cup', 'each', '%']

def format_quantity_display(quantity, unit):
    """
    Format quantity and unit for display
    
    Args:
        quantity: Numeric quantity
        unit: Unit string
    
    Returns:
        Formatted string
    """
    if not quantity:
        return unit if unit else ""
    
    if not unit:
        return str(quantity)
    
    # Format quantity to remove unnecessary decimals
    if isinstance(quantity, (int, float)):
        if quantity == int(quantity):
            quantity_str = str(int(quantity))
        else:
            quantity_str = f"{quantity:.2f}".rstrip('0').rstrip('.')
    else:
        quantity_str = str(quantity)
    
    return f"{quantity_str} {unit}"
