# template_app/app/api/labels_api.py
from flask import Blueprint, request, jsonify, g, current_app, make_response, render_template_string, send_file
import sqlite3
import logging
import base64
from io import BytesIO
import io
import qrcode
from PIL import Image, ImageDraw, ImageFont, ImageOps
import os
from datetime import datetime
from ..db import get_system_parameters

# Define a Blueprint for Labels API
labels_api_bp = Blueprint('labels_api', __name__)

# Get a logger for this module
logger = logging.getLogger(__name__)

def get_db():
    if 'db' not in g:
        db_path = current_app.config['DATABASE_PATH']
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row
    return g.db

# Label configurations for different sheet types and Niimbot printers
LABEL_CONFIGS = {
    '8_labels': {
        'name': '8 Labels (2x4)',
        'type': 'sheet',
        'page_width_mm': 210,  # A4 width
        'page_height_mm': 297,  # A4 height
        'labels_per_row': 2,
        'labels_per_col': 4,
        'label_width_mm': 97.5,  # (210mm - 10mm margins - 5mm gap) / 2
        'label_height_mm': 65.5,  # (297mm - 20mm margins - 15mm gaps) / 4
        'margin_top_mm': 10,  # 1cm top buffer
        'margin_bottom_mm': 10,  # 1cm bottom buffer
        'margin_left_mm': 5,  # Left margin
        'margin_right_mm': 5,  # Right margin
        'gap_horizontal_mm': 5,  # 0.5cm padding between columns
        'gap_vertical_mm': 5  # 0.5cm padding between rows
    },
    '14_labels': {
        'name': '14 Labels (2x7)',
        'type': 'sheet',
        'page_width_mm': 210,  # A4 width
        'page_height_mm': 297,  # A4 height
        'labels_per_row': 2,
        'labels_per_col': 7,
        'label_width_mm': 97.5,  # (210mm - 10mm margins - 5mm gap) / 2
        'label_height_mm': 35.3,  # (297mm - 20mm margins - 30mm gaps) / 7
        'margin_top_mm': 10,  # 1cm top buffer
        'margin_bottom_mm': 10,  # 1cm bottom buffer
        'margin_left_mm': 5,  # Left margin
        'margin_right_mm': 5,  # Right margin
        'gap_horizontal_mm': 5,  # 0.5cm padding between columns
        'gap_vertical_mm': 5  # 0.5cm padding between rows
    },
    'niimbot_b1': {
        'name': 'Niimbot B1',
        'type': 'niimbot',
        'model': 'b1',
        'max_width_px': 384,  # Maximum print width in pixels (48mm @ 203 DPI)
        'dpi': 203,
        'common_sizes': {
            '30x12mm': {'width_mm': 30, 'height_mm': 12},
            '30x15mm': {'width_mm': 30, 'height_mm': 15},
            '40x20mm': {'width_mm': 40, 'height_mm': 20},
            '40x24mm': {'width_mm': 40, 'height_mm': 24},
            '60x30mm': {'width_mm': 60, 'height_mm': 30},  # Your current labels
        }
    },
    'niimbot_d110': {
        'name': 'Niimbot D110',
        'type': 'niimbot',
        'model': 'd110',
        'max_width_px': 240,  # Maximum print width in pixels (30mm @ 203 DPI = 240px)
        'dpi': 203,
        'common_sizes': {
            '30x15mm': {'width_mm': 30, 'height_mm': 15},
            '40x12mm': {'width_mm': 40, 'height_mm': 12},
            '50x14mm': {'width_mm': 50, 'height_mm': 14},
            '75x12mm': {'width_mm': 75, 'height_mm': 12},
        }
    }
}

@labels_api_bp.route('/label_configs', methods=['GET'])
def get_label_configs():
    """Get available label configurations"""
    return jsonify(LABEL_CONFIGS)

@labels_api_bp.route('/entries/<int:entry_id>/label_preview', methods=['GET'])
def preview_entry_label(entry_id):
    """Generate a preview of a label for an entry"""
    try:
        label_type = request.args.get('label_type', '8_labels')
        rotation = int(request.args.get('rotation', 0))  # 0 or 90 degrees
        
        # Force rotation to 0 for 14-label sheets (smaller labels)
        if label_type == '14_labels':
            rotation = 0
        
        # Get entry data
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT e.id, e.title, e.description, e.intended_end_date, e.actual_end_date, 
                   e.status, e.created_at, et.singular_label as entry_type_label
            FROM Entry e
            JOIN EntryType et ON e.entry_type_id = et.id
            WHERE e.id = ?
        ''', (entry_id,))
        
        entry = cursor.fetchone()
        if not entry:
            return jsonify({'error': 'Entry not found'}), 404
            
        # Get system parameters
        params = get_system_parameters()
        
        # Generate label image
        label_image = generate_single_label(dict(entry), params, label_type, rotation, for_printing=False)
        
        # Convert to base64 for preview
        img_buffer = io.BytesIO()
        label_image.save(img_buffer, format='PNG')
        img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
        
        return jsonify({
            'label_preview': f'data:image/png;base64,{img_base64}',
            'entry': dict(entry)
        })
        
    except Exception as e:
        logger.error(f"Error generating label preview: {e}", exc_info=True)
        return jsonify({'error': 'Failed to generate label preview'}), 500

@labels_api_bp.route('/entries/<int:entry_id>/print_labels', methods=['POST'])
def print_entry_labels(entry_id):
    """Generate a printable label page for an entry with multiple positions"""
    try:
        data = request.json
        label_type = data.get('label_type', '8_labels')
        positions = data.get('positions', [])  # List of positions
        rotation = data.get('rotation', 0)  # 0 or 90 degrees
        
        # Force rotation to 0 for 14-label sheets (smaller labels)
        if label_type == '14_labels':
            rotation = 0
        
        if label_type not in LABEL_CONFIGS:
            return jsonify({'error': 'Invalid label type'}), 400
            
        config = LABEL_CONFIGS[label_type]
        max_labels = config['labels_per_row'] * config['labels_per_col']
        
        if not positions:
            return jsonify({'error': 'At least one position must be specified'}), 400
            
        for position in positions:
            if position < 1 or position > max_labels:
                return jsonify({'error': f'Position {position} must be between 1 and {max_labels}'}), 400
        
        # Get entry data
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT e.id, e.title, e.description, e.intended_end_date, e.actual_end_date, 
                   e.status, e.created_at, et.singular_label as entry_type_label
            FROM Entry e
            JOIN EntryType et ON e.entry_type_id = et.id
            WHERE e.id = ?
        ''', (entry_id,))
        
        entry = cursor.fetchone()
        if not entry:
            return jsonify({'error': 'Entry not found'}), 404
            
        # Get system parameters
        params = get_system_parameters()
        
        # Generate printable page with multiple labels
        page_image = generate_multiple_labels_page(dict(entry), params, label_type, positions, rotation)
        
        # Convert to base64 for web display
        img_buffer = io.BytesIO()
        page_image.save(img_buffer, format='PNG', dpi=(300, 300))
        img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
        
        return jsonify({
            'print_page': f'data:image/png;base64,{img_base64}',
            'label_type': label_type,
            'positions': positions,
            'entry': dict(entry)
        })
        
    except Exception as e:
        logger.error(f"Error generating printable labels: {e}", exc_info=True)
        return jsonify({'error': 'Failed to generate printable labels'}), 500

