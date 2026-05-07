# template_app/app/api/backup_api.py
from flask import Blueprint, request, jsonify, current_app
import os
import shutil
import signal
import logging
from datetime import datetime, timezone

backup_api_bp = Blueprint('backup_api', __name__)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _db_path():
    return current_app.config['DATABASE_PATH']


def _backup_dir():
    """
    Return the directory used for backups.
    Reads BACKUP_DIR from app config (set in config.py, which checks the
    /app/backups volume mount first, then falls back to ./backups).
    Override by mounting a NAS path to /app/backups in docker-compose.yml.
    """
    return current_app.config.get('BACKUP_DIR') or os.path.join(
        os.path.dirname(os.path.dirname(_db_path())), 'backups'
    )


def _ensure_backup_dir():
    d = _backup_dir()
    os.makedirs(d, exist_ok=True)
    return d


def _backup_filename():
    ts = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
    db_name = os.path.basename(_db_path())
    return f"{db_name}.{ts}.bak"


def _list_backups_raw():
    backup_dir = _backup_dir()
    if not os.path.isdir(backup_dir):
        return []
    entries = []
    for name in sorted(os.listdir(backup_dir), reverse=True):
        path = os.path.join(backup_dir, name)
        if os.path.isfile(path) and name.endswith('.bak'):
            stat = os.stat(path)
            entries.append({
                'filename': name,
                'size_bytes': stat.st_size,
                'size_human': _human_size(stat.st_size),
                'created_at': datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
            })
    return entries


def _human_size(n):
    for unit in ('B', 'KB', 'MB', 'GB'):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def _safe_filename(name):
    """Reject filenames that try to escape the backup dir."""
    return name == os.path.basename(name) and name.endswith('.bak') and '..' not in name


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@backup_api_bp.route('/backup/list', methods=['GET'])
def list_backups():
    """Return all available backups, newest first."""
    try:
        backups = _list_backups_raw()
        return jsonify({
            'success': True,
            'backup_dir': _backup_dir(),
            'backups': backups,
            'count': len(backups)
        })
    except Exception as e:
        logger.error(f"Error listing backups: {e}")
        return jsonify({'error': str(e)}), 500


@backup_api_bp.route('/backup/create', methods=['POST'])
def create_backup():
    """Copy the live database to the backup directory right now."""
    try:
        src = _db_path()
        if not os.path.isfile(src):
            return jsonify({'error': 'Database file not found'}), 404

        dest_dir = _ensure_backup_dir()
        filename = _backup_filename()
        dest = os.path.join(dest_dir, filename)

        shutil.copy2(src, dest)
        stat = os.stat(dest)
        logger.info(f"Backup created: {dest}")

        return jsonify({
            'success': True,
            'message': f'Backup created: {filename}',
            'filename': filename,
            'size_human': _human_size(stat.st_size),
            'backup_dir': dest_dir
        })
    except Exception as e:
        logger.error(f"Error creating backup: {e}")
        return jsonify({'error': str(e)}), 500


@backup_api_bp.route('/backup/restore', methods=['POST'])
def restore_backup():
    """
    Restore a named backup over the live database, then restart the process so
    the app re-opens the replaced file.

    Body: { "filename": "template.db.20260507_120000.bak" }

    The container's restart policy (always/unless-stopped) means Docker will
    bring it back up automatically after the SIGTERM.
    """
    try:
        data = request.get_json() or {}
        filename = data.get('filename', '').strip()

        if not filename:
            return jsonify({'error': 'filename is required'}), 400

        if not _safe_filename(filename):
            return jsonify({'error': 'Invalid filename'}), 400

        src = os.path.join(_backup_dir(), filename)
        if not os.path.isfile(src):
            return jsonify({'error': f'Backup not found: {filename}'}), 404

        dest = _db_path()

        # Write an atomic replacement: copy to a temp file beside the target,
        # then rename (atomic on POSIX within the same filesystem).
        tmp = dest + '.restore_tmp'
        shutil.copy2(src, tmp)
        os.replace(tmp, dest)

        logger.info(f"Restored {filename} → {dest}. Restarting process.")

        # Schedule a clean shutdown so Docker restarts the container.
        # We respond first, then signal after a short delay via a background thread.
        import threading
        def _shutdown():
            import time
            time.sleep(1)          # let the response flush
            os.kill(os.getpid(), signal.SIGTERM)

        threading.Thread(target=_shutdown, daemon=True).start()

        return jsonify({
            'success': True,
            'message': f'Restored from {filename}. App is restarting — please wait a few seconds then refresh.'
        })

    except Exception as e:
        logger.error(f"Error restoring backup: {e}")
        return jsonify({'error': str(e)}), 500


@backup_api_bp.route('/backup/delete', methods=['POST'])
def delete_backup():
    """Delete a named backup file.

    Body: { "filename": "template.db.20260507_120000.bak" }
    """
    try:
        data = request.get_json() or {}
        filename = data.get('filename', '').strip()

        if not filename:
            return jsonify({'error': 'filename is required'}), 400

        if not _safe_filename(filename):
            return jsonify({'error': 'Invalid filename'}), 400

        path = os.path.join(_backup_dir(), filename)
        if not os.path.isfile(path):
            return jsonify({'error': f'Backup not found: {filename}'}), 404

        os.remove(path)
        logger.info(f"Deleted backup: {path}")
        return jsonify({'success': True, 'message': f'Deleted {filename}'})

    except Exception as e:
        logger.error(f"Error deleting backup: {e}")
        return jsonify({'error': str(e)}), 500
