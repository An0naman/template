# template_app/app/api/labels_api.py
from flask import Blueprint, request, jsonify, g, current_app, make_response, render_template_string
import sqlite3
import logging
import base64
import io
import qrcode
from PIL import Image, ImageDraw, ImageFont
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

# Label configurations for different sheet types
LABEL_CONFIGS = {
    '8_labels': {
        'name': '8 Labels (2x4)',
        'page_width_mm': 210,  # A4 width
        'page_height_mm': 297,  # A4 height
        'labels_per_row': 2,
        'labels_per_col': 4,
        'label_width_mm': 99.1,
        'label_height_mm': 67.7,
        'margin_top_mm': 8.5,
        'margin_left_mm': 4.7,
        'gap_horizontal_mm': 2.3,
        'gap_vertical_mm': 0
    },
    '14_labels': {
        'name': '14 Labels (2x7)',
        'page_width_mm': 210,  # A4 width
        'page_height_mm': 297,  # A4 height
        'labels_per_row': 2,
        'labels_per_col': 7,
        'label_width_mm': 99.1,
        'label_height_mm': 38.1,
        'margin_top_mm': 8.5,
        'margin_left_mm': 4.7,
        'gap_horizontal_mm': 2.3,
        'gap_vertical_mm': 0
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
    
    # Handle rotation for final output - use same approach for both preview and print
    if rotation == 90:
        # Always use the same rotation approach for consistency
        # The image is already laid out in landscape mode (work_width x work_height)
        # This gives us the proper 90-degree rotated appearance
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
    
    # Calculate positioning variables - adjust for rotation
    margin_left_px = int(config['margin_left_mm'] * mm_to_px)
    margin_top_px = int(config['margin_top_mm'] * mm_to_px)
    
    # For rotated labels, we need to use the rotated dimensions for positioning
    if rotation == 90:
        # For 90-degree rotation, the label template is in landscape mode
        # So we use height as width and width as height for positioning
        label_width_px = int(config['label_height_mm'] * mm_to_px)  # Swapped
        label_height_px = int(config['label_width_mm'] * mm_to_px)  # Swapped
    else:
        # Normal orientation
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
    
    # For rotated labels, adjust dimensions for positioning
    if rotation == 90:
        label_width_px = int(config['label_height_mm'] * mm_to_px)  # Swapped
        label_height_px = int(config['label_width_mm'] * mm_to_px)  # Swapped
    else:
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
            upload_dir = os.path.join(current_app.root_path, 'static', 'uploads')
            os.makedirs(upload_dir, exist_ok=True)
            
            # Save file
            filename = f"project_logo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{file.filename.rsplit('.', 1)[1].lower()}"
            filepath = os.path.join(upload_dir, filename)
            file.save(filepath)
            
            # Update system parameter
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