@labels_api_bp.route('/entries/<int:entry_id>/labels_pdf', methods=['POST'])
def generate_labels_pdf(entry_id):
    """Generate a PDF for printing multiple labels"""
    try:
        data = request.json
        label_type = data.get('label_type', '8_labels')
        positions = data.get('positions', [])
        rotation = data.get('rotation', 0)  # 0 or 90 degrees
        
        # Force rotation to 0 for 14-label sheets (smaller labels)
        if label_type == '14_labels':
            rotation = 0
        
        # Get entry data
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT e.id, e.title, e.description, e.intended_end_date, e.actual_end_date, 
                   e.status, e.created_at, et.singular_label as entry_type_label
            FROM Entry e
            JOIN EntryType et ON e.entry_type_id = et.id
            WHERE e.id = ?
        ''', (entry_id,))
        
        entry = cursor.fetchone()
        if not entry:
            return jsonify({'error': 'Entry not found'}), 404
            
        # Get system parameters
        params = get_system_parameters()
        
        # Generate page image
        page_image = generate_multiple_labels_page(dict(entry), params, label_type, positions, rotation)
        
        # Convert to PDF
        pdf_buffer = io.BytesIO()
        page_image.save(pdf_buffer, format='PDF', resolution=300.0)
        pdf_data = pdf_buffer.getvalue()
        
        response = make_response(pdf_data)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=labels_entry_{entry_id}.pdf'
        
        return response
        
    except Exception as e:
        logger.error(f"Error generating PDF: {e}", exc_info=True)
        return jsonify({'error': 'Failed to generate PDF'}), 500
def print_entry_label(entry_id):
    """Generate a printable label page for an entry"""
    try:
        data = request.json
        label_type = data.get('label_type', '8_labels')
        position = data.get('position', 1)  # Label position on sheet (1-8 or 1-14)
        
        if label_type not in LABEL_CONFIGS:
            return jsonify({'error': 'Invalid label type'}), 400
            
        config = LABEL_CONFIGS[label_type]
        max_labels = config['labels_per_row'] * config['labels_per_col']
        
        if position < 1 or position > max_labels:
            return jsonify({'error': f'Position must be between 1 and {max_labels}'}), 400
        
        # Get entry data
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT e.id, e.title, e.description, e.intended_end_date, e.actual_end_date, 
                   e.status, e.created_at, et.singular_label as entry_type_label
            FROM Entry e
            JOIN EntryType et ON e.entry_type_id = et.id
            WHERE e.id = ?
        ''', (entry_id,))
        
        entry = cursor.fetchone()
        if not entry:
            return jsonify({'error': 'Entry not found'}), 404
            
        # Get system parameters
        params = get_system_parameters()
        
        # Generate printable page
        page_image = generate_label_page(dict(entry), params, label_type, position)
        
        # Convert to base64 for web display
        img_buffer = io.BytesIO()
        page_image.save(img_buffer, format='PNG', dpi=(300, 300))
        img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
        
        return jsonify({
            'print_page': f'data:image/png;base64,{img_base64}',
            'label_type': label_type,
            'position': position,
            'entry': dict(entry)
        })
        
    except Exception as e:
        logger.error(f"Error generating printable label: {e}", exc_info=True)
        return jsonify({'error': 'Failed to generate printable label'}), 500

