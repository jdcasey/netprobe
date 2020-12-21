from .config import get_config, NODE_NAME, WRITER_COUNT, DEFAULT_WRITER_COUNT
import asyncio
import logging
from google.cloud import firestore

logging.basicConfig(
    format="[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s", level=logging.INFO
)

db = firestore.AsyncClient()

last_report = None
q = asyncio.Queue()


async def consumer(index, q):
    logging.info(f"Writer[{index}]: Ready to write new database documents...")
    while True:
        try:
            doc_task = await q.get()

            coll_id = doc_task["coll"]
            doc_id = doc_task.get("doc")
            data = doc_task["data"]

            # logging.info(f"Writing new doc to {coll_id}")
            if doc_id:
                _stamp = await db.collection(coll_id).document(doc_id).set(data)
                logging.info(f"Writer[{index}]: Wrote {doc_id} to {coll_id}")
            else:
                _stamp, doc = await db.collection(coll_id).add(data)
                logging.info(f"Writer[{index}]: Wrote {doc.id} to {coll_id}")

        except Exception as exception:
            logging.error(exception)


async def start_database():
    count = int(get_config(WRITER_COUNT) or DEFAULT_WRITER_COUNT)
    for i in range(count):
        asyncio.create_task(consumer(i, q))


async def record_ping(ping):
    global q
    await q.put(
        {
            "coll": f"netprobe/{get_config(NODE_NAME)}/ping",
            "data": ping,
        }
    )


async def record_wifi(wifi):
    global q
    await q.put(
        {
            "coll": f"netprobe/{get_config(NODE_NAME)}/wifi",
            "data": wifi,
        }
    )


async def record_machine_info(info):
    global q
    await q.put({
        "coll": f"netprobe",
        "doc": get_config(NODE_NAME),
        "data": info,
    })


async def record_speed(speed):
    global q
    await q.put(
        {
            "coll": f"netprobe/{get_config(NODE_NAME)}/speed",
            "data": speed,
        }
    )
