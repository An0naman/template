"""Chat page route."""
from flask import Blueprint, render_template

chat_routes_bp = Blueprint('chat', __name__)


@chat_routes_bp.route('/chat')
def chat_page():
    """Render the Ollama chat interface."""
    try:
        from app.db import get_system_parameters
        params = get_system_parameters()
    except Exception:
        params = {}
    ollama_model_name = params.get('ollama_model_name') or 'llama3.2:latest'
    comfy_model_name  = params.get('comfy_model_name') or ''
    return render_template('chat.html',
        ollama_model_name=ollama_model_name,
        comfy_model_name=comfy_model_name,
    )