def generate_single_label(entry, params, label_type, rotation=0, for_printing=False):
    """Generate a single label image with optional rotation (0 or 90 degrees)"""
    config = LABEL_CONFIGS[label_type]
    
    # Convert mm to pixels (assuming 300 DPI)
    dpi = 300
    mm_to_px = dpi / 25.4
    
    # Base label dimensions (always in standard orientation)
    base_width_px = int(config['label_width_mm'] * mm_to_px)
    base_height_px = int(config['label_height_mm'] * mm_to_px)
    
    # Determine working dimensions based on rotation
    if rotation == 90:
        # For 90-degree rotation, work in landscape mode
        work_width = base_height_px  # Swap dimensions for layout
        work_height = base_width_px
    else:
        # Normal portrait mode
        work_width = base_width_px
        work_height = base_height_px
    
    # Create image with working dimensions for layout
    img = Image.new('RGB', (work_width, work_height), 'white')
    draw = ImageDraw.Draw(img)
    
    # Determine if this is a larger label (8-label sheet has taller labels)
    is_large_label = label_type == '8_labels'
    
    # Try to load a reasonable font
    font_size = int(params.get('label_font_size', 10))
    # Convert pt to px properly at 300 DPI: 1 pt = 300/72 = 4.167 px
    # But also scale up since the font seems too small
    font_size_px = max(int(font_size * 300 / 72), 20)  # Minimum 20px
    
    logger.info(f"Font size setting: {font_size}pt -> {font_size_px}px")
    
    # Try different font paths in order of preference
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans.ttf", 
        "/system/fonts/DejaVuSans.ttf",
        "/Library/Fonts/DejaVuSans.ttf",  # macOS
        "arial.ttf",  # Windows fallback
    ]
    
    font_bold_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
        "/system/fonts/DejaVuSans-Bold.ttf", 
        "/Library/Fonts/DejaVuSans-Bold.ttf",  # macOS
        "arialbd.ttf",  # Windows fallback
    ]
    
    # Try to find working fonts
    font = None
    font_bold = None
    
    for font_path in font_paths:
        try:
            font = ImageFont.truetype(font_path, font_size_px)
            logger.info(f"Successfully loaded font: {font_path}")
            break
        except Exception:
            continue
    
    for font_path in font_bold_paths:
        try:
            font_bold = ImageFont.truetype(font_path, int(font_size_px * 1.3))
            break
        except Exception:
            continue
    
    # Fall back to default font if none found
    if font is None:
        logger.warning("Could not load any TrueType fonts, using default PIL font")
        try:
            font = ImageFont.load_default()
            font_bold = ImageFont.load_default()
        except Exception:
            # Last resort - create minimal font objects
            logger.error("Could not load any fonts, using basic fallback")
            font = None
            font_bold = None
    
    # Create font variations with better scaling for rotation
    if font is not None:
        try:
            # Adjust font sizes based on rotation and label size
            base_small_size = int(font_size_px * 0.8)
            base_tiny_size = int(font_size_px * 0.6)
            
            # For 90-degree rotation on small labels, use slightly smaller fonts
            if rotation == 90 and not is_large_label:
                base_small_size = int(font_size_px * 0.7)
                base_tiny_size = int(font_size_px * 0.5)
            
            font_small = ImageFont.truetype(font.path, base_small_size) if hasattr(font, 'path') else font
            font_title = font_bold if font_bold else font
            font_tiny = ImageFont.truetype(font.path, base_tiny_size) if hasattr(font, 'path') else font
        except Exception:
            # Use the same font for all if variations fail
            font_small = font
            font_title = font
            font_tiny = font
    else:
        # Absolute fallback
        font = font_small = font_title = font_tiny = ImageFont.load_default()
    
    # Calculate layout with better spacing
    margin = int(1.5 * mm_to_px)  # 1.5mm margin
    y_pos = margin
    
    # 1. PROJECT LOGO AND NAME (Header) - Track if logo is present
    logo_present = False
    if params.get('label_include_logo', 'true').lower() == 'true':
        logo_path = params.get('project_logo_path', '')
        project_name = params.get('project_name', 'Project')
        
        # Try to load and display logo image
        if logo_path and os.path.exists(os.path.join(current_app.root_path, logo_path.lstrip('/'))):
            try:
                logo_full_path = os.path.join(current_app.root_path, logo_path.lstrip('/'))
                logo_img = Image.open(logo_full_path)
                
                # Resize logo appropriately based on label size
                if is_large_label:
                    max_logo_width = int(work_width * 0.25)
                    max_logo_height = int(work_height * 0.18)
                else:
                    max_logo_width = int(work_width * 0.2)
                    max_logo_height = int(work_height * 0.25)
                
                # Calculate scaling to maintain aspect ratio
                logo_ratio = min(max_logo_width / logo_img.width, max_logo_height / logo_img.height)
                new_logo_size = (int(logo_img.width * logo_ratio), int(logo_img.height * logo_ratio))
                logo_img = logo_img.resize(new_logo_size, Image.Resampling.LANCZOS)
                
                # Paste logo
                img.paste(logo_img, (margin, y_pos))
                
                # Add project name next to logo
                text_x = margin + new_logo_size[0] + int(1 * mm_to_px)
                text_y = y_pos + (new_logo_size[1] // 2) - (font_size_px // 2)
                draw.text((text_x, text_y), project_name, font=font_small, fill='black')
                
                y_pos += new_logo_size[1] + int(1 * mm_to_px)
                logo_present = True
                    
            except Exception as e:
                logger.warning(f"Could not load logo image: {e}")
                # Fallback to text only
                draw.text((margin, y_pos), project_name, font=font_small, fill='black')
                y_pos += int(font_size_px * 1.2)
        else:
            # No logo, just project name
            draw.text((margin, y_pos), project_name, font=font_small, fill='black')
            y_pos += int(font_size_px * 1.2)
    
    # Add separator line only if we have logo/project name
    if params.get('label_include_logo', 'true').lower() == 'true':
        line_y = y_pos
        draw.line([(margin, line_y), (work_width - margin, line_y)], fill='lightgray', width=1)
        y_pos += int(0.5 * mm_to_px)
    
    # 2. ENTRY TITLE (Most Important - Large and Bold)
    title = entry['title']
    # Adjust title length based on label size and rotation
    if is_large_label:
        max_title_length = 50 if rotation == 90 else 40
    else:
        max_title_length = 35 if rotation == 90 else 25
        
    if len(title) > max_title_length:
        title = title[:max_title_length-3] + "..."
    draw.text((margin, y_pos), title, font=font_title, fill='black')
    y_pos += int(font_size_px * 1.4)
    
    # 3. ENTRY TYPE AND ID (Secondary identification)
    entry_type = entry['entry_type_label'] if 'entry_type_label' in entry.keys() else 'Entry'
    type_id_text = f"{entry_type} #{entry['id']}"
    draw.text((margin, y_pos), type_id_text, font=font, fill='#333333')
    y_pos += int(font_size_px * 1.2)
    
    # 4. STATUS (Only if not active)
    status = (entry['status'] if 'status' in entry.keys() else 'active').lower()
    if status != 'active':
        status_text = f"STATUS: {status.upper()}"
        status_color = 'red' if status in ['inactive', 'cancelled', 'failed'] else 'orange'
        draw.text((margin, y_pos), status_text, font=font_small, fill=status_color)
        y_pos += int(font_size_px * 1.0)
    
    # 5. DESCRIPTION (Dynamic space calculation)
    if is_large_label and entry.get('description'):
        desc = str(entry['description']).strip()
        if desc and desc.lower() not in ['none', 'null', '']:
            # Calculate QR code space and position first
            qr_space_width = 0
            qr_space_height = 0
            qr_bottom_corner_height = 0
            
            if params.get('label_include_qr_code', 'true').lower() == 'true':
                # QR code size calculation
                if is_large_label:
                    if rotation == 90:
                        qr_size = int(min(work_width * 0.2, work_height * 0.22))
                    else:
                        qr_size = int(min(work_width * 0.22, work_height * 0.25))
                else:
                    if rotation == 90:
                        qr_size = int(min(work_width * 0.22, work_height * 0.28))
                    else:
                        qr_size = int(min(work_width * 0.25, work_height * 0.3))
                
                # QR will be in bottom right corner
                qr_space_width = qr_size + margin  # QR + margin from right edge
                qr_bottom_corner_height = qr_size + margin  # Height from bottom
            
            # Calculate remaining vertical space
            remaining_height = work_height - y_pos - margin
            
            # Account for dates section (we need space for at least created date)
            date_line_height = int(font_size_px * 0.9)
            dates_needed = 1  # Always have created date
            if 'intended_end_date' in entry.keys() and entry['intended_end_date']:
                dates_needed += 1  # Add space for target date
            
            reserved_for_dates = dates_needed * date_line_height + int(0.5 * mm_to_px)  # Small buffer
            available_for_description = remaining_height - reserved_for_dates
            
            # Calculate how many lines we can fit
            line_height = int(font_size_px * 0.9)
            max_description_lines = max(1, int(available_for_description / line_height))
            
            # Calculate text width - use full width for most lines, but account for QR in bottom area
            max_width_full = work_width - 2 * margin  # Full width when no QR interference
            max_width_with_qr = work_width - 2 * margin - qr_space_width  # Reduced width when QR interferes
            
            # Calculate at what line the QR starts interfering (from the bottom)
            qr_interference_start_line = max_description_lines - int(qr_bottom_corner_height / line_height)
            
            # Word wrap the description
            words = desc.split()
            lines = []
            current_line = ""
            
            for word in words:
                test_line = current_line + (" " if current_line else "") + word
                
                # Determine which width limit to use for this line
                current_line_number = len(lines)
                if current_line_number >= qr_interference_start_line and qr_space_width > 0:
                    max_width = max_width_with_qr
                else:
                    max_width = max_width_full
                
                # Get text width using textbbox
                bbox = draw.textbbox((0, 0), test_line, font=font_small)
                text_width = bbox[2] - bbox[0]
                
                if text_width <= max_width:
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line)
                        current_line = word
                    else:
                        # Word is too long, truncate it
                        current_line = word[:max(10, int(max_width / (font_size_px * 0.6)))] + "..."
                        lines.append(current_line)
                        current_line = ""
            
            if current_line:
                lines.append(current_line)
            
            # Limit lines to available space and add ellipsis if truncated
            if len(lines) > max_description_lines:
                lines = lines[:max_description_lines]
                # Add ellipsis to the last line if we truncated
                if max_description_lines > 0:
                    last_line = lines[-1]
                    # Use the appropriate width for the last line
                    line_max_width = max_width_with_qr if (max_description_lines - 1) >= qr_interference_start_line and qr_space_width > 0 else max_width_full
                    # Make sure there's room for ellipsis
                    while len(last_line) > 5:
                        test_line = last_line[:-1] + "..."
                        bbox = draw.textbbox((0, 0), test_line, font=font_small)
                        if bbox[2] - bbox[0] <= line_max_width:
                            lines[-1] = test_line
                            break
                        last_line = last_line[:-1]
            
            # Draw each line
            for line in lines:
                draw.text((margin, y_pos), line, font=font_small, fill='#444444')
                y_pos += line_height
                
            logger.info(f"Description: used {len(lines)}/{max_description_lines} lines, QR interference starts at line {qr_interference_start_line}")
    
    # 6. DATES (Position at bottom, using remaining space)
    # Calculate where dates should start (bottom of label, working upward)
    date_line_height = int(font_size_px * 0.9)
    dates_needed = 1  # Always have created date
    if 'intended_end_date' in entry.keys() and entry['intended_end_date']:
        dates_needed += 1
    
    # Position dates at the bottom
    dates_start_y = work_height - margin - (dates_needed * date_line_height)
    
    # Make sure we don't overlap with description
    if dates_start_y < y_pos:
        dates_start_y = y_pos + int(0.3 * mm_to_px)  # Small gap after description
    
    date_y_pos = dates_start_y
    
    # Target date (if exists)
    if 'intended_end_date' in entry.keys() and entry['intended_end_date']:
        date_str = entry['intended_end_date'][:10]
        draw.text((margin, date_y_pos), f"Target: {date_str}", font=font_small, fill='#555555')
        date_y_pos += date_line_height
    
    # Created date
    created_date = entry['created_at'][:10]
    draw.text((margin, date_y_pos), f"Created: {created_date}", font=font_small, fill='#777777')
    
    # 7. QR CODE (Bottom right corner)
    if params.get('label_include_qr_code', 'true').lower() == 'true':
        # Get QR code prefix from system parameters, with fallback
        qr_prefix = params.get('label_qr_code_prefix', params.get('project_name', 'Project'))
        qr_data = f"{qr_prefix}/entry/{entry['id']}"
        
        qr = qrcode.QRCode(version=1, box_size=2, border=1)
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        qr_img = qr.make_image(fill_color="black", back_color="white")
        
        # Size QR code based on label type and rotation
        if is_large_label:
            if rotation == 90:
                qr_size = int(min(work_width * 0.2, work_height * 0.22))
            else:
                qr_size = int(min(work_width * 0.22, work_height * 0.25))
        else:
            if rotation == 90:
                qr_size = int(min(work_width * 0.22, work_height * 0.28))
            else:
                qr_size = int(min(work_width * 0.25, work_height * 0.3))
            
        qr_img = qr_img.resize((qr_size, qr_size))
        
        # Position QR code in bottom right corner
        qr_x = work_width - qr_size - margin
        qr_y = work_height - qr_size - margin
        
        img.paste(qr_img, (qr_x, qr_y))
    
    # Handle rotation for final output
    if rotation == 90:
        if for_printing:
            # For printing, we need to actually rotate the image so it appears correctly on the label sheet
            # The image was created in landscape layout, now rotate it 90 degrees clockwise
            img = img.rotate(-90, expand=True)
        else:
            # For preview, keep the landscape layout as-is to show how it will look when rotated
            pass  # Keep the image as-is - it's already in the correct rotated layout
    
    return img

