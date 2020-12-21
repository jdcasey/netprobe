#!/usr/bin/env python

import asyncio
import click
from .control import start_telegram
from .config import load_config
from .reporter import report_loop
import logging

logging.basicConfig(
    format="[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s", level=logging.INFO
)


@click.command()
@click.argument("config_file")
def run(config_file):
    load_config(config_file)

    loop = asyncio.get_event_loop()
    logging.info(f"Command loop: {loop}")

    logging.info("Starting Telegram client")
    logging.info("Starting reporting loop")
    asyncio.gather(
        start_telegram(),
        report_loop()
    )

    loop.run_forever()

