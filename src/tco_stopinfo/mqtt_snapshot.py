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
    connect_timeout: float = 0.5,
    wait_seconds: float = 0.35,
    suffixes: tuple[str, ...] = FETCH_SUFFIXES,
) -> dict[str, Any]:
    """Fetch retained/live MQTT topics for one vehicle (HTTP fallback).

    Returns as soon as retained messages arrive or *wait_seconds* elapses after
    connect — avoids blocking HTTP for multiple seconds when no active trip exists.
    """
    prefix = f"{mqtt_cfg.root}/{vehicle_id}/{mqtt_cfg.topic_prefix}/{mqtt_cfg.pis_instance}"
    topics = [f"{prefix}/{suffix}" for suffix in suffixes]
    results: dict[str, Any] = {}
    connected = threading.Event()
    done = threading.Event()

    def on_connect(
        client: mqtt.Client,
        _userdata: object,
        _flags: object,
        reason_code: object,
        _properties: object = None,
    ) -> None:
        if reason_code != 0:
            done.set()
            return
        connected.set()
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
    try:
        if not connected.wait(timeout=connect_timeout):
            return results
        deadline = time.monotonic() + wait_seconds
        while time.monotonic() < deadline:
            if len(results) >= len(suffixes):
                break
            time.sleep(0.02)
    finally:
        client.loop_stop()
        client.disconnect()
    return results
