#!/usr/bin/env python3
"""Regression tests for Ollama AI provider support."""

import sqlite3
from pathlib import Path
from unittest.mock import patch

import requests
from flask import Flask

from app.api.ai_api import ai_api_bp
from app.services.ai_service import AIService


SCHEMA_SQL = """
CREATE TABLE SystemParameters (
    parameter_name TEXT PRIMARY KEY NOT NULL,
    parameter_value TEXT
);
"""


def _init_test_db(db_path: Path) -> None:
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    conn.close()


def _make_test_app(db_path: Path) -> Flask:
    app = Flask(__name__)
    app.config['DATABASE_PATH'] = str(db_path)
    return app


class _FakeResponse:
    def __init__(self, payload=None):
        self._payload = payload or {}
        self.status_code = 200

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


@patch('app.services.ai_service.requests.post')
@patch('app.services.ai_service.requests.get')
def test_ai_service_can_use_ollama_as_primary_provider(mock_get, mock_post, tmp_path):
    db_path = tmp_path / 'ollama_test.db'
    _init_test_db(db_path)

    conn = sqlite3.connect(db_path)
    conn.execute("INSERT INTO SystemParameters (parameter_name, parameter_value) VALUES (?, ?)", ('primary_ai_provider', 'ollama'))
    conn.execute("INSERT INTO SystemParameters (parameter_name, parameter_value) VALUES (?, ?)", ('ollama_base_url', 'http://localhost:11434'))
    conn.execute("INSERT INTO SystemParameters (parameter_name, parameter_value) VALUES (?, ?)", ('ollama_model_name', 'llama3.2:latest'))
    conn.commit()
    conn.close()

    mock_get.return_value = _FakeResponse({'models': []})
    mock_post.return_value = _FakeResponse({'response': 'OK'})

    app = _make_test_app(db_path)

    with app.app_context():
        service = AIService()
        result = service.generate_description('Widget', 'Component')

    assert service.provider == 'ollama'
    assert service.is_available() is True
    assert result == 'OK'


@patch('app.api.ai_api.fetch_ollama_models')
def test_ollama_models_endpoint_falls_back_to_openai_compatible_endpoint(mock_fetch_models, tmp_path):
    db_path = tmp_path / 'ollama_models_test.db'
    _init_test_db(db_path)

    base_url = 'https://ollama.example.com'

    conn = sqlite3.connect(db_path)
    conn.execute("INSERT INTO SystemParameters (parameter_name, parameter_value) VALUES (?, ?)", ('ollama_base_url', base_url))
    conn.execute("INSERT INTO SystemParameters (parameter_name, parameter_value) VALUES (?, ?)", ('ollama_model_name', 'qwen2.5:latest'))
    conn.commit()
    conn.close()

    mock_fetch_models.return_value = (
        [
            {'id': 'llama3.2:latest', 'name': 'llama3.2:latest', 'size': None, 'modified_at': None},
            {'id': 'qwen2.5:latest', 'name': 'qwen2.5:latest', 'size': None, 'modified_at': None},
        ],
        'openai',
    )

    app = _make_test_app(db_path)
    app.register_blueprint(ai_api_bp, url_prefix='/api')

    with app.app_context():
        client = app.test_client()
        response = client.get('/api/ai/ollama/models', query_string={'base_url': base_url})

    assert response.status_code == 200
    payload = response.get_json()
    assert [item['id'] for item in payload['models']] == ['llama3.2:latest', 'qwen2.5:latest']
    assert payload['default'] == 'qwen2.5:latest'
    assert payload['api_style'] == 'openai'


@patch('app.services.ai_service.requests.post')
@patch('app.services.ai_service.requests.get')
def test_ai_service_falls_back_to_native_ollama_chat_endpoint(mock_get, mock_post, tmp_path):
    db_path = tmp_path / 'ollama_chat_test.db'
    _init_test_db(db_path)

    base_url = 'http://proxy.example.local:8080'

    conn = sqlite3.connect(db_path)
    conn.execute("INSERT INTO SystemParameters (parameter_name, parameter_value) VALUES (?, ?)", ('primary_ai_provider', 'ollama'))
    conn.execute("INSERT INTO SystemParameters (parameter_name, parameter_value) VALUES (?, ?)", ('ollama_base_url', base_url))
    conn.execute("INSERT INTO SystemParameters (parameter_name, parameter_value) VALUES (?, ?)", ('ollama_model_name', 'qwen2.5:latest'))
    conn.commit()
    conn.close()

    def get_side_effect(url, timeout=0, **kwargs):
        if url == f'{base_url}/api/tags':
            return _FakeResponse({'models': [{'name': 'qwen2.5:latest'}]})
        raise AssertionError(f'Unexpected GET URL: {url}')

    def post_side_effect(url, json=None, timeout=0, **kwargs):
        if url == f'{base_url}/api/generate':
            raise requests.exceptions.RequestException('generate endpoint unavailable')
        if url == f'{base_url}/api/chat':
            return _FakeResponse({'message': {'content': 'OK from chat'}})
        raise AssertionError(f'Unexpected POST URL: {url}')

    mock_get.side_effect = get_side_effect
    mock_post.side_effect = post_side_effect

    app = _make_test_app(db_path)

    with app.app_context():
        service = AIService()
        result = service.generate_description('Widget', 'Component')

    assert service.provider == 'ollama'
    assert service.is_available() is True
    assert result == 'OK from chat'


@patch('app.services.ai_service.requests.post')
@patch('app.services.ai_service.requests.get')
def test_ai_service_falls_back_to_openai_compatible_ollama_endpoints(mock_get, mock_post, tmp_path):
    db_path = tmp_path / 'ollama_https_test.db'
    _init_test_db(db_path)

    base_url = 'https://ollama.example.com'

    conn = sqlite3.connect(db_path)
    conn.execute("INSERT INTO SystemParameters (parameter_name, parameter_value) VALUES (?, ?)", ('primary_ai_provider', 'ollama'))
    conn.execute("INSERT INTO SystemParameters (parameter_name, parameter_value) VALUES (?, ?)", ('ollama_base_url', base_url))
    conn.execute("INSERT INTO SystemParameters (parameter_name, parameter_value) VALUES (?, ?)", ('ollama_model_name', 'qwen2.5:latest'))
    conn.commit()
    conn.close()

    def get_side_effect(url, timeout=0, **kwargs):
        if url == f'{base_url}/api/tags':
            raise requests.exceptions.RequestException('native endpoint unavailable')
        if url == f'{base_url}/v1/models':
            return _FakeResponse({'data': [{'id': 'qwen2.5:latest'}]})
        raise AssertionError(f'Unexpected GET URL: {url}')

    def post_side_effect(url, json=None, timeout=0, **kwargs):
        if url == f'{base_url}/api/generate':
            raise requests.exceptions.RequestException('native endpoint unavailable')
        if url == f'{base_url}/v1/chat/completions':
            return _FakeResponse({'choices': [{'message': {'content': 'OK'}}]})
        raise AssertionError(f'Unexpected POST URL: {url}')

    mock_get.side_effect = get_side_effect
    mock_post.side_effect = post_side_effect

    app = _make_test_app(db_path)

    with app.app_context():
        service = AIService()
        result = service.generate_description('Widget', 'Component')

    assert service.provider == 'ollama'
    assert service.is_available() is True
    assert result == 'OK'
