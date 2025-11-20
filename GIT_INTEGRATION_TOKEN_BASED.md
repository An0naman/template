# Git Integration - Token-Based Discovery Implementation

## Overview
This document describes the token-based Git integration feature that allows users to connect their GitHub or GitLab accounts and automatically discover repositories to track.

## Key Features
- **Provider Support**: GitHub and GitLab (including self-hosted instances)
- **Auto-Discovery**: Automatically discover all repositories from connected account
- **Selective Tracking**: Toggle which repositories to track
- **Dashboard Widget**: Embedded Git widget in main dashboard showing commits
- **Secure Token Storage**: Personal Access Tokens stored in system parameters

## Architecture

### Database Schema
Three main tables created by `migrations/add_git_integration.py`:

1. **GitRepository**: Stores tracked repositories
   - name, url, local_path, default_branch
   - credentials_encrypted (deprecated, kept for backward compatibility)
   - entry_type_id, auto_sync, sync_interval
   - commit_types filter

2. **GitCommit**: Stores commit history
   - repository_id, commit_hash, author, message
   - commit_date, branch, files_changed
   - insertions, deletions
   - entry_id (for linking commits to entries)

3. **GitBranch**: Stores branch information
   - repository_id, name, is_default
   - last_commit_hash, last_commit_date
   - entry_id (for linking branches to entries)