def generate_multiple_labels_page(entry, params, label_type, positions, rotation=0):
    """Generate a full A4 page with labels at the specified positions"""
    config = LABEL_CONFIGS[label_type]
    
    # Convert mm to pixels (assuming 300 DPI)
    dpi = 300
    mm_to_px = dpi / 25.4
    
    page_width_px = int(config['page_width_mm'] * mm_to_px)
    page_height_px = int(config['page_height_mm'] * mm_to_px)
    
    # Create page
    page = Image.new('RGB', (page_width_px, page_height_px), 'white')
    
    # Generate the single label template - for printing, keep original dimensions
    label_template = generate_single_label(entry, params, label_type, rotation, for_printing=True)
    
    # Calculate positioning variables - labels are always positioned based on their final dimensions
    margin_left_px = int(config['margin_left_mm'] * mm_to_px)
    margin_top_px = int(config['margin_top_mm'] * mm_to_px)
    
    # Label dimensions for positioning are always based on the original label size
    # because the rotated label will be placed in the same spot as a non-rotated label
    label_width_px = int(config['label_width_mm'] * mm_to_px)
    label_height_px = int(config['label_height_mm'] * mm_to_px)
        
    gap_h_px = int(config['gap_horizontal_mm'] * mm_to_px)
    gap_v_px = int(config['gap_vertical_mm'] * mm_to_px)
    
    # Place labels at specified positions
    for position in positions:
        # Calculate row and column for this position
        row = (position - 1) // config['labels_per_row']
        col = (position - 1) % config['labels_per_row']
        
        x = margin_left_px + col * (label_width_px + gap_h_px)
        y = margin_top_px + row * (label_height_px + gap_v_px)
        
        # Paste label onto page
        page.paste(label_template, (x, y))
    
    # Draw light grid lines for reference (optional)
    draw = ImageDraw.Draw(page)
    
    # Draw light outline around all label positions for reference
    for r in range(config['labels_per_col']):
        for c in range(config['labels_per_row']):
            x_pos = margin_left_px + c * (label_width_px + gap_h_px)
            y_pos = margin_top_px + r * (label_height_px + gap_v_px)
            
            # Very light gray outline
            draw.rectangle([x_pos, y_pos, x_pos + label_width_px, y_pos + label_height_px], 
                         outline='lightgray', width=1)
    
    return page

def generate_label_page(entry, params, label_type, position, rotation=0):
    """Generate a full A4 page with a label at the specified position"""
    config = LABEL_CONFIGS[label_type]
    
    # Convert mm to pixels (assuming 300 DPI)
    dpi = 300
    mm_to_px = dpi / 25.4
    
    page_width_px = int(config['page_width_mm'] * mm_to_px)
    page_height_px = int(config['page_height_mm'] * mm_to_px)
    
    # Create page
    page = Image.new('RGB', (page_width_px, page_height_px), 'white')
    
    # Generate the single label
    label = generate_single_label(entry, params, label_type, rotation, for_printing=True)
    
    # Calculate position on page
    row = (position - 1) // config['labels_per_row']
    col = (position - 1) % config['labels_per_row']
    
    margin_left_px = int(config['margin_left_mm'] * mm_to_px)
    margin_top_px = int(config['margin_top_mm'] * mm_to_px)
    
    # Label dimensions for positioning are always based on the original label size
    # because the rotated label will be placed in the same spot as a non-rotated label
    label_width_px = int(config['label_width_mm'] * mm_to_px)
    label_height_px = int(config['label_height_mm'] * mm_to_px)
        
    gap_h_px = int(config['gap_horizontal_mm'] * mm_to_px)
    gap_v_px = int(config['gap_vertical_mm'] * mm_to_px)
    
    x = margin_left_px + col * (label_width_px + gap_h_px)
    y = margin_top_px + row * (label_height_px + gap_v_px)
    
    # Paste label onto page
    page.paste(label, (x, y))
    
    # Draw light grid lines for reference (optional)
    draw = ImageDraw.Draw(page)
    
    # Draw light outline around all label positions for reference
    for r in range(config['labels_per_col']):
        for c in range(config['labels_per_row']):
            x_pos = margin_left_px + c * (label_width_px + gap_h_px)
            y_pos = margin_top_px + r * (label_height_px + gap_v_px)
            
            # Very light gray outline
            draw.rectangle([x_pos, y_pos, x_pos + label_width_px, y_pos + label_height_px], 
                         outline='lightgray', width=1)
    
    return page

