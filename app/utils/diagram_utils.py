"""Utility functions for processing and analyzing mxGraph diagrams"""

import xml.etree.ElementTree as ET
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)


def extract_diagram_structure(xml_str: str) -> Dict[str, Any]:
    """
    Extract a human-readable structure summary from mxGraph XML
    
    Returns a dictionary with:
    - node_count: number of nodes
    - edge_count: number of edges  
    - nodes: list of node details (id, label, style, position, size)
    - edges: list of edge details (id, label, source, target, style, exit/entry points)
    - canvas: canvas settings (grid, page size, etc)
    """
    try:
        root = ET.fromstring(xml_str)
        
        # Extract canvas settings
        model = root if root.tag == 'mxGraphModel' else root.find('.//mxGraphModel')
        canvas = {}
        if model is not None:
            canvas = {
                'grid': model.get('grid') == '1',
                'gridSize': model.get('gridSize', '10'),
                'pageWidth': model.get('pageWidth', '850'),
                'pageHeight': model.get('pageHeight', '1100'),
            }
        
        # Extract cells
        nodes = []
        edges = []
        
        for cell in root.findall('.//mxCell'):
            cell_id = cell.get('id')
            
            # Skip root cells (0 and 1)
            if cell_id in ['0', '1']:
                continue
            
            value = cell.get('value', '')
            style = cell.get('style', '')
            source = cell.get('source')
            target = cell.get('target')
            edge = cell.get('edge') == '1'
            
            # Get geometry
            geom = cell.find('mxGeometry')
            geometry = None
            if geom is not None:
                geometry = {
                    'x': geom.get('x'),
                    'y': geom.get('y'),
                    'width': geom.get('width'),
                    'height': geom.get('height'),
                }
            
            if edge or source is not None:
                # It's an edge/connection
                exit_x = cell.get('exitX')
                exit_y = cell.get('exitY')
                entry_x = cell.get('entryX')
                entry_y = cell.get('entryY')
                
                edge_info = {
                    'id': cell_id,
                    'label': value,
                    'source': source,
                    'target': target,
                    'style': style,
                    'exitX': exit_x,
                    'exitY': exit_y,
                    'entryX': entry_x,
                    'entryY': entry_y,
                }
                edges.append(edge_info)
            else:
                # It's a node/vertex
                node_info = {
                    'id': cell_id,
                    'label': value,
                    'style': style,
                    'geometry': geometry,
                }
                nodes.append(node_info)
        
        return {
            'canvas': canvas,
            'node_count': len(nodes),
            'edge_count': len(edges),
            'nodes': nodes,
            'edges': edges,
        }
        
    except Exception as e:
        logger.error(f"Error extracting diagram structure: {e}")
        return {
            'error': str(e),
            'node_count': 0,
            'edge_count': 0,
            'nodes': [],
            'edges': [],
        }


def format_diagram_summary(structure: Dict[str, Any], max_items: int = 20) -> str:
    """
    Format diagram structure as a human-readable text block for AI prompts
    """
    lines = []
    
    if 'error' in structure:
        return f"Error parsing diagram: {structure['error']}"
    
    # Canvas info
    canvas = structure.get('canvas', {})
    lines.append(f"Canvas: {canvas.get('pageWidth', '?')}x{canvas.get('pageHeight', '?')}px, grid={canvas.get('gridSize', '?')}px")
    
    # Summary counts
    lines.append(f"\nDiagram contains: {structure['node_count']} nodes, {structure['edge_count']} edges\n")
    
    # Nodes
    if structure['nodes']:
        lines.append("Nodes:")
        for node in structure['nodes'][:max_items]:
            label = node['label'] if node['label'] else '(no label)'
            geom = node['geometry'] or {}
            pos = f"at ({geom.get('x', '?')}, {geom.get('y', '?')})" if geom else ''
            size = f"size {geom.get('width', '?')}x{geom.get('height', '?')}" if geom else ''
            
            # Parse style for key attributes
            style_attrs = parse_style_string(node['style'])
            shape = style_attrs.get('shape', 'rectangle')
            fill = style_attrs.get('fillColor', '')
            
            lines.append(f"  • [{node['id']}] '{label}' - {shape} {pos} {size}")
            if fill:
                lines.append(f"    Style: fillColor={fill}, strokeColor={style_attrs.get('strokeColor', '')}")
    
    # Edges
    if structure['edges']:
        lines.append("\nEdges/Connections:")
        for edge in structure['edges'][:max_items]:
            label = edge['label'] if edge['label'] else '(no label)'
            source = edge['source'] if edge['source'] else '?'
            target = edge['target'] if edge['target'] else 'unconnected'
            
            # Parse style for color
            style_attrs = parse_style_string(edge['style'])
            color = style_attrs.get('strokeColor', '')
            edge_style = style_attrs.get('edgeStyle', 'orthogonal')
            
            exit_info = f"exit=({edge['exitX']},{edge['exitY']})" if edge.get('exitX') else ''
            entry_info = f"entry=({edge['entryX']},{edge['entryY']})" if edge.get('entryX') else ''
            
            lines.append(f"  • [{edge['id']}] '{label}': {source} → {target}")
            lines.append(f"    {edge_style}, color={color}, {exit_info} {entry_info}")
    
    return '\n'.join(lines)


def parse_style_string(style: str) -> Dict[str, str]:
    """Parse mxGraph style string into key-value pairs"""
    if not style:
        return {}
    
    attrs = {}
    for part in style.split(';'):
        if '=' in part:
            key, value = part.split('=', 1)
            attrs[key] = value
        else:
            # Style without value (like 'rounded')
            if part:
                attrs[part] = 'true'
    
    return attrs


def compare_diagrams(xml1: str, xml2: str) -> str:
    """
    Compare two diagrams and return a human-readable diff summary
    Useful for showing AI what improved in generated vs example diagrams
    """
    struct1 = extract_diagram_structure(xml1)
    struct2 = extract_diagram_structure(xml2)
    
    lines = []
    lines.append("Diagram Comparison:")
    lines.append(f"  Generated: {struct1['node_count']} nodes, {struct1['edge_count']} edges")
    lines.append(f"  Example:   {struct2['node_count']} nodes, {struct2['edge_count']} edges")
    
    # Check for key differences in edges
    if struct1['edges'] and struct2['edges']:
        gen_has_exit_points = any(e.get('exitX') for e in struct1['edges'])
        example_has_exit_points = any(e.get('exitX') for e in struct2['edges'])
        
        if not gen_has_exit_points and example_has_exit_points:
            lines.append("\n⚠ Generated diagram missing explicit exit/entry points on edges")
            lines.append("  Example uses exitX/exitY to control where wires connect to components")
    
    return '\n'.join(lines)
