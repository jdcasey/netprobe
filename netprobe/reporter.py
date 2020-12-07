from .config import get_config, REPORTER_TIMEOUT, DEFAULT_REPORTER_TIMEOUT
from .probe import run_probes
import asyncio
import logging
import time

logging.basicConfig(
    format="[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s", level=logging.INFO
)


async def report_results(results):
    logging.info(results)
    pass


last_report = None


def get_latest_report():
    global last_report
    return last_report


async def report_loop():
    logging.info("Starting reporting loop")
    global last_report

    loop = asyncio.get_event_loop()
    logging.info(f"Reporter loop: {loop}")

    while True:
        try:
            start = time.time()
            last_report = await run_probes()
            await report_results(last_report)
            timeout = int(get_config(REPORTER_TIMEOUT) or DEFAULT_REPORTER_TIMEOUT)
            elapsed = time.time() - start
            if timeout > elapsed > timeout / 2:
                timeout = round(timeout - elapsed)

            logging.info(f"Reporting loop sleeping {timeout} seconds")
            await asyncio.sleep(timeout)
        except KeyboardInterrupt:
            break