@labels_api_bp.route('/entries/<int:entry_id>/label_pdf', methods=['POST'])
def generate_label_pdf(entry_id):
    """Generate a PDF for printing labels"""
    try:
        data = request.json
        label_type = data.get('label_type', '8_labels')
        position = data.get('position', 1)
        
        # Get entry data
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT e.id, e.title, e.description, e.intended_end_date, e.actual_end_date, 
                   e.status, e.created_at, et.singular_label as entry_type_label
            FROM Entry e
            JOIN EntryType et ON e.entry_type_id = et.id
            WHERE e.id = ?
        ''', (entry_id,))
        
        entry = cursor.fetchone()
        if not entry:
            return jsonify({'error': 'Entry not found'}), 404
            
        # Get system parameters
        params = get_system_parameters()
        
        # Generate page image
        page_image = generate_label_page(dict(entry), params, label_type, position, rotation=0)
        
        # Convert to PDF (simplified - you might want to use a proper PDF library)
        pdf_buffer = io.BytesIO()
        page_image.save(pdf_buffer, format='PDF', resolution=300.0)
        pdf_data = pdf_buffer.getvalue()
        
        response = make_response(pdf_data)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=label_entry_{entry_id}.pdf'
        
        return response
        
    except Exception as e:
        logger.error(f"Error generating PDF: {e}", exc_info=True)
        return jsonify({'error': 'Failed to generate PDF'}), 500

@labels_api_bp.route('/upload_logo', methods=['POST'])
def upload_project_logo():
    """Upload and save project logo"""
    try:
        if 'logo' not in request.files:
            return jsonify({'error': 'No logo file provided'}), 400
            
        file = request.files['logo']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
            
        if file and allowed_file(file.filename):
            # Create uploads directory if it doesn't exist
            # Use /app/uploads which is mounted as a volume for persistence
            upload_dir = '/app/uploads'
            os.makedirs(upload_dir, exist_ok=True)
            
            # Use static filename with extension from uploaded file
            file_ext = file.filename.rsplit('.', 1)[1].lower()
            filename = f"project_logo.{file_ext}"
            filepath = os.path.join(upload_dir, filename)
            
            # Delete old logo files (any project_logo.* files)
            import glob
            for old_logo in glob.glob(os.path.join(upload_dir, 'project_logo.*')):
                try:
                    os.remove(old_logo)
                except Exception as e:
                    logger.warning(f"Could not remove old logo {old_logo}: {e}")
            
            # Save new file
            file.save(filepath)
            
            # Update system parameter with static path
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE SystemParameters SET parameter_value = ? WHERE parameter_name = 'project_logo_path'",
                (f'/static/uploads/{filename}',)
            )
            conn.commit()
            
            return jsonify({
                'message': 'Logo uploaded successfully',
                'logo_path': f'/static/uploads/{filename}'
            })
        else:
            return jsonify({'error': 'Invalid file type. Allowed: png, jpg, jpeg, gif'}), 400
            
    except Exception as e:
        logger.error(f"Error uploading logo: {e}", exc_info=True)
        return jsonify({'error': 'Failed to upload logo'}), 500

def allowed_file(filename):
    """Check if file type is allowed"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ============================================================================
# Niimbot Printer Endpoints
# ============================================================================

@labels_api_bp.route('/niimbot/discover', methods=['GET'])
def discover_niimbot_printers_endpoint():
    """Discover available Niimbot printers via Bluetooth"""
    try:
        from ..services.niimbot_printer_ble import discover_niimbot_printers
        
        timeout = float(request.args.get('timeout', 10.0))
        
        # Run async discovery in sync context
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        printers = loop.run_until_complete(discover_niimbot_printers(timeout))
        loop.close()
        
        return jsonify({
            'success': True,
            'printers': printers,
            'count': len(printers)
        })
        
    except ImportError as e:
        logger.error(f"Niimbot library not available: {e}")
        return jsonify({
            'success': False,
            'error': 'Bluetooth support not available. Please install required dependencies (bleak).'
        }), 500
    except Exception as e:
        logger.error(f"Error discovering Niimbot printers: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Failed to discover printers: {str(e)}'
        }), 500


@labels_api_bp.route('/niimbot/connect', methods=['POST'])
def connect_niimbot_printer():
    """Test connection to a Niimbot printer"""
    try:
        from ..services.niimbot_printer_ble import NiimbotPrinterBLE as NiimbotPrinter
        
        data = request.json
        address = data.get('address')
        model = data.get('model', 'd110')
        
        if not address:
            return jsonify({'success': False, 'error': 'Printer address required'}), 400
        
        # Test connection
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def test_connection():
            printer = NiimbotPrinter(address, model)
            connected = await printer.connect()
            if connected:
                # Get printer info
                info = {
                    'battery': await printer.get_info(1),  # InfoEnum.BATTERY value
                    'connected': True
                }
                await printer.disconnect()
                return info
            return {'connected': False}
        
        result = loop.run_until_complete(test_connection())
        loop.close()
        
        return jsonify({
            'success': result.get('connected', False),
            'info': result
        })
        
    except ImportError:
        return jsonify({
            'success': False,
            'error': 'Bluetooth support not available'
        }), 500
    except Exception as e:
        logger.error(f"Error connecting to printer: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Connection failed: {str(e)}'
        }), 500


@labels_api_bp.route('/entries/<int:entry_id>/niimbot/print', methods=['POST'])
def print_to_niimbot(entry_id):
    """Print a label directly to a Niimbot printer"""
    try:
        from ..services.niimbot_printer_ble import NiimbotPrinterBLE as NiimbotPrinter
        
        data = request.json
        printer_address = data.get('printer_address')
        printer_model = data.get('printer_model', 'd110')
        label_size = data.get('label_size', '60x30mm')  # Default to 60x30mm for B1
        density = int(data.get('density', 3))
        quantity = int(data.get('quantity', 1))
        rotation = int(data.get('rotation', 0))  # 0 = no rotation (correct for B1)
        
        if not printer_address:
            return jsonify({'success': False, 'error': 'Printer address required'}), 400
        
        # Get entry data
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT e.id, e.title, e.description, e.intended_end_date, e.actual_end_date, 
                   e.status, e.created_at, et.singular_label as entry_type_label
            FROM Entry e
            JOIN EntryType et ON e.entry_type_id = et.id
            WHERE e.id = ?
        ''', (entry_id,))
        
        entry = cursor.fetchone()
        if not entry:
            return jsonify({'success': False, 'error': 'Entry not found'}), 404
        
        # Get system parameters
        params = get_system_parameters()
        
        # Generate label for Niimbot printer
        label_type = f'niimbot_{printer_model}'
        label_image = generate_niimbot_label(dict(entry), params, label_type, label_size)
        
        # Print to Niimbot
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def print_job():
            logger.info(f"Starting print job to {printer_address} (model: {printer_model})")
            printer = NiimbotPrinter(printer_address, printer_model)
            
            logger.info("Attempting to connect to printer...")
            if not await printer.connect():
                raise Exception(f"Failed to connect to printer at {printer_address}")
            
            logger.info("Connection successful, preparing image...")
            
            # The Niimbot printer service handles color inversion internally
            # Just convert to RGB and optionally rotate
            rgb_image = label_image.convert('RGB')
            
            # Rotate image for proper orientation (configurable)
            if rotation != 0:
                rotated_image = rgb_image.rotate(rotation, Image.Resampling.BICUBIC, expand=True)
                logger.info(f"Image rotated {rotation} degrees: {rgb_image.size} -> {rotated_image.size}")
            else:
                rotated_image = rgb_image
                logger.info(f"No rotation applied: {rgb_image.size}")
            
            logger.info(f"Sending print job (density: {density}, quantity: {quantity})...")
            success = await printer.print_image(rotated_image, density, quantity)
            
            logger.info("Disconnecting from printer...")
            await printer.disconnect()
            
            logger.info(f"Print job completed: {'success' if success else 'failed'}")
            return success
        
        try:
            success = loop.run_until_complete(print_job())
        except Exception as e:
            logger.error(f"Print job failed with exception: {type(e).__name__}: {e}")
            raise
        finally:
            loop.close()
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Successfully printed {quantity} label(s)',
                'entry_id': entry_id
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Print job failed'
            }), 500
        
    except ImportError:
        return jsonify({
            'success': False,
            'error': 'Bluetooth support not available'
        }), 500
    except Exception as e:
        logger.error(f"Error printing to Niimbot: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Print failed: {str(e)}'
        }), 500


        size = request.args.get('size', '100', type=int)
        
        # Get system parameters for QR prefix
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT parameter_name, parameter_value FROM SystemParameters")
        params = {row['parameter_name']: row['parameter_value'] for row in cursor.fetchall()}
        
        # Get QR prefix
        qr_prefix = params.get('label_qr_code_prefix', params.get('project_name', 'Entry'))
        qr_data = f"{qr_prefix}{entry_id}"
        
        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=0)
        qr.add_data(qr_data)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")
        
        # Resize to requested size
        qr_img = qr_img.resize((size, size), Image.Resampling.NEAREST)
        
        # Convert to PNG and return
        img_io = BytesIO()
        qr_img.save(img_io, 'PNG')
        img_io.seek(0)
        
        return send_file(img_io, mimetype='image/png')
        
    except Exception as e:
        logger.error(f"Error generating QR code: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500
        return jsonify({'error': str(e)}), 500


@labels_api_bp.route('/niimbot/print_image', methods=['POST'])
def print_niimbot_image():
    """Print a pre-rendered image directly to a Niimbot printer"""
    try:
        from ..services.niimbot_printer_ble import NiimbotPrinterBLE as NiimbotPrinter
        
        data = request.json
        printer_address = data.get('printer_address')
        printer_model = data.get('printer_model', 'd110')
        image_data = data.get('image_data')  # Base64 encoded PNG
        density = int(data.get('density', 3))
        quantity = int(data.get('quantity', 1))
        
        if not printer_address:
            return jsonify({'success': False, 'error': 'Printer address required'}), 400
        
        if not image_data:
            return jsonify({'success': False, 'error': 'Image data required'}), 400
        
        # Decode base64 image
        import base64
        from io import BytesIO
        image_bytes = base64.b64decode(image_data)
        label_image = Image.open(BytesIO(image_bytes))
        
        logger.info(f"Received image for printing: {label_image.size} ({label_image.mode})")
        
        # Print to Niimbot
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def print_job():
            logger.info(f"Starting print job to {printer_address} (model: {printer_model})")
            printer = NiimbotPrinter(printer_address, printer_model)
            
            logger.info("Attempting to connect to printer...")
            if not await printer.connect():
                raise Exception(f"Failed to connect to printer at {printer_address}")
            
            logger.info("Connection successful, preparing image...")
            
            # The Niimbot service handles color inversion internally, so just pass RGB
            # Convert to RGB if needed
            if label_image.mode != 'RGB':
                rgb_image = label_image.convert('RGB')
            else:
                rgb_image = label_image
            
            logger.info(f"Sending image to printer: {rgb_image.size}")
            
            logger.info(f"Sending print job (density: {density}, quantity: {quantity})...")
            success = await printer.print_image(rgb_image, density, quantity)
            
            logger.info("Disconnecting from printer...")
            await printer.disconnect()
            
            logger.info(f"Print job completed: {'success' if success else 'failed'}")
            return success
        
        try:
            success = loop.run_until_complete(print_job())
        except Exception as e:
            logger.error(f"Print job failed with exception: {type(e).__name__}: {e}")
            raise
        finally:
            loop.close()
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Successfully printed {quantity} label(s)'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Print job failed'
            }), 500
        
    except ImportError:
        return jsonify({
            'success': False,
            'error': 'Bluetooth support not available'
        }), 500
    except Exception as e:
        logger.error(f"Error printing image to Niimbot: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Print failed: {str(e)}'
        }), 500


