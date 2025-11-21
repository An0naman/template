"""
Git API - REST endpoints for Git integration
"""
from flask import Blueprint, request, jsonify, g
from functools import wraps
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

git_api_bp = Blueprint('git_api', __name__)

def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is logged in (adapt to your auth system)
        if not hasattr(g, 'user') or not g.user:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

@git_api_bp.route('/api/git/test-repo', methods=['POST'])
def test_repository():
    """Test if a local path is a valid git repository"""
    try:
        data = request.get_json()
        path = data.get('path', '').strip()
        
        if not path:
            return jsonify({
                'success': False,
                'error': 'Path is required'
            }), 400
        
        import os
        from git import Repo, InvalidGitRepositoryError
        
        if not os.path.exists(path):
            return jsonify({
                'success': False,
                'error': f'Path does not exist: {path}'
            }), 400
        
        try:
            repo = Repo(path)
            commits = list(repo.iter_commits(max_count=100))
            
            return jsonify({
                'success': True,
                'commit_count': len(commits),
                'current_branch': repo.active_branch.name if repo.active_branch else 'unknown',
                'message': 'Valid Git repository'
            })
        except InvalidGitRepositoryError:
            return jsonify({
                'success': False,
                'error': f'Not a valid Git repository: {path}'
            }), 400
            
    except Exception as e:
        logger.error(f"Failed to test repository: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@git_api_bp.route('/api/git/repositories', methods=['GET'])
def list_repositories():
    """List all tracked repositories from GitRepository table"""
    try:
        from app.db import get_connection
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # Get all repositories with their commit counts
        cursor.execute('''
            SELECT 
                r.id,
                r.name,
                r.url,
                r.local_path,
                r.default_branch,
                r.last_synced,
                r.entry_type_id,
                r.allowed_statuses,
                COUNT(c.id) as total_commits
            FROM GitRepository r
            LEFT JOIN GitCommit c ON r.id = c.repository_id
            GROUP BY r.id
            ORDER BY r.name
        ''')
        
        rows = cursor.fetchall()
        repositories = []
        
        for row in rows:
            repositories.append({
                'id': row['id'],
                'name': row['name'],
                'url': row['url'],
                'local_path': row['local_path'],
                'default_branch': row['default_branch'],
                'last_synced': row['last_synced'],
                'entry_type_id': row['entry_type_id'],
                'allowed_statuses': row['allowed_statuses'],
                'stats': {
                    'total_commits': row['total_commits']
                }
            })
        
        return jsonify({
            'success': True,
            'repositories': repositories
        })
    
    except Exception as e:
        logger.error(f"Failed to list repositories: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@git_api_bp.route('/api/git/discover', methods=['POST'])
def discover_repositories():
    """Discover repositories from GitHub/GitLab using Personal Access Token"""
    try:
        data = request.get_json()
        
        provider = data.get('provider')  # 'github' or 'gitlab'
        token = data.get('token')
        gitlab_url = data.get('gitlab_url', 'https://gitlab.com')
        
        if not provider or not token:
            return jsonify({
                'success': False,
                'error': 'provider and token are required'
            }), 400
        
        from app.services.git_service import get_git_service
        git_service = get_git_service()
        
        repos = []
        if provider == 'github':
            if not git_service.connect_github(token):
                return jsonify({
                    'success': False,
                    'error': 'Failed to connect to GitHub. Check your token.'
                }), 401
            repos = git_service.discover_github_repos()
        elif provider == 'gitlab':
            if not git_service.connect_gitlab(token, gitlab_url):
                return jsonify({
                    'success': False,
                    'error': 'Failed to connect to GitLab. Check your token.'
                }), 401
            repos = git_service.discover_gitlab_repos()
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid provider. Use "github" or "gitlab".'
            }), 400
        
        return jsonify({
            'success': True,
            'repositories': repos,
            'total': len(repos)
        })
    
    except Exception as e:
        logger.error(f"Failed to discover repositories: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@git_api_bp.route('/api/git/repositories', methods=['POST'])
def add_repository():
    """Add a discovered repository to tracking"""
    try:
        data = request.get_json()
        
        # Accept either wrapped format {repo_data: {...}} or direct format {...}
        if 'repo_data' in data:
            repo_data = data['repo_data']
        else:
            # Direct format - extract repo fields
            repo_data = {
                'name': data.get('name'),
                'url': data.get('url'),
                'description': data.get('description', ''),
                'default_branch': data.get('default_branch', 'main'),
                'is_private': data.get('is_private', False)
            }
        
        # Validate required fields
        if not repo_data.get('name') or not repo_data.get('url'):
            return jsonify({
                'success': False,
                'error': 'Missing required fields: name and url'
            }), 400
        
        # Get token from data
        token = data.get('token')
        if not token:
            return jsonify({
                'success': False,
                'error': 'Token is required for cloning repository'
            }), 400
        
        from app.services.git_service import get_git_service
        git_service = get_git_service()
        
        repo_id = git_service.add_repository(
            repo_data=repo_data,
            token=token,
            entry_type_id=data.get('entry_type_id'),
            auto_create_entries=data.get('auto_create_entries', False)
        )
        
        return jsonify({
            'success': True,
            'repository_id': repo_id,
            'message': 'Repository added successfully'
        }), 201
    
    except Exception as e:
        logger.error(f"Failed to add repository: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@git_api_bp.route('/api/git/repositories/<int:repo_id>', methods=['GET'])
def get_repository(repo_id):
    """Get repository details"""
    try:
        from app.services.git_service import get_git_service
        git_service = get_git_service()
        
        repository = git_service.get_repository(repo_id)
        
        if not repository:
            return jsonify({
                'success': False,
                'error': 'Repository not found'
            }), 404
        
        # Add stats
        try:
            stats = git_service.get_repository_stats(repo_id)
            repository['stats'] = stats
        except Exception as e:
            logger.warning(f"Could not get stats for repo {repo_id}: {e}")
            repository['stats'] = {}
        
        # Don't send encrypted credentials to client
        if 'credentials_encrypted' in repository:
            del repository['credentials_encrypted']
        if 'credentials' in repository:
            del repository['credentials']
        
        return jsonify({
            'success': True,
            'repository': repository
        })
    
    except Exception as e:
        logger.error(f"Failed to get repository: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@git_api_bp.route('/api/git/repositories/<int:repo_id>', methods=['PATCH'])
def update_repository(repo_id):
    """Update repository configuration"""
    try:
        data = request.get_json() or {}
        
        from app.db import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        
        # Verify repository exists
        cursor.execute('SELECT id FROM GitRepository WHERE id = ?', (repo_id,))
        if not cursor.fetchone():
            return jsonify({
                'success': False,
                'error': 'Repository not found'
            }), 404
        
        # Build update query dynamically based on provided fields
        updates = []
        params = []
        
        if 'entry_type_id' in data:
            updates.append('entry_type_id = ?')
            params.append(data['entry_type_id'])
        
        if 'allowed_statuses' in data:
            updates.append('allowed_statuses = ?')
            params.append(data['allowed_statuses'])
        
        if not updates:
            return jsonify({
                'success': False,
                'error': 'No fields to update'
            }), 400
        
        # Update the repository
        params.append(repo_id)
        query = f"UPDATE GitRepository SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, params)
        conn.commit()
        
        return jsonify({
            'success': True,
            'message': 'Repository updated successfully'
        })
    
    except Exception as e:
        logger.error(f"Failed to update repository: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@git_api_bp.route('/api/git/repositories/<int:repo_id>/sync', methods=['POST'])
def sync_repository(repo_id):
    """Sync repository commits and branches"""
    try:
        data = request.get_json() or {}
        limit = data.get('limit', 100)
        
        from app.services.git_service import get_git_service
        git_service = get_git_service()
        
        # Verify repository exists
        repository = git_service.get_repository(repo_id)
        if not repository:
            return jsonify({
                'success': False,
                'error': 'Repository not found'
            }), 404
        
        # Sync commits
        result = git_service.sync_commits(repo_id, limit=limit)
        
        return jsonify({
            'success': True,
            'result': result,
            'message': f"Synced {result['synced']} new commits"
        })
    
    except Exception as e:
        logger.error(f"Failed to sync repository {repo_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@git_api_bp.route('/api/git/repositories/<int:repo_id>/commits', methods=['GET'])
def get_commits(repo_id):
    """Get commit history for repository"""
    try:
        # Get query parameters
        limit = request.args.get('limit', 50, type=int)
        branch = request.args.get('branch')
        
        from app.services.git_service import get_git_service
        from app.db import get_connection
        
        git_service = get_git_service()
        
        # Get commits from database (already synced)
        conn = get_connection()
        cursor = conn.cursor()
        
        query = '''
            SELECT c.*, r.name as repo_name, e.id as entry_id, e.title as entry_title
            FROM GitCommit c
            JOIN GitRepository r ON c.repository_id = r.id
            LEFT JOIN Entry e ON c.entry_id = e.id
            WHERE c.repository_id = ?
        '''
        params = [repo_id]
        
        if branch:
            query += ' AND c.branch = ?'
            params.append(branch)
        
        query += ' ORDER BY c.commit_date DESC LIMIT ?'
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        columns = [desc[0] for desc in cursor.description]
        commits = []
        
        for row in rows:
            commit = dict(zip(columns, row))
            # Format date
            if commit.get('commit_date'):
                commit['commit_date'] = commit['commit_date']
            commits.append(commit)
        
        return jsonify({
            'success': True,
            'commits': commits,
            'total': len(commits)
        })
    
    except Exception as e:
        logger.error(f"Failed to get commits for repo {repo_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@git_api_bp.route('/api/git/repositories/<int:repo_id>/branches', methods=['GET'])
def get_branches(repo_id):
    """Get branches for repository"""
    try:
        from app.services.git_service import get_git_service
        git_service = get_git_service()
        
        branches = git_service.get_branches(repo_id)
        
        return jsonify({
            'success': True,
            'branches': branches,
            'total': len(branches)
        })
    
    except Exception as e:
        logger.error(f"Failed to get branches for repo {repo_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@git_api_bp.route('/api/git/commits/<string:commit_hash>/create-entry', methods=['POST'])
def create_entry_from_commit(commit_hash):
    """Create entry from commit"""
    try:
        data = request.get_json() or {}
        entry_type_id = data.get('entry_type_id')
        custom_title = data.get('title')
        custom_status = data.get('status')
        
        if not entry_type_id:
            return jsonify({
                'success': False,
                'error': 'entry_type_id is required'
            }), 400
        
        from app.db import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        
        # Get commit details
        cursor.execute('''
            SELECT c.*, r.name as repo_name
            FROM GitCommit c
            JOIN GitRepository r ON c.repository_id = r.id
            WHERE c.commit_hash = ?
        ''', (commit_hash,))
        
        row = cursor.fetchone()
        if not row:
            return jsonify({
                'success': False,
                'error': 'Commit not found'
            }), 404
        
        columns = [desc[0] for desc in cursor.description]
        commit = dict(zip(columns, row))
        
        # Check if entry already exists
        if commit.get('entry_id'):
            return jsonify({
                'success': False,
                'error': 'Entry already exists for this commit',
                'entry_id': commit['entry_id']
            }), 400
        
        # Create entry - use custom title and status if provided
        title = custom_title if custom_title else commit['message'][:200]
        description = f"""**Commit:** `{commit['commit_hash'][:7]}`
**Repository:** {commit['repo_name']}
**Author:** {commit['author']} <{commit['author_email']}>
**Date:** {commit['commit_date']}

{commit['message_body'] or commit['message']}

---
**Changes:**
- Files changed: {commit['files_changed']}
- Insertions: +{commit['insertions']}
- Deletions: -{commit['deletions']}
"""
        
        # Determine status - use custom if provided, otherwise get default for entry type
        status = custom_status
        if not status:
            # Get default status for this entry type
            cursor.execute('''
                SELECT name FROM EntryState 
                WHERE entry_type_id = ? AND is_default = 1
                LIMIT 1
            ''', (entry_type_id,))
            default_state = cursor.fetchone()
            status = default_state[0] if default_state else 'active'
        
        cursor.execute('''
            INSERT INTO Entry (entry_type_id, title, description, status, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (entry_type_id, title, description, status, commit['commit_date']))
        
        entry_id = cursor.lastrowid
        
        # Link commit to entry
        cursor.execute('''
            UPDATE GitCommit SET entry_id = ? WHERE commit_hash = ?
        ''', (entry_id, commit_hash))
        
        conn.commit()
        
        return jsonify({
            'success': True,
            'entry_id': entry_id,
            'message': 'Entry created successfully'
        }), 201
    
    except Exception as e:
        logger.error(f"Failed to create entry from commit: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@git_api_bp.route('/api/git/repositories/<int:repo_id>/stats', methods=['GET'])
def get_repository_stats(repo_id):
    """Get statistics for repository"""
    try:
        from app.services.git_service import get_git_service
        git_service = get_git_service()
        
        stats = git_service.get_repository_stats(repo_id)
        
        return jsonify({
            'success': True,
            'stats': stats
        })
    
    except Exception as e:
        logger.error(f"Failed to get stats for repo {repo_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@git_api_bp.route('/api/entries/<int:entry_id>/git/link', methods=['POST'])
def link_git_commit(entry_id):
    """Link existing entry to Git commit"""
    try:
        data = request.get_json()
        commit_hash = data.get('commit_hash')
        
        if not commit_hash:
            return jsonify({
                'success': False,
                'error': 'commit_hash is required'
            }), 400
        
        from app.db import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        
        # Verify entry exists
        cursor.execute('SELECT id FROM Entry WHERE id = ?', (entry_id,))
        if not cursor.fetchone():
            return jsonify({
                'success': False,
                'error': 'Entry not found'
            }), 404
        
        # Verify commit exists
        cursor.execute('SELECT id FROM GitCommit WHERE commit_hash = ?', (commit_hash,))
        if not cursor.fetchone():
            return jsonify({
                'success': False,
                'error': 'Commit not found'
            }), 404
        
        # Link them
        cursor.execute('''
            UPDATE GitCommit SET entry_id = ? WHERE commit_hash = ?
        ''', (entry_id, commit_hash))
        
        conn.commit()
        
        return jsonify({
            'success': True,
            'message': 'Entry linked to commit successfully'
        })
    
    except Exception as e:
        logger.error(f"Failed to link entry to commit: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@git_api_bp.route('/api/git/commits/<commit_hash>/unlink', methods=['POST'])
def unlink_commit_from_entry(commit_hash):
    """Unlink a commit from its entry"""
    try:
        from app.db import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        
        # Verify commit exists
        cursor.execute('SELECT id, entry_id FROM GitCommit WHERE commit_hash = ?', (commit_hash,))
        commit = cursor.fetchone()
        
        if not commit:
            return jsonify({
                'success': False,
                'error': 'Commit not found'
            }), 404
        
        if not commit['entry_id']:
            return jsonify({
                'success': False,
                'error': 'Commit is not linked to any entry'
            }), 400
        
        # Unlink
        cursor.execute('''
            UPDATE GitCommit SET entry_id = NULL WHERE commit_hash = ?
        ''', (commit_hash,))
        
        conn.commit()
        
        return jsonify({
            'success': True,
            'message': 'Commit unlinked successfully'
        })
    
    except Exception as e:
        logger.error(f"Failed to unlink commit: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@git_api_bp.route('/api/entries/<int:entry_id>/git/commits', methods=['GET'])
def get_entry_commits(entry_id):
    """Get all git commits linked to an entry"""
    try:
        from app.db import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        
        # Verify entry exists
        cursor.execute('SELECT id FROM Entry WHERE id = ?', (entry_id,))
        if not cursor.fetchone():
            return jsonify({
                'success': False,
                'error': 'Entry not found'
            }), 404
        
        # Check if GitCommit table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='GitCommit'
        """)
        if not cursor.fetchone():
            # Git integration tables don't exist yet
            return jsonify({
                'success': True,
                'commits': [],
                'count': 0
            })
        
        # Get all commits linked to this entry
        cursor.execute('''
            SELECT 
                c.commit_hash,
                c.message,
                c.message_body,
                c.author,
                c.author_email,
                c.commit_date,
                c.files_changed,
                c.insertions,
                c.deletions,
                r.name as repository_name,
                r.url as repository_url,
                r.provider
            FROM GitCommit c
            JOIN GitRepository r ON c.repository_id = r.id
            WHERE c.entry_id = ?
            ORDER BY c.commit_date DESC
        ''', (entry_id,))
        
        columns = [desc[0] for desc in cursor.description]
        commits = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        # Add URL to view commit if available
        for commit in commits:
            if commit['repository_url'] and commit['provider']:
                base_url = commit['repository_url'].rstrip('/')
                if commit['provider'] == 'github':
                    commit['url'] = f"{base_url}/commit/{commit['commit_hash']}"
                elif commit['provider'] == 'gitlab':
                    commit['url'] = f"{base_url}/-/commit/{commit['commit_hash']}"
                else:
                    commit['url'] = None
            else:
                commit['url'] = None
        
        return jsonify({
            'success': True,
            'commits': commits,
            'count': len(commits)
        })
    
    except Exception as e:
        logger.error(f"Failed to get commits for entry {entry_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
