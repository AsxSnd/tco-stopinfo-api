# MQTT topic layout

The MQTT-PIS-PT specification describes topics relative to **one vehicle**, e.g. `pis/0/journey`. On a shared broker, that tree is usually mounted **under each vehicle**.

## Vilnius-style layout (your broker)

```
vilniustest/
  └── {vehicle_id}/          ← e.g. 1232, 4567
        └── pis/
              └── 0/         ← pis_instance from spec (usually "0")
                    ├── journey
                    ├── destination
                    ├── linkprogress
                    ├── stopinfo
                    ├── list/stops
                    ├── connections
                    └── ...
```

### Full topic examples (vehicle `1232`)

| PIS spec topic | Your broker topic |
|----------------|-------------------|
| `pis/0/journey` | `vilniustest/1232/pis/0/journey` |
| `pis/0/linkprogress` | `vilniustest/1232/pis/0/linkprogress` |
| `pis/0/list/stops` | `vilniustest/1232/pis/0/list/stops` |
| `pis/0/destination` | `vilniustest/1232/pis/0/destination` |
| `pis/0/connections` | `vilniustest/1232/pis/0/connections` |
| `pis/0/stopinfo` | `vilniustest/1232/pis/0/stopinfo` |

### `config.yaml` for this layout

```yaml
mqtt:
  broker: "your-mqtt-host"
  port: 1883
  root: "vilniustest"
  topic_prefix: "pis"
  pis_instance: "0"
```

The service subscribes to wildcards such as:

```
vilniustest/+/pis/0/journey
vilniustest/+/pis/0/linkprogress
vilniustest/+/pis/0/list/stops
...
```

`+` matches any **vehicle id** under `vilniustest`.

## HTTP ↔ MQTT vehicle id

HTTP and MQTT must use the **same vehicle id**:

| HTTP | MQTT |
|------|------|
| `GET /api/stopinfo/hsl/1232` | `vilniustest/1232/pis/0/...` |

The `{account}` segment (`hsl`) is only for account settings in config — it does **not** appear in MQTT topics.

## What the service reads vs ignores

| Topic | Used for TCO API |
|-------|------------------|
| `journey`, `destination`, `linkprogress`, `list/stops` | **FS** (following stops) |
| `connections` | **FS** connections, **LD**, **OM** |
| `announcement` | **OM** |
| `stopinfo` | Subscribed and stored; FS is built mainly from `linkprogress` + `list/stops` |

See [mqtt-pis-mapping.md](mqtt-pis-mapping.md) for field-level mapping.

## Legacy flat layout

If topics are directly `pis/{vehicle}/journey` (no broker root), leave `root` empty:

```yaml
mqtt:
  root: ""
  topic_prefix: "pis"
```

Subscriptions: `pis/+/journey`, `pis/+/linkprogress`, …

## Verify on the server

```bash
# Install mosquitto clients if needed: sudo apt install mosquitto-clients

mosquitto_sub -h YOUR_BROKER -t 'vilniustest/+/pis/0/journey' -v
mosquitto_sub -h YOUR_BROKER -t 'vilniustest/1232/pis/0/#' -v
```

After starting the service, check logs for the subscribed layout:

```bash
sudo journalctl -u tco-stopinfo-api | grep -i mqtt
# MQTT connected ... layout=vilniustest/{vehicle}/pis/0/{suffix}
```
