from telethon import TelegramClient, events
from telethon.tl.types import MessageEntityMention
from telethon.sessions import StringSession
import logging
from datetime import datetime
import asyncio
from .probe import run_probes, get_my_ip, service_uptime, machine_uptime
from .config import (
    get_config,
    TELEGRAM_SESSION_ID,
    TELEGRAM_API_ID,
    TELEGRAM_API_HASH,
    TELEGRAM_NODE_NAME,
)
from .formatter import format
from .reporter import get_latest_report

logging.basicConfig(
    format="[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s", level=logging.INFO
)

client = None
started = datetime.now()


def sync_start_telegram():
    asyncio.run(start_telegram())


async def start_telegram():
    global client
    loop = asyncio.get_event_loop()
    logging.info(f"Telegram loop: {loop}")
    client = TelegramClient(
        StringSession(get_config(TELEGRAM_SESSION_ID)),
        get_config(TELEGRAM_API_ID),
        get_config(TELEGRAM_API_HASH),
        loop=loop
    )

    client.add_event_handler(
        rollcall, events.NewMessage(pattern=r".*roll\s?call.*")
    )
    client.add_event_handler(
        time_reply, events.NewMessage(pattern=r".*time.*")
    )
    client.add_event_handler(
        get_probe_handler, events.NewMessage(pattern=r".*(get )?(latest|last) (probe|report).*")
    )
    client.add_event_handler(
        run_probe_handler, events.NewMessage(pattern=r".*run probe.*")
    )
    client.add_event_handler(
        get_ip_address,
        events.NewMessage(pattern=r".*get [iI][pP].*"),
    )

    await client.start()
    await client.send_message("@buildchimp", f"*{get_config(TELEGRAM_NODE_NAME)}* is online! 🎉")
    logging.info("Telegram client should be running.")
    await client.run_until_disconnected()


async def directed_at_me(event):
    global client
    node_name = get_config(TELEGRAM_NODE_NAME)
    logging.warning(f"Handle for node: {node_name}: {event.raw_text}")

    me = await client.get_me()
    for e, txt in event.get_entities_text():
        if type(e) == MessageEntityMention and txt[1:] == me.username and node_name in event.raw_text:
            logging.warning("This message is directed at me.")
            return True

    return False


def adjust_report(data):
    if data["wifi"]:
        data["wifi"].sort(key=lambda r: int(r["chan"]))


async def rollcall(event):
    node_name = get_config(TELEGRAM_NODE_NAME)
    for e, txt in event.get_entities_text():
        print(type(e))

    await event.reply(f"*{node_name}* is online!")


async def time_reply(event):
    global client
    global started
    if await directed_at_me(event):
        await event.reply(f"`Local:` **{datetime.now()}**\n"
                          f"`UTC:  ` **{datetime.utcnow()}**\n"
                          f"`Service Uptime:` **{service_uptime()}**\n\n"
                          f"`Machine Uptime:`\n"
                          f"`{await machine_uptime()}`")


async def get_probe_handler(event):
    if await directed_at_me(event):
        await event.reply("Gathering / running probe...please stand by")
        report = get_latest_report()
        logging.info(f"Last report is: {report}")
        if report is None:
            logging.info("Running new probe...")
            report = await run_probes()

        logging.info("Rendering report")
        adjust_report(report)
        rendered = await format('probe-result.md', report)
        await event.reply(f"{rendered}")


async def run_probe_handler(event):
    if await directed_at_me(event):
        await event.reply("Running network probe...please stand by")
        report = await run_probes()
        adjust_report(report)
        rendered = await format('probe-result.md', report)
        await event.reply(f"{rendered}")


async def get_ip_address(event):
    if await directed_at_me(event):
        scan = await get_my_ip()
        await event.reply(f"{scan}")
