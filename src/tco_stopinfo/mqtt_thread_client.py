from __future__ import annotations

import logging
import threading
from typing import Callable

import orjson
import paho.mqtt.client as mqtt

from .config import AppConfig
from .mqtt_client import parse_mqtt_topic
from .store import TOPIC_SUFFIXES, VehicleStore

logger = logging.getLogger(__name__)

RebuildCallback = Callable[[str], None]


class MqttThreadIngestService:
    """Thread-based MQTT ingest for Windows (ProactorEventLoop lacks add_reader)."""

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
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self.connected = False
        self.messages_received = 0

    def _on_message(
        self,
        _client: mqtt.Client,
        _userdata: object,
        msg: mqtt.MQTTMessage,
    ) -> None:
        parsed = parse_mqtt_topic(msg.topic, self._mqtt)
        if parsed is None:
            return
        vehicle_id, suffix = parsed
        self.messages_received += 1
        try:
            payload = orjson.loads(msg.payload)
        except orjson.JSONDecodeError:
            logger.warning("Invalid JSON on topic %s", msg.topic)
            return
        if self._store.update_topic(vehicle_id, suffix, payload):
            self._on_vehicle_updated(vehicle_id)

    def start(self) -> None:
        if self._thread is not None:
            return

        def run() -> None:
            mqtt_cfg = self._config.mqtt
            client = mqtt.Client(
                mqtt.CallbackAPIVersion.VERSION2,
                client_id=mqtt_cfg.client_id,
            )
            if mqtt_cfg.username:
                client.username_pw_set(mqtt_cfg.username, mqtt_cfg.password or "")
            client.on_message = self._on_message

            while not self._stop.is_set():
                try:
                    client.connect(mqtt_cfg.broker, mqtt_cfg.port, keepalive=60)
                    for suffix in TOPIC_SUFFIXES:
                        client.subscribe(mqtt_cfg.subscription_topic(suffix), qos=1)
                    logger.info(
                        "MQTT connected to %s:%s layout=%s (%d subscriptions)",
                        mqtt_cfg.broker,
                        mqtt_cfg.port,
                        mqtt_cfg.describe_layout(),
                        len(TOPIC_SUFFIXES),
                    )
                    self.connected = True
                    client.loop_start()
                    while not self._stop.wait(1.0):
                        pass
                    self.connected = False
                    client.loop_stop()
                    client.disconnect()
                    return
                except Exception as exc:
                    if self._stop.is_set():
                        return
                    logger.error(
                        "MQTT error: %s — reconnecting in %ss",
                        exc,
                        mqtt_cfg.reconnect_seconds,
                    )
                    if self._stop.wait(mqtt_cfg.reconnect_seconds):
                        return

        self._thread = threading.Thread(target=run, name="mqtt-ingest", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=15)
            self._thread = None
