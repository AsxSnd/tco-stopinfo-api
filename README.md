# TCO Stopinfo API

High-performance HTTP gateway that exposes the **TCO API2** stop-info protocol to on-board displays, backed by **MQTT-PIS-PT** vehicle telemetry instead of the legacy PaCIM-RT `tcoioh` + `PPluginHSL.dll` stack.

## Features

- `GET /api/stopinfo/{account}/{vehicle}` — TCO-compatible JSON (FS, LD, TD, MD, OM)
- MQTT ingest from `pis/{vehicle_id}/...` topics
- **Pre-built per-vehicle response cache** — HTTP reads never block on MQTT
- Fast-response deduplication (configurable, default 10 s)
- Linux systemd unit + nginx example for production hosting

## Quick start

```bash
cd "D:\.Source\Python\TCO stopinfo API"
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\pip install -e .

copy config.example.yaml config.yaml
# Edit mqtt.broker

.venv\Scripts\tco-stopinfo-api -c config.yaml
```

```bash
curl http://localhost:8084/api/stopinfo/hsl/1232
```

## Documentation

| Document | Description |
|----------|-------------|
| [docs/tco-stopinfo-api-spec.md](docs/tco-stopinfo-api-spec.md) | HTTP API layout specification |
| [docs/mqtt-pis-mapping.md](docs/mqtt-pis-mapping.md) | MQTT-PIS-PT → TCO JSON field mapping |
| [docs/mqtt-pis-pt-specification.md](docs/mqtt-pis-pt-specification.md) | Source MQTT protocol (V1.6.0) |
| [docs/service-architecture.md](docs/service-architecture.md) | Caching, performance, nginx guidance |
| [docs/deployment.md](docs/deployment.md) | Linux deployment |

## nginx vs direct HTTP

| Approach | Use when |
|----------|----------|
| **uvicorn direct** on `:8084` | Dev, private network, TLS elsewhere |
| **nginx → uvicorn** | **Production** — TLS, rate limits, optional load balancing |

nginx **can** load-balance multiple app instances (`deploy/nginx.conf.example`). Default deployment uses **one process** with in-memory cache — sufficient for thousands of displays polling every 5 seconds. See [docs/service-architecture.md](docs/service-architecture.md).

## Project layout

```
src/tco_stopinfo/
  app.py           FastAPI application + lifespan
  builder.py       MQTT state → TCO JSON
  mqtt_client.py   aiomqtt subscriber
  store.py         Vehicle state + response cache
  config.py        YAML configuration
deploy/
  tco-stopinfo-api.service
  nginx.conf.example
docs/
tests/
```

## Tests

```bash
.venv\Scripts\pip install pytest
.venv\Scripts\pytest
```

## License

Internal / project use — adjust as needed.
