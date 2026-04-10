#!/usr/bin/env python3
"""Patch an app-instance docker-compose.yml in place to add current framework defaults.

This preserves existing app-specific settings while ensuring Ollama/Tailscale support
is present for downstream apps created before the template was updated.
"""

from __future__ import annotations

from pathlib import Path
import sys
import yaml

COMPOSE_PATH = Path("docker-compose.yml")


def _listify(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _unique(seq):
    seen = set()
    result = []
    for item in seq:
        key = str(item)
        if key not in seen and item not in (None, ""):
            seen.add(key)
            result.append(item)
    return result


def _ensure_env(service: dict, key: str, value: str) -> None:
    env = service.get("environment")
    if env is None:
        service["environment"] = {key: value}
        return

    if isinstance(env, dict):
        env.setdefault(key, value)
        return

    if isinstance(env, list):
        existing_keys = set()
        for item in env:
            if isinstance(item, str) and "=" in item:
                existing_keys.add(item.split("=", 1)[0])
        if key not in existing_keys:
            env.append(f"{key}={value}")
        return

    # Unexpected format; normalize to dict without dropping current value entirely.
    service["environment"] = {key: value}


def main() -> int:
    if not COMPOSE_PATH.exists():
        print("docker-compose.yml not found", file=sys.stderr)
        return 1

    data = yaml.safe_load(COMPOSE_PATH.read_text()) or {}
    services = data.setdefault("services", {})
    if not services:
        print("No services found in docker-compose.yml", file=sys.stderr)
        return 1

    app_service_name = "app" if "app" in services else next((name for name in services if name != "watchtower"), None)
    if not app_service_name:
        print("Could not determine app service name", file=sys.stderr)
        return 1

    app_service = services[app_service_name]

    app_service["extra_hosts"] = _unique([
        "host.docker.internal:host-gateway",
        "andrews-macbook-pro.taile4ced3.ts.net:100.106.14.60",
        *_listify(app_service.get("extra_hosts")),
    ])

    app_service["dns"] = _unique([
        "100.100.100.100",
        "1.1.1.1",
        "8.8.8.8",
        *_listify(app_service.get("dns")),
    ])

    app_service["dns_opt"] = _unique([
        *_listify(app_service.get("dns_opt")),
        "single-request",
        "timeout:2",
        "attempts:3",
    ])

    _ensure_env(app_service, "AI_PROVIDER", "${AI_PROVIDER:-}")
    _ensure_env(app_service, "OLLAMA_BASE_URL", "${OLLAMA_BASE_URL:-}")
    _ensure_env(app_service, "OLLAMA_MODEL_NAME", "${OLLAMA_MODEL_NAME:-}")

    watchtower_service = services.get("watchtower")
    if isinstance(watchtower_service, dict):
        _ensure_env(watchtower_service, "TZ", "${TZ:-UTC}")

    COMPOSE_PATH.write_text(
        yaml.safe_dump(data, sort_keys=False, default_flow_style=False),
        encoding="utf-8",
    )

    print(f"Updated docker-compose.yml for service: {app_service_name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