@labels_api_bp.route('/niimbot/preview/<int:entry_id>', methods=['GET'])
def preview_niimbot_label(entry_id):
    """Generate a preview of a label for Niimbot printer"""
    try:
        label_type = request.args.get('label_type', 'niimbot_d110')
        label_size = request.args.get('label_size', '50x14mm')
        
        # Get entry data
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT e.id, e.title, e.description, e.intended_end_date, e.actual_end_date, 
                   e.status, e.created_at, et.singular_label as entry_type_label
            FROM Entry e
            JOIN EntryType et ON e.entry_type_id = et.id
            WHERE e.id = ?
        ''', (entry_id,))
        
        entry = cursor.fetchone()
        if not entry:
            return jsonify({'error': 'Entry not found'}), 404
        
        # Get system parameters
        params = get_system_parameters()
        
        # Override params with query string values for preview
        override_params = [
            'label_font_size', 'label_title_font_size', 'label_border_style',
            'label_text_wrap', 'label_include_qr_code', 'label_qr_size', 'label_qr_code_prefix',
            'label_qr_position', 'label_include_logo', 'label_logo_position'
        ]
        for param in override_params:
            if param in request.args:
                params[param] = request.args.get(param)
        
        # Generate label image
        label_image = generate_niimbot_label(dict(entry), params, label_type, label_size)
        
        # Convert to base64 for preview
        img_buffer = io.BytesIO()
        label_image.save(img_buffer, format='PNG')
        img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
        
        return jsonify({
            'label_preview': f'data:image/png;base64,{img_base64}',
            'entry': dict(entry)
        })
        
    except Exception as e:
        logger.error(f"Error generating Niimbot label preview: {e}", exc_info=True)
        return jsonify({'error': 'Failed to generate label preview'}), 500


def generate_niimbot_label(entry, params, label_type, label_size):
    """
    Generate a label image optimized for Niimbot printers
    
    Args:
        entry: Entry data dictionary
        params: System parameters
        label_type: Type of Niimbot printer (niimbot_b1, niimbot_d110)
        label_size: Label size string (e.g., '50x14mm')
    
    Returns:
        PIL Image object
    """
    config = LABEL_CONFIGS.get(label_type)
    if not config or config['type'] != 'niimbot':
        raise ValueError(f"Invalid Niimbot label type: {label_type}")
    
    # Resolve per-size parameters (e.g., label_60x30mm_border_style -> label_border_style)
    # This allows settings to be configured per label size
    # First try base size (portrait/0 degrees), then try rotated (_r90) if that was configured
    size_prefix = f"label_{label_size}_"
    size_params = {}
    
    # Check for size-specific params (portrait)
    for key, value in params.items():
        if key.startswith(size_prefix) and '_r90_' not in key:
            # Extract the setting name without the size prefix
            setting_name = key.replace(size_prefix, 'label_')
            size_params[setting_name] = value
    
    # TODO: Add rotation support to entry page, then check for _r90_ params here
    
    # Merge size-specific params into params (size-specific takes precedence)
    params = {**params, **size_params}
    
    # Log resolved parameters for debugging
    logger.info(f"Label generation for {label_size}: border_style={params.get('label_border_style')}, "
                f"qr_position={params.get('label_qr_position')}, include_logo={params.get('label_include_logo')}, "
                f"logo_position={params.get('label_logo_position')}")
    
    # Parse label size
    size_config = config['common_sizes'].get(label_size)
    if not size_config:
        # Default to first available size
        label_size = list(config['common_sizes'].keys())[0]
        size_config = config['common_sizes'][label_size]
    
    # Calculate dimensions in pixels at printer DPI
    dpi = config['dpi']
    mm_to_px = dpi / 25.4
    
    width_px = int(size_config['width_mm'] * mm_to_px)
    height_px = int(size_config['height_mm'] * mm_to_px)
    
    # Ensure width doesn't exceed max
    if width_px > config['max_width_px']:
        width_px = config['max_width_px']
    
    # Create image (will be rotated 90 degrees for printing)
    img = Image.new('RGB', (width_px, height_px), 'white')
    draw = ImageDraw.Draw(img)
    
    # Use smaller fonts for compact labels
    # Ensure font_size is an integer
    # Font sizes are specified as pixels for the canvas (which is already at 203 DPI)
    # So use them directly without additional scaling
    font_size_param = params.get('label_font_size', 8)
    try:
        font_size_param = int(font_size_param)
    except (ValueError, TypeError):
        font_size_param = 8
    font_size_px = max(font_size_param, 8)
    
    # Try to load fonts
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans.ttf",
    ]
    
    font_bold_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
    ]
    
    font = None
    font_bold = None
    
    for font_path in font_paths:
        try:
            font = ImageFont.truetype(font_path, font_size_px)
            break
        except:
            continue
    
    for font_path in font_bold_paths:
        try:
            font_bold = ImageFont.truetype(font_path, int(font_size_px * 1.2))
            break
        except:
            continue
    
    if font is None:
        font = ImageFont.load_default()
        font_bold = font
    
    # Create title font (larger than body)
    # Use same logic as body font - canvas pixels at 203 DPI
    title_font_size_param = params.get('label_title_font_size', 14)
    try:
        title_font_size_param = int(title_font_size_param)
    except (ValueError, TypeError):
        title_font_size_param = 14
    title_font_size_px = max(title_font_size_param, 12)
    
    font_title = None
    for font_path in font_bold_paths:
        try:
            font_title = ImageFont.truetype(font_path, title_font_size_px)
            break
        except:
            continue
    if font_title is None:
        font_title = font_bold if font_bold else font
    
    font_small = font
    
    # Layout with proper margins (B1 can't print to edges)
    margin = int(2 * mm_to_px)  # 2mm margin on all sides
    
    # Draw border based on style setting
    border_style = params.get('label_border_style', 'simple')
    if border_style == 'simple':
        draw.rectangle([margin, margin, width_px-margin-1, height_px-margin-1], 
                      outline='black', width=1)
    elif border_style == 'thick':
        draw.rectangle([margin, margin, width_px-margin-1, height_px-margin-1], 
                      outline='black', width=3)
    elif border_style == 'double':
        draw.rectangle([margin, margin, width_px-margin-1, height_px-margin-1], 
                      outline='black', width=1)
        draw.rectangle([margin+3, margin+3, width_px-margin-4, height_px-margin-4], 
                      outline='black', width=1)
    elif border_style == 'rounded':
        # Draw rounded corners (simplified)
        corner_radius = 5
        draw.rectangle([margin+corner_radius, margin, width_px-margin-corner_radius-1, height_px-margin-1], 
                      outline='black', width=1)
        draw.rectangle([margin, margin+corner_radius, width_px-margin-1, height_px-margin-corner_radius-1], 
                      outline='black', width=1)
    elif border_style == 'dashed':
        # Dashed border - draw segments
        dash_length = 5
        gap_length = 3
        # Top edge
        x = margin
        while x < width_px - margin:
            draw.line([(x, margin), (min(x + dash_length, width_px - margin), margin)], fill='black', width=1)
            x += dash_length + gap_length
        # Bottom edge
        x = margin
        while x < width_px - margin:
            draw.line([(x, height_px - margin), (min(x + dash_length, width_px - margin), height_px - margin)], fill='black', width=1)
            x += dash_length + gap_length
        # Left edge
        y = margin
        while y < height_px - margin:
            draw.line([(margin, y), (margin, min(y + dash_length, height_px - margin))], fill='black', width=1)
            y += dash_length + gap_length
        # Right edge
        y = margin
        while y < height_px - margin:
            draw.line([(width_px - margin, y), (width_px - margin, min(y + dash_length, height_px - margin))], fill='black', width=1)
            y += dash_length + gap_length
    elif border_style == 'dotted':
        # Dotted border - draw small segments
        dash_length = 2
        gap_length = 2
        # Top edge
        x = margin
        while x < width_px - margin:
            draw.line([(x, margin), (min(x + dash_length, width_px - margin), margin)], fill='black', width=1)
            x += dash_length + gap_length
        # Bottom edge
        x = margin
        while x < width_px - margin:
            draw.line([(x, height_px - margin), (min(x + dash_length, width_px - margin), height_px - margin)], fill='black', width=1)
            x += dash_length + gap_length
        # Left edge
        y = margin
        while y < height_px - margin:
            draw.line([(margin, y), (margin, min(y + dash_length, height_px - margin))], fill='black', width=1)
            y += dash_length + gap_length
        # Right edge
        y = margin
        while y < height_px - margin:
            draw.line([(width_px - margin, y), (width_px - margin, min(y + dash_length, height_px - margin))], fill='black', width=1)
            y += dash_length + gap_length
    elif border_style == 'decorative':
        # Main border
        draw.rectangle([margin, margin, width_px-margin-1, height_px-margin-1], 
                      outline='black', width=1)
        # Corner decorations
        corner_size = 15
        # Top-left corner
        draw.line([(margin, margin + corner_size), (margin, margin), (margin + corner_size, margin)], fill='black', width=2)
        # Top-right corner
        draw.line([(width_px - margin - corner_size, margin), (width_px - margin, margin), (width_px - margin, margin + corner_size)], fill='black', width=2)
        # Bottom-right corner
        draw.line([(width_px - margin, height_px - margin - corner_size), (width_px - margin, height_px - margin), (width_px - margin - corner_size, height_px - margin)], fill='black', width=2)
        # Bottom-left corner
        draw.line([(margin + corner_size, height_px - margin), (margin, height_px - margin), (margin, height_px - margin - corner_size)], fill='black', width=2)
    elif border_style == 'shadow':
        # Shadow effect
        draw.rectangle([margin+2, margin+2, width_px-margin+1, height_px-margin+1], 
                      outline='#cccccc', width=1)
        draw.rectangle([margin+1, margin+1, width_px-margin, height_px-margin], 
                      outline='#999999', width=1)
        # Main border
        draw.rectangle([margin, margin, width_px-margin-1, height_px-margin-1], 
                      outline='black', width=1)
    
    y_pos = margin + 8  # Add spacing inside border
    
    # QR code size based on setting
    qr_size_setting = params.get('label_qr_size', 'medium')
    qr_sizes = {'small': 50, 'medium': 70, 'large': 90}
    qr_size = min(qr_sizes.get(qr_size_setting, 70), min(int(height_px * 0.5), int(width_px * 0.3)))
    
    # Logo size
    logo_size = min(60, min(int(height_px * 0.3), int(width_px * 0.2)))
    
    # Calculate QR position if enabled
    qr_x, qr_y = 0, 0
    include_qr = params.get('label_include_qr_code', 'true').lower() == 'true'
    qr_position = params.get('label_qr_position', 'right')
    
    if include_qr:
        if qr_position == 'left':
            qr_x = margin + 5
            qr_y = margin + ((height_px - margin * 2 - qr_size) // 2)
        elif qr_position == 'top-left':
            qr_x = margin + 5
            qr_y = margin + 5
        elif qr_position == 'top-right':
            qr_x = width_px - qr_size - margin - 5
            qr_y = margin + 5
        elif qr_position == 'bottom-right':
            qr_x = width_px - qr_size - margin - 5
            qr_y = height_px - qr_size - margin - 5
        elif qr_position == 'bottom-left':
            qr_x = margin + 5
            qr_y = height_px - qr_size - margin - 5
        else:  # 'right' or 'center-right'
            qr_x = width_px - qr_size - margin - 5
            qr_y = margin + ((height_px - margin * 2 - qr_size) // 2)
    
    # Calculate logo position if enabled
    logo_x, logo_y = 0, 0
    include_logo = params.get('label_include_logo', 'false').lower() == 'true'
    logo_position = params.get('label_logo_position', 'top-left')
    
    if include_logo:
        if logo_position == 'top-left':
            logo_x = margin + 5
            logo_y = margin + 5
        elif logo_position == 'top-right':
            logo_x = width_px - logo_size - margin - 5
            logo_y = margin + 5
        elif logo_position == 'left':
            logo_x = margin + 5
            logo_y = margin + ((height_px - margin * 2 - logo_size) // 2)
        else:  # 'bottom-left'
            logo_x = margin + 5
            logo_y = height_px - logo_size - margin - 5
    
    # Calculate available text area based on QR and logo positions
    text_start_x = margin + 5
    text_width = width_px - (margin * 2) - 10
    
    # Adjust for QR on left
    if include_qr and qr_position in ['left', 'top-left', 'bottom-left']:
        if qr_x < text_start_x + 50:  # QR overlaps left text area
            text_start_x = qr_x + qr_size + 10
            text_width = width_px - text_start_x - margin - 5
    
    # Adjust for QR on right
    if include_qr and qr_position in ['right', 'center-right', 'top-right', 'bottom-right']:
        qr_right = qr_x + qr_size
        if qr_right > width_px - margin - 50:  # QR overlaps right text area
            text_width = qr_x - text_start_x - 10
    
    # Adjust for logo on left
    if include_logo and logo_position in ['left', 'top-left', 'bottom-left']:
        if logo_x < text_start_x + 50:  # Logo overlaps left text area
            logo_end = logo_x + logo_size + 10
            if logo_end > text_start_x:
                text_start_x = logo_end
                text_width = width_px - text_start_x - margin - 5
    
    # Adjust for logo on right
    if include_logo and logo_position in ['top-right']:
        logo_right = logo_x + logo_size
        if logo_right > width_px - margin - 50:  # Logo overlaps right text area
            text_width = min(text_width, logo_x - text_start_x - 10)
    
    # Helper function for text wrapping
    def wrap_text(text, font, max_width):
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            if bbox[2] - bbox[0] <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    lines.append(word)
        if current_line:
            lines.append(' '.join(current_line))
        return lines
    
    # Title with wrapping
    title = entry['title']
    text_wrap_enabled = params.get('label_text_wrap', 'true').lower() == 'true'
    
    if text_wrap_enabled:
        title_lines = wrap_text(title, font_title, text_width)
        # Limit to 2 lines
        if len(title_lines) > 2:
            title_lines = title_lines[:2]
            title_lines[1] = title_lines[1][:20] + "..." if len(title_lines[1]) > 20 else title_lines[1]
    else:
        if len(title) > 20:
            title = title[:17] + "..."
        title_lines = [title]
    
    for line in title_lines:
        draw.text((text_start_x, y_pos), line, font=font_title, fill='black')
        y_pos += title_font_size_px + 2
    
    y_pos += 5  # Extra spacing after title
    
    # Entry type and ID (smaller text)
    entry_type = entry.get('entry_type_label', 'Entry')
    type_id_text = f"{entry_type} #{entry['id']}"
    draw.text((text_start_x, y_pos), type_id_text, font=font_small, fill='#555555')
    y_pos += font_size_px + 3
    
    # Status if available
    if entry.get('status'):
        status_text = f"Status: {entry['status']}"
        draw.text((text_start_x, y_pos), status_text, font=font_small, fill='#666666')
        y_pos += font_size_px + 3
    
    # Draw logo if enabled
    if include_logo:
        # For now, draw a placeholder box (in production, you'd load actual logo image)
        draw.rectangle([logo_x, logo_y, logo_x + logo_size, logo_y + logo_size], 
                      outline='#4caf50', width=2, fill='#e8f5e9')
        # Draw "LOGO" text in center
        logo_text = "LOGO"
        bbox = draw.textbbox((0, 0), logo_text, font=font_small)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        draw.text((logo_x + (logo_size - text_w) // 2, logo_y + (logo_size - text_h) // 2), 
                 logo_text, font=font_small, fill='#4caf50')
    
    # Draw QR code at calculated position
    if include_qr:
        qr_prefix = params.get('label_qr_code_prefix', params.get('project_name', 'Project'))
        qr_data = f"{qr_prefix}/entry/{entry['id']}"
        
        qr = qrcode.QRCode(version=1, box_size=2, border=1)
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_img = qr_img.resize((qr_size, qr_size))
        img.paste(qr_img, (qr_x, qr_y))
    
    # Created date at bottom - adaptive to logo and QR positions
    created_date = entry['created_at'][:10]
    date_text = f"{created_date}"
    date_x = margin + 5
    date_y = height_px - margin - font_size_px - 5
    
    # Check if date overlaps with logo at bottom-left
    if include_logo and logo_position == 'bottom-left':
        # Move date to right of logo if it overlaps
        if date_x < logo_x + logo_size + 10:
            date_x = logo_x + logo_size + 10
    
    # Check if date overlaps with QR at bottom-left
    if include_qr and qr_position == 'bottom-left':
        # Move date to right of QR if it overlaps
        if date_x < qr_x + qr_size + 10:
            date_x = qr_x + qr_size + 10
    
    # Check if date overlaps with QR at bottom-right
    if include_qr and qr_position == 'bottom-right':
        # Check if date would overlap
        bbox = draw.textbbox((0, 0), date_text, font=font_small)
        date_width = bbox[2] - bbox[0]
        if date_x + date_width > qr_x - 5:
            # Move date to left of QR
            date_x = qr_x - date_width - 10
    
    draw.text((date_x, date_y), date_text, font=font_small, fill='#888888')
    
    return img


def allowed_file(filename):
    """Check if file type is allowed"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
