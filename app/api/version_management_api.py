from flask import Blueprint, jsonify, request, current_app
import json
import os
import re

version_management_api_bp = Blueprint('version_management_api', __name__)

SEMVER_RE = re.compile(r'^\d+\.\d+\.\d+$')


def _to_bool(value):
    return str(value).strip().lower() in ('1', 'true', 'yes', 'on')


def _manual_controls_allowed():
    app_env = os.environ.get('APP_ENV', os.environ.get('FLASK_ENV', '')).strip().lower()
    flask_debug = bool(current_app.debug) if current_app else False
    return flask_debug or app_env in ('dev', 'development', 'local') or _to_bool(os.environ.get('ENABLE_MANUAL_VERSION_CONTROL', 'false'))


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
    if not _manual_controls_allowed():
        return jsonify({'error': 'Manual version changes are only enabled in development environments.'}), 403

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
    if not _manual_controls_allowed():
        return jsonify({'error': 'Manual version changes are only enabled in development environments.'}), 403

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


@version_management_api_bp.route('/version/manage/trigger-deploy', methods=['POST'])
def trigger_deploy():
    if not _manual_controls_allowed():
        return jsonify({'error': 'Deploy trigger is only enabled in development environments.'}), 403

    github_token = os.environ.get('GITHUB_TOKEN', '').strip()
    github_repo = os.environ.get('GITHUB_REPO', '').strip()  # e.g. "username/repo"

    if not github_token:
        return jsonify({'error': 'GITHUB_TOKEN env var is not set.'}), 500
    if not github_repo:
        return jsonify({'error': 'GITHUB_REPO env var is not set (e.g. username/repo).'}), 500

    data = request.get_json(silent=True) or {}
    workflow = str(data.get('workflow', 'docker-build.yml')).strip()
    version = str(data.get('version', '')).strip()

    if workflow not in ('docker-build.yml',):
        return jsonify({'error': 'Invalid workflow. Only docker-build.yml is allowed.'}), 400
    
    if not version:
        return jsonify({'error': 'Version parameter is required.'}), 400
    
    if not SEMVER_RE.match(version):
        return jsonify({'error': 'Invalid version format. Use semantic version like 3.1.0'}), 400

    import urllib.request
    import urllib.error
    import base64

    # The version to deploy is passed from the frontend
    local_version = version

    # Step 1: Sync VERSION file to GitHub repo (main branch) via API
    try:
        # Get current VERSION file SHA so we can update it
        get_url = f'https://api.github.com/repos/{github_repo}/contents/VERSION?ref=main'
        get_req = urllib.request.Request(
            get_url,
            headers={
                'Authorization': f'Bearer {github_token}',
                'Accept': 'application/vnd.github+json',
                'X-GitHub-Api-Version': '2022-11-28',
            }
        )
        with urllib.request.urlopen(get_req) as resp:
            file_data = json.loads(resp.read().decode('utf-8'))
            current_sha = file_data.get('sha')
    except urllib.error.HTTPError as e:
        if e.code == 404:
            current_sha = None  # File doesn't exist yet
        else:
            body = e.read().decode('utf-8', errors='replace')
            return jsonify({'error': f'GitHub API error checking VERSION: {e.code}', 'output': body}), 500
    except Exception as e:
        return jsonify({'error': f'Failed to check VERSION on GitHub: {str(e)}'}), 500

    # Update/create VERSION file on GitHub
    try:
        put_url = f'https://api.github.com/repos/{github_repo}/contents/VERSION'
        put_payload = {
            'message': f'chore: sync VERSION to {local_version}',
            'content': base64.b64encode(local_version.encode('utf-8')).decode('utf-8'),
            'branch': 'main'
        }
        if current_sha:
            put_payload['sha'] = current_sha

        put_req = urllib.request.Request(
            put_url,
            data=json.dumps(put_payload).encode('utf-8'),
            headers={
                'Authorization': f'Bearer {github_token}',
                'Accept': 'application/vnd.github+json',
                'X-GitHub-Api-Version': '2022-11-28',
                'Content-Type': 'application/json',
            },
            method='PUT'
        )
        with urllib.request.urlopen(put_req) as resp:
            if resp.status not in (200, 201):
                return jsonify({'error': f'GitHub API returned {resp.status} when updating VERSION'}), 500
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', errors='replace')
        return jsonify({'error': f'Failed to update VERSION on GitHub: {e.code}', 'output': body}), 500
    except Exception as e:
        return jsonify({'error': f'Failed to sync VERSION file: {str(e)}'}), 500

    # Step 3: Dispatch workflow
    try:
        dispatch_url = f'https://api.github.com/repos/{github_repo}/actions/workflows/{workflow}/dispatches'
        dispatch_payload = json.dumps({
            'ref': 'main'
        }).encode('utf-8')

        dispatch_req = urllib.request.Request(
            dispatch_url,
            data=dispatch_payload,
            headers={
                'Authorization': f'Bearer {github_token}',
                'Accept': 'application/vnd.github+json',
                'X-GitHub-Api-Version': '2022-11-28',
                'Content-Type': 'application/json',
            },
            method='POST'
        )

        with urllib.request.urlopen(dispatch_req) as resp:
            # 204 No Content = success
            if resp.status == 204:
                return jsonify({'message': f'VERSION synced to {local_version} and Docker build triggered.'}), 200
            return jsonify({'error': f'Unexpected status {resp.status} when dispatching workflow'}), 500
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', errors='replace')
        return jsonify({'error': f'GitHub API error dispatching workflow: {e.code}', 'output': body}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500
