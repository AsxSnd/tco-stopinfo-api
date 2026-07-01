# Service architecture, caching, and scaling

## Overview

```
  Vehicles (on-board)                Linux host
  ┌─────────────────┐               ┌──────────────────────────────────┐
  │ Displays poll   │  HTTP GET     │ nginx (optional)                 │
  │ every 5 s       │──────────────>│   TLS, rate limit, load balance  │
  └─────────────────┘               │           │                      │
                                    │           v                      │
  PIS / AVL                         │  tco-stopinfo-api (uvicorn)      │
  ┌─────────────────┐    MQTT       │    ├─ HTTP handler (read cache)  │
  │ pis/{id}/...    │──────────────>│    └─ MQTT ingest (write cache)  │
  └─────────────────┘               └──────────────────────────────────┘
```

The service is **read-optimized**: HTTP handlers never wait on MQTT. They return **pre-serialized JSON bytes** from an in-memory cache.

## Request path (hot path)

1. Client calls `GET /api/stopinfo/{account}/{vehicle}`.
2. Handler looks up `(account, vehicle)` in the response cache.
3. If found within `cache.fast_response_seconds`, return immediately (same bytes as last build).
4. Otherwise return latest cached body for that vehicle (rebuilt on last MQTT change).
5. If no MQTT data exists yet, return empty TCO envelope (all areas 204).

Target latency: **sub-millisecond** per request when cached (memory lookup + kernel send).

## MQTT ingest path

1. Background task subscribes to `pis/+/{topic}` for all mapped suffixes.
2. On message: parse JSON, update `VehicleState.topics[suffix]`.
3. If payload changed: increment state version, call `rebuild_vehicle(vehicle_id)`.
4. Rebuild runs `build_stopinfo_response()` for **each configured account** and stores `orjson`-serialized bytes + headers.

Rebuild happens on **MQTT update**, not on HTTP request — this is the main performance design choice.

## Caching layers

### 1. Per-vehicle response cache (primary)

| Key | Value |
|-----|-------|
| `(account, vehicle_id)` | Pre-built JSON `bytes`, HTTP headers, `built_at`, `state_version` |

Populated when any subscribed MQTT topic for that vehicle changes.

### 2. Fast-response window (secondary)

Mirrors legacy TCO `fastResponse` / `fastResponseMaxSeconds` (default **10 s** in `config.example.yaml`).

Within this window, repeated HTTP polls for the same vehicle return the **same cached object** without checking state version — reduces CPU under burst polling (many displays per vehicle).

Configurable: `cache.fast_response_seconds`.

### 3. HTTP `Cache-Control`

Clients receive `Cache-Control: max-age=30` (configurable via `cache.http_cache_max_age`), matching the legacy ITCS service.

### 4. Vehicle TTL (memory management)

Vehicles with no MQTT updates for `cache.vehicle_ttl_seconds` (default 2 h) are purged every 5 minutes to limit RAM.

## Capacity planning

Example: **2 000 devices**, poll every **5 s** → ~**400 requests/s** average.

With pre-built responses:

- Single Python process + `uvloop` + `httptools` typically handles **thousands of simple GET/s** on a modest Linux VM or bare-metal host (2 vCPU / 4 GB RAM is a common starting point).
- CPU is dominated by MQTT ingest and rebuilds (~1 Hz per vehicle on `linkprogress`), not HTTP reads.

| Vehicles | MQTT msg/s (approx.) | HTTP req/s (2000 displays / 5s) | Suggested host |
|----------|----------------------|-----------------------------------|----------------|
| 500 | 500–1000 | 100 | 2 vCPU, 2–4 GB RAM |
| 2000 | 2000–4000 | 400 | 2–4 vCPU, 4–8 GB RAM |
| 5000+ | 5000+ | 1000+ | 4+ vCPU, 8+ GB RAM, or 2× app + nginx LB |

## nginx: needed or not?

### Direct hosting (no nginx)

**Works** for:

- Internal networks / VPN
- TLS terminated elsewhere (load balancer)
- Development and smaller fleets

Run uvicorn on `0.0.0.0:8084` as in `config.example.yaml`.

### Recommended: nginx in front (typical production setup)

Use nginx when you need:

| Feature | nginx | uvicorn alone |
|---------|-------|---------------|
| TLS (HTTPS) | Yes (certbot) | Possible but nginx is simpler |
| Rate limiting | `limit_req` | Not built-in |
| Load balancing | `upstream` with multiple backends | Single process per port |
| Static error pages | Yes | No |
| DDoS / connection hygiene | Better defaults | Basic |

**Typical production setup:** nginx on 443 → uvicorn on `127.0.0.1:8084`. See `deploy/nginx.conf.example`.

### Can nginx load-balance?

**Yes.** Example:

```nginx
upstream tco_stopinfo_backend {
    least_conn;
    server 127.0.0.1:8084;
    server 127.0.0.1:8085;
    server 127.0.0.1:8086;
}
```

**Important:** Default in-memory cache is **per process**. Multiple uvicorn workers or instances **do not share cache** unless you add a shared store (Redis).

| Deployment | Cache | When to use |
|------------|-------|-------------|
| 1 process, `workers: 1` | In-memory | **Default** — up to ~few thousand displays |
| nginx + N instances | Each has own cache | Only if single box CPU-saturated; MQTT connects to **one** ingestor or all instances subscribe (duplicate MQTT OK with idempotent cache) |
| nginx + Redis cache | Shared | Very large scale / HA |

For most HSL-scale deployments: **one app instance + nginx for TLS** is sufficient.

## Multi-worker uvicorn

`http.workers > 1` forks processes — **each has separate MQTT connection and cache**. Not recommended unless every worker subscribes to MQTT (wasteful) or you externalize state.

Keep `workers: 1` in config.

## Configuration reference

See `config.example.yaml` and `docs/deployment.md`.

## Monitoring

- `GET /health` — liveness
- Watch MQTT reconnect logs
- Metric suggestions: HTTP req/s, cache hit rate, rebuild count/s, MQTT lag, memory, open connections

## Failure behaviour

| Scenario | HTTP behaviour |
|----------|----------------|
| No MQTT data for vehicle | Empty TCO JSON (204 areas) |
| MQTT broker down | Serves last cached data; logs reconnect loop |
| Stale vehicle purged | Empty response until MQTT retained messages repopulate state |

Retained MQTT messages (QoS 1, retain on journey/stops/destination) repopulate state quickly after service restart.
