from flask import Blueprint, jsonify, request
import json
import os
import re

version_management_api_bp = Blueprint('version_management_api', __name__)

SEMVER_RE = re.compile(r'^\d+\.\d+\.\d+$')


def _project_root():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


def _version_file_path():
    runtime_path = '/app/VERSION'
    if os.path.exists('/app'):
        return runtime_path
    return os.path.join(_project_root(), 'VERSION')


def _app_json_path():
    runtime_path = '/app/app.json'
    if os.path.exists('/app'):
        return runtime_path
    return os.path.join(_project_root(), 'app.json')


def _ensure_version_file():
    version_file = _version_file_path()
    version_dir = os.path.dirname(version_file)
    if version_dir and not os.path.exists(version_dir):
        os.makedirs(version_dir, exist_ok=True)
    if not os.path.exists(version_file):
        with open(version_file, 'w', encoding='utf-8') as f:
            f.write('1.0.0')
    return version_file


def _read_version():
    version_file = _ensure_version_file()
    with open(version_file, 'r', encoding='utf-8') as f:
        return f.read().strip() or '1.0.0'


def _write_version(version):
    version_file = _ensure_version_file()
    with open(version_file, 'w', encoding='utf-8') as f:
        f.write(version)


def _sync_app_json_version(version):
    app_json = _app_json_path()
    if not os.path.exists(app_json):
        return

    try:
        with open(app_json, 'r', encoding='utf-8') as f:
            data = json.load(f)

        data['version'] = version

        with open(app_json, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
            f.write('\n')
    except Exception:
        # Do not block version updates if app.json is unavailable or malformed
        return


def _bump_semver(version, bump_type):
    major, minor, patch = [int(x) for x in version.split('.')]

    if bump_type == 'major':
        major += 1
        minor = 0
        patch = 0
    elif bump_type == 'minor':
        minor += 1
        patch = 0
    else:
        patch += 1

    return f'{major}.{minor}.{patch}'


@version_management_api_bp.route('/version/manage', methods=['GET'])
def get_version():
    try:
        version_file = _version_file_path()
        app_json = _app_json_path()
        current_version = _read_version()

        return jsonify({
            'version': current_version,
            'version_file': version_file,
            'app_json': app_json,
            'version_file_writable': os.access(os.path.dirname(version_file) or '.', os.W_OK),
            'app_json_writable': os.path.exists(app_json) and os.access(app_json, os.W_OK)
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@version_management_api_bp.route('/version/manage/set', methods=['POST'])
def set_version():
    data = request.get_json(silent=True) or {}
    version = str(data.get('version', '')).strip()

    if not SEMVER_RE.match(version):
        return jsonify({'error': 'Invalid version format. Use semantic version like 3.1.0'}), 400

    try:
        _write_version(version)
        _sync_app_json_version(version)
        return jsonify({'message': f'Version set to {version}', 'version': version}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@version_management_api_bp.route('/version/manage/bump', methods=['POST'])
def bump_version():
    data = request.get_json(silent=True) or {}
    bump_type = str(data.get('type', 'patch')).strip().lower()

    if bump_type not in ['major', 'minor', 'patch']:
        return jsonify({'error': 'Invalid bump type. Use major, minor, or patch'}), 400

    try:
        current = _read_version()
        if not SEMVER_RE.match(current):
            return jsonify({'error': f'Current version is not semantic: {current}. Set a semantic version first.'}), 400

        new_version = _bump_semver(current, bump_type)
        _write_version(new_version)
        _sync_app_json_version(new_version)

        return jsonify({
            'message': f'Version bumped from {current} to {new_version}',
            'previous_version': current,
            'version': new_version
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
