"""
Chat Proxy API
Proxies requests to Ollama and ComfyUI backends so the browser avoids CORS issues.
All endpoints are mounted at /ollama/* (registered with url_prefix='/ollama').
The chat frontend sets its server variable to '/ollama' to match these paths.
"""
import base64
import json
import random
import time
import logging
import os

from flask import Blueprint, request, jsonify, Response, stream_with_context, current_app
import requests

logger = logging.getLogger(__name__)

chat_proxy_bp = Blueprint('chat_proxy', __name__)


def _get_ollama_url() -> str:
    try:
        from app.db import get_system_parameters
        params = get_system_parameters()
        url = params.get('ollama_base_url') or os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
    except Exception:
        url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
    return url.rstrip('/')


def _get_comfy_url() -> str:
    """Return the custom Animagine/ComfyUI image API URL (e.g. port 8799)."""
    try:
        from app.db import get_system_parameters
        params = get_system_parameters()
        url = params.get('comfy_server_url') or os.getenv('COMFY_SERVER_URL', 'http://localhost:8799')
    except Exception:
        url = os.getenv('COMFY_SERVER_URL', 'http://localhost:8799')
    return url.rstrip('/')


def _get_comfy_tts_url() -> str:
    """Return the ComfyUI API URL used for Kokoro TTS.

    If ``comfy_tts_url`` is explicitly set, use it.  Otherwise fall back to
    ``comfy_server_url`` so that both image generation and TTS can share a
    single ComfyUI instance (e.g. on port 8188).
    """
    try:
        from app.db import get_system_parameters
        params = get_system_parameters()
        tts_url = params.get('comfy_tts_url')
        if tts_url:
            return tts_url.rstrip('/')
        # Default: same ComfyUI instance used for image generation
        comfy_url = params.get('comfy_server_url') or os.getenv('COMFY_SERVER_URL', 'http://localhost:8188')
    except Exception:
        comfy_url = os.getenv('COMFY_SERVER_URL', 'http://localhost:8188')
    return comfy_url.rstrip('/')


# ---------------------------------------------------------------------------
# Ollama proxy endpoints
# ---------------------------------------------------------------------------

@chat_proxy_bp.route('/api/chat', methods=['POST'])
def proxy_chat():
    """Stream-proxy POST /api/chat to the configured Ollama server."""
    ollama_url = _get_ollama_url()
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'Missing or invalid JSON body'}), 400

    try:
        upstream = requests.post(
            f"{ollama_url}/api/chat",
            json=data,
            stream=True,
            timeout=(10, 300),  # connect 10s, read up to 300s
        )

        def generate():
            for chunk in upstream.iter_content(chunk_size=None):
                if chunk:
                    yield chunk

        return Response(
            stream_with_context(generate()),
            status=upstream.status_code,
            content_type=upstream.headers.get('Content-Type', 'application/x-ndjson'),
        )
    except requests.exceptions.ConnectionError as e:
        logger.warning("Ollama connection error: %s", e)
        return jsonify({'error': f'Cannot reach Ollama at {ollama_url}'}), 502
    except requests.exceptions.Timeout:
        return jsonify({'error': 'Ollama request timed out'}), 504
    except Exception as e:
        logger.exception("Unexpected error proxying chat")
        return jsonify({'error': str(e)}), 500


@chat_proxy_bp.route('/api/tags', methods=['GET'])
def proxy_tags():
    """Proxy GET /api/tags to Ollama — returns the list of local models."""
    ollama_url = _get_ollama_url()
    try:
        resp = requests.get(f"{ollama_url}/api/tags", timeout=10)
        return Response(resp.content, status=resp.status_code, content_type='application/json')
    except requests.exceptions.ConnectionError:
        return jsonify({'error': f'Cannot reach Ollama at {ollama_url}', 'models': []}), 502
    except Exception as e:
        return jsonify({'error': str(e), 'models': []}), 500


@chat_proxy_bp.route('/api/health', methods=['GET'])
def proxy_health():
    """
    Combined health check: probes Ollama and ComfyUI (image + TTS).
    Returns JSON compatible with the Ollama-Nano frontend health expectations.
    """
    ollama_url = _get_ollama_url()
    comfy_url = _get_comfy_url()
    comfy_tts_url = _get_comfy_tts_url()

    def probe(url, path, timeout=3):
        try:
            r = requests.get(f"{url}{path}", timeout=timeout)
            return {'online': r.status_code < 500}
        except Exception as exc:
            return {'online': False, 'error': str(exc)}

    ollama_status = probe(ollama_url, '/api/tags')
    comfy_status = probe(comfy_url, '/api/models')
    tts_status = probe(comfy_tts_url, '/system_stats')

    return jsonify({
        'proxy': {'online': True},
        'ollama': ollama_status,
        'comfy': comfy_status,
        'tts': tts_status,
        'timestamp': int(time.time() * 1000),
    })


