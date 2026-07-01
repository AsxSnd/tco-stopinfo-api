# MQTT-PIS-PT → TCO Stopinfo API mapping

This service subscribes to **MQTT-PIS-PT V1.6.0** topics (see `docs/mqtt-pis-pt-specification.md`) and maps vehicle state into the TCO API2 JSON envelope.

## Topic naming

See **[mqtt-topic-layout.md](mqtt-topic-layout.md)** for full broker tree examples.

### Vilnius-style layout (broker root + vehicle + spec)

```
vilniustest/{vehicle_id}/pis/0/{suffix}
```

| MQTT topic | Example (vehicle 1232) |
|------------|------------------------|
| `{root}/{vehicle_id}/pis/0/journey` | `vilniustest/1232/pis/0/journey` |
| `{root}/{vehicle_id}/pis/0/linkprogress` | `vilniustest/1232/pis/0/linkprogress` |
| `{root}/{vehicle_id}/pis/0/list/stops` | `vilniustest/1232/pis/0/list/stops` |

Config:

```yaml
mqtt:
  root: "vilniustest"
  topic_prefix: "pis"
  pis_instance: "0"
```

Subscriptions: `vilniustest/+/pis/0/journey`, etc.

### Flat layout (legacy)

| MQTT topic | Example |
|------------|---------|
| `{prefix}/{vehicle_id}/journey` | `pis/1232/journey` |

Set `mqtt.root: ""` and `topic_prefix: pis`.

## Subscribed topics

| MQTT suffix | Retain | Used for TCO area |
|-------------|--------|-------------------|
| `journey` | yes | FS — line, journey id |
| `destination` | yes | FS — destination header |
| `linkprogress` | no (1 Hz) | FS — position, ETAs, delay |
| `list/stops` | yes | FS — stop names, zones |
| `list/destinations` | yes | FS — multiple destinations |
| `connections` | yes | FS connections + **LD** + **OM** situations |
| `journeystate` | yes | (stored; future gating of FS when not in traffic) |
| `announcement` | yes | **OM** |
| `list/announcements` | yes | (stored; future OM queue) |
| `sensors/stop_button` | yes | FS — `Requested` on stops |
| `sensors/door` | yes | FS — `AtStop` hint when doors open |

Topics not listed are ignored.

## FS — Following Stops

| TCO JSON field | MQTT source | Transformation |
|----------------|-------------|----------------|
| `Line` | `destination.externalDisplay.lineNumber` → `journey.lineNumber` | First non-empty |
| `JourneyIdent` | `journey.vehicleJourneyRef` → `list/stops.vehicleJourneyRef` | First non-empty |
| `DelayMin` | `linkprogress.delaySeconds` | `floor(seconds / 60)` |
| `DistanceToNext` | `linkprogress.distance` | Metres; `-1` if absent |
| `DistanceFromPrev` | — | `-1` (not in MQTT) |
| `DestinationName` | `destination.externalDisplay` | `destinationName` + optional ` via ` + `viaDestinationName` |
| `ETA` / `ETAMinutes` | `linkprogress.expectedArrivalTimeDestination` | Format `hh:mm`; minutes from now |
| `DestinationExtended[]` | `destination`, `list/destinations` | One row per unique destination |
| `DestinationExtended[].DestinationStopIdx` | Last stop in `list/stops` | `stops[].number` |
| `Content[].Name` | `list/stops.stops[].name` | Skip `blind: true` |
| `Content[].StopIdx` | `stops[].number` | Call sequence number |
| `Content[].TariffZone` | `stops[].zoneCode` → `stops[].zone` | String |
| `Content[].Time` | `linkprogress.followingStops[].expectedArrivalTime` or first stop ETA | `"N min"`, `"Now"`, `"1 min"` |
| `Content[].TimeArrival` | Same ISO time | `hh:mm` |
| `Content[].AtStop` | `linkprogress.distance == 0` or `sensors/door.doorOpen` | First row only |
| `Content[].Requested` | `sensors/stop_button.stopPressed` or stop flags | `alightingAllowed` default true |
| `Content[].Note` | `stops[].cancelled` | `"cancelled"` or empty |
| `Content[].Connections` | `connections.connections[]` | Compact mode: unique lines per `transportModeCode` |
| `Connections[].TransportType` | `connections.transportModeCode` | BUS→700, TRAM→900, RAIL→100, METRO→400 |
| `Count` | Built rows | Max `accounts.*.max_following_stops` |
| `Heading` | constant | `"Following stops"` |
| `StatusCode` | — | 200 if `Count > 0`, else 204 |

### Stop selection logic

1. Read `linkprogress.callSequenceNumber` (next/current stop, 1-based).
2. Find matching stop in `list/stops.stops` by `number`.
3. Emit up to `max_following_stops` subsequent visible stops.
4. Match ETAs from `linkprogress.followingStops[]` by `callSequenceNumber`.

## LD — Line destinations

| TCO JSON field | MQTT source | Transformation |
|----------------|-------------|----------------|
| `Heading` | `connections.heading` | Or `"Departures at {stop name}"` |
| `Message` | `connections.message` | When empty list |
| `Display` | `connections.displayDurationSeconds` | Default -1 |
| `Content[].Mode` | `connections[].transportModeCode` | Uppercase string |
| `Content[].Line` | `connections[].lineDesignation` | Required |
| `Content[].Dest` | `connections[].directionName` | |
| `Content[].Stop` | `connections[].stopPointDesignation` | |
| `Content[].Times` | `connections[].departures[].expectedDepartureTime` | Relative minutes |
| `Content[].TimesExtended` | Same departures | Planned/absolute/relative/delay |
| `StatusCode` | — | 200 if non-empty and not expired |

**Gating:** Ignored if `connections.callSequenceNumber` ≠ current `linkprogress.callSequenceNumber`, or `expiryDateTime` is in the past.

## TD / MD — Train / Metro

Not produced from MQTT in this version. Areas always return `StatusCode: 204` with empty `Content`. (Full ITCS stack fills these from Darwin LDBWS / TfGM.)

## OM — Operation messages

| TCO JSON field | MQTT source |
|----------------|-------------|
| `Content[].MessageData.Heading` | `connections.situationMessages[].heading` or `announcement.message[].heading` |
| `Content[].MessageData.Detail` | `...body` |
| `MessageType` | `0` (general) |
| `Heading` | `"Traffic info"` when messages present |

Language: `announcement.message[]` entry matching `accounts.*.base_language` (e.g. `fi`).

## Status code summary

| Condition | FS | LD | OM |
|-----------|----|----|-----|
| No journey / stops | 204 | 204 | 204 |
| Journey active, following stops | 200 | — | — |
| Valid connections at current stop | — | 200 | — |
| Situation / announcement | — | — | 200 |

## Vehicle id alignment

HTTP `GET /api/stopinfo/hsl/1232` reads MQTT state for vehicle **`1232`**.

Ensure on-board MQTT publishers use the same id in the topic path (`pis/1232/...`) as displays use in HTTP.

## Reference

- MQTT-PIS-PT specification: `docs/mqtt-pis-pt-specification.md`
- TCO HTTP spec: `docs/tco-stopinfo-api-spec.md`
