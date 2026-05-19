# HTTPS Setup (Production) with Caddy

This setup adds a reverse proxy that terminates TLS on ports 80/443 and forwards traffic to the Flask app on `127.0.0.1:5001`.

## What this gives you

- Valid HTTPS certificates from Let's Encrypt (automatic renewal)
- HTTP to HTTPS redirection
- Security headers (HSTS, nosniff, frame/options, referrer policy)
- A stable URL for iOS and browser clients

## Requirements

1. A real DNS hostname you control (for example: `app.example.com`)
2. DNS `A`/`AAAA` record for that hostname pointing to this server
3. Ports `80` and `443` reachable from the internet
4. Existing app stack already running on `5001`

### Tailscale domain note

If you use a MagicDNS host like `*.ts.net`, Caddy can obtain trusted certs through the local Tailscale daemon.
This repository's `docker-compose.https.yml` already mounts `/var/run/tailscale/tailscaled.sock` into the Caddy container for that flow.

## Files added

- `docker-compose.https.yml`
- `deploy/caddy/Caddyfile`

## Start HTTPS proxy

From the repo root:

```bash
export APP_DOMAIN=app.example.com

docker compose -f docker-compose.yml -f docker-compose.https.yml up -d caddy
```

If your app is not already running, start both:

```bash
export APP_DOMAIN=app.example.com

docker compose -f docker-compose.yml -f docker-compose.https.yml up -d
```

## Verify

```bash
curl -I https://$APP_DOMAIN
```

Expected:

- Valid certificate chain
- `HTTP/2 200` or a redirect followed by `200`

## iOS app configuration

Set backend URL to:

```text
https://app.example.com
```

After moving to trusted HTTPS, remove the ATS insecure HTTP exception from your iOS `Info.plist`.

## Troubleshooting

### TLS handshake fails or cert is missing

- Confirm `APP_DOMAIN` matches DNS exactly
- Confirm ports `80` and `443` are open
- Check logs:

```bash
docker logs -f template-caddy
```

### Using a `ts.net` domain and seeing TLS internal error

- Verify socket mount exists on host: `ls -l /var/run/tailscale/tailscaled.sock`
- Recreate Caddy after config changes:

```bash
docker compose -f docker-compose.yml -f docker-compose.https.yml up -d caddy
```

### Domain only reachable on Tailscale

Public Let's Encrypt validation may fail if the host is not internet-reachable.
Use one of these alternatives:

1. Expose a public hostname for ACME validation.
2. Use a DNS-01 flow with your DNS provider.
3. Use Tailscale cert workflow for your tailnet hostname.