# ---------------------------------------------------------------------------
# ComfyUI image generation proxy endpoints
# ---------------------------------------------------------------------------

# Loader nodes whose first required input contains the list of available models.
_COMFY_LOADER_NODES = [
    ('CheckpointLoaderSimple', 'ckpt_name'),
    ('DiffusersLoader',        'model_path'),
    ('UNETLoader',             'unet_name'),
    ('CheckpointLoader',       'ckpt_name'),
]

@chat_proxy_bp.route('/api/comfy-models', methods=['GET'])
def proxy_comfy_models():
    """Fetch available image models from ComfyUI by reading /object_info.

    The standard /api/models/* endpoints only scan ComfyUI's default model
    directories and miss models loaded via extra_model_paths or Diffusers
    format.  Querying /object_info for each loader node is authoritative
    because it reflects exactly what ComfyUI would show in its own UI.

    Accepts an optional ``?server_url=`` query parameter so the settings page
    can query a URL before it has been saved to the database.
    """
    override_url = request.args.get('server_url', '').strip()
    comfy_url = override_url.rstrip('/') if override_url else _get_comfy_url()
    try:
        seen: set = set()
        all_models: list = []

        for node_class, param in _COMFY_LOADER_NODES:
            try:
                resp = requests.get(f"{comfy_url}/object_info/{node_class}", timeout=10)
                if resp.status_code != 200:
                    continue
                node_info = resp.json().get(node_class, {})
                spec = node_info.get('input', {}).get('required', {}).get(param, [[]])
                model_list = spec[0] if spec and isinstance(spec[0], list) else []
                for name in model_list:
                    if name and name not in seen:
                        seen.add(name)
                        all_models.append(name)
            except Exception:
                pass

        return jsonify({'models': all_models})
    except requests.exceptions.ConnectionError:
        return jsonify({'error': f'Cannot reach ComfyUI at {comfy_url}', 'models': []}), 502
    except Exception as e:
        return jsonify({'error': str(e), 'models': []}), 500


_SDXL_WORKFLOW_TEMPLATE = {
    "1": {
        "class_type": "DiffusersLoader",
        "inputs": {"model_path": "bubble-hentai-illustrious-v10-sdxl"},
    },
    "2": {
        "class_type": "CLIPTextEncode",
        "inputs": {"text": "", "clip": ["1", 1]},
    },
    "3": {
        "class_type": "CLIPTextEncode",
        "inputs": {
            "text": "lowres, bad anatomy, bad hands, text, error, missing fingers, extra digits, cropped, worst quality, low quality, watermark",
            "clip": ["1", 1],
        },
    },
    "4": {
        "class_type": "EmptyLatentImage",
        "inputs": {"width": 512, "height": 512, "batch_size": 1},
    },
    "5": {
        "class_type": "KSampler",
        "inputs": {
            "model": ["1", 0],
            "positive": ["2", 0],
            "negative": ["3", 0],
            "latent_image": ["4", 0],
            "seed": 0,
            "steps": 20,
            "cfg": 7.0,
            "sampler_name": "dpmpp_2m",
            "scheduler": "karras",
            "denoise": 1.0,
        },
    },
    "6": {
        "class_type": "VAEDecode",
        "inputs": {"samples": ["5", 0], "vae": ["1", 2]},
    },
    "7": {
        "class_type": "SaveImage",
        "inputs": {"images": ["6", 0], "filename_prefix": "chat_gen_"},
    },
}


