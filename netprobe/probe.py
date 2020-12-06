from speedtest import Speedtest
import time
from pythonping import ping
import json
from math import floor
from .config import get_config, IP_REFLECTOR
from aiohttp import ClientSession
import asyncio
import logging

logging.basicConfig(
    format="[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s", level=logging.INFO
)
probe_semaphore = asyncio.Semaphore(1)


async def get_my_ip():
    ip_reflector = get_config(IP_REFLECTOR)
    async with ClientSession() as session:
        async with session.get(ip_reflector) as response:
            data = await response.json()
            return data.get("ipv4")


def sync_ping(target):
    try:
        logging.info(f">>>START PING {target}...")
        result = ping(target, count=10)
        logging.info(
            f"<<<DONE PING {target}, {result.rtt_min_ms}/{result.rtt_avg_ms}/{result.rtt_max_ms}/"
            f"{100*round(result.packets_lost, 2)}%"
        )
        return {
            "host": target,
            "min": result.rtt_min_ms,
            "max": result.rtt_max_ms,
            "avg": result.rtt_avg_ms,
            "loss": result.packets_lost,
        }
    except Exception as e:
        logging.error(e)
        return {"host": target, "error": str(e)}


def sync_detect_mtu(target):
    start = 1450
    end = 1800
    logging.info(f">>>START Determine MTU using: {target}, scanning ({start}-{end})...")

    next = start
    add = 20
    while next < end:
        res = ping(target, count=10, timeout=0.75, size=next, df=True)
        logging.info(
            f".........MTU check, size: {next}, packet loss: {100*round(res.packets_lost, 2)}%, target: {target}"
        )
        if res.packets_lost == 1.0:
            if add == 1:
                logging.info(f"<<<DONE MTU: {next-1}")
                return {"target": target, "mtu": next - 1}
            else:
                next -= add
                add = floor(add / 4)

        next += add

    return {
        "host": target,
        "mtu": "unknown",
    }


async def scan_for_wifi():
    logging.info(">>>START WiFi scanning...")
    process = await asyncio.create_subprocess_shell(
        " ".join(
            [
                "nmcli",
                "-t",
                "-f",
                "ssid,signal,freq,chan,in-use",
                "device",
                "wifi",
                "list",
            ]
        ),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    scan_output, stderr = await process.communicate()

    if process.returncode != 0:
        logging.error(f"Failed to scan for WiFi: {stderr.decode('utf-8').strip()}")
        return []
    else:
        lines = scan_output.decode("utf-8").splitlines()
        result = []
        for line in lines:
            parts = line.split(":")
            result.append(
                {
                    "ssid": parts[0],
                    "str": parts[1],
                    # "frequency": parts[2],
                    "chan": parts[3],
                    # "in-use": parts[4] == "*",
                }
            )

        logging.info(f"<<<DONE WiFi scanning, {len(result)} networks found")
        return result


def run_speedtest():
    logging.info(">>>START Speedtest...")
    test = Speedtest()
    test.get_best_server()

    logging.info(".........Checking download speed")
    test.download()
    logging.info(".........Checking upload speed")
    test.upload()

    result = test.results.dict()

    result["down_mbps"] = round(result["download"] / (1024 * 1024), 2)
    result["up_mbps"] = round(result["upload"] / (1024 * 1024), 2)

    for key in [
        "download",
        "upload",
        "bytes_sent",
        "bytes_received",
        "server",
        "client",
        "timestamp",
        "share",
    ]:
        result.pop(key, None)

    logging.info(f"<<<DONE Speedtest, {result['down_mbps']}/{result['up_mbps']}")
    return result


async def run_probes():
    async with probe_semaphore:
        loop = asyncio.get_event_loop()

        results = await asyncio.gather(
            loop.run_in_executor(None, run_speedtest),
            scan_for_wifi(),
            loop.run_in_executor(None, sync_detect_mtu, "8.8.8.8"),
            loop.run_in_executor(None, sync_ping, "8.8.8.8"),
            loop.run_in_executor(None, sync_ping, "192.168.1.1"),
            # loop.run_in_executor(None, sync_ping, "2001:4860:4860::8888")
        )

        now = int(time.time())
        message = {
            "tstamp": now,
            "speed": results[0],
            "wifi": results[1],
            "MTU": results[2],
            "ping": results[3:],
        }

        logging.info(message)

        resultstr = json.dumps(message)
        logging.info(f"Size of result info: {len(resultstr.encode('utf-8'))}")

        return message


if __name__ == "__main__":
    asyncio.run(run_probes())
