from __future__ import annotations

import asyncio
import logging
from typing import Callable

import aiomqtt
import orjson

from .config import AppConfig, MqttConfig
from .store import TOPIC_SUFFIXES, VehicleStore

logger = logging.getLogger(__name__)

RebuildCallback = Callable[[str], None]


def parse_mqtt_topic(topic: str, mqtt_cfg: MqttConfig) -> tuple[str, str] | None:
    """
    Parse vehicle id and PIS suffix from an MQTT topic.

  Nested layout (when mqtt.root is set):
      {root}/{vehicle_id}/pis/{instance}/{suffix}
      e.g. vilniustest/1232/pis/0/journey

  Flat layout (legacy, mqtt.root empty):
      pis/{vehicle_id}/{suffix}
      e.g. pis/1232/journey
    """
    parts = topic.split("/")
    suffix_map = {suffix: suffix for suffix in TOPIC_SUFFIXES}

    if mqtt_cfg.root:
        # vilniustest / vehicle / pis / 0 / journey  (+ optional list/stops)
        if len(parts) < 5:
            return None
        if parts[0] != mqtt_cfg.root:
            return None
        if parts[2] != mqtt_cfg.topic_prefix or parts[3] != mqtt_cfg.pis_instance:
            return None
        vehicle_id = parts[1]
        suffix = "/".join(parts[4:])
    else:
        if len(parts) < 3:
            return None
        if parts[0] != mqtt_cfg.topic_prefix:
            return None
        vehicle_id = parts[1]
        suffix = "/".join(parts[2:])

    if suffix not in suffix_map:
        return None
    return vehicle_id, suffix


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
        self._mqtt = config.mqtt
        self._rebuild_sem = asyncio.Semaphore(4)
        self._rebuild_tasks: dict[str, asyncio.Task[None]] = {}
        self.connected = False
        self.messages_received = 0

    def _parse_topic(self, topic: str) -> tuple[str, str] | None:
        return parse_mqtt_topic(topic, self._mqtt)

    def _decode_payload(self, payload: bytes | None) -> dict | list | None:
        if not payload:
            return None
        try:
            return orjson.loads(payload)
        except orjson.JSONDecodeError:
            logger.warning("Invalid JSON payload (%d bytes)", len(payload))
            return None

    async def _rebuild_vehicle(self, vehicle_id: str) -> None:
        async with self._rebuild_sem:
            await asyncio.to_thread(self._on_vehicle_updated, vehicle_id)

    def _schedule_rebuild(self, vehicle_id: str) -> None:
        existing = self._rebuild_tasks.get(vehicle_id)
        if existing is not None and not existing.done():
            return

        async def run() -> None:
            try:
                await asyncio.sleep(0.05)
                await self._rebuild_vehicle(vehicle_id)
            finally:
                self._rebuild_tasks.pop(vehicle_id, None)

        self._rebuild_tasks[vehicle_id] = asyncio.create_task(run())

    async def run(self, stop_event: asyncio.Event) -> None:
        mqtt_cfg = self._config.mqtt
        subscriptions = [
            (mqtt_cfg.subscription_topic(suffix), 1) for suffix in TOPIC_SUFFIXES
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
                    self.connected = True
                    for topic, qos in subscriptions:
                        await client.subscribe(topic, qos=qos)
                    logger.info(
                        "MQTT connected to %s:%s client_id=%s layout=%s (%d subscriptions)",
                        mqtt_cfg.broker,
                        mqtt_cfg.port,
                        mqtt_cfg.client_id,
                        mqtt_cfg.describe_layout(),
                        len(subscriptions),
                    )
                    for topic, _qos in subscriptions[:3]:
                        logger.info("  subscribe: %s", topic)
                    if len(subscriptions) > 3:
                        logger.info("  subscribe: ... and %d more", len(subscriptions) - 3)
                    async for message in client.messages:
                        if stop_event.is_set():
                            break
                        self.messages_received += 1
                        parsed = self._parse_topic(str(message.topic))
                        if parsed is None:
                            continue
                        vehicle_id, suffix = parsed
                        payload = self._decode_payload(message.payload)
                        if payload is None:
                            continue
                        changed = self._store.update_topic(vehicle_id, suffix, payload)
                        if changed:
                            self._schedule_rebuild(vehicle_id)
            except aiomqtt.MqttError as exc:
                self.connected = False
                if stop_event.is_set():
                    break
                logger.error("MQTT error: %s — reconnecting in %ss", exc, mqtt_cfg.reconnect_seconds)
                await asyncio.sleep(mqtt_cfg.reconnect_seconds)
            finally:
                self.connected = False