@chat_proxy_bp.route('/api/generate-image', methods=['POST'])
def proxy_generate_image():
    """Submit an image generation workflow to ComfyUI and return the prompt_id immediately.

    The client is responsible for polling /api/image-status/<prompt_id> until
    the job completes.  This avoids any server-side timeout on long-running
    SDXL generations.
    """
    comfy_url = _get_comfy_url()
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'Missing request body'}), 400

    positive = (data.get('prompt') or '').strip()
    negative = (data.get('negative_prompt') or '').strip() or \
        'lowres, bad anatomy, bad hands, text, error, missing fingers, extra digits, cropped, worst quality, low quality, watermark'
    model = (data.get('model') or '').strip()
    steps = int(data.get('steps', 20))
    cfg = float(data.get('cfg', 7.0))
    width = int(data.get('width', 512))
    height = int(data.get('height', 512))
    seed = int(data.get('seed', -1))
    if seed < 0:
        seed = random.randint(0, 2 ** 31 - 1)

    if not positive:
        return jsonify({'error': 'Missing prompt'}), 400

    if not model:
        try:
            from app.db import get_system_parameters
            params = get_system_parameters()
            model = params.get('comfy_model_name', '') or 'bubble-hentai-illustrious-v10-sdxl'
        except Exception:
            model = 'bubble-hentai-illustrious-v10-sdxl'

    workflow = json.loads(json.dumps(_SDXL_WORKFLOW_TEMPLATE))
    loader_input_key = list(workflow['1']['inputs'].keys())[0]
    workflow['1']['inputs'][loader_input_key] = model
    workflow['2']['inputs']['text'] = positive
    workflow['3']['inputs']['text'] = negative
    workflow['4']['inputs'].update({'width': width, 'height': height})
    workflow['5']['inputs'].update({'steps': steps, 'cfg': cfg, 'seed': seed})

    try:
        submit_resp = requests.post(
            f"{comfy_url}/prompt",
            json={'prompt': workflow},
            timeout=15,
        )
        if submit_resp.status_code != 200:
            return jsonify({'error': f'ComfyUI /prompt returned {submit_resp.status_code}: {submit_resp.text[:200]}'}), 502
        prompt_id = submit_resp.json().get('prompt_id')
        if not prompt_id:
            return jsonify({'error': 'ComfyUI did not return a prompt_id'}), 502

        return jsonify({'prompt_id': prompt_id, 'status': 'queued'})

    except requests.exceptions.ConnectionError:
        return jsonify({'error': f'Cannot reach ComfyUI at {comfy_url}'}), 502
    except requests.exceptions.Timeout:
        return jsonify({'error': 'ComfyUI submit timed out'}), 504
    except Exception as e:
        logger.exception("Error submitting image workflow to ComfyUI")
        return jsonify({'error': str(e)}), 500


@chat_proxy_bp.route('/api/image-status/<prompt_id>', methods=['GET'])
def proxy_image_status(prompt_id: str):
    """Poll ComfyUI /history for the status of a submitted image job.

    Returns one of:
      { "status": "pending" }
      { "status": "done", "data_url": "data:image/png;base64,...", "prompt_id": "..." }
      { "status": "error", "error": "..." }
    """
    comfy_url = _get_comfy_url()
    try:
        hist_resp = requests.get(f"{comfy_url}/history/{prompt_id}", timeout=10)
        if hist_resp.status_code != 200:
            return jsonify({'status': 'pending'})

        hist = hist_resp.json()
        if not hist.get(prompt_id):
            return jsonify({'status': 'pending'})

        job = hist[prompt_id]

        # Check for ComfyUI-reported error
        if job.get('status', {}).get('status_str') == 'error':
            msgs = job.get('status', {}).get('messages', [])
            err_msg = next((m[1] for m in msgs if m[0] == 'execution_error'), 'ComfyUI error')
            return jsonify({'status': 'error', 'error': err_msg})

        image_file = None
        for node_out in job.get('outputs', {}).values():
            if node_out.get('images'):
                image_file = node_out['images'][0]
                break

        if not image_file:
            return jsonify({'status': 'pending'})

        view_url = (f"{comfy_url}/view?filename={image_file['filename']}"
                    f"&type={image_file.get('type', 'output')}")
        img_resp = requests.get(view_url, timeout=30)
        content_type = img_resp.headers.get('Content-Type', 'image/png')
        data_url = f"data:{content_type};base64,{base64.b64encode(img_resp.content).decode()}"
        return jsonify({'status': 'done', 'data_url': data_url, 'prompt_id': prompt_id})

    except requests.exceptions.ConnectionError:
        return jsonify({'status': 'error', 'error': f'Cannot reach ComfyUI at {comfy_url}'})
    except Exception as e:
        logger.exception("Error polling image status from ComfyUI")
        return jsonify({'status': 'error', 'error': str(e)})


@chat_proxy_bp.route('/api/delete-image', methods=['POST'])
def proxy_delete_image():
    """Remove a generated image's history entry from ComfyUI."""
    comfy_url = _get_comfy_url()
    data = request.get_json(silent=True)
    prompt_id = (data or {}).get('prompt_id') or (data or {}).get('asset_id')
    if not prompt_id:
        return jsonify({'error': 'Missing prompt_id'}), 400
    try:
        resp = requests.post(
            f"{comfy_url}/history",
            json={'delete': [prompt_id]},
            timeout=10,
        )
        return Response(resp.content, status=resp.status_code, content_type='application/json')
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ---------------------------------------------------------------------------
# TTS proxy endpoints (Kokoro via standard ComfyUI API on port 8189)
# ---------------------------------------------------------------------------

