"""
Photo Gallery API

Entry-level nomination endpoints for configurable photo gallery sections.
"""

import json
import logging
import os
from datetime import datetime
from flask import Blueprint, request, jsonify, g
from werkzeug.utils import secure_filename

from ..db import get_connection

logger = logging.getLogger(__name__)

photo_gallery_api_bp = Blueprint('photo_gallery_api', __name__)


def get_db():
    if 'db' not in g:
        g.db = get_connection()
    return g.db


def is_allowed_image(filename: str) -> bool:
    if not filename or '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    # Include HEIC/HEIF for iPhone compatibility.
    return ext in {'jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp', 'svg', 'heic', 'heif'}


@photo_gallery_api_bp.route('/entries/<int:entry_id>/photo-gallery/<int:section_id>', methods=['GET'])
def get_entry_photo_gallery(entry_id, section_id):
    """Get nominated images for a specific entry + gallery section."""
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT image_urls, updated_at FROM EntryPhotoGalleryConfig WHERE entry_id = ? AND section_id = ?",
            (entry_id, section_id)
        )
        row = cursor.fetchone()

        image_urls = []
        updated_at = None

        if row:
            try:
                image_urls = json.loads(row['image_urls'] or '[]')
            except (json.JSONDecodeError, TypeError):
                image_urls = []
            updated_at = row['updated_at']

        return jsonify({
            'entry_id': entry_id,
            'section_id': section_id,
            'image_urls': image_urls,
            'updated_at': updated_at
        }), 200
    except Exception as e:
        logger.error(f"Error getting photo gallery config for entry {entry_id}, section {section_id}: {e}", exc_info=True)
        return jsonify({'error': 'Failed to load photo gallery nominations'}), 500


@photo_gallery_api_bp.route('/entries/<int:entry_id>/photo-gallery/<int:section_id>', methods=['PUT'])
def update_entry_photo_gallery(entry_id, section_id):
    """Save nominated images for a specific entry + gallery section."""
    try:
        data = request.get_json(silent=True) or {}
        image_urls = data.get('image_urls', [])

        if not isinstance(image_urls, list):
            return jsonify({'error': 'image_urls must be an array'}), 400

        sanitized = []
        for raw in image_urls:
            if not isinstance(raw, str):
                continue
            value = raw.strip()
            if value:
                sanitized.append(value)

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id FROM EntryPhotoGalleryConfig WHERE entry_id = ? AND section_id = ?",
            (entry_id, section_id)
        )
        existing = cursor.fetchone()

        if existing:
            cursor.execute(
                """
                UPDATE EntryPhotoGalleryConfig
                SET image_urls = ?, updated_at = CURRENT_TIMESTAMP
                WHERE entry_id = ? AND section_id = ?
                """,
                (json.dumps(sanitized), entry_id, section_id)
            )
        else:
            cursor.execute(
                """
                INSERT INTO EntryPhotoGalleryConfig (entry_id, section_id, image_urls)
                VALUES (?, ?, ?)
                """,
                (entry_id, section_id, json.dumps(sanitized))
            )

        conn.commit()

        return jsonify({
            'message': 'Photo gallery nominations saved',
            'entry_id': entry_id,
            'section_id': section_id,
            'image_urls': sanitized
        }), 200
    except Exception as e:
        logger.error(f"Error saving photo gallery config for entry {entry_id}, section {section_id}: {e}", exc_info=True)
        try:
            conn.rollback()
        except Exception:
            pass
        return jsonify({'error': 'Failed to save photo gallery nominations'}), 500


@photo_gallery_api_bp.route('/entries/<int:entry_id>/photo-gallery/<int:section_id>', methods=['DELETE'])
def clear_entry_photo_gallery(entry_id, section_id):
    """Clear nominated images so section falls back to layout defaults."""
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute(
            "DELETE FROM EntryPhotoGalleryConfig WHERE entry_id = ? AND section_id = ?",
            (entry_id, section_id)
        )
        conn.commit()

        return jsonify({
            'message': 'Photo gallery nominations cleared',
            'entry_id': entry_id,
            'section_id': section_id
        }), 200
    except Exception as e:
        logger.error(f"Error clearing photo gallery config for entry {entry_id}, section {section_id}: {e}", exc_info=True)
        try:
            conn.rollback()
        except Exception:
            pass
        return jsonify({'error': 'Failed to clear photo gallery nominations'}), 500


@photo_gallery_api_bp.route('/entries/<int:entry_id>/photo-gallery/<int:section_id>/uploads', methods=['POST'])
def upload_entry_photo_gallery_images(entry_id, section_id):
    """Upload images from device camera/photo library and add them to this entry's nominations."""
    try:
        files = request.files.getlist('images')
        if not files:
            return jsonify({'error': 'No images uploaded'}), 400

        upload_folder = '/app/uploads' if os.path.exists('/app/uploads') else os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 'static', 'uploads'
        )
        os.makedirs(upload_folder, exist_ok=True)

        max_file_size_bytes = 50 * 1024 * 1024
        uploaded_paths = []

        for file in files:
            if not file or not file.filename:
                continue

            if not is_allowed_image(file.filename):
                return jsonify({'error': f'Unsupported image type for {file.filename}'}), 400

            file.seek(0, os.SEEK_END)
            file_size = file.tell()
            file.seek(0)
            if file_size > max_file_size_bytes:
                return jsonify({'error': f'{file.filename} exceeds 50MB limit'}), 400

            original_name = secure_filename(file.filename)
            timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S%f')
            filename = f'gallery_e{entry_id}_s{section_id}_{timestamp}_{original_name}'
            abs_path = os.path.join(upload_folder, filename)
            file.save(abs_path)
            uploaded_paths.append(f'uploads/{filename}')

        if not uploaded_paths:
            return jsonify({'error': 'No valid images were uploaded'}), 400

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT image_urls FROM EntryPhotoGalleryConfig WHERE entry_id = ? AND section_id = ?",
            (entry_id, section_id)
        )
        row = cursor.fetchone()

        existing = []
        if row:
            try:
                existing = json.loads(row['image_urls'] or '[]')
                if not isinstance(existing, list):
                    existing = []
            except (json.JSONDecodeError, TypeError):
                existing = []

        merged = existing + [p for p in uploaded_paths if p not in existing]

        if row:
            cursor.execute(
                """
                UPDATE EntryPhotoGalleryConfig
                SET image_urls = ?, updated_at = CURRENT_TIMESTAMP
                WHERE entry_id = ? AND section_id = ?
                """,
                (json.dumps(merged), entry_id, section_id)
            )
        else:
            cursor.execute(
                """
                INSERT INTO EntryPhotoGalleryConfig (entry_id, section_id, image_urls)
                VALUES (?, ?, ?)
                """,
                (entry_id, section_id, json.dumps(merged))
            )

        conn.commit()

        return jsonify({
            'message': 'Images uploaded and added to gallery nominations',
            'uploaded_paths': uploaded_paths,
            'image_urls': merged
        }), 201

    except Exception as e:
        logger.error(f"Error uploading gallery images for entry {entry_id}, section {section_id}: {e}", exc_info=True)
        try:
            conn.rollback()
        except Exception:
            pass
        return jsonify({'error': 'Failed to upload gallery images'}), 500
