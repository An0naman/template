import sqlite3

def get_hierarchical_relations(cursor, entry_id, direction='parents'):
    """
    Get hierarchical relationships (parents or children) for a given entry.
    
    The CASE logic determines what role the OTHER entity type has:
    - If CASE returns 'Parent' for a definition, the OTHER type is the parent
    - If CASE returns 'Child' for a definition, the OTHER type is the child
    
    Args:
        cursor: Database cursor
        entry_id: ID of the entry to get relationships for
        direction: 'parents' or 'children'
    
    Returns:
        List of related entries with relationship details
    """
    
    # First get the entry's type
    cursor.execute("SELECT entry_type_id FROM Entry WHERE id = ?", [entry_id])
    entry_row = cursor.fetchone()
    if not entry_row:
        return []
    entry_type_id = entry_row['entry_type_id']
    
    if direction == 'parents':
        # Find definitions where CASE returns 'Child' (meaning this type IS a child)
        # CASE returns 'Child' when:
        # - entry_type_id_to = 9 AND hierarchy_direction = 'from_to_child'
        # - entry_type_id_to = 9 AND hierarchy_direction = 'to_from_child'
        cursor.execute('''
            SELECT 
                id,
                name,
                entry_type_id_from,
                entry_type_id_to,
                hierarchy_direction,
                label_from_side,
                label_to_side,
                CASE 
                    WHEN entry_type_id_from = ? AND hierarchy_direction = 'from_to_child' THEN 'Parent' 
                    WHEN entry_type_id_from = ? AND hierarchy_direction = 'to_from_child' THEN 'Parent' 
                    WHEN entry_type_id_to = ? AND hierarchy_direction = 'from_to_child' THEN 'Child' 
                    WHEN entry_type_id_to = ? AND hierarchy_direction = 'to_from_child' THEN 'Child' 
                    ELSE 'NA' 
                END as role
            FROM RelationshipDefinition
            WHERE is_hierarchical = 1
            AND (entry_type_id_from = ? OR entry_type_id_to = ?)
            AND (
                (entry_type_id_to = ? AND hierarchy_direction = 'from_to_child')
                OR
                (entry_type_id_to = ? AND hierarchy_direction = 'to_from_child')
            )
        ''', [entry_type_id, entry_type_id, entry_type_id, entry_type_id, entry_type_id, entry_type_id, entry_type_id, entry_type_id])
        
        parent_definitions = cursor.fetchall()
        relations = []
        
        for defn in parent_definitions:
            # Determine which side has the parent type and the appropriate label
            if defn['entry_type_id_from'] == entry_type_id:
                # Entry type is FROM, so TO is the parent
                relationship_label = defn['label_to_side']
            else:
                # Entry type is TO, so FROM is the parent
                relationship_label = defn['label_from_side']
            
            # Find all EntryRelationship records
            cursor.execute('''
                SELECT 
                    er.id as relationship_id,
                    er.source_entry_id,
                    er.target_entry_id,
                    CASE 
                        WHEN er.source_entry_id = ? THEN er.target_entry_id
                        WHEN er.target_entry_id = ? THEN er.source_entry_id
                    END as parent_id
                FROM EntryRelationship er
                WHERE er.relationship_type = ?
                AND (er.source_entry_id = ? OR er.target_entry_id = ?)
            ''', [entry_id, entry_id, defn['id'], entry_id, entry_id])
            
            relationships = cursor.fetchall()
            
            for rel in relationships:
                if not rel['parent_id']:
                    continue
                    
                cursor.execute("""
                    SELECT e.id, e.title, e.status, et.singular_label as entry_type
                    FROM Entry e
                    JOIN EntryType et ON e.entry_type_id = et.id
                    WHERE e.id = ?
                """, [rel['parent_id']])
                
                parent_entry = cursor.fetchone()
                if parent_entry:
                    relations.append({
                        'id': parent_entry['id'],
                        'title': parent_entry['title'],
                        'status': parent_entry['status'],
                        'entry_type': {
                            'label': parent_entry['entry_type'],
                            'icon': 'fas fa-link',
                            'color': '#6c757d'
                        },
                        'relationship_id': rel['relationship_id'],
                        'relationship_type': relationship_label,
                        'relationship_def_id': defn['id'],
                        'relationship_type_name': defn['name'],
                        'hierarchy_direction': defn['hierarchy_direction'],
                        'source_entry_id': rel['source_entry_id'],
                        'target_entry_id': rel['target_entry_id']
                    })
        
        return relations
        
    elif direction == 'children':
        # Find definitions where CASE returns 'Parent' (meaning this type IS a parent)
        # CASE returns 'Parent' when:
        # - entry_type_id_from = 9 AND hierarchy_direction = 'from_to_child'
        # - entry_type_id_from = 9 AND hierarchy_direction = 'to_from_child'
        cursor.execute('''
            SELECT 
                id,
                name,
                entry_type_id_from,
                entry_type_id_to,
                hierarchy_direction,
                label_from_side,
                label_to_side,
                CASE 
                    WHEN entry_type_id_from = ? AND hierarchy_direction = 'from_to_child' THEN 'Parent' 
                    WHEN entry_type_id_from = ? AND hierarchy_direction = 'to_from_child' THEN 'Parent' 
                    WHEN entry_type_id_to = ? AND hierarchy_direction = 'from_to_child' THEN 'Child' 
                    WHEN entry_type_id_to = ? AND hierarchy_direction = 'to_from_child' THEN 'Child' 
                    ELSE 'NA' 
                END as role
            FROM RelationshipDefinition
            WHERE is_hierarchical = 1
            AND (entry_type_id_from = ? OR entry_type_id_to = ?)
            AND (
                (entry_type_id_from = ? AND hierarchy_direction = 'from_to_child')
                OR
                (entry_type_id_from = ? AND hierarchy_direction = 'to_from_child')
            )
        ''', [entry_type_id, entry_type_id, entry_type_id, entry_type_id, entry_type_id, entry_type_id, entry_type_id, entry_type_id])
        
        child_definitions = cursor.fetchall()
        relations = []
        
        for defn in child_definitions:
            # Determine which side has the child type and the appropriate label
            if defn['entry_type_id_from'] == entry_type_id:
                # Entry type is FROM, so TO is the child
                relationship_label = defn['label_to_side']
            else:
                # Entry type is TO, so FROM is the child
                relationship_label = defn['label_from_side']
            
            # Find all EntryRelationship records
            cursor.execute('''
                SELECT 
                    er.id as relationship_id,
                    er.source_entry_id,
                    er.target_entry_id,
                    CASE 
                        WHEN er.source_entry_id = ? THEN er.target_entry_id
                        WHEN er.target_entry_id = ? THEN er.source_entry_id
                    END as child_id
                FROM EntryRelationship er
                WHERE er.relationship_type = ?
                AND (er.source_entry_id = ? OR er.target_entry_id = ?)
            ''', [entry_id, entry_id, defn['id'], entry_id, entry_id])
            
            relationships = cursor.fetchall()
            
            for rel in relationships:
                if not rel['child_id']:
                    continue
                    
                cursor.execute("""
                    SELECT e.id, e.title, e.status, et.singular_label as entry_type
                    FROM Entry e
                    JOIN EntryType et ON e.entry_type_id = et.id
                    WHERE e.id = ?
                """, [rel['child_id']])
                
                child_entry = cursor.fetchone()
                if child_entry:
                    relations.append({
                        'id': child_entry['id'],
                        'title': child_entry['title'],
                        'status': child_entry['status'],
                        'entry_type': {
                            'label': child_entry['entry_type'],
                            'icon': 'fas fa-link',
                            'color': '#6c757d'
                        },
                        'relationship_id': rel['relationship_id'],
                        'relationship_type': relationship_label,
                        'relationship_def_id': defn['id'],
                        'relationship_type_name': defn['name'],
                        'hierarchy_direction': defn['hierarchy_direction'],
                        'source_entry_id': rel['source_entry_id'],
                        'target_entry_id': rel['target_entry_id']
                    })
        
        return relations
    
    return []
