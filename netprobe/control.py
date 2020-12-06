from telethon import TelegramClient, events
from telethon.tl.types import MessageEntityMention
from telethon.sessions import StringSession
from .probe import run_probes, get_my_ip
from .config import (
    get_config,
    TELEGRAM_SESSION_ID,
    TELEGRAM_API_ID,
    TELEGRAM_API_HASH,
    TELEGRAM_NODE_NAME,
)
import logging
from datetime import datetime
import asyncio

logging.basicConfig(
    format="[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s", level=logging.INFO
)

client = None


def start_telegram():
    global client
    client = TelegramClient(
        StringSession(get_config(TELEGRAM_SESSION_ID)),
        get_config(TELEGRAM_API_ID),
        get_config(TELEGRAM_API_HASH),
        loop=asyncio.get_event_loop()
    )

    node_name = get_config(TELEGRAM_NODE_NAME)
    client.add_event_handler(
        time_reply, events.NewMessage(pattern=r".*time.*")
    )
    client.add_event_handler(
        probe_handler, events.NewMessage(pattern=r".*run probe.*")
    )
    client.add_event_handler(
        get_ip_address,
        events.NewMessage(pattern=r".*get [iI][pP].*"),
    )

    client.start()
    client.run_until_disconnected()


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


async def time_reply(event):
    global client
    if await directed_at_me(event):
        await event.reply(f"The UTC time is now {datetime.utcnow()}")


# @client.on(events.NewMessage(pattern=r".+run probe.+"))
async def probe_handler(event):
    if await directed_at_me(event):
        scan = await run_probes()
        await event.reply(f"{scan}")


# @client.on(events.NewMessage(pattern=r".+get [iI][pP].+"))
async def get_ip_address(event):
    if await directed_at_me(event):
        scan = await get_my_ip()
        await event.reply(f"{scan}")
