from __future__ import annotations

import argparse
import logging
import sys

import uvicorn

from .app import create_app
from .config import load_config


def main() -> None:
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

    app = create_app(config)
    uvicorn.run(
        app,
        host=config.http.host,
        port=config.http.port,
        workers=config.http.workers,
        log_level=config.http.log_level,
        loop="uvloop",
        http="httptools",
        access_log=True,
    )


if __name__ == "__main__":
    sys.exit(main())
