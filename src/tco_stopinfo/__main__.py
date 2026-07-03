from __future__ import annotations

import argparse
import asyncio
import logging
import sys

import uvicorn

from .app import create_app
from .config import load_config


def _configure_asyncio_for_platform() -> None:
    """aiomqtt needs add_reader/add_writer; Windows ProactorEventLoop lacks them."""
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


def _uvicorn_runtime_options() -> dict[str, str]:
    """uvloop is Linux/macOS only; use defaults on Windows."""
    options: dict[str, str] = {
        # h11 preserves legacy X.TC-* header casing; uvicorn httptools lowercases names.
        "http": "h11",
    }
    if sys.platform == "win32":
        options["loop"] = "asyncio"
    else:
        try:
            import uvloop  # noqa: F401

            options["loop"] = "uvloop"
        except ImportError:
            pass
    return options


def main() -> None:
    _configure_asyncio_for_platform()

    parser = argparse.ArgumentParser(description="TCO stopinfo API service")
    parser.add_argument(
        "-c",
        "--config",
        default="config.yaml",
        help="Path to YAML configuration file (default: config.yaml)",
    )
    args = parser.parse_args()

    config = load_config(args.config)
    logging.basicConfig(
        level=getattr(logging, config.http.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    workers = config.http.workers
    if sys.platform == "win32" and workers != 1:
        logging.warning("Multiple workers are not supported on Windows; using workers=1")
        workers = 1

    app = create_app(config)
    uvicorn.run(
        app,
        host=config.http.host,
        port=config.http.port,
        workers=workers,
        log_level=config.http.log_level,
        access_log=True,
        **_uvicorn_runtime_options(),
    )


if __name__ == "__main__":
    sys.exit(main())
