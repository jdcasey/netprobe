from .config import get_config, REPORTER_TIMEOUT, DEFAULT_REPORTER_TIMEOUT
from .probe import run_probes
from .database import start_database
import asyncio
import logging
import time

logging.basicConfig(
    format="[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s", level=logging.INFO
)

last_report = None


def get_latest_report():
    global last_report
    return last_report


async def report_loop():
    global last_report
    logging.info("Starting reporting loop")

    await start_database()
    while True:
        try:
            start = time.time()

            last_report = await run_probes()

            # await report_results(last_report, q)
            timeout = int(get_config(REPORTER_TIMEOUT) or DEFAULT_REPORTER_TIMEOUT)
            elapsed = time.time() - start
            if timeout > elapsed > timeout / 2:
                timeout = round(timeout - elapsed)

            logging.info(f"Reporting loop sleeping {timeout} seconds")
            await asyncio.sleep(timeout)
        except KeyboardInterrupt:
            break
