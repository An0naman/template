"""
Git Service - Handles Git repository operations using Personal Access Tokens
Simplified to auto-discover repos from GitHub/GitLab accounts
"""
import git
from git import Repo, InvalidGitRepositoryError, GitCommandError
import os
import logging
from datetime import datetime
from typing import Optional, Dict, List, Tuple
import sqlite3

try:
    from github import Github, GithubException
except ImportError:
    Github = None
    GithubException = Exception

try:
    from gitlab import Gitlab
    from gitlab.exceptions import GitlabError
except ImportError:
    Gitlab = None
    GitlabError = Exception

logger = logging.getLogger(__name__)

class GitService:
    """Service for Git repository operations using Personal Access Tokens"""
    
    def __init__(self, db_connection):
        self.conn = db_connection
        self.github_client = None
        self.gitlab_client = None
    
    @staticmethod
    def _safe_rmtree(path: str):
        """Safely remove a directory tree, handling permission issues"""
        import shutil
        import stat
        
        def handle_remove_readonly(func, path, exc):
            """Error handler for Windows and read-only files"""
            os.chmod(path, stat.S_IWRITE)
            func(path)
        
        try:
            shutil.rmtree(path, onerror=handle_remove_readonly)
        except Exception as e:
            logger.warning(f"Failed to remove {path}: {e}, trying with ignore_errors")
            shutil.rmtree(path, ignore_errors=True)
    
    def connect_github(self, token: str) -> bool:
        """Connect to GitHub using Personal Access Token"""
        if not Github:
            logger.error("PyGithub not installed")
            return False
        
        try:
            self.github_client = Github(token)
            # Test connection
            user = self.github_client.get_user()
            logger.info(f"Connected to GitHub as {user.login}")
            return True
        except Exception as e:
            logger.error(f"GitHub connection failed: {e}")
            return False
    
    def connect_gitlab(self, token: str, url: str = "https://gitlab.com") -> bool:
        """Connect to GitLab using Personal Access Token"""
        if not Gitlab:
            logger.error("python-gitlab not installed")
            return False
        
        try:
            self.gitlab_client = Gitlab(url, private_token=token)
            self.gitlab_client.auth()
            user = self.gitlab_client.user
            logger.info(f"Connected to GitLab as {user.username}")
            return True
        except Exception as e:
            logger.error(f"GitLab connection failed: {e}")
            return False
    
    def discover_github_repos(self) -> List[Dict]:
        """Discover all repositories from connected GitHub account"""
        if not self.github_client:
            logger.error("GitHub client not connected")
            return []
        
        repos = []
        try:
            for repo in self.github_client.get_user().get_repos():
                repos.append({
                    'id': str(repo.id),
                    'name': repo.name,
                    'full_name': repo.full_name,
                    'url': repo.clone_url,
                    'ssh_url': repo.ssh_url,
                    'description': repo.description or '',
                    'default_branch': repo.default_branch or 'main',
                    'private': repo.private,
                    'language': repo.language,
                    'updated_at': repo.updated_at.isoformat() if repo.updated_at else None,
                    'size': repo.size,
                    'provider': 'github'
                })
            logger.info(f"Discovered {len(repos)} GitHub repositories")
        except Exception as e:
            logger.error(f"Error discovering GitHub repos: {e}")
        
        return repos
    
    def discover_gitlab_repos(self) -> List[Dict]:
        """Discover all repositories from connected GitLab account"""
        if not self.gitlab_client:
            logger.error("GitLab client not connected")
            return []
        
        repos = []
        try:
            projects = self.gitlab_client.projects.list(membership=True, all=True)
            for project in projects:
                repos.append({
                    'id': str(project.id),
                    'name': project.name,
                    'full_name': project.path_with_namespace,
                    'url': project.http_url_to_repo,
                    'ssh_url': project.ssh_url_to_repo,
                    'description': project.description or '',
                    'default_branch': project.default_branch or 'main',
                    'private': project.visibility == 'private',
                    'language': None,
                    'updated_at': project.last_activity_at,
                    'size': 0,
                    'provider': 'gitlab'
                })
            logger.info(f"Discovered {len(repos)} GitLab repositories")
        except Exception as e:
            logger.error(f"Error discovering GitLab repos: {e}")
        
        return repos
    
    def add_repository(self, repo_data: Dict, token: Optional[str] = None,
                      entry_type_id: Optional[int] = None, 
                      auto_create_entries: bool = False) -> int:
        """Add a discovered repository to tracking"""
        cursor = self.conn.cursor()
        
        cursor.execute('''
            INSERT INTO GitRepository 
            (name, url, local_path, default_branch, entry_type_id, 
             auto_sync, auto_create_entries)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            repo_data['name'],
            repo_data['url'],
            None,  # Will be set when first cloned
            repo_data.get('default_branch', 'main'),
            entry_type_id,
            True,  # Auto-sync enabled by default
            auto_create_entries
        ))
        
        self.conn.commit()
        repo_id = cursor.lastrowid
        
        logger.info(f"Added repository: {repo_data['name']} (ID: {repo_id})")
        
        # Clone the repository immediately if token provided
        if token:
            try:
                self.clone_or_open_repository(repo_id, token)
                logger.info(f"Successfully cloned repository: {repo_data['name']}")
            except Exception as e:
                logger.error(f"Failed to clone repository {repo_data['name']}: {e}")
                # Don't fail the add operation if clone fails
        return repo_id
    
    def get_repository(self, repo_id: int) -> Optional[Dict]:
        """Get repository details"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM GitRepository WHERE id = ?', (repo_id,))
        row = cursor.fetchone()
        
        if not row:
            return None
        
        columns = [desc[0] for desc in cursor.description]
        repo = dict(zip(columns, row))
        
        # Decrypt credentials if present
        if repo.get('credentials_encrypted'):
            repo['credentials'] = self.decrypt_credentials(repo['credentials_encrypted'])
        
        return repo
    
    def list_repositories(self) -> List[Dict]:
        """List all repositories"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM GitRepository ORDER BY created_at DESC')
        rows = cursor.fetchall()
        
        columns = [desc[0] for desc in cursor.description]
        repositories = []
        
        for row in rows:
            repo = dict(zip(columns, row))
            repositories.append(repo)
        
        return repositories
    
    def clone_or_open_repository(self, repo_id: int, token: Optional[str] = None) -> Tuple[Repo, str]:
        """Clone repository if needed or open existing (uses token for authentication)"""
        repo_info = self.get_repository(repo_id)
        if not repo_info:
            raise ValueError(f"Repository {repo_id} not found")
        
        local_path = repo_info.get('local_path')
        
        # If no local path, create one
        if not local_path:
            repos_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'git_repos')
            os.makedirs(repos_dir, exist_ok=True)
            local_path = os.path.join(repos_dir, f"repo_{repo_id}")
            
            # Update database with local path
            cursor = self.conn.cursor()
            cursor.execute('UPDATE GitRepository SET local_path = ? WHERE id = ?',
                         (local_path, repo_id))
            self.conn.commit()
        
        # Check if path exists and is a git repository
        if not os.path.exists(local_path):
            # Path doesn't exist, need to clone
            logger.info(f"Local path {local_path} doesn't exist, cloning repository from {repo_info['url']}")
            clone_url = repo_info['url']
            
            if token:
                if 'github.com' in clone_url:
                    clone_url = clone_url.replace('https://', f'https://{token}@')
                elif 'gitlab.com' in clone_url:
                    clone_url = clone_url.replace('https://', f'https://oauth2:{token}@')
            
            try:
                repo = Repo.clone_from(clone_url, local_path)
                logger.info(f"Cloned repository to {local_path}")
            except GitCommandError as clone_error:
                # If clone fails because directory exists, clean it up and retry
                if 'already exists and is not an empty directory' in str(clone_error):
                    logger.warning(f"Directory {local_path} exists but is not empty, cleaning up")
                    self._safe_rmtree(local_path)
                    repo = Repo.clone_from(clone_url, local_path)
                    logger.info(f"Cloned repository to {local_path} after cleanup")
                else:
                    raise
        elif os.path.exists(local_path) and not os.path.exists(os.path.join(local_path, '.git')):
            # Path exists but is not a git repository - clean it and clone
            logger.warning(f"Path {local_path} exists but is not a git repo, removing and re-cloning")
            self._safe_rmtree(local_path)
            
            clone_url = repo_info['url']
            if token:
                if 'github.com' in clone_url:
                    clone_url = clone_url.replace('https://', f'https://{token}@')
                elif 'gitlab.com' in clone_url:
                    clone_url = clone_url.replace('https://', f'https://oauth2:{token}@')
            
            repo = Repo.clone_from(clone_url, local_path)
            logger.info(f"Cloned repository to {local_path}")
        else:
            # Path exists, try to open as git repo
            try:
                repo = Repo(local_path)
                logger.info(f"Opened existing repository at {local_path}")
                
                # Check for corrupted refs before attempting operations
                # list(repo.refs) doesn't validate ref names, so we need to check manually
                has_invalid_refs = False
                try:
                    refs_to_check = list(repo.refs)
                    for ref in refs_to_check:
                        ref_name = ref.name
                        # Check for invalid ref names that will cause iter_commits to fail
                        if ref_name.startswith('.') or '/.' in ref_name or ref_name.endswith('.'):
                            logger.warning(f"Found invalid ref: {ref_name}")
                            has_invalid_refs = True
                            # Try to manually delete the ref file
                            try:
                                ref_path = os.path.join(local_path, '.git', 'refs', 'heads', ref_name.replace('refs/heads/', ''))
                                if os.path.exists(ref_path):
                                    os.remove(ref_path)
                                    logger.info(f"Deleted invalid ref file: {ref_path}")
                            except Exception as delete_error:
                                logger.warning(f"Could not delete ref file: {delete_error}")
                except Exception as ref_error:
                    logger.warning(f"Error checking refs: {ref_error}")
                    has_invalid_refs = True
                
                # If we found invalid refs that couldn't be cleaned, re-clone
                if has_invalid_refs:
                    logger.error(f"Repository has invalid refs. Removing and re-cloning.")
                    self._safe_rmtree(local_path)
                    
                    clone_url = repo_info['url']
                    if token:
                        if 'github.com' in clone_url:
                            clone_url = clone_url.replace('https://', f'https://{token}@')
                        elif 'gitlab.com' in clone_url:
                            clone_url = clone_url.replace('https://', f'https://oauth2:{token}@')
                    
                    repo = Repo.clone_from(clone_url, local_path)
                    logger.info(f"Re-cloned repository to {local_path} due to invalid refs")
                    return repo, local_path
                
                # Pull latest changes
                try:
                    origin = repo.remotes.origin
                    # Use token in URL if provided
                    if token:
                        url = repo_info['url']
                        if 'github.com' in url:
                            auth_url = url.replace('https://', f'https://{token}@')
                        elif 'gitlab.com' in url:
                            auth_url = url.replace('https://', f'https://oauth2:{token}@')
                        else:
                            auth_url = url
                        origin.set_url(auth_url)
                    
                    # Clean up any invalid refs before pulling
                    try:
                        for ref in list(repo.refs):
                            # Check for invalid ref names
                            ref_name = ref.name
                            if ref_name.startswith('.') or '/.' in ref_name or ref_name.endswith('.'):
                                logger.warning(f"Removing invalid ref: {ref_name}")
                                try:
                                    ref.delete(repo, ref)
                                except Exception as ref_error:
                                    logger.warning(f"Could not delete invalid ref {ref_name}: {ref_error}")
                    except Exception as ref_check_error:
                        logger.warning(f"Error checking refs: {ref_check_error}")
                    
                    origin.pull()
                    logger.info(f"Pulled latest changes for repo {repo_id}")
                except Exception as e:
                    logger.warning(f"Could not pull latest changes: {e}")
                    # If pull fails due to invalid refs, repository is corrupted - re-clone
                    if 'Invalid reference' in str(e) or 'cannot start with a period' in str(e):
                        logger.error(f"Repository corrupted with invalid refs. Re-cloning.")
                        self._safe_rmtree(local_path)
                        
                        clone_url = repo_info['url']
                        if token:
                            if 'github.com' in clone_url:
                                clone_url = clone_url.replace('https://', f'https://{token}@')
                            elif 'gitlab.com' in clone_url:
                                clone_url = clone_url.replace('https://', f'https://oauth2:{token}@')
                            else:
                                clone_url = repo_info['url']
                        else:
                            clone_url = repo_info['url']
                        
                        repo = Repo.clone_from(clone_url, local_path)
                        logger.info(f"Re-cloned repository to {local_path} due to invalid refs")
                        return repo, local_path
                    
            except InvalidGitRepositoryError:
                # Path exists but is not a valid git repo, remove and re-clone
                logger.warning(f"Path {local_path} exists but is not a valid git repo, removing and re-cloning")
                self._safe_rmtree(local_path)
                
                clone_url = repo_info['url']
                if token:
                    if 'github.com' in clone_url:
                        clone_url = clone_url.replace('https://', f'https://{token}@')
                    elif 'gitlab.com' in clone_url:
                        clone_url = clone_url.replace('https://', f'https://oauth2:{token}@')
                
                repo = Repo.clone_from(clone_url, local_path)
                logger.info(f"Cloned repository to {local_path}")
        
        return repo, local_path
    
    def get_commits(self, repo_id: int, branch: Optional[str] = None, 
                   limit: int = 50, since: Optional[datetime] = None) -> List[Dict]:
        """Get commits from repository"""
        try:
            repo, _ = self.clone_or_open_repository(repo_id)
            
            # Validate branch name if provided
            if branch:
                # Skip invalid branch names (empty, starting with ., or containing /.)
                if not branch or branch.startswith('.') or '/.' in branch:
                    logger.warning(f"Invalid branch name '{branch}', using default branch")
                    branch = None
            
            if branch:
                try:
                    commits_iter = repo.iter_commits(branch, max_count=limit)
                except Exception as e:
                    logger.warning(f"Could not get commits for branch {branch}: {e}")
                    commits_iter = repo.iter_commits(max_count=limit)
            else:
                try:
                    commits_iter = repo.iter_commits(max_count=limit)
                except Exception as e:
                    # If iter_commits fails due to invalid refs, return empty list
                    # The repository will be cleaned up on next access
                    if 'Invalid reference' in str(e) or 'cannot start with a period' in str(e):
                        logger.error(f"Repository has invalid refs, returning empty commit list: {e}")
                        return []
                    raise
            
            commits = []
            for commit in commits_iter:
                # Skip if before 'since' date
                if since and commit.committed_datetime < since:
                    continue
                
                # Get commit stats
                stats = commit.stats.total
                
                # Get branch name if available
                try:
                    # Try to get the current branch we're iterating from
                    if branch:
                        branch_name = branch
                    elif repo.active_branch:
                        # Clean up the branch name from refs path
                        branch_name = repo.active_branch.name
                        if branch_name.startswith('refs/heads/'):
                            branch_name = branch_name.replace('refs/heads/', '')
                    else:
                        branch_name = 'main'
                    
                    # Validate branch name - skip invalid names
                    if branch_name.startswith('.') or '/.' in branch_name:
                        branch_name = 'main'
                except Exception:
                    branch_name = 'main'
                
                commit_data = {
                    'hash': commit.hexsha,
                    'short_hash': commit.hexsha[:7],
                    'author': commit.author.name,
                    'author_email': commit.author.email,
                    'message': commit.message.split('\n')[0],  # First line
                    'message_body': commit.message,
                    'date': commit.committed_datetime,
                    'files_changed': stats['files'],
                    'insertions': stats['insertions'],
                    'deletions': stats['deletions'],
                    'branch': branch_name
                }
                commits.append(commit_data)
            
            return commits
            
        except Exception as e:
            logger.error(f"Failed to get commits for repo {repo_id}: {e}")
            raise
    
    def sync_commits(self, repo_id: int, limit: int = 100) -> Dict:
        """Sync commits to database"""
        repo_info = self.get_repository(repo_id)
        if not repo_info:
            raise ValueError(f"Repository {repo_id} not found")
        
        commits = self.get_commits(repo_id, limit=limit)
        cursor = self.conn.cursor()
        
        synced = 0
        skipped = 0
        
        for commit_data in commits:
            # Check if commit already exists
            cursor.execute('SELECT id FROM GitCommit WHERE commit_hash = ?',
                         (commit_data['hash'],))
            if cursor.fetchone():
                skipped += 1
                continue
            
            # Insert commit
            cursor.execute('''
                INSERT INTO GitCommit 
                (repository_id, commit_hash, author, author_email, message, 
                 message_body, commit_date, branch, files_changed, insertions, deletions)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                repo_id, commit_data['hash'], commit_data['author'],
                commit_data['author_email'], commit_data['message'],
                commit_data['message_body'], commit_data['date'],
                commit_data['branch'],
                commit_data['files_changed'], commit_data['insertions'],
                commit_data['deletions']
            ))
            synced += 1
            
            # Auto-create entry if enabled
            if repo_info['auto_create_entries'] and repo_info['entry_type_id']:
                self._create_entry_from_commit(commit_data, repo_id, repo_info['entry_type_id'])
        
        # Update last synced time
        cursor.execute('UPDATE GitRepository SET last_synced = ? WHERE id = ?',
                     (datetime.now(), repo_id))
        
        self.conn.commit()
        
        logger.info(f"Synced {synced} new commits, skipped {skipped} existing")
        return {'synced': synced, 'skipped': skipped, 'total': len(commits)}
    
    def _create_entry_from_commit(self, commit_data: Dict, repo_id: int, entry_type_id: int):
        """Create an entry from a Git commit"""
        cursor = self.conn.cursor()
        
        # Create entry
        title = commit_data['message'][:200]  # Limit title length
        description = f"""**Commit:** `{commit_data['short_hash']}`
**Author:** {commit_data['author']} <{commit_data['author_email']}>
**Date:** {commit_data['date'].strftime('%Y-%m-%d %H:%M:%S')}

{commit_data['message_body']}

---
**Changes:**
- Files changed: {commit_data['files_changed']}
- Insertions: +{commit_data['insertions']}
- Deletions: -{commit_data['deletions']}
"""
        
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
        ''', (entry_type_id, title, description, status, commit_data['date']))
        
        entry_id = cursor.lastrowid
        
        # Link commit to entry
        cursor.execute('''
            UPDATE GitCommit SET entry_id = ? WHERE commit_hash = ?
        ''', (entry_id, commit_data['hash']))
        
        logger.info(f"Created entry {entry_id} from commit {commit_data['short_hash']}")
    
    def get_branches(self, repo_id: int) -> List[Dict]:
        """Get all branches from repository"""
        try:
            repo, _ = self.clone_or_open_repository(repo_id)
            
            branches = []
            for ref in repo.refs:
                # Skip HEAD references
                if 'HEAD' in ref.name:
                    continue
                
                try:
                    # Extract clean branch name from ref
                    # Handle refs like 'origin/main', 'refs/heads/main', 'refs/remotes/origin/main'
                    branch_name = ref.name
                    if branch_name.startswith('refs/heads/'):
                        branch_name = branch_name.replace('refs/heads/', '')
                    elif branch_name.startswith('refs/remotes/origin/'):
                        branch_name = branch_name.replace('refs/remotes/origin/', '')
                    elif branch_name.startswith('origin/'):
                        branch_name = branch_name.replace('origin/', '')
                    
                    # Skip invalid branch names (starting with . or containing /.)
                    if branch_name.startswith('.') or '/.' in branch_name:
                        logger.debug(f"Skipping invalid branch name: {branch_name}")
                        continue
                    
                    last_commit = ref.commit
                    branch_data = {
                        'name': branch_name,
                        'last_commit_hash': last_commit.hexsha,
                        'last_commit_date': last_commit.committed_datetime,
                        'last_commit_message': last_commit.message.split('\n')[0]
                    }
                    branches.append(branch_data)
                except Exception as e:
                    logger.warning(f"Could not get info for branch {ref.name}: {e}")
            
            return branches
            
        except Exception as e:
            logger.error(f"Failed to get branches for repo {repo_id}: {e}")
            raise
    
    def get_repository_stats(self, repo_id: int) -> Dict:
        """Get statistics for a repository"""
        cursor = self.conn.cursor()
        
        # Total commits
        cursor.execute('SELECT COUNT(*) FROM GitCommit WHERE repository_id = ?', (repo_id,))
        total_commits = cursor.fetchone()[0]
        
        # Commits today
        cursor.execute('''
            SELECT COUNT(*) FROM GitCommit 
            WHERE repository_id = ? AND DATE(commit_date) = DATE('now')
        ''', (repo_id,))
        commits_today = cursor.fetchone()[0]
        
        # Unique authors
        cursor.execute('''
            SELECT COUNT(DISTINCT author) FROM GitCommit WHERE repository_id = ?
        ''', (repo_id,))
        unique_authors = cursor.fetchone()[0]
        
        # Total lines changed
        cursor.execute('''
            SELECT SUM(insertions), SUM(deletions) FROM GitCommit WHERE repository_id = ?
        ''', (repo_id,))
        lines = cursor.fetchone()
        
        return {
            'total_commits': total_commits,
            'commits_today': commits_today,
            'unique_authors': unique_authors,
            'total_insertions': lines[0] or 0,
            'total_deletions': lines[1] or 0
        }


def get_git_service(db_connection=None):
    """Get GitService instance"""
    if db_connection is None:
        from app.db import get_connection
        db_connection = get_connection()
    
    return GitService(db_connection)