_KOKORO_WORKFLOW_TEMPLATE = {
    "1": {
        "inputs": {
            "text": "",
            "speaker": "af_sarah"
        },
        "class_type": "Kokoro TextToSpeech",
        "_meta": {"title": "Kokoro TTS"}
    },
    "2": {
        "inputs": {"audio": ["1", 0], "filename_prefix": "kokoro_"},
        "class_type": "SaveAudio",
        "_meta": {"title": "Save Audio"}
    }
}


@chat_proxy_bp.route('/api/tts', methods=['POST'])
def proxy_tts():
    """
    Submit a Kokoro TTS workflow to the standard ComfyUI API, poll for
    completion, then stream the audio bytes back to the client.
    """
    comfy_tts_url = _get_comfy_tts_url()
    data = request.get_json(silent=True)
    if not data or not data.get('text'):
        return jsonify({'error': 'Missing text field'}), 400

    text = data['text']
    speaker = data.get('voice', data.get('speaker', 'af_sarah'))

    # Build the workflow
    workflow = json.loads(json.dumps(_KOKORO_WORKFLOW_TEMPLATE))  # deep copy
    workflow['1']['inputs'].update({'text': text, 'speaker': speaker})

    try:
        # Submit workflow
        submit_resp = requests.post(
            f"{comfy_tts_url}/prompt",
            json={'prompt': workflow},
            timeout=15,
        )
        if submit_resp.status_code != 200:
            return jsonify({'error': f'ComfyUI /prompt returned {submit_resp.status_code}'}), 502
        prompt_id = submit_resp.json().get('prompt_id')
        if not prompt_id:
            return jsonify({'error': 'ComfyUI did not return a prompt_id'}), 502

        # Poll /history until done (max 60s)
        deadline = time.time() + 60
        output = None
        while time.time() < deadline:
            hist_resp = requests.get(f"{comfy_tts_url}/history/{prompt_id}", timeout=5)
            if hist_resp.status_code == 200:
                hist = hist_resp.json()
                entry = hist.get(prompt_id)
                if entry and entry.get('outputs'):
                    # Find the audio output
                    for node_out in entry['outputs'].values():
                        if 'audio' in node_out and node_out['audio']:
                            output = node_out['audio'][0]
                            break
                    if output:
                        break
            time.sleep(0.5)

        if not output:
            return jsonify({'error': 'TTS generation timed out or produced no output'}), 504

        filename = output.get('filename', '')
        subfolder = output.get('subfolder', '')
        file_type = output.get('type', 'output')

        # Download the audio
        audio_resp = requests.get(
            f"{comfy_tts_url}/view",
            params={'filename': filename, 'subfolder': subfolder, 'type': file_type},
            timeout=15,
        )
        content_type = audio_resp.headers.get('Content-Type', 'audio/wav')
        return Response(
            audio_resp.content,
            status=200,
            content_type=content_type,
            headers={
                'X-TTS-Duration': audio_resp.headers.get('X-TTS-Duration', ''),
                'X-TTS-Filename': filename,
            },
        )
    except requests.exceptions.ConnectionError:
        return jsonify({'error': f'Cannot reach ComfyUI TTS at {comfy_tts_url}'}), 502
    except Exception as e:
        logger.exception("Error in TTS proxy")
        return jsonify({'error': str(e)}), 500


@chat_proxy_bp.route('/api/delete-audio', methods=['POST'])
def proxy_delete_audio():
    """Delete a TTS audio entry from ComfyUI history."""
    comfy_tts_url = _get_comfy_tts_url()
    data = request.get_json(silent=True)
    prompt_id = data.get('prompt_id') if data else None
    if not prompt_id:
        return jsonify({'error': 'Missing prompt_id'}), 400
    try:
        resp = requests.post(
            f"{comfy_tts_url}/history",
            json={'delete': [prompt_id]},
            timeout=10,
        )
        return Response(resp.content, status=resp.status_code, content_type='application/json')
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@chat_proxy_bp.route('/api/restart', methods=['POST'])
def proxy_restart():
    """Stub: the Flask app is its own proxy, so restart is a no-op."""
    return jsonify({'status': 'ok', 'message': 'Flask proxy does not require restart'})
