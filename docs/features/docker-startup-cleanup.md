# Docker Startup Cleanup

**Status**: ✅ Implemented

## Overview

The Docker Startup Cleanup feature is a system maintenance utility designed to automatically prune Docker files and clear cached builds when the server starts up. This helps in maintaining disk space and ensuring a clean environment for Docker operations.

## Components

The feature consists of three main components located in the `scripts/` directory:

1. **`scripts/cleanup_docker_cache.sh`**: The core script that performs the cleanup operations.
2. **`scripts/docker-cleanup.service`**: A systemd service file that defines the cleanup task to run on system startup.
3. **`scripts/install_cleanup_service.sh`**: An installation script to set up the systemd service.

## How It Works

### 1. Cleanup Script (`cleanup_docker_cache.sh`)

This script performs the following actions:
- Waits for the Docker daemon to be ready.
- Prunes dangling images (`docker image prune -f`).
- Prunes the build cache (`docker builder prune -a -f`).

### 2. Systemd Service (`docker-cleanup.service`)

The service is configured to:
- Run as a `oneshot` service.
- Execute after `docker.service` has started.
- Run the `cleanup_docker_cache.sh` script.

## Installation

To enable this feature on your server, run the installation script as root:

```bash
sudo ./scripts/install_cleanup_service.sh
```

This will:
1. Copy the service file to `/etc/systemd/system/`.
2. Reload the systemd daemon.
3. Enable the service to run on boot.

## Manual Execution

You can also run the cleanup script manually at any time:

```bash
./scripts/cleanup_docker_cache.sh
```

## Verification

To verify that the service is installed and enabled:

```bash
systemctl status docker-cleanup.service
```

To check the logs of the cleanup service:

```bash
journalctl -u docker-cleanup.service
```
