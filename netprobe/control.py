from telethon import TelegramClient, events
from telethon.tl.types import MessageEntityMention
from telethon.sessions import StringSession
import logging
from datetime import datetime, timedelta
import asyncio
from netprobe.probe import run_probes, get_my_ip, service_uptime, machine_uptime
from netprobe.config import (
    get_config,
    ANNOUNCE_START,
    DEFAULT_ANNOUNCE_START,
    TELEGRAM_SESSION_ID,
    TELEGRAM_API_ID,
    TELEGRAM_API_HASH,
    NODE_NAME,
)
from netprobe.formatter import format
from netprobe.reporter import get_latest_report
from netprobe.systrol import list_packages, upgrade_packages, reboot
from os import execv
import sys

logging.basicConfig(
    format="[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s", level=logging.INFO
)

client = None


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
        loop=loop,
    )

    client.add_event_handler(rollcall, events.NewMessage(pattern=r".*roll\s?call.*"))
    client.add_event_handler(time_reply, events.NewMessage(pattern=r".*time.*"))
    client.add_event_handler(
        handle_get_last_probe,
        events.NewMessage(pattern=r".*(get )?(latest|last) (probe|report).*"),
    )
    client.add_event_handler(
        handle_run_probe, events.NewMessage(pattern=r".*run probe.*")
    )
    client.add_event_handler(
        handle_get_ip,
        events.NewMessage(pattern=r".*get [iI][pP].*"),
    )
    client.add_event_handler(
        handle_pip_list, events.NewMessage(pattern=r".*pip list\s*")
    )
    client.add_event_handler(
        handle_pip_upgrade, events.NewMessage(pattern=r".*pip upgrade\s*")
    )
    client.add_event_handler(
        handle_reboot, events.NewMessage(pattern=r".*reboot\s*")
    )
    client.add_event_handler(
        handle_help, events.NewMessage(pattern=r".*help\s*")
    )

    await client.start()

    if bool(get_config(ANNOUNCE_START) or DEFAULT_ANNOUNCE_START) is True:
        await client.send_message(
            "@buildchimp", f"*{get_config(NODE_NAME)}* is online! 🎉"
        )

    logging.info("Telegram client should be running.")
    await client.run_until_disconnected()


async def _directed_at_me(event):
    global client
    node_name = get_config(NODE_NAME)
    logging.warning(f"Handle for node: {node_name}: {event.raw_text}")

    me = await client.get_me()
    for e, txt in event.get_entities_text():
        if (
            type(e) == MessageEntityMention
            and txt[1:] == me.username
            and node_name in event.raw_text
        ):
            logging.warning("This message is directed at me.")
            return True

    return False


def _adjust_report(data):
    if data["wifi"]:
        data["wifi"].sort(key=lambda r: int(r["chan"]))


async def handle_reboot(event):
    logging.warning("Rebooting system!")
    message = await reboot()
    await event.reply(f"`{message}`")


async def handle_help(event):
    handlers = event.client.list_event_handlers()
    names = []
    for handler, _ in handlers:
        name = handler.__name__
        if name.startswith("handle_"):
            name = name[len("handle_"):]
        name = name.replace("_", " ")
        names.append(name)

    message = "\n".join(names)
    await event.reply(message)


async def handle_pip_list(event):
    package_list = await list_packages()
    await event.reply(f"`{package_list}`")


async def handle_pip_upgrade(event):
    logging.warning("Upgrading pip packages and restarting service!")
    package_list = await upgrade_packages()
    sender = await event.get_sender()
    await event.client.send_file(
        sender,
        package_list.encode("utf-8"),
        caption="`pip` output is attached. Netprobe is restarting.",
        reply_to=event.message,
    )
    execv(sys.argv[0], sys.argv)


async def rollcall(event):
    node_name = get_config(NODE_NAME)
    for e, txt in event.get_entities_text():
        print(type(e))

    await event.reply(f"*{node_name}* is online!")


async def time_reply(event):
    global client
    if await _directed_at_me(event):
        await event.reply(
            f"`Local:` **{datetime.now()}**\n"
            f"`UTC:  ` **{datetime.utcnow()}**\n"
            f"`Service Uptime:` **{timedelta(seconds=await service_uptime())}**\n"
            f"`Machine Uptime:` **{timedelta(seconds=await machine_uptime())}**"
        )


async def handle_get_last_probe(event):
    if await _directed_at_me(event):
        await event.reply("Gathering / running probe...please stand by")
        report = get_latest_report()
        logging.info(f"Last report is: {report}")
        if report is None:
            logging.info("Running new probe...")
            report = await run_probes()

        logging.info("Rendering report")
        _adjust_report(report)
        rendered = await format("probe-result.md", report)
        await event.reply(f"{rendered}")


async def handle_run_probe(event):
    if await _directed_at_me(event):
        await event.reply("Running network probe...please stand by")
        report = await run_probes()
        _adjust_report(report)
        rendered = await format("probe-result.md", report)
        await event.reply(f"{rendered}")


async def handle_get_ip(event):
    if await _directed_at_me(event):
        scan = await get_my_ip()
        await event.reply(f"{scan}")
