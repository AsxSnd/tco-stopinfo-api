from __future__ import annotations

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone

import orjson
from fastapi import FastAPI, Request, Response
from fastapi.responses import ORJSONResponse

from .builder import build_response_headers, build_stopinfo_response
from .config import AppConfig, load_config
from .mqtt_client import MqttIngestService
from .store import CachedResponse, VehicleStore

logger = logging.getLogger(__name__)


class ApplicationState:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.store = VehicleStore(vehicle_ttl_seconds=config.cache.vehicle_ttl_seconds)
        self._stop_event = asyncio.Event()
        self._mqtt_task: asyncio.Task | None = None
        self._purge_task: asyncio.Task | None = None

    def rebuild_vehicle(self, vehicle_id: str) -> None:
        state = self.store.get_state(vehicle_id)
        if state is None:
            return
        for account_name, account_cfg in self.config.accounts.items():
            payload = build_stopinfo_response(state.topics, account_cfg)
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

    async def start_background_tasks(self) -> None:
        mqtt = MqttIngestService(self.config, self.store, self.rebuild_vehicle)

        async def purge_loop() -> None:
            while not self._stop_event.is_set():
                await asyncio.sleep(300)
                removed = self.store.purge_stale()
                if removed:
                    logger.info("Purged %d stale vehicles from cache", removed)

        self._mqtt_task = asyncio.create_task(mqtt.run(self._stop_event))
        self._purge_task = asyncio.create_task(purge_loop())

    async def stop_background_tasks(self) -> None:
        self._stop_event.set()
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
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/stopinfo/{account}/{vehicle}")
    async def stopinfo(account: str, vehicle: str, request: Request) -> Response:
        cached = state.store.get_response(
            account,
            vehicle,
            fast_response_seconds=state.config.cache.fast_response_seconds,
        )
        if cached is None:
            # No MQTT data yet — return empty TCO envelope (matches legacy error response).
            account_cfg = state.config.account(account)
            payload = build_stopinfo_response({}, account_cfg)
            body = orjson.dumps(payload)
            headers = build_response_headers(
                payload,
                cache_max_age=state.config.cache.http_cache_max_age,
            )
            return Response(content=body, media_type="application/json", headers=headers)

        # Optional: rebuild if state advanced but cache missed (safety net).
        vehicle_state = state.store.get_state(vehicle)
        if vehicle_state and vehicle_state.version != cached.state_version:
            state.rebuild_vehicle(vehicle)
            cached = state.store.get_response(
                account,
                vehicle,
                fast_response_seconds=0,
            ) or cached

        return Response(content=cached.body, media_type="application/json", headers=cached.headers)

    app.state.tco = state
    return app
