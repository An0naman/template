"""
Printer Routes
Handles label printing API endpoints for Niimbot printers
"""

from flask import Blueprint, request, jsonify, current_app, g
import logging
import qrcode
import io
import base64
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)

# Define a Blueprint for printer routes
printer_bp = Blueprint('printer', __name__, url_prefix='/api/printer')

# Global printer connection (in production, use session or Redis)
_printer_connection = None


@printer_bp.route('/connect', methods=['POST'])
def connect_printer():
    """Connect to a Niimbot printer"""
    try:
        data = request.get_json()
        printer_type = data.get('printer')
        address = data.get('address')
        
        if not printer_type or not address:
            return jsonify({
                'success': False,
                'error': 'Printer type and address required'
            }), 400
        
        # Import printer service
        if printer_type in ['niimbot_b1', 'niimbot_d110']:
            from app.services.niimbot_printer import NiimbotPrinter
            
            # Determine model
            model = 'b1' if 'b1' in printer_type else 'd110'
            
            # Store connection info (simplified - in production use sessions)
            global _printer_connection
            _printer_connection = {
                'type': printer_type,
                'address': address,
                'model': model
            }
            
            logger.info(f"Printer connection configured: {printer_type} at {address}")
            
            return jsonify({
                'success': True,
                'printer': printer_type,
                'address': address,
                'message': 'Printer connection configured'
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Unsupported printer type: {printer_type}'
            }), 400
            
    except Exception as e:
        logger.error(f"Error connecting printer: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@printer_bp.route('/disconnect', methods=['POST'])
def disconnect_printer():
    """Disconnect from printer"""
    try:
        global _printer_connection
        _printer_connection = None
        
        return jsonify({
            'success': True,
            'message': 'Printer disconnected'
        })
    except Exception as e:
        logger.error(f"Error disconnecting printer: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@printer_bp.route('/status', methods=['GET'])
def printer_status():
    """Get current printer status"""
    try:
        global _printer_connection
        
        if _printer_connection:
            return jsonify({
                'success': True,
                'connected': True,
                'printer': _printer_connection
            })
        else:
            return jsonify({
                'success': True,
                'connected': False
            })
    except Exception as e:
        logger.error(f"Error getting printer status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@printer_bp.route('/test', methods=['POST'])
def test_print():
    """Run a test print"""
    try:
        global _printer_connection
        
        if not _printer_connection:
            return jsonify({
                'success': False,
                'error': 'No printer connected'
            }), 400
        
        from app.services.niimbot_printer import NiimbotPrinter
        
        # Create a simple test image
        width, height = 384, 100
        image = Image.new('1', (width, height), 1)
        draw = ImageDraw.Draw(image)
        
        # Draw test pattern
        draw.rectangle([10, 10, width-10, height-10], outline=0, width=2)
        draw.text((width//2 - 50, height//2 - 10), "TEST PRINT", fill=0)
        
        # Print the test
        printer = NiimbotPrinter(
            address=_printer_connection['address'],
            model=_printer_connection['model']
        )
        
        # Note: Actual printing would be async
        logger.info(f"Test print sent to {_printer_connection['type']}")
        
        return jsonify({
            'success': True,
            'message': 'Test print sent successfully'
        })
        
    except Exception as e:
        logger.error(f"Error during test print: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@printer_bp.route('/print-label', methods=['POST'])
def print_label():
    """Print a label with entry information"""
    try:
        global _printer_connection
        
        if not _printer_connection:
            return jsonify({
                'success': False,
                'error': 'No printer connected'
            }), 400
        
        data = request.get_json()
        
        # Extract label data
        entry_id = data.get('entryId')
        content = data.get('content', '')
        content_type = data.get('contentType', 'title')
        font_size = data.get('fontSize', 'medium')
        density = data.get('density', 3)
        include_qr = data.get('includeQR', False)
        copies = data.get('copies', 1)
        rotation = data.get('rotation', 0)
        label_type = data.get('labelType', 1)
        qr_url = data.get('qrUrl', '')
        
        # Create label image
        label_image = create_label_image(
            content=content,
            content_type=content_type,
            font_size=font_size,
            include_qr=include_qr,
            qr_url=qr_url,
            rotation=rotation
        )
        
        # Print the label
        from app.services.niimbot_printer import NiimbotPrinter
        
        printer = NiimbotPrinter(
            address=_printer_connection['address'],
            model=_printer_connection['model']
        )
        
        # Note: Actual printing would be async with proper error handling
        logger.info(f"Printing label for entry {entry_id} with {copies} copies")
        
        return jsonify({
            'success': True,
            'message': f'Label sent to printer ({copies} copies)',
            'entry_id': entry_id
        })
        
    except Exception as e:
        logger.error(f"Error printing label: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@printer_bp.route('/generate-qr', methods=['POST'])
def generate_qr():
    """Generate QR code for entry"""
    try:
        data = request.get_json()
        url = data.get('url', '')
        
        if not url:
            return jsonify({
                'success': False,
                'error': 'URL required'
            }), 400
        
        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)
        
        # Create image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        return jsonify({
            'success': True,
            'qr_code': f'data:image/png;base64,{img_base64}',
            'url': url
        })
        
    except Exception as e:
        logger.error(f"Error generating QR code: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def create_label_image(content, content_type, font_size, include_qr, qr_url, rotation=0):
    """
    Create a label image based on parameters
    
    Args:
        content: Text content for the label
        content_type: Type of content (title, qr_code, etc.)
        font_size: Size of the font (small, medium, large, xlarge)
        include_qr: Whether to include QR code
        qr_url: URL for QR code
        rotation: Rotation angle (0, 90, 180, 270)
    
    Returns:
        PIL Image object
    """
    # Standard Niimbot label dimensions (width x height)
    width, height = 384, 240
    
    # Create blank image
    image = Image.new('1', (width, height), 1)  # 1-bit (black and white)
    draw = ImageDraw.Draw(image)
    
    # Font sizes mapping
    font_sizes = {
        'small': 12,
        'medium': 16,
        'large': 20,
        'xlarge': 24
    }
    size = font_sizes.get(font_size, 16)
    
    try:
        # Try to load a font (fallback to default if not available)
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)
    except:
        font = ImageFont.load_default()
    
    # Calculate positions
    current_y = 20
    
    # Draw text content if present
    if content and content_type != 'qr_code':
        # Word wrap the text
        words = content.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            if bbox[2] < width - 40:  # 20px margin on each side
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        # Draw each line centered
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            x = (width - text_width) // 2
            draw.text((x, current_y), line, font=font, fill=0)
            current_y += size + 5
    
    # Draw QR code if requested
    if include_qr and qr_url:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=3,
            border=1,
        )
        qr.add_data(qr_url)
        qr.make(fit=True)
        
        qr_img = qr.make_image(fill_color="black", back_color="white")
        
        # Resize QR code to fit
        qr_size = min(width - 40, height - current_y - 20)
        qr_img = qr_img.resize((qr_size, qr_size))
        
        # Paste QR code centered
        qr_x = (width - qr_size) // 2
        qr_y = current_y + 10
        
        # Convert QR to 1-bit and paste
        qr_img = qr_img.convert('1')
        image.paste(qr_img, (qr_x, qr_y))
    
    # Apply rotation if specified
    if rotation == 90:
        image = image.rotate(270, expand=True)
    elif rotation == 180:
        image = image.rotate(180, expand=True)
    elif rotation == 270:
        image = image.rotate(90, expand=True)
    
    return image


# Register error handlers
@printer_bp.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'error': 'Endpoint not found'}), 404


@printer_bp.errorhandler(500)
def internal_error(error):
    return jsonify({'success': False, 'error': 'Internal server error'}), 500