### System Parameters
New parameters added for Git configuration:
- `git_provider`: 'github' or 'gitlab'
- `git_token`: Personal Access Token (PAT)
- `gitlab_url`: URL for self-hosted GitLab instances (default: https://gitlab.com)

## Components

### Backend Services

#### `app/services/git_service.py`
Core Git operations service:
- `connect_github(token)`: Authenticate with GitHub API using PyGithub
- `connect_gitlab(token, url)`: Authenticate with GitLab API
- `discover_github_repos()`: Fetch all user repos from GitHub
- `discover_gitlab_repos()`: Fetch all user repos from GitLab
- `add_repository(repo_data)`: Add discovered repo to tracking
- `clone_or_open_repository(repo_id, token)`: Clone/pull repo using token in URL
- `get_repository_stats(repo_id)`: Get commit counts and stats
- `get_commits(repo_id, limit)`: Fetch commit history

**Dependencies**:
- GitPython>=3.1.40 - Core Git operations
- PyGithub>=2.1.1 - GitHub API client
- python-gitlab>=4.4.0 - GitLab API client

### API Endpoints

#### `app/api/git_api.py`

**POST /api/git/discover**
Discovers repositories from GitHub/GitLab account.

Request:
```json
{
  "provider": "github|gitlab",
  "token": "personal_access_token",
  "gitlab_url": "https://gitlab.com" // optional, for GitLab only
}
```

Response:
```json
{
  "success": true,
  "provider": "github",
  "repositories": [
    {
      "name": "repo-name",
      "url": "https://github.com/user/repo.git",
      "description": "Repository description",
      "default_branch": "main",
      "is_private": false
    }
  ]
}
```

**POST /api/git/repositories**
Add a discovered repository to tracking.

Request:
```json
{
  "name": "repo-name",
  "url": "https://github.com/user/repo.git",
  "default_branch": "main",
  "token": "personal_access_token"
}
```

**GET /api/git/repositories**
List all tracked repositories.

**GET /api/git/repositories/{id}/commits**
Get commit history for a repository.

Query parameters:
- `limit`: Number of commits to return (default: 50)
- `branch`: Branch name (optional)

**POST /api/git/repositories/{id}/sync**
Sync latest commits from remote repository.

### Frontend Components

#### `app/templates/components/git_widget.html`
Embeddable dashboard widget:
- Shows list of tracked repositories
- Displays commit history for selected repo
- Handles empty state with "Connect Provider" message
- Auto-initializes when URL includes `?show_git=1` or `#git`

#### `app/templates/settings.html` - Git Integration Section
Configuration interface:
1. **Provider Selection**: Dropdown to choose GitHub or GitLab
2. **GitLab URL**: Conditional field for self-hosted instances
3. **Personal Access Token**: Password field for PAT
4. **Discover Button**: Triggers repository discovery
5. **Repository List**: Displays discovered repos with toggle switches
6. **Save Button**: Adds selected repos to tracking

JavaScript features:
- Dynamic GitLab URL field visibility
- Token help links (guides to create PATs)
- Discovery workflow with status messages
- Toggle switches for selective repo tracking
- Auto-redirect to dashboard after saving

## User Workflow

### Setup Process
1. Navigate to Settings > Git Integration
2. Select Git provider (GitHub or GitLab)
3. Enter Personal Access Token
   - GitHub: Needs `repo` scope
   - GitLab: Needs `read_api` and `read_repository` scopes
4. Click "Discover Repositories"
5. Toggle repositories to track
6. Click "Save Tracked Repositories"
7. Redirected to dashboard with Git widget visible

### Viewing Commits
1. Dashboard shows Git widget with tracked repos
2. Click on repository to view commits
3. Recent 10 commits displayed by default
4. Refresh button syncs latest commits

## Token Requirements

### GitHub Personal Access Token
Scopes needed:
- `repo` - Full control of private repositories (includes read access)

Create at: https://github.com/settings/tokens

### GitLab Personal Access Token
Scopes needed:
- `read_api` - Read access to API
- `read_repository` - Read access to repositories

Create at: https://gitlab.com/-/profile/personal_access_tokens

## Security Considerations

1. **Token Storage**: Tokens stored in SystemParameters table (plaintext in DB)
   - Consider encrypting in future update
   - Tokens needed for git clone/pull operations

2. **Token Usage**: 
   - Used for API calls to discover repos
   - Embedded in git URLs for authenticated clone/pull
   - Format: `https://<username>:<token>@github.com/user/repo.git`

3. **Permissions**:
   - Only read access required
   - No write operations to repositories
   - User must explicitly enable tracking per repo

## Docker Deployment

### Migration
Auto-runs via `docker-entrypoint.sh`:
```bash
python migrations/add_git_integration.py
```

### Environment Variables
No additional environment variables required. Tokens configured via web UI.

### Volume Mounts
Repositories cloned to `/app/repos/` directory (consider adding volume mount to persist clones).

## Future Enhancements

### Planned Features
- [ ] Webhook support for real-time commit tracking
- [ ] Commit-to-entry automation (auto-create entries from commits)
- [ ] Branch comparison view
- [ ] Pull request tracking
- [ ] Commit statistics and graphs
- [ ] Multi-account support
- [ ] Token encryption at rest
- [ ] Support for Bitbucket and other providers

### Known Limitations
- No write operations (commits, pushes)
- No merge request/pull request tracking
- No code review features
- Tokens stored in plaintext (consider encryption)
- No support for SSH keys (only HTTPS with tokens)

## Troubleshooting

### "Discovery failed: Bad credentials"
- Token is invalid or expired
- Token lacks required scopes
- For GitLab: Check URL is correct for self-hosted instances

### "No repositories found"
- User has no repositories in account
- Token lacks `repo` (GitHub) or `read_repository` (GitLab) scope
- For GitLab: User may not have access to any projects

### "Failed to clone repository"
- Token expired or revoked
- Repository is private and token lacks access
- Network connectivity issues
- Disk space issues (check `/app/repos/` directory)

### Empty dashboard widget
- No repositories added to tracking yet
- Click "Connect Provider" to configure in Settings
- Verify migration ran successfully (`docker logs` to check)

## Testing

### Manual Testing Checklist
- [ ] Settings page loads Git Integration section
- [ ] Provider dropdown shows GitHub/GitLab
- [ ] GitLab URL field shows/hides correctly
- [ ] Token help link opens correct documentation
- [ ] Discovery button triggers API call
- [ ] Discovered repos display with toggles
- [ ] Toggling repos updates selection
- [ ] Save button adds repos to tracking
- [ ] Dashboard redirects and shows Git widget
- [ ] Widget displays tracked repos
- [ ] Clicking repo loads commits
- [ ] Commits display with author, date, message
- [ ] Refresh button syncs latest commits

### API Testing
```bash
# Discover repos
curl -X POST http://localhost:5000/api/git/discover \
  -H "Content-Type: application/json" \
  -d '{"provider":"github","token":"ghp_xxxxx"}'

# Add repository
curl -X POST http://localhost:5000/api/git/repositories \
  -H "Content-Type: application/json" \
  -d '{"name":"test-repo","url":"https://github.com/user/repo.git","token":"ghp_xxxxx"}'

# List repositories
curl http://localhost:5000/api/git/repositories

# Get commits
curl http://localhost:5000/api/git/repositories/1/commits?limit=10

# Sync repository
curl -X POST http://localhost:5000/api/git/repositories/1/sync
```

## Files Modified

### New Files
- `migrations/add_git_integration.py` - Database migration
- `app/services/git_service.py` - Git operations service
- `app/api/git_api.py` - REST API endpoints
- `app/routes/git_routes.py` - Page routes
- `app/templates/components/git_widget.html` - Dashboard widget

### Modified Files
- `requirements.txt` - Added GitPython, PyGithub, python-gitlab
- `app/__init__.py` - Registered Git blueprints
- `app/api/system_params_api.py` - Added git_provider, git_token, gitlab_url params
- `app/templates/settings.html` - Added Git Integration section
- `app/templates/dashboard.html` - Included git_widget.html

## Migration Notes

### From Local Repo to Token-Based
If migrating from previous local-only implementation:
1. Old system params removed: `git_local_repo_path`, `git_auto_create_entries`, `git_entry_type_id`
2. New system params: `git_provider`, `git_token`, `gitlab_url`
3. Database schema unchanged (backward compatible)
4. `credentials_encrypted` field deprecated but kept for future use

### Docker Rebuild Required
After updating code:
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

Migration will auto-run on container start.

## References

- [GitHub REST API](https://docs.github.com/en/rest)
- [GitLab API](https://docs.gitlab.com/ee/api/)
- [PyGithub Documentation](https://pygithub.readthedocs.io/)
- [python-gitlab Documentation](https://python-gitlab.readthedocs.io/)
- [GitPython Documentation](https://gitpython.readthedocs.io/)
