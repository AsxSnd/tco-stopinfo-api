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

# Copy project files (git clone or rsync) into /opt/tco-stopinfo-api
sudo chown -R tco:tco /opt/tco-stopinfo-api

sudo -u tco bash -c 'cd /opt/tco-stopinfo-api && \
  python3 -m venv .venv && \
  .venv/bin/pip install --upgrade pip && \
  .venv/bin/pip install -r requirements.txt && \
  .venv/bin/pip install .'

sudo cp config.example.yaml /etc/tco-stopinfo-api/config.yaml
sudo chown tco:tco /etc/tco-stopinfo-api/config.yaml
# Edit broker, port, accounts
sudo nano /etc/tco-stopinfo-api/config.yaml
```

Use `pip install .` (not `-e .`) on production servers — editable installs write metadata under `src/` and often fail when ownership or permissions are mixed.

### Install error: `Cannot update time stamp of directory 'src/...egg-info'`

Usually caused by leftover build metadata or mixed root/`tco` ownership (e.g. venv created as root, or files copied from another machine).

```bash
sudo rm -rf /opt/tco-stopinfo-api/src/*.egg-info \
           /opt/tco-stopinfo-api/build \
           /opt/tco-stopinfo-api/dist
sudo chown -R tco:tco /opt/tco-stopinfo-api

sudo -u tco bash -c 'cd /opt/tco-stopinfo-api && \
  .venv/bin/pip install .'
```

If the venv was created as root, recreate it as `tco`:

```bash
sudo rm -rf /opt/tco-stopinfo-api/.venv
sudo -u tco bash -c 'cd /opt/tco-stopinfo-api && \
  python3 -m venv .venv && \
  .venv/bin/pip install -r requirements.txt && \
  .venv/bin/pip install .'
```

## Configuration

| Setting | Description |
|---------|-------------|
| `http.host` | Bind address (`0.0.0.0` behind nginx, `127.0.0.1` with nginx) |
| `http.port` | HTTP port (default **8084**, matches legacy TCO) |
| `http.workers` | Keep **1** (in-memory cache) |
| `mqtt.broker` | MQTT hostname |
| `mqtt.port` | Usually 1883 or 8883 (TLS) |
| `mqtt.root` | Broker root segment, e.g. **`vilniustest`** (see `docs/mqtt-topic-layout.md`) |
| `mqtt.topic_prefix` | PIS segment, usually **`pis`** |
| `mqtt.pis_instance` | Spec placeholder, usually **`0`** → topics like `.../pis/0/journey` |
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
sudo apt install nginx
sudo cp deploy/nginx.conf.example /etc/nginx/sites-available/tco-stopinfo-api
# Edit server_name and upstream
sudo ln -s /etc/nginx/sites-available/tco-stopinfo-api /etc/nginx/sites-enabled/
sudo certbot --nginx -d stopinfo.example.com
sudo nginx -t && sudo systemctl reload nginx
```

### Vilnius lab (HTTP only — no TLS)

Host name: **`stopinfo.vilnius.stjernberg.lab.suite.luminator.com`**

1. DNS: **A** or **CNAME** → nginx server IP.
2. App binds to localhost:

```yaml
http:
  host: "127.0.0.1"
  port: 8184
```

3. Enable nginx site:

```bash
sudo apt install nginx
sudo cp deploy/nginx-vilnius-stjernberg-http.conf.example \
  /etc/nginx/sites-available/stopinfo-vilnius
sudo ln -sf /etc/nginx/sites-available/stopinfo-vilnius /etc/nginx/sites-enabled/
```

Long hostnames (`stopinfo.vilnius.stjernberg.lab.suite.luminator.com`) require a larger hash bucket in `/etc/nginx/nginx.conf` inside the `http { }` block:

```nginx
server_names_hash_bucket_size 128;
```

Then:

```bash
sudo nginx -t && sudo systemctl reload nginx
sudo ufw allow 80/tcp
```

Public URL:

```text
http://stopinfo.vilnius.stjernberg.lab.suite.luminator.com/api/stopinfo/vilnius/1721
```

Verify:

```bash
curl -s http://stopinfo.vilnius.stjernberg.lab.suite.luminator.com/health | jq .
```

TLS can be added later with `deploy/nginx-vilnius-stjernberg.conf.example` when a certificate is ready.

### Vilnius lab (HTTPS with existing cert)

Host name: **`stopinfo.vilnius.stjernberg.lab.suite.luminator.com`**  
Certificate: **`*.stjernberg.lab.suite.luminator.com`**

1. DNS: create an **A** or **CNAME** record for `stopinfo.vilnius.stjernberg.lab.suite.luminator.com` → nginx server IP (or CDN origin).
2. Install the wildcard cert on the nginx host (paths depend on your PKI).
3. Use `deploy/nginx-vilnius-stjernberg.conf.example` — copy, adjust `ssl_certificate` paths, enable the site.
4. Bind the app to localhost only:

```yaml
http:
  host: "127.0.0.1"
  port: 8084
```

Public URL example:

```text
https://stopinfo.vilnius.stjernberg.lab.suite.luminator.com/api/stopinfo/vilnius/1721
```

If a CDN terminates TLS in front of nginx, origin can stay HTTP on a private network; ensure `/api/stopinfo/` is not cached aggressively (honour app `Cache-Control: max-age=30` or bypass cache).

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

## MQTT disconnect loop

Log pattern:

```text
MQTT connected ...
MQTT error: Disconnected during message iteration — reconnecting in 5s
```

**Common causes:**

1. **Retained message burst blocking the event loop** (fixed in recent versions — rebuild runs in a thread pool). Upgrade and restart.
2. **Second client using the same MQTT username** — stop the Windows dev instance if it uses the same broker credentials. Some brokers allow only one session per user.
3. **Duplicate `client_id`** — each instance uses `{client_id}-{hostname}-{pid}-{port}`; check `/health` → `mqtt.client_id`.

**Checks:**

```bash
curl -s http://127.0.0.1:8184/health | jq .mqtt
# connected: true, messages_received increasing

sudo journalctl -u tco-stopinfo-api -n 30 --no-pager
# Should show client_id=... and no repeated disconnects
```

If disconnects continue after upgrade, verify broker ACL allows subscribe to `vilniustest/+/pis/0/#` and that no other service uses the same MQTT user.

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
sudo chown -R tco:tco .
sudo -u tco git pull   # or rsync
sudo rm -rf src/*.egg-info build dist
sudo -u tco bash -c '.venv/bin/pip install -r requirements.txt && .venv/bin/pip install .'
sudo systemctl restart tco-stopinfo-api
```

Retained MQTT messages refill vehicle cache without downtime.
