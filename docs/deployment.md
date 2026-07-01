# Deployment on Linux

## Requirements

- Ubuntu 22.04 / 24.04 (or Debian 12)
- Python 3.11+
- Network access to MQTT broker
- Open port 8084 (app) or 443 (nginx)

## Install

```bash
sudo useradd --system --home /opt/tco-stopinfo-api --shell /usr/sbin/nologin tco
sudo mkdir -p /opt/tco-stopinfo-api /etc/tco-stopinfo-api
cd /opt/tco-stopinfo-api

# Copy project files (git clone or rsync)
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/pip install -e .

sudo cp config.example.yaml /etc/tco-stopinfo-api/config.yaml
# Edit broker, port, accounts
sudo nano /etc/tco-stopinfo-api/config.yaml
```

## Configuration

| Setting | Description |
|---------|-------------|
| `http.host` | Bind address (`0.0.0.0` behind nginx, `127.0.0.1` with nginx) |
| `http.port` | HTTP port (default **8084**, matches legacy TCO) |
| `http.workers` | Keep **1** (in-memory cache) |
| `mqtt.broker` | MQTT hostname |
| `mqtt.port` | Usually 1883 or 8883 (TLS) |
| `mqtt.topic_prefix` | Default `pis` |
| `cache.fast_response_seconds` | Dedup window for identical vehicle polls (default 10) |
| `cache.vehicle_ttl_seconds` | Remove idle vehicles from RAM |
| `accounts.{name}` | Per-account limits (`hsl`, etc.) |

Environment override:

```bash
export TCO_CONFIG_FILE=/etc/tco-stopinfo-api/config.yaml
```

## systemd

```bash
sudo cp deploy/tco-stopinfo-api.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now tco-stopinfo-api
sudo systemctl status tco-stopinfo-api
```

## nginx + TLS (recommended)

```bash
sudo apt install nginx certbot python3-certbot-nginx
sudo cp deploy/nginx.conf.example /etc/nginx/sites-available/tco-stopinfo-api
# Edit server_name and upstream
sudo ln -s /etc/nginx/sites-available/tco-stopinfo-api /etc/nginx/sites-enabled/
sudo certbot --nginx -d stopinfo.example.com
sudo nginx -t && sudo systemctl reload nginx
```

Set in `config.yaml`:

```yaml
http:
  host: "127.0.0.1"
  port: 8084
```

## Firewall

Allow HTTPS (and SSH for administration) on the host firewall or cloud security group:

```bash
# Example with ufw (Ubuntu/Debian)
sudo ufw allow 443/tcp
sudo ufw allow 22/tcp
# Only if exposing the app directly without nginx:
# sudo ufw allow 8084/tcp
```

On other distributions, use `firewalld`, `iptables`, or your provider's network firewall the same way.

## Verify

```bash
curl -s http://127.0.0.1:8084/health
curl -s http://127.0.0.1:8084/api/stopinfo/hsl/1232 | jq .
```

## Docker (optional)

A minimal Dockerfile can wrap the same entrypoint:

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt && pip install -e .
EXPOSE 8084
CMD ["tco-stopinfo-api", "-c", "/etc/tco-stopinfo-api/config.yaml"]
```

Mount config and run behind nginx on the host for TLS.

## Upgrade

```bash
cd /opt/tco-stopinfo-api
git pull   # or rsync
.venv/bin/pip install -r requirements.txt
sudo systemctl restart tco-stopinfo-api
```

Retained MQTT messages refill vehicle cache without downtime.
