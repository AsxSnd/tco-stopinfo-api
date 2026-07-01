from __future__ import annotations

import asyncio
import logging
from typing import Callable

import aiomqtt
import orjson

from .config import AppConfig
from .store import TOPIC_SUFFIXES, VehicleStore

logger = logging.getLogger(__name__)

RebuildCallback = Callable[[str], None]


class MqttIngestService:
    """Subscribes to MQTT-PIS-PT topics and updates the in-memory vehicle store."""

    def __init__(
        self,
        config: AppConfig,
        store: VehicleStore,
        on_vehicle_updated: RebuildCallback,
    ) -> None:
        self._config = config
        self._store = store
        self._on_vehicle_updated = on_vehicle_updated
        self._prefix = config.mqtt.topic_prefix.rstrip("/")
        self._suffix_map = {suffix: suffix for suffix in TOPIC_SUFFIXES}

    def _parse_topic(self, topic: str) -> tuple[str, str] | None:
        # Expected: {prefix}/{vehicle_id}/{suffix...}
        parts = topic.split("/")
        if len(parts) < 3:
            return None
        if parts[0] != self._prefix:
            return None
        vehicle_id = parts[1]
        suffix = "/".join(parts[2:])
        if suffix not in self._suffix_map:
            return None
        return vehicle_id, suffix

    def _decode_payload(self, payload: bytes | None) -> dict | list | None:
        if not payload:
            return None
        try:
            return orjson.loads(payload)
        except orjson.JSONDecodeError:
            logger.warning("Invalid JSON payload (%d bytes)", len(payload))
            return None

    async def run(self, stop_event: asyncio.Event) -> None:
        mqtt_cfg = self._config.mqtt
        subscriptions = [
            (f"{self._prefix}/+/{suffix}", 1) for suffix in TOPIC_SUFFIXES
        ]

        while not stop_event.is_set():
            try:
                async with aiomqtt.Client(
                    hostname=mqtt_cfg.broker,
                    port=mqtt_cfg.port,
                    username=mqtt_cfg.username,
                    password=mqtt_cfg.password,
                    identifier=mqtt_cfg.client_id,
                ) as client:
                    for topic, qos in subscriptions:
                        await client.subscribe(topic, qos=qos)
                    logger.info(
                        "MQTT connected to %s:%s (%d subscriptions)",
                        mqtt_cfg.broker,
                        mqtt_cfg.port,
                        len(subscriptions),
                    )
                    async for message in client.messages:
                        if stop_event.is_set():
                            break
                        parsed = self._parse_topic(str(message.topic))
                        if parsed is None:
                            continue
                        vehicle_id, suffix = parsed
                        payload = self._decode_payload(message.payload)
                        if payload is None:
                            continue
                        changed = self._store.update_topic(vehicle_id, suffix, payload)
                        if changed:
                            self._on_vehicle_updated(vehicle_id)
            except aiomqtt.MqttError as exc:
                if stop_event.is_set():
                    break
                logger.error("MQTT error: %s — reconnecting in %ss", exc, mqtt_cfg.reconnect_seconds)
                await asyncio.sleep(mqtt_cfg.reconnect_seconds)
