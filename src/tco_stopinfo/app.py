from __future__ import annotations

import asyncio
import logging
import os
import sys
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone

import orjson
from fastapi import FastAPI, Request, Response
from fastapi.responses import ORJSONResponse

from .builder import build_response_headers, build_stopinfo_response
from .config import AppConfig, load_config
from .journey_context import refresh_active_fs_context, resolve_journey_stop_context
from .mqtt_client import MqttIngestService
from .mqtt_snapshot import fetch_vehicle_topics
from .mqtt_thread_client import MqttThreadIngestService
from .store import CachedResponse, VehicleStore

logger = logging.getLogger(__name__)


class ApplicationState:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.config.mqtt.client_id = (
            f"{config.mqtt.client_id}-{os.getpid()}-{config.http.port}"
        )
        self.store = VehicleStore(vehicle_ttl_seconds=config.cache.vehicle_ttl_seconds)
        self._stop_event = asyncio.Event()
        self._mqtt_task: asyncio.Task | None = None
        self._mqtt_thread: MqttThreadIngestService | None = None
        self._purge_task: asyncio.Task | None = None

    def _fs_inputs_ready(self, vehicle_id: str) -> bool:
        state = self.store.get_state(vehicle_id)
        if state is None:
            return False
        stop_list, stopinfo, _active_ref = resolve_journey_stop_context(
            state,
            stopinfo_ttl_seconds=self.config.cache.journey_stopinfo_ttl_seconds,
        )
        return bool(stop_list.get("stops")) and bool(
            stopinfo and stopinfo.get("callSequenceNumber") is not None
        )

    def ensure_vehicle_stop_context(self, vehicle_id: str) -> None:
        """Fill missing stopinfo/list/stops from a direct MQTT read (retained topics)."""
        if self._fs_inputs_ready(vehicle_id):
            return
        fetched = fetch_vehicle_topics(self.config.mqtt, vehicle_id)
        if not fetched:
            return
        state = self.store.get_or_create(vehicle_id)
        for suffix, payload in fetched.items():
            if isinstance(payload, dict):
                state.set_topic(suffix, payload)
        refresh_active_fs_context(state)

    def rebuild_vehicle(self, vehicle_id: str, accounts: list[str] | None = None) -> None:
        state = self.store.get_state(vehicle_id)
        if state is None:
            return
        refresh_active_fs_context(state)
        stop_list, stopinfo, _active_ref = resolve_journey_stop_context(
            state,
            stopinfo_ttl_seconds=self.config.cache.journey_stopinfo_ttl_seconds,
        )
        state.active_stop_list = stop_list
        state.active_stopinfo = stopinfo

        topics = {
            key: value
            for key, value in state.topics.items()
            if key not in {"list/stops", "stopinfo"}
        }
        topics["list/stops"] = stop_list
        if stopinfo is not None:
            topics["stopinfo"] = stopinfo

        account_names = accounts or list(self.config.accounts.keys())
        for account_name in account_names:
            account_cfg = self.config.account(account_name)
            payload = build_stopinfo_response(topics, account_cfg)
            headers = build_response_headers(
                payload,
                cache_max_age=self.config.cache.http_cache_max_age,
            )
            headers["Date"] = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")
            body = orjson.dumps(payload)
            self.store.put_response(
                account_name,
                vehicle_id,
                CachedResponse(
                    body=body,
                    headers=headers,
                    built_at=time.time(),
                    state_version=state.version,
                ),
            )

    def vehicle_debug(self, vehicle_id: str) -> dict[str, object]:
        state = self.store.get_state(vehicle_id)
        if state is None:
            return {"vehicle_id": vehicle_id, "present": False}
        stop_list, stopinfo, active_ref = resolve_journey_stop_context(
            state,
            stopinfo_ttl_seconds=self.config.cache.journey_stopinfo_ttl_seconds,
        )
        cached = self.store.get_response("vilnius", vehicle_id, fast_response_seconds=0)
        fs_count = 0
        if cached:
            fs_count = int(orjson.loads(cached.body)["FS"]["Count"])
        return {
            "vehicle_id": vehicle_id,
            "present": True,
            "topic_keys": sorted(state.topics.keys()),
            "cached_stop_lists": sorted(state.stop_lists_by_ref.keys()),
            "cached_stopinfo": sorted(state.stopinfo_by_ref.keys()),
            "active_journey_ref": active_ref,
            "resolved_stop_count": len(stop_list.get("stops") or []),
            "resolved_stopinfo": stopinfo,
            "cached_fs_count": fs_count,
            "state_version": state.version,
        }

    async def start_background_tasks(self) -> None:
        async def purge_loop() -> None:
            while not self._stop_event.is_set():
                await asyncio.sleep(300)
                removed = self.store.purge_stale()
                if removed:
                    logger.info("Purged %d stale vehicles from cache", removed)

        if sys.platform == "win32":
            self._mqtt_thread = MqttThreadIngestService(
                self.config, self.store, self.rebuild_vehicle
            )
            self._mqtt_thread.start()
        else:
            mqtt = MqttIngestService(self.config, self.store, self.rebuild_vehicle)
            self._mqtt_task = asyncio.create_task(mqtt.run(self._stop_event))

        self._purge_task = asyncio.create_task(purge_loop())

    async def stop_background_tasks(self) -> None:
        self._stop_event.set()
        if self._mqtt_thread is not None:
            self._mqtt_thread.stop()
            self._mqtt_thread = None
        for task in (self._mqtt_task, self._purge_task):
            if task is not None:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass


def create_app(config: AppConfig | None = None) -> FastAPI:
    app_config = config or load_config()
    state = ApplicationState(app_config)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        await state.start_background_tasks()
        yield
        await state.stop_background_tasks()

    app = FastAPI(
        title="TCO Stopinfo API",
        version="1.0.0",
        default_response_class=ORJSONResponse,
        lifespan=lifespan,
    )

    @app.get("/health")
    async def health() -> dict[str, object]:
        mqtt_cfg = state.config.mqtt
        cache_stats = state.store.stats()
        mqtt_info: dict[str, object] = {
            "layout": mqtt_cfg.describe_layout(),
            "broker": mqtt_cfg.broker,
            "port": mqtt_cfg.port,
        }
        if state._mqtt_thread is not None:
            mqtt_info["connected"] = state._mqtt_thread.connected
            mqtt_info["messages_received"] = state._mqtt_thread.messages_received
        return {
            "status": "ok",
            "http_port": state.config.http.port,
            "accounts_configured": list(state.config.accounts.keys()),
            "mqtt": mqtt_info,
            "cache": cache_stats,
        }

    @app.get("/debug/vehicle/{vehicle_id}")
    async def debug_vehicle(vehicle_id: str) -> dict[str, object]:
        return state.vehicle_debug(vehicle_id)

    @app.get("/api/stopinfo/{account}/{vehicle}")
    async def stopinfo(account: str, vehicle: str, request: Request) -> Response:
        await asyncio.to_thread(state.ensure_vehicle_stop_context, vehicle)
        state.rebuild_vehicle(vehicle, accounts=[account])
        cached = state.store.get_response(
            account,
            vehicle,
            fast_response_seconds=0,
        )
        if cached is None:
            account_cfg = state.config.account(account)
            payload = build_stopinfo_response({}, account_cfg)
            body = orjson.dumps(payload)
            headers = build_response_headers(
                payload,
                cache_max_age=state.config.cache.http_cache_max_age,
            )
            return Response(content=body, media_type="application/json", headers=headers)

        return Response(content=cached.body, media_type="application/json", headers=cached.headers)

    app.state.tco = state
    return app
