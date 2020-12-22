from netprobe.config import get_config, IP_REFLECTOR, WIFI_DEVICE, DEFAULT_WIFI_DEVICE
from netprobe.database import record_speed, record_ping, record_wifi, record_machine_info
from speedtest import Speedtest
from pythonping import ping
import re
from math import floor
from aiohttp import ClientSession
import asyncio
import logging
from datetime import datetime
import time

NMCLI_CMD = "nmcli -t -f ssid,signal,chan device wifi list"

logging.basicConfig(
    format="[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s", level=logging.INFO
)
probe_semaphore = asyncio.Semaphore(1)
started = datetime.now()


async def get_my_ip():
    ip_reflector = get_config(IP_REFLECTOR)
    async with ClientSession() as session:
        async with session.get(ip_reflector) as response:
            data = await response.json()
            return data.get("ipv4")


async def machine_uptime():
    with open("/proc/uptime") as f:
        return float(f.readlines()[0].rstrip().split(" ")[0])


async def service_uptime():
    td = datetime.now() - started
    return td.total_seconds()


async def run_ping(target):
    try:
        logging.info(f">>>START PING {target}...")
        result = ping(target, count=10)
        logging.info(
            f"<<<DONE PING {target}, {result.rtt_min_ms}/{result.rtt_avg_ms}/{result.rtt_max_ms}/"
            f"{100*round(result.packets_lost, 2)}%"
        )
        result = {
            "host": target,
            "tstamp": get_timestamp(),
            "min": result.rtt_min_ms,
            "max": result.rtt_max_ms,
            "avg": result.rtt_avg_ms,
            "loss": result.packets_lost,
        }

        await record_ping(result)
        return result
    except Exception as e:
        logging.error(e)
        return {"host": target, "error": str(e)}


async def detect_mtu(target):
    start = 1450
    end = 1800
    logging.info(f">>>START Determine MTU using: {target}, scanning ({start}-{end})...")
    try:
        nxt = start
        add = 20
        while nxt < end:
            res = ping(target, count=10, timeout=0.75, size=nxt, df=True)
            logging.info(
                f".........MTU check, size: {nxt}, packet loss: {100*round(res.packets_lost, 2)}%, target: {target}"
            )
            if res.packets_lost == 1.0:
                if add == 1:
                    logging.info(f"<<<DONE MTU: {nxt-1}")
                    result = {"target": target, "mtu": nxt - 1}
                    # await record_mtu(tstamp, result)
                    return result
                else:
                    nxt -= add
                    add = floor(add / 4)

            nxt += add
            await asyncio.sleep(0.1)

        return {
            "host": target,
            "mtu": "unknown",
        }
    except Exception as e:
        logging.error(e)
        return {}


async def scan_for_wifi():
    for i in range(3):
        result = await iwlist_scan()
        if result and len(result) > 0:
            tstamp = get_timestamp()
            for w in result:
                w["tstamp"] = tstamp

                await record_wifi(w)
            return result

        logging.info("WiFi scan failed...sleeping before trying again.")
        await asyncio.sleep(0.5)

    return []
    # return await nmcli_scan()


async def iwlist_scan():
    device = get_config(WIFI_DEVICE) or DEFAULT_WIFI_DEVICE
    # logging.info(f"Using WiFi device: {device}")
    command = f"/usr/sbin/iwlist {device} scan last"
    logging.info(f">>>START WiFi scanning...\n\n    {command}\n\n")
    process = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    scan_output, stderr = await process.communicate()

    # logging.info("Retrieving output from command")
    err = stderr.decode("utf-8")
    out = scan_output.decode("utf-8")

    # logging.info(f"output from wifi scan:\n\n{out}\n\n")
    # logging.info(f"error output from wifi scan:\n\n{err}\n\n")

    if process.returncode != 0:
        logging.error(f"Failed to scan for WiFi: {err.strip()}")
        return []
    else:
        lines = out.splitlines()

        result = []
        current = None
        for line in lines:
            if re.match(r"\s*Cell \d+ - Address: [:0-9a-fA-F]{17}\s*", line):
                # logging.info("Detected new network")
                if current is not None and len(current.keys()) > 2:
                    # logging.info(f"Appending current network: {current}")
                    result.append(current)

                current = {}
            else:
                parts = [p.strip() for p in re.split(r"\s*[:=]\s*", line)]

                if parts[0] == "ESSID":
                    current["ssid"] = parts[1][1:-1]
                elif parts[0] == "Quality":
                    qparts = [p.strip() for p in re.split(r"[ /]", parts[1])]

                    strength = round((int(qparts[0]) / int(qparts[1])) * 100)
                    current["str"] = strength
                elif parts[0] == "Channel":
                    current["chan"] = int(parts[1])

        # logging.info(
        #     f"<<<DONE WiFi scanning, {len(result)} networks found:\n\n{result}\n\n"
        # )
        return result


async def nmcli_scan():
    logging.info(">>>START WiFi scanning...")
    process = await asyncio.create_subprocess_shell(
        NMCLI_CMD,
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
                    "chan": parts[2],
                }
            )

        logging.info(f"<<<DONE WiFi scanning, {len(result)} networks found")
        return result


def get_timestamp():
    return int(time.time())


async def run_speedtest():
    logging.info(">>>START Speedtest...")
    try:
        tstamp = get_timestamp()
        test = Speedtest()
        test.get_best_server()

        logging.info(".........Checking download speed")
        test.download()
        logging.info(".........Checking upload speed")
        test.upload()

        result = test.results.dict()

        result["tstamp"] = tstamp
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
        await record_speed(result)
        return result
    except Exception as exception:
        logging.error(exception)
        return {}


async def gather_uptimes():
    uptimes = await asyncio.gather(
        machine_uptime(),
        service_uptime(),
    )

    uptime = {"machine": uptimes[0], "service": uptimes[1]}
    return uptime


async def probe_machine_info():
    results = await asyncio.gather(detect_mtu("8.8.8.8"), gather_uptimes())

    await record_machine_info(
        {"mtu": results[0], "tstamp": get_timestamp(), "uptime": results[1]}
    )


async def run_probes():
    async with probe_semaphore:
        results = await asyncio.gather(
            run_speedtest(),
            probe_machine_info(),
            scan_for_wifi(),
            run_ping("8.8.8.8"),
            run_ping("192.168.1.1"),
        )

        message = {
            "tstamp": get_timestamp(),
            "speed": results[0],
            "MTU": results[1],
            "uptime": results[2],
            "wifi": results[3],
            "ping": results[4:],
        }

        # logging.info(message)

        # resultstr = json.dumps(message)
        # logging.info(f"Size of result info: {len(resultstr.encode('utf-8'))}")

        return message


if __name__ == "__main__":
    asyncio.run(run_probes())
