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
        label_image = generate_single_label(dict(entry), params, label_type)
        
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

@labels_api_bp.route('/entries/<int:entry_id>/print_label', methods=['POST'])
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

def generate_single_label(entry, params, label_type):
    """Generate a single label image"""
    config = LABEL_CONFIGS[label_type]
    
    # Convert mm to pixels (assuming 300 DPI)
    dpi = 300
    mm_to_px = dpi / 25.4
    
    width_px = int(config['label_width_mm'] * mm_to_px)
    height_px = int(config['label_height_mm'] * mm_to_px)
    
    # Create image
    img = Image.new('RGB', (width_px, height_px), 'white')
    draw = ImageDraw.Draw(img)
    
    # Try to load a reasonable font
    try:
        font_size = int(params.get('label_font_size', 10))
        font_size_px = int(font_size * mm_to_px / 25.4 * 12)  # Convert pt to px
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size_px)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", int(font_size_px * 0.7))
        font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(font_size_px * 1.2))
    except:
        font = ImageFont.load_default()
        font_small = font
        font_title = font
    
    # Calculate layout
    margin = int(2 * mm_to_px)  # 2mm margin
    y_pos = margin
    
    # Project name and logo
    if params.get('label_include_logo', 'true').lower() == 'true':
        project_name = params.get('project_name', 'Project')
        draw.text((margin, y_pos), project_name, font=font_title, fill='black')
        y_pos += int(font_size_px * 1.5)
    
    # Entry title
    title = entry['title'][:30]  # Truncate if too long
    draw.text((margin, y_pos), f"Title: {title}", font=font, fill='black')
    y_pos += int(font_size_px * 1.2)
    
    # Entry type
    entry_type = entry['entry_type_label'] if 'entry_type_label' in entry.keys() else 'Entry'
    draw.text((margin, y_pos), f"Type: {entry_type}", font=font_small, fill='black')
    y_pos += int(font_size_px * 1.0)
    
    # Entry ID
    draw.text((margin, y_pos), f"ID: #{entry['id']}", font=font_small, fill='black')
    y_pos += int(font_size_px * 1.0)
    
    # Status
    status = (entry['status'] if 'status' in entry.keys() else 'active').upper()
    draw.text((margin, y_pos), f"Status: {status}", font=font_small, fill='black')
    y_pos += int(font_size_px * 1.0)
    
    # Dates
    if 'intended_end_date' in entry.keys() and entry['intended_end_date']:
        date_str = entry['intended_end_date'][:10]  # Just date part
        draw.text((margin, y_pos), f"Target End: {date_str}", font=font_small, fill='black')
        y_pos += int(font_size_px * 1.0)
    
    # Created date
    created_date = entry['created_at'][:10]
    draw.text((margin, y_pos), f"Created: {created_date}", font=font_small, fill='black')
    
    # QR Code if enabled
    if params.get('label_include_qr_code', 'true').lower() == 'true':
        qr_data = f"{params.get('project_name', 'Project')}/entry/{entry['id']}"
        qr = qrcode.QRCode(version=1, box_size=2, border=1)
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_size = int(min(width_px * 0.25, height_px * 0.4))
        qr_img = qr_img.resize((qr_size, qr_size))
        
        # Position QR code in bottom right
        qr_x = width_px - qr_size - margin
        qr_y = height_px - qr_size - margin
        img.paste(qr_img, (qr_x, qr_y))
    
    return img

def generate_label_page(entry, params, label_type, position):
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
    label = generate_single_label(entry, params, label_type)
    
    # Calculate position on page
    row = (position - 1) // config['labels_per_row']
    col = (position - 1) % config['labels_per_row']
    
    margin_left_px = int(config['margin_left_mm'] * mm_to_px)
    margin_top_px = int(config['margin_top_mm'] * mm_to_px)
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
        page_image = generate_label_page(dict(entry), params, label_type, position)
        
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
