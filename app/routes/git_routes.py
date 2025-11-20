"""
Git Routes - Page routes for Git integration
"""
from flask import Blueprint, render_template, redirect, url_for, flash, g
from functools import wraps
import logging

logger = logging.getLogger(__name__)

git_routes_bp = Blueprint('git_routes', __name__)

def login_required(f):
    """Decorator to require login (adapt to your auth system)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is logged in
        # This is a placeholder - adapt to your authentication system
        if not hasattr(g, 'user') or not g.user:
            # If you have a login route, redirect there
            # For now, just render the page (no auth check)
            pass
        return f(*args, **kwargs)
    return decorated_function

@git_routes_bp.route('/git')
@git_routes_bp.route('/git/dashboard')
def dashboard():
    """DevOps dashboard page"""
    # Redirect into the main dashboard - the Git widget is embedded there
    from flask import redirect, url_for
    return redirect(url_for('main.dashboard', show_git=1))

@git_routes_bp.route('/git/repositories')
def repositories():
    """Repository management page"""
    return render_template('git_dashboard.html')

@git_routes_bp.route('/git/repositories/<int:repo_id>')
def repository_detail(repo_id):
    """Repository detail page"""
    try:
        from app.services.git_service import get_git_service
        git_service = get_git_service()
        
        repository = git_service.get_repository(repo_id)
        if not repository:
            flash('Repository not found', 'error')
            return redirect(url_for('git_routes.dashboard'))
        
        return render_template('git_dashboard.html', selected_repo=repo_id)
    
    except Exception as e:
        logger.error(f"Failed to load repository {repo_id}: {e}")
        flash(f'Failed to load repository: {str(e)}', 'error')
        return redirect(url_for('git_routes.dashboard'))
