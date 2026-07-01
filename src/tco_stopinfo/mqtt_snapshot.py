from __future__ import annotations

import json
import threading
import time
from typing import Any

import paho.mqtt.client as mqtt

from .config import MqttConfig

FETCH_SUFFIXES = ("stopinfo", "list/stops", "journey")


def fetch_vehicle_topics(
    mqtt_cfg: MqttConfig,
    vehicle_id: str,
    *,
    wait_seconds: float = 2.0,
    suffixes: tuple[str, ...] = FETCH_SUFFIXES,
) -> dict[str, Any]:
    """Fetch retained/live MQTT topics for one vehicle (HTTP fallback)."""
    prefix = f"{mqtt_cfg.root}/{vehicle_id}/{mqtt_cfg.topic_prefix}/{mqtt_cfg.pis_instance}"
    topics = [f"{prefix}/{suffix}" for suffix in suffixes]
    results: dict[str, Any] = {}
    done = threading.Event()

    def on_connect(client: mqtt.Client, _userdata: object, _flags: object, reason_code: object, _properties: object = None) -> None:
        if reason_code != 0:
            done.set()
            return
        for topic in topics:
            client.subscribe(topic, qos=1)

    def on_message(_client: mqtt.Client, _userdata: object, msg: mqtt.MQTTMessage) -> None:
        for suffix, topic in zip(suffixes, topics, strict=True):
            if msg.topic != topic:
                continue
            if not msg.payload:
                continue
            try:
                results[suffix] = json.loads(msg.payload.decode("utf-8"))
            except json.JSONDecodeError:
                pass

    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id=f"{mqtt_cfg.client_id}-fetch-{vehicle_id}-{int(time.time())}",
    )
    if mqtt_cfg.username:
        client.username_pw_set(mqtt_cfg.username, mqtt_cfg.password or "")
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(mqtt_cfg.broker, mqtt_cfg.port, keepalive=30)
    client.loop_start()
    done.wait(timeout=1.0)
    time.sleep(wait_seconds)
    client.loop_stop()
    client.disconnect()
    return results
